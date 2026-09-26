"""validate.py — collection 후 paper 무결성 검증 (sci-retr A1).

`references/collection_failure_patterns.md` 의 `validate_collected_paper()` 를
*실제 모듈* 로 구현. 그동안 SKILL.md/agent 가 "6가지 강제 검증"을 선언만 하고
runner.py 는 classify_content(길이 3-tier)만 실행하던 정책-구현 괴리를 해소한다.

호출 위치:
  - runner.finish_result()      — 자동 batch success 마킹 직전
  - manual_ingest.ingest_paper() — 수동 PDF ingest success 직전

PDF 처리는 fitz(pymupdf) 로 통일 (runner.py 와 동일 — pypdf/pdfminer 추가 의존성 회피).

검증 6종 (+ paywall fall-through):
  1. body length        (chars >= 5000 AND words >= 1500)
  2. section headers     (Methods/Results/Discussion/Conclusions/Experimental >= 2)
  3. reference ratio     (## References 이후가 본문보다 길면 reject)
  4. Elsevier 1-page preview (publisher=elsevier + page_count<=1 + chars<10k)
  4b. paywall fall-through   (paywall kw >=5 AND 본문 헤더 <2)
  5. DOI 매칭            (PDF 첫 페이지에 expected DOI 존재 확인; 없고 다른 DOI만 → 의심)
  6. replacement guard   (현재 source.md < 50% × backup → replacement_loss)
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    try:
        import pymupdf as fitz  # runner.py 와 동일 엔진 (옛 이름 fitz 는 경고를 찍는다)
    except ImportError:
        import fitz
except Exception:  # pragma: no cover
    fitz = None

# 본문 섹션 헤더 (2개 이상이면 본문 구조 인정)
SECTION_PATTERNS = [
    r"\bMethods?\b", r"\bResults?\b", r"\bDiscussion\b",
    r"\bConclusions?\b", r"\bExperimental\b",
]
# paywall / publisher furniture 키워드
PAYWALL_KW = (
    r"(purchase\s+access|subscribe\s+to|recommended\s+articles|cited\s+by|"
    r"institutional\s+access\s+required|sign\s+in\s+to\s+download)"
)
# 본문 키워드 (paywall fall-through 판정 시 본문 존재 여부)
BODY_KW = (
    r"(introduction|results?\s+and\s+discussion|experimental|method|"
    r"conclusion|materials?)"
)
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)")


def _pdf_pages_and_first_page(pdf_path: Path) -> tuple[int | None, str]:
    """(page_count, first_page_text). fitz 없거나 실패 시 (None, '')."""
    if fitz is None or not pdf_path.exists():
        return None, ""
    try:
        doc = fitz.open(str(pdf_path))
        n = doc.page_count
        first = doc[0].get_text("text") if n else ""
        doc.close()
        return n, first or ""
    except Exception:
        return None, ""


def _pdf_head_text(pdf_path: Path, n_pages: int = 2) -> str:
    """앞 n 쪽의 텍스트. fitz 없거나 실패 시 ''."""
    if fitz is None or not pdf_path.exists():
        return ""
    try:
        doc = fitz.open(str(pdf_path))
        text = "\n".join(doc[i].get_text("text") for i in range(min(n_pages, doc.page_count)))
        doc.close()
        return text
    except Exception:
        return ""


def validate_collected_paper(
    paper_id: str,
    paper_dir: "str | Path",
    expected_doi: str,
    publisher: str,
    *,
    min_chars: int = 5000,
    min_words: int = 1500,
) -> dict:
    """collection 후 모든 검증 통과해야 success.

    Returns:
        {'paper_id': ..., 'issues': [str, ...], 'success': bool}
        issues != [] 이면 success=False → retry/manual queue 분기.
    """
    paper_dir = Path(paper_dir)
    issues: list[str] = []

    src_path = paper_dir / "source.md"
    src_md = src_path.read_text(encoding="utf-8", errors="ignore") if src_path.exists() else ""
    pdf_path = paper_dir / "pdf" / f"{paper_id}.pdf"

    chars = len(src_md)
    words = len(src_md.split())

    # 1. body length
    if chars < min_chars or words < min_words:
        issues.append(f"inadequate_body_length:chars={chars},words={words}")

    # 2. section headers
    section_hits = sum(1 for p in SECTION_PATTERNS if re.search(p, src_md, re.I))
    if section_hits < 2:
        issues.append(f"section_headers_missing:hits={section_hits}")

    # 3. reference ratio (## References 이후가 본문보다 크면 본문 빈약)
    ref_match = re.search(r"^##\s+References?\s*$", src_md, re.I | re.M)
    if ref_match:
        before = src_md[: ref_match.start()]
        after = src_md[ref_match.start():]
        if len(after) > len(before):
            issues.append("reference_ratio_over_50pct")

    # 4. Elsevier 1-page preview
    pub = (publisher or "").lower()
    if "elsevier" in pub and pdf_path.exists():
        n_pages, _ = _pdf_pages_and_first_page(pdf_path)
        if n_pages is not None and n_pages <= 1 and chars < 10000:
            issues.append(f"elsevier_1page_preview_suspected:pages={n_pages},chars={chars}")

    # 4b. paywall fall-through (검증된 publisher 라도 paper별 paywall HTML)
    paywall_hits = len(re.findall(PAYWALL_KW, src_md, re.I))
    body_hits = len(re.findall(BODY_KW, src_md, re.I))
    if paywall_hits >= 5 and body_hits < 2:
        issues.append(f"paywall_fallthrough_suspected:paywall={paywall_hits},body={body_hits}")

    # 5. DOI 매칭 (wrong-paper drift) — 보수적:
    #    expected DOI 가 앞 두 쪽 어디에도 없고 다른 DOI 만 있으면 의심.
    #    (옛 Science PDF 는 옛 형식 DOI `10.1126/science.1057823` 를 먼저 찍고 Crossref DOI 는 뒤에 나온다, 2026-09-27)
    if pdf_path.exists() and expected_doi:
        # expected DOI 가 PDF 어디에든 있으면 같은 논문으로 본다 (옛 Science PDF 는 마지막 쪽에만 Crossref DOI 가 있다)
        if expected_doi.lower() not in _pdf_head_text(pdf_path, 10**6).lower():
            head = _pdf_head_text(pdf_path, 2)
            others = sorted({m.group(1).rstrip(".,;)") for m in DOI_RE.finditer(head)}, key=str.lower)
            others = [d for d in others if d.lower() != expected_doi.lower()]
            if others:
                issues.append(f"doi_mismatch_suspected:expected={expected_doi},found={others[0]}")

    # 6. replacement guard (이전 source.md 가 더 풍부했는지)
    backups = (
        list(paper_dir.glob("source_pre_*.md"))
        + list(paper_dir.glob("source.md.replaced_*.bak"))
        + list(paper_dir.glob("source.md.*backup*"))
    )
    # 공백을 뺀 글자 수로 비교: 예전 PDF 추출(sort=True)은 두 단 정렬 공백으로 글자 수가 3~7배 부풀어 오경보가 났다 (2026-09-24)
    def _solid(txt: str) -> int:
        return sum(1 for c in txt if not c.isspace())
    cur_solid = _solid(src_md)
    for bak in backups:
        try:
            bak_solid = _solid(bak.read_text(encoding="utf-8", errors="ignore"))
            if bak_solid > 0 and cur_solid < 0.5 * bak_solid:
                issues.append(f"replacement_loss:current={cur_solid}<50pct_of={bak_solid}@{bak.name} (공백 제외 글자 수)")
        except Exception:
            pass

    return {"paper_id": paper_id, "issues": issues, "success": len(issues) == 0}


# ============================================================
# self-test (합성 케이스)
# ============================================================
if __name__ == "__main__":
    import os
    import sys
    import tempfile

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # 인자로 실제 paper_dir 주면 그걸 검증 (예: PdAg)
    if len(sys.argv) >= 4:
        pid, pdir, doi = sys.argv[1], sys.argv[2], sys.argv[3]
        pub = sys.argv[4] if len(sys.argv) >= 5 else ""
        res = validate_collected_paper(pid, pdir, doi, pub)
        print(f"[real] {pid}: success={res['success']} issues={res['issues']}")
        sys.exit(0)

    n_pass = 0
    cases = []

    def case(label, files, doi, pub, expect_success):
        cases.append((label, files, doi, pub, expect_success))

    # 정상 본문 (full)
    good_body = (
        "## Extracted Full Text\n\n# Title\n\n## Abstract\nWe report...\n\n"
        "## Introduction\n" + ("electrochemical epoxidation of ethylene. " * 200)
        + "\n\n## Experimental\nCHI660E...\n\n## Results and Discussion\n"
        + ("Faradaic efficiency reached 90%. " * 200)
        + "\n\n## Conclusions\nWe demonstrated...\n"
    )
    case("정상 본문", {"source.md": good_body}, "10.1016/j.test.2025.1", "elsevier", True)

    # thin (PdAg 류 — title+abstract 만)
    thin = "## Extracted HTML Text\n\n# Sustainable electrosynthesis of ethylene oxide via water-oxidation intermediates on PdAg alloy catalysts\n\nAbstract only, 51.3% FE.\n"
    case("thin (PdAg 류)", {"source.md": thin}, "10.1016/j.jallcom.2025.181219", "elsevier", False)

    # paywall fall-through (5k+ chars 지만 본문 없음)
    paywall = (
        "## Extracted HTML Text\n\n# Title\n\n"
        + "Purchase access. Subscribe to this journal. Recommended Articles. Cited By. "
        "Institutional access required. Sign in to download. " * 60
    )
    case("paywall fall-through", {"source.md": paywall}, "10.1039/d5gc00148j", "rsc", False)

    # replacement loss (backup 이 훨씬 큼)
    case(
        "replacement loss",
        {"source.md": good_body[:3000], "source_pre_batch.md": good_body * 5},
        "10.1016/j.test.2025.2",
        "elsevier",
        False,
    )

    for label, files, doi, pub, expect in cases:
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td)
            for fn, content in files.items():
                (pdir / fn).write_text(content, encoding="utf-8")
            res = validate_collected_paper("tst", pdir, doi, pub)
            ok = res["success"] == expect
            n_pass += ok
            mark = "OK" if ok else "FAIL"
            print(f"  [{mark}] {label:24} success={res['success']} (expect {expect}) issues={res['issues']}")

    print(f"\n  {n_pass}/{len(cases)} self-test passed")
    sys.exit(0 if n_pass == len(cases) else 1)
