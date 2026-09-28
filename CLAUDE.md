# sci-retr on Claude — 설치·실행 지침 (Claude 에이전트용)

> 이 문서는 Claude (Claude Code CLI / Claude Desktop 앱) 가 sci-retr 을 설치하고 쓸 때 따르는 기준이다.
> 사용자가 "https://github.com/angmond1/sci 설치해줘", "sci-retr 설치해줘", "이거 설치해줘" 라고 하면 추측하지 말고 아래 1번 절차를 순서대로 실행한다.
> 공용 skill 본문(SKILL.md·요령 문서)은 Claude 와 Codex 가 함께 읽는다. 그중 Codex 기준으로 적힌 동작(CAPTCHA 풀이, Computer Use, 쿠키 배너 처리)을 Claude 에서 어떻게 하는지는 2.1 에 둔다. Codex 지침은 [CODEX.md](CODEX.md).
> 갱신 기준: 2026-09-28, 소스 `5174c57`, 패키지 `VERSION` 0.2.1.

## 0. sci-retr 이 무엇인가 (한 줄)

논문 수집 skill `sci-retr`, 색인 skill `sci-index`, 한국어 한 줄 요약 skill `sci-tldr`(사용자가 원할 때만) 세 개. DOI 목록을 받아 출판사별로 파이썬 API·직접 다운로드 또는 사용자의 Chrome("Claude in Chrome" 확장)으로 논문 PDF·SI 를 받아 폴더로 정리하고, `index.csv` 를 만든다. 자세한 것은 설치 뒤 `~/.claude/skills/sci-retr/SKILL.md`.

권장 모델(README 구성 표): `sci-retr` 는 Opus, `sci-index`·`sci-tldr` 는 Sonnet. 색인은 LLM 없이 스크립트로 끝난다. 한 줄 요약은 전용 에이전트 `sci-tldr-writer`(sonnet, 도구 Read·Write)가 쓴다. 웹 다운로드는 전용 에이전트 `sci-retr-web`(sonnet·추론 medium, 도구 Chrome·Bash·Read) 하나가 목록 끝까지 받는다.

웹 다운로드 중 확인 창(CAPTCHA)이 뜨면 Claude 에서는 사용자가 대신 눌러 준다(README 첫머리 ⚠️). 처리 순서는 2.1.

## 1. 설치 절차 (에이전트가 그대로 실행)

### Step 0 — 필요한 프로그램 (Step 2 의 설치 스크립트가 확인하고, 없으면 설치)
먼저 한 줄 알리고 확인 질문 없이 진행한다: "설치에 필요한 프로그램을 확인하고, 없는 것은 바로 설치하겠습니다." 에이전트가 미리 확인할 필요는 없다. Step 2 스크립트가 아래 표의 확인을 똑같이 한다(Node.js 만 예외, Step 3.2).

| 항목 | 확인 | 없을 때 Windows | 없을 때 macOS / Linux |
|---|---|---|---|
| Python 3.11 이상 | `py -3.12 --version`, `py -3 --version`, `python --version` (macOS/Linux `python3 --version`) | `winget install -e --id Python.Python.3.12 --source winget --scope user --silent --accept-source-agreements --accept-package-agreements` | macOS `brew install python@3.12`. Linux 는 관리자 권한이 필요해 `sudo apt install python3 python3-pip python3-venv` 를 안내 |
| Google Chrome | `chrome.exe` 기본 경로(Program Files, 사용자 AppData) | `winget install -e --id Google.Chrome --source winget --silent --accept-source-agreements --accept-package-agreements` | macOS `brew install --cask google-chrome`. Linux 는 https://www.google.com/chrome/ 안내 |
| 파이썬 패키지 | 설치 스크립트가 넣는다 | Step 2 | Step 2 (시스템 Python 에 pip 이 없거나 설치를 막으면 `~/.sci-retr/venv` 가상환경) |
| Claude in Chrome 확장 | 설치 스크립트·`doctor` 가 Chrome 프로필에서 확인 | 자동 설치 불가 → Step 3.1 | 같음 |
| Node.js LTS (chrome-devtools MCP 용) | `node --version` (설치 스크립트는 확인하지 않음) | `winget install -e --id OpenJS.NodeJS.LTS --source winget --silent --accept-source-agreements --accept-package-agreements` | macOS `brew install node`. Linux 는 https://nodejs.org/ 안내 |
| git | 선택 | 없으면 ZIP 으로 진행. 설치를 요구하지 않는다 | 같음 |

- **Step 2 의 설치 스크립트가 Python·Chrome 확인과 설치를 스스로 한다.** 에이전트는 winget·brew 를 따로 돌리지 않고 스크립트를 실행해 출력을 읽는다. 위 표의 설치 명령은 스크립트가 실패했을 때 직접 쓰는 것이다. Python 이 없어 스크립트를 못 여는 일은 없다(PowerShell·bash 스크립트).
- Python 이 여러 버전이면 스크립트가 `py -3.12` 부터 찾아 고르고 출력의 `[확인] Python` 줄에 적는다. 이후 명령도 그 인터프리터로 실행한다.
- winget 이 없으면(새 PC 에 Microsoft Store 의 '앱 설치 관리자' 가 아직 없음) 스크립트가 알려 준다. 사용자에게 Microsoft Store 에서 '앱 설치 관리자' 를 설치하거나 https://www.python.org/downloads/ ('Add python.exe to PATH' 체크)·https://www.google.com/chrome/ 에서 직접 설치해 달라고 한 뒤 스크립트를 다시 돌린다.
- 관리자 확인 창(UAC)이 뜨면 사용자가 '예' 를 누른다. 에이전트는 누르지 않는다.
- 설치 직후 이번 세션에서 `py`·`python` 이 안 잡히면 PATH 가 아직 반영되지 않은 것이다. 스크립트는 알아서 다시 찾는다. 에이전트가 직접 부를 때는 새 터미널을 쓰거나 전체 경로(`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`)를 쓴다.
- Node.js 는 chrome-devtools MCP(Step 3.2)에만 쓰인다. 설치 스크립트는 확인·설치하지 않으므로 Step 3.2 에서 확인하고, 없으면 위 표의 명령으로 설치한다.
- 교내 망(KIST IP)에서만 유료 논문이 열린다. 밖이면 KIST VPN 을 안내한다.

### Step 1 — 폴더 위치 정하기 + 패키지 확보
1. 먼저 묻고 답을 기다린다: "프로그램 파일(수집 skill sci-retr, 색인 skill sci-index, 한 줄 요약 skill sci-tldr)을 어디에 둘까요? ① 기본 `C:\sci`(macOS/Linux `~/sci`) ② 다른 위치. 논문을 저장할 폴더는 수집할 때 따로 정합니다." 사용자가 기본이라고 하거나 원하는 곳이 따로 없다고 하면 기본 위치.
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
2. `sci-retr`, `sci-index`, `sci-tldr` 를 `~/.claude/skills/` 로 복사하고, 한 줄 요약 전용 에이전트 `sci-tldr/agents/sci-tldr-writer.md` 와 웹 다운로드 전용 에이전트 `sci-retr/agents/sci-retr-web.md` 를 `~/.claude/agents/` 로 복사(Codex 설치 때는 하지 않음).
3. 파이썬 패키지(requests, pymupdf, truststore, beautifulsoup4, lxml, openpyxl, playwright) 설치. 권한 문제면 `--user` 로 다시 한다. macOS/Linux 에서 시스템 Python 에 pip 이 없거나(Ubuntu 24.04 기본 상태) 설치를 막으면 `~/.sci-retr/venv` 가상환경에 설치한다.
4. 환경 점검(`doctor`) 실행. Claude in Chrome 확장이 없으면 Chrome 웹스토어 페이지를 연다.

출력 끝의 `▼・ᴥ・▼  sci-retr 설치 완료` 와 점검 결과를 읽고, `[문제]` 로 나온 것과 새로 설치한 프로그램을 사용자에게 알린다. 프로그램을 설치하지 않고 확인만 하려면 `-NoAutoInstall`(install.sh 는 `--no-auto-install`). 이후 명령은 설치 스크립트가 `sci-retr/python.txt` 에 적어 둔 Python 으로 실행한다(가상환경에 설치했으면 `~/.sci-retr/venv/bin/python`). `ModuleNotFoundError` 가 나면 다른 인터프리터(`py -3.12`, `python3.12` 등)로 같은 명령을 다시 시도한다.

### Step 3 — 브라우저 도구 두 가지
둘 다 사용자가 평소 쓰는 Chrome 에 붙인다. 도구가 따로 띄운 Chrome(별도 프로필)은 웹 경로에 쓰지 않는다. 그런 Chrome 에서는 Elsevier·Wiley 확인 창이 반복되고 RSC 는 PDF 가 거부됐다(2026-09-24 실측).

#### 3.1 "Claude in Chrome" 확장 — 웹 다운로드 도구
SKILL.md 5.5 와 전용 에이전트 `sci-retr-web` 이 이 확장으로 받는다. 확장은 자동으로 설치할 수 없다. 설치 스크립트가 확장이 없으면 웹스토어 페이지를 열어 준다. 사용자에게 'Chrome에 추가' 를 누르고 Claude 계정으로 로그인해 달라고 한다. 주소: https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn . Claude 데스크탑 앱(Code 탭 포함)은 좌하단 이니셜 클릭 → "설정" → 좌측 탭 "Claude in Chrome 설정" → "Claude in Chrome 사용설정" 켜기(설정 첫 화면에는 안 보인다). 터미널의 Claude Code CLI 는 `claude --chrome` 으로 시작한다. 세션에서 `list_connected_browsers` 가 이 컴퓨터의 브라우저를 돌려주면 성공. 같은 계정으로 확장을 켠 다른 컴퓨터도 목록에 나오므로 이 컴퓨터 것(`onThisComputer`)만 쓴다.

#### 3.2 chrome-devtools MCP — 보조 도구 (README 준비물, 2026-09-28)
설치 중 이 단계에 오거나 사용자가 "chrome-devtools mcp 설치해서 사용가능하게 해줘" 라고 하면, 한 줄 알리고 다음을 한다.
1. Node.js 를 확인한다(Step 0 표).
2. 사용자 범위로 등록한다. **`--autoConnect` 를 꼭 붙인다.** 실행 중인 사용자 Chrome(기본 프로필)에 붙는 옵션이다. 빠지면 도구가 별도 프로필의 새 Chrome 을 띄운다.
   - Windows: `claude mcp add --scope user chrome-devtools -- cmd /c npx -y chrome-devtools-mcp@latest --autoConnect`
   - macOS / Linux: `claude mcp add --scope user chrome-devtools -- npx -y chrome-devtools-mcp@latest --autoConnect`
   - 먼저 `claude mcp list` 로 같은 이름이 있는지 본다. 있으면 중복 등록하지 않고 인자에 `--autoConnect` 가 있는지만 확인한다. Claude 플러그인 목록의 `chrome-devtools-mcp` 플러그인은 이 옵션 없이 실행돼 새 Chrome 을 띄우므로 웹 경로에 쓰지 않는다.
   - `claude` 명령을 찾지 못하면 등록하지 않고 사용자에게 알린다. 웹 다운로드는 3.1 의 확장만으로도 된다.
3. 사용자에게 부탁한다: Chrome(144 이상)에서 `chrome://inspect/#remote-debugging` 을 열어 원격 디버깅을 켜고, MCP 가 처음 붙을 때 Chrome 이 띄우는 연결 허용 창에서 허용.
4. Claude 를 다시 시작한 뒤 `list_pages` 가 사용자가 열어 둔 탭을 돌려주면 성공. `DevToolsActivePort` 오류나 연결 시간 초과는 Chrome 이 꺼져 있거나 3의 원격 디버깅이 꺼진 것이다.
5. 쓰임: 받는 순서는 3.1 의 확장으로 한다(SKILL.md 5.5). chrome-devtools 는 메인이 보조로 쓴다 — 같은 Chrome 에 붙었는지 확인(`list_pages`), 작업 탭을 앞으로 가져오기(`select_page` 의 `bringToFront`, 확장으로는 못 한다), 약 1,000자에서 잘리는 확장 스크립트 출력 대신 긴 결과 읽기(`evaluate_script`). 도구 이름 대응은 CODEX.md 3절 표.

### Step 4 — Chrome 설정 두 가지 (점검에서 [문제] 로 나올 때만, 사용자가 직접)
> "Chrome 에서 두 가지를 바꿔 주세요. ① `chrome://settings/content/pdfDocuments` 에서 'PDF 다운로드' 선택 ② `chrome://settings/downloads` 에서 '다운로드 전에 각 파일의 저장 위치 확인' 끄기. 이래야 PDF 가 저장 창 없이 다운로드 폴더로 바로 들어갑니다."

### Step 5 — 새 대화 안내 (반드시)
새 skill 은 새 대화(세션)부터 인식된다. 설치 스크립트의 끝 안내와 같은 문구로 알린다.
> "설치 완료. 새 대화를 열거나 Claude 를 다시 시작한 뒤, 논문 목록 파일(Web of Science·Scopus 내보내기 또는 DOI 목록)을 대화창에 끌어다 놓고 'sci-retr 스킬로 논문 수집해줘' 라고 해 주세요."
> 이어서 알린다(2026-09-27 사용자 지시): "특정 주제의 논문 목록은 Web of Science 나 Scopus 에서 검색해 내보내기(Export)로 만들 수 있습니다. Web of Science: https://www.webofscience.com/wos/woscc/smart-search , Scopus: https://www.scopus.com/pages/home#basic"
> 마지막으로 README 의 주의 두 가지: "웹 다운로드 중 확인 창(CAPTCHA)이 뜨면 알려 드릴 테니 그 탭에서 통과시켜 주세요. 처음 한두 번은 과정을 지켜보시면서 잘못된 점을 알려 주시면 좋습니다."

### Step 6 — 점검 (사용자가 요청할 때)
설치 스크립트가 이미 점검했으므로 따로 하지 않아도 된다. 사용자가 "sci-retr 점검해줘" 라고 하면 다음을 돌린다.
`python ~/.claude/skills/sci-retr/scripts/sci_collect.py doctor --kb-root <논문 폴더>` 를 돌려(가상환경에 설치했으면 `python` 대신 `~/.sci-retr/venv/bin/python`) "문제 0" 을 확인한다. 논문 폴더를 아직 정하지 않았으면 `--kb-root` 에 임시 폴더(예: `%TEMP%\sci-retr-check`, macOS/Linux `/tmp/sci-retr-check`)를 준다. 논문 폴더는 수집할 때 정한다(SKILL.md 5.0). 문제가 있으면 출력의 안내대로 고친 뒤 다시 돌린다. 키·토큰(선택)은 수집 목록에 Elsevier OA·Wiley 논문이 있을 때 안내한다(SKILL.md 3.2.1). 값은 사용자가 skill 폴더의 `token.txt` 에 직접 넣고, 채팅창에는 절대 적지 않게 한다.

## 2. 실행
사용자가 DOI 목록이나 "논문 받아줘" 라고 하면 `sci-retr` skill 지침(SKILL.md)을 따른다. 수집 전에 저장 폴더를 묻고 확인하며(5.0), 수집이 끝나면 편수와 관계없이 색인(sci-index, 몇 초)을 바로 만들고, 한국어 한 줄 요약(sci-tldr)은 한 번 물어 원할 때만 한다(5.7). 논문 PDF·링크를 주며 참고문헌 수집을 부탁하면 SKILL.md 5.10(`refs`).

### 2.1 Claude 에서 다르게 하는 것
공용 SKILL.md·요령 문서의 아래 대목은 Codex 기준으로 적혀 있다(CODEX.md 3.2). Claude 에서는 이렇게 한다.

- **확인 창·CAPTCHA** (SKILL.md 2절 5·5.5, 요령 문서 2.1 의 '직접 풀이'): README 안내대로 사용자가 눌러 준다. 확인 창이 뜬 탭은 닫거나 다른 주소로 옮기지 않고 그대로 두고, 어느 사이트의 어느 탭인지 사용자에게 알린다. 기다리는 동안 다른 출판사는 새 탭에서 받는다. 사용자가 통과했다고 하거나 그 탭 제목이 논문 페이지로 바뀌면 그 탭에서 이어 받는다. 끝까지 통과하지 못한 논문은 DOI 와 함께 최종 보고한다.
- **메인과 `sci-retr-web`** (SKILL.md 5.5 의 3): 에이전트가 `확인 창: …` 이나 `창 최소화` 를 보내면 메인은 사용자에게 그대로 전하고, 사용자가 통과했다(창을 앞으로 가져왔다)고 하면 SendMessage 로 에이전트에게 알린다. 에이전트가 끝나면 바로 색인(5.7)으로 간다.
- **쿠키 동의 창**: 누르지 않는다(`sci-retr-web` 정의와 같다). 창이 클릭을 막으면 스크립트로 읽은 PDF·SI 링크 주소로 탭을 옮겨 받고(요령 문서 2.2·3.14), 그래도 안 되면 사용자에게 알린다.
- **Computer Use·ChatGPT Chrome 확장**: Codex 준비물이다. Claude 는 Step 3 의 두 도구를 쓴다.

## 3. 갱신
`<root>` 에서 `git pull` 한 뒤 Step 2 의 설치 스크립트를 다시 실행한다. 설치본은 복사본이라 `git pull` 만으로는 바뀌지 않는다. 스크립트가 세 skill 과 전용 에이전트 두 개를 다시 복사하고, 새 대화부터 반영된다. chrome-devtools MCP 등록(Step 3.2)은 다시 하지 않는다. 설정과 `.env` 는 논문 폴더에 있고, 설치 스크립트는 skill 폴더의 `token.txt` 를 남겨 두므로 영향이 없다. 논문은 기본으로 `<root>\papers\<주제>` 에 쌓이고 git 이 무시하므로 `git pull` 에도 그대로다. `<root>` 폴더를 지우고 다시 받지 않는다(논문이 함께 지워진다).
