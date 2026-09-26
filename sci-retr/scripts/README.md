# sci-retr scripts/

> **옛 배치 스크립트 설명이다.** 새 작업은 `sci_collect.py` 만 쓴다(SKILL.md). runner.py 는 판정·검증 함수를 제공하는 라이브러리로만 남아 있고, 아래의 `playwright install chromium` 은 옛 도구 창 방식에만 필요해 지금은 하지 않아도 된다. 환경 점검은 `python sci_collect.py doctor --kb-root <root>`.

논문 fulltext batch 수집 파이프라인. 5개 script를 순서대로 실행하여
body_absent 논문의 PDF/HTML를 자동 수집하고, 실패 항목을 분류 및 수동 ingest.

## 전제 조건

```
pip install requests playwright pymupdf wiley-tdm truststore beautifulsoup4 lxml
# truststore: KIST 망 TLS 재서명 환경에서 OS 인증서 저장소 사용. beautifulsoup4+lxml: sci_collect.py HTML 본문 컨테이너 추출.
# (curl_cffi 는 2026-09-24 '봇 탐지 우회 금지' 정책으로 제거 — SKILL.md 원칙 0)
playwright install chromium
```

## 환경변수 / .env

`.env` 파일 (기본 위치: `<kb_root>/.env`) 또는 환경변수로 설정:

| 변수 | 용도 |
|---|---|
| `KB_ROOT` | KB 최상위 경로 (`--kb-root` 대체) |
| `ELSEVIER_API_KEY` | Elsevier Article Retrieval API 키 |
| `WILEY_TDM_TOKEN` | Wiley Text and Data Mining API 토큰 (TDM_API_TOKEN으로도 자동 매핑) |
| `SEMANTIC_SCHOLAR_KEY` | Semantic Scholar API 키 (직접 사용 script 아님, 참고용) |
| `AGENT_NAME` | runner.py의 작업자 이름 (`--agent` 대체) |
| `CHROME_EXE` | Chrome 실행 경로 (`--chrome-exe` 대체) |

**credentials는 절대 script에 hardcode 금지. .env 또는 환경변수로만.**

## 공통 인자 (모든 script)

| 인자 | 기본값 | 설명 |
|---|---|---|
| `--kb-root` | `$KB_ROOT` | KB 최상위 경로 |
| `--batch-name` | `batch_<utc_yyyymmdd>` | work_root 하위 폴더명 |
| `--work-dir` | `<kb_root>/pdf_download_tests/<batch_name>` | 직접 work 경로 (--batch-name 무시) |
| `--env-path` | `<kb_root>/.env` | .env 파일 위치 |

## 디렉터리 구조

```
<kb_root>/
  papers/
    <paper_id>/
      source.md          # 수집된 fulltext (YAML frontmatter + 본문)
      source.json        # 메타데이터
      source_origin.txt  # 수집 이력 append 로그
      pdf/               # PDF 원본
      html/              # HTML 원본
      figures/
        pdf_pages/       # PDF 페이지별 PNG
        pdf_extracted/   # PDF 임베디드 이미지
        html_figures/    # HTML figure 이미지
  pdf_download_tests/
    <batch_name>/
      assignment_codex.csv
      assignment_claude.csv
      assignment_summary.md
      download_log_<agent>.csv
      failures_<agent>.csv
      failures_classified.csv
      failures_summary.md
      ingest_log.csv
      manual_pdf_dropbox/
        <paper_id>/
          request.json   # queued_by runner 자동 생성
          <paper_id>.pdf # 사용자 수동 drop
```

---

## 1. split_assignment.py

body_absent 논문 CSV를 agent(codex/claude)별 assignment CSV로 분할.

### 기본 사용

```bash
python split_assignment.py \
  --kb-root D:\repo\llm-debate-echem-ai\phase1_e_epoxidation_kb \
  --batch-name v02_590batch_20260429
```

### 전체 옵션

```
--kb-root       KB 최상위 경로
--batch-name    작업 폴더명
--work-dir      직접 work 경로 (--batch-name 무시)
--env-path      .env 경로
--input-csv     입력 CSV (기본: kb_root/reports/fulltext_coverage_audit/02_papers_body_absent.csv)
```

### 출력

- `assignment_codex.csv` — Codex 담당 paper 목록
- `assignment_claude.csv` — Claude 담당 paper 목록
- `assignment_summary.md` — publisher별 분담 통계

### 분담 정책

| publisher | 정책 |
|---|---|
| acs, wiley | Codex 전담 (Playwright 환경) |
| world_scientific, csj_chem_lett, pharm_soc_japan | Claude 전담 (Cloudflare/J-STAGE) |
| 그 외 | 절반 분배 (paper_id 알파벳 sort) |

---

## 2. runner.py

Assignment CSV를 읽어 publisher별 자동 수집 method를 순차 시도.

### 기본 사용

```bash
# dry-run (각 publisher 첫 1편씩 테스트)
python runner.py \
  --kb-root <path> --batch-name <name> \
  --agent claude --dry-run

# 전체 실행
python runner.py \
  --kb-root <path> --batch-name <name> \
  --agent claude --all

# 특정 paper 지정
python runner.py \
  --kb-root <path> --batch-name <name> \
  --agent claude --paper-id P001 --paper-id P002
```

### 전체 옵션

```
--kb-root       KB 최상위 경로
--batch-name    작업 폴더명
--work-dir      직접 work 경로
--env-path      .env 경로
--agent         작업자 이름 (claude/codex, 환경변수 AGENT_NAME)
--chrome-exe    Chrome 실행 경로 (환경변수 CHROME_EXE)
--dry-run       dry-run 샘플 실행
--all           전체 assignment 실행
--paper-id ID   특정 paper 지정 (반복 가능)
--limit N       처리 수 제한
--sleep S       paper 간 대기 초 (기본 0.75)
--keep-logs     기존 로그 archive 건너뜀
```

### Publisher별 수집 method

| publisher | method 순서 |
|---|---|
| elsevier | API(PDF+XML) → ScienceDirect direct → browser |
| rsc | landing HTML → articlepdf URL |
| acs | HTML → browser session PDF |
| wiley | TDM API → HTML → direct → browser |
| springer | HTML → content/pdf URL |
| mdpi | direct PDF URL → HTML |
| ecs | IOP direct PDF → HTML |
| 기타 | HTML → landing PDF 후보 |

### 자동 실패 시 manual queue

MANUAL_QUEUE_PUBLISHERS (world_scientific, csj_chem_lett, pharm_soc_japan, thieme, other_small, unknown, tsinghua_oae, ecs, royal_society, pleiades_springer_ru)는 자동 method 모두 실패 시 `manual_pdf_dropbox/{paper_id}/request.json`으로 등록.

---

## 3. elsevier_html_retry_safe.py

Elsevier ScienceDirect 논문을 브라우저(Playwright)로 article HTML 수집.
rate-limit 감지 시 즉시 중단, chunk 단위 진행 + chunk 간 대기 지원.

### 기본 사용

```bash
python elsevier_html_retry_safe.py \
  --kb-root <path> --batch-name <name> \
  --chunk-start 0 --chunk-size 15 --total-chunks 3
```

### 전체 옵션

```
--kb-root           KB 최상위 경로
--batch-name        작업 폴더명
--work-dir          직접 work 경로
--env-path          .env 경로
--pending-csv       입력 CSV (기본: work_dir/elsevier_retry_pending.csv)
--log-csv           로그 CSV (기본: work_dir/elsevier_html_retry_log.csv)
--profile-name      Chrome 프로필 폴더명 (기본: kistsso)
--chrome-exe        Chrome 실행 경로
--chunk-start N     시작 paper 인덱스
--chunk-size N      chunk 크기 (기본 15, 권장)
--total-chunks N    연속 진행할 chunk 수 (기본 1)
--chunk-wait S      chunk 간 sleep 초 (기본 1800 = 30분)
--paper-interval S  paper 간 sleep 초 (기본 90, rate-limit 방지)
--paper-wait S      page load 후 대기 초 (기본 8)
--paper-wait-old S  2010년 이전 논문 대기 초 (기본 12)
--no-warmup         ScienceDirect warmup 건너뜀
--no-priority       year 우선순위 정렬 건너뜀
--skip-done         이미 success 기록된 paper skip (기본 True)
```

### rate-limit 안전 정책

- paper_interval=90s (Codex의 13s/paper 패턴이 rate-limit 트리거됨)
- problem page (rate-limit 감지) 시 즉시 중단
- chunk 간 1800s(30분) 대기
- 기관 IP 접속 필요 (KIST ePrism 또는 핫스팟 우회)

---

## 4. failure_classifier.py

batch 실패 항목(failures_*.csv)을 카테고리별로 분류.

### 기본 사용

```bash
# 양쪽 합산 (codex + claude)
python failure_classifier.py \
  --kb-root <path> --batch-name <name>

# claude만
python failure_classifier.py \
  --kb-root <path> --batch-name <name> --claude-only

# 직접 경로 지정
python failure_classifier.py \
  --input D:\repo\...\v02_590batch_20260429
```

### 전체 옵션

```
--kb-root       KB 최상위 경로
--batch-name    작업 폴더명
--work-dir      직접 work 경로
--env-path      .env 경로
--input DIR     입력 배치 디렉터리 (--work-dir 하위 호환)
--codex-only    failures_codex.csv만 처리
--claude-only   failures_claude.csv만 처리
--output-csv    분류 결과 CSV 경로
--output-md     요약 마크다운 경로
```

### 출력

- `failures_classified.csv` — category 컬럼 추가된 전체 실패 목록
- `failures_summary.md` — 카테고리/publisher/agent별 통계 + 추천 조치

### 분류 카테고리

| 카테고리 | 추천 조치 |
|---|---|
| elsevier_partial_pdf | manual_pdf_dropbox (institutional token 또는 수동 PDF) |
| elsevier_sciencedirect_403 | ScienceDirect Playwright sign-in |
| metadata_mismatch | metadata 보강 후 재시도 |
| access_wall | manual_pdf_dropbox + 권한 보강 |
| cloudflare_or_js_landing | manual_pdf_dropbox (자동 우회 어려움) |
| oup_abstract_redirect | manual_pdf_dropbox 또는 OUP TDM |
| short_content_no_structure | 수동 review (옛 short letter 가능성) |
| pdf_endpoint_404 | PII/DOI 정규화 재시도 |
| pdf_endpoint_other_failure | publisher 재확인 후 retry |
| unknown_other | 수동 review |

---

## 5. manual_ingest.py

`manual_pdf_dropbox/{paper_id}/` 에 수동으로 drop된 PDF를 검증 후
`papers/{paper_id}/` 표준 폴더로 promote.

### 기본 사용

```bash
# 전체 스캔
python manual_ingest.py \
  --kb-root <path> --batch-name <name> --all

# 특정 paper
python manual_ingest.py \
  --kb-root <path> --batch-name <name> \
  --paper-id P001 --paper-id P002

# dry-run (PDF 발견 여부만 확인)
python manual_ingest.py \
  --kb-root <path> --batch-name <name> --all --dry-run
```

### 전체 옵션

```
--kb-root       KB 최상위 경로
--batch-name    작업 폴더명
--work-dir      직접 work 경로
--env-path      .env 경로
--paper-id ID   특정 paper_id만 처리 (반복 가능)
--all           manual_pdf_dropbox 전체 스캔
--dry-run       PDF 발견 여부만 출력 (실제 처리 없음)
--keep-logs     기존 ingest_log.csv archive 건너뜀
```

### 처리 흐름

1. `manual_pdf_dropbox/<paper_id>/request.json` 읽기
2. `<paper_id>.pdf` 탐색 (없으면 첫 번째 .pdf)
3. PDF magic bytes 검증 (`%PDF-`)
4. `write_pdf_source()` → content 검증 + papers/ promote
5. 성공 시 `request.json` status="ingested" 갱신
6. 실패 시 status="ingest_failed" + reason 기록

---

## 전체 실행 예시

```bash
KB=D:\repo\llm-debate-echem-ai\phase1_e_epoxidation_kb
BATCH=v02_590batch_20260429

# 1. assignment 분할
python split_assignment.py --kb-root $KB --batch-name $BATCH

# 2. claude dry-run 검증
python runner.py --kb-root $KB --batch-name $BATCH --agent claude --dry-run

# 3. claude 전체 실행
python runner.py --kb-root $KB --batch-name $BATCH --agent claude --all

# 4. Elsevier HTML retry (KIST IP 필요)
python elsevier_html_retry_safe.py --kb-root $KB --batch-name $BATCH \
  --chunk-start 0 --chunk-size 15 --total-chunks 3

# 5. 실패 분류
python failure_classifier.py --kb-root $KB --batch-name $BATCH

# 6. 수동 drop된 PDF ingest
python manual_ingest.py --kb-root $KB --batch-name $BATCH --all
```
