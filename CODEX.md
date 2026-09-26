# sci-retr on Codex — 설치·실행 지침 (Codex 에이전트용)

> 이 문서는 Codex Desktop / Codex CLI 가 [sci-retr 패키지](https://github.com/angmond1/sci)를 설치하고 사용할 때 읽는 지침이다. 사용자가 “sci-retr 설치해줘”라고 하면 1절부터 진행한다.
> 공용 skill 본문은 Claude 기준이다. 수집·색인 절차는 [sci-retr/SKILL.md](sci-retr/SKILL.md)와 [sci-index/SKILL.md](sci-index/SKILL.md)를 따르고, 도구·모델·경로 차이는 이 문서를 적용한다. [CLAUDE.md](CLAUDE.md)는 Claude 설치용이다.
> 작성 기준: 2026-09-27, 패키지 `VERSION` 1.0.0. Codex 에서 확인한 범위와 Claude 쪽 시험 기록은 7절에 구분한다.

## 0. 구성과 적용 범위

`sci-retr` 는 DOI 목록이나 WoS·Scopus 검색 결과로 논문 PDF·본문 텍스트·SI 를 수집한다. `sci-index` 는 그 결과를 `index.csv` 로 정리하고 검수·한국어 요약을 붙인다. 두 skill 을 함께 설치한다. 두 CLI 모두 **`sci-retr/scripts/`** 에 있다.

- README 의 Opus·Sonnet 은 Claude 모델이다. Codex 모델과 임의로 대응시키지 않는다. 현재 세션 모델을 쓰고, 하위 에이전트도 별도 지정이 없으면 세션 기본값을 따른다.
- 이 문서는 설치 스크립트가 복사하는 두 skill 폴더 밖에 있다. `CODEX.md` 라는 이름만으로 자동 로드된다고 가정하지 않는다. 설치 완료 안내에 이 파일의 절대경로를 남기고, 새 대화에서는 먼저 읽도록 안내한다.
- 예시 요청: “`<패키지 폴더>/CODEX.md` 를 먼저 읽고, sci-retr 로 이 목록의 논문을 `<논문 폴더>` 에 수집해줘.” 이후 공용 skill 을 읽어 실행한다.

## 1. 설치

### 1.1 실행 환경과 패키지 폴더

1. 사용자가 준 패키지 폴더가 있으면 그대로 쓴다. 없으면 Windows `C:\sci-retr`, macOS/Linux `~/sci-retr` 를 기본으로 안내한다. 논문을 저장할 폴더는 이와 별도로 정한다.
2. Python 3.11 이상을 확인한다. Windows 는 `py -0p` 와 `py -3 --version`, macOS/Linux 는 `python3 --version` 을 쓴다. 이미 동작하는 인터프리터가 있으면 재설치하지 않는다. 없으면 [Python 공식 배포처](https://www.python.org/downloads/)에서 설치한다.
3. 패키지가 없으면 `git clone https://github.com/angmond1/sci.git <패키지 폴더>` 로 받는다. git 이 없으면 GitHub 의 `Code → Download ZIP` 으로 받아 푼다. 동료에게 받은 폴더도 쓸 수 있다.
4. 브라우저 제어용 chrome-devtools MCP 를 새로 설치할 때만 Node.js LTS·npm 이 추가로 필요하다. Python 수집·색인과 사용자의 직접 다운로드에는 MCP 가 필수가 아니다.

### 1.2 두 skill 설치

**아래 예시는 경로를 실제 선택값으로 바꿔 실행한다.** 기존 설치 폴더에 개인 수정이 있으면 먼저 패키지의 `_history/` 아래에 보관한다. 설치 스크립트는 대상 `sci-retr`, `sci-index` 폴더를 교체하므로, 대상의 절대경로와 링크 여부를 확인하고 실행한다. 패키지 원본 폴더를 설치 대상으로 지정하지 않는다.

Windows (PowerShell):

```powershell
$packageRoot = 'C:\sci-retr'  # 예시. 이미 받은 폴더가 있으면 그 경로
$retrCodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillBase = Join-Path $retrCodexHome 'skills'
powershell -ExecutionPolicy Bypass -File "$packageRoot\install.ps1" -Codex -Dest "$skillBase"
```

macOS / Linux:

```bash
package_root="$HOME/sci-retr"  # 예시. 이미 받은 폴더가 있으면 그 경로
skill_base="${CODEX_HOME:-$HOME/.codex}/skills"
bash "$package_root/install.sh" --codex
```

- `-Codex` / `--codex` 를 생략하면 Claude 경로에 설치된다. Codex 옵션의 기본 목적지는 `$CODEX_HOME/skills`, 환경변수가 없으면 `~/.codex/skills` 다.
- 스크립트는 두 skill 폴더를 복사하고 `requests`, `pymupdf`, `truststore`, `beautifulsoup4`, `lxml`, `openpyxl`, `wiley-tdm`, `playwright` 를 설치한다. `_history`, `__pycache__` 는 복사하지 않는다. MCP 등록은 하지 않는다.
- Windows 스크립트는 `py -3.12 → py -3.11 → py -3 → python`, 셸 스크립트는 `python3.12 → python3.11 → python3 → python` 순으로 찾는다. **설치 출력에 나온 인터프리터를 이후 CLI 실행에도 쓴다.** 아래 Windows 예시는 `py -3.12` 를 쓴다.
- `ModuleNotFoundError` 가 나면 같은 인터프리터의 `-m pip` 로 패키지를 확인한다. macOS/Linux 에서 시스템 Python 의 pip 설치가 제한되면 venv 를 만들고 그 인터프리터에 패키지를 설치해 CLI 를 실행한다. 시스템 패키지 보호를 끄지 않는다.

**Codex 의 skill 검색 경로는 실행 환경에서 확인한다.** 이 PC 의 현재 세션은 `~/.codex/skills` 를 읽는다. 한편 [OpenAI 공식 skill 문서](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)는 사용자 경로 `~/.agents/skills` 와 저장소 경로 `.agents/skills` 를 안내한다. 다른 환경에서 패키지 기본 경로가 인식되지 않으면 실제 검색 경로에 맞춘다. Windows 는 `-Dest "$env:USERPROFILE\.agents\skills"` 를 쓸 수 있다. `install.sh` 에는 `--dest` 가 없으므로 그 경우 두 skill 폴더를 실제 검색 경로 아래에 각각 복사한다. 같은 이름의 skill 을 여러 경로에 중복 설치하지 않는다.

설치 후 두 `SKILL.md` 와 `sci-retr/scripts/sci_collect.py`, `sci-retr/scripts/sci_index.py` 가 있는지 확인한다. Codex 의 skill 목록에서 두 이름이 보이는지도 확인한다. 공식 문서는 자동 변경 감지를 안내하며, 나타나지 않으면 Codex 를 재시작한다. 스크립트의 재시작 문구를 모든 Codex 환경의 필수 동작으로 단정하지 않는다.

### 1.3 논문 폴더와 점검

논문 폴더는 패키지·skill 설치 폴더 밖에 둔다. 색인 생성은 그 폴더의 `README.md` 도 쓰므로 저장소 루트를 `--kb-root` 로 주지 않는다.

```powershell
$kbRoot = 'D:\papers\my_topic'  # 예시. 사용자가 정한 논문 폴더
$collectScript = Join-Path $skillBase 'sci-retr\scripts\sci_collect.py'
$indexScript = Join-Path $skillBase 'sci-retr\scripts\sci_index.py'
py -3.12 "$collectScript" doctor --kb-root "$kbRoot"
```

`doctor` 는 파일·설정을 바꾸지 않지만 Crossref 에 연결해 인터넷·인증서도 확인한다. “문제 0”과 주의 항목을 확인한다. 출력에 남은 “Claude in Chrome” 문구는 공용 코드의 안내이며, 이 명령은 Codex MCP 연결이나 기관 구독 접근을 검증하지 않는다.

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
4. 사용자가 `chrome://settings/content/pdfDocuments` 에서 “PDF 다운로드”를 선택하고, `chrome://settings/downloads` 에서 “다운로드 전에 각 파일의 저장 위치 확인”을 끈다. `doctor` 가 읽은 프로필·다운로드 폴더가 연결된 Chrome 과 일치하는지도 확인한다.
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
| 논문 자료 | `<kbRoot>/papers/`, `collection_registry.csv`, `_collect/`, `index.csv`, `index_check.csv` |
| 개인 설정 | `<kbRoot>/sci_collect.config.json` 을 쓴다 |
| 선택 자격증명 | `<kbRoot>/.env`. 다른 파일이면 CLI 의 `--env` 로 지정한다 |
| 브라우저 저장 위치 | `doctor`·`intake` 가 찾은 Chrome/OS 다운로드 폴더. 다르면 `--downloads` 또는 설정 `downloads_dir` |

**설정 경로는 문자열만 Codex 로 바꾸면 안 된다.** 현재 `sci_collect.py` 는 논문 폴더 설정을 먼저 읽고, 없으면 `~/.claude/sci/sci_collect.config.json` 을 읽는다. `~/.codex/sci/` 나 `--config` 옵션은 지원하지 않는다. Claude 전역 설정을 함께 쓰지 않으려면 논문 폴더에 유효한 설정 JSON 을 둔다. 별도 옵션이 없으면 `{}` 로 기본값을 쓸 수 있다. 기존 설정은 덮어쓰지 않는다.

키·토큰은 선택이며 [자격증명 안내](sci-retr/references/credentials_setup.md)와 `sci-retr/examples/.env.example` 을 참고한다. 사용자가 `.env` 에 직접 입력하게 하고, 값은 채팅·로그·명령 인자·지침에 넣지 않는다. `doctor` 의 있음/없음 출력으로 확인한다. 이미 제공했거나 없이 진행하기로 정한 값을 다시 요구하지 않는다.

## 5. 수집 실행

공용 [sci-retr 지침](sci-retr/SKILL.md)의 2절 원칙과 5절 절차를 따른다. [publisher matrix](sci-retr/references/publisher_matrix.md)의 오래된 자동화·우회·별도 프로필 기록은 현행 공통 정책을 대체하지 않는다.

1. `doctor` → `resolve` 로 환경과 메타를 확인한다. 큰 목록의 주제·제외 범위와 review 인용 follow-up 은 공용 지침에 따라 확인한다. 이미 사용자가 정한 내용은 다시 묻지 않는다.
2. 받을 논문과 파일을 출판사별로 알리고 사용자가 확인한 범위에서 수집한다. 범위가 늘어나면 추가분을 확인한다. 설치 요청만으로 샘플 논문을 다운로드하지 않는다.
3. 자동 경로는 `collect`, 웹 경로 목록은 **`assist` 만** 실행한다. `assist --window` 는 쓰지 않는다. 설정 `web_only_publishers` 를 줄여 자동 요청을 시도하지 않는다. Elsevier API 는 키가 있는 OA 논문에만, Wiley 자동 경로는 TDM 토큰이 있을 때 쓴다.
4. 웹 경로는 [playbook](sci-retr/references/web_download_playbook.md)의 출판사별 순서를 이 문서 3절 도구로 수행한다. 논문 한 편의 다운로드가 끝나기 전에 탭을 다음 주소로 옮기지 않는다. `.crdownload` 가 사라지고 파일이 완성됐는지 확인한다.
5. SI 는 PDF·Word 문서만 받는다. 동영상·음성·결정 구조·압축·스프레드시트·Science MDAR 체크리스트는 받지 않는다. “Download full issue”, 다른 논문 묶음, 모든 SI 압축 다운로드도 쓰지 않는다.
6. `intake --dry-run` 으로 매칭을 보고 `intake` 로 옮긴다. 파일명은 바꿀 필요가 없다. 못 가린 파일은 그대로 두고 DOI·제목으로 확인한다. `status` 로 PDF 와 텍스트 반영을 확인한 뒤 6절 색인을 수행한다.

Windows 실행 예시 — 1절에서 정한 변수·인터프리터를 이어 쓴다. 다운로드 명령은 위 확인 단계 뒤에 실행한다.

```powershell
py -3.12 "$collectScript" resolve --kb-root "$kbRoot" --input "$kbRoot\dois.txt"
# 범위·출판사별 파일 목록 확인 뒤
py -3.12 "$collectScript" collect --kb-root "$kbRoot"
py -3.12 "$collectScript" assist --kb-root "$kbRoot"
# 사용자 Chrome 에서 파일 다운로드 완료 뒤
py -3.12 "$collectScript" intake --kb-root "$kbRoot" --hours 1 --dry-run
py -3.12 "$collectScript" intake --kb-root "$kbRoot" --hours 1
py -3.12 "$collectScript" status --kb-root "$kbRoot"
```

`--hours 1` 은 방금 받은 묶음의 예시다. 오래전에 받은 파일도 정리해야 하면 시간 범위를 늘린다. macOS/Linux 도 같은 CLI 인자를 쓰되 설치된 Python 과 실제 경로를 쓴다.

- 웹의 “30~60초”는 Claude 쪽 한 편 처리 시간이며 고정 대기나 Codex 속도 보장이 아니다. 웹은 한 편이 끝나면 다음 편으로 가고, 자동 경로는 설정 간격을 유지한다.
- 차단·확인 반복이면 그 사이트를 멈춘다. 쿠키 복사, User-Agent·TLS 지문·자동화 표시 위장, 응답 가로채기, 차단 직전 간격 시험은 하지 않는다. 공용 지침의 대기 후 재개 규칙을 따르되 무인 재시도를 반복하지 않는다.
- 끊긴 뒤에는 `intake → status → assist` 순으로 남은 목록을 다시 만든다. 작업에서 만든 보조 탭만 정리하고 사용자 기존 탭은 보존한다.
- 브라우저 제어를 쓰지 못해도 사용자가 평소 Chrome 에서 직접 받은 파일을 같은 `intake` 절차로 정리할 수 있다.
- `reextract` 는 저장된 원본에서 텍스트를 다시 뽑는다. `mark` 는 범위 제외·복귀에 쓴다. 출판사에 재요청하는 `collect --force` 와 구분한다.

## 6. Codex 색인·검수

[sci-index 지침](sci-index/SKILL.md)을 읽고 다음 순서로 한다. 색인 스크립트가 `sci-index/scripts/` 에 있다고 가정하지 않는다.

```powershell
py -3.12 "$indexScript" build --kb-root "$kbRoot"
# 검수·요약 CSV 작성 뒤, 파일마다 병합
py -3.12 "$indexScript" apply --kb-root "$kbRoot" --gists "$kbRoot\_collect\index_gists_1.csv"
```

- 공용 지침의 “sonnet”을 Codex 모델명으로 바꾸어 호출하지 않는다. 사용 가능한 하위 에이전트 도구가 있고 세션 지침이 허용하면 30~40편 단위 검수를 나눈다. 도구가 없거나 위임이 제한된 환경에서는 주 에이전트가 같은 규격으로 순서대로 수행한다.
- 하위 에이전트에는 해당 `paper_id` 목록, `index.csv` 의 제목·초록·원문상태·단어수, 출력 파일 경로를 준다. 초록이 없거나 잘린 행만 `source.md` 앞부분을 읽게 한다. 단어수를 다시 세지 않는다.
- 결과는 `_collect/index_gists_<n>.csv`, 열은 **`paper_id, 요약_ko, check_flags`**, 인코딩은 UTF-8 BOM 이다. Python `csv` 모듈로 쓴다. 요약은 연구 내용·결과를 한국어 한 문장, 200자 이내로 쓰며 근거가 부족하면 flag 로 남긴다.
- 각 에이전트는 자기 gists 파일만 쓴다. `build`·`apply`, registry 변경, 다운로드, Chrome 조작은 주 에이전트가 담당한다. CSV 병합은 순서대로 실행한다.
- 큰 목록 사전 분류도 같은 방식으로 역할을 바꾼다. 공용 지침의 `_collect/triage.csv` (`paper_id, verdict, reason`) 규격과 IN/BORDERLINE/OUT 기준을 유지한다.
- `build` 가 만든 안내의 “Claude 용” 문구는 생성 코드에 남은 표현이다. Codex 도 `index.csv → 관련 source.md/PDF` 순으로 자료를 찾는다. 출력 문구를 바꾸려고 공용 코드를 임의 수정하지 않는다.

완료 보고에는 총 편수·상태별 편수, 요약을 채운 수, 남은 flag 와 필요한 조치를 적는다. `build` 가 끝났다는 이유만으로 요약·검수까지 완료됐다고 보고하지 않는다.

## 7. 확인된 범위와 유지보수

### 7.1 Codex 에서 확인 (2026-09-27)

| 항목 | 확인 범위 |
|---|---|
| 저장소·설치 옵션 | GitHub 배포주소와 로컬 remote 일치. `install.ps1 -Codex -Dest`, `install.sh --codex` 의 복사 경로·의존성·교체 동작을 코드로 확인. 이번 작업에서는 실제 설치·업데이트를 실행하지 않음 |
| skill 검색 | 현재 세션이 `~/.codex/skills` 의 skill 을 노출함. 로컬 `sci-retr/SKILL.md` 는 존재하고 `sci-index` 폴더는 없었음. 인계 문서의 “둘 다 미설치”와 시점 차이가 있음 |
| Python | Python 3.12 에서 설치 스크립트의 8개 패키지 import 성공. `sci_collect.py --help`, `intake --help`, `sci_index.py --help`, `apply --help` 실행 성공 |
| 공용 코드 | 개인 설정 검색 순서, `--env`·`--downloads`·`--hours`·`--dry-run`, 색인 build/apply 경로·CSV 규격 확인 |
| 브라우저 도구 | 현재 MCP 설정에 `--autoConnect` 가 있고, 3절의 기본 도구와 `pageId`·`uid`·`bringToFront` 인자가 노출됨. 실제 Chrome 연결·클릭·다운로드는 시험하지 않음 |
| 보조 화면 제어 | Windows computer-use 스킬·node_repl 제공 및 API 문서 확인. 실제 제어와 `--experimentalVision` 은 미시험 |

### 7.2 Claude 쪽 기록과 미검증 항목

- 인계 기록상 Python CLI 는 깨끗한 Python 3.12·3.14 환경에서 시험했다. 자동 경로와 `intake`, `build/apply` 의 기존 성공 이력은 그 기록이며, 이번 Codex 문서 작업에서 전체 과정을 재시험한 것은 아니다.
- 웹 경로의 Elsevier·Wiley·ACS·RSC·IOP·Science·Taylor & Francis·PNAS·AIP·Oxford·IEEE·ChemRxiv 기록은 **Claude in Chrome 실측**이다. 선택자·파일명·순서는 참고하되 Codex 에서 모두 동작한다고 보고하지 않는다.
- macOS/Linux 설치·skill 재탐색, 기관 구독 접근, Codex 웹 다운로드와 실제 논문을 이용한 수집·색인 전체 흐름은 이번 작업에서 미검증이다.
- 실제 다운로드 시험은 사용자에게 출판사별 대상 논문과 본문/SI 목록을 제시하고 확인받은 뒤 한다. 확인된 출판사·날짜·도구·파일 검증 결과만 추가한다.

### 7.3 갱신

패키지를 갱신할 때는 로컬 변경을 먼저 확인하고, git 을 쓰는 설치는 `git pull --ff-only` 뒤 1절의 Codex 설치를 다시 한다. 설치본의 개인 수정은 교체 전에 보관한다. `.env` 와 논문 폴더의 설정·자료는 패키지 밖에 유지한다.

문서를 고치기 전에는 기존 파일을 `_history/<원본이름>_YYMMDD_HHMM.<확장자>` 로 남긴다. 시험 파일은 `_tmp/` 에 둔다. 이 Codex 어댑터를 고칠 때 `README.md`, 공용 `SKILL.md`, `references/` 의 수정이 필요하면 별도로 제안한다. 커밋·푸시는 사용자가 요청할 때만 한다.
