"""runner.py — sci_collect.py 가 불러 쓰는 판정·정리 함수 모음. 직접 실행하는 스크립트가 아니다.

  classify_content      본문 텍스트 판정 (길이, DOI·제목 일치, 접근 제한 문구)
  strip_html_text       HTML 에서 본문 줄만 남기기 (출판사 화면 부품 줄 제거)
  source_frontmatter    source.md 머리말
  html_pdf_candidates   논문 페이지의 PDF 주소 후보
  mdpi_pdf_candidates   MDPI PDF 주소 규칙

네트워크 요청과 브라우저는 쓰지 않는다. 요청은 sci_collect.py 가 보내고, truststore 로 OS 인증서 저장소
(기관 망의 재서명 인증서 포함)를 써서 인증서를 확인한다.

2026-09-27: 옛 배치 실행부(CLI, 인증서 확인을 끈 request_get(verify=False), 출판사별 collect_*, Playwright 창)를 뺐다.
그 판은 git 기록과 scripts/_history/runner_260927_1109.py (로컬 보관) 에 있다.
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin

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

_AGENT_NAME: str = "claude"   # source.md 머리말의 collected_by. sci_collect 가 configure("sci_collect") 로 정한다


def configure(agent_name: str) -> None:
    """source.md 머리말의 collected_by 에 적을 이름을 정한다."""
    global _AGENT_NAME
    _AGENT_NAME = agent_name


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
