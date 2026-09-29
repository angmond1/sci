#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci_index.py — 수집 논문 검색용 색인 (CSV, LLM 없음).

    python sci_index.py build --kb-root <dir>              # index.csv + index_check.csv + README.md (편수와 관계없이 몇 초)

index.csv 열 (2026-09-18 확정): paper_id, DOI, 웹페이지(https://doi.org/DOI, 2026-09-27), 제목, 저자(6명 이하 전원 / 7명 이상 앞3+뒤3), 교신저자,
  연도, 저널, 저널약어, 권, 호, 페이지, 초록, 키워드(있을 때만), 원문상태, 본문 단어수, SI 유무, 수집일, 수집 URL, 파일경로
  + 참고문헌 번호: 참고문헌 수집(refs → resolve)이면 맨 왼쪽 열. 원 논문의 참고문헌 목록 번호 (2026-09-27 사용자 지시)
  + 한줄요약: 사용자가 원할 때만 sci-tldr(sci_tldr.py)이 붙이는 열. build 는 있으면 그대로 두고, 옛 열 이름 요약_ko 는 한줄요약으로 옮긴다.
재료: collection_registry.csv (resolve 메타) + papers/{id}/source.json + source.md + pdf/ 파일 실물. UTF-8 BOM (엑셀 한글 OK), 초록은 한 줄.
검수(결정적): index_check.csv — DOI 형식/중복, 필수 항목 누락, 상태-단어수 정합, 파일 존재, 깨진 문자, 초록 길이, 연도 범위.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COLUMNS = ["paper_id", "DOI", "웹페이지", "제목", "저자", "교신저자", "연도", "저널", "저널약어", "권", "호", "페이지", "초록", "키워드",
           "원문상태", "본문 단어수", "SI 유무", "수집일", "수집 URL", "파일경로"]
TLDR_COL = "한줄요약"          # sci-tldr 이 붙이는 열 (사용자가 원할 때만, 2026-09-27 사용자 결정)
REF_COL = "참고문헌 번호"      # 참고문헌 수집일 때만 맨 왼쪽 열 (레지스트리 ref_no, 0 = 번호 모름 '-')
OLD_TLDR_COLS = ("요약_ko",)   # 옛 열 이름 — 읽을 때 한줄요약으로 옮긴다


def read_index(path: Path) -> tuple[list[dict], bool]:
    """index.csv 읽기. 옛 요약_ko 열은 한줄요약으로 옮긴다. (행, 한줄요약 열이 있었는지)"""
    if not path.exists():
        return [], False
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames or []
        rows = list(rd)
    has = TLDR_COL in fields or any(c in fields for c in OLD_TLDR_COLS)
    for r in rows:
        if not r.get(TLDR_COL):
            for c in OLD_TLDR_COLS:
                if r.get(c):
                    r[TLDR_COL] = r[c]
        for c in OLD_TLDR_COLS:
            r.pop(c, None)
    return rows, has


def write_index(path: Path, rows: list[dict], with_tldr: bool) -> None:
    cols = ([REF_COL] if any(r.get(REF_COL) for r in rows) else []) + COLUMNS + ([TLDR_COL] if with_tldr else [])
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
STATUS_KO = {"full": "전문", "abstract_only": "초록만", "human_required": "미수집(사용자 확인 필요)", "failed": "실패", "resolved": "미수집", "": "미수집",
             "pdf_missing": "전문(PDF 없음, 재시도 대상)", "out_of_scope": "범위밖-미수집",
             "fulltext": "전문", "preview": "초록만(미리보기)",   # 옛 수집기의 access_status (2026-09-27 옛 KB 시험)
             "web_text": "전문(웹 본문, PDF 없음)",   # PDF 없는 웹 전용 글의 본문·참고문헌 (2026-09-27)
             "web_text_pdffail": "전문(웹 본문, PDF 받기 실패)"}   # PDF 받기에 여러 번 실패해 웹 본문을 저장 (method 로 가림)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>,;]+")
KEYWORD_RE = re.compile(r"(?im)^\s*(?:\*\*)?key\s*words?(?:\*\*)?\s*[:：][ \t]*(.*)$")
BAD_CHARS = ("\x00", "�", "ﬁ", "ﬂ", "ﬀ", "ﬃ", "ﬄ", "Ã©", "Ã¶", "â€", "Â°", "â\x80")   # \x00: 2026-09-26 이전 추출본의 NUL, Ã©·Â°: 웹페이지 인코딩 깨짐(2026-09-27)
# 저널명이 없는 프리프린트 (Crossref 에 container-title 이 없다) — 저널약어를 저널명으로 쓴다
PREPRINT_NAMES = {"ChemRxiv", "arXiv", "bioRxiv", "medRxiv", "ResSq", "SSRN", "OSF", "Preprint"}
# 초록 제목: 한 줄에 제목만(Abstract, A B S T R A C T, Summary) 또는 줄 앞 "Abstract—"·"ABSTRACT:" (대문자로 시작할 때만)
ABS_HEAD_RE = re.compile(r"(?m)^[ \t#*_]*(?:(?i:abstract|a b s t r a c t)|Summary|SUMMARY)[ \t*_:.]*$|^[ \t#*_]*(?:Abstract|ABSTRACT)[ \t]*[:—–.-][ \t]*(?=\S)")
ABS_STOP_RE = re.compile(r"(?i)^\s*(#{1,6}\s|key\s*words?\b|index terms\b|(?:1\.?|i\.)?\s*introduction\b|©|\(c\)\s*\d{4}|copyright\b|\*\s*corresponding|e-?mail\b"
                         r"|https?://doi\.org|received\b|accepted\b|available online\b|article history\b|graphical abstract\b|highlights\b|cite this\b|you have full access\b)")


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
        raw = one_line(line)
        if not raw or len(raw.split()) >= 8 or raw.endswith(".") or raw.lower().startswith(("1.", "1 ", "introduction", "abstract", "##", "#")):
            break
        s = raw.strip(" .;,")
        parts.extend(p.strip() for p in re.split(r"[;,]", s) if p.strip())
        if len(parts) >= 15:
            break
    return "; ".join(dict.fromkeys(parts))[:300]


BOILER_RE = re.compile(r"all rights reserved|publication history|opens in new window|accepted after revision|published online|"
                       r"this article is distributed|creative commons|downloaded from|cookie|sign in|log in|purchase", re.I)


def looks_boilerplate(ab: str) -> bool:
    """초록 칸에 초록 대신 사이트 문구가 들어온 것 (2026-09-27 Thieme: 'All articles of this category … Publication History …
    © 2023. Thieme. All rights reserved'). 문구 두 가지 이상이 있고 문장이 적으면 보일러플레이트로 본다."""
    if not ab:
        return False
    hits = len(set(m.group(0).lower() for m in BOILER_RE.finditer(ab)))
    return hits >= 2 and ab.count(". ") < 4


def looks_citation(ab: str, title: str, journal: str = "") -> bool:
    """초록 칸에 서지 인용문이 들어온 것 (2026-09-27 Codex 검증: Oxford 3편이 '저자; 제목, National Science Review, , nwaf110,
    https://doi.org/10.…' 155자). 짧고(600자 미만) 제목 앞부분이 그대로 있고 DOI 주소나 저널명이 함께 있으면 초록이 아니다."""
    if not ab or len(ab) >= 600:
        return False
    norm = lambda s: re.sub(r"\W+", " ", s or "").strip().lower()
    a, tt = norm(ab), norm(title)
    if not tt or tt[:40] not in a:
        return False
    return bool(re.search(r"doi\.org/10\.|\bdoi:?\s*10\.", ab, re.I)) or (bool(journal) and norm(journal) in a)


SHORT_KIND_RE = re.compile(r"(?m)^[ \t]*(RESEARCH HIGHLIGHTS?|HIGHLIGHTS?|NEWS (?:AND|&) VIEWS|EDITORIAL|COMMENTARY|PERSPECTIVE|VIEWPOINT|CORRESPONDENCE|BOOK REVIEW|IN BRIEF)[ \t]*$")


def short_kind(md: str) -> str:
    """짧은 기사 종류: 본문 첫머리(400자 안) 한 줄짜리 대문자 머리표 RESEARCH HIGHLIGHT·EDITORIAL 등 (2026-09-27 Oxford 1쪽 하이라이트). 없으면 ''.
    초록 제목이 있으면 연구 논문이다 — 첫 쪽만 온 연구 논문을 짧은 기사로 보지 않는다."""
    body = md.split("## Full Text", 1)[-1]
    m = SHORT_KIND_RE.search(body[:400])
    return m.group(1).title() if m and not ABS_HEAD_RE.search(body[:3000]) else ""


def abstract_from_body(md: str) -> str:
    """초록 칸이 비었을 때 본문의 초록 절을 쓴다 (2026-09-27 연습: Springer·Elsevier 는 OpenAlex 에 초록이 없어 96편 중 12편이 빈칸).
    틀린 초록보다 빈칸이 낫다: 두 단이 섞였거나 참고문헌·각주가 끼었거나 단어가 붙은 추출본은 버린다 (옛 KB 648편 시험에서 가려냄)."""
    body = md.split("## Full Text", 1)[-1] if "## Full Text" in md else md
    head = body[:12000]
    m = ABS_HEAD_RE.search(head)
    if not m:
        return ""
    out: list[str] = []
    for line in head[m.end():].splitlines():
        s = line.strip()
        if not s:
            if sum(len(x) for x in out) > 300:
                break          # 빈 줄 = 문단 끝
            continue
        if s.startswith("## Page"):
            if out:
                break
            continue
        if ABS_STOP_RE.match(s):
            break
        out.append(s)
        if sum(len(x) for x in out) > 3000:
            break
    text = one_line(" ".join(out)).rstrip("■ ").strip()
    if not (300 <= len(text) <= 3000) or text.count(". ") < 2:
        return ""
    if not re.match(r"[A-Z0-9(\[\"'“]", text) or not re.search(r"[.!?)\]]$", text):
        return ""   # 문장 가운데서 시작하거나 끝나지 않았다 (두 단 섞임·잘림)
    if len(re.findall(r"\[\d[\d,a-z–-]*\]", text)) > 2 or re.search(r"\(\d+\)\s*[A-Z][a-z]+,\s*[A-Z]\.", text):
        return ""   # 인용 번호·참고문헌이 끼었다
    if any(len(w) > 30 for w in re.findall(r"[A-Za-z]+", text)):
        return ""   # 띄어쓰기가 사라진 추출본
    return text


def pdf_pages(pdf: Path, sj: dict) -> int:
    """본문 PDF 쪽수: source.json 의 pdf_pages, 없으면(옛 폴더) PDF 를 열어 센다. 모르면 0."""
    try:
        n = int(sj.get("pdf_pages") or 0)
    except (TypeError, ValueError):
        n = 0
    if n or not pdf.exists():
        return n
    try:
        import fitz
        with fitz.open(pdf) as doc:
            return doc.page_count
    except Exception:
        return 0


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
        if access == "abstract_only" and status != "out_of_scope":
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
            REF_COL: ("-" if str(r.get("ref_no")) == "0" else str(r.get("ref_no"))) if r.get("ref_no") not in (None, "") else "",
            "제목": one_line(pick("title")),
            "저자": pick("authors"), "교신저자": pick("corresponding"),
            "연도": pick("year"), "저널": pick("journal"), "저널약어": pick("journal_abbrev"),
            "권": pick("volume"), "호": pick("issue"), "페이지": pick("pages"),
            "초록": one_line(pick("abstract")), "키워드": find_keywords(md) if md else "",
            "원문상태": STATUS_KO["web_text_pdffail"] if status == "web_text" and r.get("method") == "web_text_pdffail" else STATUS_KO.get(status, status),
            "본문 단어수": words if status in ("full", "web_text") else "",
            "SI 유무": f"Y({len(si)})" if si else "N", "수집일": (sj.get("collected_at") or r.get("updated_at") or "")[:10],
            "수집 URL": sj.get("source_url") or r.get("landing_url") or "", "파일경로": str(pdf) if pdf.exists() else (str(d / "source.md") if md else ""),
        }
        # 논문 웹페이지: DOI 주소는 늘 그 논문 페이지로 간다 (수집 URL 은 API·PDF 주소일 때가 있다, 2026-09-27 사용자 지시)
        row["웹페이지"] = f"https://doi.org/{row['DOI']}" if re.fullmatch(r"10\.\d{4,9}/\S+", row["DOI"] or "") else (r.get("landing_url") or "")
        if not row["저널"] and row["저널약어"] in PREPRINT_NAMES:
            row["저널"] = row["저널약어"]   # 프리프린트는 서버 이름이 저널명 (2026-09-27 ChemRxiv 4편 "저널 누락")
        abs_from_body = boiler = cite = False
        if looks_boilerplate(row["초록"]):
            row["초록"], boiler = "", True   # 사이트 문구는 초록이 아니다 — 빼고 본문의 초록 절에서 채워 본다
        elif looks_citation(row["초록"], row["제목"], row["저널"]):
            row["초록"], cite = "", True     # 서지 인용문도 초록이 아니다 (진짜 초록이 없으면 '초록 없음')
        if not row["초록"] and status in ("full", "web_text") and md:
            row["초록"] = abstract_from_body(md)
            abs_from_body = bool(row["초록"])
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
                # 짧은 기사(뉴스·하이라이트·학회 초록, 2~4쪽)는 쪽당 단어가 정상이면 잘린 것이 아니다 (2026-09-27 연습 4편: 쪽당 250~700 단어).
                # 한 쪽짜리(첫 쪽만 온 것)나 쪽당 단어가 적은 것(추출 실패)만 알린다.
                # 첫머리에 RESEARCH HIGHLIGHT·EDITORIAL 같은 머리표가 있는 짧은 기사는 쪽수와 관계없이 종류만 알린다 (Codex 검증: Oxford 1쪽 하이라이트).
                n_pages = pdf_pages(pdf, sj)
                kind = short_kind(md)
                if kind and words >= 200 * max(n_pages, 1):
                    flags.append(f"짧은 기사({kind}" + (f", {n_pages}쪽)" if n_pages else ")"))
                elif not (2 <= n_pages <= 4 and words >= 200 * n_pages):
                    flags.append(f"전문인데 단어수 {words}" + (f" (PDF {n_pages}쪽)" if n_pages else ""))
            if not pdf.exists():
                flags.append("PDF 없음")
        if row["초록"] and (len(row["초록"]) < 200 or len(row["초록"]) > 5000):
            flags.append(f"초록 길이 {len(row['초록'])}")
        if not row["초록"] and status in ("full", "web_text", "abstract_only"):
            flags.append("초록 없음")
        if boiler:
            flags.append("초록 보일러플레이트(뺌)")
        if cite:
            flags.append("초록 아님(서지 인용문, 뺌)")
        if abs_from_body:
            flags.append("초록 본문에서 채움")   # 두 단 섞임 등은 버렸다. 제목과 맞는지 한 번 보면 좋다
        if any(ch in (row["제목"] + row["초록"] + md[:50000]) for ch in BAD_CHARS):
            flags.append("깨진 문자/합자")
        if row["파일경로"] and not Path(row["파일경로"]).exists():
            flags.append("파일 경로 없음")
        checks.append({"paper_id": pid, "flags": "; ".join(flags), "n_flags": len(flags)})
    return rows, checks


README_TEXT = """# 논문 색인 사용법 (에이전트용 5줄)
1. `index.csv` 가 색인이다. 한 행이 논문 한 편이고 제목·저자·연도·저널·초록·키워드·원문상태·웹페이지(논문 페이지 주소)·파일경로가 있다(사용자가 원했으면 한국어 한줄요약 열, 참고문헌 수집이면 맨 왼쪽에 원 논문의 참고문헌 번호 열도 있다). 먼저 이 파일로 관련 논문을 고른다. 크면 제목·초록·키워드를 Grep 한다.
2. 원문 텍스트는 `papers/{paper_id}/source.md` (본문), 원문 PDF 는 `papers/{paper_id}/pdf/{paper_id}.pdf`, SI 는 같은 폴더의 `{paper_id}_SI*` 파일(pdf·docx 등)이다.
3. 키워드로 훑을 때는 `papers/*/source.md` 를 Grep 한다. 몇 편을 읽을지는 질문에 맞춰 판단한다 (강제 규칙 없음).
4. 원문상태가 "초록만" 이면 구독 밖이라 초록만 있고, "전문(웹 본문, PDF 없음)" 은 PDF 가 없는 웹 전용 글이라 본문·참고문헌이 source.md 에만 있다. "미수집(사용자 확인 필요)" 는 사용자와 함께 `sci_collect.py assist` 로 받는다.
5. 새 논문을 받으려면 DOI 를 `sci_collect.py resolve/collect` 에 넣고, 끝나면 `sci_index.py build` 로 색인을 다시 만든다.
"""


def cmd_build(args) -> None:
    kb_root = Path(args.kb_root).resolve()
    if not kb_root.exists() or not ((kb_root / "papers").exists() or (kb_root / "collection_registry.csv").exists()):
        print(f"논문 폴더가 아닙니다 (papers/ 나 collection_registry.csv 가 없음): {kb_root}"); raise SystemExit(1)
    rows, checks = build_rows(kb_root)
    out = kb_root / "index.csv"
    old_rows, with_tldr = read_index(out)   # sci-tldr 이 붙인 한줄요약은 build 를 다시 해도 남긴다
    existing = {r["paper_id"]: r.get(TLDR_COL, "") for r in old_rows if r.get(TLDR_COL)}
    if with_tldr:
        for r in rows:
            r[TLDR_COL] = existing.get(r["paper_id"], "")
    chk_path = kb_root / "index_check.csv"
    if chk_path.exists():   # 검수 패스가 붙인 'LLM: …' flag 는 build 를 다시 해도 남긴다
        with open(chk_path, encoding="utf-8-sig", newline="") as f:
            llm = {c["paper_id"]: [x.strip() for x in c.get("flags", "").split(";") if x.strip().startswith("LLM:")] for c in csv.DictReader(f)}
        for c in checks:
            keep = llm.get(c["paper_id"]) or []
            if keep:
                c["flags"] = "; ".join(x for x in [c["flags"]] + keep if x)
                c["n_flags"] = len([x for x in c["flags"].split(";") if x.strip()])
    write_index(out, rows, with_tldr)
    with open(kb_root / "index_check.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["paper_id", "flags", "n_flags"]); w.writeheader(); w.writerows(checks)
    (kb_root / "README.md").write_text(README_TEXT, encoding="utf-8")
    st = {}
    for r in rows:
        st[r["원문상태"]] = st.get(r["원문상태"], 0) + 1
    flagged = [c for c in checks if c["n_flags"]]
    print(f"index.csv: {len(rows)}행 — " + ", ".join(f"{k} {v}" for k, v in st.items()))
    print(f"index_check.csv: flag 있는 논문 {len(flagged)}편" + (" → " + "; ".join(f"{c['paper_id']}: {c['flags']}" for c in flagged[:12]) if flagged else ""))
    if with_tldr:
        print(f"한줄요약 {sum(1 for r in rows if r.get(TLDR_COL))}/{len(rows)} — 빈 행은 사용자가 원할 때만 sci-tldr  ▼・ᴥ・▼")
    else:
        print("한줄요약: 없음 — 사용자가 원할 때만 sci-tldr 로 붙인다 (편수와 관계없이 물어본다)  ▼・ᴥ・▼")


def body_excerpt(md: str, n: int = 1500, title: str = "") -> str:
    """초록이 없거나 짧을 때 요약 재료: 머리 블록·제목 줄·참고문헌을 뺀 본문 앞부분.
    본문 앞쪽에 이 논문 제목이 있으면 그 자리부터 자른다. Cell Press Preview 처럼 앞 기사의 끝과 한 쪽을 나눠 쓰는 PDF 는
    첫 쪽이 다른 기사 글로 시작해 요약이 빗나간다 (2026-09-27 색인 시험 '제목-초록 불일치')."""
    body = md.split("## Full Text", 1)[-1] if "## Full Text" in md else md   # 수집 URL·텍스트 소스 같은 머리 줄은 뺀다
    if body.startswith("---"):
        end = body.find("\n---", 3)
        body = body[end + 4:] if end > 0 else body
    body = re.split(r"(?im)^#+\s*(references|bibliography|참고\s*문헌)\s*$", body)[0]
    body = re.sub(r"(?m)^#.*$", " ", body)
    words = re.findall(r"[A-Za-z0-9]+", title or "")[:6]
    if len(words) >= 3:
        m = re.search(r"[^A-Za-z0-9]+".join(map(re.escape, words)), body[:12000], re.I)
        if m and m.start() > 200:
            body = body[m.start():]
    return one_line(body)[:n]


def main() -> None:
    ap = argparse.ArgumentParser(description="sci_index — 논문 색인 CSV")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("--kb-root", required=True)
    for old in ("prep", "apply"):   # 2026-09-27 한 줄 요약은 sci-tldr 로 옮김 — 옛 명령을 부르면 새 명령을 알려 준다
        p = sub.add_parser(old); p.add_argument("--kb-root"); p.add_argument("rest", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    if args.cmd in ("prep", "apply"):
        print(f"한 줄 요약은 sci-tldr 로 옮겼다: python {Path(__file__).with_name('sci_tldr.py')} {args.cmd} --kb-root <root>  (sci-tldr 지침)")
        raise SystemExit(2)
    cmd_build(args)


if __name__ == "__main__":
    main()
