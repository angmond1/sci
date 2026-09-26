# sci-retr on Claude — 설치·실행 지침 (Claude 에이전트용)

> 이 문서는 Claude (Claude Code CLI / Claude Desktop 앱) 가 sci-retr 을 설치할 때 따르는 기준이다.
> 사용자가 "sci-retr 설치해줘", "이거 설치해줘" 라고 하면 추측하지 말고 아래 1번 절차를 순서대로 실행한다.
> Codex 사용자는 [CODEX.md](CODEX.md).

## 0. sci-retr 이 무엇인가 (한 줄)

논문 수집 skill `sci-retr` 과 색인 skill `sci-index` 두 개. DOI 목록을 받아 출판사별로 파이썬 API·직접 다운로드 또는 사용자의 Chrome("Claude in Chrome" 확장)으로 논문 PDF·SI 를 받아 폴더로 정리하고, `index.csv` 를 만든다. 자세한 것은 설치 뒤 `~/.claude/skills/sci-retr/SKILL.md`.

권장 모델: 설치와 첫 수집은 Opus. 색인 검수는 Sonnet.

## 1. 설치 절차 (에이전트가 그대로 실행)

### Step 0 — 실행 환경
- Python 3.11 이상. 확인: Windows `py -3 --version`, macOS/Linux `python3 --version`. 없으면 Windows 는 `winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements`, macOS 는 `brew install python@3.12`(Homebrew 없으면 python.org 설치 파일).
- git 은 있으면 쓰고 없으면 ZIP 으로 진행한다. 설치를 요구하지 않는다.
- 교내 망(KIST IP)에서만 유료 논문이 열린다. 밖이면 KIST VPN 을 안내한다.

### Step 1 — 폴더 위치 정하기 + 패키지 확보
1. 먼저 묻는다: "sci-retr 을 어디에 둘까요? ① 기본 `C:\sci-retr`(macOS/Linux `~/sci-retr`) ② 다른 위치". 답이 없으면 기본.
2. 패키지를 그 폴더에 확보한다.
   - git 있으면 `git clone https://github.com/angmond1/sci-retr.git <root>`.
   - git 없으면 GitHub 페이지에서 `Code ▾ → Download ZIP` 을 받아 그 폴더에 푼다(collaborator 권한 필요).
   - 동료에게 받은 폴더면 그대로 쓴다.

### Step 2 — skill 설치
현재 OS 를 판단해 하나만 실행한다.
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File <root>\install.ps1`
- macOS / Linux: `bash <root>/install.sh`

스크립트가 `sci-retr`, `sci-index` 를 `~/.claude/skills/` 로 복사하고 파이썬 패키지(requests, pymupdf, truststore, beautifulsoup4, lxml, openpyxl, wiley-tdm, playwright)를 설치한다. `ModuleNotFoundError` 가 나면 다른 인터프리터(`py -3.12`, `python3.12` 등)로 같은 명령을 다시 시도한다.

### Step 3 — "Claude in Chrome" 확장
Chrome 웹스토어 https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn 에서 설치하고 Claude 계정으로 로그인한다. Claude Desktop 은 설정 → "Claude in Chrome" 켜기, Claude Code 는 `claude --chrome`. 세션에서 `list_connected_browsers` 가 이 컴퓨터의 브라우저를 돌려주면 성공. 같은 계정으로 확장을 켠 다른 컴퓨터도 목록에 나오므로 이 컴퓨터 것(`onThisComputer`)만 쓴다.

### Step 4 — Chrome 설정 두 가지 (사용자가 직접)
> "Chrome 에서 두 가지를 바꿔 주세요. ① `chrome://settings/content/pdfDocuments` 에서 'PDF 다운로드' 선택 ② `chrome://settings/downloads` 에서 '다운로드 전에 각 파일의 저장 위치 확인' 끄기. 이래야 PDF 가 저장 창 없이 다운로드 폴더로 바로 들어갑니다."

### Step 5 — 재시작 (반드시 안내)
`~/.claude/skills/` 에 새 skill 폴더가 생기면 그 세션에서는 인식되지 않는다.
> "설치 완료. Claude 를 재시작한 뒤 `sci-retr 점검해줘` 라고 해주세요."

### Step 6 — 점검 (재시작 뒤 첫 대화)
`python ~/.claude/skills/sci-retr/scripts/sci_collect.py doctor --kb-root <논문 폴더>` 를 돌려 "문제 0" 을 확인한다. 문제가 있으면 출력의 안내대로 고친 뒤 다시 돌린다. 키·토큰(선택)은 `sci-retr/examples/.env.example` 을 논문 폴더의 `.env` 로 복사해 채우게 안내하되, 값은 채팅에 적지 않게 한다.

## 2. 실행
사용자가 DOI 목록이나 "논문 받아줘" 라고 하면 `sci-retr` skill 지침(SKILL.md)을 따른다. 수집이 끝나면 `sci-index` 로 색인한다.

## 3. 갱신
`<root>` 에서 `git pull` 한 뒤 Step 2 의 설치 스크립트를 다시 실행한다. 설정과 `.env` 는 논문 폴더에 있으므로 영향이 없다.
