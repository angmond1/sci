# sci-retr on Claude — 설치·실행 지침 (Claude 에이전트용)

> 이 문서는 Claude (Claude Code CLI / Claude Desktop 앱) 가 sci-retr 을 설치할 때 따르는 기준이다.
> 사용자가 "sci-retr 설치해줘", "이거 설치해줘" 라고 하면 추측하지 말고 아래 1번 절차를 순서대로 실행한다.

## 0. sci-retr 이 무엇인가 (한 줄)

논문 수집 skill `sci-retr` 과 색인 skill `sci-index` 두 개. DOI 목록을 받아 출판사별로 파이썬 API·직접 다운로드 또는 사용자의 Chrome("Claude in Chrome" 확장)으로 논문 PDF·SI 를 받아 폴더로 정리하고, `index.csv` 를 만든다. 자세한 것은 설치 뒤 `~/.claude/skills/sci-retr/SKILL.md`.

권장 모델: 설치와 첫 수집은 Opus. 색인 검수는 Sonnet.

## 1. 설치 절차 (에이전트가 그대로 실행)

### Step 0 — 필요한 프로그램 (Step 2 의 설치 스크립트가 확인하고, 없으면 설치)
먼저 한 줄 알리고 확인 질문 없이 진행한다: "설치에 필요한 프로그램을 확인하고, 없는 것은 바로 설치하겠습니다."

| 항목 | 확인 | 없을 때 Windows | 없을 때 macOS / Linux |
|---|---|---|---|
| Python 3.11 이상 | `py -3.12 --version`, `py -3 --version`, `python --version` (macOS/Linux `python3 --version`) | `winget install -e --id Python.Python.3.12 --source winget --scope user --silent --accept-source-agreements --accept-package-agreements` | macOS `brew install python@3.12`. Linux 는 관리자 권한이 필요해 `sudo apt install python3 python3-pip python3-venv` 를 안내 |
| Google Chrome | `chrome.exe` 기본 경로(Program Files, 사용자 AppData) | `winget install -e --id Google.Chrome --source winget --silent --accept-source-agreements --accept-package-agreements` | macOS `brew install --cask google-chrome`. Linux 는 https://www.google.com/chrome/ 안내 |
| 파이썬 패키지 | 설치 스크립트가 넣는다 | Step 2 | Step 2 (시스템 Python 에 pip 이 없거나 설치를 막으면 `~/.sci-retr/venv` 가상환경) |
| Claude in Chrome 확장 | 설치 스크립트·`doctor` 가 Chrome 프로필에서 확인 | 자동 설치 불가 → Step 3 | 같음 |
| git | 선택 | 없으면 ZIP 으로 진행. 설치를 요구하지 않는다 | 같음 |

- **Step 2 의 설치 스크립트가 Python·Chrome 확인과 설치를 스스로 한다.** 에이전트는 winget·brew 를 따로 돌리지 않고 스크립트를 실행해 출력을 읽는다. 위 표의 설치 명령은 스크립트가 실패했을 때 직접 쓰는 것이다. Python 이 없어 스크립트를 못 여는 일은 없다(PowerShell·bash 스크립트).
- Python 이 여러 버전이면 스크립트가 `py -3.12` 부터 찾아 고르고 출력의 `[확인] Python` 줄에 적는다. 이후 명령도 그 인터프리터로 실행한다.
- winget 이 없으면(새 PC 에 Microsoft Store 의 '앱 설치 관리자' 가 아직 없음) 스크립트가 알려 준다. 사용자에게 Microsoft Store 에서 '앱 설치 관리자' 를 설치하거나 https://www.python.org/downloads/ ('Add python.exe to PATH' 체크)·https://www.google.com/chrome/ 에서 직접 설치해 달라고 한 뒤 스크립트를 다시 돌린다.
- 관리자 확인 창(UAC)이 뜨면 사용자가 '예' 를 누른다. 에이전트는 누르지 않는다.
- 설치 직후 이번 세션에서 `py`·`python` 이 안 잡히면 PATH 가 아직 반영되지 않은 것이다. 스크립트는 알아서 다시 찾는다. 에이전트가 직접 부를 때는 새 터미널을 쓰거나 전체 경로(`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`)를 쓴다.
- Node.js 는 필요 없다(Claude 기준).
- 교내 망(KIST IP)에서만 유료 논문이 열린다. 밖이면 KIST VPN 을 안내한다.

### Step 1 — 폴더 위치 정하기 + 패키지 확보
1. 먼저 묻고 답을 기다린다: "프로그램 파일(수집 skill sci-retr, 색인 skill sci-index)을 어디에 둘까요? ① 기본 `C:\sci-retr`(macOS/Linux `~/sci-retr`) ② 다른 위치. 논문을 저장할 폴더는 수집할 때 따로 정합니다." 사용자가 기본이라고 하거나 원하는 곳이 따로 없다고 하면 기본 위치.
2. 패키지를 그 폴더에 확보한다.
   - git 있으면 `git clone https://github.com/angmond1/sci.git <root>`.
   - git 없으면 GitHub 페이지에서 `Code ▾ → Download ZIP` 을 받아 그 폴더에 푼다. 공개 저장소라 로그인은 필요 없다.
   - 동료에게 받은 폴더면 그대로 쓴다.

### Step 2 — skill 설치
현재 OS 를 판단해 하나만 실행한다.
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File <root>\install.ps1`
- macOS / Linux: `bash <root>/install.sh`. Windows 의 Git Bash 에서 실행해도 install.ps1 로 넘어간다.
- skill 을 다른 곳에 설치하려면 `-Dest <폴더>`(Windows 만, 기본 `~/.claude/skills`).

스크립트가 하는 일은 네 단계다.
1. 필요한 프로그램 확인과 설치: Python 3.11 이상, Google Chrome (Step 0 표).
2. `sci-retr`, `sci-index` 를 `~/.claude/skills/` 로 복사.
3. 파이썬 패키지(requests, pymupdf, truststore, beautifulsoup4, lxml, openpyxl, wiley-tdm, playwright) 설치. 권한 문제면 `--user` 로 다시 한다. macOS/Linux 에서 시스템 Python 에 pip 이 없거나(Ubuntu 24.04 기본 상태) 설치를 막으면 `~/.sci-retr/venv` 가상환경에 설치한다.
4. 환경 점검(`doctor`) 실행. Claude in Chrome 확장이 없으면 Chrome 웹스토어 페이지를 연다.

출력 끝의 `▼・ᴥ・▼  sci-retr 설치 완료` 와 점검 결과를 읽고, `[문제]` 로 나온 것과 새로 설치한 프로그램을 사용자에게 알린다. 프로그램을 설치하지 않고 확인만 하려면 `-NoAutoInstall`(install.sh 는 `--no-auto-install`). 가상환경에 설치했으면 이후 모든 명령을 `~/.sci-retr/venv/bin/python` 으로 실행한다. `ModuleNotFoundError` 가 나면 다른 인터프리터(`py -3.12`, `python3.12` 등)로 같은 명령을 다시 시도한다.

### Step 3 — "Claude in Chrome" 확장
확장은 자동으로 설치할 수 없다. 설치 스크립트가 확장이 없으면 웹스토어 페이지를 열어 준다. 사용자에게 'Chrome에 추가' 를 누르고 Claude 계정으로 로그인해 달라고 한다. 주소: https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn . Claude 데스크탑 앱(Code 탭 포함)은 좌하단 이니셜 클릭 → "설정" → 좌측 탭 "Claude in Chrome 설정" → "Claude in Chrome 사용설정" 켜기(설정 첫 화면에는 안 보인다). 터미널의 Claude Code CLI 는 `claude --chrome` 으로 시작한다. 세션에서 `list_connected_browsers` 가 이 컴퓨터의 브라우저를 돌려주면 성공. 같은 계정으로 확장을 켠 다른 컴퓨터도 목록에 나오므로 이 컴퓨터 것(`onThisComputer`)만 쓴다.

### Step 4 — Chrome 설정 두 가지 (사용자가 직접)
> "Chrome 에서 두 가지를 바꿔 주세요. ① `chrome://settings/content/pdfDocuments` 에서 'PDF 다운로드' 선택 ② `chrome://settings/downloads` 에서 '다운로드 전에 각 파일의 저장 위치 확인' 끄기. 이래야 PDF 가 저장 창 없이 다운로드 폴더로 바로 들어갑니다."

### Step 5 — 재시작 (반드시 안내)
`~/.claude/skills/` 에 새 skill 폴더가 생기면 그 세션에서는 인식되지 않는다.
> "설치 완료. Claude 를 재시작한 뒤 `sci-retr 점검해줘` 라고 해주세요."

### Step 6 — 점검 (재시작 뒤 첫 대화)
`python ~/.claude/skills/sci-retr/scripts/sci_collect.py doctor --kb-root <논문 폴더>` 를 돌려(가상환경에 설치했으면 `python` 대신 `~/.sci-retr/venv/bin/python`) "문제 0" 을 확인한다. 논문 폴더를 아직 정하지 않았으면 `--kb-root` 에 임시 폴더(예: `%TEMP%\sci-retr-check`, macOS/Linux `/tmp/sci-retr-check`)를 준다. 논문 폴더는 수집할 때 정한다(SKILL.md 5.0). 문제가 있으면 출력의 안내대로 고친 뒤 다시 돌린다. 키·토큰(선택)은 `sci-retr/examples/.env.example` 을 논문 폴더의 `.env` 로 복사해 채우게 안내하되, 값은 채팅에 적지 않게 한다.

## 2. 실행
사용자가 DOI 목록이나 "논문 받아줘" 라고 하면 `sci-retr` skill 지침(SKILL.md)을 따른다. 수집 전에 저장 폴더를 묻고 확인하며(5.0), 수집이 끝나면 30편을 넘을 때 색인 여부를 묻고 30편 이하면 생략을 알린다(5.7).

## 3. 갱신
`<root>` 에서 `git pull` 한 뒤 Step 2 의 설치 스크립트를 다시 실행한다. 설정과 `.env` 는 논문 폴더에 있으므로 영향이 없다.
