# sci-retr on Codex — 설치·실행 지침 (Codex 에이전트용)

> 이 문서는 Codex Desktop / Codex CLI 가 [sci-retr 패키지](https://github.com/angmond1/sci)를 설치하고 사용할 때 읽는 지침이다. 사용자가 “sci-retr 설치해줘”라고 하면 1절부터 진행한다.
> 공용 skill 본문은 Claude 기준이다. 수집은 [sci-retr/SKILL.md](sci-retr/SKILL.md), 색인은 [sci-index/SKILL.md](sci-index/SKILL.md), 선택 사항인 한국어 한 줄 요약은 [sci-tldr/SKILL.md](sci-tldr/SKILL.md)를 따른다. 도구·모델·경로 차이는 이 문서를 적용한다. [CLAUDE.md](CLAUDE.md)는 Claude 설치용이다.
> 갱신 기준: 2026-09-28, 소스 `822971b`, 패키지 `VERSION` 0.2.1. `a29fff0`까지의 수집 기능과 이후 README의 Codex 우선 설치 안내를 반영했다. Codex에서 확인한 범위와 Claude 쪽 시험 기록은 7절에 구분한다.

## 0. 구성과 적용 범위

`sci-retr` 는 DOI 목록이나 WoS·Scopus 검색 결과로 논문 PDF·본문 텍스트·SI 를 수집하고, `refs` 로 원 논문의 참고문헌 DOI 목록도 만든다. 수집이 끝나면 **편수와 관계없이 `sci-index` 로 색인을 바로 만든다.** 색인 생성 여부는 묻지 않는다. 한국어 한 줄 요약은 그 뒤 한 번 물어 사용자가 원할 때만 `sci-tldr` 로 만든다.

사용자가 “sci-retr 스킬로 논문을 수집해줘”처럼 수집을 명령하면 자동 경로와 웹 다운로드뿐 아니라 CAPTCHA·확인 창의 클릭과 문제 풀이까지 포함해 요청 범위를 끝까지 처리하라는 승인이다. Codex는 웹 다운로드 목록이나 CAPTCHA 처리 여부를 중간에 다시 묻지 않는다. 정상 화면의 UI를 직접 사용하고, 외부 CAPTCHA 풀이 서비스·토큰 추출·응답 위조는 쓰지 않는다. 반복해도 현재 도구로 통과할 수 없는 DOI만 시도 결과와 함께 최종 보고하고, 나머지 목록은 계속 처리한다.

세 skill 을 함께 설치한다. 세 CLI 는 모두 **`sci-retr/scripts/`** 에 있다.

| skill | CLI | 역할 |
|---|---|---|
| `sci-retr` | `sci_collect.py` | 수집·정리·참고문헌 목록 |
| `sci-index` | `sci_index.py build` | 서지정보 색인·결정적 검수. LLM 없음 |
| `sci-tldr` | `sci_tldr.py prep/apply` | 요약 재료 준비·검증·병합. 한국어 문장은 LLM 이 작성 |

배포 저장소는 `angmond1/sci` 다. 기존 로컬 폴더 `D:\repo\sci-retr` 는 그대로 쓴다.

- README 의 권장모델은 Codex / Claude 순서로 `sci-retr` Sol High / Opus, `sci-index`·`sci-tldr` Luna / Sonnet 이다. sci-retr의 Codex 권장 effort는 **High**다. 권장값이며 현재 세션 모델을 자동으로 바꾸지는 않는다. 2026-09-27 웹 경로 검증은 Sol Medium으로 수행했다. 하위 에이전트도 별도 지정이 없으면 세션 기본값을 따른다.
- 이 문서는 설치 스크립트가 복사하는 세 skill 폴더 밖에 있다. `CODEX.md` 라는 이름만으로 자동 로드된다고 가정하지 않는다. README 설치 절은 Codex 에 이 문서를 읽도록 안내한다. 설치 완료 때도 절대경로를 남기고 새 대화에서 먼저 읽도록 한다.
- 예시 요청: “`<패키지 폴더>/CODEX.md` 를 먼저 읽고, sci-retr 로 이 목록의 논문을 `<논문 폴더>` 에 수집해줘.” 이후 공용 skill 을 읽어 실행한다.

## 1. 설치

### 1.1 실행 환경과 패키지 폴더

1. 사용자가 준 패키지 폴더가 있으면 그대로 쓴다. 없으면 “프로그램 파일을 어디에 둘까요? 기본은 Windows `C:\sci`, macOS/Linux `~/sci` 입니다.”라고 묻고 답을 기다린다. 논문을 저장할 폴더는 수집할 때 확인한다.
2. “설치에 필요한 프로그램을 확인하고, 없는 것은 바로 설치하겠습니다.”라고 알린다. Python 3.11 이상·Google Chrome 확인과 설치는 1.2 의 설치 스크립트가 한다. 에이전트가 같은 점검이나 winget·brew 설치를 먼저 반복하지 않는다.
3. 패키지가 없으면 `git clone https://github.com/angmond1/sci.git <패키지 폴더>` 로 받는다. git 이 없으면 GitHub 의 `Code → Download ZIP` 으로 받아 푼다. 동료에게 받은 폴더도 쓸 수 있다.
4. 웹 다운로드에는 Codex 앱의 `chrome-devtools` MCP와 ChatGPT Chrome 확장을 설치하고, Codex 설정의 **컴퓨터 사용 → Google Chrome 사용**을 켠다. 수동으로 `npx` 기반 MCP를 등록할 때만 Node.js LTS·npm이 추가로 필요하다. Python 수집·색인과 사용자의 직접 다운로드에는 MCP가 필수가 아니다.

### 1.2 세 skill 설치

**아래 예시는 경로를 실제 선택값으로 바꿔 실행한다.** 기존 설치 폴더에 개인 수정이 있으면 먼저 패키지의 `_history/` 아래에 보관한다. 설치 스크립트는 대상 `sci-retr`, `sci-index`, `sci-tldr` 폴더를 교체하므로, 대상의 절대경로와 링크 여부를 확인하고 실행한다. 패키지 원본 폴더를 설치 대상으로 지정하지 않는다.

Windows (PowerShell):

```powershell
$packageRoot = 'C:\sci'  # 예시. 이미 받은 폴더가 있으면 그 경로
$retrCodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillBase = Join-Path $retrCodexHome 'skills'
powershell -ExecutionPolicy Bypass -File "$packageRoot\install.ps1" -Codex -Dest "$skillBase"
```

macOS / Linux:

```bash
package_root="$HOME/sci"  # 예시. 이미 받은 폴더가 있으면 그 경로
skill_base="${CODEX_HOME:-$HOME/.codex}/skills"
bash "$package_root/install.sh" --codex
```

- `-Codex` / `--codex` 를 생략하면 Claude 경로에 설치된다. Codex 옵션의 기본 목적지는 `$CODEX_HOME/skills`, 환경변수가 없으면 `~/.codex/skills` 다.
- 스크립트는 **프로그램 확인·설치 → 세 skill 복사 → pip 패키지 설치 → `doctor` 점검** 순서로 실행한다. 패키지는 `requests`, `pymupdf`, `truststore`, `beautifulsoup4`, `lxml`, `openpyxl`, `playwright` 일곱 개다. `wiley-tdm` 은 설치 목록·점검에서 빠졌으며, Wiley TDM API 는 `requests` 로 직접 부른다.
- Windows 는 Python·Chrome 이 없으면 winget 의 `Python.Python.3.12`·`Google.Chrome` 을 설치한다(`--source winget`, Python 은 먼저 `--scope user`). winget 이 없거나 설치가 실패하면 출력의 수동 설치 안내를 따른다. UAC 창은 사용자가 처리한다. pip 실패 시에는 `--user` 로 한 번 더 시도한다.
- macOS 는 Homebrew 가 있을 때 `python@3.12`·`--cask google-chrome` 을 설치한다. Linux 는 필요한 시스템 프로그램의 설치 방법을 안내한다. macOS/Linux 에서 pip 이 없거나 시스템 Python 설치가 제한되면 `~/.sci-retr/venv` 에 패키지를 넣는다. Windows Git Bash 에서는 `install.ps1` 로 넘긴다.
- `-NoAutoInstall` / `--no-auto-install` 은 Python·Chrome 자동 설치를 끈다. **전체 스크립트의 dry-run 은 아니다.** 이미 필요한 프로그램이 있으면 skill 복사·pip 설치·점검은 진행한다.
- Windows 의 Python 탐색 순서는 `py -3.12 → py -3.13 → py -3.11 → py -3 → python → python3`, 이후 사용자 설치 경로의 Python312·313·311 이다. 셸 스크립트는 `python3.12 → python3.13 → python3.11 → python3 → python` 순으로 3.11 이상을 찾는다. 설치 직후 PATH 미반영도 구분한다.
- 선택한 Python 실행 파일의 절대경로는 **`<skillBase>/sci-retr/python.txt`** 에 기록한다. 가상환경을 썼으면 그 경로다. 이후 수집·색인·요약 CLI 는 모두 이 인터프리터로 실행한다. `ModuleNotFoundError` 가 나면 먼저 이 파일과 해당 Python 의 패키지를 확인한다. `python.txt` 가 없는 이전 설치에서만 동작하는 인터프리터를 별도로 찾는다.
- 재설치 때 기존 설치본의 `token.txt` 는 보존한다. 원본의 `token.txt`, `python.txt`, `_history`, `__pycache__` 는 복사하지 않는다. `-Codex` / `--codex` 는 Claude 확장 설치 안내·웹스토어 열기를 건너뛴다. Node.js 설치·MCP 등록·ChatGPT Chrome 확장 설치는 하지 않으므로 README 준비물 3~4번을 별도로 따른다.
- Claude 설치에만 전용 에이전트 `sci-tldr/agents/sci-tldr-writer.md` 와 `sci-retr/agents/sci-retr-web.md` 를 `~/.claude/agents/` 로 추가 복사한다. **Codex 옵션은 둘 다 추가 복사하지 않는다.** skill 안의 정의 파일이 함께 복사돼도 Codex 에이전트로 등록된 것은 아니다. 웹 목록은 5절, 요약은 6.2 의 주 에이전트 처리 방법을 쓴다.

**Codex 의 skill 검색 경로는 실행 환경에서 확인한다.** 이 PC 의 현재 세션은 `~/.codex/skills` 를 읽는다. 한편 [OpenAI 공식 skill 문서](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)는 사용자 경로 `~/.agents/skills` 와 저장소 경로 `.agents/skills` 를 안내한다. 다른 환경에서 패키지 기본 경로가 인식되지 않으면 실제 검색 경로에 맞춘다. Windows 는 `-Dest "$env:USERPROFILE\.agents\skills"` 를 쓸 수 있다. `install.sh` 에는 `--dest` 가 없으므로 그 경우 세 skill 폴더를 실제 검색 경로 아래에 각각 복사한다. 같은 이름의 skill 을 여러 경로에 중복 설치하지 않는다.

설치 후 세 `SKILL.md`, `sci_collect.py`·`sci_index.py`·`sci_tldr.py`, `sci-retr/python.txt` 를 확인한다. 출력의 설치 완료 문구만 보지 말고 `[문제]`·주의 항목과 새로 설치한 프로그램을 안내한다. Chrome 설정 변경은 점검에서 문제가 나온 항목만 요청한다. 점검의 `root` 는 임시 폴더이며 논문 저장 위치가 아니다.

마지막에는 “새 대화를 열거나 Codex 를 다시 시작한 뒤, 논문 목록 파일을 대화창에 끌어다 놓고 ‘sci-retr 스킬로 논문 수집해줘’라고 해 주세요.”라고 안내하고, 이 `CODEX.md` 의 절대경로도 남긴다. 공식 문서는 skill 자동 변경 감지를 안내하므로 재시작이 모든 환경에서 필수라고 단정하지 않는다. 새 대화에서 세 skill 의 인식을 확인한다.

설치 직후와 사용법을 묻는 대화에서는 특정 주제의 논문 목록을 [Web of Science](https://www.webofscience.com/wos/woscc/smart-search) 또는 [Scopus](https://www.scopus.com/pages/home#basic)에서 검색·Export 해 파일로 전달할 수 있다고 안내한다(공용 지침 4·8절).

### 1.3 논문 폴더와 점검

논문 저장 위치를 묻고 확인받은 뒤 `resolve` 나 `refs` 를 시작한다. 추천은 Windows **`C:\sci\papers\<주제>`**, macOS/Linux **`~/sci/papers/<주제>`** 다. 공용 지침에 따라 패키지를 다른 곳에 설치했어도 추천 경로는 같다. 사용자가 요청에서 경로를 이미 정했으면 그 경로를 한 줄로 확인하고 이어간다. 참고문헌 수집은 원 논문 PDF 가 기존 수집 폴더에 있더라도 5.1 의 새 원 논문별 폴더를 쓴다.

기본 설치에서는 논문 폴더가 패키지 안에 있고 `/papers/` 는 git 이 무시한다. `--kb-root` 는 주제 폴더다. 예를 들어 `C:\sci\papers\my_topic` 아래에 `papers/{paper_id}/`, 목록과 색인이 생긴다. 색인의 `README.md` 는 주제 폴더에 쓰므로 저장소 README 와 겹치지 않는다. **저장소 루트나 설치된 skill 폴더를 `--kb-root` 로 주지 않는다.**

```powershell
$kbRoot = 'C:\sci\papers\my_topic'  # 예시. 사용자가 확인한 논문 폴더
$retrPython = (Get-Content -LiteralPath (Join-Path $skillBase 'sci-retr\python.txt') -Raw).Trim()
$collectScript = Join-Path $skillBase 'sci-retr\scripts\sci_collect.py'
$indexScript = Join-Path $skillBase 'sci-retr\scripts\sci_index.py'
$tldrScript = Join-Path $skillBase 'sci-retr\scripts\sci_tldr.py'
& $retrPython "$collectScript" doctor --kb-root "$kbRoot"
```

설치 직후에는 스크립트가 이미 점검했으므로 같은 점검을 반복하지 않는다. 위 명령은 새 논문 폴더에서 첫 수집을 하거나 사용자가 점검을 요청할 때 쓴다. `collection_registry.csv` 가 있으면 이어서 수집하며 이미 받은 논문은 다시 받지 않는다.

`doctor` 는 파일·설정을 바꾸지 않지만 Crossref 에 연결해 인터넷·인증서도 확인한다. “문제 0”과 주의 항목을 확인한다. Claude 확장이 없다는 주의에는 “Codex 는 필요 없음”이 붙는다. 그 경고 때문에 Codex 에 Claude 확장을 설치하지 않는다. 이 명령은 Codex MCP·ChatGPT Chrome 확장 연결이나 기관 구독 접근을 검증하지 않는다.

## 2. 사용자 Chrome 연결

웹 다운로드는 **사용자가 평소 쓰는 Chrome** 에서 한다. Claude in Chrome 확장은 Codex의 준비물이 아니다. Codex에서는 `chrome-devtools` MCP로 DOM·탭·다운로드 링크를 다루고, ChatGPT Chrome 확장과 **컴퓨터 사용 → Google Chrome 사용** 연결로 Chrome 자체 화면·확인 창·CAPTCHA를 처리한다.

1. 사용자가 평소 Chrome을 실행한다. README 준비물에 따라 ChatGPT Chrome 확장을 설치하고 Codex 앱에서 **설정 → 컴퓨터 사용 → Google Chrome 사용**을 켠다.
2. Codex 앱에서 **설정 → 플러그인 → MCP**를 열고 MCP 서버 검색에서 `chrome-devtools`를 설치한다. 이미 있으면 중복 등록하지 않는다. 앱 설치가 없거나 수동 설정이 필요한 환경에서만 아래 설정 파일 예시를 쓴다. 설정 파일은 `$CODEX_HOME/config.toml`, 기본 `~/.codex/config.toml`이다.

Windows 예시:

```toml
[mcp_servers.chrome-devtools]
command = "cmd"
args = ["/d", "/c", "npx", "-y", "chrome-devtools-mcp@latest", "--autoConnect"]
```

macOS/Linux 예시:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
```

3. MCP 도구가 나타나는지 확인한다. 설정 변경이 반영되지 않으면 Codex를 재시작한다. `list_pages`로 탭 목록을 읽고 사용자의 평소 Chrome에 연결됐는지 확인한다. 여러 프로필 중 어느 것인지 불분명하면 사용자에게 확인한다. `list_pages`는 프로필 선택 도구가 아니다. Computer Use를 쓸 때도 같은 Chrome 프로필을 선택한다. `DevToolsActivePort` 오류는 MCP 등록 성공과 별개로 Chrome 연결이 없다는 뜻이다. Edge 만 보인다고 Chrome 대신 선택하지 않는다. 로컬 원 논문의 `file://` PDF 탭은 참고문헌 추출용 파일이지 웹 다운로드 탭이 아니다. 연결된 Chrome 에서 `https://doi.org/...` 페이지를 열 수 있을 때만 웹 수집을 진행하고, 브라우저 도구가 URL 정책으로 조작을 거부하면 해당 차단을 따르고 정확한 사유를 보고한다.
4. `doctor` 가 읽은 프로필·다운로드 폴더가 연결된 Chrome 과 일치하는지 확인한다. 설정이 맞지 않을 때만 사용자가 `chrome://settings/content/pdfDocuments` 에서 “PDF 다운로드”를 선택하고, `chrome://settings/downloads` 에서 “다운로드 전에 각 파일의 저장 위치 확인”을 끄게 안내한다.
5. 구독 논문은 소속 기관의 구독 범위와 접속 망이 필요하다. KIST에서는 교내 망 또는 기관 VPN을 확인한다. 계정 로그인·자격증명 입력·약관 동의는 사용자에게 맡긴다. 쿠키 배너가 버튼을 가리면 Codex가 `Reject all`·필수 쿠키만·닫기 순으로 처리하고 페이지를 다시 스캔한다.

`--autoConnect` 는 실행 중인 Chrome 의 기본 프로필에 붙는 방식이다. 이를 빼고 기본 실행하면 별도 프로필의 Chrome 을 띄울 수 있으므로 이 패키지의 웹 경로에 쓰지 않는다. 연결이 안 되면 새 프로필·앱 내장 브라우저·`assist --window` 로 바꾸지 말고 사용자 직접 다운로드 후 `intake` 로 이어간다. 연결 방법의 근거는 [Chrome DevTools MCP 공식 안내](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/advanced-usage.md#automatically-connecting-to-a-running-chrome-instance)다.

## 3. 도구 대응과 클릭 방식

도구 이름은 짧게 표기한다. 실제 서버 접두어·인자는 해당 세션의 도구 정의를 확인한다. 2026-09-27 이 세션에서는 페이지별 도구에 `pageId` 가 필요했다.

| 공용 지침의 Claude 도구·표현 | Codex 에서 적용할 방법 |
|---|---|
| `tabs_context_mcp`, 탭 목록 | `list_pages` |
| `tabs_create_mcp`, 새 탭 | `new_page`. 평소에는 작업용 탭 하나를 재사용한다. 확인 창 탭을 보존하는 동안 다른 출판사에 쓸 새 탭을 만든다 |
| `navigate` | `navigate_page` 에 작업 탭의 `pageId` 와 주소를 준다 |
| 탭 선택·앞으로 가져오기 | `select_page` 의 `pageId`, `bringToFront: true` |
| `javascript_tool` | `evaluate_script`. DOM 읽기·링크 확인·스크롤에 쓴다 |
| `find`, `read_page` | `take_snapshot` 의 접근성 트리와 최신 `uid`. 필요하면 DOM 읽기를 보완한다 |
| `computer` 의 screenshot·zoom | 일반 웹 페이지는 `take_screenshot`, Chrome 자체 화면·시각 문제는 ChatGPT Chrome 확장에 연결된 Computer Use. 현재 화면과 배율을 다시 확인한다 |
| `computer` 의 좌표 클릭 | 기본 MCP `click`은 좌표가 아니라 최신 snapshot의 `uid`를 받는다. 좌표가 필요하면 Computer Use 지침과 현재 화면을 확인한다 |
| 키 입력·일반 폼 | `press_key`, `fill`. 계정 로그인·자격증명·약관 동의는 사용자 담당이며, 다운로드 권한·쿠키 배너·CAPTCHA는 3.2를 따른다 |
| 탭 닫기 | `close_page`. 이번 작업에서 만든 탭만 닫는다 |
| `browser_batch` | 동일 이름의 도구를 가정하지 않는다. 같은 탭의 이동·관찰·클릭·저장은 순서대로 처리한다 |
| `list_connected_browsers`, `select_browser`, `onThisComputer` | 직접 대응하는 필드는 없다. 로컬 MCP 설정과 `list_pages` 결과로 연결 대상을 확인한다 |
| `selectedTabId` | 작업 탭의 `pageId` 를 기록한다. 실제 앞 탭 여부는 `select_page` 와 화면 상태로 확인한다 |
| Bash·Read·Grep·파일 쓰기 | 세션의 셸·파일 도구. Windows 는 PowerShell, 검색은 `rg` 를 쓴다 |
| Claude 전용 하위 에이전트 | `sci-retr-web`(웹 목록 전체), `sci-tldr-writer`(한 줄 요약), 큰 목록 사전 분류는 Claude 절차다. Codex 의 웹 목록은 주 에이전트가 5절, 요약은 6.2, 사전 분류는 6.3 을 따른다. 색인은 LLM 없이 실행한다 |

### 3.1 페이지 안의 링크·버튼

1. [웹 다운로드 요령](sci-retr/references/web_download_playbook.md)의 해당 출판사 절을 읽는다. 논문 제목·DOI 와 본문/SI 링크의 역할을 먼저 확인한다.
2. `select_page` 로 작업 탭을 앞으로 가져오고 `take_snapshot` 을 읽는다. 다운로드할 요소를 최신 `uid` 로 특정한 뒤 `click` 한다. 메뉴 펼침·페이지 이동·늦은 로딩 뒤에는 snapshot 을 다시 받는다.
3. 스크롤이 필요하면 `evaluate_script` 로 해당 요소에 `scrollIntoView({block:'center', behavior:'instant'})` 를 적용하고 화면을 확인한다. Claude playbook 의 좌표·배율을 그대로 넣지 않는다.
   페이지마다 로딩과 링크 위치를 다시 읽어 클릭 시점·스크롤 횟수·이동량을 정한다. 고정된 클릭 간격이나 같은 좌표·스크롤 순서를 반복하지 않는다. 커서 제어가 가능한 도구에서는 확인한 대상으로 이동하고, 무관한 클릭·가짜 마우스 움직임은 넣지 않는다. 도구가 커서 경로를 제공하지 않으면 그 기능이 있다고 가정하지 않는다.
4. 클릭이 안 되고 페이지에 실제 다운로드 링크가 있으면 **그 페이지에서 확인한 주소**로 같은 탭을 이동하는 방법을 검토한다. Elsevier SI·View PDF, ACS/RSC 의 `/article-pdf/`·`/article-supplement/`, IOP 본문 `/pdf` 는 Claude 쪽 주소 이동 사례다. Codex 성공을 보장하는 목록은 아니다.
5. IOP SI 의 서명 링크는 `/data` 목록에서 클릭한다. Science 본문은 playbook 의 온라인 보기 또는 View Options 경로를 쓴다. 주소를 추측하거나 토큰을 떼어 새 다운로드 요청을 만들지 않는다.

Elsevier 본문의 `View PDF`에는 `downloadMedia()`를 쓰지 않는다. 이 링크는 원 논문 탭에서 직접 다운로드하지 않고 `pdfft` 중간 탭을 열기 때문에 원 탭의 다운로드 이벤트를 기다리면 제한 시간까지 멈출 수 있다(2026-09-28 실제 수집에서 119초). 다운로드 폴더 상태를 먼저 보고, View PDF를 일반 클릭한 뒤 새 `pdfft` 탭이나 새 `*-main.pdf`를 확인한다. CAPTCHA·Cloudflare가 나오면 그 `pdfft` 탭을 유지한 채 3.2의 Computer Use로 직접 통과한다. 파일이 생기고 `.crdownload`가 사라진 뒤 보조 탭을 닫으며, 파일이 이미 있으면 다시 클릭하지 않는다. SI 직접 파일 링크는 본문과 별도 동작으로 처리한다.

링크 후보 찾기는 설치본의 [references/web_find.js](sci-retr/references/web_find.js)를 세션에서 한 번 읽어 재사용한다. 머리의 짧은 영어 주석 한 줄 뒤 첫 코드 줄은 `await (async () => { … })();` 이며 **JSON 문자열을 반환**한다. `evaluate_script`의 `function`에 넣을 때는 `async () => { return await (async () => { … })(); }`로 감싼다. 첫 코드의 `await`를 `return await`로 바꿔 바깥 async 함수 안에 넣고, 실제 파일 본문을 쓴다(`…`는 예시다). 결과와 함수의 자세한 규격은 [playbook 2.4](sci-retr/references/web_download_playbook.md#24-web_findjs-결과와-함수)에 둔다. 스크립트에 긴 설명이나 한글을 다시 넣지 않는다. `pageId`는 작업 탭이다. 스크립트가 준비 상태를 기다리므로 별도 고정 대기를 겹치지 않는다.

- 스크립트는 HTML 로딩, 그림 등 최대 3초, 후보가 나타날 때까지 1초 간격으로 약 20초까지 기다린다. 본문만 먼저 뜨고 SI·참고문헌 절이 아직 없으면 최대 6초 더 보고, SI 절 제목은 있으나 링크가 없으면 그 절로 스크롤해 최대 6초 더 본다. 전체 대기는 26초를 넘지 않는다. 끝내 후보가 없으면 제목 `t`와 playbook의 선택자로 확인한다. 이 스크립트만 실행해서 파일이 다운로드되지는 않는다.
- 결과 키는 `t`(제목), `v`(visibilityState), `w`(innerWidth), `dpr`, `sih`(SI 절 제목 존재), `sx`(SI 절은 있으나 링크를 못 찾음), `sk`(받지 않는 형식이라 제외한 SI 수), `ms`(실제 대기 시간), `s`(SI 최대 5개), `m`(본문 최대 4개)다. `sx: 1`은 SI 없음이 아니므로 절을 한 번 확인한다. `s`가 비고 `sk`가 있으면 받을 형식의 SI가 없는 것이다. 창이 최소화된 것으로 감지되면 `min: 1`이 붙는다. 각 후보는 `[번호, 글자, 경로, x, y]` 또는 `[번호, 글자, 경로, "hidden"]`이며, 온라인 보기는 `"online"`, figshare iframe은 `"frame"`이 붙는다.
- 빈 경로는 접힌 절 제목·버튼, `"#"`·`"js"`는 목차·메뉴일 수 있다. 글자와 경로는 줄인 **표시용 값**이므로 다운로드 주소로 쓰지 않는다. 같은 페이지에서 절을 펼치거나 늦게 뜬 내용을 다시 볼 때는 `async () => await window.sciretrScan()`으로 재탐색한다. 페이지가 다시 로드돼 함수가 없으면 `web_find.js`를 다시 넣는다.
- 후보 번호 `n` 은 MCP 의 `uid` 가 아니다. `sciretrFocus` 는 **비동기 함수**이며 요소 자리가 멈출 때까지 1초 간격으로 최대 3초 기다린다. Codex 의 uid 클릭에서는 **예상 좌표 없이** `async () => await window.sciretrFocus(3)` 처럼 부른다(`3`은 예시). 반환된 `ok`, `n`, `x`, `y`, `w`, `hit`, `guard`, `text` 를 확인하고, 최신 snapshot 에서 같은 링크의 `uid` 를 찾아 클릭한다. `hit: false` 면 가림·배치를 확인한다.
- 좌표를 함께 주는 `sciretrFocus(n, x, y)` 는 예상 지점에 해당 요소가 없으면 다음 클릭 한 번을 막는 투명한 막을 만든다(`guard: 1`, 최대 8초). uid 클릭에 이 방식을 섞지 않는다. 이미 막이 생겼으면 사라진 뒤 snapshot 을 다시 받는다. 좌표 도구를 쓸 때는 `await` 뒤 실제 화면 좌표계와 `hit`·`guard` 를 확인한다.
- `min: 1` 또는 최소화 때문에 `ok: false` 면 창을 복원하고 작업 탭을 앞으로 가져온 뒤 다시 읽는다. `v: hidden` 만으로 클릭 불가라고 단정하지 않는다. 최소화 상태에서 클릭이 닿지 않은 것은 Claude 실측이며 Codex 에서는 현재 화면·도구 결과로 확인한다.
- `() => window.sciretrGo(3)` 는 찾아 둔 실제 링크로 **같은 탭을 이동**하며 주소를 출력하지 않는다. 다운로드를 일으킬 수 있으므로 파일 목록 확인 뒤에만 쓴다. 같은 탭의 두 번째 다운로드부터 Chrome 의 “여러 파일 다운로드” 확인에 걸린 Claude 기록이 있다. `sciretrSaveText` 도 영향을 받았으므로 웹 본문은 새 탭에서 저장한다. 실제 저장 여부를 다운로드 폴더에서 확인한다.
- Silverchair SI의 문서 형식, 다른 논문 링크, 학회 초록집 `Supplement_1`, `suppliers`·`data-sharing-policy`, 규소 `Si`, 7z·ZIP-Document, 동영상·`.txt`, 호·권의 `/issue/` 링크를 거른다. MDPI의 `/s` SI 후보는 숫자 1~3자리만 인정한다. Elsevier·Silverchair·IOP SI 도메인과 figshare의 허용 경로만 외부 후보로 쓴다. figshare 화면 후보는 `sciretrGo`로 iframe 주소에 들어가 확인한다. 후보가 없다고 SI가 없다고 단정하지 않으며, PDF·Word 형식과 MDAR 제외는 최종 확인한다.

결과를 약 1,000자 안으로 줄인 것은 Claude 도구의 출력 제한에 맞춘 설계다. Codex 에도 같은 제한이 있다고 가정하지 않는다.

PDF 가 없는 웹 전용 글 또는 5절의 PDF 실패 처리에는 [references/web_text.js](sci-retr/references/web_text.js)를 쓴다([playbook 2.5](sci-retr/references/web_download_playbook.md#25-웹-전용-글의-웹-본문-web_textjs)). 파일 끝의 즉시 실행 함수를 `evaluate_script` 에서는 `() => { return (() => { … })(); }` 로 감싼다. 반환 통계 `chars`·`paras`·`refs`·`removed`·`heads` 를 읽고, `heads` 에 추천·관련 글·뉴스·지표가 남아 있으면 저장하지 않고 점검한다. 본문이 500자 미만이면 저장 함수가 `ok: false` 를 반환할 수 있다. 적절한 전문이면 **앞서 다운로드하지 않은 새 탭에서 같은 논문 페이지를 열고 스크립트를 다시 넣어**, `() => window.sciretrSaveText('<paper_id>')` 를 실행한다. PDF 재시도에도 실패한 경우에는 두 번째 인자 `'pdffail'` 을 준다. `<paper_id>.sciretr.html` 이 다운로드 폴더에 실제로 생겼는지 확인한 뒤 `intake` 한다. 본문·참고문헌 외의 추천 글 등이 빠졌는지 `heads` 와 저장 파일로 확인한다.

웹 전용 출판사의 파일을 `requests`, `curl`, 페이지 안 `fetch`, 네트워크 응답 추출로 대신 받지 않는다. 브라우저에서 정상 다운로드하고 파일 정리는 `intake` 에 맡긴다. 서명 URL·쿠키·토큰은 출력하지 않는다. playbook 의 `[BLOCKED]` 마스킹·출력 잘림·클릭 실패는 Claude 도구의 관찰이며 Codex 에도 같다고 단정하지 않는다.

### 3.2 Chrome이 그리는 화면·CAPTCHA·권한 창

Wiley·IEEE의 “열기/Open”, Science 온라인 보기의 다운로드 아이콘, Chrome의 여러 파일 다운로드 권한과 CAPTCHA는 일반 페이지 DOM만으로 조작하기 어려울 수 있다. `take_snapshot`에 실제 요소가 나오면 최신 `uid`로 누르고, 나오지 않으면 ChatGPT Chrome 확장으로 연결된 Computer Use를 사용한다. 두 방법 모두 **같은 사용자 Chrome 창**의 최신 화면을 기준으로 한다.

- CAPTCHA가 나타나면 화면과 문제 지시를 읽고 해당 UI를 직접 풀어 확인 상태와 제출 결과를 확인한 뒤 원래 다운로드로 돌아간다. 최초 논문 수집 명령이 이 작업까지 승인하므로 중간에 다시 허락을 묻거나 사용자에게 대신 눌러 달라고 하지 않는다. 외부 CAPTCHA 풀이 서비스, 토큰 추출, 응답 위조는 쓰지 않는다. 실패하면 새 문제를 읽어 다시 시도하며, 다른 출판사를 처리한 뒤 남은 탭으로 돌아올 수 있다.
- 2026-09-27 Sol Medium 검증에서는 IOP DOI `10.1149/2162-8777/ac7417`의 Radware hCaptcha가 실제로 나타났다. 첫 이미지 문제 뒤 두 번째 문제를 풀어 `I am human` 확인과 Submit을 완료했고, 본문 PDF가 intake에서 정상 식별됐다. 이 한 유형의 성공을 모든 CAPTCHA 유형의 보장으로 확대하지 않는다.
- “여러 파일을 다운로드하도록 허용할까요?”가 뜨면 허용하고 실제 새 파일을 확인한다. 반복되면 `chrome://settings/content/automaticDownloads`에서 해당 출판사 사이트의 자동 다운로드를 허용한다. 전역 무조건 허용으로 바꾸지 않는다.
- 쿠키 배너가 클릭을 가리면 `Reject all`·필수 쿠키만·닫기 순으로 처리한 뒤 snapshot과 `sciretrScan()`을 새로 받는다. 쿠키 설정만으로 사이트 자체 동의 배너가 자동으로 사라진다고 가정하지 않는다.
- `handle_dialog`는 Chrome의 모든 화면·저장 창을 처리하는 도구가 아니다. 일반 탭은 chrome-devtools MCP, Chrome 자체 화면과 시각 문제는 Computer Use를 선택한다.

평소에는 **탭 하나로 한 편씩, 작업 탭은 화면 앞에** 둔다. 확인 창이 뜬 탭은 닫거나 다른 주소로 옮기지 않고 그대로 두며, 다른 출판사는 `new_page`로 연 새 탭에서 이어간다(5절). 사용자의 수집 요청 범위가 남아 있는 동안 확인 창 하나를 이유로 전체 작업을 끝내지 않는다.

## 4. 경로·설정·자격증명

| 용도 | 경로·처리 |
|---|---|
| 패키지 원본 | `<패키지 폴더>/CODEX.md`, `install.ps1`, `install.sh`, 세 skill 폴더 |
| 설치된 수집 지침 | `<skillBase>/sci-retr/SKILL.md` |
| 설치된 색인 지침 | `<skillBase>/sci-index/SKILL.md` |
| 설치된 요약 지침 | `<skillBase>/sci-tldr/SKILL.md` |
| 세 CLI | `<skillBase>/sci-retr/scripts/` 의 `sci_collect.py`, `sci_index.py`, `sci_tldr.py` |
| 실행 Python | `<skillBase>/sci-retr/python.txt` 에 기록된 절대경로 |
| 논문 자료 | `<kbRoot>/papers/`, `collection_registry.csv`, `_collect/`, `index.csv`, `index_check.csv` |
| 선택형 요약 자료 | `<kbRoot>/_collect/tldr_batch_<n>.md`, `tldr_src_<n>.json`, `tldr_<n>.jsonl` |
| 개인 설정 | `<kbRoot>/sci_collect.config.json` 을 쓴다 |
| 선택 자격증명 | **`<skillBase>/sci-retr/token.txt`**. 논문 폴더 `.env` 또는 `--env` 지정 파일도 지원한다 |
| 브라우저 저장 위치 | `doctor`·`intake` 가 찾은 Chrome/OS 다운로드 폴더. 다르면 `--downloads` 또는 설정 `downloads_dir` |

**설정 경로는 문자열만 Codex 로 바꾸면 안 된다.** 현재 `sci_collect.py` 는 논문 폴더 설정을 먼저 읽고, 없으면 `~/.claude/sci/sci_collect.config.json` 을 읽는다. `~/.codex/sci/` 나 `--config` 옵션은 지원하지 않는다. Claude 전역 설정을 함께 쓰지 않으려면 논문 폴더에 유효한 설정 JSON 을 둔다. 별도 옵션이 없으면 `{}` 로 기본값을 쓸 수 있다. 기존 설정은 덮어쓰지 않는다.

키·토큰은 공용 SKILL 3.2.1 의 `token` 명령으로 관리한다. **에이전트는 자격증명 파일을 열어 값을 읽거나 출력하지 않는다.** 논문 폴더 `.env`(또는 `--env` 파일) → skill 의 `token.txt` → 기존 환경변수 순으로 확인하며, 상태와 출처만 명령 출력으로 본다. [자격증명 안내](sci-retr/references/credentials_setup.md)의 옛 `--env-path`·값 출력 예시 대신 아래 현행 CLI 를 쓴다.

```powershell
& $retrPython "$collectScript" token --kb-root "$kbRoot"
# 사용자가 발급받기로 했을 때만 빈 양식 생성. 기존 token.txt 는 보존한다
& $retrPython "$collectScript" token --kb-root "$kbRoot" --create
```

`token` 은 `--create` 가 없으면 파일을 만들지 않는다. 저장 위치는 **실행한 CLI 가 속한 skill 폴더**이므로 설치본 CLI 를 사용한다. `--kb-root` 또는 `--env` 를 주어 실제 수집과 같은 자격증명 출처를 확인한다.

resolve 결과에 Elsevier OA·Wiley 논문이 있고 해당 키·토큰이 없을 때만 [Elsevier 발급 페이지](https://dev.elsevier.com/)·[Wiley 발급 페이지](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining)를 붙여 “발급받으시겠습니까?”라고 묻는다. Elsevier 구독 논문만 있으면 키를 묻지 않는다. 이미 키가 있거나 같은 대화에서 없이 진행하기로 했으면 다시 묻지 않는다.

발급받겠다고 하면 빈 양식을 만들고 사용자가 편집기에서 `token.txt` 에 직접 입력하게 한다. 채팅에는 값을 적지 말고 저장 후 알려 달라고 안내한다. 알려 주면 `token` 으로 유무만 확인하고 해당 논문을 `collect --ids <paper_id …> --force` 로 받는다. 발급 대기 중에는 답과 무관한 다른 자동 수집을 진행한다.

## 5. 수집 실행

공용 [sci-retr 지침](sci-retr/SKILL.md)의 2절 원칙과 5절 절차를 따른다. [publisher matrix](sci-retr/references/publisher_matrix.md)의 오래된 자동화·우회·별도 프로필 기록은 현행 공통 정책을 대체하지 않는다.

1. 1.3 에 따라 **저장 폴더를 확인받은 뒤** 새 폴더는 `doctor`, 이어서 `resolve` 를 실행한다. `resolve` 끝의 **`=== 다음 단계 … ===`** 블록에 나온 경로별 편수·review·키 질문·주제 확인·다음 명령을 안내에 옮긴다. 숫자나 경로 분류를 따로 다시 계산하지 않는다. 같은 `kb-root` 의 `refs`·`resolve`·`collect`·`intake`·`index` 명령은 하나가 종료된 뒤 다음을 시작한다. 출력이 잠시 멈춰도 실행 중인 셸 세션을 확인하고 중복 실행하지 않는다. `collection_registry.csv` 저장 오류가 나면 다른 실행·CSV 열림 여부를 확인하고 `status` 로 실제 저장 상태를 재확인한다.
2. 주제 확인은 **30편 초과**일 때만 하며, 이미 주제를 받았으면 다시 묻지 않는다. 30편 이하는 WoS·Scopus 입력이어도 목록 그대로 진행한다. review 는 제목 추정 대신 출력의 `[review]` 와 registry `doc_type` 을 쓴다. 문서 유형은 WoS `DT`·Scopus `Document Type`, 없으면 OpenAlex 유형이다. review follow-up·해당 키 발급 질문은 한 메시지에 묶는다. 신규 논문의 연도·paper_id 는 인쇄 연도 우선이며 기존 id 는 바꾸지 않는다. Angewandte 의 ange/anie 두 판은 `resolve` 가 독일어판을 범위 밖으로 처리한다.
3. 사용자가 요청한 수집 범위에서 **답과 무관한 자동 수집은 먼저 진행**한다. 키 발급 질문이 있으면 해당 출판사만 `collect --exclude-publishers elsevier,wiley` 로 빼고, 없으면 `collect` 를 쓴다. 제외 목록은 실제로 답을 기다리는 출판사만 넣는다. 주제 답에 의존하는 분류·수집이나 추가 참고문헌 수집은 답을 받은 뒤 한다. 자동 결과와 남은 질문을 함께 알린다.
4. **`collect`가 `_collect/manual_download.csv`도 만든다.** 웹 경로를 처음 시작할 때 `assist`를 반복할 필요가 없다. 목록을 다시 만들거나 중단 뒤 재개할 때만 `assist`를 쓴다(`--exclude-publishers`도 지원). 초록만·범위 밖 논문과 이미 저장된 파일 항목은 목록에서 제외된다. 목록은 설정 `web_first_publishers` 순으로 확인 창이 잦은 사이트를 앞에 둔다. 출판사별 논문·본문/SI 목록은 진행 상황으로 알릴 수 있지만 답을 기다리지 않고, **Codex 주 에이전트가 목록 순서대로 끝까지** 처리한다. [playbook](sci-retr/references/web_download_playbook.md)의 순서를 이 문서 3절 도구로 수행하고, `.crdownload`가 사라져 파일이 완성되기 전에 다음 논문으로 이동하지 않는다. Review·News & Views·Perspective는 본문 PDF·텍스트만 수집하고 SI 확인·클릭은 건너뛴다. `doc_type`이 `article`이어도 페이지의 기사 분류나 PDF 첫 쪽 머리표가 해당 유형이면 이 정책을 적용한다. 제목의 단어만으로는 판정하지 않는다. 이 경우 `mark --si-none`을 쓰지 않고 기존 SI 파일도 지우지 않는다. 그 밖의 Elsevier 기사는 첫 결과에 SI가 없으면 View PDF 전에 `sciretrScan()`을 한 번 더 부른다. `sx`면 SI 절을 확인하고, `sk`만 있으면 받는 형식의 SI가 없는 것으로 기록한다. 파일 자체에 DOI·제목이 없을 것 같으면 다운로드 직후 `record --id <paper_id> --slot main|si --latest --url <현재 판 주소>`로 연결한다.
5. SI 는 PDF·Word 문서만 받는다. 동영상·음성·결정 구조·압축·스프레드시트·Science MDAR 체크리스트는 받지 않는다. “Download full issue”, 다른 논문 묶음, 모든 SI 압축 다운로드도 쓰지 않는다.
6. `intake --dry-run`으로 매칭을 보고 `intake`로 옮긴다. 파일명은 바꿀 필요가 없다. 못 가린 파일은 그대로 두고 DOI·제목을 확인하며, 어느 논문인지 알면 `record --id <paper_id> --slot main|si --file <파일 이름>`으로 기록한 뒤 다시 실행한다. 기록과 내용 판정이 다른 논문이나 다른 자리를 가리키면 억지로 옮기지 않는다. `status`의 **`=== 보고용 요약 … ===`에서 `색인` 줄**을 따른다. 받을 논문이 남았으면 웹 수집·intake를 마치고, 끝났으면 편수와 관계없이 6.1의 `build`를 바로 실행한다. 한 줄 요약만 6.2에 따라 사용자에게 한 번 묻는다.

Windows 실행 예시 — 1절에서 확인한 폴더·Python 을 이어 쓴다. 범위·키 질문이 없는 경우다.

```powershell
& $retrPython "$collectScript" resolve --kb-root "$kbRoot" --input "$kbRoot\dois.txt"
# '다음 단계' 안내에 따라 자동 수집. 웹 경로 목록도 생성된다
& $retrPython "$collectScript" collect --kb-root "$kbRoot"
# 웹 목록을 진행 상황으로 알리고, 답을 기다리지 않고 사용자 Chrome 에서 다운로드 완료 뒤
& $retrPython "$collectScript" intake --kb-root "$kbRoot" --hours 1 --dry-run
& $retrPython "$collectScript" intake --kb-root "$kbRoot" --hours 1
& $retrPython "$collectScript" status --kb-root "$kbRoot"
# '색인' 줄에서 수집 완료를 확인한 뒤. 색인은 별도로 묻지 않는다
& $retrPython "$indexScript" build --kb-root "$kbRoot"
```

`--hours 1` 은 방금 받은 묶음의 예시다. 오래전에 받은 파일도 정리해야 하면 시간 범위를 늘린다. macOS/Linux 도 `python.txt` 에 적힌 실행 파일과 같은 CLI 인자를 쓴다.

- 보고는 `collect`·`intake`·`status`·`assist` 의 **`보고용 요약`** 블록을 바탕으로 한다. 출판사별 편수·SI 수·실패 사유와 `색인` 안내, `받는 순서`, `웹 본문만`, `PDF 받기 실패 → 웹 본문 저장`, `SI 만 받을 행` 을 그대로 활용한다. PDF 실패 행은 논문마다 보고 블록의 DOI 링크를 함께 전달한다. 공용 SKILL 의 인사·완료/부분 완료/중단 제목을 따르되, 이 표시는 채팅 보고에만 쓰고 CSV·본문·파일명에는 넣지 않는다.
- 수집 중에는 공용 SKILL 5.2·5.4·5.5의 세 시점에 `## 🐶 1. 수집 전략`, `## 🐶 2. 자동 수집 결과`, `## 🐶 3. 웹 수집 결과` 제목으로 진행 상황을 채팅에 알린다. 제목 형식으로 강아지 이모지를 크게 보여 주고, 실제 편수·남은 일은 각 단계의 출력에 맞춘다. 웹 수집 결과는 다운로드 뒤 `intake`·`status`까지 반영한 다음 알린다. 웹 대상이 0편이면 대상 없음이라고 적는다.
- `intake`는 PNAS `.sapp`, IEEE “Supplementary File”, PDF·Word(`.docx`, `.doc`)의 제목·DOI와 `record` 기록을 판정에 쓴다. “본문 후보 N개”가 나오면 임의로 하나를 본문으로 정하지 않는다. 첫 쪽·DOI·제목으로 SI를 확인해 지정된 자리에 정리한 뒤 다시 실행한다. 파일 주소 이동이 `net::ERR_ABORTED`로 끝나도 저장됐을 수 있으므로 재시도 전에 다운로드 폴더의 완성 파일을 본다. dry-run도 같은 실행의 SI 이름·중복을 반영하며, 목록과 무관한 개인 파일 이름은 출력하지 않는다.
- `intake` 는 `<paper_id>.sciretr.html` 을 해당 논문의 `html/{paper_id}.html` 로 옮겨 `source.md` 를 만든다. PDF 가 중복 저장돼도 본문 글이 같으면 하나만 옮기고, SI 도 글 내용으로 중복을 가린다. 동일 논문의 두 DOI 중 하나가 범위 밖이면 남은 논문에 맞춘다. 웹 본문을 나중에 PDF 로 보완하면 해당 PDF 를 `intake` 해 상태를 갱신한다.
- 웹에서 구독 밖·게재 전을 확인했으면 `mark --ids <paper_id> --status abstract_only --note "웹 확인: 구독 밖"` 또는 `--note "웹 확인: 게재 전"` 으로 남긴다. `status` 는 그 사유를 함께 보여 준다. 코드가 “구독 밖일 수 있음”이라고 한 것만으로 확정하지 않는다.
- 본문은 이미 있고 웹 목록에 SI만 남은 논문에서 SI가 없음을 확인했으면 `mark --ids <paper_id> --si-none --note "웹 확인: SI 없음"`으로 그 행을 닫는다. `SI 확인` 행에도 같은 명령을 쓰며, `sk`가 있는 경우에는 `--note "웹 확인: SI 는 받지 않는 형식뿐"`으로 남긴다. 논문 상태는 바꾸지 않는다.
- 확인 창이나 CAPTCHA 탭은 닫거나 다른 주소로 옮기지 않는다. 3.2에 따라 화면을 직접 처리하고, 오래 걸리면 다른 출판사를 새 탭에서 진행한 뒤 돌아온다. 한 차례 실패했다고 사용자에게 넘기거나 승인·대리 클릭을 요청하거나 전체 수집을 종료하지 않는다. 같은 문제가 반복돼 현재 도구로 풀 수 없을 때만 해당 DOI와 시도 결과를 남기고 나머지 목록을 끝까지 처리한다.
- PDF 가 한 번 안 받아졌다고 웹 본문으로 넘기지 않는다. ① 출판사별 기본 버튼 ② 페이지에서 확인한 다른 경로(`navigate_page` 로 PDF 주소 열기, `sciretrGo`, 온라인 보기의 다운로드) ③ 논문 페이지 재방문 후 재시도를 한다. 그래도 PDF 를 받지 못했고 페이지에 전문이 보일 때만 3.1 의 `web_text.js` 를 **새 탭에서** 실행해 `sciretrSaveText('<paper_id>', 'pdffail')` 로 저장한다. 확인 창과 구독 밖은 PDF 실패로 분류하지 않는다. PDF 자체가 없는 웹 전용 글은 `sciretrSaveText('<paper_id>')` 를 쓴다.
- `assist --window`는 쓰지 않는다. 설정 `web_only_publishers`를 줄여 자동 요청을 시도하지 않는다. Elsevier API는 키가 있는 OA 논문에만, Wiley 자동 경로는 **개인 TDM 토큰**이 있을 때 쓴다. Elsevier API는 XML의 PDF·Word SI를 같은 키로 받고, 저장소 사본·Wiley TDM으로 본문만 받았으나 본문에 SI 언급이 있으면 웹 목록의 `SI 확인` 행으로 올린다. 미구독 출판사도 OA 논문은 자동 경로로 한 번 시도하고 실패하면 웹 경로로 넘긴다. 자동 요청의 User-Agent는 `sci-retr/0.2.1 (+https://github.com/angmond1/sci)`이며 브라우저로 위장하지 않는다.
- playbook의 96편·81편·6편 기록은 Claude 실측이다. Codex는 2026-09-27 Sol Medium으로 21개 출판사 63편의 웹 경로를 검증했다. 페이지 준비는 `web_find.js`의 기다림·결과로 확인한다. ScienceDirect 웹 경로는 한 편의 본문·SI 다운로드가 끝나고 `.crdownload`가 사라진 뒤 30초를 추가로 기다린 후 다음 논문을 연다(2026-09-28 사용자 지시). 다른 웹 경로는 한 편이 끝나면 다음 편으로 가며 자동 경로는 설정 간격을 유지한다.
- 차단·확인 반복이면 그 사이트를 멈춘다. 쿠키 복사, User-Agent·TLS 지문·자동화 표시 위장, 응답 가로채기, 차단 직전 간격 시험은 하지 않는다. 공용 지침의 대기 후 재개 규칙을 따르되 무인 재시도를 반복하지 않는다.
- 끊긴 뒤에는 `intake → status → assist` 순으로 남은 목록을 다시 만든다. 작업에서 만든 보조 탭만 정리하고 사용자 기존 탭은 보존한다.
- 브라우저 제어를 쓰지 못해도 사용자가 평소 Chrome 에서 직접 받은 파일을 같은 `intake` 절차로 정리할 수 있다.
- `reextract` 는 저장된 원본에서 텍스트를 다시 뽑고, 옛 HTML 의 깨진 문자·합자도 복원한다. 새 수집은 `resp_text()` 로 응답 charset·HTML meta·UTF-8 을 확인한다. `reextract` 는 출판사에 재요청하는 `collect --force` 와 구분한다.
- 옛 `split_assignment.py`, `elsevier_html_retry_safe.py`, `failure_classifier.py`, `manual_ingest.py` 는 제거됐다. `runner.py` 는 판정·정리 라이브러리로만 쓰고 직접 실행하지 않는다. 인증서 확인을 끄던 코드도 제거됐으므로 옛 기록의 `verify=False`·`ignore_https_errors` 를 되살리지 않는다. 현재 요청은 `truststore` 로 OS 인증서 저장소를 쓴다.

### 5.1 참고문헌 수집 (refs)

사용자가 논문 PDF·링크·DOI 또는 기존 `paper_id` 를 주며 참고문헌 수집을 요청하면, 먼저 저장 폴더를 확인하고 다음을 실행한다. `refs` 는 파일을 수집하지 않고 DOI 목록을 만든다.

```powershell
# 예시: 사용자가 준 로컬 원 논문 PDF
$sourcePdf = 'C:\papers_inbox\source_paper.pdf'
& $retrPython "$collectScript" refs --kb-root "$kbRoot" --source "$sourcePdf"
# 출력된 _collect/refs_<원 논문>.txt 의 실제 경로로 이어서 resolve 한다
```

참고문헌 목록은 Crossref·OpenAlex 로 조회하고, 둘 다 비면 로컬 PDF 의 참고문헌 DOI 를 쓴다. 링크에서 원 논문 DOI 를 찾을 때 웹 전용 출판사 페이지에는 요청하지 않는다. 그 밖의 허용된 사이트에서는 DOI 메타를 읽을 수 있다. DOI 를 찾지 못하면 원 논문 PDF 나 DOI 를 요청한다. 원 논문 자체는 목록에서 제외된다. DOI 없는 참고문헌은 출력·목록 머리에 표시된 누락 번호와 함께 알린다.

`_collect/refs_<원 논문>.txt` 의 각 데이터 줄은 **`번호<TAB>DOI`** 다. Crossref 목록 순서가 원 논문의 참고문헌 번호이며, OpenAlex 에서 더 찾은 DOI 는 원 목록의 DOI 없는 항목과 제목 또는 연도·권·첫 쪽을 맞춰 번호를 붙인다. 못 찾으면 `00`(번호 모름)이다. PDF 만 있을 때는 `[12]`·`12.` 같은 줄 번호가 1부터 이어질 때만 번호로 쓴다. 파일의 `#` 로 시작하는 안내 줄은 입력에서 제외된다.

참고문헌 수집은 **원 논문마다 새 주제 폴더**에서 시작한다. 원 논문 PDF 가 다른 수집 폴더 안에 있어도 새 폴더를 `$kbRoot` 로 정하고 `refs` 부터 색인까지 같은 경로를 쓴다. 결과 파일로 `resolve` 하면 번호가 신규 논문의 `paper_id`·폴더·PDF·SI 파일명 앞에 붙는다(예: `07_2021_ACS-Catal_Cheng`, 최소 두 자리). 이미 등록된 논문은 id 를 바꾸지 않고 레지스트리의 `ref_no` 와 색인 번호만 채운다. 사용자가 “모두”라고 했으면 편수와 관계없이 주제 확인·사전 분류로 목록을 줄이지 않는다. `--limit N` 은 사용자가 일부만 요청했거나 허락한 시험에만 쓴다. review follow-up 에 동의한 경우도 `refs --source <paper_id>` 로 목록을 만들고 이미 등록된 DOI 를 제외해 이어간다.

## 6. Codex 색인·한 줄 요약

### 6.1 서지정보 색인 — 수집 뒤 항상

[sci-index 지침](sci-index/SKILL.md)을 읽고 수집·intake 가 끝나면 **편수와 관계없이, 묻지 않고** 실행한다. 기존 색인도 새 논문을 받을 때마다 갱신한다. 예전 20편 기준 질문·생략 규칙은 없다. 주제 확인의 30편 기준은 수집 범위 판단에만 쓴다.

```powershell
& $retrPython "$indexScript" build --kb-root "$kbRoot"
```

- `build` 는 LLM 없이 `index.csv`, `index_check.csv`, 주제 폴더의 `README.md`(에이전트용 5줄 사용법)를 만든다. 별도의 LLM 색인 검수나 검수용 하위 에이전트를 실행하지 않는다.
- DOI 다음 `웹페이지` 열에는 `https://doi.org/<DOI>`, DOI 가 없으면 레지스트리의 논문 주소가 들어간다. `수집 URL` 은 실제 API·PDF 주소일 수 있어 별개다. `ref_no` 가 있는 참고문헌 수집 색인은 맨 왼쪽에 `참고문헌 번호` 열을 둔다(번호를 모르면 `-`). 웹 본문 수집은 `원문상태` 에 `전문(웹 본문, PDF 없음)`, PDF 실패 뒤 웹 본문 저장은 `전문(웹 본문, PDF 받기 실패)` 로 구별한다.
- 사이트 안내 문구와 DOI·저널명·제목이 반복된 서지 인용문은 초록에서 빼고 flag를 남긴다. 빈 초록은 전문의 초록 절에서 복원할 수 있을 때 채운다. 두 단이 섞이거나 참고문헌·붙은 단어로 의심되면 채우지 않는다. 머리표와 분량으로 확인되는 highlight·editorial·commentary·perspective·correspondence·book review 같은 짧은 기사는 `짧은 기사(종류, N쪽)`로 표시해 정상 단문과 불완전 PDF를 구분한다. 프리프린트의 저널명은 서버 이름으로 보완한다.
- 기존 `한줄요약` 열과 `LLM:` flag 를 보존한다. 옛 `요약_ko` 열은 `한줄요약` 으로 옮긴다. 요약 열이 없던 색인에는 `build` 만으로 새 요약 열을 붙이지 않는다.
- 총 편수·상태별 편수, 남은 flag 와 조치, 실제 걸린 시간을 보고한다. Claude 기록의 “96편 1~3초”를 Codex 에서 측정한 시간으로 보고하지 않는다. `index.csv` 는 논문을 고르는 입구이며, 판단 근거는 `source.md`·PDF 에서 읽는다.

옛 `sci_index.py prep`·`apply` 는 새 명령 안내 뒤 **종료 코드 2** 로 끝난다. 요약은 아래 `sci_tldr.py` 로 실행한다. `index_gists_*.csv`, `--gists`, `check_flags` 결과 규격은 더 쓰지 않는다.

### 6.2 한국어 한 줄 요약 — 사용자가 원할 때만

색인 뒤 편수와 관계없이 “한국어 한 줄 요약도 만들까요? (N편)”라고 한 번 묻는다. 이미 요청했거나 동의했으면 다시 묻지 않고, 거절했으면 실행하지 않는다. Codex 의 소요 시간·토큰 비용은 아직 측정하지 않았으므로 Claude 전용 에이전트의 수치로 예상 시간을 약속하지 않는다.

[sci-tldr 지침](sci-tldr/SKILL.md)을 읽고 `index.csv` 가 있는 상태에서 다음 순서로 진행한다.

```powershell
# 사용자가 요약을 원할 때만
& $retrPython "$tldrScript" prep --kb-root "$kbRoot"
# 출력에 적힌 묶음을 읽고, 각 결과 경로에 JSONL 을 작성한 뒤
& $retrPython "$tldrScript" apply --kb-root "$kbRoot"
```

1. `prep` 은 기본적으로 요약이 빈 행을 `_collect/tldr_batch_<n>.md` 로 묶고, 검증 재료를 `tldr_src_<n>.json` 에 둔다. `범위밖-미수집` 행은 요약 대상에서 제외한다. 기본 분할 기준은 50편·50KB(`--size`, `--max-kb`)다. 출력의 실제 묶음 번호·결과 경로를 사용한다. `--ids` 는 기존 요약이 있어도 지정 논문을 다시 묶고, `--all` 은 전체를 다시 묶는다.
2. **Codex 기본 경로는 주 에이전트의 순차 처리다.** Claude 의 `sci-tldr-writer` 는 Read·Write 도구와 `model: sonnet` 으로 정의되어 있으며 Codex 에 등록되지 않는다. 전용 에이전트가 없으면 메인이 처리한다는 공용 지침을 따른다. 10편 미만은 원래부터 메인이 처리하고, 10편 이상도 이 Codex 경로에서는 묶음마다 직접 읽고 쓴다. 범용 하위 에이전트를 대용으로 띄우거나 Claude 의 모델·effort 를 Codex 설정으로 옮기지 않는다. 전용 에이전트 정의에도 현재 effort 지정은 없다.
3. 묶음 파일을 한 번 읽고 머리의 규칙 8개에 따라, **묶음의 모든 논문**을 지정된 `_collect/tldr_<n>.jsonl` 에 한 번에 쓴다. 한 줄에 JSON 하나, 필드는 `paper_id`, `한줄요약`, `flag` 다. Python `json.dumps(..., ensure_ascii=False)` 등으로 따옴표·줄바꿈을 이스케이프하고 UTF-8 로 저장한다. 마크다운 코드 울타리는 결과 파일에 넣지 않는다.
4. 요약은 제공된 글에 근거한 한국어 한 문장, 권장 60~120자·최대 150자로 마침표로 끝낸다. 숫자·단위·물질명·화학식을 추측하거나 변환해 보태지 않는다. 리뷰·논평은 그 유형에 맞게 쓴다. 재료 부족·제목과 글 불일치면 `한줄요약` 을 빈 문자열로 두고 이유를 `flag` 에 쓴다.
5. 결과를 모두 쓴 뒤 `apply` 로 검증·병합한다. 기본은 `_collect/tldr_*.jsonl` 이며 `--files <경로 …>` 로 결과를 지정할 수 있다. `tldr_src_<n>.json` 도 함께 보존한다. `prep` 을 다시 실행하면 기존 묶음 Markdown 을 지우므로, 현재 묶음의 작성·병합을 마친 뒤 재준비한다. 새 결과 번호는 기존 `tldr_<n>.jsonl` 다음부터 시작한다.
6. 보류는 `prep --ids <paper_id …>` 로 한 번 더 쓴다. “재료 부족”인데 전문이 있으면 `prep --body <paper_id …>` 로 본문 앞부분 3,000자를 쓴다. 두 번째도 해결되지 않으면 비워 두고 이유를 보고한다. 검증에서 보류된 새 문장은 병합되지 않으며 기존 요약은 남을 수 있다. 명시적으로 빈 결과를 쓴 행은 `apply` 가 예전 요약도 지운다. 최종 비움이 필요하면 빈 결과와 이유를 다시 병합해 확인한다.

일반 요약 재료는 초록 최대 1,500자다. 초록이 200자 미만이면 해당 논문 제목 자리부터의 본문 앞부분을 우선 확인하고, 쓸 재료가 없으면 묶지 않는다. 초록만 받은 논문의 `source.md` 는 본문 재료로 쓰지 않는다. 제목만으로 요약하지 않는다.

`apply` 는 두 자리 이상 숫자·소수와 숫자가 든 화학식·코드를 재료 글과 대조한다(영어 낱말 수 포함). 길이 초과·한글 없음·마침표 없음·판단 과정 문구도 보류한다. 숫자·화학식 검증이 의미나 한국어 번역의 정확성까지 보증하지는 않으므로 작성할 때 글과 대조한다. 보류·비움 사유는 `index_check.csv` 의 `LLM:` flag 로 반영된다. 같은 결과를 다시 병합해도 flag 가 중복되지 않는다.

완료 보고에는 `apply` 뒤의 `index.csv`를 다시 읽어 **모든 논문을 채팅에 출력한다.** sci-tldr 5절 형식대로 각 논문을 독립 문단으로 쓰며, 번호·연도·저널·교신저자 다음 줄에 제목, 그다음 줄에 한글 한줄요약을 놓는다. 각 줄 끝은 공백 두 칸으로 강제 줄바꿈하고, 논문 사이에는 `&nbsp;` 독립 문단을 넣어 화면에 한 줄 높이의 공백을 확보한다. `1.`로 시작하는 Markdown 자동 번호 목록은 쓰지 않고 `**1. 연도 · 저널 · 교신저자**`처럼 번호를 문단 안에 넣는다. 표·한 줄 압축·일부 예시·CSV 링크·완료 편수만으로 끝내지 않는다. 긴 목록은 연속 메시지로 나누고, 빈 요약은 사유를 표시한다. 함께 **한줄요약 채운 수 / 전체**, 보류·비운 논문과 이유, 실제 걸린 시간을 적는다. 색인 생성과 요약 완료를 구분한다.

### 6.3 큰 목록 사전 분류

수집 범위를 줄이는 사전 분류는 sci-retr 5.3 의 별도 단계다. `_collect/triage.csv` (`paper_id, verdict, reason`)와 IN/BORDERLINE/OUT 기준을 유지한다. 하위 에이전트를 쓸 때는 해당 세션의 위임 허용 범위와 사용 가능한 도구를 따르고, 별도 모델 지정이 없으면 세션 기본값을 쓴다. 위임하지 못하면 주 에이전트가 같은 규격으로 처리한다. 이 절차를 색인 검수나 `sci-tldr` 의 범용 에이전트 실행으로 확대하지 않는다.

## 7. 확인된 범위와 유지보수

### 7.1 Codex에서 확인 (2026-09-27~28)

| 항목 | 확인 범위 |
|---|---|
| 저장소·설치 | 소스 `a29fff0`, `VERSION` 0.2.1을 별도 폴더에 다시 받아 `-Codex` 설치. `doctor` 오류 0·경고 0. 문서 순서 변경은 `822971b`까지 반영 |
| 웹 경로 | Sol Medium, 사용자 Chrome, chrome-devtools MCP 중심으로 21개 출판사에서 무작위 3편씩 총 63편 처리. PDF 전문 61, C&EN 웹 전문 1, Oxford 구독 밖 초록 1, 실패·미처리 0 |
| SI·intake | SI 21파일(PDF 18, DOCX 3). `intake --dry-run` 뒤 실제 반입, `record`로 내용만으로 가리지 못한 Springer/Nature SI 2개 연결. 63개 paper_id·DOI 고유성 확인 |
| CAPTCHA·Chrome 화면 | IOP Radware hCaptcha를 두 번째 이미지 문제에서 통과해 본문 PDF 저장. Wiley·IEEE의 Chrome “열기”, Science·PNAS 다중 다운로드도 파일 생성까지 확인 |
| 웹 본문·상태 | PDF 없는 C&EN 기사를 `web_text.js`로 저장해 `web_text`; 구독 밖 Oxford는 `abstract_only`. `human_required`, `failed`, `pdf_missing` 0 |
| 색인·파일 감사 | `sci_index.py build`로 `index.csv` 63행. PDF 79개는 서명·EOF·페이지를 읽었고 Poppler 열기 실패 0, DOCX 3개는 유효한 OOXML 컨테이너 |
| 저장소 영향 | 검증 데이터는 별도 폴더에 두었고 소스 저장소·검증 clone의 작업 트리가 깨끗함을 확인 |

검증 보고서는 `D:\repo\sci-retr-sol-verify-data-260927\web_only_random\_verification\VALIDATION_REPORT.md`에 있다. 이 절의 수치는 해당 표본과 날짜의 결과이며 모든 미래 CAPTCHA·사이트 개편을 보장하지 않는다.

### 7.2 Claude 쪽 기록과 아직 미검증인 항목

- 2026-09-27 전 출판사 96편 연습과 전체 흐름 81편 시험은 **Claude 실측**이다. playbook의 사이트별 요령은 참고하되 처리 시간·확인 화면 동작을 Codex 수치로 바꾸어 보고하지 않는다.
- 최신 소스의 Wiley 개인 TDM 토큰 자동 경로, Elsevier API 자동 경로와 실제 API SI 수집은 이번 63편 웹 전용 시험에 포함하지 않았다. 자동 수집 경로 전체를 최신 커밋에서 다시 검증한 것으로 보고하지 않는다.
- `refs`, `reextract`, WoS·Scopus의 모든 내보내기 형식, 대규모 사전 분류, `sci-tldr` 한 줄 요약은 이번 최신 웹 전용 시험에 포함하지 않았다.
- 새 설치 스크립트의 Windows PowerShell 5.1·7, PATH/winget 누락, Git Bash 위임, WSL Ubuntu 24.04 가상환경 시험은 Claude 쪽 인계 기록이다. macOS는 그 기록에서도 미시험이다.
- Claude 전용 요약 에이전트의 처리 시간·토큰 수치를 Codex의 예상 시간이나 비용으로 쓰지 않는다. Codex 주 에이전트의 `sci-tldr` 처리 시간·비용은 미측정이다.
- 실제 다운로드 시험도 사용자가 sci-retr 수집·검증을 명령한 범위라면 출판사별 대상 논문과 본문/SI 목록을 진행 상황으로 알리고 바로 수행한다. 확인된 출판사·날짜·도구·파일 검증 결과만 추가한다.

### 7.3 갱신

패키지를 갱신할 때는 로컬 변경을 먼저 확인하고, git 을 쓰는 설치는 `git pull --ff-only` 뒤 1절의 Codex 설치를 다시 한다. 설치본의 개인 수정은 교체 전에 보관한다. 설치 스크립트는 설치본의 `token.txt` 를 보존하고 `python.txt` 를 다시 기록한다. 논문 폴더의 설정·`.env`·자료도 유지한다.

기본 위치의 논문은 `<패키지 폴더>/papers/<주제>` 에 있으며 git 이 무시한다. **패키지 폴더를 삭제하고 다시 받지 않는다.** 논문이 함께 지워질 수 있다. 문서·코드만 갱신하고 기존 논문 폴더를 그대로 쓴다.

문서를 고치기 전에는 기존 파일을 `_history/<원본이름>_YYMMDD_HHMM.<확장자>` 로 남긴다. 시험 파일은 `_tmp/` 에 둔다. 이 Codex 어댑터를 고칠 때 `README.md`, 공용 `SKILL.md`, `references/` 의 수정이 필요하면 별도로 제안한다. 커밋·푸시는 사용자가 요청할 때만 한다.

여러 세션이 작업할 때 원본 폴더를 수정하고 커밋·푸시하는 세션은 하나로 둔다. 별도 작업은 다른 폴더·브랜치의 worktree 에서 한다. 같은 폴더를 공유해야 하면 `git add -A`·`git add -u`·`git stash` 를 쓰지 않는다. 사용자가 커밋을 요청했을 때만 담당 파일을 경로별로 추가하고 `git diff --cached --stat` 으로 범위를 확인한 뒤 커밋한다. 다른 세션의 변경을 포함하거나 되돌리지 않는다.
