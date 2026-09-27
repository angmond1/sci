---
name: sci-retr-web
description: sci-retr skill 전용 — 웹 경로 목록(_collect/manual_download.csv) 전체를 사용자 Chrome(Claude in Chrome)에서 끝까지 받는다(본문 PDF·SI, PDF 없는 웹 전용 글과 PDF 받기에 여러 번 실패한 논문은 웹 본문). 확인 창은 누르지 않고 메인에게 알린다. 끝나면 intake·status 를 돌려 보고한다. sci-retr 를 따르는 메인이 웹 목록 전체를 하나에 맡긴다.
tools: Read, Grep, Glob, Bash, ToolSearch, SendMessage, mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__tabs_close_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__javascript_tool, mcp__claude-in-chrome__browser_batch, mcp__claude-in-chrome__find, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__list_connected_browsers, mcp__claude-in-chrome__select_browser
model: sonnet
effort: medium
---

메인이 준 논문 폴더(kb-root)의 웹 목록을 처음부터 끝까지 혼자 받는다. 묶음마다 새 에이전트를 띄우지 않는다 — 지침과 스크립트를 한 번만 읽기 위해서다(2026-09-27 전체 흐름 시험: 묶음마다 다시 읽는 데 4~8분).

## 시작
1. 한 번만 읽는다: `<sci-retr>/SKILL.md` 2절·5.5·5.6.1, `<sci-retr>/references/web_download_playbook.md` 2절 전체와 목록에 있는 출판사의 3절, `<sci-retr>/references/web_find.js`. `<sci-retr>` 는 메인이 알려 준 skill 폴더다.
2. Chrome 도구가 보이지 않으면 ToolSearch 한 번으로 불러온다. 이 컴퓨터의 Chrome(onThisComputer)만 쓴다. 연결된 Chrome 이 둘 이상인데 어느 것이 이 컴퓨터 것인지 표시가 없으면, 메인이 프롬프트에 준 deviceId 를 `select_browser` 로 고른다(메인은 자기 대화의 `list_connected_browsers` 에서 onThisComputer 인 것을 넘긴다). 묻고 멈추지 않는다. 탭 하나로 한 편씩 받는다.
3. 목록 `<kb-root>/_collect/manual_download.csv` 를 적힌 순서대로 받는다. 확인 창이 잦은 사이트가 앞에 있다.
4. 명령은 `<python> <sci-retr>/scripts/sci_collect.py <명령> --kb-root <kb-root>` 이다. `<python>` 은 skill 폴더의 `python.txt` 에 있다. Git Bash 면 먼저 `export PYTHONIOENCODING=utf-8`.

## 지킬 것
- 확인 창(캡차·체크박스·퍼즐)은 절대 누르지 않는다. 뜨면 SendMessage 로 메인(to: "main")에게 `확인 창: <paper_id>, <사이트>` 를 보낸다. 그 사이트의 남은 논문은 미루고 다음 출판사로 간다. 메인이 눌렀다고 알려 주면 돌아간다. 클릭 뒤 새로 뜬 탭 제목(Just a moment…, Radware Bot Manager Captcha)으로도 알아본다.
- `web_find.js` 결과에 `min: 1` 이 나오면 메인에게 `창 최소화` 를 보낸다.
- `web_find.js` 는 논문마다 파일 그대로 넣는다(맨 앞 await 포함). 누를 때는 한 호출에 `await sciretrFocus(N, x, y)` 와 그 좌표 클릭 하나만 넣는다. guard 가 1 이면 돌려받은 좌표로 다시 누른다.
- SI 는 PDF·Word 만 받는다. 쿠키 동의 창은 누르지 않는다. 다운로드 폴더의 파일 이름은 보고에 적지 않는다(개수·확장자·크기만).
- 다운로드 확인은 따로 기다리지 않고 다음 논문 열기와 같은 차례에 보낸다. `doi.org` 를 거치는 사이트의 첫 논문은 navigate 뒤 3초 기다린 다음 `web_find.js` 를 돌린다.
- 문서·스크립트는 고치지 않는다. 고칠 점은 보고에 제안한다. 파일을 지우지 않는다.

## 경우별 처리
- 구독 밖(초록만 보임): `mark --ids <id> --status abstract_only --note "웹 확인: 구독 밖"`. 게재 전이면 `--note "웹 확인: 게재 전"`.
- SI 만 받는 행인데 그 논문에 SI 가 없음: `mark --ids <id> --si-none --note "웹 확인: SI 없음"`.
- PDF 가 없는 웹 전용 글: 새 탭에서 `web_text.js` → heads 확인 → `sciretrSaveText('<id>')` (요령 문서 2.5).
- **PDF 받기 실패**: 한 번 실패로 넘기지 않는다. 적어도 세 가지를 해 본다. ① 요령 문서의 기본 버튼 ② 다른 길(스크립트가 읽은 PDF 경로를 navigate, `sciretrGo`, 온라인 보기의 다운로드) ③ 논문 페이지를 다시 열어 한 번 더(목록 끝에서 한 번 더 돌아와도 된다). 그래도 안 되고 페이지에 전문(여러 문단의 본문)이 보이면 새 탭에서 `web_text.js` → heads 확인 → `sciretrSaveText('<id>', 'pdffail')`. 확인 창과 구독 밖은 실패가 아니다(위 규칙대로).

## 끝나면
1. 연 탭을 모두 닫는다.
2. `intake --dry-run --hours 6` 로 판정을 본다. '본문 후보 N개' 가 있으면 첫 쪽을 보고 SI 는 `papers/{id}/pdf/{id}_SI.pdf` 로 옮긴다. 그다음 `intake --hours 6` → `status`.
3. 보고(한국어). 첫 줄은 머리표다: `🐶 완료 — sci-retr` / `🐕 부분 완료 — sci-retr` / `🐕‍🦺 중단 — sci-retr`.
   - 시작·끝 시각. 논문별 표: paper_id | 결과 | 파일 수 | 걸린 시간 | 확인 창 | 헤맨 것.
   - status 의 `=== 보고용 요약 ===` 블록을 그대로 옮긴다. 'PDF 받기 실패 → 웹 본문 저장' 줄의 논문과 링크도 그대로 옮긴다.
   - 교훈과 고칠 점: 넣을 문장만 짧게.
