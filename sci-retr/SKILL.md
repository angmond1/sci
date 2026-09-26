---
name: sci-retr
description: Sci Retriever(sci-retr) — DOI 목록이나 WoS·Scopus 검색 결과를 받아 논문 본문 PDF, 본문 텍스트, SI 를 수집하는 도구. 공식 API·직접 PDF 가 되는 곳(Elsevier OA, 토큰 있는 Wiley, Springer, MDPI, Nature)은 자동으로, 자동 요청을 막는 곳(Elsevier 구독 논문, 토큰 없는 Wiley, ACS, RSC, Science, ECS/IOP)은 사용자가 평소 쓰는 Chrome 에서 받아 정리한다. 수집 전에 저장 폴더를 확인하고, 수집 뒤 30편이 넘으면 sci-index 색인 여부를 묻는다. "논문 받아줘", "DOI 수집", "원문 다운로드", "SI 저장", "이 논문들 모아줘" 에 사용.
---

# sci-retr (Sci Retriever) — 논문 원문 수집 지침서

리트리버가 논문을 물어 온다는 뜻의 이름이다. 짝 스킬 `sci-index` 는 수집이 끝난 뒤 사용자가 원하면 이 지침이 이어서 부른다(5.7).

> 🐶 **리트리버 인사(정체성)**: 대화에서 이 skill 을 처음 시작할 때 첫 줄은 *"안녕하세요 🐶 sci-retr 가 논문을 물어 올게요."* 한 줄, 그 다음부터는 평소 문체. 작업 보고의 첫 줄은 머리표로 시작한다: `🐶 완료 — sci-retr`(다 받음. 사용자 차례가 남으면 괄호로 적는다, 예: `🐶 완료 — sci-retr (웹 다운로드 6편은 사용자 차례)`) / `🐕 부분 완료 — sci-retr`(일부만, 예: 18편 중 15편) / `🐕‍🦺 중단 — sci-retr`(막혀서 멈추고 사용자를 기다림: 교내 망 밖·확인 창 반복·연결 끊김). 이모지는 🐶 🐕 🐕‍🦺 세 개만 쓰고, 대부분은 🐶 이다. 받은 파일·파일 이름·`index.csv`·`source.md`·오류 문구에는 넣지 않는다.

## 1. 무엇을 하는가

- 입력은 DOI 목록이다. 출력은 `papers/{paper_id}/` 폴더마다 본문 PDF(필수), SI 파일, 본문 텍스트(`source.md`), 메타(`source.json`)와 전체 목록 `collection_registry.csv` 다.
- 수집은 두 경로다.
  - **자동 경로**: LLM 없이 도는 CLI `scripts/sci_collect.py` 가 공식 API(Elsevier OA 논문, Wiley TDM)와 직접 PDF(Springer, MDPI, Nature)로 받는다. Elsevier API 는 OA 논문에만 쓴다.
  - **웹 경로**: 자동 요청을 막는 출판사는 사용자가 평소 쓰는 Chrome 에서 받는다. Claude 가 Claude in Chrome 확장으로 논문 페이지를 열어 PDF·SI 를 받고, `intake` 명령이 다운로드 폴더의 파일을 논문 폴더로 정리한다.
- Claude 가 하는 일: 수집 범위 판단(사전 분류), review 논문의 인용 follow-up 선별, 웹 경로 수집, 사용자와의 확인.
- 짝이 되는 skill 은 `sci-index` 다. 수집이 끝나면 편수에 따라 색인 여부를 묻거나 생략을 알린다(5.7).
- 하위 에이전트가 필요한 LLM 작업(사전 분류, 색인 검수)은 sonnet 으로 돌린다.

## 2. 원칙

1. **봇 탐지 우회 금지.** 출판사 확인 창(Cloudflare, Radware 등)은 사용자가 직접 누른다. Claude 도 누르지 않는다. 확인 통과 쿠키 복사, 자동화 브라우저 표시 숨김, User-Agent 위장, TLS 지문 흉내, 확인 응답 가로채기, 타 기관 IP 헤더는 쓰지 않는다. 차단되지 않는 가장 빠른 간격을 찾는 시험도 하지 않는다. 이유: 출판사 약관 위반이고, 같은 IP 대역을 쓰는 KIST 전체가 차단될 수 있다.
2. **막히는 곳에는 자동 요청을 보내지 않는다.** ACS·RSC·Science·ECS/IOP, 토큰 없는 Wiley, OA 가 아닌 Elsevier 구독 논문은 자동 단계에서 요청하지 않고 바로 웹 경로로 넘긴다. 그 밖의 출판사도 확인 페이지나 403 이 한 번 나오면 나머지 논문은 요청 없이 웹 경로로 넘긴다(도구가 자동으로 처리).
3. **Elsevier API 는 OA 논문에만 쓴다.** OA 가 아닌 구독 논문에는 API 를 호출하지 않는다. 기관 토큰이 없어 첫 페이지만 오기 때문이다.
4. **자격증명은 `.env` 로만.** 스크립트나 지침에 값을 적지 않고, 채팅에 값을 출력하지 않는다.
5. **사용자에게 묻는 것은 여섯 가지뿐.** 저장 폴더 확인(5.0), 수집 범위 확인, review 인용 follow-up 여부, 웹 경로로 받을 파일 목록 확인(묶음당 한 번), 확인 창 클릭 요청, 색인 여부(30편을 넘을 때, 5.7). 옵션 이름이나 내부 상태값은 말하지 않고 자연어로 설명한다.
6. **미구독 출판사는 초록만 저장**하고 그 사실을 사용자에게 알린다.
7. **양과 간격.** 자동 경로는 설정 간격(3.3)을 지킨다. 웹 경로는 같은 출판사 안에서 한 편씩 받고, 한 편이 끝나면 기다리지 않고 바로 다음 논문으로 간다(2026-09-25 사용자 지시로 30초 간격 폐지). 한 편에 보통 30초~1분이 걸린다. 출판사당 한 번에 수십 편 이내로 나눈다. 수백 편 이상이 필요하면 도서관을 통해 출판사의 텍스트 마이닝 이용을 정식으로 요청하도록 안내한다. 차단 문구가 보이면 그 사이트는 즉시 멈추고 30분 뒤 다시 한다.
8. **몇 편을 수집·읽을지 강제하지 않는다.** 사용자의 목록이 기준이고, follow-up 은 제안만 한다.
9. **개인 연구 자료나 특정 논문의 수치를 지침에 넣지 않는다.** 예시는 "예시" 로 표시한다.

## 3. 준비

### 3.0 처음 한 번 (순서대로)

1. **교내 망**에서 실행한다. 구독 논문은 KIST IP 로 열린다. 밖에서는 자동 경로와 웹 경로 모두 구독 논문을 받지 못한다.
2. **Python 과 패키지**를 설치한다(3.1). 저장소의 설치 스크립트(`install.ps1`, `install.sh`)가 Python 3.11 이상과 Google Chrome 이 없으면 winget(macOS 는 Homebrew)으로 설치하고, 패키지를 넣고, 점검까지 한다.
3. **Chrome 설정 두 가지**를 맞춘다(3.1): "PDF 다운로드", 저장 위치 확인 끄기.
4. **Claude in Chrome 확장**을 Chrome 에 설치하고 Claude 계정으로 로그인한다. 같은 계정으로 확장을 켠 다른 컴퓨터가 있으면 그 Chrome 도 목록에 나온다. Claude 는 이 컴퓨터의 것(`onThisComputer`)만 쓰고, 이 컴퓨터 것이 둘 이상이면 사용자에게 묻는다.
5. **점검 명령**을 돌려 "문제 0" 을 확인한다. 읽기만 하고 아무것도 바꾸지 않는다.
6. **키·토큰**은 선택이다(3.2). 없어도 된다.

```bash
python scripts/sci_collect.py doctor --kb-root <root>
```

- 점검 항목: Python 버전, 패키지, Chrome 의 PDF 설정과 저장 위치 확인 설정, intake 가 볼 다운로드 폴더, `.env` 의 키 유무(값은 보이지 않음), 설정 파일, 목록 편수, 인터넷과 인증서.
- 확인하지 못하는 것: 확장 연결(Claude 가 대화에서 확인), 교내 망 여부(구독 논문 페이지가 열리는지로 확인).

### 3.1 소프트웨어

- Python 3.11 이상과 패키지: `pip install requests playwright pymupdf wiley-tdm truststore beautifulsoup4 lxml openpyxl`
- Google Chrome. 기본 경로가 아니면 환경변수 `CHROME_EXE` 에 실행 파일 경로를 둔다. 기본 설정에서는 자동 단계가 브라우저를 띄우지 않는다. 웹 전용 출판사를 설정 목록에서 뺐을 때만 창 없는 시도에 쓴다.
- **웹 경로용**: 사용자 Chrome 에 Claude in Chrome 확장이 연결되어 있어야 한다. 그리고 Chrome 설정 두 가지를 맞춘다(사용자가 직접 바꾼다. `doctor` 가 읽어서 알려 준다).
  - `chrome://settings/content/pdfDocuments` 의 기본 동작을 "PDF 다운로드" 로 둔다. 그래야 PDF 가 저장 창 없이 다운로드 폴더로 바로 저장된다. Chrome PDF 보기 화면의 다운로드 버튼은 설정과 관계없이 항상 저장 창을 띄우므로 쓰지 않는다. 수집이 끝나면 되돌려도 된다.
  - `chrome://settings/downloads` 의 "다운로드 전에 각 파일의 저장 위치 확인" 을 끈다. 켜져 있으면 파일마다 저장 창이 떠서 웹 경로가 멈춘다.
  - 다운로드 폴더는 바꾸지 않아도 된다. `intake` 가 Chrome 설정과 Windows 의 다운로드 폴더 위치(OneDrive 로 옮긴 경우 포함)를 읽어 찾는다. 다른 곳이면 `--downloads` 나 설정 `downloads_dir`.
  - 영어 Chrome 에서는 PDF 를 열 때 뜨는 "열기" 버튼이 "Open" 이다. 위치는 같다.
- 시작 전에 3.0 의 `doctor` 로 확인한다. `ModuleNotFoundError` 가 나면 다른 인터프리터(`py -3.12`, `python3.12` 등)로 같은 명령을 다시 시도해 되는 것을 쓴다. macOS·Linux 에서 설치 스크립트가 가상환경을 만들었으면 `~/.sci-retr/venv/bin/python` 이다. 패키지만 빠르게 볼 때는 다음 한 줄.

```bash
python -c "import requests, pymupdf, bs4, lxml, truststore, openpyxl; print('ok')"
```

### 3.2 자격증명 (`<root>/.env`, 선택)

| 변수 | 있으면 | 없으면 |
|---|---|---|
| `ELSEVIER_API_KEY` | Elsevier OA 논문의 본문 XML 과 PDF 를 API 로 바로 빠르게 받는다. 논문 사이 3초. 구독 논문(OA 아님)에는 쓰지 않는다 | Elsevier 는 OA 논문까지 모두 웹 경로 |
| `WILEY_TDM_TOKEN` | Wiley PDF 를 TDM API 로 자동으로 받는다 | Wiley 는 모두 웹 경로 (자동 요청을 보내지 않는다) |

발급 방법은 `references/credentials_setup.md`. `--env <경로>` 로 다른 위치를 줄 수 있다.

#### 3.2.1 첫 사용 안내 (키·토큰이 없을 때 한 번만)

처음 쓰는 사용자(`.env` 에 위 변수가 없을 때)에게 한 번만 안내하고 선택을 받는다. 확인은 `.env` 의 해당 줄만 Grep 하고, 값은 읽어도 출력하지 않는다.

- Wiley: "Wiley 논문을 자동으로 받으려면 Text and Data Mining 토큰이 필요합니다. 기관 구독이 있으면 무료이고, 이 페이지에서 발급받아 `.env` 의 `WILEY_TDM_TOKEN` 에 넣으면 됩니다: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining . 토큰이 없으면 Wiley 논문은 평소 쓰시는 Chrome 에서 받아야 합니다."
- Elsevier: "Elsevier 의 Open Access 논문은 API 키가 있으면 바로 빠르게 받을 수 있습니다. 키는 Elsevier 개발자 사이트에서 무료로 몇 분이면 발급됩니다: https://dev.elsevier.com/ . 받은 키는 `.env` 의 `ELSEVIER_API_KEY` 에 넣으면 됩니다. OA 가 아닌 구독 논문은 키가 있어도 API 로 받을 수 없어서 평소 쓰시는 Chrome 에서 받습니다."
- Elsevier API 속도: 공식 한도는 키 하나당 초당 10회, 한 주 5만 회이다(https://dev.elsevier.com/api_key_settings.html, 2026-09-25 확인). 도구는 논문 한 편에 두 번(XML, PDF, 사이 1초) 요청하고 논문 사이 3초를 둔다. 한도를 넘으면 Elsevier 가 429 응답을 주고, 도구는 그 자리에서 멈춘 뒤 남은 논문을 다음 collect 로 미룬다.
- 없이 진행하기로 하면 `.env` 에 빈 값과 주석 `# 없음 (날짜)` 을 적어 두고 다시 묻지 않는다. 나중에 값을 넣으면 자동 경로로 받는다.
- Wiley 토큰은 구독 논문의 경우 기관 IP 대역에서만 유효하고, OA 논문은 어디서나 된다.

### 3.3 설정 (선택)

`<root>/sci_collect.config.json` 또는 `~/.claude/sci/sci_collect.config.json`. 없으면 기본값을 쓴다.

| 키 | 기본값 | 뜻 |
|---|---|---|
| `intervals` | elsevier_api 3, wiley 5, springer 2, mdpi 2, nature 15, generic 5 (초) | 자동 경로에서 같은 출판사 논문 사이의 대기. 요청을 보내지 않은 논문 뒤에는 기다리지 않는다. acs·science·rsc·ecs·elsevier 값은 웹 전용 출판사를 목록에서 뺄 때만 쓰인다 |
| `web_only_publishers` | acs, rsc, science, ecs, tandf, pnas, aip, oup, ieee, chemrxiv | 자동 요청을 보내지 않고 바로 웹 경로로 보낼 출판사(2026-09-26 여섯 곳 추가). 사이트 사정이 바뀌면 여기서 뺀다 |
| `abstract_only_publishers` | thieme, world_scientific, csj, bentham, royal_society | 초록만 저장할 미구독 출판사 |
| `si_skip_exts` | mp4·avi·mov 등 동영상, mp3·wav, cif·fcf·hkl·mol·mol2·sdf·pdb·xyz·cdx, zip·rar·7z·tar·gz·tgz, xls·xlsx·xlsm·xlsb·csv·ods | 받지 않는 SI 형식. 링크 확장자로 거르고, 받은 뒤 파일 형식으로도 거른다(zip 형식이라도 안이 Word 문서면 받는다). intake 도 이 형식은 옮기지 않는다 |
| `downloads_dir` | 없음 → Chrome 설정의 다운로드 폴더 → Windows 다운로드 폴더 → 사용자 Downloads 순으로 찾음 | intake 가 볼 다운로드 폴더 (`--downloads` 로도 가능). intake 와 doctor 가 어느 근거로 정했는지 출력한다 |
| `crossref_mailto` | 빈 값 | Crossref·OpenAlex 예의용 이메일 (`--mailto` 로도 가능) |
| `assist_wait_seconds` | 300 | 예전 도구 창 방식(`assist --window`)에서만 쓰임 |

### 3.4 폴더 root

수집 전에 사용자에게 확인받은 논문 폴더 하나(5.0)를 `--kb-root` 로 준다(예시: `D:/papers/my_topic`). 그 아래에 `papers/`, `collection_registry.csv`, `_collect/`(로그·목록)가 생긴다. 실험이나 임시 수집은 `_tmp/` 아래에 둔다.

## 4. 입력

- DOI 문자열(한 개 이상), `.txt`·`.csv`(DOI 가 어디 있든 정규식으로 뽑는다), `.xlsx`(openpyxl), WoS·Scopus export 파일(DOI 열 자동 추출). 중복은 제거된다.
- 논문 한 편도 같은 절차다. 규모 판단에서 바로 수집으로 간다.
- WoS·Scopus export 판별: WoS 는 탭 구분 `savedrecs*.txt` 에 `DI`·`TI`·`AB` 열, Scopus 는 `DOI`·`Title`·`Abstract` 열이 있는 CSV.

## 5. 절차

모든 명령은 `python <이 skill 폴더>/scripts/sci_collect.py <명령> --kb-root <root> …` 형태다. 아래에서는 `scripts/sci_collect.py` 로 줄여 쓴다.

### 5.0 저장 폴더 확인 (수집 전에 항상)

- 논문을 저장할 폴더를 사용자에게 묻고 확인받은 뒤에 5.1 을 시작한다. resolve 가 그 폴더에 목록을 만들기 때문이다.
- 추천 경로를 함께 제시한다. 폴더 이름은 입력 파일의 제목들이나 사용자의 말에서 짧은 주제어로 정한다(영문 소문자와 밑줄, 예시: `epoxidation`).
  - Windows: D 드라이브가 있으면 `D:\papers\<주제>`, 없으면 `%USERPROFILE%\Documents\papers\<주제>`
  - macOS·Linux: `~/papers/<주제>`
  - 패키지 폴더와 skill 폴더 안은 쓰지 않는다.
- 사용자가 요청에서 폴더를 이미 말했으면 그 경로를 한 줄로 확인만 한다.
- 고른 폴더에 `collection_registry.csv` 가 이미 있으면 이어서 받는다고 알린다. 이미 받은 논문은 다시 받지 않는다.
- 메시지 예시:

```
논문을 어느 폴더에 저장할까요?
추천: D:\papers\epoxidation (없으면 새로 만듭니다)
다른 곳을 원하시면 경로를 알려 주세요.
```

### 5.1 메타 확정 (resolve)

```bash
python scripts/sci_collect.py resolve --kb-root <root> --input <DOI 파일 또는 DOI …>
```

- Crossref 와 OpenAlex 에서 제목·저자·연도·저널·권호·초록·OA 여부·출판사를 받아 `collection_registry.csv` 에 기록한다. 가입이나 인증은 필요 없다.
- `paper_id` 를 `연도_저널약어_교신저자` 로 만든다(예시: `2021_ACS-Catal_Cheng`). 충돌하면 `_2`, `_3`. 한 번 부여한 id 는 다시 실행해도 바뀌지 않는다.
- 출력 한 줄이 논문 한 편이다: `paper_id 출판사 oa=1/0 abs=Y/- 제목`. 출판사별 편수와 OA 수를 세어, 5.4 전에 사용자에게 자동으로 받을 편수와 웹 경로로 받을 편수를 알린다(6절 표 기준).

### 5.2 규모 판단과 범위 확인 (Claude)

- 30편 이하면 바로 5.4 로 간다.
- 30편을 넘거나 입력이 WoS·Scopus export 면 레지스트리의 제목·초록 몇 개로 주제를 추정하고 사용자에게 한 줄로 확인한다. 사용자가 이미 주제를 말했으면 묻지 않는다.
- 같은 메시지에 review follow-up 질문(5.8)을 묶어 한 번만 묻는다.

### 5.3 사전 분류 (sonnet 하위 에이전트, 큰 목록일 때만)

- 입력: `collection_registry.csv` 의 paper_id·title·abstract 와 사용자가 확인한 주제.
- 판정: IN / BORDERLINE / OUT. IN 과 BORDERLINE 은 수집하고 OUT 은 제외한다.
- 출력: `_collect/triage.csv` (paper_id, verdict, reason 한 줄).
- OUT 은 다음 명령으로 표시한다. 폴더는 만들지 않고 레지스트리에만 남아 색인에 '범위밖-미수집' 으로 보인다. 나중에 사용자가 "이것도 받아" 하면 `--status resolved` 로 되돌린 뒤 5.4 를 다시 한다.

```bash
python scripts/sci_collect.py mark --kb-root <root> --ids <paper_id …> --status out_of_scope
```

- 하위 에이전트 프롬프트 골격:

```
주제: <사용자가 확인한 주제 한 줄>
<root>/collection_registry.csv 의 각 행(paper_id, title, abstract)을 읽고 주제와의 관련을 IN / BORDERLINE / OUT 으로 판정하라.
IN = 주제를 직접 다룸, BORDERLINE = 일부 관련 또는 판단 불충분, OUT = 무관.
결과를 CSV(paper_id, verdict, reason)로 <root>/_collect/triage.csv 에 저장하라. reason 은 한 줄.
```

- 사용자에게는 제외한 논문의 제목 목록과 편수만 보고한다. 판정 라벨 이름은 말하지 않는다.

### 5.4 자동 수집 (collect)

```bash
python scripts/sci_collect.py collect --kb-root <root>
```

- 레지스트리에서 아직 안 받은 논문(미수집·실패·PDF 없음)을 출판사별 스레드로 병렬 수집한다. 같은 출판사 안에서는 설정 간격을 지킨다.
- 웹 전용 출판사(ACS·RSC·Science·ECS/IOP), 토큰 없는 Wiley, OA 가 아닌 Elsevier 구독 논문은 요청하지 않고 바로 웹 경로 대상으로 표시한다. 그 밖의 출판사도 첫 논문에서 막히면 나머지를 요청하지 않는다.
- Elsevier OA 논문은 API 로 받는다. API 한도에 걸리면(429) 그 자리에서 멈추고 남은 논문은 다음 collect 로 미룬다.
- `--input` 을 함께 주면 resolve 를 겸한다. `--ids` 또는 `--publishers elsevier,rsc` 로 범위를 좁힐 수 있고, `--force` 는 이미 받은 것도 다시 받는다.
- 출력 한 줄이 논문 한 편이다. 표시: `OK` 전문, `ABS` 초록만, `USR` 웹 경로 대상, `NOPDF` 텍스트만 확보, `FAIL` 실패. 끝에 상태별 편수 요약이 나온다.

### 5.5 웹 경로 — 평소 쓰는 Chrome 에서 받기

자동으로 받지 못한 논문(웹 경로 대상, PDF 없음)은 사용자 Chrome 에서 받는다. 사용자가 자리에 있을 때 한다. 확인 창이 뜰 수 있기 때문이다.

1. **목록 만들기**: 아래 명령은 창을 열지 않고 논문 주소와 저장 경로 목록을 만든다(`_collect/manual_download.csv`).

```bash
python scripts/sci_collect.py assist --kb-root <root>
```

2. **받을 파일 확인**: 출판사별로 받을 논문과 파일(본문 PDF, SI)을 사용자에게 한 번에 알리고 확인을 받는다. 파일 다운로드는 확인 없이 하지 않는다. Chrome 설정 두 가지(3.1)는 이때 `doctor` 로 확인한다.
3. **받기**: Claude in Chrome 확장으로 사용자 Chrome 의 새 탭에서 논문 주소를 연다. 한 편씩 진행한다. 그 Chrome 창은 화면 앞에 두고 수집 중에는 건드리지 않는다. 다른 모니터나 다른 프로그램은 써도 되지만, 그 창이 다른 창에 완전히 덮이거나 최소화되면 스크린샷이 안 되고 클릭이 빗나간다.
   - 출판사별 요령(선택자, 기다릴 시간, 누르는 순서, 함정)은 `references/web_download_playbook.md` 를 먼저 읽고 첫 논문부터 그대로 한다. 헤매는 호출을 줄이는 것이 시간을 가장 많이 줄인다.
   - 확인 창(체크박스)이 뜨면 사용자에게 눌러 달라고 한다. Claude 는 누르지 않는다. 눌러도 계속 다시 뜨면 더 누르지 말라고 알리고 그 사이트는 멈춘다.
   - SI 는 문서(PDF, Word)만 받는다. 동영상·음성, 결정 구조 파일(CIF 등), 압축 파일(zip 등), 스프레드시트(Excel, CSV 등)는 받지 않는다(2026-09-25 사용자 지시). 결정 구조와 대형 스프레드시트 데이터는 대개 zip 이나 Excel 로 온다. 링크 글자나 파일 이름으로 형식을 보고 누른다. 도구의 자동 경로도 설정 `si_skip_exts` 로 같은 형식을 거른다.
   - 6절 표의 버튼으로 본문 PDF 와 SI 를 받는다. 누르기 전에 버튼을 화면에 띄우고 스크린샷으로 위치를 확인한 뒤 좌표로 누른다. 페이지 배치가 바뀌어 클릭이 추천 논문 링크에 떨어진 적이 있다.
   - 쿠키 동의 창은 누르지 않는다(사용자 결정). 뉴스레터·추천 논문 안내 창은 닫기(X)만 누른다. 다른 논문을 여러 편 받는 버튼("Download (6) PDFs" 등)은 누르지 않는다.
   - PDF 를 받으며 열린 보조 탭(확인 단계 탭 등)은 닫는다.
4. **정리**: 받은 뒤 `intake` 로 다운로드 폴더의 파일을 논문 폴더로 옮기고 반영한다(5.6.1). 출력에서 가리지 못한 파일이 있으면 무엇인지 확인한다.
5. **간격과 양**: 같은 출판사 안에서는 한 편씩 받고, 한 편이 끝나면 기다리지 않고 바로 다음 논문으로 간다. 출판사당 한 번에 수십 편 이내로 나눈다. 탭은 하나만 쓰고, 그 탭을 화면 앞에 둔 채 순서대로 받는다(2026-09-26 사용자 확정). 여러 탭이나 여러 창을 번갈아 쓰는 방식은 쓰지 않는다. 시험 결과 시간 이득이 18편에 1~3분에 그쳤고, 뒤쪽 탭에서는 클릭이 빗나가고 연결이 끊겼으며, 확장은 탭을 앞으로 가져오거나 창을 옮길 수 없다(references/web_download_playbook.md 4절).
6. **마무리**: 작업이 끝나면 연 탭을 모두 닫는다.
7. **중단 뒤 재개**: 탭이 닫혔거나 세션이 끊겼으면 `intake` → `status` → `assist` 순으로 돌린다. 받아 둔 파일이 정리되고 남은 논문만 목록에 남는다. 확장이 새로 만드는 Chrome 창은 뒤에 열리므로 사용자에게 앞으로 가져와 달라고 한 뒤 이어서 받는다(references/web_download_playbook.md 5절).

사용자가 직접 받겠다고 하면 목록(`_collect/manual_download.csv` 의 url·save_to)을 전달한다. 평소처럼 받아 다운로드 폴더에 두면 `intake` 로 정리한다.

예전 도구 창 방식(`assist --window`)은 쓰지 않는다. 도구가 띄운 Chrome 에서는 Elsevier·Wiley 확인 창이 반복되고, RSC 는 PDF 가 거부된다(2026-09-24 실측).

### 5.6 직접 저장한 PDF 반영 (status)

```bash
python scripts/sci_collect.py status --kb-root <root>
```

- 사용자가 `papers/{paper_id}/pdf/{paper_id}.pdf` 에 직접 저장한 파일을 감지해 본문 텍스트를 뽑고(`source.md`, `source.json`, 검증) 상태를 전문으로 바꾼다. 대상은 메타만 있음, 웹 경로 대상, PDF 없음, 실패 논문이다. 현재 상태별 편수도 보여 준다.

### 5.6.1 다운로드 폴더 정리 (intake)

```bash
python scripts/sci_collect.py intake --kb-root <root>
```

- 다운로드 폴더에서 논문 PDF·SI 를 찾아, 어느 논문인지 가린 뒤 `papers/{id}/pdf/` 에 정해진 이름(`{id}.pdf`, `{id}_SI.pdf`, `_SI_2` …)으로 옮기고 본문 텍스트를 반영한다.
- 가리는 근거: 파일 이름의 논문 코드(Elsevier PII, DOI 끝부분), PDF 앞 두 쪽의 DOI, 첫 쪽의 제목, PDF 뒤쪽의 DOI. 근거가 충분하고 한 논문에만 해당할 때만 옮긴다. 참고문헌에 다른 논문 DOI 가 있어도 그것만으로는 옮기지 않는다. Science·IOP PDF 는 첫 쪽에 DOI 글자가 없어 파일 이름과 제목으로 가린다. Word(.docx) SI 는 본문 앞부분의 제목·DOI 로도 가린다. IOP 옛 논문 SI 는 파일 이름이 `1960.docx` 처럼 숫자뿐이다.
- SI 구분: 파일 이름 규칙(mmc, _suppl, _si_, -sup-, -sm 등) 또는 첫 쪽 맨 앞의 Supporting/Supplementary 문구. ACS 본문 PDF 는 첫 쪽 중간에 "Supporting Information" 안내가 있어 맨 앞만 본다.
- 이미 본문 PDF 가 있거나 같은 SI 가 있으면 옮기지 않는다. 가리지 못한 파일도 그대로 둔다. 파일을 지우지 않는다.
- 다운로드 폴더는 설정 `downloads_dir`, Chrome 설정의 다운로드 폴더, Windows 의 다운로드 폴더, `~/Downloads` 순으로 찾고 어느 근거인지 출력한다. 기본은 최근 24시간 안에 받은 파일만 본다(`--hours`). 다른 폴더는 `--downloads`. `--dry-run` 이면 옮기지 않고 판정만 보여 준다.
- 판정 기록: `_collect/intake_log.csv`.
- 시험 (2026-09-25): 여섯 출판사 실제 다운로드 이름 그대로 11개 파일 → 모두 맞는 논문·자리로 이동, 목록에 없는 논문 PDF 1개는 그대로 둠, 같은 파일을 다시 넣으면 옮기지 않음.
- 시험 2 (2026-09-25): 여섯 출판사 18편을 웹으로 받은 34개 파일(211 MB) → 모두 맞는 논문·자리로 이동, 약 5초. 이름이 숫자뿐인 Word SI 1개를 처음에 못 가려 Word 본문 대조를 넣었다.

### 5.6.2 본문 다시 뽑기 (reextract)

```bash
python scripts/sci_collect.py reextract --kb-root <root>
```

- 저장된 PDF·HTML·XML 원본만으로 `source.md` 와 `source.json` 을 다시 만든다. 출판사에 요청을 보내지 않는다.
- 추출 규칙이 바뀐 뒤 기존 수집분에 적용할 때 쓴다. 예: 2026-09-24 PDF 텍스트 순서 수정, 2026-09-26 제어 문자(NUL) 제거, 출판사 새 페이지 구조 반영.
- 이전 본문이 새 본문보다 훨씬 길면 `source_pre_<날짜>.md` 로 남겨 둔다.

### 5.7 색인 (편수에 따라 묻거나 생략)

수집(웹 경로와 intake 까지)이 끝나면 이번에 받은 논문 편수(전문과 초록만의 합)로 정한다.

- **30편을 넘으면 묻는다**: "수집한 논문 N편의 서지정보를 색인화 하겠습니까?" 동의하면 `sci-index` 지침대로 `sci_index.py build` 를 돌리고 sonnet 검수·요약 패스를 거친다.
- **30편 이하면 색인하지 않고 알린다**: "논문 색인 과정은 생략하겠습니다. 색인을 원하시면 말씀해 주세요." 사용자가 원하면 위와 같이 색인한다.
- 폴더에 `index.csv` 가 이미 있으면 편수와 관계없이 "새로 받은 N편을 기존 색인에 반영할까요?" 라고 묻는다.

### 5.8 review 인용 follow-up (선택, Claude)

- resolve 결과에서 제목·초록으로 review·perspective·roadmap 류를 알아본다. 있으면 5.2 의 확인 메시지에 "review 논문 N편의 인용 논문도 이어서 받을까요?" 를 묶어 한 번만 묻는다.
- 동의하면 수집이 끝난 뒤 해당 review 의 `source.md` 참고문헌에서 DOI 를 뽑고(정규식 `10\.\d{4,9}/\S+`), 레지스트리에 없는 것만 골라 편수를 알린 뒤 5.1 부터 다시 돈다. 어떤 인용을 고를지는 사용자의 주제에 맞춰 Claude 가 판단하되, 수를 채우려고 고르지 않는다.

### 5.9 보고

사용자에게 다음만 말한다.

- 총 편수와 상태별 편수: 전문 / 초록만(미구독 출판사 이름) / 웹 경로로 받을 논문(출판사별) / 범위 밖
- 다음 행동: 웹 경로로 받을 파일 목록과 자리 요청, 색인 질문 또는 생략 안내(5.7)
- 실패가 있으면 논문과 이유 한 줄씩

## 6. 출판사별 수집 방법 (2026-09-26 최종)

### 6.0 사용자 안내용 요약표

사용자가 출판사별 수집 방법이나 간격을 물으면 이 표를 그대로 보여 준다. "파이썬 API" 는 도구가 출판사 공식 API 로 받는 방식, "파이썬 직접 다운로드" 는 도구가 출판사 PDF 주소로 바로 받는 방식, "웹 다운로드" 는 사용자가 평소 쓰는 Chrome 에서 Claude 가 받고 다운로드 폴더 정리 명령(intake)으로 논문 폴더에 넣는 방식이다.

| 출판사 | 조건 | 수집 방법 | 간격 | 메모 |
|---|---|---|---|---|
| Elsevier | API key 있음 + OA 논문. 발급: https://dev.elsevier.com/ | 파이썬 API | 3초 | 기관 API key 발급요청 거절 datasupportRD@elsevier.com |
| Elsevier | 유료 논문 또는 API key 없음 | 웹 다운로드 | 30~60초 | - |
| Wiley | TDM 토큰 있음. 발급: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining | 파이썬 API | 5초 | 기관 TDM 토큰 발급요청 거절 TDM@wiley.com |
| Wiley | TDM 토큰 없음 | 웹 다운로드 | 30~60초 | - |
| Springer | - | 파이썬 | 2초 | - |
| Nature | - | 파이썬 | 15초 | - |
| MDPI | - | 파이썬 | 2초 | - |
| Frontiers | - | 파이썬 | 5초 | - |
| PLOS | - | 파이썬 | 5초 | - |
| Beilstein | - | 파이썬 | 5초 | - |
| Copernicus | - | 파이썬 | 5초 | - |
| APS | KIST 구독 저널만 | 파이썬 | 5초 | - |
| Cambridge | - | 파이썬 | 5초 | - |
| ACS | - | 웹 다운로드 | 30~60초 | API key 발급요청 거절 acs_pubs_assist@acs.org |
| RSC | - | 웹 다운로드 | 30~60초 | 개별요청 RSC TDM 페이지: https://www.rsc.org/journals-books-databases/research-tools/text-and-data-mining/ |
| IOP | - | 웹 다운로드 | 30~60초 | - |
| Science | - | 웹 다운로드 | 30~60초 | - |
| Taylor & Francis | - | 웹 다운로드 | 30~60초 | - |
| PNAS | - | 웹 다운로드 | 30~60초 | - |
| AIP | - | 웹 다운로드 | 30~60초 | - |
| Oxford | - | 웹 다운로드 | 30~60초 | - |
| IEEE | - | 웹 다운로드 | 30~60초 | - |
| ChemRxiv | - | 웹 다운로드 | 30~60초 | - |
웹의 30~60초는 한 편을 받는 데 자연히 드는 시간이다(페이지 열기, 누르기, 저장). 논문 사이에 따로 기다리지는 않는다. 미구독 출판사(초록만 저장)와 표에 없는 출판사(파이썬 직접 시도, 막히면 그 사이트만 웹)는 6.1 을 본다. 웹 경로의 사이트별 순서는 references/web_download_playbook.md 3절이다.

### 6.1 상세 (Claude 작업용)

| 출판사 | DOI 접두 | 자동 경로 | 웹 경로 (평소 쓰는 Chrome) | 간격 | 유의사항 |
|---|---|---|---|---|---|
| Elsevier, OA 논문 | 10.1016, 10.1006 | Article Retrieval API 로 본문 XML+PDF. API 키 필요. 키 발급: https://dev.elsevier.com/. 가장 빠른 경로 | 키가 없을 때만 | 3초 (공식 한도: 키당 초당 10회, 주 5만 회) | OA 표시가 있어도 출판사판이 비공개면 첫 페이지만 온다 → 저장소 사본을 찾아본 뒤 웹 경로 |
| Elsevier, 구독 논문 (OA 아님) | 10.1016, 10.1006 | API 를 쓰지 않음, 바로 웹 경로 | 상단 "View PDF". SI 는 부록의 "Download … file" 링크 | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | "View PDF" 뒤 뜨는 추천 논문 안내 창은 닫기만(안의 "Download (6) PDFs" 금지). 상단 고정 막대의 "Download full issue"(호 전체) 금지. 확인 단계 탭은 닫기. 차단 문구가 나오면 즉시 중단, 30분 뒤 |
| Wiley, 토큰 있음 | 10.1002 | TDM API 로 PDF. 토큰 발급: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining | API 가 실패한 논문만 | 5초 | 구독 논문 토큰은 기관 IP 대역에서만 유효 |
| Wiley, 토큰 없음 | 10.1002 | 없음, 바로 웹 경로 | 본문 끝 "Download PDF" → PDF 가 든 페이지에서 Chrome "열기". SI 는 접힌 "Supporting Information" 을 펼친 뒤 파일 링크 | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | 상단 "PDF" 는 온라인 보기라 쓰지 않음. Advanced 계열은 `advanced.onlinelibrary.wiley.com`. 페이지가 늦게 뜰 때가 있음. 첫 사용 때 토큰 안내 |
| ACS | 10.1021 | 없음, 바로 웹 경로 | "Open PDF". SI 는 Supporting Information 절의 "sifile1" 류 링크 | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | 확인 창이 한 번 뜰 수 있음, 사용자가 누름. SI 미리보기 창의 Download 버튼 말고 링크를 씀. 토큰 제도 없음 |
| RSC | 10.1039 | 없음, 바로 웹 경로 | 툴바 "PDF". SI 는 "Supplementary information (PDF)" | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | 2026-06-30 새 플랫폼. 로그인 확인 페이지를 잠깐 거친 뒤 자동으로 열림 |
| ECS/IOP | 10.1149 | 없음, 바로 웹 경로 | "PDF" 버튼. SI 는 "Supplementary data" 버튼 → 목록 페이지의 파일 링크(있을 때) | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | 쿠키 동의 창은 누르지 않음. 출판사 텍스트 마이닝 정책 페이지가 있음 |
| Science | 10.1126 | 없음, 바로 웹 경로 | 제목 아래 오른쪽 빨간 PDF 아이콘 → 열린 온라인 보기의 오른쪽 위 둥근 다운로드 아이콘. 또는 도구 막대 눈 아이콘 "View Options" → "DOWNLOAD PDF". SI 는 Supplementary Material 의 "DOWNLOAD" | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | 아래쪽 뉴스레터 안내는 닫기 |
| Springer | 10.1007, 10.1023 | 직접 PDF + HTML + SI | 자동 실패한 논문만 | 2초 | |
| Nature | 10.1038 | 논문 페이지 + PDF + SI | 자동 실패한 논문만 | 15초 | 갓 나온 논문은 페이지에 초록만 있고 PDF 주소가 HTML 로 응답해 실패로 남는다(2026-09-26). 며칠 뒤 `collect --ids <id> --force` |
| MDPI | 10.3390 | 직접 PDF + HTML + SI | 자동 실패한 논문만 | 2초 | 모두 OA |
| Frontiers, PLOS, Beilstein, Copernicus, APS, Cambridge | 10.3389, 10.1371, 10.3762, 10.5194, 10.1103, 10.1017 | 논문 페이지 + PDF + SI (일반 경로, 이름만 붙임) | 자동 실패한 논문만 | 5초 | 2026-09-26 확인: 사이트마다 3편을 5초 간격으로, 일곱 사이트 동시에 받아 차단 없음. 한 편 완료 간격 4~11초, PDF 가 8~11 MB 인 Beilstein·Copernicus 는 23~54초. APS 는 KIST 구독 저널(Phys. Rev. B)만 받히고 Phys. Rev. D·Applied 는 페이지에 PDF 링크가 없어 실패(구독 밖) |
| Taylor & Francis, PNAS, AIP, Oxford, IEEE | 10.1080, 10.1073, 10.1063, 10.1093, 10.1109 | 없음, 바로 웹 경로 (설정 `web_only_publishers`, 2026-09-26 실측 403·202) | playbook 3.7~3.11. T&F·PNAS·ChemRxiv 는 페이지 아래 "Download PDF", AIP 는 도구 막대 "PDF"(새 탭), Oxford 는 상단 "PDF", IEEE 는 "PDF" → "열기". PNAS·Oxford 는 저장 전에 Cloudflare 확인 화면을 스스로 통과 | 30~60초 (한 편 처리 시간, 따로 기다리지 않음) | 상황이 바뀌면 설정에서 뺀다 |
| 그 외 | | 논문 페이지 + PDF 후보 + SI. 사이트(호스트)별로 한 번 막히면 그 사이트의 나머지는 요청하지 않고 웹 경로. 막힌 논문 자체도 웹 경로 대상으로 표시. 페이지에 PDF 링크가 없고 본문이 짧으면 '구독 밖일 수 있음' 으로 표시 | 막힌 논문 | 5초 | |
| 프리프린트 | 10.26434 (ChemRxiv), 10.48550 (arXiv), 10.1101 (bioRxiv) | ChemRxiv 는 자동 요청을 막아(403) 바로 웹 경로(설정 `web_only_publishers`). arXiv·bioRxiv 는 그 외와 같음 | playbook 3.12 (ChemRxiv "Download PDF") | 5초 | 접두어로 고정(Crossref 는 ChemRxiv 를 ACS 로 적음). 저널약어는 ChemRxiv·arXiv·bioRxiv |
| 미구독 출판사 | 10.1055 (Thieme), 10.1142, 10.1246, 10.2174, 10.1098 | 초록만 저장 | 없음 | | 사용자에게 알림. 구독이 생기면 설정에서 뺀다 |

- 웹 경로는 논문 사이에 따로 기다리지 않는다(2026-09-25 사용자 지시로 30초 간격 폐지). 페이지 열기, 누르기, 확인, 정리까지 한 편에 보통 30초~1분이 걸린다. 실측(2026-09-25, 여섯 출판사 18편)은 한 편 26~262초, 중앙값 60초였고 Wiley 가 가장 느렸다(references/publisher_matrix.md). 요령 문서대로 새 논문 18편을 받은 2차 시험은 16.7분, 한 편 중앙값 42.5초였다(references/web_download_playbook.md). 출판사당 한 번에 수십 편 이내로 나눈다.
- 2026-09-24 사용자 Chrome 실측: Elsevier·RSC·Wiley·Science·IOP 는 확인 창 없이 열렸고 ACS 만 한 번 떴다. 날마다 달라질 수 있다.
- 다운로드 폴더 파일 이름 규칙과 출판사별 상세·실측 이력은 `references/publisher_matrix.md` 맨 앞 ★ 절에 있다.

## 7. 산출물

```
<root>/
  collection_registry.csv        DOI → paper_id, 메타, 상태 (한 행 = 논문 한 편)
  papers/{paper_id}/
    pdf/{paper_id}.pdf           본문 PDF (필수)
    pdf/{paper_id}_SI.pdf        SI. 여러 개면 _SI_2, _SI_3 … (받은 형식 그대로, 변환 없음. 확장자는 받은 파일 형식)
    html/{paper_id}.html         원본 HTML (있을 때)
    xml/{paper_id}.xml           Elsevier XML (있을 때)
    source.md                    본문 텍스트 (머리에 메타, "## Full Text" 아래 본문)
    source.json                  메타 + 수집 방법 + 텍스트 출처
    source_origin.txt            수집 이력 (append)
  _collect/
    collect_log.csv              자동 수집 시도 로그
    manual_download.csv          웹 경로 목록 (url, save_to)
    intake_log.csv               다운로드 폴더 정리 판정 기록
    chrome_profile_headless_*/   자동 단계의 창 없는 1회 시도용 프로필
    triage.csv, index_gists_*.csv  Claude 하위 에이전트 출력
```

- SI 는 논문 페이지의 SI 링크에서 받는다. 도구가 받지 못한 SI 는 버리지 않고 웹 경로 목록에 다음 번호의 저장 이름으로 올라간다.
- 본문 텍스트 출처 우선순위: XML > HTML(본문 영역만 추출, 추천 논문·인용·메뉴 같은 부속 요소 제거) > PDF(PDF 기본 순서로 읽어 두 단이 섞이지 않게, 하이픈 복원, 반복 머리말 제거). HTML 텍스트가 PDF 텍스트 길이의 0.6~1.6배 밖이면 PDF 텍스트를 쓴다. 웹 경로로 받은 논문은 PDF 텍스트를 쓴다.
- 저장 뒤 검증(본문 길이·구조·첫 페이지 미리보기 여부)에 걸리면 PDF 가 있을 때는 경고, 없을 때는 실패로 기록한다.

레지스트리 상태값:

| 상태 | 뜻 | 다음 단계 |
|---|---|---|
| resolved | 메타만 있음 | collect |
| full | 본문 PDF + 텍스트 | 색인 |
| abstract_only | 미구독, 초록만 | 없음 (사용자에게 알림) |
| human_required | 웹 경로 대상 | 5.5 웹 경로 → intake |
| pdf_missing | 텍스트는 있으나 PDF 없음 | 5.5 웹 경로 → intake |
| failed | 오류 | 로그 확인 후 collect 재시도, 안 되면 웹 경로 |
| out_of_scope | 사전 분류에서 제외 | 필요 시 mark 로 되돌림 |

## 8. 사용자 안내 문구 (템플릿)

- 범위 확인 + follow-up: "목록이 N편입니다. 주제를 '…' 로 보고 관련 논문만 받겠습니다. 맞나요? review 논문 M편의 인용 논문도 이어서 받을까요?"
- 자동·웹 안내: "A편은 자동으로 받습니다. B편(출판사 …)은 사이트가 자동 수집을 막아서 평소 쓰시는 Chrome 에서 받아야 합니다. 자리에 계실 때 말씀해 주세요."
- Elsevier OA: "Elsevier 논문 중 Open Access 인 N편은 API 키로 바로 받았습니다. 나머지 M편은 구독 논문이라 평소 쓰시는 Chrome 에서 받아야 합니다." 키가 없으면 3.2.1 문구로 발급을 안내한다.
- 받을 파일 확인: "평소 쓰시는 Chrome 에서 다음 파일을 받겠습니다. 출판사 …: 논문 N편의 본문 PDF 와 SI. 진행할까요?"
- Chrome 설정: "받기 전에 Chrome 에서 PDF 를 바로 내려받도록 설정해 주세요. 주소창에 chrome://settings/content/pdfDocuments 를 열고 'PDF 다운로드' 를 고르면 됩니다."
- 확인 창: "Chrome 탭에 확인 체크박스가 떴습니다. 눌러 주시면 이어서 받겠습니다."
- 확인 창 반복: "확인 창이 계속 다시 뜨면 더 누르지 않으셔도 됩니다. 이 사이트는 잠시 멈추겠습니다."
- 직접 받는 경우: "아래 주소에서 PDF 를 받아 다운로드 폴더에 두시면 제가 정리하겠습니다." 목록은 `_collect/manual_download.csv` 의 url 열이다.
- Wiley·Elsevier 첫 사용: 3.2.1 의 문구를 한 번.
- 미구독: "다음 출판사 논문은 구독이 없어 초록만 저장했습니다: …"
- 차단: "사이트가 잠시 접근을 제한했습니다. 30분 뒤 이어서 받겠습니다."
- 대량 수집: "수백 편 이상은 도서관을 통해 출판사의 텍스트 마이닝 이용을 정식으로 요청하시는 것이 안전합니다."

## 9. 문제 대응

| 증상 | 원인 | 조치 |
|---|---|---|
| `ModuleNotFoundError` | 다른 파이썬 인터프리터 | 3.1 의 확인 명령으로 되는 인터프리터를 찾는다 |
| SSL 오류 (인증서 검증 실패) | 기관 망의 TLS 재서명 | truststore 가 OS 인증서를 쓰므로 설치 확인 |
| 자동 단계에서 USR 가 많음 | 사이트가 자동 요청을 막음 | 정상. 5.5 웹 경로 |
| Elsevier API 가 첫 페이지만 | OA 표시와 달리 출판사판이 비공개 | 저장소 사본을 찾아보고 없으면 5.5 웹 경로 |
| Elsevier API 429 응답 | 키 한도(초당 10회, 주 5만 회) 초과 | 도구가 멈추고 남은 논문을 다음 collect 로 미룸. 주 한도면 다음 주 |
| "problem providing the content" 문구 | ScienceDirect 일시 제한 | 즉시 멈추고 30분 뒤 |
| PDF 누르면 저장 창이 뜸 | Chrome PDF 보기 화면의 다운로드 버튼 | 3.1 의 "PDF 다운로드" 설정 확인 |
| 클릭이 다른 논문 링크에 떨어짐 | 페이지 배치 변화 | 버튼을 화면에 띄우고 스크린샷으로 확인 뒤 좌표로 누른다. 잘못 열린 페이지는 뒤로 가기 |
| 눌러도 확인 창이 반복됨 | 그 사이트 확인이 통과되지 않음 | 더 누르지 않는다. 그 사이트는 멈추고 나중에 다시 한다 |
| intake 가 가리지 못한 파일 | 목록에 없는 논문이거나 다른 파일 | 그대로 둔다. 필요한 논문이면 resolve 로 등록한 뒤 다시 intake |
| 다운로드 이름 끝에 " (2)" | 같은 이름의 파일이 이미 있음 | intake 는 이름이 아니라 내용으로 가리므로 그대로 둔다 |
| resolve 실패 | DOI 오타·Crossref 미등록 | DOI 확인, 필요하면 사용자에게 제목으로 확인 |
| 같은 논문이 두 폴더 | DOI 표기 차이 | 하나를 out_of_scope 로 표시 |
| 실행마다 `fitz API is deprecated` 경고 | 옛 pymupdf 이름 | 오류가 아니다. 2026-09-26 부터 도구가 새 이름을 써서 나오지 않는다. 나오면 `pip install -U pymupdf` |
| 파일마다 저장 창이 뜸 | Chrome "다운로드 전에 각 파일의 저장 위치 확인" 켜짐 | `chrome://settings/downloads` 에서 끈다. `doctor` 가 알려 준다 |
| intake 가 파일을 하나도 못 봄 | 다운로드 폴더가 다른 곳(OneDrive 등) | `doctor`·intake 출력의 폴더와 근거를 보고 `--downloads` 로 지정 |
| "열기" 버튼이 안 보임 | 영어 Chrome | "Open". 위치는 같다 |
| 확장 브라우저 목록에 둘 이상 | 같은 계정의 다른 컴퓨터 Chrome | 이 컴퓨터 것(`onThisComputer`)만 고른다. 이 컴퓨터 것이 둘이면 사용자에게 묻는다 |
| 스크린샷이 하얗거나 시간 초과 | 그 Chrome 창이 뒤에 있거나 최소화 | 사용자에게 창을 앞으로 가져와 달라고 한다 |
| 그 외 출판사에서 `status=403/202` | 그 사이트가 자동 요청을 막음 | 도구가 그 논문과 같은 사이트의 나머지를 웹 경로로 표시한다. 다른 사이트는 계속 시도한다 |
| Nature 갓 나온 논문이 `inadequate_body_length` | 페이지에 초록만 있고 PDF 미공개 | 며칠 뒤 `collect --ids <id> --force`. 급하면 웹 경로 |

## 10. 예시 (예시)

DOI 12개가 든 `dois.txt` 를 `D:/papers/my_topic` 에 받는 흐름. Elsevier 키와 Wiley 토큰이 있다고 가정한다.

```bash
python scripts/sci_collect.py doctor --kb-root D:/papers/my_topic
python scripts/sci_collect.py resolve --kb-root D:/papers/my_topic --input D:/papers/my_topic/dois.txt
```

출력 예시: elsevier 4 (oa 1), wiley 3, acs 2, mdpi 2, thieme 1. 사용자에게 "Elsevier OA 1편과 Wiley·MDPI 5편은 자동, Elsevier 구독 3편과 ACS 2편은 평소 쓰시는 Chrome 에서 받아야 하고, Thieme 1편은 초록만" 이라고 알린다.

```bash
python scripts/sci_collect.py collect --kb-root D:/papers/my_topic
```

자동 단계 결과 예시: 전문 6, 초록만 1, 웹 경로 대상 5. 사용자가 자리에 오면 목록을 만들고 받을 파일을 확인받는다.

```bash
python scripts/sci_collect.py assist --kb-root D:/papers/my_topic
```

Claude 가 사용자 Chrome 에서 5편의 본문 PDF 와 SI 를 받은 뒤 정리한다.

```bash
python scripts/sci_collect.py intake --kb-root D:/papers/my_topic
```

결과 예시: 전문 11, 초록만 1. 이어서 `sci-index` 로 색인한다.

## 11. 참고 문서

- `references/publisher_matrix.md`: 맨 앞 ★ 절에 웹 경로 버튼 위치·파일 이름 규칙, 뒤에 출판사별 URL·방법·실측 이력. 공통 정책이 개별 절보다 우선한다.
- `references/web_download_playbook.md`: 웹 경로 출판사별 요령과 교훈. 선택자, 기다릴 시간, 누르는 순서, 함정, 예상 시간.
- `references/safe_rate_policy.md`: 요청 간격의 현재 규칙과 근거(ScienceDirect 4월 일시 차단 기록, 규칙 변천).
- `examples/sample_doi_input.csv`: 출판사별 실제 DOI 예시(2026-09-26 확인). 첫 실행 연습용.
- `references/_history/`, `examples/_history/`: 옛 문서(2026-04~05 의 도구 창·Playwright·90초 간격 방식, 개인 기록). 현재 규칙과 다르므로 지침으로 읽지 않는다.
- `references/credentials_setup.md`: 키·토큰 발급.
- `scripts/README.md`: 옛 배치 스크립트(runner.py 등) 설명. 새 작업은 `sci_collect.py` 만 쓴다. runner.py 는 판정·검증 함수를 제공하는 라이브러리로 남아 있다.

## 12. 하지 않는 것

- 별도 agent 파일. skill 과 CLI 로 충분하다. LLM 은 사전 분류, follow-up 선별, 색인 검수에만 쓴다.
- 임베딩·DB 구축. 색인은 CSV 다.
- CAPTCHA 나 확인 창을 대신 누르는 일. 사용자가 부탁해도 할 수 없다고 말한다.
- 자동화 표시 숨김, 쿠키 옮겨 쓰기, 연결 방식 흉내 같은 우회 기능, 차단 직전 간격을 찾는 시험.
- 쿠키 동의, 약관 동의, 로그인. 필요하면 사용자에게 맡긴다.
- 논문 그림·표 추출, SI 의 텍스트 변환.
