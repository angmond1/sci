# -*- coding: utf-8 -*-
"""failure_classifier.py — sci-retr skill scripts.

Batch fulltext recovery 실패 항목 사후 분류 스크립트.

원본 logic 보존 + 일반화 변경:
  - DEFAULT_BATCH_DIR hardcode → --kb-root / --batch-name / --work-dir / --input 인자
  - load_dotenv(env_path) 패턴 추가
  - CATEGORY_ACTIONS / classify_row / build_summary_md 등 분류 logic 그대로

CLI 사용:
    python failure_classifier.py --kb-root <path> --batch-name <name> [--codex-only | --claude-only]
    python failure_classifier.py --input <batch_dir> [--output-csv <path>] [--output-md <path>]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# 카테고리 추천 조치 사전 (출력 MD용)
# ──────────────────────────────────────────────────────────────────────────────
CATEGORY_ACTIONS: OrderedDict = OrderedDict([
    ("elsevier_partial_pdf",
     "manual_pdf_dropbox 권장 (Elsevier institutional token 또는 사용자 수동 PDF)"),
    ("elsevier_sciencedirect_403",
     "manual_pdf_dropbox 권장 또는 ScienceDirect Playwright sign-in 시도"),
    ("metadata_mismatch",
     "재시도 시 metadata 보강 후 또는 manual_pdf_dropbox"),
    ("access_wall",
     "manual_pdf_dropbox + 권한 보강"),
    ("cloudflare_or_js_landing",
     "manual_pdf_dropbox 권장 (자동 우회 어려움)"),
    ("oup_abstract_redirect",
     "manual_pdf_dropbox 또는 OUP TDM 권한"),
    ("short_content_no_structure",
     "수동 review (옛 short letter일 가능성)"),
    ("pdf_endpoint_404",
     "PII/DOI 정규화 재시도"),
    ("pdf_endpoint_other_failure",
     "publisher 재확인 후 retry"),
    ("unknown_other",
     "수동 review 필요"),
])


# ──────────────────────────────────────────────────────────────────────────────
# CSV 읽기 유틸 (utf-8-sig 우선, utf-8 fallback)
# ──────────────────────────────────────────────────────────────────────────────
def read_csv_rows(path: Path) -> list[dict]:
    """
    CSV 파일을 읽어 dict 리스트로 반환.
    BOM 있는 utf-8-sig를 먼저 시도하고, 실패하면 utf-8로 재시도.
    파일이 없으면 경고 후 빈 리스트 반환.
    """
    if not path.exists():
        print(f"[WARNING] 파일 없음, 건너뜀: {path}", file=sys.stderr)
        return []

    for enc in ("utf-8-sig", "utf-8"):
        try:
            with open(path, newline="", encoding=enc) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return rows
        except UnicodeDecodeError:
            continue

    # 최후 수단: latin-1 (손실 허용)
    print(f"[WARNING] UTF-8 디코딩 실패, latin-1로 재시도: {path}", file=sys.stderr)
    with open(path, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ──────────────────────────────────────────────────────────────────────────────
# 핵심 분류 함수
# ──────────────────────────────────────────────────────────────────────────────
def classify_row(row: dict) -> str:
    """
    단일 실패 행을 카테고리 문자열로 분류.
    우선순위 순서대로 첫 매치 카테고리를 반환.
    """
    notes = (row.get("notes") or "").strip()
    error_msg = (row.get("error_message") or "").strip()
    publisher = (row.get("publisher") or "").strip().lower()
    content_length_raw = (row.get("content_length_chars") or "0").strip()

    # content_length_chars를 정수로 변환 (파싱 실패 시 0)
    try:
        content_length = int(content_length_raw)
    except (ValueError, TypeError):
        content_length = 0

    # 검색 대상 텍스트를 합쳐서 한 번에 검색하는 헬퍼
    combined = f"{notes}\n{error_msg}"

    def contains(pattern: str, text: str = combined) -> bool:
        """대소문자 무관 부분 문자열 포함 여부"""
        return pattern.lower() in text.lower()

    def contains_re(pattern: str, text: str = combined) -> bool:
        """정규식 매칭 (IGNORECASE)"""
        return bool(re.search(pattern, text, re.IGNORECASE))

    # ── 1. elsevier_partial_pdf ──────────────────────────────────────────────
    if contains("first-page partial: page range indicates multi-page article"):
        return "elsevier_partial_pdf"

    # ── 2. elsevier_sciencedirect_403 ────────────────────────────────────────
    if (
        contains("elsevier_sciencedirect direct pdf failed status=403")
        or contains("elsevier_sciencedirect browser pdf failed status=403")
    ):
        return "elsevier_sciencedirect_403"

    # ── 3. metadata_mismatch ─────────────────────────────────────────────────
    if contains("DOI/title match failed"):
        return "metadata_mismatch"

    # ── 4. access_wall ───────────────────────────────────────────────────────
    if contains("access-wall keyword detected"):
        return "access_wall"

    # ── 5. cloudflare_or_js_landing ──────────────────────────────────────────
    # world_scientific publisher 이거나 notes에 관련 키워드 포함 + 콘텐츠 짧은 경우
    is_world_scientific = publisher == "world_scientific"
    has_cf_keyword = (
        contains("worldscientific.com")
        or contains("cloudflare")
        or contains("challenge")
    )
    if (is_world_scientific or has_cf_keyword) and content_length < 200:
        return "cloudflare_or_js_landing"

    # ── 6. oup_abstract_redirect ─────────────────────────────────────────────
    if contains("academic.oup.com", notes):
        return "oup_abstract_redirect"

    # ── 7. short_content_no_structure ────────────────────────────────────────
    if contains("short text lacks references/captions/article structure"):
        return "short_content_no_structure"

    # ── 8. pdf_endpoint_404 ──────────────────────────────────────────────────
    if contains("pdf_status=404") or contains("status=404"):
        return "pdf_endpoint_404"

    # ── 9. pdf_endpoint_other_failure ────────────────────────────────────────
    # 다운로드 시도 흔적이 있는 일반 실패 (status 코드 포함 패턴)
    if contains_re(r"status=\d{3}") or contains("download failed") or contains("pdf failed"):
        return "pdf_endpoint_other_failure"

    # ── 10. unknown_other ────────────────────────────────────────────────────
    return "unknown_other"


# ──────────────────────────────────────────────────────────────────────────────
# CSV 출력
# ──────────────────────────────────────────────────────────────────────────────
def write_classified_csv(rows: list[dict], output_path: Path) -> None:
    """
    category 컬럼이 추가된 행들을 CSV로 저장.
    출력 인코딩: utf-8-sig (Excel BOM 호환).
    """
    if not rows:
        print("[WARNING] 분류할 행이 없습니다.", file=sys.stderr)
        output_path.write_text("", encoding="utf-8-sig")
        return

    # 원본 컬럼 순서 유지 + category 추가
    original_cols = list(rows[0].keys())
    if "category" not in original_cols:
        fieldnames = original_cols + ["category"]
    else:
        fieldnames = original_cols  # 혹시 이미 있으면 그대로

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] 분류 CSV 저장: {output_path}  ({len(rows)}행)")


# ──────────────────────────────────────────────────────────────────────────────
# 마크다운 요약 생성
# ──────────────────────────────────────────────────────────────────────────────
def _md_table(headers: list[str], rows_data: list[list]) -> str:
    """간단한 마크다운 테이블 문자열 생성"""
    sep = "| " + " | ".join(["---"] * len(headers)) + " |"
    header_row = "| " + " | ".join(str(h) for h in headers) + " |"
    body_rows = [
        "| " + " | ".join(str(c) for c in row) + " |"
        for row in rows_data
    ]
    return "\n".join([header_row, sep] + body_rows)


def build_summary_md(rows: list[dict]) -> str:
    """
    분류된 행 목록으로부터 마크다운 요약 문자열을 생성.

    포함 섹션:
      1. 카테고리별 통계 (count, paper_id 리스트, 추천 조치)
      2. publisher별 통계
      3. agent별 (codex / claude) 통계
    """
    if not rows:
        return "# 실패 분류 요약\n\n분류할 행이 없습니다.\n"

    total = len(rows)

    # ── 카테고리별 집계 ────────────────────────────────────────────────────────
    cat_map: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        cat_map[r.get("category", "unknown_other")].append(r)

    # ── publisher별 집계 ─────────────────────────────────────────────────────
    pub_map: dict[str, int] = defaultdict(int)
    for r in rows:
        pub_map[r.get("publisher") or "(unknown)"] += 1

    # ── agent별 집계 ──────────────────────────────────────────────────────────
    agent_map: dict[str, int] = defaultdict(int)
    for r in rows:
        agent_map[r.get("agent") or "(unknown)"] += 1

    lines: list[str] = []
    lines.append("# batch 실패 분류 요약")
    lines.append("")
    lines.append(f"- 총 실패 행: **{total}**")
    lines.append("- 생성일: 이 파일은 `failure_classifier.py`로 자동 생성됨")
    lines.append("")

    # ── 섹션 1: 카테고리별 통계 ──────────────────────────────────────────────
    lines.append("## 1. 카테고리별 통계")
    lines.append("")

    cat_table_rows = []
    for cat in CATEGORY_ACTIONS:
        sub = cat_map.get(cat, [])
        count = len(sub)
        if count == 0:
            continue
        paper_ids = ", ".join(
            str(r.get("paper_id", "?")) for r in sub[:10]
        )
        if len(sub) > 10:
            paper_ids += f" ... (+{len(sub) - 10})"
        action = CATEGORY_ACTIONS[cat]
        cat_table_rows.append([cat, count, paper_ids, action])

    # unknown_other는 CATEGORY_ACTIONS에 포함되어 있지만,
    # 혹시 cat_map에 정의되지 않은 카테고리가 있으면 추가
    for cat, sub in cat_map.items():
        if cat not in CATEGORY_ACTIONS:
            count = len(sub)
            paper_ids = ", ".join(str(r.get("paper_id", "?")) for r in sub[:10])
            if len(sub) > 10:
                paper_ids += f" ... (+{len(sub) - 10})"
            cat_table_rows.append([cat, count, paper_ids, "수동 review 필요"])

    if cat_table_rows:
        lines.append(
            _md_table(
                ["카테고리", "count", "paper_id (최대 10개)", "추천 조치"],
                cat_table_rows,
            )
        )
    else:
        lines.append("(분류된 항목 없음)")
    lines.append("")

    # ── 섹션 1b: 카테고리별 상세 paper_id 목록 ──────────────────────────────
    lines.append("### 카테고리별 paper_id 전체 목록")
    lines.append("")
    for cat in list(CATEGORY_ACTIONS.keys()) + [
        c for c in cat_map if c not in CATEGORY_ACTIONS
    ]:
        sub = cat_map.get(cat, [])
        if not sub:
            continue
        ids_str = ", ".join(str(r.get("paper_id", "?")) for r in sub)
        lines.append(f"**{cat}** ({len(sub)}건): {ids_str}")
        lines.append("")

    # ── 섹션 2: publisher별 통계 ─────────────────────────────────────────────
    lines.append("## 2. publisher별 통계")
    lines.append("")
    pub_rows_sorted = sorted(pub_map.items(), key=lambda x: -x[1])
    lines.append(
        _md_table(
            ["publisher", "count"],
            [[p, c] for p, c in pub_rows_sorted],
        )
    )
    lines.append("")

    # ── 섹션 3: agent별 통계 ─────────────────────────────────────────────────
    lines.append("## 3. agent별 통계")
    lines.append("")
    agent_rows_sorted = sorted(agent_map.items(), key=lambda x: -x[1])
    lines.append(
        _md_table(
            ["agent", "count"],
            [[a, c] for a, c in agent_rows_sorted],
        )
    )
    lines.append("")

    return "\n".join(lines)


def write_summary_md(rows: list[dict], output_path: Path) -> None:
    """마크다운 요약 파일을 utf-8 (no BOM)으로 저장"""
    md_text = build_summary_md(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_text, encoding="utf-8")
    print(f"[OK] 요약 MD 저장: {output_path}")


# ──────────────────────────────────────────────────────────────────────────────
# 메인 파이프라인
# ──────────────────────────────────────────────────────────────────────────────
def run(
    batch_dir: Path,
    use_codex: bool,
    use_claude: bool,
    output_csv: Path,
    output_md: Path,
) -> None:
    """실패 CSV를 로드 → 분류 → 출력 CSV/MD 저장."""
    all_rows: list[dict] = []

    if use_codex:
        codex_path = batch_dir / "failures_codex.csv"
        codex_rows = read_csv_rows(codex_path)
        print(f"[INFO] codex 행 수: {len(codex_rows)}")
        all_rows.extend(codex_rows)

    if use_claude:
        claude_path = batch_dir / "failures_claude.csv"
        claude_rows = read_csv_rows(claude_path)
        print(f"[INFO] claude 행 수: {len(claude_rows)}")
        all_rows.extend(claude_rows)

    if not all_rows:
        print("[WARNING] 처리할 행이 없습니다. 종료.", file=sys.stderr)
        return

    # 분류 적용
    for row in all_rows:
        row["category"] = classify_row(row)

    # 카테고리별 간단 집계 출력
    cat_counter: dict[str, int] = defaultdict(int)
    for row in all_rows:
        cat_counter[row["category"]] += 1

    print("\n[분류 결과 요약]")
    for cat in CATEGORY_ACTIONS:
        cnt = cat_counter.get(cat, 0)
        if cnt > 0:
            print(f"  {cat}: {cnt}")
    # CATEGORY_ACTIONS에 없는 카테고리 (있을 경우)
    for cat, cnt in cat_counter.items():
        if cat not in CATEGORY_ACTIONS:
            print(f"  {cat} (미정의): {cnt}")
    print(f"  총계: {len(all_rows)}")
    print()

    write_classified_csv(all_rows, output_csv)
    write_summary_md(all_rows, output_md)


def load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        print(f"[warn] .env not found: {env_path}")
        return
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_paths(args: argparse.Namespace) -> dict[str, Path]:
    kb_root = Path(args.kb_root or os.environ.get("KB_ROOT", "")).resolve()
    if not kb_root.exists():
        raise SystemExit(f"--kb-root 또는 KB_ROOT 환경변수 필요. 받은 값: {kb_root}")
    batch_name = args.batch_name or f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    work_root = Path(args.work_dir).resolve() if args.work_dir else (
        kb_root / "pdf_download_tests" / batch_name
    )
    work_root.mkdir(parents=True, exist_ok=True)
    return {
        "kb_root": kb_root,
        "papers_root": kb_root / "papers",
        "work_root": work_root,
    }


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Batch fulltext recovery 실패 항목 사후 분류 스크립트.\n"
            "failures_codex.csv / failures_claude.csv를 읽어 카테고리를 부여하고\n"
            "failures_classified.csv + failures_summary.md를 생성합니다."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--kb-root", default=None,
                        help="KB 최상위 경로 (환경변수 KB_ROOT 대체 가능)")
    parser.add_argument("--batch-name", default=None,
                        help="작업 폴더명 (기본: batch_<utc_yyyymmdd>)")
    parser.add_argument("--work-dir", default=None,
                        help="직접 work 디렉터리 경로 지정 (--batch-name 무시)")
    parser.add_argument("--env-path", default=None,
                        help=".env 파일 경로 (기본: kb_root/.env)")
    parser.add_argument(
        "--input",
        metavar="DIR",
        default=None,
        help="입력 파일이 있는 배치 디렉터리 (--work-dir 와 동일, 하위 호환용)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--codex-only", action="store_true", help="failures_codex.csv만 처리")
    group.add_argument("--claude-only", action="store_true", help="failures_claude.csv만 처리")
    parser.add_argument(
        "--output-csv",
        metavar="PATH",
        default=None,
        help="분류 결과 CSV 출력 경로 (기본값: batch_dir/failures_classified.csv)",
    )
    parser.add_argument(
        "--output-md",
        metavar="PATH",
        default=None,
        help="요약 마크다운 출력 경로 (기본값: batch_dir/failures_summary.md)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    # batch_dir 결정: --input 하위 호환, 없으면 --kb-root / --batch-name 조합
    if args.input:
        batch_dir = Path(args.input)
    else:
        paths = get_paths(args)
        batch_dir = paths["work_root"]

    env_path = Path(args.env_path) if args.env_path else (batch_dir.parent.parent / ".env")
    load_dotenv(env_path)

    # 어느 쪽 CSV를 사용할지 결정
    use_codex = not args.claude_only   # --claude-only가 아니면 codex 포함
    use_claude = not args.codex_only   # --codex-only가 아니면 claude 포함

    # 출력 경로 결정
    output_csv = Path(args.output_csv) if args.output_csv else (
        batch_dir / "failures_classified.csv"
    )
    output_md = Path(args.output_md) if args.output_md else (
        batch_dir / "failures_summary.md"
    )

    run(
        batch_dir=batch_dir,
        use_codex=use_codex,
        use_claude=use_claude,
        output_csv=output_csv,
        output_md=output_md,
    )


if __name__ == "__main__":
    main()
