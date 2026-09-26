"""elsevier_html_retry_safe.py — sci-retr skill scripts.

Elsevier ScienceDirect 논문을 브라우저(Playwright)로 article HTML 수집.
rate-limit 감지 시 즉시 중단, chunk 단위 진행 + chunk 간 대기 지원.

원본 logic 보존 + 일반화 변경:
  - hardcoded WORK/PROFILE/CHROME_EXE/PENDING_CSV/LOG_CSV → --kb-root / --batch-name / --work-dir / --profile-name 인자
  - from v02_590batch_claude_runner import ... → from runner import ...
  - load_dotenv(env_path) 패턴 추가

CLI 사용:
    python elsevier_html_retry_safe.py --kb-root <path> --batch-name <name> [--chunk-start N] [--chunk-size N]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# runner 함수 재사용
sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner  # noqa: E402
from runner import (  # noqa: E402
    Paper, CollectionResult,
    write_html_source, finish_result, append_source_origin,
    strip_html_text, utc_now,
    load_dotenv, get_paths, configure,
)

PROBLEM_PAGE_KEYWORDS = [
    "There was a problem providing the content you requested",
    "Please contact our support team",
    "Reference number:",
]

LOG_FIELDS = [
    "paper_id", "doi", "publisher", "attempt_method", "content_source",
    "success", "content_status", "content_length_chars",
    "n_pdf_pages", "n_pdf_extracted_images", "n_html_figures", "figure_status",
    "pdf_path", "html_path", "xml_path",
    "source_md_size_bytes", "error_message", "started_at", "completed_at",
    "agent", "chunk_index", "paper_index_in_chunk",
]


def detect_problem_page(html: str, body_text: str) -> tuple[bool, str]:
    combined = (html[:6000] + " " + body_text[:2000]).lower()
    for kw in PROBLEM_PAGE_KEYWORDS:
        if kw.lower() in combined:
            return True, kw
    return False, ""


def append_log(rows: list[dict], log_csv: Path) -> None:
    if not rows:
        return
    exists = log_csv.exists() and log_csv.stat().st_size > 0
    if exists:
        with log_csv.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
            for r in rows:
                w.writerow(r)
    else:
        with log_csv.open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)


def year_priority_key(row: dict) -> tuple[int, int]:
    y = (row.get("year", "0") or "0")[:4]
    try:
        yr = int(y)
    except Exception:
        yr = 0
    if yr >= 2010:
        return (0, -yr)
    if yr >= 2000:
        return (1, -yr)
    if yr >= 1990:
        return (2, -yr)
    return (3, -yr)


def already_done_paper_ids(log_csv: Path) -> set[str]:
    """이미 log_csv에 success 기록된 paper_id (재실행 시 skip 용)."""
    done = set()
    if not log_csv.exists():
        return done
    try:
        with log_csv.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if (r.get("success", "") or "").lower() == "true":
                    done.add(r.get("paper_id", "").strip())
    except Exception:
        pass
    return done


def process_chunk(page, chunk: list[dict], chunk_start_idx: int, args, log_csv: Path) -> bool:
    """단일 chunk 처리. rate-limit 감지 시 True 반환 (모든 chunk 중단 신호)."""
    rate_limited = False
    for i, row in enumerate(chunk):
        global_idx = chunk_start_idx + i
        pid = row["paper_id"]
        doi = row["doi"]
        year = row.get("year", "")
        article_url = row.get("final_url", "")
        year_int = 0
        try:
            year_int = int(year[:4]) if year else 0
        except Exception:
            pass
        wait_sec = args.paper_wait_old if year_int and year_int < 2010 else args.paper_wait

        print(f"\n[idx={global_idx} ({i+1}/{len(chunk)})] {pid} ({doi}) year={year}")
        print(f"  -> URL: {article_url[:110]}")
        print(f"  -> wait_after_load: {wait_sec}s")

        paper = Paper(
            paper_id=pid, doi=doi, title=row.get("title", ""), year=year,
            scope_label="", is_curated_pathway="", publisher="elsevier", agent="claude",
        )
        result = CollectionResult(paper=paper, started_at=utc_now())

        try:
            page.goto(article_url, wait_until="networkidle", timeout=120000)
            time.sleep(wait_sec)
            html_content = page.content()
            body_check = strip_html_text(html_content)

            is_problem, kw = detect_problem_page(html_content, body_check)
            if is_problem:
                result.success = False
                result.content_status = "rate_limited_stop"
                result.error_message = f"problem page: {kw}"
                result.completed_at = utc_now()
                print(f"  [WARN] RATE LIMIT detected: {kw}")
                rate_limited = True
                log_row = result.log_row()
                log_row["chunk_index"] = chunk_start_idx
                log_row["paper_index_in_chunk"] = i
                append_log([log_row], log_csv)
                break

            result.attempt_method = "elsevier_sciencedirect_article_html_kistip"
            write_html_source(paper, html_content, page.url, result.attempt_method, result)
            finish_result(result)
            if result.success:
                append_source_origin(paper, result)
            print(f"  -> success={result.success} status={result.content_status} chars={result.content_length_chars} figs={result.n_html_figures}")

        except Exception as exc:
            result.success = False
            result.content_status = "reject"
            result.error_message = f"{type(exc).__name__}: {str(exc)[:300]}"
            result.completed_at = utc_now()
            print(f"  -> ERROR: {result.error_message}")

        log_row = result.log_row()
        log_row["chunk_index"] = chunk_start_idx
        log_row["paper_index_in_chunk"] = i
        append_log([log_row], log_csv)

        if i < len(chunk) - 1 and not rate_limited:
            print(f"  ... sleeping {args.paper_interval}s before next paper")
            time.sleep(args.paper_interval)

    return rate_limited


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Elsevier ScienceDirect 논문 HTML 수집 (rate-limit 안전 chunk 방식)."
    )
    parser.add_argument("--kb-root", default=None,
                        help="KB 최상위 경로 (환경변수 KB_ROOT 대체 가능)")
    parser.add_argument("--batch-name", default=None,
                        help="작업 폴더명 (기본: batch_<utc_yyyymmdd>)")
    parser.add_argument("--work-dir", default=None,
                        help="직접 work 디렉터리 경로 지정 (--batch-name 무시)")
    parser.add_argument("--env-path", default=None,
                        help=".env 파일 경로 (기본: kb_root/.env)")
    parser.add_argument("--pending-csv", default=None,
                        help="입력 CSV 경로 (기본: work_dir/elsevier_retry_pending.csv)")
    parser.add_argument("--log-csv", default=None,
                        help="로그 CSV 경로 (기본: work_dir/elsevier_html_retry_log.csv)")
    parser.add_argument("--profile-name", default="kistsso",
                        help="Chrome 프로필 폴더명 (기본: kistsso → work_dir/chrome_profile_kistsso)")
    parser.add_argument("--chrome-exe",
                        default=os.environ.get("CHROME_EXE", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                        help="Chrome 실행 경로 (환경변수 CHROME_EXE 대체 가능)")
    parser.add_argument("--agent", default=os.environ.get("AGENT_NAME", "claude"),
                        help="작업자 이름 (claude/codex, 기본: claude / 환경변수 AGENT_NAME)")
    parser.add_argument("--chunk-start", type=int, default=0, help="시작 paper 인덱스 (정렬 후)")
    parser.add_argument("--chunk-size", type=int, default=15)
    parser.add_argument("--total-chunks", type=int, default=1, help="연속 진행할 chunk 수")
    parser.add_argument("--chunk-wait", type=int, default=1800, help="chunk 간 sleep 초 (기본 30분)")
    parser.add_argument("--paper-interval", type=int, default=90)
    parser.add_argument("--paper-wait", type=int, default=8)
    parser.add_argument("--paper-wait-old", type=int, default=12)
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--no-priority", action="store_true")
    parser.add_argument("--skip-done", action="store_true", default=True,
                        help="이미 success 기록된 paper skip")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    paths = get_paths(args)
    # runner module globals 초기화 (write_html_source / finish_result / append_source_origin 등 호출 전 필수)
    configure(paths, args.agent, args.chrome_exe)
    work_root = paths["work_root"]

    env_path = Path(args.env_path) if args.env_path else (paths["kb_root"] / ".env")
    load_dotenv(env_path)

    pending_csv = Path(args.pending_csv) if args.pending_csv else (work_root / "elsevier_retry_pending.csv")
    log_csv = Path(args.log_csv) if args.log_csv else (work_root / "elsevier_html_retry_log.csv")
    profile = work_root / f"chrome_profile_{args.profile_name}"
    chrome_exe = Path(args.chrome_exe)

    with pending_csv.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not args.no_priority:
        rows.sort(key=year_priority_key)

    done = already_done_paper_ids(log_csv) if args.skip_done else set()
    if done:
        print(f"[skip-done] 이미 success 기록된 {len(done)}편 skip")

    print(f"[main] total rows: {len(rows)} | total_chunks={args.total_chunks} | chunk_size={args.chunk_size} | chunk_wait={args.chunk_wait}s")

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            executable_path=str(chrome_exe),
            headless=False,
            ignore_https_errors=True,
            args=["--no-first-run", "--start-maximized"],
        )
        page = ctx.new_page()

        if not args.no_warmup:
            print("[warmup] navigating to sciencedirect.com main + wait 10s...")
            try:
                page.goto("https://www.sciencedirect.com/", wait_until="networkidle", timeout=120000)
                time.sleep(10)
            except Exception as exc:
                print(f"[warmup] WARN: {exc}")

        any_rate_limited = False
        for chunk_n in range(args.total_chunks):
            cs = args.chunk_start + chunk_n * args.chunk_size
            chunk_all = rows[cs: cs + args.chunk_size]
            chunk = [r for r in chunk_all if r["paper_id"] not in done]
            print(f"\n{'='*70}")
            print(f"[chunk {chunk_n+1}/{args.total_chunks}] start_idx={cs} size_raw={len(chunk_all)} size_after_skip={len(chunk)}")
            print(f"{'='*70}")
            if not chunk:
                print("  (skipping -- no rows after skip-done)")
                continue
            rl = process_chunk(page, chunk, cs, args, log_csv)
            if rl:
                any_rate_limited = True
                print(f"\n[WARN] chunk {chunk_n+1} RATE LIMITED -- 모든 chunk 중단")
                break
            # 마지막 chunk 아니면 wait
            if chunk_n < args.total_chunks - 1:
                print(f"\n[chunk-wait] {args.chunk_wait}s sleep before next chunk...")
                time.sleep(args.chunk_wait)

        ctx.close()

    print(f"\n{'='*70}")
    if any_rate_limited:
        print(f"FINAL: rate-limited stop. 진행 완료된 paper는 {log_csv.name}에 보존")
    else:
        print(f"FINAL: 모든 chunk 완료 (total_chunks={args.total_chunks})")
    print(f"log: {log_csv}")


if __name__ == "__main__":
    main()
