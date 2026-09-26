"""manual_ingest.py — sci-retr skill scripts.

manual_pdf_dropbox/{paper_id}/ 에 수동으로 drop된 PDF를 검증 후
papers/{paper_id}/ 표준 폴더로 promote.

원본 logic 보존 + 일반화 변경:
  - hardcoded PHASE1_ROOT/WORK_ROOT/MANUAL_DROPBOX/INGEST_LOG_CSV → --kb-root / --batch-name / --work-dir 인자
  - from v02_590batch_claude_runner import ... → from runner import ...
  - load_dotenv(env_path) 패턴 추가

처리 흐름:
  1. manual_pdf_dropbox/ 하위 폴더 스캔
  2. 각 폴더의 request.json 에서 paper metadata 읽기
  3. PDF 파일 탐색 ({paper_id}.pdf 우선, 없으면 첫 번째 .pdf)
  4. PDF magic 검증 → write_pdf_source 호출 (내부 classify_content 포함)
  5. 성공 시 request.json status="ingested" 갱신 + append_source_origin
  6. 실패 시 request.json status="ingest_failed" + reason 갱신
  7. PDF 없으면 status="awaiting_pdf" (변경 없음)

출력:
  - ingest_log.csv (utf-8-sig BOM, 이후 append는 utf-8)

CLI 사용:
    python manual_ingest.py --kb-root <path> --batch-name <name> [--paper-id ID] [--all] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- runner import ---
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import (  # noqa: E402
    Paper,
    CollectionResult,
    write_pdf_source,
    classify_content,
    page_range_indicates_multiple_pages,
    paper_dir,
    ensure_paper_dirs,
    source_frontmatter,
    load_source_json,
    backup_source_md,
    append_source_origin,
    utc_now,
    is_pdf,
    load_dotenv,
    get_paths,
    configure,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INGEST_LOG_FIELDS = [
    "paper_id",
    "doi",
    "publisher",
    "pdf_filename",
    "success",
    "content_status",
    "content_length_chars",
    "n_pdf_pages",
    "n_pdf_extracted_images",
    "ingested_at",
    "error_message",
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def archive_existing(path: Path) -> None:
    """기존 파일을 .archive_<utc_ts> 로 rename (runner 동일 패턴)."""
    if path.exists():
        archive = path.with_suffix(path.suffix + f".archive_{utc_stamp()}")
        path.rename(archive)


# ---------------------------------------------------------------------------
# CSV append (runner의 append_csv 패턴과 동일)
# ---------------------------------------------------------------------------
def append_ingest_csv(rows: list[dict[str, str]], ingest_log_csv: Path) -> None:
    """첫 write만 utf-8-sig BOM + 헤더, 이후 append는 utf-8 (BOM 없음)."""
    if not rows:
        return
    ingest_log_csv.parent.mkdir(parents=True, exist_ok=True)
    exists = ingest_log_csv.exists() and ingest_log_csv.stat().st_size > 0
    if exists:
        with ingest_log_csv.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=INGEST_LOG_FIELDS)
            for row in rows:
                writer.writerow(row)
    else:
        with ingest_log_csv.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=INGEST_LOG_FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


# ---------------------------------------------------------------------------
# request.json 읽기
# ---------------------------------------------------------------------------
def load_request_json(folder: Path) -> dict | None:
    req_path = folder / "request.json"
    if not req_path.exists():
        return None
    try:
        return json.loads(req_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def save_request_json(folder: Path, data: dict) -> None:
    req_path = folder / "request.json"
    req_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_paper_from_request(req: dict) -> Paper:
    """request.json 필드로 Paper 객체 생성.

    Paper dataclass 필드:
        paper_id, doi, title, year, scope_label,
        is_curated_pathway, publisher, agent
    request.json 에 없는 is_curated_pathway, agent는 기본값으로 채움.
    """
    return Paper(
        paper_id=str(req.get("paper_id", "")),
        doi=str(req.get("doi", "")),
        title=str(req.get("title", "")),
        year=str(req.get("year", "")),
        scope_label=str(req.get("scope_label", "")),
        is_curated_pathway=str(req.get("is_curated_pathway", "false")),
        publisher=str(req.get("publisher", "unknown")),
        agent="manual_ingest",
    )


# ---------------------------------------------------------------------------
# PDF 파일 탐색 (paper_id.pdf 우선, 없으면 첫 번째 .pdf)
# ---------------------------------------------------------------------------
def find_pdf_in_folder(folder: Path, paper_id: str) -> Path | None:
    preferred = folder / f"{paper_id}.pdf"
    if preferred.exists():
        return preferred
    candidates = sorted(folder.glob("*.pdf"))
    return candidates[0] if candidates else None


# ---------------------------------------------------------------------------
# 단일 paper ingest
# ---------------------------------------------------------------------------
def ingest_paper(folder: Path, dry_run: bool = False) -> dict[str, str]:
    """한 paper_id 폴더를 처리하고 ingest_log.csv 1행 반환."""
    paper_id = folder.name
    req = load_request_json(folder)

    # request.json 없으면 skip row 반환
    if req is None:
        print(f"[ingest] {paper_id} skip (request.json 없음)")
        return {
            "paper_id": paper_id,
            "doi": "",
            "publisher": "",
            "pdf_filename": "",
            "success": "skip",
            "content_status": "",
            "content_length_chars": "",
            "n_pdf_pages": "",
            "n_pdf_extracted_images": "",
            "ingested_at": "",
            "error_message": "request.json 없음",
        }

    paper = build_paper_from_request(req)
    pdf_path = find_pdf_in_folder(folder, paper_id)

    # PDF 없으면 awaiting
    if pdf_path is None:
        print(f"[ingest] {paper_id} awaiting (PDF 없음)")
        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": "",
            "success": "awaiting",
            "content_status": "",
            "content_length_chars": "",
            "n_pdf_pages": "",
            "n_pdf_extracted_images": "",
            "ingested_at": "",
            "error_message": "",
        }

    if dry_run:
        print(f"[ingest] {paper_id} dry-run -> PDF 발견: {pdf_path.name}")
        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": pdf_path.name,
            "success": "dry_run",
            "content_status": "",
            "content_length_chars": "",
            "n_pdf_pages": "",
            "n_pdf_extracted_images": "",
            "ingested_at": "",
            "error_message": "",
        }

    # PDF 바이트 읽기
    try:
        pdf_bytes = pdf_path.read_bytes()
    except Exception as exc:
        error_msg = f"PDF 파일 읽기 실패: {type(exc).__name__}: {exc}"
        print(f"[ingest] {paper_id} failed ({error_msg})")
        req.update({"status": "ingest_failed", "reason": error_msg, "attempted_at": utc_now()})
        save_request_json(folder, req)
        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": pdf_path.name,
            "success": "false",
            "content_status": "reject",
            "content_length_chars": "",
            "n_pdf_pages": "",
            "n_pdf_extracted_images": "",
            "ingested_at": "",
            "error_message": error_msg,
        }

    # PDF magic 검증
    if not is_pdf(pdf_bytes):
        error_msg = f"PDF magic bytes 불일치: {pdf_path.name} (첫 5바이트: {pdf_bytes[:5]!r})"
        print(f"[ingest] {paper_id} failed ({error_msg})")
        req.update({"status": "ingest_failed", "reason": error_msg, "attempted_at": utc_now()})
        save_request_json(folder, req)
        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": pdf_path.name,
            "success": "false",
            "content_status": "reject",
            "content_length_chars": "",
            "n_pdf_pages": "",
            "n_pdf_extracted_images": "",
            "ingested_at": "",
            "error_message": error_msg,
        }

    # CollectionResult 초기화 + write_pdf_source 호출
    result = CollectionResult(
        paper=paper,
        attempt_method="manual_dropbox_ingest",
        started_at=utc_now(),
    )

    try:
        write_pdf_source(paper, pdf_bytes, "manual_dropbox_ingest", result)
        # A1 (2026-05-29): success 마킹 전 validate_collected_paper 6종 검증.
        from validate import validate_collected_paper
        _v = validate_collected_paper(paper.paper_id, paper_dir(paper), paper.doi, paper.publisher)
        if not _v["success"]:
            raise RuntimeError("validate failed: " + "; ".join(_v["issues"]))
        result.success = True
        result.completed_at = utc_now()

        # request.json 성공 갱신
        req.update(
            {
                "status": "ingested",
                "ingested_at": result.completed_at,
                "content_status": result.content_status,
                "content_length_chars": result.content_length_chars,
            }
        )
        save_request_json(folder, req)

        # source_origin.txt append
        append_source_origin(paper, result)

        print(
            f"[ingest] {paper_id} success "
            f"(status={result.content_status} chars={result.content_length_chars} "
            f"pages={result.n_pdf_pages} images={result.n_pdf_extracted_images})"
        )
        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": pdf_path.name,
            "success": "true",
            "content_status": result.content_status,
            "content_length_chars": str(result.content_length_chars),
            "n_pdf_pages": str(result.n_pdf_pages),
            "n_pdf_extracted_images": str(result.n_pdf_extracted_images),
            "ingested_at": result.completed_at,
            "error_message": "",
        }

    except RuntimeError as exc:
        error_msg = str(exc)
        result.completed_at = utc_now()
        print(f"[ingest] {paper_id} failed ({error_msg[:120]})")

        req.update({"status": "ingest_failed", "reason": error_msg[:1000], "attempted_at": result.completed_at})
        save_request_json(folder, req)

        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": pdf_path.name,
            "success": "false",
            "content_status": result.content_status,
            "content_length_chars": str(result.content_length_chars) if result.content_length_chars else "",
            "n_pdf_pages": str(result.n_pdf_pages) if result.n_pdf_pages else "",
            "n_pdf_extracted_images": str(result.n_pdf_extracted_images) if result.n_pdf_extracted_images else "",
            "ingested_at": "",
            "error_message": error_msg[:500],
        }

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        result.completed_at = utc_now()
        print(f"[ingest] {paper_id} failed unexpected ({error_msg[:120]})")

        req.update({"status": "ingest_failed", "reason": error_msg[:1000], "attempted_at": result.completed_at})
        save_request_json(folder, req)

        return {
            "paper_id": paper_id,
            "doi": paper.doi,
            "publisher": paper.publisher,
            "pdf_filename": pdf_path.name,
            "success": "false",
            "content_status": getattr(result, "content_status", "reject"),
            "content_length_chars": "",
            "n_pdf_pages": "",
            "n_pdf_extracted_images": "",
            "ingested_at": "",
            "error_message": error_msg[:500],
        }


# ---------------------------------------------------------------------------
# 전체 스캔
# ---------------------------------------------------------------------------
def collect_folders(paper_ids: list[str] | None, manual_dropbox: Path) -> list[Path]:
    """manual_pdf_dropbox/ 에서 처리 대상 폴더 목록 반환."""
    if not manual_dropbox.exists():
        print(f"[ingest] manual_pdf_dropbox 폴더가 없습니다: {manual_dropbox}")
        return []

    if paper_ids:
        folders = []
        for pid in paper_ids:
            folder = manual_dropbox / pid
            if folder.is_dir():
                folders.append(folder)
            else:
                print(f"[ingest] {pid} 폴더 없음, skip")
        return folders

    return sorted(
        f for f in manual_dropbox.iterdir() if f.is_dir()
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="manual PDF dropbox ingest -- 수동 드롭된 PDF를 papers/ 로 promote"
    )
    parser.add_argument("--kb-root", default=None,
                        help="KB 최상위 경로 (환경변수 KB_ROOT 대체 가능)")
    parser.add_argument("--batch-name", default=None,
                        help="작업 폴더명 (기본: batch_<utc_yyyymmdd>)")
    parser.add_argument("--work-dir", default=None,
                        help="직접 work 디렉터리 경로 지정 (--batch-name 무시)")
    parser.add_argument("--env-path", default=None,
                        help=".env 파일 경로 (기본: kb_root/.env)")
    parser.add_argument("--agent", default=os.environ.get("AGENT_NAME", "claude"),
                        help="작업자 이름 (claude/codex, 기본: claude / 환경변수 AGENT_NAME)")
    parser.add_argument("--chrome-exe",
                        default=os.environ.get("CHROME_EXE", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                        help="Chrome 실행 경로 (환경변수 CHROME_EXE 대체 가능)")
    parser.add_argument(
        "--paper-id",
        dest="paper_ids",
        metavar="ID",
        action="append",
        default=None,
        help="특정 paper_id만 처리 (반복 가능). 생략 시 --all 동작.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="manual_pdf_dropbox 전체 스캔 (--paper-id 없을 때 기본 동작과 동일).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="실제 처리 없이 PDF 발견 여부만 출력.",
    )
    parser.add_argument(
        "--keep-logs",
        action="store_true",
        default=False,
        help="기존 ingest_log.csv 를 archive 하지 않음 (기본은 archive 후 새 파일).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    paths = get_paths(args)
    # runner module globals 초기화 (write_pdf_source / paper_dir / append_source_origin 등 호출 전 필수)
    configure(paths, args.agent, args.chrome_exe)
    work_root = paths["work_root"]

    env_path = Path(args.env_path) if args.env_path else (paths["kb_root"] / ".env")
    load_dotenv(env_path)

    manual_dropbox = work_root / "manual_pdf_dropbox"
    ingest_log_csv = work_root / "ingest_log.csv"

    # 기존 로그 archive (--keep-logs 없으면)
    if not args.keep_logs and not args.dry_run:
        archive_existing(ingest_log_csv)

    folders = collect_folders(args.paper_ids, manual_dropbox)
    if not folders:
        print("[ingest] 처리할 폴더가 없습니다.")
        return

    n_ingested = 0
    n_failed = 0
    n_awaiting = 0

    for folder in folders:
        try:
            row = ingest_paper(folder, dry_run=args.dry_run)
        except KeyboardInterrupt:
            print("\n[ingest] KeyboardInterrupt -- 진행분은 ingest_log.csv에 보존됨.")
            raise
        except Exception as exc:
            # 예상치 못한 최상위 예외: 로그만 남기고 계속
            paper_id = folder.name
            row = {
                "paper_id": paper_id,
                "doi": "",
                "publisher": "",
                "pdf_filename": "",
                "success": "false",
                "content_status": "reject",
                "content_length_chars": "",
                "n_pdf_pages": "",
                "n_pdf_extracted_images": "",
                "ingested_at": "",
                "error_message": f"상위 예외: {type(exc).__name__}: {exc}"[:500],
            }
            print(f"[ingest] {paper_id} failed top-level ({type(exc).__name__}: {exc})")

        success_val = row.get("success", "")
        if success_val == "true":
            n_ingested += 1
        elif success_val in ("false",):
            n_failed += 1
        elif success_val == "awaiting":
            n_awaiting += 1

        # dry_run 이 아닌 경우에만 CSV append (skip/dry_run 행도 기록)
        if not args.dry_run:
            append_ingest_csv([row], ingest_log_csv)

    print(
        f"\n[ingest] 완료 -- total ingested={n_ingested} failed={n_failed} awaiting={n_awaiting}"
    )


if __name__ == "__main__":
    main()
