#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci_index.py — 수집 논문 검색용 색인 (CSV, LLM 없음).

    python sci_index.py build --kb-root <dir>              # index.csv + index_check.csv + README.md
    python sci_index.py apply --kb-root <dir> --gists <csv> # Claude(sonnet) 가 만든 요약_ko / 검수 flag 를 index.csv 에 병합

index.csv 열 (2026-09-18 확정): paper_id, DOI, 제목, 저자(6명 이하 전원 / 7명 이상 앞3+뒤3), 교신저자, 연도, 저널, 저널약어, 권, 호, 페이지,
  초록, 키워드(있을 때만), 원문상태, 본문 단어수, SI 유무, 수집일, 수집 URL, 파일경로, 요약_ko
재료: collection_registry.csv (resolve 메타) + papers/{id}/source.json + source.md + pdf/ 파일 실물. UTF-8 BOM (엑셀 한글 OK), 초록은 한 줄.
검수 1단계(결정적): index_check.csv — DOI 형식/중복, 필수 항목 누락, 상태-단어수 정합, 파일 존재, 깨진 문자, 초록 길이, 연도 범위.
검수 2단계(LLM, sonnet): Claude 가 제목-초록 정합·잘림·보일러플레이트 판단 + 요약_ko 생성 → apply 로 병합.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COLUMNS = ["paper_id", "DOI", "제목", "저자", "교신저자", "연도", "저널", "저널약어", "권", "호", "페이지", "초록", "키워드",
           "원문상태", "본문 단어수", "SI 유무", "수집일", "수집 URL", "파일경로", "요약_ko"]
STATUS_KO = {"full": "전문", "abstract_only": "초록만", "human_required": "미수집(사용자 확인 필요)", "failed": "실패", "resolved": "미수집", "": "미수집",
             "pdf_missing": "전문(PDF 없음, 재시도 대상)", "out_of_scope": "범위밖-미수집"}
KEYWORD_RE = re.compile(r"(?im)^\s*(?:\*\*)?key\s*words?(?:\*\*)?\s*[:：][ \t]*(.*)$")
BAD_CHARS = ("\x00", "�", "ﬁ", "ﬂ", "ﬀ", "ﬃ", "ﬄ", "Ã©", "Ã¶", "â€")   # \x00: 2026-09-26 이전 추출본의 NUL


def one_line(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def read_registry(kb_root: Path) -> dict[str, dict]:
    p = kb_root / "collection_registry.csv"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8-sig", newline="") as f:
        return {r["paper_id"]: r for r in csv.DictReader(f)}


def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_frontmatter(md: str) -> dict:
    """source.md 머리의 YAML 비슷한 블록 (key: "value") → dict. 레거시 폴더(registry 없음) 메타 fallback."""
    if not md.startswith("---"):
        return {}
    end = md.find("\n---", 3)
    if end < 0:
        return {}
    out = {}
    for line in md[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith('"') and v.endswith('"') and len(v) >= 2:
                v = v[1:-1]
            out[k.strip()] = v
    return out


def count_words(md: str) -> int:
    body = md.split("## Full Text", 1)[-1] if "## Full Text" in md else md
    return len(re.findall(r"[A-Za-z가-힣0-9]+", body))


def find_keywords(md: str) -> str:
    """본문의 Keywords 줄. 같은 줄에 있으면 그대로, 비어 있으면 다음 줄들을 빈 줄이나 문장(단어 8개 이상·마침표로 끝남)이 나올 때까지 모은다(Elsevier PDF 는 한 줄에 하나씩). 구분자는 `; `."""
    head = md[:20000]
    m = KEYWORD_RE.search(head)
    if not m:
        return ""
    same = one_line(m.group(1))
    if same:
        parts = [p.strip(" .") for p in re.split(r"[;,·]|\s{2,}", same) if p.strip(" .")]
        return "; ".join(dict.fromkeys(parts))[:300]
    parts = []
    for line in head[m.end():].splitlines()[1:]:
        s = one_line(line).strip(" .;,")
        if not s or len(s.split()) >= 8 or s.endswith(".") or s.lower().startswith(("1.", "1 ", "introduction", "abstract", "##", "#")):
            break
        parts.extend(p.strip() for p in re.split(r"[;,]", s) if p.strip())
        if len(parts) >= 15:
            break
    return "; ".join(dict.fromkeys(parts))[:300]


def build_rows(kb_root: Path) -> tuple[list[dict], list[dict]]:
    reg = read_registry(kb_root)
    papers = kb_root / "papers"
    rows, checks = [], []
    seen_doi: dict[str, str] = {}
    ids = sorted({p.name for p in papers.glob("*") if p.is_dir()} | set(reg.keys()))
    for pid in ids:
        r = reg.get(pid, {})
        d = papers / pid
        sj = read_json(d / "source.json") if d.exists() else {}
        md = (d / "source.md").read_text(encoding="utf-8", errors="ignore") if (d / "source.md").exists() else ""
        pdf = d / "pdf" / f"{pid}.pdf"
        si = sorted((d / "pdf").glob(f"{pid}_SI*")) if (d / "pdf").exists() else []
        fm = read_frontmatter(md) if md else {}
        words = count_words(md) if md else 0
        access = sj.get("access_status") or fm.get("access_status") or ""
        status = r.get("status") or ("full" if access == "fulltext" else access)
        if access == "abstract_only":
            status = "abstract_only"
        if status in ("", "resolved") and (pdf.exists() or words >= 1500):
            status = "full"   # 레거시 폴더: 실물 기준
        def pick(*keys, default=""):
            for src in (r, sj, fm):
                for k in keys:
                    v = src.get(k)
                    if v and v not in ("[]", "{}", "None"):
                        return v if isinstance(v, str) else ("; ".join(v) if isinstance(v, list) else str(v))
            return default
        row = {
            "paper_id": pid, "DOI": pick("doi"), "제목": one_line(pick("title")),
            "저자": pick("authors"), "교신저자": pick("corresponding"),
            "연도": pick("year"), "저널": pick("journal"), "저널약어": pick("journal_abbrev"),
            "권": pick("volume"), "호": pick("issue"), "페이지": pick("pages"),
            "초록": one_line(pick("abstract")), "키워드": find_keywords(md) if md else "",
            "원문상태": STATUS_KO.get(status, status), "본문 단어수": words if status == "full" else "",
            "SI 유무": f"Y({len(si)})" if si else "N", "수집일": (sj.get("collected_at") or r.get("updated_at") or "")[:10],
            "수집 URL": sj.get("source_url") or r.get("landing_url") or "", "파일경로": str(pdf) if pdf.exists() else (str(d / "source.md") if md else ""),
            "요약_ko": "",
        }
        rows.append(row)
        # ---- 결정적 검수
        flags = []
        doi = row["DOI"]
        if not re.fullmatch(r"10\.\d{4,9}/\S+", doi or ""):
            flags.append("DOI 형식")
        if doi and doi.lower() in seen_doi:
            flags.append(f"DOI 중복({seen_doi[doi.lower()]})")
        seen_doi.setdefault(doi.lower(), pid)
        for k in ("제목", "연도", "저널"):
            if not row[k]:
                flags.append(f"{k} 누락")
        y = row["연도"]
        if y and not (1900 <= int(y) <= datetime.now().year + 1 if y.isdigit() else False):
            flags.append("연도 범위")
        if status == "full":
            if words < 1500:
                flags.append(f"전문인데 단어수 {words}")
            if not pdf.exists():
                flags.append("PDF 없음")
        if row["초록"] and (len(row["초록"]) < 200 or len(row["초록"]) > 5000):
            flags.append(f"초록 길이 {len(row['초록'])}")
        if not row["초록"] and status in ("full", "abstract_only"):
            flags.append("초록 없음")
        if any(ch in (row["제목"] + row["초록"] + md[:50000]) for ch in BAD_CHARS):
            flags.append("깨진 문자/합자")
        if row["파일경로"] and not Path(row["파일경로"]).exists():
            flags.append("파일 경로 없음")
        checks.append({"paper_id": pid, "flags": "; ".join(flags), "n_flags": len(flags)})
    return rows, checks


README_TEXT = """# 논문 색인 사용법 (Claude 용 5줄)
1. `index.csv` 가 색인이다. 한 행이 논문 한 편이고 제목·저자·연도·저널·초록·원문상태·파일경로가 있다. 먼저 이 파일을 읽어 관련 논문을 고른다.
2. 원문 텍스트는 `papers/{paper_id}/source.md` (본문), 원문 PDF 는 `papers/{paper_id}/pdf/{paper_id}.pdf`, SI 는 같은 폴더의 `{paper_id}_SI*` 파일(pdf·docx 등)이다.
3. 키워드로 훑을 때는 `papers/*/source.md` 를 Grep 한다. 몇 편을 읽을지는 질문에 맞춰 판단한다 (강제 규칙 없음).
4. 원문상태가 "초록만" 이면 구독 밖이라 초록만 있고, "미수집(사용자 확인 필요)" 는 사용자와 함께 `sci_collect.py assist` 로 받는다.
5. 새 논문을 받으려면 DOI 를 `sci_collect.py resolve/collect` 에 넣고, 끝나면 `sci_index.py build` 로 색인을 다시 만든다.
"""


def cmd_build(args) -> None:
    kb_root = Path(args.kb_root).resolve()
    rows, checks = build_rows(kb_root)
    out = kb_root / "index.csv"
    existing = {}
    if out.exists():   # 기존 요약_ko 보존
        with open(out, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("요약_ko"):
                    existing[r["paper_id"]] = r["요약_ko"]
    for r in rows:
        r["요약_ko"] = existing.get(r["paper_id"], "")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    with open(kb_root / "index_check.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["paper_id", "flags", "n_flags"]); w.writeheader(); w.writerows(checks)
    (kb_root / "README.md").write_text(README_TEXT, encoding="utf-8")
    st = {}
    for r in rows:
        st[r["원문상태"]] = st.get(r["원문상태"], 0) + 1
    flagged = [c for c in checks if c["n_flags"]]
    print(f"index.csv: {len(rows)}행 — " + ", ".join(f"{k} {v}" for k, v in st.items()))
    print(f"index_check.csv: flag 있는 논문 {len(flagged)}편" + (" → " + "; ".join(f"{c['paper_id']}: {c['flags']}" for c in flagged[:12]) if flagged else ""))
    print(f"요약_ko 채움 {sum(1 for r in rows if r['요약_ko'])}/{len(rows)} (비어 있으면 Claude 검수 패스 후 apply)")


def cmd_apply(args) -> None:
    """gists csv: paper_id, 요약_ko[, check_flags] — Claude 가 작성. index.csv 의 요약_ko 채우고 flag 는 index_check 에 추가."""
    kb_root = Path(args.kb_root).resolve()
    out = kb_root / "index.csv"
    with open(out, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    with open(args.gists, encoding="utf-8-sig", newline="") as f:
        gists = {r["paper_id"]: r for r in csv.DictReader(f)}
    n = 0
    for r in rows:
        g = gists.get(r["paper_id"])
        if g and g.get("요약_ko"):
            r["요약_ko"] = one_line(g["요약_ko"])[:200]; n += 1
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
    chk = kb_root / "index_check.csv"
    if chk.exists() and any(g.get("check_flags") for g in gists.values()):
        with open(chk, encoding="utf-8-sig", newline="") as f:
            checks = list(csv.DictReader(f))
        for c in checks:
            g = gists.get(c["paper_id"])
            if g and g.get("check_flags"):
                c["flags"] = "; ".join(x for x in [c["flags"], "LLM: " + one_line(g["check_flags"])] if x)
                c["n_flags"] = str(len([x for x in c["flags"].split(";") if x.strip()]))
        with open(chk, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["paper_id", "flags", "n_flags"]); w.writeheader(); w.writerows(checks)
    print(f"요약_ko 병합 {n}건 → {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="sci_index — 논문 색인 CSV")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("--kb-root", required=True)
    p = sub.add_parser("apply"); p.add_argument("--kb-root", required=True); p.add_argument("--gists", required=True)
    args = ap.parse_args()
    {"build": cmd_build, "apply": cmd_apply}[args.cmd](args)


if __name__ == "__main__":
    main()
