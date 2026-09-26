# sci-retr on Codex — 설치·사용 지침 (Codex 에이전트용)

> 이 문서는 Codex (Codex Desktop 앱 / Codex CLI) 가 sci-retr 을 설치하고 쓸 때 따르는 기준이다.
> 사용자가 "sci-retr 설치해줘", "https://github.com/angmond1/sci-retr 설치해줘" 라고 하면 추측하지 말고 아래 1절을 순서대로 실행한다.
> skill 본문(`sci-retr/SKILL.md`, `sci-index/SKILL.md`, `sci-retr/references/*.md`)은 Claude 기준으로 쓰여 있다. Codex 는 2절 대응표로 바꿔 읽는다. 정책과 절차는 본문이 정본이다.

## 0. 무엇인가 (한 줄)

논문 수집 skill `sci-retr` 과 색인 skill `sci-index` 두 개. DOI 목록(WoS·Scopus 내보내기 파일 포함)을 받아 출판사별로 파이썬 API·직접 다운로드로 받거나, 자동 요청을 막는 출판사는 사용자의 Chrome 에서 받아 `papers/{paper_id}/` 폴더(본문 PDF, SI, `source.md`, `source.json`)로 정리하고 `index.csv` 를 만든다.

권장 모델: README 의 Claude 모델을 Codex 모델에 임의로 대응시키지 않는다. 설치와 첫 수집은 사용자가 쓰는 가장 높은 추론 설정으로 한다.

## 1. 설치 절차 (에이전트가 그대로 실행)

### Step 0 — 실행 환경
- Python 3.11 이상. 확인: Windows `py -3 --version`, macOS/Linux `python3 --version`. 없으면 Windows 는 `winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements`, macOS 는 `brew install python@3.12`.
- Node.js (웹 다운로드용 브라우저 도구가 `npx` 로 돈다). 확인 `node --version`. 없으면 Windows `winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements`.
- git 은 있으면 쓰고 없으면 ZIP 으로 진행한다. 설치를 요구하지 않는다.
- 교내 망(기관 IP)에서만 유료 논문이 열린다. 밖이면 기관 VPN 을 안내한다.

### Step 1 — 폴더 위치 정하기 + 패키지 확보
1. 먼저 묻는다: "sci-retr 을 어디에 둘까요? ① 기본 `C:\sci-retr`(macOS/Linux `~/sci-retr`) ② 다른 위치". 답이 없으면 기본.
2. git 있으면 `git clone https://github.com/angmond1/sci-retr.git <root>`. 없으면 GitHub 페이지에서 `Code ▾ → Download ZIP` 을 받아 그 폴더에 푼다(collaborator 권한 필요).

### Step 2 — skill 설치 (Codex 폴더로)
현재 OS 를 판단해 하나만 실행한다. `-Codex` / `--codex` 가 있어야 Codex 폴더(`~/.codex/skills`, `CODEX_HOME` 이 있으면 그 아래)로 들어간다.
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File <root>\install.ps1 -Codex`
- macOS / Linux: `bash <root>/install.sh --codex`

스크립트가 `sci-retr`, `sci-index` 를 `~/.codex/skills/` 로 복사하고 파이썬 패키지(requests, pymupdf, truststore, beautifulsoup4, lxml, openpyxl, wiley-tdm, playwright)를 설치한다. `ModuleNotFoundError` 가 나면 다른 인터프리터(`py -3.12`, `python3.12` 등)로 다시 시도한다.

### Step 3 — 브라우저 도구 (웹 다운로드용, chrome-devtools MCP)
웹 다운로드는 사용자가 평소 쓰는 Chrome 에서 한다. Codex 는 chrome-devtools MCP 를 `--autoConnect` 로 등록해 그 Chrome 에 붙는다. 별도 Chrome 창을 띄우는 방식(`--autoConnect` 없이)은 출판사 확인 창이 잦을 수 있어 쓰지 않는다(2026-09-24, 도구가 띄운 Chrome 에서 Elsevier·Wiley 확인 창 반복, RSC PDF 거부).

1. 이미 등록돼 있는지 본다: `~/.codex/config.toml` 의 `[mcp_servers.chrome-devtools]`. 있고 인자에 `--autoConnect` 가 있으면 그대로 쓴다. `--autoConnect` 가 없으면 사용자에게 추가를 제안한다.
2. 없으면 등록한다. Codex 설정 → MCP 서버 → 서버 추가 → 이름 `chrome-devtools`, 명령 `npx -y chrome-devtools-mcp@latest --autoConnect`. CLI 로는:
   ```
   codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest --autoConnect
   ```
   Windows 에서 `npx` 를 찾지 못하면 `-- cmd /c npx -y chrome-devtools-mcp@latest --autoConnect`.
3. 사용자에게 한 번 부탁한다 (Chrome 144 이상):
   > "평소 쓰시는 Chrome 주소창에 `chrome://inspect/#remote-debugging` 을 열고 원격 디버깅을 허용해 주세요. Codex 가 그 Chrome 의 탭을 열어 논문을 받습니다."

### Step 4 — Chrome 설정 두 가지 (사용자가 직접)
> "Chrome 에서 두 가지를 바꿔 주세요. ① `chrome://settings/content/pdfDocuments` 에서 'PDF 다운로드' 선택 ② `chrome://settings/downloads` 에서 '다운로드 전에 각 파일의 저장 위치 확인' 선택 해제. 이래야 PDF 가 저장 창 없이 다운로드 폴더로 바로 들어갑니다."

### Step 5 — 재시작 (반드시 안내)
Codex 는 시작할 때 skill 목록을 읽는다. 새 skill 과 새 MCP 서버는 재시작해야 보인다.
> "설치 완료. Codex 를 재시작한 뒤 `sci-retr 점검해줘` 라고 해주세요."

### Step 6 — 점검 (재시작 뒤 첫 대화)
```
python ~/.codex/skills/sci-retr/scripts/sci_collect.py doctor --kb-root <논문 폴더>
```
"문제 0" 이면 된다. 키·토큰(선택)은 `sci-retr/examples/.env.example` 을 논문 폴더의 `.env` 로 복사해 채우게 안내하고, 값은 채팅에 적지 않게 한다. 도구 목록에 chrome-devtools 도구(`list_pages`, `navigate_page` 등)가 보이는지도 확인한다.

## 2. Claude 표현 → Codex 대응표

본문에 나오는 Claude 쪽 이름을 아래처럼 바꿔 읽는다. 도구 이름의 실제 접두어는 세션의 도구 목록에서 확인한다.

| 본문 (Claude) | Codex |
|---|---|
| Claude | Codex |
| `~/.claude/skills/sci-retr`, `~/.claude/skills/sci-index` | `~/.codex/skills/sci-retr`, `~/.codex/skills/sci-index` |
| "Claude in Chrome" 확장 | chrome-devtools MCP (`--autoConnect` 로 평소 Chrome 에 연결) |
| 탭 목록 / 새 탭 / 탭 닫기 (`tabs_context_mcp` 등) | `list_pages` / `new_page` / `close_page`, 탭 고르기 `select_page` |
| 주소 이동 (`navigate`) | `navigate_page` |
| 페이지 스크립트 (`javascript_tool`) | `evaluate_script` (함수 형태 `() => { … }`) |
| 요소 찾기 (`find`, `read_page`) | `take_snapshot` (요소마다 uid 가 붙는다) |
| 스크린샷·확대 (`computer` screenshot·zoom) | `take_screenshot` |
| 좌표 클릭 (`computer` left_click) | 좌표 클릭 도구는 없다. `take_snapshot` 으로 버튼 uid 를 찾아 `click(uid)` |
| 여러 동작 묶음 (`browser_batch`) | 없음. 한 동작씩 호출 |
| 연결된 브라우저 고르기 (`list_connected_browsers`, `select_browser`, `onThisComputer`) | 해당 없음. `--autoConnect` 는 이 컴퓨터에서 실행 중인 Chrome 에 붙는다 |
| sonnet 하위 에이전트 (사전 분류, 색인 검수·요약) | Codex 가 직접 한다. 색인 검수·요약은 30~40편씩 나눠서 |

## 3. 수집 절차 (Codex)

파이썬 명령(`doctor`, `resolve`, `collect`, `assist`, `intake`, `status`, `reextract`, `mark`, `sci_index.py build/apply`)은 Claude 와 똑같다. 스크립트 경로만 `~/.codex/skills/sci-retr/scripts/` 로 읽는다. 순서는 `sci-retr/SKILL.md` 5절을 따른다.

웹 경로(자동 요청을 막는 출판사: 유료 Elsevier, 토큰 없는 Wiley, ACS, RSC, IOP, Science, Taylor & Francis, PNAS, AIP, Oxford, IEEE, ChemRxiv)는 두 가지다.

**A. 사용자가 직접 받기 (항상 된다)**
1. `assist` 가 만든 `_collect/manual_download.csv` 의 논문 주소를 출판사별로 보여 준다.
2. 사용자가 평소 Chrome 에서 본문 PDF 와 SI(PDF·Word)를 받아 다운로드 폴더에 둔다. 파일 이름은 바꾸지 않아도 된다.
3. `intake` 로 논문 폴더에 정리한다. 가리지 못한 파일이 있으면 무엇인지 확인한다.

**B. Codex 가 받기 (chrome-devtools, 첫 사용 때 출판사별 1편으로 확인)**
- 사이트별 선택자·누르는 순서·함정은 `sci-retr/references/web_download_playbook.md` 3절을 따른다. 누르기만 방식이 다르다.
- 누르기: `take_snapshot` 으로 버튼·링크의 uid 를 찾아 `click(uid)`. `evaluate_script` 로 요소를 찾고 위치를 확인할 수 있다.
- 링크 주소로 옮겨도 되는 곳은 `navigate_page` 가 더 확실하다(playbook 4.2절): Elsevier SI 파일 주소와 View PDF 링크 주소, ACS `/article-pdf/`·`/article-supplement/`, RSC `/article-pdf/`·`/article-supplement/`, IOP 본문 `/pdf`. Science 본문 PDF 주소로 바로 가는 것은 확인 화면이 떠서 하지 않는다.
- Chrome 이 직접 그리는 화면의 버튼(Wiley·IEEE 의 PDF "열기", Science 온라인 보기의 다운로드 아이콘)은 스냅샷에 잡히지 않을 수 있다. `take_screenshot` 으로 확인하고, 안 되면 그 논문은 A 로 넘긴다.
- 확인 창(Cloudflare 체크박스 등)이 뜨면 사용자에게 눌러 달라고 한다. Codex 는 누르지 않는다. 눌러도 반복되면 그 사이트는 멈추고 A 로 넘긴다.
- 탭은 하나만 쓰고, 그 탭을 화면 앞에 둔 채 한 편씩 받는다. 한 편이 끝나면 따로 기다리지 않고 다음 논문으로 간다.
- 받기 전에 받을 논문과 파일 목록을 출판사별로 한 번 알리고 확인을 받는다. 끝나면 `intake`.

색인은 `sci-index/SKILL.md` 대로 `sci_index.py build` → 검수·요약(Codex 가 직접, 결과를 `_collect/index_gists_<n>.csv` 로) → `apply`.

## 4. 원칙 (본문과 같음)

- 봇 탐지 우회를 하지 않는다. 확인 창은 사용자가 누르고, 쿠키 복사·User-Agent 위장·자동화 표시 숨김 같은 기법은 쓰지 않는다. 같은 IP 대역을 쓰는 기관 전체가 차단될 수 있다.
- 자동 요청을 막는 출판사에는 요청을 보내지 않는다(도구가 알아서 웹 경로로 넘긴다).
- SI 는 문서(PDF, Word)만 받는다. 동영상, 결정 구조 파일, 압축 파일, 스프레드시트는 받지 않는다.
- 자격증명은 `.env` 로만 다루고 채팅이나 출력에 값을 내지 않는다.
- 파일 다운로드는 사용자 확인 뒤에 한다. 쿠키 동의·약관 동의·로그인은 사용자에게 맡긴다.

## 5. 확인된 것과 아닌 것 (2026-09-27)

- 확인: 설치 스크립트, 파이썬으로 도는 전 과정(`doctor`, `resolve`, `collect`, `assist`, `intake`, `status`, `sci_index.py`). 에이전트와 상관없이 같다.
- Codex 에서 아직 확인하지 않음: B(Codex 가 chrome-devtools 로 웹 다운로드). 요령은 Claude in Chrome 으로 실측한 것이라 누르는 방식이 다르다. 첫 사용 때 출판사별 1편씩 해 보고, 되지 않는 출판사는 A 로 받는다. 확인한 결과는 이 절에 적는다.

## 6. 갱신

`<root>` 에서 `git pull` 한 뒤 `install.ps1 -Codex`(또는 `install.sh --codex`)를 다시 실행한다. 설정과 `.env` 는 논문 폴더에 있으므로 영향이 없다.
