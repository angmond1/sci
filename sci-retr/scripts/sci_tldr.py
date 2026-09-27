#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sci_tldr.py — 논문마다 한국어 한 줄 요약(index.csv 의 한줄요약 열). 사용자가 원할 때만 쓴다 (sci-tldr skill).

    python sci_tldr.py prep  --kb-root <dir> [--ids …] [--all] [--size 50] [--max-kb 50]   # _collect/tldr_batch_<n>.md (+ tldr_src_<n>.json)
    python sci_tldr.py apply --kb-root <dir> [--files <jsonl …>]                             # _collect/tldr_<n>.jsonl 검증 뒤 한줄요약 열에 병합

요약을 쓰는 것은 LLM(sonnet 전용 에이전트 sci-tldr-writer, 또는 몇 편이면 메인)이고, 이 스크립트는 준비와 검증·병합만 한다.
할루시네이션 막기 (2026-09-27 설계):
  - 재료: 초록(1,500자까지), 초록이 짧거나 없으면 본문 앞부분(이 논문 제목이 나오는 자리부터). 재료가 없으면 요약하지 않는다(제목만으로 쓰지 않는다).
  - 쓰는 규칙(묶음 머리에 적음): 글에 있는 내용만, 숫자·물질명·화학식은 글에 나온 그대로, 평가어(최초·최고) 금지, 리뷰·논평은 그렇게 쓴다,
    글이 제목과 다른 논문이면 비운다, 판단 과정을 쓰지 않는다.
  - 검증(apply, 결정적): 요약의 숫자(두 자리 이상·소수)와 화학식·물질 코드(대문자로 시작하고 숫자가 든 토큰)가 재료 글에 있는지 본다.
    없으면 병합하지 않고 '보류' 로 알린다(prep --ids 로 다시). 형식(한 문장·한글·마침표·길이)과 판단 과정 문구도 본다.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sci_index import TLDR_COL, body_excerpt, looks_boilerplate, one_line, read_index, read_registry, write_index  # noqa: E402

ABS_MAX = 1500          # 초록은 앞 1,500자면 한 문장 요약에 충분하다 (묶음 크기·토큰 절감)
MIN_MATERIAL = 300      # 이보다 짧은 본문 앞부분은 재료로 보지 않는다
REVIEW_TYPES = {"review", "editorial", "comment", "commentary", "letter", "erratum", "news", "perspective"}
META_RE = re.compile(r"(제공된|주어진)\s*(초록|본문|정보|글)|초록(은|이|에는|만으로)\s|제목(은|만으로)\s|본문 앞부분|글에 (따르면|없)")
NUM_RE = re.compile(r"\d+(?:\.\d+)?")
FORMULA_RE = re.compile(r"(?<![A-Za-z0-9])[A-Z][A-Za-z]*\d[A-Za-z0-9]*")   # 화학식·물질 코드: Pd3Pb, MgFe2O4, H2O2, CO2 (한글 조사 앞에서 끊긴다)
HANGUL_RE = re.compile(r"[가-힣]")

RULES = [
    "1. 한국어 한 문장, 60~120자(최대 150자), '~했다.'·'~이다.' 로 끝낸다. 이 논문이 무엇을 했고 무엇을 찾았는지(리뷰·논평이면 무엇을 정리·해설했는지)를 쓴다. 제목 번역이 아니다.",
    "2. '글' 에 있는 내용만 쓴다. 배경지식·추측·일반론을 더하지 않는다.",
    "3. 숫자·단위·물질명·화학식·약어는 글에 나온 그대로만 쓴다. 글에 없는 숫자나 화학식은 쓰지 않는다(물질 이름을 화학식으로 바꾸지도 않는다). 확실하지 않으면 숫자를 빼고 쓴다. 스크립트가 숫자·화학식을 글과 대조해 없으면 요약을 버린다.",
    "4. '최초'·'최고'·'획기적' 같은 평가는 글에 그렇게 쓰여 있을 때만 쓴다.",
    "5. 유형이 review·editorial·comment 등이면 자기 연구 결과처럼 쓰지 않는다('~를 정리한 리뷰이다', '~를 소개한 해설이다').",
    "6. 글이 제목과 다른 논문으로 보이면 한줄요약을 비우고 flag 에 '제목-글 불일치'. 글이 너무 짧아 쓸 것이 없으면 비우고 flag 에 '재료 부족'.",
    "7. 한줄요약에는 판단 과정('초록이 부족하다' 등)을 쓰지 않는다. flag 는 문제가 있을 때만 짧게 쓴다.",
    "8. 초록 끝의 '…(뒤 생략)' 은 스크립트가 자른 표시다. 문제 삼지 않는다.",
]


def material(kb_root: Path, r: dict, body: bool = False) -> tuple[str, str]:
    """요약 재료 (종류, 글). 초록이 200자 이상이면 초록, 아니면 본문 앞부분(제목 자리부터), 그것도 없으면 짧은 초록. 없으면 ('', '').
    body=True 면 본문 앞부분 3,000자를 쓴다 — 초록 칸이 배경 문단뿐이라 '재료 부족' 이 난 논평 등 (2026-09-27 PNAS Commentary)."""
    ab = one_line(r.get("초록", ""))
    # 초록만 받은 논문의 source.md 는 본문이 아니라 초록 보관 파일이다 (2026-09-27 Thieme: 사이트 문구가 '본문 앞부분' 으로 들어갔다)
    has_body = not (r.get("원문상태") or "").startswith("초록만")
    if body and has_body:
        src = kb_root / "papers" / r["paper_id"] / "source.md"
        if src.exists():
            ex = body_excerpt(src.read_text(encoding="utf-8", errors="ignore"), n=2 * ABS_MAX, title=r.get("제목", ""))
            if len(ex) >= MIN_MATERIAL:
                return "본문 앞부분", ex
    if len(ab) >= 200:
        return "초록", (ab if len(ab) <= ABS_MAX else ab[:ABS_MAX] + " …(뒤 생략)")
    src = kb_root / "papers" / r["paper_id"] / "source.md"
    if has_body and src.exists():
        ex = body_excerpt(src.read_text(encoding="utf-8", errors="ignore"), n=ABS_MAX, title=r.get("제목", ""))
        if len(ex) >= MIN_MATERIAL and not looks_boilerplate(ex):
            return ("초록+본문 앞부분", f"{ab} / {ex}") if ab else ("본문 앞부분", ex)
    if len(ab) >= 60:
        return "초록(짧음)", ab
    return "", ""


def _num_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").replace("−", "-").replace("–", "-")
    s = re.sub(r"(?<=\d)[,   ](?=\d{3}(?!\d))", "", s)   # 1,000·100 000 → 1000·100000
    return s


NUM_WORDS = {"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
             "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
             "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "dozen": 12, "tenfold": 10, "hundredfold": 100, "thousandfold": 1000}
ONES = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}


def _word_numbers(src: str) -> str:
    """글에 영어 낱말로 쓴 수(ten times, twenty-five, tenfold)를 숫자로도 적어 둔다 — 요약이 '10배' 로 옮긴 것을 지어낸 숫자로 보지 않게
    (2026-09-27 'more than ten times' → '10배' 가 걸렸다)."""
    low = (src or "").lower()
    found = [str(v) for w, v in NUM_WORDS.items() if re.search(rf"\b{w}\b", low)]
    for m in re.finditer(r"\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[- ](one|two|three|four|five|six|seven|eight|nine)\b", low):
        found.append(str(NUM_WORDS[m.group(1)] + ONES[m.group(2)]))
    return " ".join(found)


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", s or "").lower())


def check_tldr(s: str, src: str) -> list[str]:
    """한줄요약 검증. 문제 목록(비었으면 통과). 숫자·화학식이 재료 글에 없으면 할루시네이션으로 본다."""
    probs = []
    if len(s) > 150:
        probs.append(f"길이 {len(s)}자")
    if not HANGUL_RE.search(s):
        probs.append("한글 아님")
    if not s.endswith("."):
        probs.append("마침표로 끝나지 않음")
    if META_RE.search(s):
        probs.append("판단 과정 섞임")
    if src:
        sn = _num_text(src) + " " + _word_numbers(src)
        bad = [n for n in NUM_RE.findall(_num_text(s))
               if ("." in n or len(n) >= 2) and not re.search(rf"(?<![\d.]){re.escape(n)}(?!\d)", sn)]   # 한 자리 정수는 글에서 낱말(two)로도 써서 보지 않는다
        if bad:
            probs.append("글에 없는 숫자 " + ", ".join(dict.fromkeys(bad)))
        sa = _alnum(src)
        badf = [f for f in FORMULA_RE.findall(unicodedata.normalize("NFKC", s)) if _alnum(f) not in sa]
        if badf:
            probs.append("글에 없는 화학식·코드 " + ", ".join(dict.fromkeys(badf)))
    return probs


def cmd_prep(args) -> None:
    kb_root = Path(args.kb_root).resolve()
    rows, _ = read_index(kb_root / "index.csv")
    if not rows:
        print(f"index.csv 가 없습니다. 먼저 색인: python {Path(__file__).with_name('sci_index.py')} build --kb-root {kb_root}"); raise SystemExit(1)
    reg = read_registry(kb_root)
    body_ids = {i.strip() for i in (args.body or [])}
    redo = {i.strip() for i in (args.ids or [])} | body_ids
    unknown = redo - {r["paper_id"] for r in rows}
    if unknown:
        print(f"!! index.csv 에 없는 paper_id: {', '.join(sorted(unknown))}")
    todo = [r for r in rows if (args.all or not r.get(TLDR_COL) or r["paper_id"] in redo)
            and not (r.get("원문상태") or "").startswith("범위밖")]   # 범위 밖으로 둔 논문(같은 논문의 다른 DOI 등)은 요약하지 않는다 (2026-09-27)
    work = kb_root / "_collect"
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("tldr_batch_*.md"):
        old.unlink()
    entries, srcs, none = [], [], []
    for r in todo:
        kind, text = material(kb_root, r, body=r["paper_id"] in body_ids)
        if not text:
            none.append(r["paper_id"]); continue
        dt = (reg.get(r["paper_id"], {}).get("doc_type") or "").lower()
        entries.append((r["paper_id"], f"## {r['paper_id']}\n제목: {r['제목']}\n유형: {dt or '-'}\n글({kind}): {text}\n"))
        srcs.append((r["paper_id"], text))
    if none:
        print(f"재료(초록·본문)가 없어 요약하지 않는 {len(none)}편 — 제목만으로 쓰면 지어내기 쉽다. 논문을 받은 뒤 다시 prep: "
              + ", ".join(none[:6]) + (" …" if len(none) > 6 else ""))
    if not entries:
        print("한줄요약을 쓸 행이 없습니다 (--all 이면 전체 다시, --ids 로 골라서).  ▼・ᴥ・▼"); return
    # 묶음 수는 편수(기본 50)·크기(기본 50KB) 기준 중 큰 쪽, 크기를 고르게 나눈다 (큰 파일은 나눠 읽혀 토큰이 늘고, 작은 묶음은 에이전트 고정 비용이 는다)
    size, max_bytes = max(5, args.size), max(10, args.max_kb) * 1000
    nbytes = [len(e.encode("utf-8")) for _, e in entries]
    n_batch = max(1, -(-sum(nbytes) // max_bytes), -(-len(entries) // size))
    target = sum(nbytes) / n_batch
    batches: list[list[int]] = [[]]
    used = 0
    for i, b in enumerate(nbytes):
        if batches[-1] and len(batches) < n_batch and (used + b / 2 > target or len(batches[-1]) >= size):
            batches.append([]); used = 0
        batches[-1].append(i); used += b
    # 결과 파일(tldr_<n>.jsonl) 번호는 이미 있는 것 다음부터 (병합 전에 prep 을 다시 돌려도 덮어쓰지 않는다)
    start = 1 + max([int(m.group(1)) for g in work.glob("tldr_*.jsonl") if (m := re.fullmatch(r"tldr_(\d+)\.jsonl", g.name))] or [0])
    for bi, idx in enumerate(batches, start):
        out = work / f"tldr_{bi}.jsonl"
        head = [f"# 한줄요약 묶음 {bi} ({bi - start + 1}/{len(batches)}) — {len(idx)}편", "",
                f"결과: `{out}` 에 한 줄에 한 논문씩 JSON 으로 쓴다(Write 한 번): "
                '{"paper_id": "…", "한줄요약": "…", "flag": ""}. 묶음의 모든 논문을 쓴다.', "", "규칙:"] + RULES + [""]
        (work / f"tldr_batch_{bi}.md").write_text("\n".join(head) + "\n" + "\n".join(entries[i][1] for i in idx), encoding="utf-8")
        (work / f"tldr_src_{bi}.json").write_text(json.dumps({srcs[i][0]: srcs[i][1] for i in idx}, ensure_ascii=False), encoding="utf-8")
    sizes = ", ".join(f"{len(b)}편" for b in batches)
    print(f"한줄요약 대상 {len(entries)}편 → 묶음 {len(batches)}개 ({sizes}; 한 묶음 최대 {size}편·{max_bytes // 1000}KB): "
          f"{work / f'tldr_batch_{start}.md'} … tldr_batch_{start + len(batches) - 1}.md")
    how = ("10편 미만 → 메인이 묶음 파일을 한 번 읽고 결과 JSONL 을 한 번 쓴다" if len(entries) < 10
           else "묶음마다 sci-tldr-writer 에이전트 하나(동시에)")
    print(f"쓰기: {how}. 다 되면: python {Path(__file__)} apply --kb-root {kb_root}  ▼・ᴥ・▼")


def read_results(files: list[str]) -> tuple[dict[str, dict], int]:
    """tldr_<n>.jsonl (한 줄 JSON). 번호 순서로 읽어 같은 논문은 나중 것이 이긴다. 형식이 틀린 줄 수도 돌려준다."""
    def num(p: str) -> int:
        m = re.search(r"(\d+)\.jsonl$", p)
        return int(m.group(1)) if m else 0
    res, bad = {}, 0
    for fp in sorted(files, key=num):
        for line in Path(fp).read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                pid = str(o.get("paper_id") or "").strip()
                if not pid:
                    raise ValueError
                res[pid] = {"s": one_line(str(o.get("한줄요약") or o.get("tldr") or "")), "flag": one_line(str(o.get("flag") or ""))}
            except Exception:
                bad += 1
    return res, bad


def cmd_apply(args) -> None:
    kb_root = Path(args.kb_root).resolve()
    out = kb_root / "index.csv"
    rows, _ = read_index(out)
    if not rows:
        print(f"index.csv 가 없습니다: {out}"); raise SystemExit(1)
    work = kb_root / "_collect"
    files = []
    for g in (args.files or [str(work / "tldr_*.jsonl")]):
        files += sorted(glob.glob(g)) or ([g] if Path(g).exists() else [])
    if not files:
        print(f"결과 파일이 없습니다: {' '.join(args.files or [str(work / 'tldr_*.jsonl')])}"); raise SystemExit(1)
    res, bad_lines = read_results(files)
    srcs: dict[str, str] = {}
    for sp in sorted(work.glob("tldr_src_*.json"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))):
        try:
            srcs.update(json.loads(sp.read_text(encoding="utf-8")))
        except Exception:
            pass
    known = {r["paper_id"] for r in rows}
    unknown = sorted(set(res) - known)
    merged, held, empty = 0, {}, {}
    for r in rows:
        g = res.get(r["paper_id"])
        if not g:
            continue
        if not g["s"]:
            # 작성자가 재료 부족·제목-글 불일치로 비웠으면 예전 요약도 지운다 (같거나 더 나쁜 재료로 쓴 것이다)
            empty[r["paper_id"]] = g["flag"] or "비움"
            r[TLDR_COL] = ""
            continue
        probs = check_tldr(g["s"], srcs.get(r["paper_id"], ""))
        if probs:
            held[r["paper_id"]] = "; ".join(probs)
            continue
        r[TLDR_COL] = g["s"]; merged += 1
    write_index(out, rows, True)
    chk = kb_root / "index_check.csv"
    if chk.exists():   # 한줄요약 쪽 판단은 'LLM:' 로 붙인다 (논문마다 가장 나중 결과로 바꾼다, build 를 다시 해도 남는다)
        with open(chk, encoding="utf-8-sig", newline="") as f:
            checks = list(csv.DictReader(f))
        for c in checks:
            pid = c["paper_id"]
            if pid not in res:
                continue
            note = ("한줄요약 보류: " + held[pid]) if pid in held else ("한줄요약 없음: " + empty[pid]) if pid in empty else res[pid]["flag"]
            det = c["flags"].split("LLM:", 1)[0].strip().rstrip(";").strip()
            c["flags"] = "; ".join(x for x in [det, "LLM: " + note if note else ""] if x)
            c["n_flags"] = str(len([x for x in c["flags"].split(";") if x.strip()]))
        with open(chk, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["paper_id", "flags", "n_flags"]); w.writeheader(); w.writerows(checks)
    left = sum(1 for r in rows if not r.get(TLDR_COL))
    print(f"한줄요약 병합 {merged}건 (결과 파일 {len(files)}개) → {out}")
    if held:
        print(f"!! 보류 {len(held)}건 — 글과 맞지 않아 넣지 않음 (한 번 더: prep --ids {' '.join(list(held)[:10])})")
        for pid, why in list(held.items())[:10]:
            print(f"   {pid}: {why}")
    if empty:
        print(f"비운 {len(empty)}건 (재료 부족·제목-글 불일치 등): " + "; ".join(f"{k}({v})" for k, v in list(empty.items())[:8]))
    if unknown:
        print(f"!! index.csv 에 없는 paper_id {len(unknown)}개는 건너뜀: {', '.join(unknown[:8])}")
    if bad_lines:
        print(f"!! 형식이 틀린 줄 {bad_lines}개는 건너뜀 (JSON 한 줄에 한 논문)")
    print(f"한줄요약 {len(rows) - left}/{len(rows)}  ▼・ᴥ・▼")


def main() -> None:
    ap = argparse.ArgumentParser(description="sci_tldr — 한국어 한 줄 요약 (index.csv 한줄요약 열)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep"); p.add_argument("--kb-root", required=True)
    p.add_argument("--ids", nargs="*", help="요약이 있어도 다시 쓸 paper_id (보류된 것, 다시 받은 논문 등)")
    p.add_argument("--all", action="store_true", help="모든 행 다시")
    p.add_argument("--body", nargs="*", help="본문 앞부분 3,000자를 재료로 다시 쓸 paper_id ('재료 부족' 으로 비었는데 본문이 있는 논문)")
    p.add_argument("--size", type=int, default=50, help="묶음당 최대 편수")
    p.add_argument("--max-kb", type=int, default=50, help="묶음 파일 최대 크기(KB)")
    p = sub.add_parser("apply"); p.add_argument("--kb-root", required=True)
    p.add_argument("--files", nargs="*", help="결과 JSONL (기본 _collect/tldr_*.jsonl, 와일드카드 가능)")
    args = ap.parse_args()
    {"prep": cmd_prep, "apply": cmd_apply}[args.cmd](args)


if __name__ == "__main__":
    main()
