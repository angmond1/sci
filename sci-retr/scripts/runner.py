"""runner.py — sci-retr skill scripts.

Fulltext / PDF batch recovery runner. 지정된 assignment CSV를 읽어
publisher별 자동 수집 method를 순차 시도하고 결과를 CSV로 기록.

원본 logic 보존 + 일반화 변경:
  - AGENT_NAME hardcode → --agent 인자 (환경변수 AGENT_NAME 대체 가능)
  - PROJECT_ROOT/PHASE1_ROOT/PAPERS_ROOT/WORK_ROOT → --kb-root / --batch-name / --work-dir
  - CHROME_EXE → --chrome-exe 인자 (환경변수 CHROME_EXE 대체 가능)
  - ENV_PATH → --env-path 인자
  - load_dotenv(env_path) 패턴으로 변경
  - collected_by / queued_by 등 AGENT_NAME 참조 → 인자 값 사용

CLI 사용:
    python runner.py --kb-root <path> --batch-name <name> [--agent claude] [--dry-run | --all | --paper-id ID]
"""
from __future__ import annotations

import argparse
import base64
import csv
import html
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, urljoin, urlparse

try:
    import pymupdf as fitz  # pymupdf 1.24+ (옛 이름 fitz 는 경고를 찍는다)
except ImportError:
    import fitz
import requests
import urllib3
from playwright.sync_api import sync_playwright

try:
    from wiley_tdm import TDMClient
except Exception:
    TDMClient = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36; sci-retr"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

ACCESS_WALL_PATTERNS = [
    "sign in to read",
    "purchase access",
    "rent this article",
    "access denied",
    "you do not have access",
    "institutional login",
    "log in via your institution",
    "subscribe to this journal",
]

# Publisher furniture — HTML scrape 시 본문 컨테이너 안에 섞여 들어오는 web UI 위젯.
# (Cited By 목록 / 조회수 통계 / 인용 내보내기 버튼 / 공유 QR / scite 광고 등)
# 2026-05-28 e-epoxidation KB audit 에서 paper_sections 4995 중 1400(28%) furniture 발견.
# strip_html_text 가 본문(line-level)은 보존하면서 이 furniture 줄만 제거.
# ⚠️ content 시작/포함 패턴만 사용 — title-only 판정은 본문 heading(References 등)과
#    충돌하므로 section 적재 단계(furniture_filter.is_furniture)에 위임 (2단 방어).
FURNITURE_LINE_PREFIXES = [
    "this article is cited by",
    "this article has not yet been cited",
    "unable to load citation data",
    "article views are the counter",
    "generating qr code",
    "explore this article's citation statements",
    "reprints and permissions",
    "total unique accesses",
    "eletters is a forum",
    "note: the article usage",
    "- published online",
    "- download -",
]
FURNITURE_LINE_CONTAINS = [
    "click to copy article link",
]
# 짧은 줄이 이것과 *완전 일치* 시 furniture heading (publisher web UI 제목 줄).
# ⚠️ 본문 heading (references / introduction / abstract / results / discussion /
#    conclusion / experimental / methods / recommended articles) 은 절대 미포함.
FURNITURE_EXACT_HEADINGS = {
    "export citation", "cited by", "share qr code", "scite metrics",
    "publication history", "terms & conditions", "how to cite",
    "download citation", "citation manager file format", "citing literature",
    "rights and permissions", "cite this article", "explore related subjects",
    "article metrics", "supporting information available", "additional information",
    "corresponding author", "metrics", "permissions", "reprints and permissions",
    "this pdf file includes:", "(0) eletters", "article usage", "cite as",
    "pdf format", "more options", "log in to view the full text",
}

# 자동 fetch 실패 시 manual queue로 등록할 publisher 그룹
MANUAL_QUEUE_PUBLISHERS = {
    "elsevier",          # 2026-09-23: Insttoken 없음 → 구독 논문은 사용자 확인 묶음(보이는 Chrome, 1클릭/편)
    "world_scientific",
    "csj_chem_lett",
    "pharm_soc_japan",
    "thieme",
    "other_small",
    "unknown",
    "tsinghua_oae",
    "ecs",
    "royal_society",
    "pleiades_springer_ru",
}

# publisher별 수집 interval (초/paper) — 차단 경험 기반 (2026-05-30).
# HTML/browser 기준 보수값. API method (Elsevier Tier0 view=FULL 등)는 _process 에서 3s 로 단축.
# 정책: 1 agent = 1 publisher (편수 아님) → batch 가 단일 publisher 라 interval 일정.
PUBLISHER_INTERVAL = {
    "elsevier": 90.0,   # ScienceDirect "6분20초 29편 IP 차단" 전력 (HTML/browser)
    "acs": 45.0,        # Atypon batch 차단 (90s 과다·30s 위험)
    "science": 30.0,    # browser 보수
    "nature": 15.0,     # 신설(A3), browser 보수
    "wiley": 5.0,       # TDM API
    "rsc": 2.0,         # A그룹 HTTP fetch
    "mdpi": 2.0,
    "springer": 2.0,
    "thieme": 2.0,
    "pharm_soc_japan": 2.0,
    "pleiades_springer_ru": 2.0,
    "tsinghua_oae": 2.0,
    "ecs": 90.0,        # IOP Radware Bot Manager: 반복 자동 요청이 점수를 올려 CAPTCHA 로 전환 (2026-09-23 실측) — 넓은 간격 + 재시도 금지
}


def publisher_interval(publisher: str, default: float) -> float:
    return PUBLISHER_INTERVAL.get(publisher, default)

LOG_FIELDS = [
    "paper_id",
    "doi",
    "publisher",
    "attempt_method",
    "content_source",
    "success",
    "content_status",
    "content_length_chars",
    "n_pdf_pages",
    "n_pdf_extracted_images",
    "n_html_figures",
    "figure_status",
    "pdf_path",
    "html_path",
    "xml_path",
    "source_md_size_bytes",
    "error_message",
    "started_at",
    "completed_at",
    "agent",
]

# 런타임 경로 (parse_args() + get_paths() 후 module-level 변수에 바인딩)
_PATHS: dict[str, Path] = {}
_AGENT_NAME: str = "claude"
_CHROME_EXE: Path = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def configure(paths: dict, agent_name: str, chrome_exe: "str | Path") -> None:
    """다른 script에서 runner 함수를 import할 때 module-level globals를 초기화.

    Usage (from elsevier_html_retry_safe.py / manual_ingest.py main()):
        import runner
        paths = get_paths(args)
        runner.configure(paths, args.agent, args.chrome_exe)
        # 이제 runner의 write_html_source 등 안전하게 호출 가능
    """
    global _PATHS, _AGENT_NAME, _CHROME_EXE
    _PATHS = paths
    _AGENT_NAME = agent_name
    _CHROME_EXE = Path(chrome_exe) if isinstance(chrome_exe, str) else chrome_exe


@dataclass
class Paper:
    paper_id: str
    doi: str
    title: str
    year: str
    scope_label: str
    is_curated_pathway: str
    publisher: str
    agent: str


@dataclass
class CollectionResult:
    paper: Paper
    attempt_method: str = ""
    content_source: str = ""
    success: bool = False
    content_status: str = "reject"
    content_length_chars: int = 0
    n_pdf_pages: int = 0
    n_pdf_extracted_images: int = 0
    n_html_figures: int = 0
    figure_status: str = "none_found"
    pdf_path: str = ""
    html_path: str = ""
    xml_path: str = ""
    source_md_size_bytes: int = 0
    error_message: str = ""
    started_at: str = ""
    completed_at: str = ""
    notes: list[str] = field(default_factory=list)

    def log_row(self) -> dict[str, str]:
        return {
            "paper_id": self.paper.paper_id,
            "doi": self.paper.doi,
            "publisher": self.paper.publisher,
            "attempt_method": self.attempt_method,
            "content_source": self.content_source,
            "success": str(self.success).lower(),
            "content_status": self.content_status,
            "content_length_chars": str(self.content_length_chars),
            "n_pdf_pages": str(self.n_pdf_pages),
            "n_pdf_extracted_images": str(self.n_pdf_extracted_images),
            "n_html_figures": str(self.n_html_figures),
            "figure_status": self.figure_status,
            "pdf_path": self.pdf_path,
            "html_path": self.html_path,
            "xml_path": self.xml_path,
            "source_md_size_bytes": str(self.source_md_size_bytes),
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "agent": _AGENT_NAME,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


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


def request_get(url: str, headers: dict[str, str] | None = None, timeout: int = 45) -> requests.Response:
    merged = dict(HEADERS)
    if headers:
        merged.update(headers)
    return requests.get(url, headers=merged, allow_redirects=True, timeout=timeout, verify=False)


def is_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def paper_dir(paper: Paper) -> Path:
    return _PATHS["papers_root"] / paper.paper_id


def ensure_paper_dirs(paper: Paper) -> dict[str, Path]:
    root = paper_dir(paper)
    paths = {
        "root": root,
        "pdf": root / "pdf",
        "xml": root / "xml",
        "html": root / "html",
        "tables": root / "tables",
        "extraction": root / "extraction",
        "figures": root / "figures",
        "pdf_pages": root / "figures" / "pdf_pages",
        "pdf_extracted": root / "figures" / "pdf_extracted",
        "html_figures": root / "figures" / "html_figures",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def load_source_json(paper: Paper) -> dict:
    path = paper_dir(paper) / "source.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def metadata_value(paper: Paper, source_json: dict, key: str, fallback: str = ""):
    value = source_json.get(key)
    if value not in (None, ""):
        return value
    return fallback


def yaml_scalar(value) -> str:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return '""'
    return json.dumps(str(value), ensure_ascii=False)


def source_frontmatter(
    paper: Paper,
    source_json: dict,
    content_source: str,
    content_length_chars: int,
    method: str,
) -> str:
    title = metadata_value(paper, source_json, "title", paper.title)
    journal = metadata_value(paper, source_json, "journal", "")
    authors = metadata_value(paper, source_json, "authors", [])
    abstract = metadata_value(paper, source_json, "abstract", "")
    lines = [
        "---",
        f"paper_id: {yaml_scalar(paper.paper_id)}",
        f"doi: {yaml_scalar(paper.doi)}",
        f"title: {yaml_scalar(title)}",
        f"year: {yaml_scalar(metadata_value(paper, source_json, 'year', paper.year))}",
        f"journal: {yaml_scalar(journal)}",
        f"authors: {yaml_scalar(authors if isinstance(authors, list) else [])}",
        f"publisher: {yaml_scalar(paper.publisher)}",
        f"content_source: {yaml_scalar(content_source)}",
        f"content_length_chars: {content_length_chars}",
        f"collected_at: {yaml_scalar(utc_now())}",
        f'collected_by: "{_AGENT_NAME}"',
        f"collection_method: {yaml_scalar(method)}",
        "---",
        "",
        f"# {title or paper.paper_id}",
        "",
    ]
    if abstract:
        lines.extend(["## Abstract", "", str(abstract).strip(), ""])
    return "\n".join(lines)


def backup_source_md(paper: Paper) -> None:
    root = paper_dir(paper)
    source = root / "source.md"
    batch_name = _PATHS["work_root"].name
    backup = root / f"source_pre_{batch_name}.md"
    if source.exists() and not backup.exists():
        shutil.copy2(source, backup)


def append_source_origin(paper: Paper, result: CollectionResult) -> None:
    origin = paper_dir(paper) / "source_origin.txt"
    batch_name = _PATHS["work_root"].name
    line = (
        f"{batch_name}: collected by {_AGENT_NAME}, "
        f"method={result.attempt_method}, content_source={result.content_source}, "
        f"content_status={result.content_status}, length={result.content_length_chars} chars, "
        f"n_pdf_pages={result.n_pdf_pages}, n_pdf_extracted_images={result.n_pdf_extracted_images}, "
        f"n_html_figures={result.n_html_figures}, figure_status={result.figure_status}, "
        f"success={str(result.success).lower()}, completed_at={result.completed_at}"
    )
    if result.notes:
        line += ", notes=" + " ; ".join(result.notes[:4]).replace("\n", " ")[:500]
    existing = ""
    if origin.exists():
        existing = origin.read_text(encoding="utf-8", errors="ignore")
        if existing and not existing.endswith("\n"):
            existing += "\n"
    origin.write_text(existing + line + "\n", encoding="utf-8")


def normalize_for_match(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def title_tokens(title: str) -> list[str]:
    stop = {
        "and", "the", "with", "for", "from", "into",
        "based", "using", "various", "associated",
    }
    return [t for t in re.findall(r"[A-Za-z0-9]+", title.lower()) if len(t) >= 5 and t not in stop]


def content_matches_metadata(text: str, paper: Paper) -> bool:
    normalized_text = normalize_for_match(text[:20000])
    doi_norm = normalize_for_match(paper.doi)
    if doi_norm and doi_norm in normalized_text:
        return True
    tokens = title_tokens(paper.title)
    if not tokens:
        return True
    hits = sum(1 for token in tokens[:8] if token in normalized_text)
    return hits >= min(3, max(1, len(tokens[:8])))


def has_article_structure(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in ["references", "experimental", "results", "discussion", "figure", "scheme"])


def has_access_wall(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in ACCESS_WALL_PATTERNS)


def classify_content(text: str, paper: Paper) -> tuple[bool, str, str]:
    length = len(text.strip())
    meta_match = content_matches_metadata(text, paper)
    wall = has_access_wall(text)
    if length >= 3000 and meta_match and not wall:
        return True, "full", ""
    if 1500 <= length < 3000 and meta_match and has_article_structure(text) and not wall:
        return True, "short_fulltext_possible", ""
    reason = []
    if length < 1500:
        reason.append(f"content length {length} < 1500")
    if not meta_match:
        reason.append("DOI/title match failed")
    if wall:
        reason.append("access-wall keyword detected")
    if 1500 <= length < 3000 and not has_article_structure(text):
        reason.append("short text lacks references/captions/article structure")
    return False, "reject", "; ".join(reason) or "content rejected"


def page_range_indicates_multiple_pages(*texts: str) -> bool:
    joined = "\n".join(texts)
    patterns = [
        r"<prism:pageRange>\s*(\d+)\s*[-–]\s*(\d+)\s*</prism:pageRange>",
        r"\b(?:pages?|pp\.?)\s+(\d+)\s*[-–]\s*(\d+)\b",
        r"\b\d+\s*,\s*(\d+)\s*[-–]\s*(\d+)\s*\(\d{4}\)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, joined, flags=re.I):
            try:
                start, end = int(match.group(1)), int(match.group(2))
            except ValueError:
                continue
            if end > start:
                return True
    return False


def strip_html_text(raw_html: str) -> str:
    body = raw_html
    article_match = re.search(r"<article\b.*?</article>", body, flags=re.I | re.S)
    if article_match:
        body = article_match.group(0)
    else:
        for marker in [
            r'id=["\']pnlArticleContent["\']',
            r'class=["\'][^"\']*article__body[^"\']*["\']',
            r'class=["\'][^"\']*c-article-body[^"\']*["\']',
            r'id=["\']article-content["\']',
            r'id=["\']ContentTab["\']',
        ]:
            marker_match = re.search(marker, body, flags=re.I)
            if marker_match:
                body = body[max(0, marker_match.start() - 1000):]
                break
    body = re.sub(r"<(script|style|noscript|svg|header|footer|nav)\b.*?</\1>", " ", body, flags=re.I | re.S)
    body = re.sub(r"</(p|div|h[1-6]|li|tr|section|article|figcaption)>", "\n", body, flags=re.I)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    lines = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines()]
    lines = [line for line in lines if line]
    # publisher furniture 줄 제거 (본문 line 은 보존)
    lines = [line for line in lines if not is_furniture_line(line)]
    return "\n".join(lines).strip()


def is_furniture_line(line: str) -> bool:
    """text 한 줄이 publisher furniture (web UI 위젯) 인지 판정.

    content 시작/포함 패턴만 사용 — 본문 보존을 위해 보수적.
    title-only furniture (Export citation 단독 줄 등) 는 section 적재 단계
    (furniture_filter.is_furniture) 에 위임.
    """
    ll = line.strip().lower()
    if not ll:
        return False
    if any(ll.startswith(p) for p in FURNITURE_LINE_PREFIXES):
        return True
    if any(frag in ll for frag in FURNITURE_LINE_CONTAINS):
        return True
    # title-only furniture heading — 짧은 줄(≤ 6 words) 이 furniture heading 과 완전일치.
    # 본문 heading (References / Introduction 등) 은 FURNITURE_EXACT_HEADINGS 에 없어 보존.
    if len(ll.split()) <= 6 and ll.rstrip(":").strip() in FURNITURE_EXACT_HEADINGS:
        return True
    return False


def meta_content(raw_html: str, names: Iterable[str]) -> list[str]:
    values: list[str] = []
    for name in names:
        patterns = [
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, raw_html, flags=re.I):
                values.append(html.unescape(match.group(1).replace("&amp;", "&")))
    return values


def landing_page(doi: str) -> tuple[str, str]:
    response = request_get("https://doi.org/" + doi, timeout=45)
    return response.url, response.text


def html_pdf_candidates(raw_html: str, base_url: str) -> list[str]:
    candidates = []
    candidates.extend(meta_content(raw_html, ["citation_pdf_url", "bepress_citation_pdf_url"]))
    patterns = [
        r'href=["\']([^"\']*(?:articlepdf|/pdf|/doi/pdf|/doi/epdf|download[^"\']*pdf)[^"\']*)["\']',
        r'data-download-url=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, raw_html, flags=re.I):
            candidates.append(match.group(1).replace("&amp;", "&"))
    return list(dict.fromkeys(urljoin(base_url, c) for c in candidates if c and not c.startswith("#")))[:20]


def html_fulltext_candidates(raw_html: str, base_url: str) -> list[str]:
    candidates = []
    candidates.extend(meta_content(raw_html, ["citation_fulltext_html_url"]))
    for pattern in [
        r'href=["\']([^"\']*(?:articlehtml|full|fulltext)[^"\']*)["\']',
    ]:
        for match in re.finditer(pattern, raw_html, flags=re.I):
            candidates.append(match.group(1).replace("&amp;", "&"))
    return list(dict.fromkeys(urljoin(base_url, c) for c in candidates if c and not c.startswith("#")))[:12]


def attr_value(tag: str, attr: str) -> str:
    match = re.search(rf'\b{re.escape(attr)}\s*=\s*["\']([^"\']+)["\']', tag, flags=re.I)
    return html.unescape(match.group(1).replace("&amp;", "&")) if match else ""


def likely_article_image(src: str, alt: str) -> bool:
    lower = (src + " " + alt).lower()
    bad = ["logo", "sprite", "icon", "facebook", "twitter", "linkedin", "pixel", "blank", "avatar", "captcha"]
    if any(token in lower for token in bad):
        return False
    good = ["figure", "fig", "scheme", "graphical", "image", "article", "gr", "fx"]
    if any(token in lower for token in good):
        return True
    return bool(re.search(r"\.(png|jpe?g|webp|gif|svg)(?:\?|$)", lower))


def extract_caption_near(raw_html: str, start: int, end: int) -> str:
    window = raw_html[max(0, start - 1200): min(len(raw_html), end + 1800)]
    match = re.search(r"<figcaption\b[^>]*>(.*?)</figcaption>", window, flags=re.I | re.S)
    if not match:
        match = re.search(r'<[^>]+class=["\'][^"\']*caption[^"\']*["\'][^>]*>(.*?)</[^>]+>', window, flags=re.I | re.S)
    if not match:
        return ""
    return strip_html_text(match.group(1))[:2000]


def download_html_figures(raw_html: str, base_url: str, paper: Paper) -> tuple[int, str, list[str]]:
    paths = ensure_paper_dirs(paper)
    notes: list[str] = []
    img_matches = list(re.finditer(r"<img\b[^>]*>", raw_html, flags=re.I | re.S))
    candidates: list[tuple[str, str]] = []
    for index, match in enumerate(img_matches, start=1):
        tag = match.group(0)
        src = attr_value(tag, "src") or attr_value(tag, "data-src") or attr_value(tag, "data-original")
        alt = attr_value(tag, "alt")
        if not src or src.startswith("data:") or not likely_article_image(src, alt):
            continue
        candidates.append((urljoin(base_url, src), extract_caption_near(raw_html, match.start(), match.end())))
    unique = []
    seen = set()
    for url, caption in candidates:
        if url in seen:
            continue
        seen.add(url)
        unique.append((url, caption))

    downloaded = 0
    for fig_index, (url, caption) in enumerate(unique[:80], start=1):
        try:
            response = request_get(url, headers={"Accept": "image/avif,image/webp,image/png,image/jpeg,image/svg+xml,*/*"}, timeout=30)
            if response.status_code != 200 or not response.content:
                notes.append(f"figure download failed status={response.status_code} url={url}")
                continue
            parsed = urlparse(response.url)
            suffix = Path(parsed.path).suffix.lower()
            ctype = response.headers.get("content-type", "").lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
                if "svg" in ctype:
                    suffix = ".svg"
                elif "png" in ctype:
                    suffix = ".png"
                elif "jpeg" in ctype or "jpg" in ctype:
                    suffix = ".jpg"
                elif "webp" in ctype:
                    suffix = ".webp"
                else:
                    suffix = ".img"
            fig_path = paths["html_figures"] / f"figure_{fig_index:03d}{suffix}"
            fig_path.write_bytes(response.content)
            (paths["html_figures"] / f"figure_{fig_index:03d}_caption.txt").write_text(caption, encoding="utf-8")
            downloaded += 1
        except Exception as exc:
            notes.append(f"figure download exception url={url}: {type(exc).__name__}: {exc}")
    if unique and downloaded == 0:
        return 0, "extraction_failed", notes
    if downloaded > 0:
        return downloaded, "extracted", notes
    return 0, "none_found", notes


def write_html_source(
    paper: Paper,
    raw_html: str,
    final_url: str,
    method: str,
    result: CollectionResult,
) -> None:
    paths = ensure_paper_dirs(paper)
    source_json = load_source_json(paper)
    backup_source_md(paper)
    html_path = paths["html"] / f"{paper.paper_id}.html"
    html_path.write_text(raw_html, encoding="utf-8", errors="ignore")
    text = strip_html_text(raw_html)
    n_figures, figure_status, figure_notes = download_html_figures(raw_html, final_url, paper)
    result.notes.extend(figure_notes)
    md_lines = [
        source_frontmatter(paper, source_json, "html", len(text), method),
        f"- HTML source URL: {final_url}",
        "",
        "## Extracted HTML Text",
        "",
        text,
        "",
    ]
    if n_figures:
        md_lines.extend(["## Downloaded HTML Figures", ""])
        for fig in sorted(paths["html_figures"].glob("figure_*.*")):
            if fig.name.endswith("_caption.txt"):
                continue
            md_lines.append(f"- `{fig.relative_to(paths['root'])}`")
        md_lines.append("")
    source_path = paths["root"] / "source.md"
    source_path.write_text("\n".join(md_lines), encoding="utf-8")
    result.content_source = "html"
    result.content_length_chars = len(text)
    result.html_path = str(html_path)
    result.n_html_figures = n_figures
    result.figure_status = figure_status
    result.source_md_size_bytes = source_path.stat().st_size


def write_pdf_source(
    paper: Paper,
    pdf_bytes: bytes,
    method: str,
    result: CollectionResult,
    xml_bytes: bytes | None = None,
) -> None:
    result.content_source = "pdf"
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result.n_pdf_pages = doc.page_count
    text_parts = []
    for page_index, page in enumerate(doc, start=1):
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", page.get_text("text") or "")   # sort=True 는 두 단 줄을 섞음 (2026-09-24). 제어 문자(NUL) 제거 (2026-09-26)
        text_parts.append(f"## Page {page_index}\n\n{text.strip()}\n")
    full_text = "\n\n".join(text_parts).strip()
    result.content_length_chars = len(full_text)
    xml_text = xml_bytes.decode("utf-8", errors="ignore") if xml_bytes else ""
    if doc.page_count <= 1 and page_range_indicates_multiple_pages(full_text, xml_text):
        result.content_status = "reject"
        raise RuntimeError("PDF appears to be first-page partial: page range indicates multi-page article")
    ok, status, reason = classify_content(full_text, paper)
    result.content_status = status
    if not ok:
        raise RuntimeError(f"PDF content rejected: {reason}")

    paths = ensure_paper_dirs(paper)
    source_json = load_source_json(paper)
    backup_source_md(paper)
    pdf_path = paths["pdf"] / f"{paper.paper_id}.pdf"
    pdf_path.write_bytes(pdf_bytes)
    result.pdf_path = str(pdf_path)

    if xml_bytes:
        xml_path = paths["xml"] / f"{paper.paper_id}.xml"
        xml_path.write_bytes(xml_bytes)
        result.xml_path = str(xml_path)

    for page_index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        pix.save(str(paths["pdf_pages"] / f"page_{page_index:03d}.png"))

    seen_xrefs: set[int] = set()
    extracted = 0
    for page_index, page in enumerate(doc, start=1):
        for image in page.get_images(full=True):
            xref = image[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                image_data = doc.extract_image(xref)
                ext = image_data.get("ext", "png")
                image_path = paths["pdf_extracted"] / f"extracted_p{page_index:03d}_xref{xref}.{ext}"
                image_path.write_bytes(image_data["image"])
                extracted += 1
            except Exception as exc:
                result.notes.append(f"embedded image extraction failed xref={xref}: {type(exc).__name__}: {exc}")
    result.n_pdf_extracted_images = extracted
    result.figure_status = "extracted" if result.n_pdf_pages > 0 or extracted > 0 else "none_found"

    source_path = paths["root"] / "source.md"
    source_path.write_text(
        "\n".join(
            [
                source_frontmatter(paper, source_json, "pdf", len(full_text), method),
                f"- PDF path: `{pdf_path}`",
                "",
                "## Extracted Full Text",
                "",
                full_text,
                "",
            ]
        ),
        encoding="utf-8",
    )
    result.source_md_size_bytes = source_path.stat().st_size


def crossref_links(doi: str) -> list[dict]:
    try:
        response = request_get("https://api.crossref.org/works/" + doi, headers={"User-Agent": "sci-retr"})
        if response.status_code != 200:
            return []
        return response.json().get("message", {}).get("link", []) or []
    except Exception:
        return []


def elsevier_pii_candidates(paper: Paper) -> list[str]:
    candidates: list[str] = []
    source_json = load_source_json(paper)
    for key in ["final_url", "pdf_url", "requested_url", "source_entry"]:
        value = str(source_json.get(key) or "")
        match = re.search(r"/pii/([^/?#]+)", value, flags=re.I)
        if match:
            candidates.append(match.group(1))
        match = re.search(r"PII:([^/?#]+)", value, flags=re.I)
        if match:
            candidates.append(match.group(1))
    for link in crossref_links(paper.doi):
        url = link.get("URL", "")
        match = re.search(r"/content/article/PII:([^?]+)", url, flags=re.I)
        if match:
            candidates.append(match.group(1))
    suffix = paper.doi.split("/", 1)[1] if "/" in paper.doi else paper.doi
    candidates.append(re.sub(r"[^A-Za-z0-9]", "", suffix))
    return list(dict.fromkeys(candidates))


def elsevier_web_pdf_candidates(paper: Paper) -> tuple[str, list[str]]:
    source_json = load_source_json(paper)
    article_url = str(source_json.get("final_url") or "")
    if not article_url:
        try:
            article_url, _ = landing_page(paper.doi)
        except Exception:
            article_url = "https://www.sciencedirect.com/"
    candidates: list[str] = []
    for pii in elsevier_pii_candidates(paper):
        candidates.extend(
            [
                f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true",
                f"https://www.sciencedirect.com/science/article/pii/{pii}/pdf?download=true",
            ]
        )
    if "/science/article/pii/" in article_url:
        base = article_url.split("?", 1)[0].rstrip("/")
        candidates.extend([base + "/pdfft?isDTMRedir=true&download=true", base + "/pdf?download=true"])
    return article_url, list(dict.fromkeys(candidates))


def try_direct_pdf_candidates(
    paper: Paper,
    result: CollectionResult,
    candidates: list[str],
    method_prefix: str,
) -> bool:
    for url in candidates:
        try:
            response = request_get(url, headers={"Accept": "application/pdf,*/*"}, timeout=75)
            if response.status_code == 200 and is_pdf(response.content):
                result.attempt_method = f"{method_prefix}_direct_pdf"
                write_pdf_source(paper, response.content, result.attempt_method, result)
                return True
            result.notes.append(
                f"{method_prefix} direct pdf failed status={response.status_code} "
                f"ctype={response.headers.get('content-type', '')} url={url}"
            )
        except Exception as exc:
            result.notes.append(f"{method_prefix} direct pdf exception url={url}: {type(exc).__name__}: {exc}")
    return False


def try_browser_pdf_candidates(
    paper: Paper,
    result: CollectionResult,
    browser: "BrowserCollector | None",
    origin: str,
    candidates: list[str],
    method_prefix: str,
) -> bool:
    if browser is None:
        result.notes.append(f"{method_prefix} browser fallback skipped: browser collector unavailable")
        return False
    for url in candidates:
        try:
            status, ctype, body = browser.fetch_pdf(origin, url)
            if status == 200 and is_pdf(body):
                result.attempt_method = f"{method_prefix}_browser_pdf"
                write_pdf_source(paper, body, result.attempt_method, result)
                return True
            result.notes.append(f"{method_prefix} browser pdf failed status={status} ctype={ctype} url={url}")
        except Exception as exc:
            result.notes.append(f"{method_prefix} browser pdf exception url={url}: {type(exc).__name__}: {exc}")
    return False


def collect_elsevier(paper: Paper, result: CollectionResult, browser: "BrowserCollector | None" = None) -> None:
    api_key = os.environ.get("ELSEVIER_API_KEY")
    if not api_key:
        result.notes.append("missing ELSEVIER_API_KEY")
        endpoints: list[str] = []
        headers = {}
    else:
        headers = {"X-ELS-APIKey": api_key, "User-Agent": "sci-retr Elsevier API"}
        endpoints = [f"https://api.elsevier.com/content/article/doi/{quote(paper.doi, safe='')}"]
        endpoints.extend(f"https://api.elsevier.com/content/article/PII:{pii}" for pii in elsevier_pii_candidates(paper))
    errors: list[str] = []
    not_entitled = False
    for endpoint in endpoints:
        xml_bytes: bytes | None = None
        xml_response = request_get(endpoint + "?httpAccept=text/xml", headers=headers, timeout=60)
        if xml_response.status_code == 200 and xml_response.content.strip().startswith(b"<"):
            xml_bytes = xml_response.content
        pdf_response = request_get(endpoint + "?httpAccept=application/pdf", headers=headers, timeout=90)
        # 2026-09-23 규칙: 기관 토큰(Insttoken) 없음 → 구독 논문은 API 가 첫 페이지만 준다.
        # X-ELS-Status 헤더가 그 사실을 명시하므로 preview 를 저장하지 말고 '사람 확인 필요' 로 분류.
        els_status = (pdf_response.headers.get("X-ELS-Status") or "").lower()
        if "first page" in els_status or "not entitled" in els_status:
            not_entitled = True
            result.notes.append(f"elsevier_api_not_entitled: {els_status[:120]}")
            break
        if pdf_response.status_code == 200 and is_pdf(pdf_response.content):
            result.attempt_method = "elsevier_article_retrieval_api_pdf"
            try:
                write_pdf_source(paper, pdf_response.content, result.attempt_method, result, xml_bytes=xml_bytes)
                return
            except RuntimeError as exc:
                errors.append(f"endpoint={endpoint} content_rejected={exc}")
                continue
        errors.append(
            f"endpoint={endpoint} pdf_status={pdf_response.status_code} "
            f"pdf_ctype={pdf_response.headers.get('content-type', '')} xml_status={xml_response.status_code}"
        )
    if errors:
        result.notes.extend(errors[-5:])
    if not_entitled:
        # 웹 PDF 후보(/pdfft 등)는 ScienceDirect Turnstile 로 자동화에서는 막힘 → 시도하지 않고 사람 확인 묶음으로.
        raise RuntimeError(ELSEVIER_HUMAN_MSG)

    origin, web_candidates = elsevier_web_pdf_candidates(paper)
    if try_direct_pdf_candidates(paper, result, web_candidates, "elsevier_sciencedirect"):
        return
    if try_browser_pdf_candidates(paper, result, browser, origin, web_candidates, "elsevier_sciencedirect"):
        return
    raise RuntimeError(" | ".join((errors + result.notes)[-8:]) or "Elsevier API and web PDF fallbacks failed")


def rsc_articlepdf_candidates(paper: Paper, landing_html: str, landing_url: str) -> list[str]:
    candidates = html_pdf_candidates(landing_html, landing_url)
    suffix = paper.doi.split("/", 1)[1].lower()
    candidates.extend(
        [
            f"https://pubs.rsc.org/en/content/articlepdf/{paper.year}/cc/{suffix}",
            f"https://pubs.rsc.org/en/content/articlepdf/{paper.year}/{suffix}",
        ]
    )
    return list(dict.fromkeys(candidates))


def try_html_first(paper: Paper, result: CollectionResult, method_prefix: str = "html_first") -> bool:
    landing_url, landing_html = landing_page(paper.doi)
    html_candidates = [landing_url]
    html_candidates.extend(html_fulltext_candidates(landing_html, landing_url))
    for url in list(dict.fromkeys(html_candidates)):
        try:
            response = request_get(url, timeout=60)
            raw_html = response.text
            text = strip_html_text(raw_html)
            ok, status, reason = classify_content(text, paper)
            if ok:
                result.attempt_method = f"{method_prefix}_html"
                result.content_status = status
                write_html_source(paper, raw_html, response.url, result.attempt_method, result)
                return True
            result.notes.append(f"html rejected url={url} reason={reason}")
        except Exception as exc:
            result.notes.append(f"html exception url={url}: {type(exc).__name__}: {exc}")
    return False


def collect_rsc(paper: Paper, result: CollectionResult) -> None:
    landing_url, landing_html = landing_page(paper.doi)
    text = strip_html_text(landing_html)
    ok, status, reason = classify_content(text, paper)
    if ok:
        result.attempt_method = "rsc_html_first"
        result.content_status = status
        write_html_source(paper, landing_html, landing_url, result.attempt_method, result)
        return
    result.notes.append(f"rsc landing html rejected: {reason}")
    for url in rsc_articlepdf_candidates(paper, landing_html, landing_url):
        response = request_get(url, headers={"Accept": "application/pdf,*/*"}, timeout=60)
        if response.status_code == 200 and is_pdf(response.content):
            result.attempt_method = "rsc_articlepdf"
            write_pdf_source(paper, response.content, result.attempt_method, result)
            return
        result.notes.append(f"rsc pdf candidate failed status={response.status_code} url={url}")
    raise RuntimeError("RSC HTML/PDF candidates failed")


def wiley_pdf_candidates(paper: Paper) -> tuple[str, list[str]]:
    landing_url = f"https://onlinelibrary.wiley.com/doi/{paper.doi}"
    candidates = [
        f"https://onlinelibrary.wiley.com/doi/pdf/{paper.doi}",
        f"https://onlinelibrary.wiley.com/doi/epdf/{paper.doi}",
    ]
    try:
        resolved_url, raw_html = landing_page(paper.doi)
        landing_url = resolved_url or landing_url
        candidates.extend(html_pdf_candidates(raw_html, landing_url))
    except Exception:
        pass
    return landing_url, list(dict.fromkeys(candidates))


def try_wiley_tdm(paper: Paper, result: CollectionResult) -> bool:
    if TDMClient is None:
        result.notes.append("wiley-tdm package not importable")
        return False
    if not os.environ.get("TDM_API_TOKEN"):
        result.notes.append("missing TDM_API_TOKEN")
        return False
    temp_dir = _PATHS["work_root"] / "_wiley_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    client = TDMClient(download_dir=temp_dir)
    try:
        client._api_session.verify = False
    except Exception:
        pass
    try:
        dl_result = client.download_pdf(paper.doi)
    except Exception as exc:
        result.notes.append(f"wiley_tdm_exception={type(exc).__name__}: {exc}")
        return False
    result.notes.append(f"wiley_result={getattr(dl_result, 'status', '')} api_status={getattr(dl_result, 'api_status', '')}")
    path = getattr(dl_result, "path", None)
    if path and Path(path).exists():
        data = Path(path).read_bytes()
        if is_pdf(data):
            result.attempt_method = "wiley_tdm_api_pdf"
            write_pdf_source(paper, data, result.attempt_method, result)
            return True
        result.notes.append("wiley_tdm_file_not_pdf")
    comment = getattr(dl_result, "comment", "")
    if comment:
        result.notes.append(f"wiley_tdm_comment={comment}")
    return False


def collect_wiley(paper: Paper, result: CollectionResult, browser: "BrowserCollector | None" = None) -> None:
    if try_wiley_tdm(paper, result):
        return
    if try_html_first(paper, result, "wiley"):
        return
    origin, candidates = wiley_pdf_candidates(paper)
    if try_direct_pdf_candidates(paper, result, candidates, "wiley_onlinelibrary"):
        return
    if try_browser_pdf_candidates(paper, result, browser, origin, candidates, "wiley_onlinelibrary"):
        return
    raise RuntimeError("Wiley TDM, HTML, and web PDF fallbacks failed: " + " | ".join(result.notes[-8:]))


def collect_springer(paper: Paper, result: CollectionResult) -> None:
    if try_html_first(paper, result, "springer"):
        return
    candidates = [
        f"https://link.springer.com/content/pdf/{paper.doi}.pdf",
        f"https://link.springer.com/content/pdf/{quote(paper.doi, safe='/:')}.pdf",
    ]
    for url in candidates:
        response = request_get(url, headers={"Accept": "application/pdf,*/*"}, timeout=60)
        if response.status_code == 200 and is_pdf(response.content):
            result.attempt_method = "springer_content_pdf"
            write_pdf_source(paper, response.content, result.attempt_method, result)
            return
        result.notes.append(f"springer pdf candidate failed status={response.status_code} url={url}")
    raise RuntimeError("Springer HTML/PDF candidates failed")


def mdpi_pdf_candidates(paper: Paper) -> list[str]:
    suffix = paper.doi.split("/", 1)[1].lower() if "/" in paper.doi else ""
    urls: list[str] = []
    match = re.match(r"([a-z]+)(\d+)$", suffix)
    if match:
        journal_code, digits = match.groups()
        mdpi_map = {
            "app": ("applsci", "2076-3417"),
            "inorganics": ("inorganics", "2304-6740"),
            "ma": ("materials", "1996-1944"),
            "molecules": ("molecules", "1420-3049"),
            "polym": ("polymers", "2073-4360"),
        }
        if journal_code in mdpi_map and len(digits) >= 8:
            slug, issn = mdpi_map[journal_code]
            volume = int(digits[:2])
            issue = int(digits[2:4])
            article = int(digits[4:])
            urls.append(f"https://mdpi-res.com/d_attachment/{slug}/{slug}-{volume:02d}-{article:05d}/article_deploy/{slug}-{volume:02d}-{article:05d}.pdf")
            urls.append(f"https://www.mdpi.com/{issn}/{volume}/{issue}/{article}/pdf?download=1")
    return urls


def collect_mdpi(paper: Paper, result: CollectionResult) -> None:
    for url in mdpi_pdf_candidates(paper):
        response = request_get(url, headers={"Accept": "application/pdf,*/*"}, timeout=60)
        if response.status_code == 200 and is_pdf(response.content):
            result.attempt_method = "mdpi_direct_pdf"
            write_pdf_source(paper, response.content, result.attempt_method, result)
            return
        result.notes.append(f"mdpi pdf candidate failed status={response.status_code} url={url}")
    if try_html_first(paper, result, "mdpi"):
        return
    raise RuntimeError("MDPI PDF/HTML candidates failed")


ELSEVIER_HUMAN_MSG = (
    "Elsevier: API not entitled (first page only; no Insttoken) - subscribed article needs "
    "user-assisted browser step (ScienceDirect Turnstile click)"
)
IOP_CHALLENGE_MARKERS = (b"validate.perfdrive.com", b"Radware Bot Manager", b"Radware", b"reese84")
IOP_CHALLENGE_MSG = "IOP Radware bot challenge - user click required (no auto retry)"


def _iop_challenged(final_url: str, body: bytes) -> bool:
    """IOPScience 의 Radware Bot Manager(perfdrive) 확인 페이지 여부."""
    if "perfdrive" in (final_url or ""):
        return True
    head = body[:30000] if body else b""
    return any(m in head for m in IOP_CHALLENGE_MARKERS)


def collect_ecs(paper: Paper, result: CollectionResult) -> None:
    """ECS / IOPScience (10.1149).

    2026-09-24 규칙: 일반 requests 로 직접 PDF 를 1회만 시도한다. 봇 확인 페이지(perfdrive/Radware)가
    보이면 우회·재시도 없이 RuntimeError 로 빠져나가 collect_paper 가 manual_pdf_dropbox 큐에 등록하고,
    사용자가 보이는 Chrome 에서 직접 확인한다. TLS 지문 흉내·쿠키 복사·UA 위장 등 탐지 우회는 하지 않는다.
    요청 간격은 PUBLISHER_INTERVAL["ecs"] = 90s.
    """
    landing = f"https://iopscience.iop.org/article/{paper.doi}"
    pdf_url = landing + "/pdf"
    # 일반 requests 로 직접 PDF 1회 (봇 확인 페이지면 즉시 사용자 묶음 — 우회·재시도 없음)
    candidates = [pdf_url, f"https://iopscience.iop.org/article/{quote(paper.doi, safe='/:')}/pdf"]
    for url in candidates:
        response = request_get(url, headers={"Accept": "application/pdf,*/*", "User-Agent": "Mozilla/5.0"}, timeout=75)
        if response.status_code == 200 and is_pdf(response.content):
            result.attempt_method = "ecs_iopscience_direct_pdf"
            write_pdf_source(paper, response.content, result.attempt_method, result)
            return
        if _iop_challenged(response.url, response.content):
            result.notes.append("iop_radware_challenge_on_direct_pdf")
            raise RuntimeError(IOP_CHALLENGE_MSG)
        result.notes.append(
            f"ecs_iopscience direct pdf failed status={response.status_code} "
            f"ctype={response.headers.get('content-type', '')} url={url}"
        )
    if try_html_first(paper, result, "ecs"):
        return
    raise RuntimeError("ECS IOP/HTML candidates failed")


def collect_generic(paper: Paper, result: CollectionResult) -> None:
    if try_html_first(paper, result, f"{paper.publisher}_generic"):
        return
    landing_url, landing_html = landing_page(paper.doi)
    for url in html_pdf_candidates(landing_html, landing_url):
        response = request_get(url, headers={"Accept": "application/pdf,*/*"}, timeout=60)
        if response.status_code == 200 and is_pdf(response.content):
            result.attempt_method = f"{paper.publisher}_landing_pdf"
            write_pdf_source(paper, response.content, result.attempt_method, result)
            return
        result.notes.append(f"generic pdf candidate failed status={response.status_code} url={url}")
    raise RuntimeError("generic HTML/PDF candidates failed")


def queue_for_manual_dropbox(paper: Paper, result: CollectionResult, reason: str) -> None:
    """미확립 publisher의 자동 method 모두 실패 시 사용자 수동 처리용 큐에 등록."""
    manual_dropbox = _PATHS["work_root"] / "manual_pdf_dropbox"
    target = manual_dropbox / paper.paper_id
    target.mkdir(parents=True, exist_ok=True)
    info = {
        "paper_id": paper.paper_id,
        "doi": paper.doi,
        "title": paper.title,
        "year": paper.year,
        "publisher": paper.publisher,
        "scope_label": paper.scope_label,
        "queued_by": _AGENT_NAME,
        "queued_at": utc_now(),
        "reason": reason[:1000],
        "last_attempt_method": result.attempt_method,
        "notes_tail": result.notes[-6:],
    }
    request_path = target / "request.json"
    request_path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    result.notes.append(f"queued_to_manual_dropbox={request_path}")


class BrowserCollector:
    def __init__(self) -> None:
        self._playwright = None
        self._context = None
        self.page = None

    def __enter__(self):
        if not _CHROME_EXE.exists():
            raise FileNotFoundError(f"Chrome executable not found: {_CHROME_EXE}")
        chrome_profile = _PATHS["work_root"] / f"chrome_profile_{_AGENT_NAME}"
        chrome_profile.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(chrome_profile),
            executable_path=str(_CHROME_EXE),
            headless=True,
            accept_downloads=True,
            ignore_https_errors=True,
            user_agent=USER_AGENT,
            args=["--disable-dev-shm-usage", "--no-first-run"],
        )
        self.page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()

    def fetch_pdf(self, origin: str, url: str) -> tuple[int, str, bytes]:
        page = self.page
        assert page is not None
        page.goto(origin, wait_until="domcontentloaded", timeout=60000)
        time.sleep(1.0)
        payload = page.evaluate(
            """async (url) => {
                const response = await fetch(url, {
                    credentials: 'include',
                    headers: {'Accept': 'application/pdf,application/octet-stream,*/*;q=0.8'}
                });
                const contentType = response.headers.get('content-type') || '';
                const buffer = await response.arrayBuffer();
                const bytes = new Uint8Array(buffer);
                let binary = '';
                const chunkSize = 0x8000;
                for (let i = 0; i < bytes.length; i += chunkSize) {
                    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
                }
                return {status: response.status, contentType, bodyBase64: btoa(binary), url: response.url};
            }""",
            url,
        )
        return int(payload.get("status") or 0), payload.get("contentType") or "", base64.b64decode(payload["bodyBase64"])


def collect_acs(paper: Paper, result: CollectionResult, browser: BrowserCollector | None) -> None:
    if try_html_first(paper, result, "acs"):
        return
    if browser is None:
        raise RuntimeError("ACS requires browser collector")
    candidates = [
        f"https://pubs.acs.org/doi/pdf/{paper.doi}",
        f"https://pubs.acs.org/doi/epdf/{paper.doi}",
    ]
    for url in candidates:
        status, ctype, body = browser.fetch_pdf("https://pubs.acs.org/", url)
        if status == 200 and is_pdf(body):
            result.attempt_method = "acs_browser_session_pdf"
            write_pdf_source(paper, body, result.attempt_method, result)
            return
        result.notes.append(f"acs browser candidate failed status={status} ctype={ctype} url={url}")
    raise RuntimeError("ACS browser candidates failed")


def finish_result(result: CollectionResult) -> None:
    if result.content_length_chars:
        source_path = paper_dir(result.paper) / "source.md"
        validation_text = source_path.read_text(encoding="utf-8", errors="ignore") if source_path.exists() else ""
        ok, status, reason = classify_content(validation_text, result.paper)
        result.success = ok
        result.content_status = status
        if not ok and reason:
            result.error_message = reason
        # A1 (2026-05-29): classify_content 통과분에 validate_collected_paper 6종 검증 적용.
        # 그동안 SKILL #9/#12/#19 가 선언만 하던 1-page-preview / paywall fall-through /
        # replacement guard / DOI 매칭을 실제 실행 (validate.py).
        if result.success:
            try:
                from validate import validate_collected_paper
                v = validate_collected_paper(
                    result.paper.paper_id, paper_dir(result.paper),
                    result.paper.doi, result.paper.publisher,
                )
                if not v["success"]:
                    result.success = False
                    result.content_status = "reject"
                    result.error_message = ("validate: " + "; ".join(v["issues"]))[:800]
                    result.notes.append("validate_failed: " + " | ".join(v["issues"]))
            except Exception as exc:
                result.notes.append(f"validate_exception={type(exc).__name__}: {exc}")
    else:
        result.success = False
        result.content_status = "reject"
    if result.success and not result.figure_status:
        result.figure_status = "none_found"
    result.completed_at = utc_now()
    if result.success:
        append_source_origin(result.paper, result)


def collect_paper(paper: Paper, browser: BrowserCollector | None = None) -> CollectionResult:
    result = CollectionResult(paper=paper, started_at=utc_now())
    try:
        if paper.publisher == "elsevier":
            collect_elsevier(paper, result, browser)
        elif paper.publisher == "rsc":
            collect_rsc(paper, result)
        elif paper.publisher == "acs":
            collect_acs(paper, result, browser)
        elif paper.publisher == "wiley":
            collect_wiley(paper, result, browser)
        elif paper.publisher == "springer":
            collect_springer(paper, result)
        elif paper.publisher == "mdpi":
            collect_mdpi(paper, result)
        elif paper.publisher == "ecs":
            collect_ecs(paper, result)
        else:
            collect_generic(paper, result)
        finish_result(result)
    except Exception as exc:
        result.success = False
        result.content_status = "reject"
        result.error_message = (str(exc) or type(exc).__name__)[:1000]
        result.completed_at = utc_now()
        # 미확립 publisher의 자동 method 모두 실패 → manual queue로 등록
        if paper.publisher in MANUAL_QUEUE_PUBLISHERS:
            try:
                queue_for_manual_dropbox(paper, result, f"auto-fetch failed: {result.error_message[:300]}")
            except Exception as queue_exc:
                result.notes.append(f"manual_queue_exception={type(queue_exc).__name__}: {queue_exc}")
    return result


def read_assignment(assignment_csv: Path) -> list[Paper]:
    with assignment_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    papers = [
        Paper(
            paper_id=r["paper_id"].strip(),
            doi=r.get("doi", "").strip(),
            title=r.get("title", "").strip(),
            year=r.get("year", "").strip(),
            scope_label=r.get("scope_label", "").strip(),
            is_curated_pathway=r.get("is_curated_pathway", "").strip(),
            publisher=r.get("publisher", "").strip(),
            agent=r.get("agent", "").strip(),
        )
        for r in rows
    ]
    invalid = [p.paper_id for p in papers if p.agent != _AGENT_NAME]
    if invalid:
        raise RuntimeError(f"assignment contains non-{_AGENT_NAME} rows: {invalid[:5]}")
    return papers


def select_dry_run(papers: list[Paper]) -> list[Paper]:
    """publisher 다양화로 최대 5편 dry-run 선택."""
    order = ["elsevier", "rsc", "springer", "world_scientific", "csj_chem_lett"]
    selected = []
    for publisher in order:
        matches = [p for p in papers if p.publisher == publisher]
        if matches:
            selected.append(matches[0])
    return selected


def append_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """utf-8-sig BOM 버그 수정: 첫 write만 BOM 포함, append는 utf-8 (BOM 없음).

    append_csv는 utf-8-sig를 항상 써서 매 append 시 BOM이 파일 중간에
    삽입될 위험이 있었음 (Python utf-8-sig codec은 새 stream 시작마다 BOM prefix).
    """
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    if exists:
        # 파일 이미 있으면 append (BOM 없는 utf-8)
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for row in rows:
                writer.writerow(row)
    else:
        # 첫 write → BOM 포함 utf-8-sig + header
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


def append_failure(result: CollectionResult, failures_csv: Path) -> None:
    if result.success:
        return
    row = result.log_row()
    row["notes"] = " | ".join(result.notes)[:1000]
    append_csv(failures_csv, LOG_FIELDS + ["notes"], [row])


def archive_existing(path: Path) -> None:
    """새 실행 시 기존 로그/보고서 파일을 .archive_<utc_ts>로 자동 backup."""
    if path.exists():
        archive = path.with_suffix(path.suffix + f".archive_{utc_stamp()}")
        path.rename(archive)


def write_dry_run_report(
    results: list[CollectionResult],
    elapsed_s: float,
    assignment_csv: Path,
    log_csv: Path,
    failures_csv: Path,
    dry_run_md: Path,
) -> None:
    archive_existing(dry_run_md)
    chrome_profile = _PATHS["work_root"] / f"chrome_profile_{_AGENT_NAME}"
    manual_dropbox = _PATHS["work_root"] / "manual_pdf_dropbox"
    lines = [
        f"# {_AGENT_NAME} batch dry-run",
        "",
        f"- generated_at: {utc_now()}",
        f"- elapsed_seconds: {elapsed_s:.1f}",
        f"- agent: `{_AGENT_NAME}`",
        f"- assignment_csv: `{assignment_csv}`",
        f"- download_log: `{log_csv}`",
        f"- failures_log: `{failures_csv}`",
        f"- chrome_profile: `{chrome_profile}`",
        f"- manual_dropbox: `{manual_dropbox}`",
        "",
        "## Results",
        "",
        "| paper_id | publisher | method | success | content_status | chars | pages | pdf_images | html_figures | figure_status | error |",
        "|---|---|---|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for r in results:
        error = (r.error_message or " | ".join(r.notes))[:180].replace("|", "/")
        lines.append(
            f"| `{r.paper.paper_id}` | {r.paper.publisher} | {r.attempt_method or '-'} | {r.success} | "
            f"{r.content_status} | {r.content_length_chars} | {r.n_pdf_pages} | {r.n_pdf_extracted_images} | "
            f"{r.n_html_figures} | {r.figure_status} | {error} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `content_status=full` : >=3000 chars + metadata match + no access wall.",
            "- `short_fulltext_possible` : 1500-3000 chars + article structure (옛 short letter 보호).",
            "- `figure_status=none_found` : HTML/PDF에 figure 자체가 없음 (정상).",
            "- `figure_status=extraction_failed` : figure는 있으나 다운로드 실패.",
            f"- 실패 row는 `failures_{_AGENT_NAME}.csv`에 자동 등록.",
            "- 미확립 publisher (world_scientific 등)는 자동 method 실패 시 `manual_pdf_dropbox/{paper_id}/request.json` 으로 큐 등록.",
            "",
            "## Paper Folders",
            "",
        ]
    )
    for r in results:
        lines.append(f"- `{r.paper.paper_id}`: `{paper_dir(r.paper)}`")
    dry_run_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fulltext/PDF batch recovery runner.")
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true",
                       help="Dry-run sample (Elsevier/RSC/Springer/WorldSci/CSJ 각 첫 row).")
    group.add_argument("--all", action="store_true", help="assignment 전체 실행.")
    group.add_argument("--paper-id", action="append", default=[],
                       help="특정 paper_id 지정 (반복 가능).")
    parser.add_argument("--limit", type=int, default=0, help="선택 paper 수 제한.")
    parser.add_argument("--sleep", type=float, default=0.75, help="paper 간 대기 초.")
    parser.add_argument("--keep-logs", action="store_true",
                        help="기존 download_log/failures CSV archive 건너뜀 (기본: archive).")
    return parser


def needs_browser(papers: list[Paper]) -> bool:
    return any(p.publisher in {"acs", "elsevier", "wiley"} for p in papers)


def main() -> None:
    args = build_parser().parse_args()
    paths = get_paths(args)
    configure(paths, args.agent, args.chrome_exe)

    env_path = Path(args.env_path) if args.env_path else (_PATHS["kb_root"] / ".env")
    load_dotenv(env_path)

    work_root = _PATHS["work_root"]
    assignment_csv = work_root / f"assignment_{_AGENT_NAME}.csv"
    log_csv = work_root / f"download_log_{_AGENT_NAME}.csv"
    failures_csv = work_root / f"failures_{_AGENT_NAME}.csv"
    dry_run_md = work_root / f"dry_run_{_AGENT_NAME}.md"

    papers = read_assignment(assignment_csv)
    if args.dry_run:
        selected = select_dry_run(papers)
    elif args.all:
        selected = papers
    elif args.paper_id:
        wanted = set(args.paper_id)
        selected = [p for p in papers if p.paper_id in wanted]
        missing = wanted - {p.paper_id for p in selected}
        if missing:
            raise RuntimeError(f"requested paper_id not assigned to {_AGENT_NAME}: {sorted(missing)}")
    else:
        raise SystemExit("Select --dry-run, --all, or --paper-id.")

    if args.limit:
        selected = selected[: args.limit]
    if not selected:
        raise SystemExit("No papers selected.")

    # 새 실행 시 기존 로그 파일 archive
    if not args.keep_logs:
        archive_existing(log_csv)
        archive_existing(failures_csv)

    start = time.time()
    results: list[CollectionResult] = []
    print(f"[{_AGENT_NAME}] selected {len(selected)} papers (assignment={assignment_csv.name})")

    def _process(paper: Paper, browser: BrowserCollector | None) -> None:
        print(f"[{_AGENT_NAME}] collecting {paper.paper_id} {paper.publisher} {paper.doi}")
        result = collect_paper(paper, browser)
        results.append(result)
        # 점진적 append: 매 paper 직후 LOG_CSV / FAILURES_CSV에 즉시 flush
        try:
            append_csv(log_csv, LOG_FIELDS, [result.log_row()])
            append_failure(result, failures_csv)
        except Exception as exc:
            print(f"[{_AGENT_NAME}] WARN: incremental append failed: {type(exc).__name__}: {exc}")
        print(
            f"[{_AGENT_NAME}] -> success={result.success} status={result.content_status} "
            f"chars={result.content_length_chars} method={result.attempt_method or '-'}"
        )
        # publisher별 interval (차단 경험 기반). API method (Elsevier Tier0 등)는 rate-limit 약해 3s로 단축.
        interval = publisher_interval(paper.publisher, args.sleep)
        if "api" in (result.attempt_method or "").lower():
            interval = min(interval, 3.0)
        time.sleep(interval)

    if needs_browser(selected):
        with BrowserCollector() as browser:
            for paper in selected:
                _process(paper, browser)
    else:
        for paper in selected:
            _process(paper, None)

    if args.dry_run:
        write_dry_run_report(results, time.time() - start, assignment_csv, log_csv, failures_csv, dry_run_md)
        print(f"[{_AGENT_NAME}] dry-run report: {dry_run_md}")

    n_success = sum(1 for r in results if r.success)
    print(f"[{_AGENT_NAME}] done: {n_success}/{len(results)} success in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
