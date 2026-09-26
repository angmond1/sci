# sci-retr on Codex — 설치·실행 지침 (Codex 에이전트용)

> 이 문서는 Codex Desktop / Codex CLI 가 [sci-retr 패키지](https://github.com/angmond1/sci)를 설치하고 사용할 때 읽는 지침이다. 사용자가 “sci-retr 설치해줘”라고 하면 1절부터 진행한다.
> 공용 skill 본문은 Claude 기준이다. 수집·색인 절차는 [sci-retr/SKILL.md](sci-retr/SKILL.md)와 [sci-index/SKILL.md](sci-index/SKILL.md)를 따르고, 도구·모델·경로 차이는 이 문서를 적용한다. [CLAUDE.md](CLAUDE.md)는 Claude 설치용이다.
> 갱신 기준: 2026-09-27, 패키지 `VERSION` 0.2.1. 설치 자동화·token/refs 명령·20편 색인 기준·CLI 판단 블록을 반영했다. Codex 에서 확인한 범위와 Claude 쪽 시험 기록은 7절에 구분한다.

## 0. 구성과 적용 범위

`sci-retr` 는 DOI 목록이나 WoS·Scopus 검색 결과로 논문 PDF·본문 텍스트·SI 를 수집한다. 논문 PDF·링크를 받으면 `refs` 로 참고문헌 DOI 목록도 만든다. `sci-index` 는 사용자가 원할 때 그 결과를 `index.csv` 로 정리하고 검수·한국어 요약을 붙인다. 두 skill 을 함께 설치한다. 두 CLI 모두 **`sci-retr/scripts/`** 에 있다.

배포 저장소는 `angmond1/sci` 다. skill 이름 `sci-retr`·`sci-index` 와 기존 로컬 폴더 `D:\repo\sci-retr` 는 그대로 쓴다.

- README 의 Opus·Sonnet 은 Claude 모델이다. Codex 모델과 임의로 대응시키지 않는다. 현재 세션 모델을 쓰고, 하위 에이전트도 별도 지정이 없으면 세션 기본값을 따른다.
- 이 문서는 설치 스크립트가 복사하는 두 skill 폴더 밖에 있다. `CODEX.md` 라는 이름만으로 자동 로드된다고 가정하지 않는다. 설치 완료 안내에 이 파일의 절대경로를 남기고, 새 대화에서는 먼저 읽도록 안내한다.
- 예시 요청: “`<패키지 폴더>/CODEX.md` 를 먼저 읽고, sci-retr 로 이 목록의 논문을 `<논문 폴더>` 에 수집해줘.” 이후 공용 skill 을 읽어 실행한다.

## 1. 설치

### 1.1 실행 환경과 패키지 폴더

1. 사용자가 준 패키지 폴더가 있으면 그대로 쓴다. 없으면 “프로그램 파일을 어디에 둘까요? 기본은 Windows `C:\sci`, macOS/Linux `~/sci` 입니다.”라고 묻고 답을 기다린다. 논문을 저장할 폴더는 수집할 때 확인한다.
2. “설치에 필요한 프로그램을 확인하고, 없는 것은 바로 설치하겠습니다.”라고 알린다. Python 3.11 이상·Google Chrome 확인과 설치는 1.2 의 설치 스크립트가 한다. 에이전트가 같은 점검이나 winget·brew 설치를 먼저 반복하지 않는다.
3. 패키지가 없으면 `git clone https://github.com/angmond1/sci.git <패키지 폴더>` 로 받는다. git 이 없으면 GitHub 의 `Code → Download ZIP` 으로 받아 푼다. 동료에게 받은 폴더도 쓸 수 있다.
4. 브라우저 제어용 chrome-devtools MCP 를 새로 설치할 때만 Node.js LTS·npm 이 추가로 필요하다. Python 수집·색인과 사용자의 직접 다운로드에는 MCP 가 필수가 아니다.

### 1.2 두 skill 설치

**아래 예시는 경로를 실제 선택값으로 바꿔 실행한다.** 기존 설치 폴더에 개인 수정이 있으면 먼저 패키지의 `_history/` 아래에 보관한다. 설치 스크립트는 대상 `sci-retr`, `sci-index` 폴더를 교체하므로, 대상의 절대경로와 링크 여부를 확인하고 실행한다. 패키지 원본 폴더를 설치 대상으로 지정하지 않는다.

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
- 스크립트는 **프로그램 확인·설치 → 두 skill 복사 → pip 패키지 설치 → `doctor` 점검** 순서로 실행한다. 패키지는 `requests`, `pymupdf`, `truststore`, `beautifulsoup4`, `lxml`, `openpyxl`, `wiley-tdm`, `playwright` 다.
- Windows 는 Python·Chrome 이 없으면 winget 의 `Python.Python.3.12`·`Google.Chrome` 을 설치한다(`--source winget`, Python 은 먼저 `--scope user`). winget 이 없거나 설치가 실패하면 출력의 수동 설치 안내를 따른다. UAC 창은 사용자가 처리한다. pip 실패 시에는 `--user` 로 한 번 더 시도한다.
- macOS 는 Homebrew 가 있을 때 `python@3.12`·`--cask google-chrome` 을 설치한다. Linux 는 필요한 시스템 프로그램의 설치 방법을 안내한다. macOS/Linux 에서 pip 이 없거나 시스템 Python 설치가 제한되면 `~/.sci-retr/venv` 에 패키지를 넣는다. Windows Git Bash 에서는 `install.ps1` 로 넘긴다.
- `-NoAutoInstall` / `--no-auto-install` 은 Python·Chrome 자동 설치를 끈다. **전체 스크립트의 dry-run 은 아니다.** 이미 필요한 프로그램이 있으면 skill 복사·pip 설치·점검은 진행한다.
- Windows 의 Python 탐색 순서는 `py -3.12 → py -3.13 → py -3.11 → py -3 → python → python3`, 이후 사용자 설치 경로의 Python312·313·311 이다. 셸 스크립트는 `python3.12 → python3.13 → python3.11 → python3 → python` 순으로 3.11 이상을 찾는다. 설치 직후 PATH 미반영도 구분한다.
- 선택한 Python 실행 파일의 절대경로는 **`<skillBase>/sci-retr/python.txt`** 에 기록한다. 가상환경을 썼으면 그 경로다. 이후 수집·색인은 모두 이 인터프리터로 실행한다. `ModuleNotFoundError` 가 나면 먼저 이 파일과 해당 Python 의 패키지를 확인한다. `python.txt` 가 없는 이전 설치에서만 동작하는 인터프리터를 별도로 찾는다.
- 재설치 때 기존 설치본의 `token.txt` 는 보존한다. 원본의 `token.txt`, `python.txt`, `_history`, `__pycache__` 는 복사하지 않는다. `-Codex` / `--codex` 는 Claude 확장 설치 안내·웹스토어 열기를 건너뛴다. Node.js 설치·MCP 등록은 하지 않는다.

**Codex 의 skill 검색 경로는 실행 환경에서 확인한다.** 이 PC 의 현재 세션은 `~/.codex/skills` 를 읽는다. 한편 [OpenAI 공식 skill 문서](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)는 사용자 경로 `~/.agents/skills` 와 저장소 경로 `.agents/skills` 를 안내한다. 다른 환경에서 패키지 기본 경로가 인식되지 않으면 실제 검색 경로에 맞춘다. Windows 는 `-Dest "$env:USERPROFILE\.agents\skills"` 를 쓸 수 있다. `install.sh` 에는 `--dest` 가 없으므로 그 경우 두 skill 폴더를 실제 검색 경로 아래에 각각 복사한다. 같은 이름의 skill 을 여러 경로에 중복 설치하지 않는다.

설치 후 두 `SKILL.md`, 두 CLI, `sci-retr/python.txt` 를 확인한다. 출력의 설치 완료 문구만 보지 말고 `[문제]`·주의 항목과 새로 설치한 프로그램을 안내한다. Chrome 설정 변경은 점검에서 문제가 나온 항목만 요청한다. 점검의 `root` 는 임시 폴더이며 논문 저장 위치가 아니다.

마지막에는 “새 대화를 열거나 Codex 를 다시 시작한 뒤, 논문 목록 파일을 대화창에 끌어다 놓고 ‘sci-retr 스킬로 논문 수집해줘’라고 해 주세요.”라고 안내하고, 이 `CODEX.md` 의 절대경로도 남긴다. 공식 문서는 skill 자동 변경 감지를 안내하므로 재시작이 모든 환경에서 필수라고 단정하지 않는다. 새 대화에서 두 skill 의 인식을 확인한다.

### 1.3 논문 폴더와 점검

논문 저장 위치를 묻고 확인받은 뒤 `resolve` 나 `refs` 를 시작한다. 추천은 Windows **`C:\sci\papers\<주제>`**, macOS/Linux **`~/sci/papers/<주제>`** 다. 공용 지침에 따라 패키지를 다른 곳에 설치했어도 추천 경로는 같다. 사용자가 요청에서 경로를 이미 정했거나 원 논문이 기존 수집 폴더에 있으면 그 경로를 한 줄로 확인하고 이어간다.

기본 설치에서는 논문 폴더가 패키지 안에 있고 `/papers/` 는 git 이 무시한다. `--kb-root` 는 주제 폴더다. 예를 들어 `C:\sci\papers\my_topic` 아래에 `papers/{paper_id}/`, 목록과 색인이 생긴다. 색인의 `README.md` 는 주제 폴더에 쓰므로 저장소 README 와 겹치지 않는다. **저장소 루트나 설치된 skill 폴더를 `--kb-root` 로 주지 않는다.**

```powershell
$kbRoot = 'C:\sci\papers\my_topic'  # 예시. 사용자가 확인한 논문 폴더
$retrPython = (Get-Content -LiteralPath (Join-Path $skillBase 'sci-retr\python.txt') -Raw).Trim()
$collectScript = Join-Path $skillBase 'sci-retr\scripts\sci_collect.py'
$indexScript = Join-Path $skillBase 'sci-retr\scripts\sci_index.py'
& $retrPython "$collectScript" doctor --kb-root "$kbRoot"
```

설치 직후에는 스크립트가 이미 점검했으므로 같은 점검을 반복하지 않는다. 위 명령은 새 논문 폴더에서 첫 수집을 하거나 사용자가 점검을 요청할 때 쓴다. `collection_registry.csv` 가 있으면 이어서 수집하며 이미 받은 논문은 다시 받지 않는다.

`doctor` 는 파일·설정을 바꾸지 않지만 Crossref 에 연결해 인터넷·인증서도 확인한다. “문제 0”과 주의 항목을 확인한다. Claude 확장이 없다는 주의에는 “Codex 는 필요 없음”이 붙는다. 그 경고 때문에 Codex 에 확장을 설치하지 않는다. 이 명령은 Codex MCP 연결이나 기관 구독 접근을 검증하지 않는다.

## 2. 사용자 Chrome 연결

웹 다운로드는 **사용자가 평소 쓰는 Chrome** 에서 한다. Claude in Chrome 확장은 Codex 의 필수 준비물이 아니다. 이 문서는 chrome-devtools MCP 의 `--autoConnect` 연결을 기준으로 한다.

1. 사용자가 평소 Chrome 을 실행한다. Chrome 144 이상에서 `chrome://inspect/#remote-debugging` 을 열어 원격 디버깅을 켜고, 연결 허용 창은 사용자가 직접 처리한다.
2. 기존 Codex MCP 설정을 확인한다. 이미 `chrome-devtools` 가 있으면 중복 등록하지 않는다. 신규 설정은 Codex 설정 파일(`$CODEX_HOME/config.toml`, 기본 `~/.codex/config.toml`)의 해당 항목에 적용한다.

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

3. MCP 도구가 나타나는지 확인한다. 설정 변경이 반영되지 않으면 Codex 를 재시작한다. `list_pages` 로 탭 목록을 읽고 사용자의 평소 Chrome 에 연결됐는지 확인한다. 여러 프로필 중 어느 것인지 불분명하면 사용자에게 확인한다. `list_pages` 는 프로필 선택 도구가 아니다.
4. `doctor` 가 읽은 프로필·다운로드 폴더가 연결된 Chrome 과 일치하는지 확인한다. 설정이 맞지 않을 때만 사용자가 `chrome://settings/content/pdfDocuments` 에서 “PDF 다운로드”를 선택하고, `chrome://settings/downloads` 에서 “다운로드 전에 각 파일의 저장 위치 확인”을 끄게 안내한다.
5. 구독 논문은 소속 기관의 구독 범위와 접속 망이 필요하다. KIST 에서는 교내 망 또는 기관 VPN 을 확인한다. 로그인·쿠키 동의·약관 동의는 사용자에게 맡긴다.

`--autoConnect` 는 실행 중인 Chrome 의 기본 프로필에 붙는 방식이다. 이를 빼고 기본 실행하면 별도 프로필의 Chrome 을 띄울 수 있으므로 이 패키지의 웹 경로에 쓰지 않는다. 연결이 안 되면 새 프로필·앱 내장 브라우저·`assist --window` 로 바꾸지 말고 사용자 직접 다운로드 후 `intake` 로 이어간다. 연결 방법의 근거는 [Chrome DevTools MCP 공식 안내](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/advanced-usage.md#automatically-connecting-to-a-running-chrome-instance)다.

## 3. 도구 대응과 클릭 방식

도구 이름은 짧게 표기한다. 실제 서버 접두어·인자는 해당 세션의 도구 정의를 확인한다. 2026-09-27 이 세션에서는 페이지별 도구에 `pageId` 가 필요했다.

| 공용 지침의 Claude 도구·표현 | Codex 에서 적용할 방법 |
|---|---|
| `tabs_context_mcp`, 탭 목록 | `list_pages` |
| `tabs_create_mcp`, 새 탭 | `new_page`. 작업용 탭 하나만 만들고 재사용한다 |
| `navigate` | `navigate_page` 에 작업 탭의 `pageId` 와 주소를 준다 |
| 탭 선택·앞으로 가져오기 | `select_page` 의 `pageId`, `bringToFront: true` |
| `javascript_tool` | `evaluate_script`. DOM 읽기·링크 확인·스크롤에 쓴다 |
| `find`, `read_page` | `take_snapshot` 의 접근성 트리와 최신 `uid`. 필요하면 DOM 읽기를 보완한다 |
| `computer` 의 screenshot·zoom | `take_screenshot`. 확대·좌표계는 현재 도구의 지원 범위에서 확인한다 |
| `computer` 의 좌표 클릭 | 기본 `click` 은 좌표가 아니라 최신 snapshot 의 `uid` 를 받는다. 아래 절차를 따른다 |
| 키 입력·일반 폼 | `press_key`, `fill`. 로그인·동의는 사용자 담당이다 |
| 탭 닫기 | `close_page`. 이번 작업에서 만든 탭만 닫는다 |
| `browser_batch` | 동일 이름의 도구를 가정하지 않는다. 같은 탭의 이동·관찰·클릭·저장은 순서대로 처리한다 |
| `list_connected_browsers`, `select_browser`, `onThisComputer` | 직접 대응하는 필드는 없다. 로컬 MCP 설정과 `list_pages` 결과로 연결 대상을 확인한다 |
| `selectedTabId` | 작업 탭의 `pageId` 를 기록한다. 실제 앞 탭 여부는 `select_page` 와 화면 상태로 확인한다 |
| Bash·Read·Grep·파일 쓰기 | 세션의 셸·파일 도구. Windows 는 PowerShell, 검색은 `rg` 를 쓴다 |
| sonnet 하위 에이전트 | Codex 의 사용 가능한 하위 에이전트 도구. 6절의 입력·출력 규격을 유지한다 |

### 3.1 페이지 안의 링크·버튼

1. [웹 다운로드 요령](sci-retr/references/web_download_playbook.md)의 해당 출판사 절을 읽는다. 논문 제목·DOI 와 본문/SI 링크의 역할을 먼저 확인한다.
2. `select_page` 로 작업 탭을 앞으로 가져오고 `take_snapshot` 을 읽는다. 다운로드할 요소를 최신 `uid` 로 특정한 뒤 `click` 한다. 메뉴 펼침·페이지 이동·늦은 로딩 뒤에는 snapshot 을 다시 받는다.
3. 스크롤이 필요하면 `evaluate_script` 로 해당 요소에 `scrollIntoView({block:'center', behavior:'instant'})` 를 적용하고 화면을 확인한다. Claude playbook 의 좌표·배율을 그대로 넣지 않는다.
4. 클릭이 안 되고 페이지에 실제 다운로드 링크가 있으면 **그 페이지에서 확인한 주소**로 같은 탭을 이동하는 방법을 검토한다. Elsevier SI·View PDF, ACS/RSC 의 `/article-pdf/`·`/article-supplement/`, IOP 본문 `/pdf` 는 Claude 쪽 주소 이동 사례다. Codex 성공을 보장하는 목록은 아니다.
5. IOP SI 의 서명 링크는 `/data` 목록에서 클릭한다. Science 본문은 playbook 의 온라인 보기 또는 View Options 경로를 쓴다. 주소를 추측하거나 토큰을 떼어 새 다운로드 요청을 만들지 않는다.

링크 후보 찾기는 설치본의 [references/web_find.js](sci-retr/references/web_find.js)를 세션에서 한 번 읽어 재사용한다. 파일은 즉시 실행 함수이며 **JSON 문자열을 반환**한다. `evaluate_script` 는 함수 선언을 받으므로 파일의 `(() => { … })();` 를 반환하는 바깥 함수를 만들어 `function` 에 넣는다. 앞의 주석은 함수 밖에 유지하고, 형태는 `() => { return (() => { … })(); }` 로 한다. 읽은 파일 본문을 넣어 쓰며 `…` 를 그대로 실행하지 않는다. `pageId` 는 작업 탭, `waitForStableDom` 은 읽기 목적이면 `false` 로 준다.

- 결과의 `si`, `main` 후보에서 제목·형식·역할을 확인한다. `main` 의 `online: true` 는 온라인 보기이고, `si` 의 빈 `path` 는 펼쳐야 하는 절 제목일 수 있다. 후보가 없다고 본문·SI 가 없다고 단정하지 않는다. 외부 CDN 링크는 제외되고 목록 길이도 제한되므로 playbook 의 선택자로 보완한다.
- 후보 번호 `n` 은 MCP 의 `uid` 가 아니다. `evaluate_script` 에 `() => window.sciretrFocus(3)` 같은 함수를 주면 해당 후보를 스크롤하고 JSON 문자열로 화면 좌표를 돌려준다(`3`은 예시). 그 뒤 최신 snapshot 에서 같은 요소의 `uid` 를 찾아 클릭한다. 좌표는 실제 좌표 도구가 있을 때만 쓴다.
- 페이지 이동·절 펼침 뒤에는 스크립트를 다시 실행한다. 반환된 `path` 는 쿼리를 제거하고 길이를 줄인 표시용 값이다. 이를 완전한 다운로드 주소로 사용하지 않는다. 스크립트는 클릭·다운로드를 하지 않으며, SI 문서 형식과 MDAR 제외는 에이전트가 최종 확인한다.

웹 전용 출판사의 파일을 `requests`, `curl`, 페이지 안 `fetch`, 네트워크 응답 추출로 대신 받지 않는다. 브라우저에서 정상 다운로드하고 파일 정리는 `intake` 에 맡긴다. 서명 URL·쿠키·토큰은 출력하지 않는다. playbook 의 `[BLOCKED]` 마스킹·출력 잘림·클릭 실패는 Claude 도구의 관찰이며 Codex 에도 같다고 단정하지 않는다.

### 3.2 Chrome 이 그리는 화면·좌표 클릭

Wiley·IEEE 의 “열기/Open”, Science 온라인 보기의 다운로드 아이콘은 일반 페이지 DOM 만으로 조작하기 어려울 수 있다. `take_snapshot` 에 실제 요소가 나오면 `uid` 클릭을 쓴다. 나오지 않으면 다음 중 현재 환경에서 가능한 방법을 쓴다.

- Windows `computer-use` 스킬이 제공되면 그 지침과 API 를 먼저 읽고, **같은 사용자 Chrome 창**의 최신 화면을 확인해 일반 다운로드 버튼을 누른다. 이 세션에는 해당 스킬과 `node_repl` 이 제공되지만 출판사 다운로드는 시험하지 않았다.
- Chrome DevTools MCP 공식 설정에는 좌표 도구를 켜는 `--experimentalVision` 이 있다. 이 세션에는 `click_at` 이 노출되지 않았고 시험하지 않았다. 기본 설치 조건으로 추가하지 않으며, 사용할 때는 설치 버전·실제 도구 정의를 확인한다. [공식 설정](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md)
- 사용할 화면 제어 도구가 없거나 버튼을 특정하지 못하면 사용자가 그 다운로드 버튼을 직접 누르게 안내한다. 저장된 파일은 `intake` 로 정리한다.

어떤 도구를 써도 출판사 봇 확인 창은 에이전트가 누르지 않는다. `handle_dialog` 는 Chrome 의 모든 화면·저장 창을 처리하는 도구가 아니다. 화면 제어 기능이 있어도 **탭 하나로 한 편씩, 작업 탭은 화면 앞에** 둔다는 규칙은 유지한다.

## 4. 경로·설정·자격증명

| 용도 | 경로·처리 |
|---|---|
| 패키지 원본 | `<패키지 폴더>/CODEX.md`, `install.ps1`, `install.sh`, 두 skill 폴더 |
| 설치된 수집 지침 | `<skillBase>/sci-retr/SKILL.md` |
| 설치된 색인 지침 | `<skillBase>/sci-index/SKILL.md` |
| 두 CLI | `<skillBase>/sci-retr/scripts/sci_collect.py`, `sci_index.py` |
| 실행 Python | `<skillBase>/sci-retr/python.txt` 에 기록된 절대경로 |
| 논문 자료 | `<kbRoot>/papers/`, `collection_registry.csv`, `_collect/`, `index.csv`, `index_check.csv` |
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

1. 1.3 에 따라 **저장 폴더를 확인받은 뒤** 새 폴더는 `doctor`, 이어서 `resolve` 를 실행한다. `resolve` 끝의 **`=== 다음 단계 … ===`** 블록에 나온 경로별 편수·review·키 질문·주제 확인·다음 명령을 안내에 옮긴다. 숫자나 경로 분류를 따로 다시 계산하지 않는다.
2. 주제 확인은 **30편 초과**일 때만 하며, 이미 주제를 받았으면 다시 묻지 않는다. 30편 이하는 WoS·Scopus 입력이어도 목록 그대로 진행한다. review 는 제목 추정 대신 출력의 `[review]` 와 registry `doc_type` 을 쓴다. 문서 유형은 WoS `DT`·Scopus `Document Type`, 없으면 OpenAlex 유형이다. review follow-up·해당 키 발급 질문은 한 메시지에 묶는다. 신규 논문의 연도·paper_id 는 인쇄 연도 우선이며 기존 id 는 바꾸지 않는다.
3. 사용자가 요청한 수집 범위에서 **답과 무관한 자동 수집은 먼저 진행**한다. 키 발급 질문이 있으면 해당 출판사만 `collect --exclude-publishers elsevier,wiley` 로 빼고, 없으면 `collect` 를 쓴다. 제외 목록은 실제로 답을 기다리는 출판사만 넣는다. 주제 답에 의존하는 분류·수집이나 추가 참고문헌 수집은 답을 받은 뒤 한다. 자동 결과와 남은 질문을 함께 알린다.
4. **`collect` 가 `_collect/manual_download.csv` 도 만든다.** 웹 경로를 처음 시작할 때 `assist` 를 반복할 필요가 없다. 목록을 다시 만들거나 중단 뒤 재개할 때만 `assist` 를 쓴다(`--exclude-publishers` 도 지원). 웹 다운로드는 출판사별 논문·본문/SI 목록을 알리고 확인받은 뒤 시작한다. [playbook](sci-retr/references/web_download_playbook.md)의 순서를 이 문서 3절 도구로 수행하고, `.crdownload` 가 사라져 파일이 완성되기 전에 다음 논문으로 이동하지 않는다.
5. SI 는 PDF·Word 문서만 받는다. 동영상·음성·결정 구조·압축·스프레드시트·Science MDAR 체크리스트는 받지 않는다. “Download full issue”, 다른 논문 묶음, 모든 SI 압축 다운로드도 쓰지 않는다.
6. `intake --dry-run` 으로 매칭을 보고 `intake` 로 옮긴다. 파일명은 바꿀 필요가 없다. 못 가린 파일은 그대로 두고 DOI·제목으로 확인한다. `status` 로 반영 상태를 확인하고, **`=== 보고용 요약 … ===` 의 `색인 판단` 줄에 따라** 6절의 질문 또는 생략 안내를 한다. 수집 종료만으로 색인을 실행하지 않는다.

Windows 실행 예시 — 1절에서 확인한 폴더·Python 을 이어 쓴다. 범위·키 질문이 없는 경우다.

```powershell
& $retrPython "$collectScript" resolve --kb-root "$kbRoot" --input "$kbRoot\dois.txt"
# '다음 단계' 안내에 따라 자동 수집. 웹 경로 목록도 생성된다
& $retrPython "$collectScript" collect --kb-root "$kbRoot"
# 출판사별 파일 목록 확인을 받고, 사용자 Chrome 에서 다운로드 완료 뒤
& $retrPython "$collectScript" intake --kb-root "$kbRoot" --hours 1 --dry-run
& $retrPython "$collectScript" intake --kb-root "$kbRoot" --hours 1
& $retrPython "$collectScript" status --kb-root "$kbRoot"
```

`--hours 1` 은 방금 받은 묶음의 예시다. 오래전에 받은 파일도 정리해야 하면 시간 범위를 늘린다. macOS/Linux 도 `python.txt` 에 적힌 실행 파일과 같은 CLI 인자를 쓴다.

- 보고는 `collect`·`intake`·`status`·`assist` 의 **`보고용 요약`** 블록을 바탕으로 한다. 출판사별 편수·SI 수·실패 사유·색인 판단을 다시 세지 않는다. 공용 SKILL 의 인사·완료/부분 완료/중단 머리표를 따르되, 이 표시는 채팅 보고에만 쓰고 CSV·본문·파일명에는 넣지 않는다.
- `assist --window` 는 쓰지 않는다. 설정 `web_only_publishers` 를 줄여 자동 요청을 시도하지 않는다. Elsevier API 는 키가 있는 OA 논문에만, Wiley 자동 경로는 TDM 토큰이 있을 때 쓴다. 미구독 출판사도 OA 논문은 자동 경로로 한 번 시도하고 실패하면 웹 경로로 넘긴다. 자동 요청의 User-Agent 는 `sci-retr/0.2.1 (+https://github.com/angmond1/sci)` 이며 브라우저로 위장하지 않는다.
- 웹의 “30~60초”는 Claude 쪽 한 편 처리 시간이며 고정 대기나 Codex 속도 보장이 아니다. 웹은 한 편이 끝나면 다음 편으로 가고, 자동 경로는 설정 간격을 유지한다.
- 차단·확인 반복이면 그 사이트를 멈춘다. 쿠키 복사, User-Agent·TLS 지문·자동화 표시 위장, 응답 가로채기, 차단 직전 간격 시험은 하지 않는다. 공용 지침의 대기 후 재개 규칙을 따르되 무인 재시도를 반복하지 않는다.
- 끊긴 뒤에는 `intake → status → assist` 순으로 남은 목록을 다시 만든다. 작업에서 만든 보조 탭만 정리하고 사용자 기존 탭은 보존한다.
- 브라우저 제어를 쓰지 못해도 사용자가 평소 Chrome 에서 직접 받은 파일을 같은 `intake` 절차로 정리할 수 있다.
- `reextract` 는 저장된 원본에서 텍스트를 다시 뽑는다. `mark` 는 범위 제외·복귀에 쓴다. 출판사에 재요청하는 `collect --force` 와 구분한다.

### 5.1 참고문헌 수집 (refs)

사용자가 논문 PDF·링크·DOI 또는 기존 `paper_id` 를 주며 참고문헌 수집을 요청하면, 먼저 저장 폴더를 확인하고 다음을 실행한다. `refs` 는 파일을 수집하지 않고 DOI 목록을 만든다.

```powershell
# 예시: 사용자가 준 로컬 원 논문 PDF
$sourcePdf = 'C:\papers_inbox\source_paper.pdf'
& $retrPython "$collectScript" refs --kb-root "$kbRoot" --source "$sourcePdf"
# 출력된 _collect/refs_<원 논문>.txt 의 실제 경로로 이어서 resolve 한다
```

참고문헌 목록은 Crossref·OpenAlex 로 조회하고, 둘 다 비면 로컬 PDF 의 참고문헌 DOI 를 쓴다. 링크에서 원 논문 DOI 를 찾을 때 웹 전용 출판사 페이지에는 요청하지 않는다. 그 밖의 허용된 사이트에서는 DOI 메타를 읽을 수 있다. DOI 를 찾지 못하면 원 논문 PDF 나 DOI 를 요청한다. 원 논문 자체는 목록에서 제외되며 DOI 없는 참고문헌은 빠지므로 출력의 누락 안내도 전달한다.

결과 파일로 `resolve` 부터 진행한다. 사용자가 “모두”라고 했으면 편수와 관계없이 주제 확인·사전 분류로 목록을 줄이지 않는다. `--limit N` 은 사용자가 일부만 요청했거나 허락한 시험에만 쓴다. review follow-up 에 동의한 경우도 `refs --source <paper_id>` 로 목록을 만들고 이미 등록된 DOI 를 제외해 이어간다.

## 6. Codex 색인·검수

[sci-index 지침](sci-index/SKILL.md)을 읽는다. 웹 다운로드·intake 가 끝난 뒤 CLI 의 `색인 판단`을 따르며, 기준은 **이 논문 폴더의 전문 + 초록만 합계**다. 이번 실행에서 새로 받은 편수나 주제 확인 기준 30편과 혼동하지 않는다.

- `index.csv` 가 이미 있으면 편수와 관계없이 “새로 받은 논문을 기존 색인에 반영할까요?”라고 묻는다.
- 기존 색인이 없고 **20편 이상**이면 “수집한 논문 N편의 서지정보를 색인화 하겠습니까?”라고 묻는다.
- 기존 색인이 없고 **20편 미만**이면 “수집 논문이 20편 미만이라 색인 과정은 생략하겠습니다. 원하시면 말씀해 주세요.”라고 알리고 실행하지 않는다.
- 사용자가 이미 색인 생성·갱신을 요청했거나 위 질문에 동의했으면 다시 묻지 않고 진행한다. 아직 웹 수집이 남았으면 CLI 안내대로 수집을 마친 뒤 판단한다.

색인 실행이 정해졌을 때 다음 순서로 한다. 스크립트는 `sci-retr/scripts/` 에 있다.

```powershell
& $retrPython "$indexScript" build --kb-root "$kbRoot"
# 검수·요약 CSV 작성 뒤, 파일마다 병합
& $retrPython "$indexScript" apply --kb-root "$kbRoot" --gists "$kbRoot\_collect\index_gists_1.csv"
```

- 공용 지침의 “sonnet”을 Codex 모델명으로 바꾸어 호출하지 않는다. 사용 가능한 하위 에이전트 도구가 있고 세션 지침이 허용하면 30~40편 단위 검수를 나눈다. 도구가 없거나 위임이 제한된 환경에서는 주 에이전트가 같은 규격으로 순서대로 수행한다.
- 하위 에이전트에는 해당 `paper_id` 목록, `index.csv` 의 제목·초록·원문상태·단어수, 출력 파일 경로를 준다. 초록이 없거나 잘린 행만 `source.md` 앞부분을 읽게 한다. 단어수를 다시 세지 않는다.
- 결과는 `_collect/index_gists_<n>.csv`, 열은 **`paper_id, 요약_ko, check_flags`**, 인코딩은 UTF-8 BOM 이다. Python `csv` 모듈로 쓴다. 요약은 연구 내용·결과를 한국어 한 문장, 200자 이내로 쓰며 근거가 부족하면 flag 로 남긴다.
- 각 에이전트는 자기 gists 파일만 쓴다. `build`·`apply`, registry 변경, 다운로드, Chrome 조작은 주 에이전트가 담당한다. CSV 병합은 순서대로 실행한다.
- 큰 목록 사전 분류도 같은 방식으로 역할을 바꾼다. 공용 지침의 `_collect/triage.csv` (`paper_id, verdict, reason`) 규격과 IN/BORDERLINE/OUT 기준을 유지한다.
- `build` 는 기존 `요약_ko` 와 `LLM:` 검수 flag 를 보존하고 관련 없는 폴더는 제외한다. 논문 폴더가 아니거나 `apply` 할 `index.csv`·gists 파일이 없으면 오류 안내를 확인하고 경로·순서를 바로잡는다.
- `build` 가 만든 안내의 “Claude 용” 문구는 생성 코드에 남은 표현이다. Codex 도 `index.csv → 관련 source.md/PDF` 순으로 자료를 찾는다. 출력 문구를 바꾸려고 공용 코드를 임의 수정하지 않는다.

완료 보고에는 총 편수·상태별 편수, 요약을 채운 수, 남은 flag 와 필요한 조치를 적는다. `build` 가 끝났다는 이유만으로 요약·검수까지 완료됐다고 보고하지 않는다.

## 7. 확인된 범위와 유지보수

### 7.1 Codex 에서 확인 (2026-09-27)

| 항목 | 확인 범위 |
|---|---|
| 저장소·설치 옵션 | 새 GitHub 주소 `angmond1/sci` 와 로컬 remote 일치. `VERSION` 0.2.1, 자동 설치 4단계, `-NoAutoInstall`/`--no-auto-install`, Python 경로 기록·token 보존을 코드로 확인. 이번 작업에서는 실제 설치·업데이트를 실행하지 않음 |
| skill 검색 | 현재 세션이 `~/.codex/skills` 의 skill 을 노출함. 로컬 `sci-retr/SKILL.md` 는 존재하고 `sci-index` 폴더는 없었음. 인계 문서의 “둘 다 미설치”와 시점 차이가 있음 |
| Python | 최초 작성 때 Python 3.12 에서 8개 패키지 import·기본 CLI 도움말 확인. 이번 갱신에서 `token`, `refs`, `collect`, `assist`, `intake`, 색인 `apply` 의 `--help` 실행 성공 |
| 공용 코드 | token 상태·생성 분리, `--exclude-publishers`, refs, 문서 유형·연도, 웹 목록 생성, 판단·보고 블록, 20편 기준, 색인 요약·LLM flag 보존을 코드로 확인 |
| 링크 찾기 스크립트 | `web_find.js` 내용과 JSON 문자열·후보 번호·스크롤 함수 확인. Node.js 구문 검사 통과. Codex 의 실제 논문 페이지에서 실행·클릭한 것은 아님 |
| 브라우저 도구 | 현재 MCP 설정에 `--autoConnect` 가 있고, 3절의 기본 도구와 `pageId`·`uid`·`bringToFront` 인자가 노출됨. 실제 Chrome 연결·클릭·다운로드는 시험하지 않음 |
| 보조 화면 제어 | Windows computer-use 스킬·node_repl 제공 및 API 문서 확인. 실제 제어와 `--experimentalVision` 은 미시험 |

### 7.2 Claude 쪽 기록과 미검증 항목

- 인계 기록상 Python CLI 는 깨끗한 Python 3.12·3.14 환경에서 시험했다. 자동 경로와 `intake`, `build/apply` 의 기존 성공 이력은 그 기록이며, 이번 Codex 문서 작업에서 전체 과정을 재시험한 것은 아니다.
- 새 설치 스크립트의 Windows PowerShell 5.1·7, PATH/winget 누락, Codex 옵션, Git Bash 위임, WSL Ubuntu 24.04 가상환경 시험은 Claude 쪽 인계 기록이다. macOS 는 그 기록에서도 미시험이다.
- 웹 경로의 Elsevier·Wiley·ACS·RSC·IOP·Science·Taylor & Francis·PNAS·AIP·Oxford·IEEE·ChemRxiv 와 추가된 MDPI·Thieme·CCS Chemistry 기록은 **Claude in Chrome 실측**이다. `web_find.js` 의 RSC·ACS·Wiley 후보 탐색도 Claude 실측이다. 선택자·파일명·순서는 참고하되 Codex 에서 모두 동작한다고 보고하지 않는다.
- macOS/Linux 설치·skill 재탐색, 기관 구독 접근, Codex 웹 다운로드와 실제 논문을 이용한 수집·색인 전체 흐름은 이번 작업에서 미검증이다.
- 실제 다운로드 시험은 사용자에게 출판사별 대상 논문과 본문/SI 목록을 제시하고 확인받은 뒤 한다. 확인된 출판사·날짜·도구·파일 검증 결과만 추가한다.

### 7.3 갱신

패키지를 갱신할 때는 로컬 변경을 먼저 확인하고, git 을 쓰는 설치는 `git pull --ff-only` 뒤 1절의 Codex 설치를 다시 한다. 설치본의 개인 수정은 교체 전에 보관한다. 설치 스크립트는 설치본의 `token.txt` 를 보존하고 `python.txt` 를 다시 기록한다. 논문 폴더의 설정·`.env`·자료도 유지한다.

기본 위치의 논문은 `<패키지 폴더>/papers/<주제>` 에 있으며 git 이 무시한다. **패키지 폴더를 삭제하고 다시 받지 않는다.** 논문이 함께 지워질 수 있다. 문서·코드만 갱신하고 기존 논문 폴더를 그대로 쓴다.

문서를 고치기 전에는 기존 파일을 `_history/<원본이름>_YYMMDD_HHMM.<확장자>` 로 남긴다. 시험 파일은 `_tmp/` 에 둔다. 이 Codex 어댑터를 고칠 때 `README.md`, 공용 `SKILL.md`, `references/` 의 수정이 필요하면 별도로 제안한다. 커밋·푸시는 사용자가 요청할 때만 한다.
