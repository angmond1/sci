"""split_assignment.py — sci-retr skill scripts.

body_absent 논문 CSV를 agent(codex/claude)별 assignment CSV로 분할.

원본 logic 보존 + 일반화 변경:
  - hardcoded REPO/OUT_DIR → --kb-root / --batch-name / --work-dir 인자
  - --input-csv 인자 추가 (기본: kb_root/reports/fulltext_coverage_audit/02_papers_body_absent.csv)
  - 환경변수 KB_ROOT 대체 가능

CLI 사용:
    python split_assignment.py --kb-root <path> --batch-name <name> [--input-csv <path>]
"""
from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime, timezone
from pathlib import Path


# DOI prefix → publisher group 매핑
def classify_publisher(doi: str) -> str:
    if not doi:
        return "unknown"
    d = doi.lower().strip()
    if d.startswith("10.1016") or d.startswith("10.1006"):
        return "elsevier"
    if d.startswith("10.1039"):
        return "rsc"
    if d.startswith("10.1007") or d.startswith("10.1023"):
        return "springer"
    if d.startswith("10.1021"):
        return "acs"
    if d.startswith("10.1002"):
        return "wiley"
    if d.startswith("10.3390"):
        return "mdpi"
    if d.startswith("10.1055"):
        return "thieme"
    if d.startswith("10.1142"):
        return "world_scientific"
    if d.startswith("10.1246"):
        return "csj_chem_lett"
    if d.startswith("10.1248"):
        return "pharm_soc_japan"
    if d.startswith("10.1149"):
        return "ecs"
    if d.startswith("10.1098"):
        return "royal_society"
    if d.startswith("10.1134"):
        return "pleiades_springer_ru"
    if d.startswith("10.20964") or d.startswith("10.26599"):
        return "tsinghua_oae"
    return "other_small"


# 분담 정책: publisher group별로 (codex, claude) 비율 또는 절반 분배 규칙
# True = Codex 전담, False = Claude 전담, None = 절반 분배 (paper_id sort 기준)
PUBLISHER_POLICY = {
    "elsevier": None,           # 절반 분배 (Elsevier API 양쪽 사용)
    "rsc": None,                # 절반 분배 (landing meta, key 불필요)
    "springer": None,           # 절반 분배
    "acs": True,                # Codex 전담 (Playwright 셋업)
    "wiley": True,              # Codex 전담 (wiley-tdm 셋업)
    "mdpi": None,               # 절반 분배
    "thieme": None,             # 절반 분배 (양쪽 신규 시도)
    "world_scientific": False,  # Claude 시도 (Cloudflare 우회 필요)
    "csj_chem_lett": False,     # Claude 시도 (J-STAGE 가능성)
    "pharm_soc_japan": False,   # Claude 시도 (J-STAGE)
    "ecs": None,                # 절반 분배
    "royal_society": None,      # 절반 분배 (소수)
    "pleiades_springer_ru": None,
    "tsinghua_oae": None,
    "other_small": None,        # 절반 분배 (다양한 작은 publishers)
    "unknown": None,
}


def split_half(items: list[dict], policy: bool | None) -> tuple[list[dict], list[dict]]:
    """policy: True=Codex 전담, False=Claude 전담, None=절반 분배."""
    if policy is True:
        return items, []
    if policy is False:
        return [], items
    items_sorted = sorted(items, key=lambda r: r["paper_id"])
    half = (len(items_sorted) + 1) // 2  # 홀수면 Codex가 1편 더
    return items_sorted[:half], items_sorted[half:]


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="body_absent 논문 CSV를 agent별 assignment CSV로 분할."
    )
    parser.add_argument("--kb-root", default=None,
                        help="KB 최상위 경로 (환경변수 KB_ROOT 대체 가능)")
    parser.add_argument("--batch-name", default=None,
                        help="작업 폴더명 (기본: batch_<utc_yyyymmdd>)")
    parser.add_argument("--work-dir", default=None,
                        help="직접 work 디렉터리 경로 지정 (--batch-name 무시)")
    parser.add_argument("--input-csv", default=None,
                        help="입력 CSV 경로 (기본: kb_root/reports/fulltext_coverage_audit/02_papers_body_absent.csv)")
    parser.add_argument("--env-path", default=None,
                        help=".env 파일 경로 (기본: kb_root/.env)")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    paths = get_paths(args)
    kb_root = paths["kb_root"]
    out_dir = paths["work_root"]

    # .env 로드 (credentials 필요 시)
    env_path = Path(args.env_path) if args.env_path else (kb_root / ".env")
    load_dotenv(env_path)

    input_csv = (
        Path(args.input_csv)
        if args.input_csv
        else kb_root / "reports" / "fulltext_coverage_audit" / "02_papers_body_absent.csv"
    )
    if not input_csv.exists():
        raise SystemExit(f"입력 CSV 없음: {input_csv}")

    # body_absent 논문 로드
    rows: list[dict] = []
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "paper_id": r["paper_id"].strip(),
                "doi": r.get("doi", "").strip(),
                "title": r.get("title_truncated", "").strip(),
                "year": r.get("year", "").strip(),
                "scope_label": r.get("scope_label", "").strip(),
                "is_curated_pathway": r.get("is_curated_pathway", "").strip(),
                "publisher": classify_publisher(r.get("doi", "")),
            })

    # publisher group별로 묶기
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["publisher"], []).append(r)

    # 분담
    codex_assignment: list[dict] = []
    claude_assignment: list[dict] = []
    summary_lines = [
        "# batch 분담 통계",
        "",
        f"총 body_absent 논문: {len(rows)}편",
        "",
        "| publisher | 총 | Codex | Claude | 정책 |",
        "|---|---:|---:|---:|---|",
    ]
    for pub in sorted(groups.keys(), key=lambda k: -len(groups[k])):
        items = groups[pub]
        policy = PUBLISHER_POLICY.get(pub)
        codex_part, claude_part = split_half(items, policy)
        for r in codex_part:
            r["agent"] = "codex"
            codex_assignment.append(r)
        for r in claude_part:
            r["agent"] = "claude"
            claude_assignment.append(r)
        policy_str = (
            "Codex 전담"
            if policy is True
            else "Claude 전담"
            if policy is False
            else "절반 분배 (paper_id sort)"
        )
        summary_lines.append(
            f"| {pub} | {len(items)} | {len(codex_part)} | {len(claude_part)} | {policy_str} |"
        )

    summary_lines.append(
        f"| **합계** | **{len(rows)}** | **{len(codex_assignment)}** | **{len(claude_assignment)}** | — |"
    )
    summary_lines.append("")
    summary_lines.append(
        f"비율: Codex {len(codex_assignment)/len(rows)*100:.1f}% / Claude {len(claude_assignment)/len(rows)*100:.1f}%"
    )

    # 출력 CSV
    fieldnames = ["paper_id", "doi", "title", "year", "scope_label", "is_curated_pathway", "publisher", "agent"]
    for fname, data in [
        ("assignment_codex.csv", codex_assignment),
        ("assignment_claude.csv", claude_assignment),
    ]:
        out_path = out_dir / fname
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in sorted(data, key=lambda x: (x["publisher"], x["paper_id"])):
                writer.writerow({k: r.get(k, "") for k in fieldnames})
        print(f"[OK] wrote {out_path} ({len(data)} rows)")

    summary_path = out_dir / "assignment_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"[OK] wrote {summary_path}")
    print()
    print("\n".join(summary_lines))


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
    if "TDM_API_TOKEN" not in os.environ and "WILEY_TDM_TOKEN" in os.environ:
        os.environ["TDM_API_TOKEN"] = os.environ["WILEY_TDM_TOKEN"]


if __name__ == "__main__":
    main()
