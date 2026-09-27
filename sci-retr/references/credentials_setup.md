# Credentials Setup — 환경변수 + .env 설정 가이드

> **현행 (2026-09-27)**: sci_collect 의 키·토큰은 skill 폴더의 `token.txt` 에 둔다. `python scripts/sci_collect.py token` 이 빈 양식을 만들고 있음/없음만 보여 준다. 값은 사용자가 파일에 직접 넣고 채팅창에는 적지 않는다(SKILL.md 3.2.1). 아래의 `.env`·`--env-path` 설명은 2026-09-27 에 패키지에서 뺀 옛 배치 스크립트용이다. sci_collect 는 논문 폴더의 `.env`(다른 파일이면 `--env <경로>`)도 함께 읽는다.

이 skill은 publisher API token이 필요한 method (Wiley TDM, Elsevier API, Semantic Scholar 등) 를 사용한다. token은 사용자 본인이 직접 발급받아 환경변수 또는 `.env` 파일에 설정해야 한다.

⚠️ **이 skill의 scripts에는 어떤 token도 hardcode 되어 있지 않다**. 사용자별로 자기 계정 token을 발급받아 사용해야 한다.

---

## 0. 권장 패턴

KB root 폴더 안에 `.env` 파일 두기:
```
{kb_root}/.env
```

scripts는 `--env-path <path>` 인자로 위치 지정. default는 `<kb-root>/.env`.

또는 shell 환경변수로 직접 설정 (e.g., PowerShell `$env:ELSEVIER_API_KEY="..."`).

---

## 1. .env 파일 형식

```bash
# Wiley Online Library TDM API
# 발급: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
WILEY_TDM_TOKEN=
# wiley-tdm Python package alias (동일 값)
TDM_API_TOKEN=

# Elsevier Article Retrieval API
# 발급: https://dev.elsevier.com/apikey/manage
ELSEVIER_API_KEY=

# (선택) Elsevier Institutional Token — paywalled fulltext API access
# 발급: 본인 소속 도서관 사서에게 요청 → Elsevier
ELSEVIER_INSTTOKEN=

# Unpaywall API — OA paper 검색용
# 발급: 이메일만 등록 (no key required)
UNPAYWALL_EMAIL=

# Semantic Scholar Graph API
# 발급: https://www.semanticscholar.org/product/api → "Request API Key"
SEMANTIC_SCHOLAR_API_KEY=

# (선택) OpenAI / Anthropic — Phase 2 debate 또는 LLM extraction 단계용
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

⚠️ **`.env`는 반드시 `.gitignore` 처리 후 사용**. token 노출 시 즉시 publisher 사이트에서 revoke + 재발급.

---

## 2. token별 발급 절차

### 2.1 Wiley TDM Token

1. https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining 접속
2. "Request a Token" 또는 "TDM Client Token" 신청
3. 본인 institution email 입력 (academic email 권장)
4. 1-3 영업일 후 token 메일 수신
5. `.env`의 `WILEY_TDM_TOKEN` 과 `TDM_API_TOKEN` 양쪽에 동일 값 설정 (alias)

**용도**: Wiley paper (10.1002 prefix) PDF 자동 다운.

**검증**: 2/2 sample 성공. `wiley-tdm` Python package 사용.

---

### 2.2 Elsevier API Key

1. https://dev.elsevier.com/apikey/manage 접속 (Elsevier 계정 필요)
2. "Create new API key" 클릭
3. project description (예: "Domain-specific KB construction at KIST")
4. 즉시 발급 (free tier)
5. `.env`의 `ELSEVIER_API_KEY` 설정

**용도**: Elsevier Article Retrieval API (10.1016, 10.1006). Free key는 abstract + 일부 OA paper. paywalled은 INSTTOKEN 필요.

**검증**: free key만으로 184편 중 51편 회복. 나머지 133편은 article HTML 우회법으로 회복.

---

### 2.3 Elsevier Institutional Token (선택)

**중요**: 이 token이 있으면 paywalled fulltext API access. 없으면 article HTML 우회법으로 fallback.

1. 소속 도서관 사서에게 요청 메일:
   ```
   Elsevier ScienceDirect TDM API 사용을 위한
   Institutional Token 발급을 요청드립니다.
   
   목적: 도메인 특화 KB 구축을 위한 paywalled paper의 fulltext API access.
   환경: KIST 구독 paper 범위 안에서 사용.
   ```
2. 사서가 Elsevier에 신청 → 1-3일 후 token 발급
3. `.env`의 `ELSEVIER_INSTTOKEN` 설정

**효과**: API 호출 시 `X-ELS-APIKey` + `X-ELS-Insttoken` 두 헤더 → fulltext API 풀림. paywalled paper 70-90% 회복 추정.

**검증**: 미설정 상태로도 article HTML 우회법(B.4)으로 ScienceDirect paper 90%+ 회복 가능. INSTTOKEN은 안전 보강용.

---

### 2.4 Unpaywall

1. https://unpaywall.org/products/api 접속
2. 이메일만 등록 (no key 필요, 무제한 free)
3. `.env`의 `UNPAYWALL_EMAIL` 에 본인 이메일 입력

**용도**: OA paper 회복용. 단 Elsevier paper에 OA copy 거의 없음 (검증 결과 0건).

---

### 2.5 Semantic Scholar API Key

1. https://www.semanticscholar.org/product/api 접속
2. "Request API Key" 클릭
3. form 작성:
   - First/Last name
   - Email (academic 권장)
   - Affiliation (예: "Korea Institute of Science and Technology")
   - Application use: **Public (Free / Nonprofit)** 권장 (academic/research)
   - Endpoints (다음 답안 권장):
     ```
     Paper Details (/graph/v1/paper/{paper_id}) — DOI lookup for openAccessPdf retrieval and metadata enrichment;
     Paper Batch (/graph/v1/paper/batch) — bulk DOI lookup;
     Paper Search (/graph/v1/paper/search) — title/keyword fallback.
     ```
   - Daily requests: "10 to 100" (대부분 use case에 충분)
   - "How do you plan to use" (50 word 이상):
     ```
     We are constructing a domain-specific knowledge base on [domain] at [institution].
     The pipeline collects DOI-anchored full-text papers, extracts quantitative and
     qualitative metadata, and structures them for LLM-mediated debate and evidence
     retrieval. Semantic Scholar API will be used to (1) look up open-access PDF
     locations via /graph/v1/paper/{paper_id}, (2) batch-resolve DOIs for ~150-500
     papers per domain via /graph/v1/paper/batch, and (3) fall back to
     /graph/v1/paper/search when DOI metadata is incomplete. We will respect rate
     limits with exponential backoff and cache responses locally to minimize repeated
     requests.
     ```
4. 1-7 영업일 후 key 메일 수신
5. `.env`의 `SEMANTIC_SCHOLAR_API_KEY` 설정

**용도**: OA paper 보강 검색 (Unpaywall 미커버 영역). 단 Elsevier paper에 OA copy 적음 (검증 결과 1/10 OA URL).

---

## 3. 환경변수 검증

skill 스크립트 실행 전 확인:

```powershell
# PowerShell
$env:WILEY_TDM_TOKEN; $env:ELSEVIER_API_KEY; $env:UNPAYWALL_EMAIL
```

또는 .env 직접 확인:

```bash
grep -c "^ELSEVIER_API_KEY=" .env
```

값이 비어있으면 해당 publisher method skip 또는 fallback 사용됨.

---

## 4. 보안 주의

- `.env` **절대 git에 commit 금지**. `.gitignore` 추가:
  ```gitignore
  .env
  *.env
  ```
- token 값을 다른 메모리, 코드 주석, 로그, 다른 사람과 공유 금지.
- token 노출 의심 시 즉시 publisher 사이트에서 revoke + 재발급.
- token은 본인 institution 계정으로 발급된 것 — 비정상 사용 시 추적 가능.
- 다른 사람이 이 skill을 쓸 때 본인 token으로 새로 발급받아야 한다.

---

## 5. token 없이 사용 가능한 publisher

다음 publisher는 token 없이 자동 처리됨 (A 그룹):
- RSC (10.1039)
- MDPI (10.3390)
- Springer (10.1007 / 10.1023)
- Thieme (10.1055)
- Pharm Soc Japan / J-STAGE (10.1248)
- Pleiades RU (10.1134)
- Tsinghua OAE (10.20964 / 10.26599)

token 발급받기 전이라도 위 publisher들의 paper는 즉시 batch 가능. token은 Wiley + Elsevier + ACS + Science 같이 paywalled publisher 처리 시 필요.

---

## 6. 환경변수 priority

scripts는 다음 순서로 token 검색:
1. shell 환경변수 (`os.environ`)
2. `--env-path` 로 지정한 .env 파일
3. default `<kb-root>/.env`
4. 없으면 해당 publisher method skip + warning log
