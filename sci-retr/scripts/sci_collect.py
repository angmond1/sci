#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci_collect.py — 논문 원문 수집 CLI (LLM 없음). 2026-09-23 확립 절차 통합판.

    python sci_collect.py resolve --kb-root <dir> --input <dois.csv|xlsx|txt|DOI ...>
    python sci_collect.py collect --kb-root <dir> [--ids ID ...] [--publishers p1,p2] [--force]
    python sci_collect.py assist  --kb-root <dir> [--ids ID ...]          # 보이는 Chrome, 사용자 확인 협력
    python sci_collect.py status  --kb-root <dir>

절차 요약
  resolve : DOI → Crossref(제목·저널·약어·권호쪽·저자·PII·초록) + OpenAlex(교신저자·OA·초록) → paper_id(연도_저널약어_교신저자, 최초 부여 후 동결)
            → collection_registry.csv 등록 (초록 포함 → Claude 의 사전 분류 재료)
  collect : publisher 별 스레드(간격 준수). 자동 경로로 PDF(필수) + 텍스트(XML > HTML > PDF) + SI(같은 폴더, _SI 파일명).
            확인 페이지(Cloudflare Turnstile / Radware) 감지 시 재시도 없이 human_queue 로. 미구독 publisher 는 초록만 저장 + 안내.
  assist  : human_queue 를 보이는 Chrome(수집 프로필) 에서 처리. 확인 창이 뜨면 사용자가 1클릭 (세션 쿠키로 이후 자동), 이후 텍스트·PDF·SI 자동.
  텍스트 : HTML 은 본문 컨테이너만 DOM 추출 후 furniture 줄 제거, PDF 텍스트와 길이 대조(0.6~1.6 밖이면 PDF 텍스트 채택).
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sys
import threading
import time
import unicodedata
import html as htmlmod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import truststore

truststore.inject_into_ssl()  # KIST 망 TLS 재서명 → OS 인증서 저장소 사용 (verify=False 불필요)

import requests  # noqa: E402
try:
    import pymupdf as fitz  # noqa: E402  (pymupdf 1.24+. 옛 이름 fitz 로 들여오면 실행마다 경고가 찍힌다)
except ImportError:
    import fitz  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import runner  # noqa: E402  검증된 판정·정리 함수 재사용
from runner import Paper, classify_content, strip_html_text, source_frontmatter, html_pdf_candidates, mdpi_pdf_candidates  # noqa: E402
from validate import validate_collected_paper  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------------ 상수
UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
UA_API = "sci_collect/1.0 (KIST; mailto:{mailto})"
CHROME_EXE = Path(os.environ.get("CHROME_EXE", r"C:\Program Files\Google\Chrome\Application\chrome.exe"))

PREFIX_PUBLISHER = {
    "10.1016": "elsevier", "10.1006": "elsevier", "10.1039": "rsc", "10.1002": "wiley", "10.1021": "acs",
    "10.1007": "springer", "10.1023": "springer", "10.3390": "mdpi", "10.1038": "nature", "10.1126": "science",
    "10.1149": "ecs", "10.1055": "thieme", "10.1142": "world_scientific", "10.1246": "csj", "10.2174": "bentham",
    "10.1098": "royal_society", "10.1248": "jstage", "10.1134": "pleiades", "10.20964": "tsinghua_oae", "10.26599": "tsinghua_oae",
    # 2026-09-26 섞인 목록 실측으로 이름을 붙인 사이트. 처리는 모두 일반(generic) 경로(논문 페이지 → PDF 후보 → SI)이고,
    # 이름은 보고·간격·차단 판정 단위가 된다. 자동 요청을 막는 곳은 DEFAULT_CONFIG["web_only_publishers"] 에도 넣는다.
    "10.3389": "frontiers", "10.1371": "plos", "10.3762": "beilstein", "10.5194": "copernicus", "10.1103": "aps", "10.1017": "cambridge",
    "10.1080": "tandf", "10.1073": "pnas", "10.1063": "aip", "10.1093": "oup", "10.1109": "ieee",
    # 프리프린트 서버. Crossref 의 publisher 이름(ChemRxiv 는 ACS)으로 웹 전용 출판사에 묶이지 않게 접두어로 고정한다.
    "10.26434": "chemrxiv", "10.48550": "generic", "10.1101": "generic", "10.21203": "generic",
}
# container-title 이 없는 프리프린트의 저널약어
PREPRINT_ABBREV = {"10.26434": "ChemRxiv", "10.48550": "arXiv", "10.1101": "bioRxiv", "10.21203": "ResSq", "10.2139": "SSRN", "10.31219": "OSF"}
DEFAULT_CONFIG = {
    "abstract_only_publishers": ["thieme", "world_scientific", "csj", "bentham", "royal_society"],
    # 자동 요청을 막는 것이 확인된 출판사 (2026-09-24 실측) → 자동 단계에서 요청하지 않고 바로 웹 경로. 사정이 바뀌면 여기서 뺀다.
    # 2026-09-26 추가: tandf(Taylor & Francis)·pnas·aip·oup(Oxford)·ieee·chemrxiv 는 첫 요청부터 403/202 로 막힘 (섞인 목록 실측).
    "web_only_publishers": ["acs", "rsc", "science", "ecs", "tandf", "pnas", "aip", "oup", "ieee", "chemrxiv"],
    # 받지 않는 SI 형식 (2026-09-25 사용자 지시: 동영상, 결정 구조 정보, 결정 구조·대형 스프레드시트 데이터가 담기는 zip·Excel 은 받지 않는다).
    # 링크 확장자로 거르고, 받은 뒤 content-type 과 파일 내용(zip 안이 Word 인지 Excel 인지)으로도 거른다.
    "si_skip_exts": ["mp4", "avi", "mov", "wmv", "mpg", "mpeg", "m4v", "webm", "mkv", "flv", "mp3", "wav",
                     "cif", "fcf", "hkl", "mol", "mol2", "sdf", "pdb", "xyz", "cdx",
                     "zip", "rar", "7z", "tar", "gz", "tgz",
                     "xls", "xlsx", "xlsm", "xlsb", "csv", "ods"],
    "abstract_only_reason": "KIST 미구독 — 원문 미수집, 초록만 보관",
    # elsevier 30s (2026-09-24 사용자 실험값): 기록된 차단은 13s 간격 + PDF 후보 다수 probe (2026-05, 29편/6분20초). 90s 는 7배 안전계수였고 60s 차단 기록 없음.
    # 논문당 요청은 본문 1회 + PDF 1회로 제한하고, throttle 문구 감지 시 그 사이트 묶음을 즉시 중단(30분 후 재실행)한다.
    "intervals": {"elsevier": 30, "elsevier_api": 3, "rsc": 15, "wiley": 5, "acs": 45, "science": 30, "nature": 15,
                  "springer": 2, "mdpi": 2, "ecs": 90, "thieme": 2, "generic": 5},
    "assist_wait_seconds": 300,
    "crossref_mailto": "",
}
CHALLENGE_TITLE = ("잠시만", "just a moment", "captcha", "radware", "attention required", "access denied")
WILEY_TDM_URL = "https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining"
_wiley_notice_shown = False
HUMAN_PUBLISHER_NOTE = {
    "elsevier": "ScienceDirect 구독 논문은 도구 창에서 확인이 반복되어 받을 수 없습니다. 평소 쓰시는 Chrome 에서 직접 받아 아래 경로에 저장해 주세요.",
    "rsc": "RSC 는 첫 방문에 확인 창이 뜰 수 있습니다. 한 번 눌러 주시면 이후 자동입니다.",
    "ecs": "IOPScience 는 Radware 확인 창이 뜹니다. 한 번 눌러 주시면 이어서 받습니다.",
    "wiley": "Wiley 는 도구 창에서 확인이 반복되어 받을 수 없습니다. 평소 쓰시는 Chrome 에서 직접 받아 아래 경로에 저장해 주세요.",
}
WEB_NOTE = {   # 웹 경로(평소 쓰는 Chrome) 목록 안내 — 2026-09-25 최종 규칙
    "elsevier": "Elsevier 구독 논문은 평소 쓰시는 Chrome 에서 받아야 합니다 (OA 는 API 로 자동).",
    "wiley": "Wiley 는 TDM 토큰이 없거나 API 가 실패한 논문을 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "acs": "ACS 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다 (확인 창은 직접 눌러 주세요).",
    "rsc": "RSC 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "science": "Science 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "ecs": "ECS/IOP 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "tandf": "Taylor & Francis 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "pnas": "PNAS 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "aip": "AIP 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "oup": "Oxford 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "ieee": "IEEE 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
    "chemrxiv": "ChemRxiv 는 자동 요청을 막아 평소 쓰시는 Chrome 에서 받아야 합니다.",
}
SI_LINK_RE = re.compile(
    r'href=["\']([^"\']*(?:/suppl_file/|/suppl/|supplementary|supporting[-_ ]?information|mmc\d+|MOESM\d+_ESM|/suppdata/|downloadSupplement|/esm/|/article-supplement/|ESM\.pdf)[^"\']*)["\']',
    re.I,
)

_log_lock = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def say(msg: str) -> None:
    with _log_lock:
        print(msg, flush=True)


# ------------------------------------------------------------------ 컨텍스트
@dataclass
class Ctx:
    kb_root: Path
    work: Path
    config: dict
    env: dict
    registry: dict = field(default_factory=dict)   # doi → row
    session: requests.Session = field(default_factory=requests.Session)

    def papers_root(self) -> Path:
        return self.kb_root / "papers"

    def interval(self, key: str) -> float:
        return float(self.config.get("intervals", {}).get(key, DEFAULT_CONFIG["intervals"].get(key, 5)))

    def api_headers(self) -> dict:
        return {"User-Agent": UA_API.format(mailto=self.config.get("crossref_mailto") or "unknown")}


def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for k in ("ELSEVIER_API_KEY", "WILEY_TDM_TOKEN", "TDM_API_TOKEN"):
        if k in os.environ and k not in env:
            env[k] = os.environ[k]
    if "TDM_API_TOKEN" not in env and "WILEY_TDM_TOKEN" in env:
        env["TDM_API_TOKEN"] = env["WILEY_TDM_TOKEN"]
    return env


def load_config(kb_root: Path) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    for p in (kb_root / "sci_collect.config.json", Path.home() / ".claude" / "sci" / "sci_collect.config.json"):
        if p.exists():
            try:
                user = json.loads(p.read_text(encoding="utf-8"))
                for k, v in user.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
                break
            except Exception as exc:
                say(f"config 읽기 실패 {p}: {exc}")
    return cfg


def make_ctx(args) -> Ctx:
    kb_root = Path(args.kb_root).resolve()
    kb_root.mkdir(parents=True, exist_ok=True)
    work = kb_root / "_collect"
    work.mkdir(parents=True, exist_ok=True)
    env = load_env(Path(args.env) if getattr(args, "env", None) else kb_root / ".env")
    cfg = load_config(kb_root)
    if getattr(args, "mailto", None):
        cfg["crossref_mailto"] = args.mailto
    ctx = Ctx(kb_root=kb_root, work=work, config=cfg, env=env)
    ctx.session.headers.update({"User-Agent": UA_BROWSER, "Accept-Language": "en-US,en;q=0.9"})
    # 간헐 SSL/연결 오류(KIST 망 TLS 재서명 장비) 재시도: 연결 3회, 읽기 2회, 백오프 2s·4s
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    adapter = HTTPAdapter(max_retries=Retry(total=3, connect=3, read=2, backoff_factor=2, status_forcelist=(502, 503, 504), allowed_methods=("GET", "HEAD")))
    ctx.session.mount("https://", adapter)
    ctx.session.mount("http://", adapter)
    runner.configure({"kb_root": kb_root, "papers_root": kb_root / "papers", "work_root": work}, "sci_collect", CHROME_EXE)
    for k, v in env.items():
        os.environ.setdefault(k, v)
    load_registry(ctx)
    return ctx


# ------------------------------------------------------------------ 레지스트리 (DOI → paper_id, 메타)
REG_FIELDS = ["paper_id", "doi", "title", "year", "journal", "journal_abbrev", "volume", "issue", "pages", "corresponding",
              "authors", "abstract", "publisher", "is_oa", "oa_pdf_url", "pii", "landing_url", "status", "method", "note", "resolved_at", "updated_at"]


def registry_path(ctx: Ctx) -> Path:
    return ctx.kb_root / "collection_registry.csv"


def load_registry(ctx: Ctx) -> None:
    ctx.registry = {}
    p = registry_path(ctx)
    if p.exists():
        with open(p, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ctx.registry[row["doi"].lower()] = row


def save_registry(ctx: Ctx) -> None:
    with _log_lock:
        p = registry_path(ctx)
        tmp = p.with_suffix(".csv.tmp")
        with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=REG_FIELDS, extrasaction="ignore")
            w.writeheader()
            for row in ctx.registry.values():
                w.writerow({k: row.get(k, "") for k in REG_FIELDS})
        tmp.replace(p)


def log_row(ctx: Ctx, row: dict) -> None:
    p = ctx.work / "collect_log.csv"
    fields = ["at", "paper_id", "doi", "publisher", "phase", "status", "method", "text_source", "chars", "pdf_bytes", "si_files", "note"]
    with _log_lock:
        new = not p.exists()
        with open(p, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in fields})


# ------------------------------------------------------------------ 입력 파싱
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>,;]+", re.I)


def read_dois(inputs: list[str]) -> list[str]:
    dois: list[str] = []
    for item in inputs:
        p = Path(item)
        if p.exists():
            if p.suffix.lower() in (".xlsx", ".xls"):
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
                    for ws in wb.worksheets:
                        for row in ws.iter_rows(values_only=True):
                            for cell in row:
                                if isinstance(cell, str):
                                    dois += DOI_RE.findall(cell)
                except ImportError:
                    raise SystemExit("xlsx 입력에는 openpyxl 필요: pip install openpyxl")
            else:
                text = p.read_text(encoding="utf-8-sig", errors="ignore")
                dois += DOI_RE.findall(text)
        else:
            dois += DOI_RE.findall(item)
    out, seen = [], set()
    for d in dois:
        d = d.rstrip(".)]}").strip()
        if d.lower() not in seen:
            seen.add(d.lower()); out.append(d)
    return out


def publisher_of(doi: str, crossref_publisher: str = "") -> str:
    prefix = doi.split("/", 1)[0].lower()
    if prefix in PREFIX_PUBLISHER:
        return PREFIX_PUBLISHER[prefix]
    cp = (crossref_publisher or "").lower()
    for key, name in (("elsevier", "elsevier"), ("royal society of chemistry", "rsc"), ("wiley", "wiley"), ("american chemical society", "acs"),
                      ("springer", "springer"), ("mdpi", "mdpi"), ("iop", "ecs"), ("association for the advancement of science", "science"), ("thieme", "thieme")):
        if key in cp:
            return name
    return "generic"


# ------------------------------------------------------------------ 메타 (Crossref + OpenAlex)
def crossref_work(ctx: Ctx, doi: str) -> dict:
    r = ctx.session.get(f"https://api.crossref.org/works/{quote(doi, safe='')}", headers=ctx.api_headers(), timeout=40)
    r.raise_for_status()
    return r.json()["message"]


def openalex_work(ctx: Ctx, doi: str) -> dict | None:
    try:
        r = ctx.session.get(f"https://api.openalex.org/works/https://doi.org/{doi}", headers=ctx.api_headers(),
                            params={"mailto": ctx.config.get("crossref_mailto") or None}, timeout=40)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def inverted_to_text(idx: dict | None) -> str:
    if not idx:
        return ""
    pos = {}
    for w, ps in idx.items():
        for p in ps:
            pos[p] = w
    return " ".join(pos[i] for i in sorted(pos))


def strip_jats(s: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def ascii_fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


ABBREV_WORDS = {
    "journal": "J", "chemistry": "Chem", "chemical": "Chem", "chemie": "Chem", "engineering": "Eng", "applied": "Appl", "catalysis": "Catal",
    "catalysts": "Catal", "science": "Sci", "sciences": "Sci", "materials": "Mater", "material": "Mater", "physics": "Phys", "physical": "Phys",
    "electrochemistry": "Electrochem", "electrochemical": "Electrochem", "international": "Int", "edition": "Ed", "letters": "Lett",
    "communications": "Commun", "communication": "Commun", "advanced": "Adv", "advances": "Adv", "environment": "Environ", "environmental": "Environ",
    "energy": "Energy", "surface": "Surf", "organic": "Org", "inorganic": "Inorg", "molecular": "Mol", "technology": "Technol", "research": "Res",
    "society": "Soc", "review": "Rev", "reviews": "Rev", "european": "Eur", "american": "Am", "angewandte": "Angew", "sustainable": "Sustain",
    "industrial": "Ind", "heterocyclic": "Heterocycl", "compounds": "Compd", "polymer": "Polym", "polymers": "Polym", "organometallic": "Organomet",
    "electrochemical society": "Electrochem Soc", "solid": "Solid", "state": "State", "nanoscale": "Nanoscale", "horizons": "Horiz", "green": "Green",
    "synthesis": "Synthesis", "nature": "Nat", "chinese": "Chin", "structure": "Struct", "analytical": "Anal", "biological": "Biol", "biology": "Biol",
    "medicine": "Med", "medicinal": "Med", "pharmaceutical": "Pharm", "electronic": "Electron", "electronics": "Electron", "processing": "Process",
    "transactions": "Trans", "proceedings": "Proc", "national": "Natl", "academy": "Acad", "general": "Gen", "microporous": "Microporous",
    "mesoporous": "Mesoporous", "porous": "Porous", "photochemistry": "Photochem", "photobiology": "Photobiol", "computational": "Comput",
    "theoretical": "Theor", "interface": "Interface", "interfaces": "Interfaces", "functional": "Funct", "sustainability": "Sustain",
}
ABBREV_STOP = {"of", "and", "the", "for", "in", "on", "a", "an", "to", "de", "la", "der", "und", "part", "section", "&"}


def journal_abbrev(m: dict) -> str:
    """Crossref short-container-title 우선; 없으면 단어별 축약(ISO4 근사) → 하이픈 연결."""
    # 정식명(container-title)에 단어 축약표를 적용해 결정적으로 생성. (short-container-title 은 Elsevier 처럼
    # 정식명을 그대로 넣거나 publisher 마다 형식이 달라 id 재료로 쓰지 않는다.)
    full = (m.get("container-title") or [""])[0] or (m.get("short-container-title") or [""])[0]
    if not full:
        prefix = (m.get("DOI") or "").split("/", 1)[0].lower()
        if prefix in PREPRINT_ABBREV:
            return PREPRINT_ABBREV[prefix]
        if m.get("type") == "posted-content":
            return "Preprint"
    base = ascii_fold(htmlmod.unescape(full).replace(".", "").replace("&", " "))
    words = [w for w in re.sub(r"[^A-Za-z0-9 ]+", " ", base).split() if w.lower() not in ABBREV_STOP]
    out = []
    for w in words:
        lw = w.lower()
        if len(words) == 1:
            out.append(w)                      # 'Science', 'Nature', 'Molecules', 'Synthesis' 는 그대로
        elif lw in ABBREV_WORDS:
            out.append(ABBREV_WORDS[lw])
        elif len(w) <= 6 or w.isupper():
            out.append(w)
        else:
            out.append(w[:5])
    return "-".join(out)[:30] or "Journal"


def corresponding_surname(cr: dict, oa: dict | None) -> tuple[str, str]:
    """(surname, source) — OpenAlex is_corresponding 우선, 없으면 Crossref 마지막 저자."""
    if oa:
        corr = [a for a in (oa.get("authorships") or []) if a.get("is_corresponding")]
        if corr:
            name = (corr[-1].get("author") or {}).get("display_name") or ""
            if name:
                return name.split()[-1], "openalex_corresponding"
    authors = cr.get("author") or []
    if authors:
        last = authors[-1]
        fam = last.get("family") or (last.get("name") or "").split()[-1:] or [""]
        fam = fam if isinstance(fam, str) else (fam[0] if fam else "")
        if fam:
            return fam, "crossref_last_author"
    return "Unknown", "none"


def authors_string(cr: dict) -> str:
    names = []
    for a in cr.get("author") or []:
        fam, giv = a.get("family") or "", a.get("given") or ""
        names.append((f"{fam}, {giv}".strip(", ") if fam else (a.get("name") or "")).strip())
    names = [n for n in names if n]
    if len(names) <= 6:
        return "; ".join(names)
    return "; ".join(names[:3]) + "; …; " + "; ".join(names[-3:])


def make_paper_id(ctx: Ctx, year: str, abbrev: str, surname: str, doi: str) -> str:
    base = f"{year or '0000'}_{abbrev}_{re.sub(r'[^A-Za-z0-9]+', '', ascii_fold(surname)) or 'Unknown'}"
    taken = {row["paper_id"] for d, row in ctx.registry.items() if d != doi.lower()}
    existing_dirs = {p.name for p in ctx.papers_root().glob("*") if p.is_dir()} if ctx.papers_root().exists() else set()
    taken |= existing_dirs
    pid, n = base, 1
    while pid in taken:
        n += 1
        pid = f"{base}_{n}"
    return pid


def resolve_doi(ctx: Ctx, doi: str) -> dict:
    row = ctx.registry.get(doi.lower())
    if row and row.get("paper_id"):
        return row  # id 동결
    cr = crossref_work(ctx, doi)
    oa = openalex_work(ctx, doi)
    year = ""
    for key in ("issued", "published-print", "published-online", "created"):
        parts = (cr.get(key) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            year = str(parts[0][0]); break
    abbrev = journal_abbrev(cr)
    surname, _ = corresponding_surname(cr, oa)
    abs_cr = strip_jats(cr.get("abstract") or "")
    abs_oa = inverted_to_text((oa or {}).get("abstract_inverted_index"))
    abstract = abs_cr if len(abs_cr) >= len(abs_oa) else abs_oa   # RSC 등은 Crossref 초록이 짧은 소개 문구뿐일 때가 있어 긴 쪽을 쓴다 (2026-09-26)
    oa_info = (oa or {}).get("open_access") or {}
    best = (oa or {}).get("best_oa_location") or {}
    row = {
        "paper_id": make_paper_id(ctx, year, abbrev, surname, doi),
        "doi": doi, "title": strip_jats((cr.get("title") or [""])[0]), "year": year,
        "journal": (cr.get("container-title") or [""])[0], "journal_abbrev": abbrev,
        "volume": cr.get("volume") or "", "issue": cr.get("issue") or "", "pages": cr.get("page") or cr.get("article-number") or "",
        "corresponding": surname, "authors": authors_string(cr), "abstract": abstract,
        "publisher": publisher_of(doi, cr.get("publisher") or ""),
        "is_oa": "1" if oa_info.get("is_oa") else "0", "oa_pdf_url": best.get("pdf_url") or oa_info.get("oa_url") or "",
        "pii": (cr.get("alternative-id") or [""])[0] if row is None else "",
        "landing_url": ((cr.get("resource") or {}).get("primary") or {}).get("URL") or f"https://doi.org/{doi}",
        "status": "resolved", "method": "", "note": "", "resolved_at": utc_now(), "updated_at": utc_now(),
    }
    ctx.registry[doi.lower()] = row
    return row


def cmd_resolve(args) -> None:
    ctx = make_ctx(args)
    dois = read_dois(args.input)
    say(f"입력 DOI {len(dois)}건 (중복 제거)")
    n_new = 0
    for i, doi in enumerate(dois, 1):
        try:
            before = doi.lower() in ctx.registry
            row = resolve_doi(ctx, doi)
            n_new += 0 if before else 1
            say(f"  [{i:3d}] {row['paper_id']:40s} {row['publisher']:9s} oa={row['is_oa']} abs={'Y' if row['abstract'] else '-'} {row['title'][:50]}")
        except Exception as exc:
            say(f"  [{i:3d}] {doi} resolve 실패: {type(exc).__name__}: {str(exc)[:80]}")
        if not (doi.lower() in ctx.registry and ctx.registry[doi.lower()].get("resolved_at") and i % 1 == 0):
            pass
        time.sleep(1.0)
    save_registry(ctx)
    say(f"registry 저장: {registry_path(ctx)} (신규 {n_new}건)")


# ------------------------------------------------------------------ 저장 (폴더 표준)
def paper_dir(ctx: Ctx, pid: str) -> Path:
    d = ctx.papers_root() / pid
    for sub in ("pdf", "html", "xml", "figures"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def is_pdf(data: bytes) -> bool:
    return bool(data) and data[:5] == b"%PDF-"


CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def pdf_text(data: bytes) -> tuple[str, int]:
    """PDF → 텍스트 (페이지 마커 유지, 하이픈 복원, 반복 머리말/쪽번호 제거)."""
    doc = fitz.open(stream=data, filetype="pdf")
    # sort=True 는 좌표순 정렬이라 두 단 편집에서 왼쪽·오른쪽 단 줄을 한 줄로 섞는다 (2026-09-24 실측: Elsevier·RSC·ACS·Wiley 모두).
    # PDF 기본 순서(내용 스트림 순서)는 출판사 PDF 에서 단 순서대로 읽힌다 (같은 4편에서 섞인 줄 0).
    # 위첨자 등이 NUL·제어 문자로 나올 때가 있다(2026-09-26 Wiley PDF 2편에서 123·35개). 줄바꿈·탭만 남기고 지운다.
    pages = [CONTROL_RE.sub("", p.get_text("text") or "") for p in doc]
    n = doc.page_count
    doc.close()
    # 반복 줄(머리말/꼬리말): 페이지 절반 이상에 등장하는 짧은 줄 제거
    from collections import Counter
    cnt = Counter()
    for t in pages:
        for line in set(l.strip() for l in t.splitlines() if 0 < len(l.strip()) <= 80):
            cnt[line] += 1
    repeated = {l for l, c in cnt.items() if n >= 3 and c >= max(3, n // 2)}
    out = []
    for i, t in enumerate(pages, 1):
        lines = [l for l in t.splitlines() if l.strip() not in repeated and not re.fullmatch(r"\s*\d{1,4}\s*", l)]
        body = "\n".join(lines)
        body = re.sub(r"(\w)-\n(\w)", r"\1\2", body)          # 줄 끝 하이픈 복원
        body = re.sub(r"[ \t]+\n", "\n", body)
        out.append(f"## Page {i}\n\n{body.strip()}\n")
    text = unicodedata.normalize("NFKC", "\n".join(out))    # 합자(ﬁ ﬂ) → 일반 글자
    return text.strip(), n


CONTAINER_SELECTORS = {
    "elsevier": ["#body", "#aep-article-fulltext", "div.Body", "article"],          # 2026-09 새 페이지: #aep-article-fulltext 없음
    "rsc": [".article-body", ".widget-ArticleFulltext", "#pnlArticleContent", ".article__body", "article", "main"],   # 2026-06-30 Silverchair
    "springer": [".c-article-body", "article", "main"],
    "nature": [".c-article-body", "article", "main"],
    "mdpi": [".html-body", "article", "main"],
    "science": ["#bodymatter", ".article__body", "article", "main"],   # 2026-09 확인: 본문은 #bodymatter, article 에는 머리말·참고문헌 섞임
    "ecs": [".article-content", "[itemprop=\"articleBody\"]", "main"],   # IOPscience (2026-09 확인)
    "wiley": [".article__body", "section.article-section__content", "article", "main"],
    "acs": [".article-body", ".widget-ArticleFulltext", ".article_content", "article", "main"],   # 2026 Silverchair 이전 후
    "generic": ["article", "main", "[role=main]", "#content"],
}
FURNITURE_CLASS_RE = re.compile(r"(cited|citation|related|recommend|share|metrics|cookie|banner|toolbar|sidebar|breadcrumb|footer|nav|menu|advert|newsletter|social)", re.I)


def html_container_text(raw_html: str, publisher: str) -> tuple[str, str]:
    """본문 컨테이너만 DOM 추출 → furniture 요소 제거 → runner.strip_html_text (줄 단위 furniture 제거 포함)."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return strip_html_text(raw_html), "regex_whole_page"
    soup = BeautifulSoup(raw_html, "lxml") if raw_html else None
    if soup is None:
        return "", "empty"
    for tag in soup(["script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form", "iframe"]):
        tag.decompose()
    node, used = None, "none"
    for sel in CONTAINER_SELECTORS.get(publisher, []) + CONTAINER_SELECTORS["generic"]:
        try:
            found = soup.select_one(sel)
        except Exception:
            found = None
        if found and len(found.get_text(" ", strip=True)) > 1500:
            node, used = found, sel
            break
    if node is None:  # 밀도 fallback: 텍스트 가장 긴 div/section
        best, best_len = None, 0
        for cand in soup.find_all(["div", "section"]):
            L = len(cand.get_text(" ", strip=True))
            if L > best_len and L < len(soup.get_text(" ", strip=True)) * 0.98:
                best, best_len = cand, L
        node, used = (best or soup.body or soup), "density"
    for el in list(node.find_all(True)):
        if getattr(el, "decomposed", False) or getattr(el, "attrs", None) is None:
            continue  # 상위 요소가 먼저 제거된 자식
        ident = " ".join([el.get("id") or "", " ".join(el.get("class") or [])])
        if FURNITURE_CLASS_RE.search(ident) and len(el.get_text(" ", strip=True)) < 4000:
            el.decompose()
    text = strip_html_text(str(node))
    return text, used


def elsevier_xml_text(xml_bytes: bytes) -> str:
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_bytes)
    except Exception:
        return ""
    parts = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("section-title",):
            t = "".join(el.itertext()).strip()
            if t:
                parts.append(f"\n## {t}\n")
        elif tag in ("para", "simple-para"):
            t = " ".join("".join(el.itertext()).split())
            if t:
                parts.append(t)
    text = "\n".join(parts).strip()
    return text if len(text) > 3000 else ""


def choose_text(html_text: str, pdf_txt: str, xml_text: str, paper: Paper) -> tuple[str, str, str]:
    """(text, source, note) — XML > HTML(검증·PDF 대조 통과) > PDF."""
    if xml_text:
        return xml_text, "xml", ""
    ok_html = bool(html_text) and classify_content(html_text, paper)[0]
    if ok_html and pdf_txt:
        ratio = len(html_text) / max(1, len(pdf_txt))
        if 0.6 <= ratio <= 1.6:
            return html_text, "html", f"html/pdf ratio={ratio:.2f}"
        return pdf_txt, "pdf", f"html/pdf ratio={ratio:.2f} out of range -> pdf text"
    if ok_html:
        return html_text, "html", "no pdf text to cross-check"
    if pdf_txt:
        return pdf_txt, "pdf", "html unusable" if html_text else ""
    return html_text, "html_unverified", "no pdf"


@dataclass
class Outcome:
    status: str = "failed"           # full | abstract_only | human_required | pdf_missing | failed  (registry 에는 resolved / out_of_scope 도 있음)
    method: str = ""
    text_source: str = ""
    chars: int = 0
    pdf_bytes: int = 0
    si_files: int = 0
    note: str = ""
    html_raw: str = ""
    xml_raw: bytes = b""
    pdf_data: bytes = b""
    page_url: str = ""
    requested: bool = True           # 출판사에 요청을 보냈는가 (False 면 다음 논문 전 대기 불필요)


def write_paper(ctx: Ctx, row: dict, out: Outcome) -> Outcome:
    """PDF 필수 저장 + 텍스트 선택 + source.md/json 작성 + 검증."""
    pid = row["paper_id"]
    d = paper_dir(ctx, pid)
    paper = Paper(paper_id=pid, doi=row["doi"], title=row["title"], year=row["year"], scope_label="", is_curated_pathway="",
                  publisher=row["publisher"], agent="sci_collect")
    pdf_txt, n_pages = ("", 0)
    if out.pdf_data and is_pdf(out.pdf_data):
        (d / "pdf" / f"{pid}.pdf").write_bytes(out.pdf_data)
        out.pdf_bytes = len(out.pdf_data)
        try:
            pdf_txt, n_pages = pdf_text(out.pdf_data)
        except Exception as exc:
            out.note += f" pdf_text_error={type(exc).__name__}"
    html_text, container = "", ""
    if out.html_raw:
        (d / "html" / f"{pid}.html").write_text(out.html_raw, encoding="utf-8", errors="ignore")
        html_text, container = html_container_text(out.html_raw, row["publisher"])
    xml_text = ""
    if out.xml_raw:
        (d / "xml" / f"{pid}.xml").write_bytes(out.xml_raw)
        xml_text = elsevier_xml_text(out.xml_raw)
    text, source, tnote = choose_text(html_text, pdf_txt, xml_text, paper)
    if not text:
        out.status, out.note = "failed", (out.note + " no text").strip()
        return out
    sj = {"paper_id": pid, "doi": row["doi"], "title": row["title"], "year": row["year"], "journal": row["journal"],
          "journal_abbrev": row["journal_abbrev"], "volume": row["volume"], "issue": row["issue"], "pages": row["pages"],
          "authors": row["authors"], "corresponding": row["corresponding"], "abstract": row["abstract"], "publisher": row["publisher"],
          "collection_method": out.method, "text_source": source, "text_note": tnote, "html_container": container,
          "pdf_pages": n_pages, "pdf_path": str(d / "pdf" / f"{pid}.pdf") if out.pdf_bytes else "", "source_url": out.page_url,
          "collected_at": utc_now(), "access_status": "fulltext"}
    fm = source_frontmatter(paper, {"title": row["title"], "journal": row["journal"], "authors": [a.strip() for a in row["authors"].split(";") if a.strip()],
                                    "abstract": row["abstract"], "year": row["year"]}, source, len(text), out.method)
    md = fm + f"- 수집 URL: {out.page_url}\n- 텍스트 소스: {source} ({tnote})\n- PDF: {'저장 (' + str(out.pdf_bytes // 1024) + ' KB)' if out.pdf_bytes else '없음'}\n\n## Full Text\n\n{text}\n"
    old = d / "source.md"
    if old.exists() and len(old.read_text(encoding='utf-8', errors='ignore')) > 2 * len(md):
        (d / f"source_pre_{datetime.now().strftime('%y%m%d_%H%M')}.md").write_text(old.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    old.write_text(md, encoding="utf-8")
    (d / "source.json").write_text(json.dumps(sj, ensure_ascii=False, indent=2), encoding="utf-8")
    v = validate_collected_paper(pid, d, row["doi"], row["publisher"])
    issues = [i for i in v["issues"] if not (i.startswith("elsevier_1page") and n_pages > 3)]
    out.chars, out.text_source = len(text), source
    if issues and not out.pdf_bytes:
        out.status, out.note = "failed", (out.note + " validate: " + "; ".join(issues)).strip()
    elif issues:
        out.status, out.note = "full", (out.note + " warn: " + "; ".join(issues)).strip()
    else:
        out.status = "full"
    if out.status == "full" and not out.pdf_bytes:
        out.status, out.note = "pdf_missing", (out.note + " PDF 미확보(텍스트만 저장) → 재시도 대상").strip()   # PDF 필수 정책
    with open(d / "source_origin.txt", "a", encoding="utf-8") as f:
        f.write(f"{utc_now()} sci_collect method={out.method} text={source} chars={len(text)} pdf={out.pdf_bytes} status={out.status} note={out.note[:200]}\n")
    return out


def write_abstract_only(ctx: Ctx, row: dict, reason: str) -> Outcome:
    pid = row["paper_id"]
    d = paper_dir(ctx, pid)
    title = row["title"] or pid
    md = (f"---\npaper_id: \"{pid}\"\ndoi: \"{row['doi']}\"\ntitle: \"{title.replace(chr(34), chr(39))}\"\nyear: \"{row['year']}\"\njournal: \"{row['journal']}\"\n"
          f"publisher: \"{row['publisher']}\"\ncontent_source: \"abstract_only\"\naccess_status: \"abstract_only\"\nabstract_only_reason: \"{reason}\"\ncollected_at: \"{utc_now()}\"\n---\n\n"
          f"# {title}\n\n> 원문 미수집: {reason}\n\n## Abstract\n\n{row['abstract'] or '(초록 없음)'}\n")
    (d / "source.md").write_text(md, encoding="utf-8")
    (d / "source.json").write_text(json.dumps({"paper_id": pid, "doi": row["doi"], "title": title, "year": row["year"], "journal": row["journal"],
                                               "publisher": row["publisher"], "access_status": "abstract_only", "abstract_only_reason": reason,
                                               "abstract": row["abstract"], "collected_at": utc_now()}, ensure_ascii=False, indent=2), encoding="utf-8")
    return Outcome(status="abstract_only", method="abstract_only", chars=len(row["abstract"] or ""), note=reason)


# ------------------------------------------------------------------ SI
def find_si_links(raw_html: str, base_url: str) -> list[str]:
    links = []
    for m in SI_LINK_RE.finditer(raw_html or ""):
        href = htmlmod.unescape(m.group(1))
        if href.startswith("#") or "javascript" in href:
            continue
        links.append(urljoin(base_url, href))
    pref = [l for l in dict.fromkeys(links) if re.search(r"\.pdf(\?|$)|/suppl_file/|mmc\d|MOESM|suppdata|downloadSupplement|/esm/|/article-supplement/", l, re.I)]
    return pref[:6]


def si_ext(url: str, default: str = "bin") -> str:
    """SI 파일 확장자: RSC 신플랫폼은 /article-supplement/{id}/{형식}/… 의 형식 칸, 그 외는 URL 끝 확장자."""
    m = re.search(r"/article-supplement/\d+/([A-Za-z0-9]+)/", url)
    if m:
        return m.group(1).lower()[:5]
    last = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    ext = last.rsplit(".", 1)[-1][:5] if "." in last else ""
    return re.sub(r"[^a-z0-9]", "", ext.lower()) or default


def si_skip_set(ctx: Ctx) -> set:
    return {str(e).lower().lstrip(".") for e in ctx.config.get("si_skip_exts", DEFAULT_CONFIG["si_skip_exts"])}


def si_skipped(url: str, skip: set) -> bool:
    """받지 않는 SI 형식인지. URL 경로·쿼리 안의 파일 확장자로 본다(Wiley 는 ?file=…, RSC 는 형식 칸)."""
    u = url.lower().split("#", 1)[0]
    if si_ext(u, "") in skip:
        return True
    return any(re.search(r"\." + re.escape(e) + r"(?:$|[?&;/])", u) for e in skip)


# 확장자 없이 온 SI 를 거를 content-type 조각 (동영상·음성, 결정 구조, 압축, 스프레드시트)
SI_SKIP_CT = ("video/", "audio/", "cif", "zip", "x-rar", "vnd.rar", "x-7z", "x-tar", "gzip",
              "ms-excel", "spreadsheetml", "opendocument.spreadsheet", "text/csv")


def zip_kind(data: bytes) -> str:
    """zip 형식 데이터의 실제 종류: docx·xlsx·pptx·zip. zip 이 아니면 빈 문자열. Word 는 받고 Excel·일반 zip 은 거르는 데 쓴다."""
    if data[:4] != b"PK\x03\x04":
        return ""
    import io, zipfile
    try:
        names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    except Exception:
        return "zip"
    for prefix, kind in (("word/", "docx"), ("xl/", "xlsx"), ("ppt/", "pptx")):
        if any(n.startswith(prefix) for n in names):
            return kind
    return "zip"


def si_name(pid: str, k: int, ext: str) -> str:
    return f"{pid}_SI.{ext}" if k == 1 else f"{pid}_SI_{k}.{ext}"


def save_si(ctx: Ctx, pid: str, fetch, links: list[str]) -> int:
    """SI 를 받은 형식 그대로 pdf/ 폴더에 {pid}_SI*.{ext} 로 저장. 거부·빈 응답·HTML 이 온 링크는 우회하지 않고 직접 다운로드 목록에 올린다."""
    d = paper_dir(ctx, pid) / "pdf"
    n, failed = 0, []
    skip = si_skip_set(ctx)
    for url in links:
        if si_skipped(url, skip):
            continue   # 받지 않는 SI 형식 (동영상, 결정 구조, 압축, 스프레드시트 등)
        try:
            data, ctype = fetch(url)
        except Exception:
            failed.append(url); continue
        if not data:
            failed.append(url); continue
        is_html = "html" in (ctype or "").lower() or data[:15].lower().startswith(b"<!doctype html") or data[:6].lower() == b"<html>"
        if is_html:
            failed.append(url); continue   # 확인·거부 페이지 또는 landing 이 온 것
        ct = (ctype or "").lower()
        pdf = is_pdf(data)
        ext = "pdf" if pdf else (zip_kind(data) or si_ext(url))
        if not pdf and ext not in ("doc", "docx") and (ext in skip or any(k in ct for k in SI_SKIP_CT)):
            continue   # 받지 않는 SI 형식 (확장자 없이 온 동영상·결정 구조·압축·스프레드시트)
        if len(data) < 5000 and not pdf:
            continue   # 너무 작은 비 PDF 응답은 SI 파일로 보지 않음
        n += 1
        (d / si_name(pid, n, ext)).write_bytes(data)
        time.sleep(2)
    if failed:
        add_manual_si(ctx, pid, failed, start=n + 1)
    return n


def http_fetch(ctx: Ctx):
    def _f(url: str) -> tuple[bytes, str]:
        r = ctx.session.get(url, timeout=120, allow_redirects=True)
        return (r.content if r.status_code == 200 else b""), r.headers.get("content-type", "")
    return _f


# ------------------------------------------------------------------ 브라우저 (Playwright, 스레드별 인스턴스)
class Browser:
    def __init__(self, ctx: Ctx, profile: str, headless: bool):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        prof = ctx.work / profile
        prof.mkdir(parents=True, exist_ok=True)
        pref = prof / "Default" / "Preferences"
        if pref.exists():
            try:
                d = json.loads(pref.read_text(encoding="utf-8"))
                d.setdefault("plugins", {})["always_open_pdf_externally"] = True   # PDF 링크 이동 시 뷰어 대신 다운로드

                d.setdefault("download", {})["prompt_for_download"] = False
                pref.write_text(json.dumps(d), encoding="utf-8")
            except Exception:
                pass
        # 정책(2026-09-24): 봇 탐지 우회 금지. 확인 쿠키 복사·UA 위장·지문 흉내를 하지 않는다.
        # 확인 페이지가 나오면 재시도하지 않고 사용자에게 넘긴다 (사용자가 직접 통과하거나 직접 다운로드).
        kw = dict(user_data_dir=str(prof), executable_path=str(CHROME_EXE), headless=headless, accept_downloads=True,
                  ignore_https_errors=True, args=["--no-first-run", "--window-size=1280,900"])
        self.ctx = self._pw.chromium.launch_persistent_context(**kw)
        self.page = self.ctx.new_page()
        self.headless = headless

    def close(self):
        try:
            self.ctx.close()
        except Exception:
            pass
        try:
            self._pw.stop()
        except Exception:
            pass

    def title(self) -> str:
        try:
            return self.page.title()
        except Exception:
            return "<closed>"

    def challenged(self) -> bool:
        t = self.title().lower()
        if any(k in t for k in CHALLENGE_TITLE):
            return True
        try:
            if "perfdrive" in self.page.url:
                return True
            return bool(self.page.evaluate("!!document.querySelector('[class*=\"cf-turnstile\"], [class*=\"cf-challenge\"], iframe[src*=\"challenges.cloudflare.com\"]')"))
        except Exception:
            return True

    def goto(self, url: str, tries: int = 3) -> None:
        last = None
        for i in range(tries):
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=120000)
                return
            except Exception as exc:
                last = exc
                if "Download is starting" in str(exc):
                    raise
                time.sleep(8)
        raise last

    def wait_ok(self, ok_selector: str, label: str, max_wait: int, prompt: str = "") -> bool:
        t0, warned = time.time(), False
        while time.time() - t0 < max_wait:
            try:
                ok = self.page.evaluate("(s) => !!document.querySelector(s)", ok_selector)
                ch = self.challenged()
            except Exception:
                time.sleep(3); continue
            if ok and not ch:
                try:
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                return True
            if ch and not warned:
                say(f"!! [{label}] 확인 창이 떴습니다. {prompt or '열린 Chrome 창에서 확인을 눌러 주세요.'} (최대 {max_wait}s 대기)")
                warned = True
            time.sleep(5)
        return False

    FETCH_JS = """async (u) => { const r = await fetch(u, {credentials:'include'}); const b = await r.arrayBuffer();
        let s = ''; const u8 = new Uint8Array(b); for (let i = 0; i < u8.length; i += 8192) { s += String.fromCharCode.apply(null, u8.subarray(i, i + 8192)); }
        return {status: r.status, ctype: r.headers.get('content-type') || '', b64: btoa(s)}; }"""

    def fetch_bytes(self, url: str) -> tuple[bytes, str, int]:
        r = self.page.evaluate(self.FETCH_JS, url)
        return base64.b64decode(r["b64"]), r["ctype"], int(r["status"])

    def request_bytes(self, url: str, referer: str = "") -> tuple[bytes, str, int]:
        resp = self.page.request.get(url, headers={"Referer": referer} if referer else {}, timeout=120000)
        return resp.body(), resp.headers.get("content-type", ""), resp.status

    def nav_download(self, url: str) -> bytes:
        with self.page.expect_download(timeout=90000) as dl:
            try:
                self.page.goto(url, wait_until="commit", timeout=90000)
            except Exception as exc:
                if "Download is starting" not in str(exc):
                    raise
        return open(dl.value.path(), "rb").read()

    def get_pdf(self, url: str, referer: str, order=("fetch", "request", "nav")) -> tuple[bytes, str]:
        notes = []
        for how in order:
            try:
                if how == "fetch":
                    data, ctype, st = self.fetch_bytes(url)
                elif how == "request":
                    data, ctype, st = self.request_bytes(url, referer)
                else:
                    data, ctype, st = self.nav_download(url), "application/pdf", 200
                if is_pdf(data):
                    return data, how
                m = re.search(rb"https://pdf\.sciencedirectassets\.com[^\"'<> ]+", data or b"")
                if m:
                    tgt = m.group(0).decode("utf-8", "ignore").replace("&amp;", "&")
                    d2, _, _ = self.request_bytes(tgt)
                    if is_pdf(d2):
                        return d2, how + "+redirect"
                notes.append(f"{how}:{st}")
            except Exception as exc:
                notes.append(f"{how}:{type(exc).__name__}")
                if how == "nav":
                    try:
                        self.goto(referer, tries=2)
                    except Exception:
                        pass
        return b"", " | ".join(notes)

    def content(self) -> str:
        try:
            return self.page.content()
        except Exception:
            return ""

    def browser_fetch(self):
        def _f(url: str):
            data, ctype, st = self.fetch_bytes(url)
            return (data if st == 200 else b""), ctype
        return _f


# ------------------------------------------------------------------ publisher 별 자동 경로
def h_elsevier(ctx: Ctx, row: dict) -> Outcome:
    """Elsevier: API 는 OA 논문에만 쓴다 (2026-09-25 사용자 규칙). OA 가 아닌 구독 논문은 요청 없이 웹 경로.
    OA 표시(OpenAlex)가 있으면 Article Retrieval API 로 XML+PDF → 첫 페이지만 오면(출판사판 비공개, 저자 원고만 공개 등)
    ScienceDirect 밖의 OA 사본(저장소 등) → 그래도 없으면 웹 경로.
    공식 한도 (dev.elsevier.com/api_key_settings.html, 2026-09-25 확인): 키당 초당 10회, 주 50,000회, 넘으면 HTTP 429.
    도구는 논문당 2회(XML, PDF, 사이 1초) + 논문 사이 intervals.elsevier_api(3초)."""
    if row.get("is_oa") != "1":
        return Outcome(status="human_required", requested=False,
                       note="Elsevier 구독 논문(OA 아님) → API 쓰지 않음, 웹 경로")
    key = ctx.env.get("ELSEVIER_API_KEY")
    api_note = "ELSEVIER_API_KEY 없음"
    tried = bool(key)
    if key:
        hdr = {"X-ELS-APIKey": key, "User-Agent": "sci_collect Elsevier API"}
        ep = f"https://api.elsevier.com/content/article/doi/{quote(row['doi'], safe='')}"
        xml = ctx.session.get(ep, headers={**hdr, "Accept": "text/xml"}, timeout=60)
        if xml.status_code == 429:
            return Outcome(status="failed", note="Elsevier API 한도 초과(429) → 잠시 뒤 collect 다시")
        time.sleep(1)
        pdf = ctx.session.get(ep, headers={**hdr, "Accept": "application/pdf"}, timeout=120)
        if pdf.status_code == 429:
            return Outcome(status="failed", note="Elsevier API 한도 초과(429) → 잠시 뒤 collect 다시")
        status = (pdf.headers.get("X-ELS-Status") or "").lower()
        limited = "first page" in status or "not entitled" in status
        if not limited and pdf.status_code == 200 and is_pdf(pdf.content):
            out = Outcome(method="elsevier_article_retrieval_api", pdf_data=pdf.content, page_url=ep,
                          xml_raw=xml.content if xml.status_code == 200 and xml.content.strip().startswith(b"<") else b"")
            return write_paper(ctx, row, out)
        api_note = "API 본문 권한 없음(첫 페이지만)" if limited else f"API pdf status={pdf.status_code}"
    # ScienceDirect 밖의 OA 사본 (저자 원고 저장소, PMC 등). 출판사 사이트는 자동 요청을 막으므로 요청하지 않는다.
    oa_url = row.get("oa_pdf_url") or ""
    host = urlparse(oa_url).netloc.lower() if oa_url else ""
    if oa_url and not any(h in host for h in ("sciencedirect.com", "elsevier.com", "doi.org")):   # doi.org 는 결국 ScienceDirect 로 이어짐
        tried = True
        try:
            r = ctx.session.get(oa_url, timeout=120)
            if r.status_code == 200 and is_pdf(r.content):
                return write_paper(ctx, row, Outcome(method="elsevier_oa_copy_pdf", pdf_data=r.content, page_url=oa_url))
        except Exception:
            pass
    return Outcome(status="human_required", requested=tried, note=f"{api_note} → 웹 경로")


def h_wiley(ctx: Ctx, row: dict) -> Outcome:
    """토큰 있으면 TDM API (간격 wiley=5s). 토큰이 없거나 API 가 실패하면 요청 없이 '직접 다운로드' 대상으로.
    2026-09-24 실측: 창 없는 일반 요청은 403, 도구가 띄운 Chrome 은 사용자가 확인을 3번 눌러도 확인 창이 반복되어 통과 불가."""
    token = ctx.env.get("TDM_API_TOKEN") or ctx.env.get("WILEY_TDM_TOKEN")
    if not token:
        wiley_notice()
        return Outcome(status="human_required", requested=False, note="Wiley TDM 토큰 없음 → 자동 수집 불가, 평소 쓰는 Chrome 에서 직접 다운로드")
    try:
        r = ctx.session.get(f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{quote(row['doi'], safe='')}",
                            headers={"Wiley-TDM-Client-Token": token, "Accept": "application/pdf"}, timeout=180, allow_redirects=True)
        if r.status_code == 200 and is_pdf(r.content):
            return write_paper(ctx, row, Outcome(method="wiley_tdm_api_pdf", pdf_data=r.content, page_url=row["landing_url"]))
        return Outcome(status="human_required", method="wiley_tdm_api", note=f"TDM API status={r.status_code} → 직접 다운로드 대상")
    except Exception as exc:
        return Outcome(status="human_required", method="wiley_tdm_api", note=f"TDM API {type(exc).__name__} → 직접 다운로드 대상")


def wiley_notice() -> None:
    """토큰이 없을 때 실행당 1회 안내 (첫 사용 안내는 SKILL.md 3.2.1 — Claude 가 사용자에게 한 번 묻는다)."""
    global _wiley_notice_shown
    if _wiley_notice_shown:
        return
    _wiley_notice_shown = True
    say("!! Wiley TDM 토큰이 없어 Wiley 논문은 자동으로 받을 수 없습니다. 평소 쓰시는 Chrome 에서 받은 뒤 intake 로 정리합니다. "
        f"토큰을 발급받으면 자동으로 받습니다 (기관 구독이 있으면 무료): {WILEY_TDM_URL} → .env 의 WILEY_TDM_TOKEN")


def h_springer(ctx: Ctx, row: dict) -> Outcome:
    out = Outcome(method="springer_content_pdf", page_url=f"https://link.springer.com/article/{row['doi']}")
    for url in (f"https://link.springer.com/content/pdf/{row['doi']}.pdf", f"https://link.springer.com/content/pdf/{quote(row['doi'], safe='/:')}.pdf"):
        r = ctx.session.get(url, timeout=120)
        if r.status_code == 200 and is_pdf(r.content):
            out.pdf_data = r.content
            break
    try:
        h = ctx.session.get(out.page_url, timeout=60)
        if h.status_code == 200:
            out.html_raw = h.text
    except Exception:
        pass
    if not out.pdf_data and not out.html_raw:
        return Outcome(status="failed", note="springer pdf/html 모두 실패")
    res = write_paper(ctx, row, out)
    if out.html_raw:
        res.si_files = save_si(ctx, row["paper_id"], http_fetch(ctx), find_si_links(out.html_raw, out.page_url))
    return res


def h_mdpi(ctx: Ctx, row: dict) -> Outcome:
    paper = Paper(row["paper_id"], row["doi"], row["title"], row["year"], "", "", "mdpi", "sci_collect")
    out = Outcome(method="mdpi_direct_pdf", page_url=f"https://www.mdpi.com/{row['doi'].split('/',1)[1]}")
    for url in mdpi_pdf_candidates(paper):
        r = ctx.session.get(url, timeout=120)
        if r.status_code == 200 and is_pdf(r.content):
            out.pdf_data = r.content; break
    try:
        h = ctx.session.get(f"https://doi.org/{row['doi']}", timeout=60)
        if h.status_code == 200 and "html" in h.headers.get("content-type", ""):
            out.html_raw, out.page_url = h.text, h.url
    except Exception:
        pass
    if not out.pdf_data and not out.html_raw:
        return Outcome(status="failed", note="mdpi pdf/html 실패")
    res = write_paper(ctx, row, out)
    if out.html_raw:
        res.si_files = save_si(ctx, row["paper_id"], http_fetch(ctx), find_si_links(out.html_raw, out.page_url))
    return res


def h_landing_generic(ctx: Ctx, row: dict, method_prefix: str) -> Outcome:
    """Nature·기타: landing HTML(본문 컨테이너) + citation_pdf_url 등 PDF 후보 + SI."""
    h = ctx.session.get(f"https://doi.org/{row['doi']}", timeout=90)
    if h.status_code != 200:
        return Outcome(status="failed", note=f"landing status={h.status_code}")
    out = Outcome(method=f"{method_prefix}_landing", html_raw=h.text, page_url=h.url)
    cands = html_pdf_candidates(h.text, h.url)
    for url in cands:
        try:
            r = ctx.session.get(url, headers={"Accept": "application/pdf,*/*", "Referer": h.url}, timeout=120)
            if r.status_code == 200 and is_pdf(r.content):
                out.pdf_data = r.content; out.method = f"{method_prefix}_landing_pdf"; break
        except Exception:
            continue
    res = write_paper(ctx, row, out)
    if res.status == "failed" and not cands:
        # 논문 페이지에 PDF 링크가 없고 본문도 짧으면 대개 구독 밖(초록만 보이는 페이지)이다 (2026-09-26 APS PRD·PR Applied 실측)
        res.note = "논문 페이지에 PDF 링크 없음 (구독 밖일 수 있음 → 웹 경로로 확인) — " + res.note
    res.si_files = save_si(ctx, row["paper_id"], http_fetch(ctx), find_si_links(h.text, h.url))
    return res


def h_ecs(ctx: Ctx, row: dict) -> Outcome:
    """ECS / IOPScience: 일반 요청으로 1회만 시도. 봇 확인 페이지(perfdrive/Radware)가 오면 우회·재시도 없이 사용자 확인 묶음으로."""
    landing = f"https://iopscience.iop.org/article/{row['doi']}"
    try:
        lp = ctx.session.get(landing, timeout=90)
        if "perfdrive" in str(lp.url) or b"Radware" in lp.content[:30000]:
            return Outcome(status="human_required", note="IOP 봇 확인 페이지 → 사용자가 창에서 직접 확인 (자동 우회·재시도 없음)")
        time.sleep(3)
        pr = ctx.session.get(landing + "/pdf", headers={"Referer": landing, "Accept": "application/pdf,*/*"}, timeout=120)
        if pr.status_code == 200 and is_pdf(pr.content):
            return write_paper(ctx, row, Outcome(method="ecs_iopscience_direct_pdf", pdf_data=pr.content, html_raw=lp.text if lp.status_code == 200 else "", page_url=landing))
        if "perfdrive" in str(pr.url) or b"Radware" in pr.content[:30000]:
            return Outcome(status="human_required", note="IOP 봇 확인 페이지(pdf) → 사용자가 창에서 직접 확인")
        return Outcome(status="failed", note=f"iop pdf status={pr.status_code}")
    except Exception as exc:
        return Outcome(status="failed", note=f"iop {type(exc).__name__}: {str(exc)[:80]}")


def h_browser_headless(ctx: Ctx, row: dict, kind: str) -> Outcome:
    """ACS / Science / RSC 자동 시도 (headless Chrome, 일반 프로필). 확인 페이지가 나오면 우회·재시도 없이 human_required → assist 에서 사용자가 직접 확인."""
    doi = row["doi"]
    if kind == "acs":
        landing, pdf_url, order = f"https://pubs.acs.org/doi/{doi}", "", ("fetch", "request")
    elif kind == "science":
        landing, pdf_url, order = f"https://www.science.org/doi/{doi}", f"https://www.science.org/doi/pdf/{doi}?download=true", ("nav", "request")
    else:  # rsc
        landing, pdf_url, order = row["landing_url"] or f"https://doi.org/{doi}", "", ("request", "fetch")
    attempts = {"acs": 2, "science": 3, "rsc": 1}.get(kind, 1)   # science: 다운로드 직후 headless 가 닫히는 현상 → 재기동 재시도
    for attempt in range(1, attempts + 1):
        br = None
        try:
            br = Browser(ctx, f"chrome_profile_headless_{kind}", headless=True)   # publisher 스레드마다 별도 프로필 (동시 실행 충돌 방지)
            br.goto(landing); time.sleep(8)
            if br.challenged():
                return Outcome(status="human_required", note=f"{kind} 확인 페이지(headless) → 사용자 확인 묶음")
            raw = br.content()
            if kind in ("rsc", "acs"):   # 새 플랫폼: 페이지에 적힌 PDF 주소를 쓴다
                m = re.search(r'<meta name="citation_pdf_url" content="([^"]+)"', raw)
                if m:
                    pdf_url = htmlmod.unescape(m.group(1))
                elif kind == "acs":
                    pdf_url = f"https://pubs.acs.org/doi/pdf/{doi}"   # 옛 플랫폼 주소 (마지막 대안)
                else:
                    return Outcome(status="human_required", note="rsc citation_pdf_url 없음 → 사용자 확인 묶음")
            data, how = br.get_pdf(pdf_url, landing, order)
            if not is_pdf(data):
                if attempt < attempts:
                    say(f"   [{kind}] {row['paper_id']} attempt {attempt}: {how} → 재기동 재시도")
                    br.close(); br = None; time.sleep(min(ctx.interval(kind), 30)); continue
                return Outcome(status="human_required", note=f"{kind} pdf 실패 ({how}) → 사용자 확인 묶음")
            out = Outcome(method=f"{kind}_browser_{how}", pdf_data=data, html_raw=raw, page_url=landing)
            res = write_paper(ctx, row, out)
            res.si_files = save_si(ctx, row["paper_id"], br.browser_fetch(), find_si_links(raw, landing))
            return res
        except Exception as exc:
            if attempt < attempts:
                time.sleep(15); continue
            return Outcome(status="failed", note=f"{kind} {type(exc).__name__}: {str(exc)[:80]}")
        finally:
            if br:
                br.close()
    return Outcome(status="failed", note=f"{kind} exhausted")


def collect_one(ctx: Ctx, row: dict) -> Outcome:
    pub = row["publisher"]
    if pub in ctx.config.get("abstract_only_publishers", []):
        return write_abstract_only(ctx, row, f"{ctx.config.get('abstract_only_reason')} ({pub})")
    if pub in ctx.config.get("web_only_publishers", []):
        return Outcome(status="human_required", requested=False, note=f"{pub}: 자동 요청을 막는 출판사 → 요청하지 않고 웹 경로")
    if pub == "elsevier":
        return h_elsevier(ctx, row)
    if pub == "wiley":
        return h_wiley(ctx, row)
    if pub == "springer":
        return h_springer(ctx, row)
    if pub == "mdpi":
        return h_mdpi(ctx, row)
    if pub == "nature":
        return h_landing_generic(ctx, row, "nature")
    if pub == "ecs":
        return h_ecs(ctx, row)
    if pub in ("acs", "science", "rsc"):
        return h_browser_headless(ctx, row, pub)
    return h_landing_generic(ctx, row, pub)


def apply_outcome(ctx: Ctx, row: dict, out: Outcome, phase: str) -> None:
    row.update({"status": out.status, "method": out.method, "note": out.note[:300], "updated_at": utc_now()})
    log_row(ctx, {"at": utc_now(), "paper_id": row["paper_id"], "doi": row["doi"], "publisher": row["publisher"], "phase": phase,
                  "status": out.status, "method": out.method, "text_source": out.text_source, "chars": out.chars,
                  "pdf_bytes": out.pdf_bytes, "si_files": out.si_files, "note": out.note[:300]})
    mark = {"full": "OK ", "abstract_only": "ABS", "human_required": "USR", "failed": "FAIL", "pdf_missing": "NOPDF"}.get(out.status, "?")
    say(f"[{row['publisher']:8s}] {mark} {row['paper_id'][:44]:44s} {out.method:36s} text={out.text_source or '-'} {out.chars:>7d}ch pdf={out.pdf_bytes // 1024:>6d}KB si={out.si_files} {out.note[:70]}")
    save_registry(ctx)


def is_block_outcome(out: Outcome) -> bool:
    """사이트가 자동 요청을 막은 결과인가 (확인 페이지·봇 확인·403/429/503). 논문별로 다른 결과(Elsevier API 권한 등)는 해당 없음."""
    if out.status == "human_required" and ("확인 페이지" in out.note or "봇 확인" in out.note):
        return True
    # 202 는 논문 페이지 대신 확인용 응답(IEEE 등, 2026-09-26 실측)
    return out.status == "failed" and bool(re.search(r"status=(403|429|503|202)\b", out.note))


def row_host(row: dict) -> str:
    """generic 출판사의 사이트 구분용 호스트 (Crossref 가 준 논문 페이지 주소). 없으면 빈 문자열."""
    lu = row.get("landing_url") or ""
    host = urlparse(lu).netloc.lower() if lu.startswith("http") else ""
    return "" if host in ("doi.org", "dx.doi.org") else host


def run_group(ctx: Ctx, pub: str, rows: list[dict], phase: str = "collect") -> None:
    blocked_hosts: set[str] = set()   # generic 은 여러 사이트가 섞여 있어 막힌 사이트(호스트)만 건너뛴다 (2026-09-26: T&F 403 이 PNAS·PLOS 등 10편을 막았던 사고)
    for i, row in enumerate(rows):
        host = row_host(row) if pub == "generic" else ""
        if host and host in blocked_hosts:
            apply_outcome(ctx, row, Outcome(status="human_required", requested=False, note=f"{host}: 앞 논문에서 이 사이트가 자동 요청을 막음 → 웹 경로 (요청 생략)"), phase)
            continue
        try:
            out = collect_one(ctx, row)
        except Exception as exc:
            out = Outcome(status="failed", note=f"{type(exc).__name__}: {str(exc)[:120]}")
        blocked = is_block_outcome(out)
        if blocked:
            # 막힌 논문은 다시 시도할 것이 아니라 웹 경로로 받을 것이므로 실패가 아니라 웹 경로 대상으로 둔다 (2026-09-26)
            out.status = "human_required"
            out.note = f"{host or pub}: 사이트가 자동 요청을 막음({out.note}) → 웹 경로"
        apply_outcome(ctx, row, out, phase)
        if blocked and i < len(rows) - 1:
            # 막힌 사이트에 논문마다 다시 요청하지 않는다 (2026-09-25 규칙). 나머지는 요청 없이 웹 경로(평소 쓰는 Chrome)로.
            if pub == "generic" and host:
                blocked_hosts.add(host)
                say(f"   [{pub}] {host} 가 자동 요청을 막았습니다 → 같은 사이트의 남은 논문은 요청하지 않고 웹 경로로 넘깁니다.")
                continue
            say(f"   [{pub}] 사이트가 자동 요청을 막았습니다 → 남은 {len(rows) - i - 1}편은 요청하지 않고 웹 경로로 넘깁니다.")
            for rest in rows[i + 1:]:
                apply_outcome(ctx, rest, Outcome(status="human_required", note=f"{pub}: 앞 논문에서 사이트가 자동 요청을 막음 → 웹 경로 (요청 생략)"), phase)
            break
        if "API 한도 초과" in out.note:
            say(f"   [{pub}] Elsevier API 한도에 걸렸습니다 → 남은 {len(rows) - i - 1}편은 이번에 시도하지 않고 다음 collect 로 미룹니다.")
            break
        if i < len(rows) - 1:
            if not out.requested:
                continue                  # 요청을 보내지 않았다 (OA 아닌 Elsevier, 토큰 없는 Wiley) → 대기 불필요
            # Elsevier 는 자동 단계에서 ScienceDirect 를 요청하지 않는다 (API·저장소 사본만) → API 간격
            key = "elsevier_api" if pub == "elsevier" else pub
            time.sleep(ctx.interval(key if key in ctx.config.get("intervals", {}) else "generic"))


def select_rows(ctx: Ctx, args, statuses: set[str] | None = None) -> list[dict]:
    rows = list(ctx.registry.values())
    if getattr(args, "ids", None):
        want = set(args.ids); rows = [r for r in rows if r["paper_id"] in want or r["doi"] in want]
    if getattr(args, "publishers", None):
        want = set(args.publishers.split(",")); rows = [r for r in rows if r["publisher"] in want]
    if statuses is not None:
        rows = [r for r in rows if r.get("status") in statuses]
    return rows


def cmd_collect(args) -> None:
    ctx = make_ctx(args)
    if args.input:
        for doi in read_dois(args.input):
            if doi.lower() not in ctx.registry:
                try:
                    resolve_doi(ctx, doi); time.sleep(1)
                except Exception as exc:
                    say(f"resolve 실패 {doi}: {exc}")
        save_registry(ctx)
    todo_status = None if args.force else {"resolved", "failed", "pdf_missing", ""}
    rows = select_rows(ctx, args, todo_status)
    if not getattr(args, "ids", None):
        rows = [r for r in rows if r.get("status") != "out_of_scope"]   # 범위 밖(mark) 논문은 id 를 직접 지정할 때만 수집
    if not rows:
        say("수집 대상 없음 (이미 완료됐거나 registry 비어 있음 — resolve 먼저)"); return
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["publisher"], []).append(r)
    say(f"수집 시작: {len(rows)}편, publisher {len(groups)}개 병렬 → {', '.join(f'{k}:{len(v)}' for k, v in groups.items())}")
    threads = [threading.Thread(target=run_group, args=(ctx, pub, rs), name=pub, daemon=True) for pub, rs in groups.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    summarize(ctx, header="collect 완료")


# ------------------------------------------------------------------ assist (보이는 Chrome, 사용자 확인 협력)
def a_elsevier(ctx: Ctx, br: Browser, row: dict, first: bool) -> Outcome:
    pii = row.get("pii") or ""
    url = f"https://www.sciencedirect.com/science/article/pii/{pii}" if pii else row["landing_url"]
    br.goto(url); time.sleep(5)
    if "problem providing the content you requested" in br.content().lower():
        return Outcome(status="human_required", note="ScienceDirect throttle 감지 (IP 일시 차단 문구) → 30분 뒤 재실행")
    if not br.wait_ok("#aep-article-fulltext, article .Body, #body, div.Body", f"Elsevier {row['paper_id']}", ctx.config["assist_wait_seconds"], HUMAN_PUBLISHER_NOTE["elsevier"]):
        return Outcome(status="human_required", note=f"확인 미통과 (title={br.title()[:40]})")
    raw = br.content()
    href = br.page.evaluate("() => { const a = document.querySelector('a.accessbar-utility-component') || document.querySelector('a[href*=\"/pdfft\"]'); return a ? a.href : null; }")
    out = Outcome(method="elsevier_sciencedirect_userassist", html_raw=raw, page_url=br.page.url)
    if href:
        # 사용자 세션에서 정상적으로 내려오는 경우만 받는다. PDF 링크에 출판사 확인이 걸려 HTML 이 오면 우회하지 않고
        # 사용자에게 직접 저장을 요청한다 (창에서 'View PDF' → 저장 → 아래 경로).
        data, how = br.get_pdf(href, url, ("request", "fetch"))
        if is_pdf(data):
            out.pdf_data = data; out.method += f"_{how}"
        else:
            target = paper_dir(ctx, row["paper_id"]) / "pdf" / f"{row['paper_id']}.pdf"
            out.note = f"PDF 는 직접 저장 필요: 창에서 'View PDF' 를 눌러 저장 → {target}"
            say(f"!! [Elsevier {row['paper_id']}] PDF 링크에 출판사 확인이 걸려 있습니다. 창에서 'View PDF' 를 눌러 파일을 다음 경로로 저장해 주세요:\n   {target}")
    res = write_paper(ctx, row, out)
    if not br.page.is_closed():
        res.si_files = save_si(ctx, row["paper_id"], br.browser_fetch(), find_si_links(raw, url))
    return res


def a_rsc(ctx: Ctx, br: Browser, row: dict, first: bool) -> Outcome:
    landing = row["landing_url"] or f"https://doi.org/{row['doi']}"
    br.goto(landing); time.sleep(5)
    if not br.wait_ok('meta[name="citation_pdf_url"]', f"RSC {row['paper_id']}", ctx.config["assist_wait_seconds"], HUMAN_PUBLISHER_NOTE["rsc"]):
        return Outcome(status="human_required", note=f"확인 미통과 (title={br.title()[:40]})")
    raw = br.content()
    pdf_url = br.page.evaluate("() => (document.querySelector('meta[name=\"citation_pdf_url\"]')||{}).content || null")
    out = Outcome(method="rsc_silverchair_userassist", html_raw=raw, page_url=br.page.url)
    if pdf_url:
        data, how = br.get_pdf(pdf_url, br.page.url, ("request", "fetch"))
        if is_pdf(data):
            out.pdf_data = data; out.method += f"_{how}"
        else:
            out.note = f"pdf 실패: {how}"
    res = write_paper(ctx, row, out)
    res.si_files = save_si(ctx, row["paper_id"], br.browser_fetch(), find_si_links(raw, br.page.url))
    return res


def a_ecs(ctx: Ctx, br: Browser, row: dict, first: bool) -> Outcome:
    landing = f"https://iopscience.iop.org/article/{row['doi']}"
    br.goto(landing); time.sleep(6)
    t0, warned = time.time(), False
    while time.time() - t0 < ctx.config["assist_wait_seconds"] and br.challenged():
        if not warned:
            say(f"!! [ECS {row['paper_id']}] {HUMAN_PUBLISHER_NOTE['ecs']} (최대 {ctx.config['assist_wait_seconds']}s)"); warned = True
        time.sleep(5)
    if br.challenged():
        return Outcome(status="human_required", note="봇 확인 미통과 (사용자 직접 확인 필요)")
    time.sleep(4)
    data, how = br.get_pdf(landing + "/pdf", landing, ("fetch", "request"))
    if not is_pdf(data):
        target = paper_dir(ctx, row["paper_id"]) / "pdf" / f"{row['paper_id']}.pdf"
        say(f"!! [ECS {row['paper_id']}] PDF 가 정상 세션에서 내려오지 않습니다. 창에서 PDF 를 직접 저장해 주세요: {target}")
        return Outcome(status="pdf_missing", note=f"PDF 직접 저장 필요 → {target} ({how})")
    raw = br.content()
    res = write_paper(ctx, row, Outcome(method=f"ecs_iopscience_userassist_{how}", pdf_data=data, html_raw=raw, page_url=landing))
    res.si_files = save_si(ctx, row["paper_id"], br.browser_fetch(), find_si_links(raw, landing))
    return res


def a_generic(ctx: Ctx, br: Browser, row: dict, first: bool) -> Outcome:
    """ACS(확인 걸림) / Wiley(토큰 없음) / Science / 기타: landing → 본문 + PDF 후보 in-page fetch."""
    landing = row["landing_url"] or f"https://doi.org/{row['doi']}"
    pub = row["publisher"]
    if pub == "acs":
        landing = f"https://pubs.acs.org/doi/{row['doi']}"
    br.goto(landing); time.sleep(6)
    if not br.wait_ok("body", f"{pub} {row['paper_id']}", ctx.config["assist_wait_seconds"], "열린 Chrome 창에서 확인을 눌러 주세요."):
        return Outcome(status="human_required", note="확인 미통과")
    raw = br.content()
    cands = html_pdf_candidates(raw, br.page.url)
    if pub == "acs":
        cands = cands + [f"https://pubs.acs.org/doi/pdf/{row['doi']}"]   # 페이지의 citation_pdf_url 이 먼저, 옛 주소는 마지막
    if pub == "wiley":
        cands = [f"https://onlinelibrary.wiley.com/doi/pdfdirect/{row['doi']}", f"https://onlinelibrary.wiley.com/doi/pdf/{row['doi']}"] + cands
    out = Outcome(method=f"{pub}_userassist", html_raw=raw, page_url=br.page.url)
    for c in (cands[:2] if pub == "wiley" else cands[:6]):   # wiley 는 pdf/pdfdirect 2개까지만 (후보 다중 probe 금지)
        data, how = br.get_pdf(c, br.page.url, ("fetch", "request") if pub != "science" else ("nav", "request"))
        if is_pdf(data):
            out.pdf_data = data; out.method += f"_{how}"; break
    if not out.pdf_data and not raw:
        return Outcome(status="failed", note="본문·PDF 모두 실패")
    res = write_paper(ctx, row, out)
    res.si_files = save_si(ctx, row["paper_id"], br.browser_fetch(), find_si_links(raw, br.page.url))
    return res


def cmd_assist(args) -> None:
    ctx = make_ctx(args)
    rows = select_rows(ctx, args, None if args.force else {"human_required", "pdf_missing", "failed"})
    if not rows:
        say("사용자 확인이 필요한 논문이 없습니다."); return
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["publisher"], []).append(r)
    # 2026-09-25 규칙: 기본은 도구 창을 열지 않고 웹 경로 목록만 만든다 (평소 쓰는 Chrome 에서 받은 뒤 intake).
    # 도구 창은 Elsevier·Wiley 에서 확인 창이 반복되고 RSC 는 PDF 가 거부되었다 (2026-09-24 실측). --window 면 예전 동작(Elsevier·Wiley 제외).
    manual_pubs = set(groups) if not getattr(args, "window", False) else {"wiley", "elsevier"}
    for pub in [p for p in groups if p in manual_pubs]:
        rs = groups.pop(pub)
        note = WEB_NOTE.get(pub, "자동으로 받지 못해 평소 쓰시는 Chrome 에서 받아야 합니다.")
        lst = write_manual_list(ctx, rs, note)
        say(f"!! {pub} {len(rs)}편: {note}")
        for r in rs[:10]:
            say(f"   {r['paper_id']}: {manual_url(r)}  →  {paper_dir(ctx, r['paper_id']) / 'pdf' / (r['paper_id'] + '.pdf')}")
        say(f"   전체 목록: {lst}  (받은 뒤 intake 실행)")
    if not groups:
        summarize(ctx, header="assist 완료"); return
    say("=== 사람 확인 협력 단계 ===")
    say("보이는 Chrome 창이 열립니다. 확인 창(체크박스)이 보이면 한 번 눌러 주세요. 같은 사이트의 다음 논문은 대체로 자동으로 넘어갑니다.")
    for pub, rs in groups.items():
        say(f"  - {pub}: {len(rs)}편  {HUMAN_PUBLISHER_NOTE.get(pub, '')}")
    br = Browser(ctx, "chrome_profile_assist", headless=False)
    try:
        for pub, rs in groups.items():
            handler = {"elsevier": a_elsevier, "rsc": a_rsc, "ecs": a_ecs}.get(pub, a_generic)
            for i, row in enumerate(rs):
                out = None
                for attempt in range(2):   # 브라우저가 닫히면(다운로드 직후 등) 재기동 후 1회 재시도
                    try:
                        if br.page.is_closed():
                            br.close(); br = Browser(ctx, "chrome_profile_assist", headless=False)
                        out = handler(ctx, br, row, i == 0)
                    except Exception as exc:
                        out = Outcome(status="failed", note=f"{type(exc).__name__}: {str(exc)[:120]}")
                    if not ("TargetClosedError" in out.note or "browser has been closed" in out.note) or attempt == 1:
                        break
                    say(f"   [{pub}] {row['paper_id']}: 브라우저 닫힘 → 재기동 후 재시도")
                    br.close(); br = Browser(ctx, "chrome_profile_assist", headless=False)
                apply_outcome(ctx, row, out, "assist")
                if out.note.startswith("ScienceDirect throttle"):
                    say(f"!! {pub}: 차단 문구 감지 — 이 사이트의 남은 {len(rs) - i - 1}편은 건너뜁니다. 30분 뒤 `assist --publishers {pub}` 로 재실행하세요.")
                    break
                if out.status == "human_required" and "확인 미통과" in out.note:
                    say(f"!! {pub}: 확인을 통과하지 못해 이 사이트의 남은 {len(rs) - i - 1}편은 건너뜁니다. 자리에 없으셨다면 나중에 `assist --publishers {pub}` 로 다시 하고, 눌러도 확인 창이 반복됐다면 직접 다운로드 목록으로 처리합니다.")
                    break
                if i < len(rs) - 1:
                    time.sleep(ctx.interval(pub if pub in ctx.config.get("intervals", {}) else "generic"))
    finally:
        br.close()
    left = [r for rs in groups.values() for r in rs if r.get("status") in ("human_required", "pdf_missing")]
    if left:
        lst = write_manual_list(ctx, left, "도구 창에서 PDF 를 받지 못함")
        say(f"!! PDF 를 받지 못한 논문 {len(left)}편 — 평소 쓰시는 Chrome 에서 직접 받아 아래 경로에 저장해 주세요:")
        for r in left[:10]:
            say(f"   {r['paper_id']}: {manual_url(r)}  →  {paper_dir(ctx, r['paper_id']) / 'pdf' / (r['paper_id'] + '.pdf')}")
        say(f"   전체 목록: {lst}  (저장 후 status 실행)")
    summarize(ctx, header="assist 완료")


# ------------------------------------------------------------------ status
def summarize(ctx: Ctx, header: str = "status") -> None:
    load_registry(ctx) if not ctx.registry else None
    rows = list(ctx.registry.values())
    cnt: dict[str, int] = {}
    for r in rows:
        cnt[r.get("status") or "?"] = cnt.get(r.get("status") or "?", 0) + 1
    say(f"=== {header}: 총 {len(rows)}편 — " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())))
    human = [r for r in rows if r.get("status") == "human_required"]
    if human:
        by = {}
        for r in human:
            by.setdefault(r["publisher"], []).append(r["paper_id"])
        say("웹 경로로 받을 논문 (평소 쓰는 Chrome → intake): " + "; ".join(f"{k} {len(v)}편" for k, v in by.items()))
    oos = [r for r in rows if r.get("status") == "out_of_scope"]
    if oos:
        say(f"범위 밖으로 표시(미수집): {len(oos)}편 — 다시 받으려면 `mark --ids <id> --status resolved` 후 collect")
    absonly = [r for r in rows if r.get("status") == "abstract_only"]
    if absonly:
        say(f"초록만 저장 (미구독): {len(absonly)}편 — " + ", ".join(sorted({r['publisher'] for r in absonly})))
    failed = [r for r in rows if r.get("status") == "failed"]
    for r in failed[:20]:
        say(f"  FAIL {r['paper_id']} [{r['publisher']}] {r.get('note', '')[:100]}")


def ingest_manual_pdfs(ctx: Ctx) -> int:
    """사용자가 papers/{id}/pdf/{id}.pdf 에 직접 저장한 PDF 를 반영: 텍스트 추출(write_paper) + 상태 갱신.
    대상: 메타만 있음 / 사용자 확인 필요 / PDF 없음 / 실패. 같은 폴더의 html·xml 원본이 있으면 텍스트 선택에 함께 쓴다."""
    n = 0
    for row in list(ctx.registry.values()):
        if row.get("status") not in ("resolved", "pdf_missing", "human_required", "failed"):
            continue
        d = ctx.papers_root() / row["paper_id"]
        p = d / "pdf" / f"{row['paper_id']}.pdf"
        if not (p.exists() and p.stat().st_size > 10000):
            continue
        data = p.read_bytes()
        if not is_pdf(data):
            say(f"  !! {p} 는 PDF 가 아닙니다 (저장 파일 확인 필요)"); continue
        html_p, xml_p = d / "html" / f"{row['paper_id']}.html", d / "xml" / f"{row['paper_id']}.xml"
        out = Outcome(method="manual_user_download", pdf_data=data,
                      html_raw=html_p.read_text(encoding="utf-8", errors="ignore") if html_p.exists() else "",
                      xml_raw=xml_p.read_bytes() if xml_p.exists() else b"",
                      page_url=row.get("landing_url") or f"https://doi.org/{row['doi']}")
        res = write_paper(ctx, row, out)
        res.si_files = len(list((d / "pdf").glob(f"{row['paper_id']}_SI*")))
        apply_outcome(ctx, row, res, "manual")
        n += 1
    return n


def cmd_reextract(args) -> None:
    """저장된 원본(pdf/html/xml)만으로 source.md·source.json 을 다시 만든다. 추출 규칙을 고친 뒤 기존 수집분에 적용할 때 쓴다 (요청 없음)."""
    ctx = make_ctx(args)
    rows = select_rows(ctx, args, {"full", "pdf_missing"})
    n = 0
    for row in rows:
        pid = row["paper_id"]
        d = ctx.papers_root() / pid
        pdf_p, html_p, xml_p = d / "pdf" / f"{pid}.pdf", d / "html" / f"{pid}.html", d / "xml" / f"{pid}.xml"
        if not (pdf_p.exists() or html_p.exists() or xml_p.exists()):
            continue
        try:
            sj = json.loads((d / "source.json").read_text(encoding="utf-8"))
        except Exception:
            sj = {}
        out = Outcome(method=sj.get("collection_method") or row.get("method") or "reextract",
                      pdf_data=pdf_p.read_bytes() if pdf_p.exists() else b"",
                      html_raw=html_p.read_text(encoding="utf-8", errors="ignore") if html_p.exists() else "",
                      xml_raw=xml_p.read_bytes() if xml_p.exists() else b"",
                      page_url=sj.get("source_url") or row.get("landing_url") or "")
        res = write_paper(ctx, row, out)
        apply_outcome(ctx, row, res, "reextract")
        n += 1
    say(f"본문 다시 추출: {n}편")
    summarize(ctx)


def cmd_status(args) -> None:
    ctx = make_ctx(args)
    changed = ingest_manual_pdfs(ctx)
    if changed:
        say(f"직접 저장된 PDF 반영: {changed}편")
    if (ctx.work / "manual_download.csv").exists():
        update_manual_csv(ctx, [])   # 끝난 논문을 웹 경로 목록에서 뺀다
    summarize(ctx)


PIP_NAMES = {"bs4": "beautifulsoup4", "wiley_tdm": "wiley-tdm"}


def cmd_doctor(args) -> None:
    """처음 쓰기 전 환경 점검. 읽기만 한다 — 폴더를 만들거나 설정을 바꾸지 않는다."""
    import importlib
    kb_root = Path(args.kb_root)
    problems, warns = [], []

    def ok(msg):
        say(f"  [OK]   {msg}")

    def warn(msg):
        warns.append(msg); say(f"  [주의] {msg}")

    def bad(msg):
        problems.append(msg); say(f"  [문제] {msg}")

    def info(msg):
        say(f"  [정보] {msg}")

    say("=== sci_collect doctor — 환경 점검 (읽기만 함)")
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro} — {sys.executable}")
    else:
        bad(f"Python {v.major}.{v.minor} — 3.11 이상이 필요하다 ({sys.executable})")
    for mod, why, level in (("requests", "필수", "bad"), ("pymupdf", "필수 (PDF 텍스트)", "bad"), ("bs4", "필수 (HTML 본문)", "bad"),
                            ("lxml", "필수 (HTML 본문)", "bad"), ("truststore", "필수 (기관 망 인증서)", "bad"),
                            ("openpyxl", "xlsx 입력에 필요", "warn"), ("playwright", "예전 도구 창 방식에만 필요", "info"),
                            ("wiley_tdm", "Wiley 토큰이 있을 때 필요", "info")):
        try:
            m = importlib.import_module(mod)
        except ImportError:
            m = None
            if mod == "pymupdf":
                try:
                    m = importlib.import_module("fitz")
                except ImportError:
                    m = None
        if m is not None:
            ver = getattr(m, "__version__", "") or getattr(m, "VersionBind", "") or ""
            ok(f"패키지 {mod} {ver}".rstrip())
        elif level == "bad":
            bad(f"패키지 {mod} 없음 — {why}. pip install {PIP_NAMES.get(mod, mod)}")
        elif level == "warn":
            warn(f"패키지 {mod} 없음 — {why}")
        else:
            info(f"패키지 {mod} 없음 — {why}")
    prof, prefs = chrome_prefs()
    if not prefs:
        warn("Chrome 설정을 읽지 못함 — Chrome 이 없거나 다른 위치. 웹 경로를 쓰려면 SKILL.md 3.1 의 Chrome 설정 두 가지를 직접 확인")
    else:
        pdf_ext = prefs.get("plugins", {}).get("always_open_pdf_externally")
        if pdf_ext:
            ok(f"Chrome({prof}) PDF 설정 = PDF 다운로드")
        else:
            bad(f"Chrome({prof}) PDF 설정 = Chrome 에서 열기 — chrome://settings/content/pdfDocuments 에서 'PDF 다운로드' 로 바꾼다 (웹 경로에 필수)")
        if prefs.get("download", {}).get("prompt_for_download"):
            bad(f"Chrome({prof}) 저장 위치 확인 = 켜짐 — chrome://settings/downloads 에서 '다운로드 전에 각 파일의 저장 위치 확인' 을 끈다 (파일마다 저장 창이 떠서 웹 경로가 멈춤)")
        else:
            ok(f"Chrome({prof}) 저장 위치 확인 = 꺼짐")
        ext_id = "fcoeoabgfenejglbffodgkkbkcdhcgfn"   # Claude in Chrome
        ud = chrome_user_data_dir()
        if ud and (ud / prof / "Extensions" / ext_id).exists():
            ok(f"Chrome({prof}) Claude in Chrome 확장 설치됨")
        else:
            warn(f"Chrome({prof}) Claude in Chrome 확장 없음 — Claude 의 웹 다운로드에 필요. https://chromewebstore.google.com/detail/claude/{ext_id} 에서 설치 (Codex 는 필요 없음)")
    cfg = load_config(kb_root)
    ddir, how = find_downloads_dir(cfg)
    if ddir.exists() and os.access(ddir, os.W_OK):
        ok(f"다운로드 폴더 {ddir} ({how})")
    else:
        bad(f"다운로드 폴더 {ddir} ({how}) 없음 또는 쓰기 불가 — intake --downloads 로 지정하거나 설정 downloads_dir")
    env = load_env(Path(args.env) if getattr(args, "env", None) else kb_root / ".env")
    for k, what in (("ELSEVIER_API_KEY", "Elsevier OA 논문 자동"), ("WILEY_TDM_TOKEN", "Wiley 자동")):
        info(f"{k} {'있음' if env.get(k) else '없음'} — {what}{'' if env.get(k) else ' 대신 웹 경로'}")
    used = next((p for p in (kb_root / "sci_collect.config.json", Path.home() / ".claude" / "sci" / "sci_collect.config.json") if p.exists()), None)
    info(f"설정 파일 {used or '없음 (기본값)'}")
    reg = kb_root / "collection_registry.csv"
    if reg.exists():
        with open(reg, encoding="utf-8-sig", newline="") as fh:
            n = sum(1 for _ in csv.DictReader(fh))
        ok(f"root {kb_root} — 목록 {n}편")
    else:
        info(f"root {kb_root} — 아직 목록 없음 (resolve 로 만든다)")
    try:
        r = requests.get("https://api.crossref.org/works/10.1039/d4gc02672a", timeout=20, headers={"User-Agent": UA_API.format(mailto="doctor")})
        (ok if r.status_code == 200 else warn)(f"Crossref 응답 {r.status_code}")
    except requests.exceptions.SSLError as exc:
        bad(f"SSL 오류 — 기관 망 인증서 문제. truststore 설치 확인: {str(exc)[:80]}")
    except Exception as exc:
        bad(f"인터넷 연결 실패 — {type(exc).__name__}: {str(exc)[:80]}")
    info("이 명령으로 확인할 수 없는 것: Claude in Chrome 확장의 연결·로그인(Claude 가 대화에서 확인), 교내 망 여부(구독 논문 페이지가 열리는지로 확인)")
    say(f"=== 점검 끝: 문제 {len(problems)}, 주의 {len(warns)}" + (" — 문제를 고친 뒤 다시 실행" if problems else " — 시작해도 된다  ▼・ᴥ・▼"))


def manual_url(row: dict) -> str:
    """사용자가 평소 쓰는 Chrome 에서 열 논문 페이지 주소."""
    if row["publisher"] == "wiley":
        lu = row.get("landing_url") or ""
        return lu if "wiley.com" in lu else f"https://onlinelibrary.wiley.com/doi/{row['doi']}"
    if row["publisher"] == "elsevier" and row.get("pii"):
        return f"https://www.sciencedirect.com/science/article/pii/{row['pii']}"
    return row.get("landing_url") or f"https://doi.org/{row['doi']}"


MANUAL_FIELDS = ["paper_id", "publisher", "title", "url", "save_to", "reason"]


def update_manual_csv(ctx: Ctx, new_rows: list[dict]) -> Path:
    """_collect/manual_download.csv 누적 갱신. 한 행 = 사용자가 저장할 파일 하나 (save_to 가 키)."""
    p = ctx.work / "manual_download.csv"
    rows: dict[str, dict] = {}
    with _log_lock:
        if p.exists():
            with open(p, encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    rows[r.get("save_to") or r.get("paper_id", "")] = r
        for r in new_rows:
            rows[r["save_to"]] = r
        # 이미 받아 정리한 행은 뺀다 (2026-09-26 중단·재개 시험): 저장 자리에 파일이 있거나, 본문 행인데 그 논문이 이미 전문/범위 밖이면 목록에서 제외.
        done = {r["paper_id"] for r in ctx.registry.values() if r.get("status") in ("full", "out_of_scope")}
        keep = [r for r in rows.values()
                if not Path(r.get("save_to") or "").exists()
                and not (r.get("paper_id") in done and str(r.get("save_to", "")).endswith(f"{r.get('paper_id')}.pdf"))]
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MANUAL_FIELDS, extrasaction="ignore")
            w.writeheader(); w.writerows(keep)
    return p


def write_manual_list(ctx: Ctx, rows: list[dict], reason: str) -> Path:
    """본문 PDF 직접 다운로드 목록 (논문 페이지 URL + 저장 경로)."""
    new = [{"paper_id": r["paper_id"], "publisher": r["publisher"], "title": r.get("title", ""), "url": manual_url(r),
            "save_to": str(paper_dir(ctx, r["paper_id"]) / "pdf" / f"{r['paper_id']}.pdf"), "reason": reason} for r in rows]
    return update_manual_csv(ctx, new)


def add_manual_si(ctx: Ctx, pid: str, urls: list[str], start: int = 1) -> Path:
    """받지 못한 SI 링크를 직접 다운로드 목록에 추가. 저장 이름은 이미 받은 SI 다음 번호부터."""
    row = next((r for r in ctx.registry.values() if r.get("paper_id") == pid), {})
    d = paper_dir(ctx, pid) / "pdf"
    new = [{"paper_id": pid, "publisher": row.get("publisher", ""), "title": row.get("title", ""), "url": u,
            "save_to": str(d / si_name(pid, k, si_ext(u, default="pdf"))), "reason": "SI 직접 다운로드 (도구로 받지 못함)"}
           for k, u in enumerate(urls, start=start)]
    say(f"   [{pid}] SI {len(urls)}개를 받지 못해 직접 다운로드 목록에 올렸습니다.")
    return update_manual_csv(ctx, new)


def cmd_mark(args) -> None:
    """범위 밖(out_of_scope) 표시 / 해제(resolved). Claude 의 사전 분류 결과를 registry 에 기록하는 유일한 경로 (CSV 직접 편집 금지)."""
    ctx = make_ctx(args)
    want = {w.lower() for w in args.ids}
    n = 0
    for row in ctx.registry.values():
        if row["paper_id"].lower() in want or row["doi"].lower() in want:
            row["status"] = args.status
            row["method"] = ""
            row["note"] = args.note or ("범위 밖 — 수집 제외" if args.status == "out_of_scope" else "")
            row["updated_at"] = utc_now()
            n += 1
    save_registry(ctx)
    say(f"{args.status} 표시: {n}편 (요청 {len(want)}건)")
    summarize(ctx)


# ------------------------------------------------------------------ intake (다운로드 폴더 정리)
# 사용자가 평소 쓰는 Chrome 에서 받은 PDF·SI 를 다운로드 폴더에서 찾아, 어느 논문인지 가린 뒤 정해진 자리로 옮기고 반영한다.
# 판정 근거(점수): 파일명에 논문 코드(PII·DOI 끝부분) 3, 앞 두 쪽에 DOI 2, 첫 쪽에 제목 2, PDF 뒤쪽에만 DOI 1.
# SI 구분: 파일명 규칙(mmc·_suppl·_si_·-sup-·-sm 등) 또는 첫 쪽 맨 앞 80자 안의 'Supporting/Supplementary' 문구.
#   (ACS 본문 PDF 는 첫 쪽 286자 뒤에 'Supporting Information' 안내가 있어 넓게 보면 SI 로 오판 — 2026-09-25 실측)
# 최고 점수가 2 이상이고 한 논문에만 해당할 때만 옮긴다. 애매하거나 못 가린 파일은 그대로 두고 보고한다 (지우지 않는다).
SI_NAME_RE = re.compile(r"(mmc\d+|_suppl|_si_\d+|-sup-\d+|suppmat|suppdata|supp\d|[-_]sm[\s._(-]|[-_]sm$|supporting|supplement|[-_]esm\b)", re.I)
SI_TEXT_PHRASES = ("supportinginformation", "supplementarymaterial", "supplementaryinformation", "electronicsupplementary", "supplementarydata")
INTAKE_EXTS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".zip", ".cif", ".txt", ".pptx", ".mp4", ".mov", ".avi"}


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", s or "").lower())


def row_codes(row: dict) -> list[str]:
    """파일명 대조용 논문 코드: Elsevier PII, DOI 끝부분 전체, DOI 마지막 조각. 6자 이상이고 숫자가 들어간 것만."""
    codes = []
    if row.get("publisher") == "elsevier" and row.get("pii"):
        codes.append(_alnum(row["pii"]))
    suffix = (row.get("doi") or "").split("/", 1)[-1]
    codes.append(_alnum(suffix))
    parts = [p for p in re.split(r"[./]", suffix) if p]
    if parts:
        codes.append(_alnum(parts[-1]))
    return [c for c in dict.fromkeys(codes) if len(c) >= 6 and re.search(r"\d", c)]


def _file_sha1(p: Path) -> str:
    import hashlib
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pdf_texts(p: Path) -> tuple[str, str, str]:
    """(첫 쪽, 앞 두 쪽, 전체) 텍스트. PDF 가 아니거나 읽기 실패면 빈 문자열."""
    try:
        doc = fitz.open(p)
        pages = [pg.get_text() or "" for pg in doc]
        doc.close()
    except Exception:
        return "", "", ""
    return (pages[0] if pages else ""), "\n".join(pages[:2]), "\n".join(pages)


def _docx_text(p: Path) -> str:
    """Word(.docx) 본문 텍스트. 파일명에 논문 정보가 없는 SI(예: IOP 의 1960.docx)를 내용으로 대조할 때 쓴다. 읽기 실패면 빈 문자열."""
    import zipfile
    try:
        with zipfile.ZipFile(p) as z:
            x = z.read("word/document.xml").decode("utf-8", "ignore")
    except Exception:
        return ""
    x = re.sub(r"<w:tab/>", " ", x)
    x = re.sub(r"</w:p>", "\n", x)
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", x))


def match_download(ctx: Ctx, f: Path) -> dict:
    """다운로드 파일 한 개를 레지스트리 논문과 대조. 반환: paper_id·slot(main|si)·score·reason·status(matched|ambiguous|unmatched)."""
    name_n = _alnum(f.stem)
    is_pdf_file = f.suffix.lower() == ".pdf"
    p1 = p12 = full = ""
    if is_pdf_file:
        p1, p12, full = _pdf_texts(f)
    elif f.suffix.lower() == ".docx":
        full = _docx_text(f)
        p1, p12 = full[:3000], full[:6000]
    p1_n, p12_n, full_n = _alnum(p1), _alnum(p12), _alnum(full)
    scored = []
    for row in ctx.registry.values():
        s, why = 0, []
        if any(c in name_n for c in row_codes(row)):
            s += 3; why.append("파일명 코드")
        doi_n = _alnum(row.get("doi"))
        if doi_n and p12_n and doi_n in p12_n:
            s += 2; why.append("앞쪽 DOI")
        elif doi_n and full_n and doi_n in full_n:
            s += 1; why.append("뒤쪽 DOI")
        title_n = _alnum(row.get("title"))[:40]
        if len(title_n) >= 20 and p1_n and title_n in p1_n:
            s += 2; why.append("첫 쪽 제목")
        if s:
            scored.append((s, row, why))
    if not scored:
        return {"status": "unmatched", "reason": "해당 논문 없음"}
    scored.sort(key=lambda x: -x[0])
    best = scored[0][0]
    tops = [x for x in scored if x[0] == best]
    if best < 2:
        return {"status": "unmatched", "reason": f"근거 부족 (점수 {best})"}
    if len(tops) > 1:
        return {"status": "ambiguous", "reason": "여러 논문에 해당: " + ", ".join(x[1]["paper_id"] for x in tops[:3])}
    s, row, why = scored[0]
    slot = "si" if (not is_pdf_file or SI_NAME_RE.search(f.name) or any(ph in p1_n[:80] for ph in SI_TEXT_PHRASES)) else "main"
    return {"status": "matched", "paper_id": row["paper_id"], "row": row, "slot": slot, "score": s, "reason": " + ".join(why)}


# ------------------------------------------------------------------ 다운로드 폴더 위치 (intake · doctor)
def chrome_user_data_dir() -> Path | None:
    """Chrome 사용자 데이터 폴더. 없으면 None."""
    if sys.platform.startswith("win"):
        la = os.environ.get("LOCALAPPDATA")
        cands = [Path(la) / "Google" / "Chrome" / "User Data"] if la else []
    elif sys.platform == "darwin":
        cands = [Path.home() / "Library" / "Application Support" / "Google" / "Chrome"]
    else:
        cands = [Path.home() / ".config" / "google-chrome"]
    return next((p for p in cands if (p / "Local State").exists()), None)


def chrome_prefs() -> tuple[str, dict]:
    """마지막에 쓴 Chrome 프로필의 Preferences (읽기만 한다). (프로필 폴더 이름, 설정 dict). 못 읽으면 ('', {})."""
    ud = chrome_user_data_dir()
    if not ud:
        return "", {}
    try:
        prof = json.loads((ud / "Local State").read_text(encoding="utf-8")).get("profile", {}).get("last_used") or "Default"
    except Exception:
        prof = "Default"
    p = ud / prof / "Preferences"
    try:
        return prof, (json.loads(p.read_text(encoding="utf-8")) if p.exists() else {})
    except Exception:
        return prof, {}


def windows_downloads_dir() -> Path | None:
    """Windows 가 정한 '다운로드' 폴더 (OneDrive 등으로 옮긴 경우 포함). Windows 가 아니면 None."""
    if not sys.platform.startswith("win"):
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
            v, _ = winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}")
        return Path(os.path.expandvars(v))
    except Exception:
        return None


def find_downloads_dir(config: dict, override: str | None = None) -> tuple[Path, str]:
    """intake 가 볼 다운로드 폴더와 그 근거. 순서: --downloads → 설정 downloads_dir → Chrome 설정의 다운로드 폴더 → Windows 다운로드 폴더 → ~/Downloads."""
    if override:
        return Path(override), "--downloads 인자"
    if config.get("downloads_dir"):
        return Path(config["downloads_dir"]), "설정 downloads_dir"
    d = chrome_prefs()[1].get("download", {}).get("default_directory")
    if d:
        return Path(d), "Chrome 설정의 다운로드 폴더"
    w = windows_downloads_dir()
    if w:
        return w, "Windows 다운로드 폴더"
    return Path.home() / "Downloads", "기본 Downloads"


def cmd_intake(args) -> None:
    import shutil
    ctx = make_ctx(args)
    ddir, how = find_downloads_dir(ctx.config, args.downloads)
    if not ddir.exists():
        say(f"다운로드 폴더가 없습니다: {ddir} ({how}). 다른 폴더면 --downloads 로 지정"); return
    since = time.time() - float(args.hours) * 3600
    files = sorted([p for p in ddir.iterdir() if p.is_file() and p.suffix.lower() in INTAKE_EXTS and p.stat().st_mtime >= since],
                   key=lambda p: p.stat().st_mtime)
    skip = si_skip_set(ctx)
    skipped = [p for p in files if p.suffix.lower().lstrip(".") in skip]
    files = [p for p in files if p not in skipped]
    say(f"다운로드 폴더 {ddir} ({how}) — 최근 {args.hours}시간 안의 파일 {len(files)}개 확인{' (미리보기, 옮기지 않음)' if args.dry_run else ''}")
    if skipped:
        say(f"  받지 않는 SI 형식(동영상, 결정 구조, 압축, 스프레드시트 등) {len(skipped)}개는 옮기지 않고 그대로 둠: " + ", ".join(p.name for p in skipped[:5]))
    moved_main, results = 0, []
    for f in files:
        m = match_download(ctx, f)
        action = "그대로 둠"
        if m["status"] == "matched":
            pid, row = m["paper_id"], m["row"]
            pdir = paper_dir(ctx, pid) / "pdf"
            if m["slot"] == "main":
                dst = pdir / f"{pid}.pdf"
                if dst.exists():
                    action = "이미 본문 PDF 있음 — 그대로 둠"
                else:
                    action = f"본문 PDF → {dst.name}"
                    if not args.dry_run:
                        shutil.move(str(f), str(dst)); moved_main += 1
            else:
                digest = _file_sha1(f)
                existing = sorted(pdir.glob(f"{pid}_SI*"))
                if any(_file_sha1(e) == digest for e in existing):
                    action = "같은 SI 이미 있음 — 그대로 둠"
                else:
                    ext = (f.suffix.lower().lstrip(".") or "bin")[:5]
                    k = 1
                    while any(pdir.glob(f"{si_name(pid, k, '*')}")):
                        k += 1
                    dst = pdir / si_name(pid, k, ext)
                    action = f"SI → {dst.name}"
                    if not args.dry_run:
                        shutil.move(str(f), str(dst))
        results.append((f.name, m, action))
        say(f"  {f.name[:60]:60s} | {m.get('paper_id', '-'):32s} | {m.get('slot', '-'):4s} | {m.get('reason', '')[:40]:40s} | {action}")
    if not args.dry_run:
        p = ctx.work / "intake_log.csv"
        new = not p.exists()
        with open(p, "a", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["at", "file", "status", "paper_id", "slot", "score", "reason", "action"])
            for name, m, action in results:
                w.writerow([utc_now(), name, m["status"], m.get("paper_id", ""), m.get("slot", ""), m.get("score", ""), m.get("reason", ""), action])
        if moved_main:
            say(f"본문 PDF {moved_main}편을 옮겼습니다. 본문 텍스트를 뽑아 반영합니다.")
            ingest_manual_pdfs(ctx)
    left = [r for r in results if r[1]["status"] != "matched"]
    if left:
        say(f"논문을 가리지 못해 그대로 둔 파일 {len(left)}개 — 다른 파일이거나 레지스트리에 없는 논문입니다.")
    if not args.dry_run and (ctx.work / "manual_download.csv").exists():
        update_manual_csv(ctx, [])   # 끝난 논문을 웹 경로 목록에서 뺀다 (중단 뒤 재개 때 남은 것만 보이게)
    summarize(ctx, header="intake 완료" if not args.dry_run else "intake 미리보기")


# ------------------------------------------------------------------ CLI
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="sci_collect — 논문 원문 수집 CLI (LLM 없음)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--kb-root", required=True, help="논문 폴더 루트 (papers/ 가 이 아래 생성)")
    common.add_argument("--env", default=None, help=".env 경로 (기본: <kb-root>/.env)")
    common.add_argument("--mailto", default=None, help="Crossref/OpenAlex 예의용 이메일")
    p = sub.add_parser("resolve", parents=[common]); p.add_argument("--input", nargs="+", required=True, help="DOI 목록 파일(csv/xlsx/txt) 또는 DOI 문자열")
    p = sub.add_parser("collect", parents=[common]); p.add_argument("--input", nargs="*", default=None); p.add_argument("--ids", nargs="*"); p.add_argument("--publishers", default=None); p.add_argument("--force", action="store_true")
    p = sub.add_parser("assist", parents=[common]); p.add_argument("--ids", nargs="*"); p.add_argument("--publishers", default=None); p.add_argument("--force", action="store_true"); p.add_argument("--window", action="store_true", help="예전 도구 창 방식 (기본: 창 없이 웹 경로 목록만)")
    p = sub.add_parser("intake", parents=[common]); p.add_argument("--downloads", default=None, help="다운로드 폴더 (기본: 설정 downloads_dir → Chrome 설정 → Windows 다운로드 폴더 → ~/Downloads)"); p.add_argument("--hours", type=float, default=24, help="최근 몇 시간 안에 받은 파일만"); p.add_argument("--dry-run", action="store_true", help="옮기지 않고 판정만 보기")
    p = sub.add_parser("reextract", parents=[common]); p.add_argument("--ids", nargs="*"); p.add_argument("--publishers", default=None)
    p = sub.add_parser("mark", parents=[common]); p.add_argument("--ids", nargs="+", required=True, help="paper_id 또는 DOI"); p.add_argument("--status", choices=["out_of_scope", "resolved"], required=True); p.add_argument("--note", default="")
    sub.add_parser("status", parents=[common])
    sub.add_parser("doctor", parents=[common], help="처음 쓰기 전 환경 점검 (읽기만 함)")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    {"resolve": cmd_resolve, "collect": cmd_collect, "assist": cmd_assist, "mark": cmd_mark, "reextract": cmd_reextract, "intake": cmd_intake, "status": cmd_status, "doctor": cmd_doctor}[args.cmd](args)


if __name__ == "__main__":
    main()
