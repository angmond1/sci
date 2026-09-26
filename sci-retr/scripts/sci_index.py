#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci_index.py — 수집 논문 검색용 색인 (CSV, LLM 없음).

    python sci_index.py build --kb-root <dir>              # index.csv + index_check.csv + README.md
    python sci_index.py prep  --kb-root <dir> [--size 35]  # 요약 패스용 묶음 파일(_collect/index_batch_<n>.md) — 에이전트는 이 파일만 읽는다
    python sci_index.py apply --kb-root <dir> --gists <csv …> # 에이전트가 만든 요약_ko / 검수 flag 를 index.csv 에 병합 (여러 파일·와일드카드 가능)

index.csv 열 (2026-09-18 확정): paper_id, DOI, 제목, 저자(6명 이하 전원 / 7명 이상 앞3+뒤3), 교신저자, 연도, 저널, 저널약어, 권, 호, 페이지,
  초록, 키워드(있을 때만), 원문상태, 본문 단어수, SI 유무, 수집일, 수집 URL, 파일경로, 요약_ko
재료: collection_registry.csv (resolve 메타) + papers/{id}/source.json + source.md + pdf/ 파일 실물. UTF-8 BOM (엑셀 한글 OK), 초록은 한 줄.
검수 1단계(결정적): index_check.csv — DOI 형식/중복, 필수 항목 누락, 상태-단어수 정합, 파일 존재, 깨진 문자, 초록 길이, 연도 범위.
검수 2단계(LLM, sonnet): Claude 가 제목-초록 정합·잘림·보일러플레이트 판단 + 요약_ko 생성 → apply 로 병합.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COLUMNS = ["paper_id", "DOI", "제목", "저자", "교신저자", "연도", "저널", "저널약어", "권", "호", "페이지", "초록", "키워드",
           "원문상태", "본문 단어수", "SI 유무", "수집일", "수집 URL", "파일경로", "요약_ko"]
STATUS_KO = {"full": "전문", "abstract_only": "초록만", "human_required": "미수집(사용자 확인 필요)", "failed": "실패", "resolved": "미수집", "": "미수집",
             "pdf_missing": "전문(PDF 없음, 재시도 대상)", "out_of_scope": "범위밖-미수집",
             "fulltext": "전문", "preview": "초록만(미리보기)"}   # 옛 수집기의 access_status (2026-09-27 옛 KB 시험)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>,;]+")
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


def main_pdf(d: Path, pid: str) -> Path:
    """본문 PDF: pdf/{pid}.pdf, 없으면 pdf/ 나 폴더 바로 아래의 SI 가 아닌 가장 큰 PDF (옛 폴더의 main.pdf 등). 없으면 pdf/{pid}.pdf 경로."""
    std = d / "pdf" / f"{pid}.pdf"
    if std.exists():
        return std
    cands = [p for p in list((d / "pdf").glob("*.pdf")) + list(d.glob("*.pdf")) if not re.search(r"(^|[_-])SI([_.-]|$)", p.stem, re.I)] if d.exists() else []
    return max(cands, key=lambda p: p.stat().st_size) if cands else std


def fix_doi(doi: str, *texts: str) -> str:
    """DOI 칸이 DOI 형식이 아니면(옛 수집기의 '10051784' 등) 원 주소·본문 머리에서 DOI 를 되살린다."""
    if re.fullmatch(r"10\.\d{4,9}/\S+", doi or ""):
        return doi
    for s in texts:
        m = DOI_RE.search(s or "")
        if m:
            return m.group(0).rstrip(".)]}")
    return doi


def build_rows(kb_root: Path) -> tuple[list[dict], list[dict]]:
    reg = read_registry(kb_root)
    papers = kb_root / "papers"
    rows, checks = [], []
    seen_doi: dict[str, str] = {}
    # 논문 폴더로 볼 것: 레지스트리에 있거나 source.json·source.md·pdf/ 가 있는 폴더 (잡폴더는 뺀다, 2026-09-27)
    dirs = {p.name for p in papers.glob("*") if p.is_dir() and ((p / "source.json").exists() or (p / "source.md").exists() or (p / "pdf").exists()
                                                                  or any(p.glob("*.pdf")))} if papers.exists() else set()
    ids = sorted(dirs | set(reg.keys()))
    for pid in ids:
        r = reg.get(pid, {})
        d = papers / pid
        sj = read_json(d / "source.json") if d.exists() else {}
        md = (d / "source.md").read_text(encoding="utf-8", errors="ignore") if (d / "source.md").exists() else ""
        pdf = main_pdf(d, pid)
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
            "paper_id": pid, "DOI": fix_doi(pick("doi"), sj.get("source_entry", ""), sj.get("final_url", ""), sj.get("requested_url", ""), md[:3000]),
            "제목": one_line(pick("title")),
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


README_TEXT = """# 논문 색인 사용법 (에이전트용 5줄)
1. `index.csv` 가 색인이다. 한 행이 논문 한 편이고 제목·저자·연도·저널·초록·원문상태·파일경로가 있다. 먼저 이 파일을 읽어 관련 논문을 고른다.
2. 원문 텍스트는 `papers/{paper_id}/source.md` (본문), 원문 PDF 는 `papers/{paper_id}/pdf/{paper_id}.pdf`, SI 는 같은 폴더의 `{paper_id}_SI*` 파일(pdf·docx 등)이다.
3. 키워드로 훑을 때는 `papers/*/source.md` 를 Grep 한다. 몇 편을 읽을지는 질문에 맞춰 판단한다 (강제 규칙 없음).
4. 원문상태가 "초록만" 이면 구독 밖이라 초록만 있고, "미수집(사용자 확인 필요)" 는 사용자와 함께 `sci_collect.py assist` 로 받는다.
5. 새 논문을 받으려면 DOI 를 `sci_collect.py resolve/collect` 에 넣고, 끝나면 `sci_index.py build` 로 색인을 다시 만든다.
"""


def cmd_build(args) -> None:
    kb_root = Path(args.kb_root).resolve()
    if not kb_root.exists() or not ((kb_root / "papers").exists() or (kb_root / "collection_registry.csv").exists()):
        print(f"논문 폴더가 아닙니다 (papers/ 나 collection_registry.csv 가 없음): {kb_root}"); raise SystemExit(1)
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
    chk_path = kb_root / "index_check.csv"
    if chk_path.exists():   # 검수 패스가 붙인 'LLM: …' flag 는 build 를 다시 해도 남긴다
        with open(chk_path, encoding="utf-8-sig", newline="") as f:
            llm = {c["paper_id"]: [x.strip() for x in c.get("flags", "").split(";") if x.strip().startswith("LLM:")] for c in csv.DictReader(f)}
        for c in checks:
            keep = llm.get(c["paper_id"]) or []
            if keep:
                c["flags"] = "; ".join(x for x in [c["flags"]] + keep if x)
                c["n_flags"] = len([x for x in c["flags"].split(";") if x.strip()])
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
    print(f"요약_ko 채움 {sum(1 for r in rows if r['요약_ko'])}/{len(rows)} (비어 있으면 검수·요약 패스 후 apply)  ▼・ᴥ・▼")


def body_excerpt(md: str, n: int = 1500) -> str:
    """초록이 없거나 짧을 때 요약 재료: 머리 블록·제목 줄·참고문헌을 뺀 본문 앞부분."""
    body = md
    if body.startswith("---"):
        end = body.find("\n---", 3)
        body = body[end + 4:] if end > 0 else body
    body = re.split(r"(?im)^#+\s*(references|bibliography|참고\s*문헌)\s*$", body)[0]
    body = re.sub(r"(?m)^#.*$", " ", body)
    return one_line(body)[:n]


def cmd_prep(args) -> None:
    """요약 패스 준비: 요약_ko 가 빈 행을 묶음 파일로 나눈다. 에이전트는 index.csv·source.md 를 따로 읽지 않고 이 파일만 읽는다 (LLM 사용량 절감, 2026-09-27)."""
    kb_root = Path(args.kb_root).resolve()
    out = kb_root / "index.csv"
    if not out.exists():
        print(f"index.csv 가 없습니다. 먼저 build: {out}"); raise SystemExit(1)
    with open(out, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    chk_path = kb_root / "index_check.csv"
    chk = {}
    if chk_path.exists():
        with open(chk_path, encoding="utf-8-sig", newline="") as f:
            chk = {c["paper_id"]: c.get("flags", "") for c in csv.DictReader(f)}
    todo = [r for r in rows if args.all or not r.get("요약_ko")]
    work = kb_root / "_collect"
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("index_batch_*.md"):
        old.unlink()
    if not todo:
        print("요약_ko 가 빈 행이 없습니다 (--all 이면 전체 다시)."); return
    size = max(5, args.size)
    batches = [todo[i:i + size] for i in range(0, len(todo), size)]
    # 이미 있는 결과 파일(index_gists_N.csv)을 덮어쓰지 않게 그 다음 번호부터 붙인다 (병합 전에 prep 을 다시 돌려도 안전)
    start = 1 + max([int(m.group(1)) for g in work.glob("index_gists_*.csv") if (m := re.fullmatch(r"index_gists_(\d+)\.csv", g.name))] or [0])
    for bi, batch in enumerate(batches, start):
        lines = [f"# 색인 검수·요약 묶음 {bi} ({bi - start + 1}/{len(batches)}) — {len(batch)}편", "",
                 "각 논문의 요약_ko(한국어 한 문장, 200자 이내, 무엇을 했고 무엇을 찾았는지)와 check_flags 를 정해",
                 f"`{work / f'index_gists_{bi}.csv'}` 에 쓴다 (열: paper_id, 요약_ko, check_flags / UTF-8 BOM / 파이썬 csv 모듈).", ""]
        for r in batch:
            ab = r.get("초록", "")
            lines += [f"## {r['paper_id']}", f"- 제목: {r['제목']}", f"- 연도·저널: {r['연도']} {r['저널']}",
                      f"- 원문상태: {r['원문상태']} / 본문 단어수: {r['본문 단어수'] or '-'}",
                      f"- 결정적 flag: {chk.get(r['paper_id']) or '없음'}", f"- 초록: {ab or '(없음)'}"]
            if len(ab) < 200:
                src = kb_root / "papers" / r["paper_id"] / "source.md"
                ex = body_excerpt(src.read_text(encoding="utf-8", errors="ignore")) if src.exists() else ""
                lines.append(f"- 본문 앞부분(초록 대신): {ex or '(본문 없음 — 제목으로만 요약하고 check_flags 에 적는다)'}")
            lines.append("")
        (work / f"index_batch_{bi}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"요약 대상 {len(todo)}편 → 묶음 {len(batches)}개 ({size}편씩): {work / f'index_batch_{start}.md'} … index_batch_{start + len(batches) - 1}.md")
    print(f"하위 에이전트 하나가 묶음 파일 하나만 읽고 index_gists_<n>.csv 를 쓴다 (sci-index 지침 5.3). 다 되면: apply --kb-root <root> --gists \"{work / 'index_gists_*.csv'}\"")


def read_gists(path: str) -> list[dict]:
    """검수 결과 CSV. UTF-8(BOM 있든 없든), 안 되면 cp949 로 읽는다."""
    for enc in ("utf-8-sig", "cp949"):
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    return []


def cmd_apply(args) -> None:
    """gists csv: paper_id, 요약_ko[, check_flags] — Claude 가 작성. index.csv 의 요약_ko 채우고 flag 는 index_check 에 추가."""
    kb_root = Path(args.kb_root).resolve()
    out = kb_root / "index.csv"
    if not out.exists():
        print(f"index.csv 가 없습니다. 먼저 build: {out}"); raise SystemExit(1)
    files = []
    for g in args.gists:
        files += sorted(glob.glob(g)) or ([g] if Path(g).exists() else [])
    if not files:
        print(f"검수 결과 파일이 없습니다: {' '.join(args.gists)}"); raise SystemExit(1)
    with open(out, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    gists = {}
    for fpath in files:
        for r in read_gists(fpath):
            if r.get("paper_id"):
                gists[r["paper_id"].strip()] = r
    known = {r["paper_id"] for r in rows}
    unknown = sorted(set(gists) - known)
    if unknown:
        print(f"!! index.csv 에 없는 paper_id {len(unknown)}개는 건너뜀: {', '.join(unknown[:8])}")
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
    left = sum(1 for r in rows if not r.get("요약_ko"))
    print(f"요약_ko 병합 {n}건 (파일 {len(files)}개) → {out}" + (f" — 아직 빈 행 {left}개 (prep 을 다시 돌리면 빈 행만 묶는다)" if left else "") + "  ▼・ᴥ・▼")


def main() -> None:
    ap = argparse.ArgumentParser(description="sci_index — 논문 색인 CSV")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("--kb-root", required=True)
    p = sub.add_parser("prep"); p.add_argument("--kb-root", required=True); p.add_argument("--size", type=int, default=50, help="묶음당 편수 (50편이면 묶음 파일이 약 40KB 로 한 번에 읽힌다)"); p.add_argument("--all", action="store_true", help="요약이 있는 행도 다시")
    p = sub.add_parser("apply"); p.add_argument("--kb-root", required=True); p.add_argument("--gists", required=True, nargs="+", help="검수 결과 CSV (여러 개·와일드카드 가능)")
    args = ap.parse_args()
    {"build": cmd_build, "prep": cmd_prep, "apply": cmd_apply}[args.cmd](args)


if __name__ == "__main__":
    main()
