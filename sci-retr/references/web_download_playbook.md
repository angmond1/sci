# 웹 다운로드 요령 — 출판사별 경험과 교훈

사용자가 평소 쓰는 Chrome 에서 Claude in Chrome 확장으로 논문 PDF·SI 를 받을 때 쓰는 요령이다. 2026-09-24 연습(6개 출판사 1편씩), 2026-09-25 1차 시험(6개 출판사 3편씩, 18편), 같은 날 이 문서대로 한 2차 시험(새 논문 18편), 여러 탭 시험 두 차례(4절), 2026-09-26 의 작은 창·재개 시험(5절)과 여섯 사이트(Taylor & Francis, PNAS, AIP, Oxford, IEEE, ChemRxiv) 1편씩 시험(3.7~3.12), 2026-09-27 첫 사용자 시뮬레이션(6개 출판사 1편씩, MDPI·Thieme 포함, 3.13~3.14)과 같은 날 전 출판사 연습(출판사마다 4편, 각 절의 '2026-09-27 연습' 항목)에서 얻었다. 여섯 사이트는 6편 12파일에 9분이 걸렸고, 시뮬레이션은 6편 9파일에 11.5분(한 편 약 2분, 요령이 없던 두 사이트와 죽은 주소·쿠키 창 때문)이 걸렸다. 웹 경로를 시작하기 전에 이 문서를 읽고, 첫 논문부터 이 순서대로 한다.

정책은 SKILL.md 2절과 publisher_matrix.md 맨 앞 공통 정책이 우선한다. 쿠키 동의는 사용자가 누른다. 논문 사이에 따로 기다리지 않고, 한 편이 끝나면 바로 다음 논문으로 간다(2026-09-25 사용자 지시). SI 는 문서(PDF, Word)만 받는다. 동영상·음성, 결정 구조 파일(CIF 등), 압축 파일(zip 등), 스프레드시트(Excel, CSV 등)는 받지 않는다(같은 날 사용자 지시). 결정 구조와 대형 스프레드시트 데이터가 대개 zip 이나 Excel 로 온다. 링크 글자나 파일 이름에서 형식을 보고 PDF·Word 만 누른다.

## 1. 시간

- 1차 시험에서 같은 출판사 안에서 편이 거듭될수록 빨라진 것은 주로 페이지 구조를 익혔기 때문이다. 버튼을 찾는 선택자, SI 링크 위치, 출판사마다 한 번 더 있는 단계(Wiley "열기", Science 온라인 보기, IOP SI 목록 페이지)를 알게 되자 헤매는 호출이 없어졌다.
- 시간은 페이지·파일을 기다리는 시간과, Claude 가 호출하고 결과를 확인하는 왕복 시간으로 이루어진다. 왕복 한 번에 5~10초가 들어, 호출 수를 줄이는 것이 가장 큰 단축이다.
- 2차 시험은 새 논문 18편을 이 문서대로 받아 16.7분이 걸렸다. 1차는 26분이었다. 한 편 중앙값은 60초에서 42.5초로 줄었다. 18편 중 13편이 예상 범위 안이거나 더 빨랐다.

| 출판사 | 1차 시험 | 2차 시험 (새 논문, 이 문서대로) | 예상 (2차 반영) | 예상을 넘은 편의 이유 |
|---|---|---|---|---|
| Elsevier | 201·66·32초 | 40·45·124초 | 30~45초 | 124초는 동영상 SI 를 재생기 메뉴로 저장한 시간 포함. 지금은 동영상 SI 를 받지 않는다 |
| Wiley | 212·262·82초 | 163·89·68초 | 70~90초, 페이지가 늦게 뜨면 45초 이상 더 | 163초는 페이지가 약 45초 늦게 뜸 |
| ACS | 79·50·38초 | 54·44·43초 | 40~55초 | 54초는 SI 미리보기 창이 커져 링크를 한 번 더 찾음 |
| RSC | 49·38·44초 | 32·35·39초 | 30~40초 | 없음 |
| ECS/IOP | 97·26·81초 | 28·35·34초 (셋 다 SI 없음) | SI 없으면 20~30초, 있으면 50~60초 | 35·34초는 당시 30초 간격을 맞추느라 5~6초 기다린 시간 포함 |
| Science | 93·49·54초 | 45·42·40초 | 40~45초 | 없음 |

- 논문 사이에 따로 기다리지 않는다. 2차 시험 때는 30초 간격 규칙이 있어 SI 없는 IOP 논문에서 몇 초씩 기다렸다. 지금은 규칙이 없어져 한 편이 끝나면 바로 다음 논문으로 간다.
- 정리 명령(intake)은 2차 시험 파일 32개를 4.5초에 처리했다.

### 1.1 전 출판사 연습 (2026-09-27, 출판사마다 4편, 96편)

- 메타 확정(resolve) 96편 2분 44초, 자동 수집 31편(Springer·Nature·Frontiers·PLOS·Beilstein·Copernicus·Cambridge 4편씩, APS 3편) 1분 23초.
- 웹 경로 59편은 네 묶음으로 받았다. 시간은 논문 페이지를 연 때부터 마지막 파일이 저장될 때까지, 헤맨 시간을 포함한다.

| 묶음 | 출판사 (한 편 중앙값, 범위) | 전체 |
|---|---|---|
| 1 | Elsevier 64초(22~103), Wiley 69초(55~93), ACS 39초(38~57), RSC 36초(33~40) | 16편 29파일 118.5 MB, 21.0분 |
| 2 | IOP 90초(65~119), Science 63초(16~79), T&F 32초(12~328), PNAS 31초(13~194) | 16편 26파일 81.2 MB, 29.8분(논문별 합 20.9분) |
| 3 | AIP 80초(43~141), ChemRxiv 41초(15~98), IEEE 66초(36~106), Oxford 29초(20~31) | 15편 17파일, 18.5분 |
| 4 | MDPI 19초(13~71), Thieme OA 42초, APS SI 19초, CCS·Renewables 72~205초, De Gruyter 133~204초 | 13편 17파일, 62.6분 |

- 4묶음이 느린 까닭: 시작 4분 뒤 작업 창이 최소화되어 클릭이 닿지 않았고(2.1), 원인을 찾는 데 약 8분, De Gruyter 가 네 번째 PDF 에서 막아(3.16) 30분 규칙대로 멈췄다.
- 오래 걸린 편의 이유: T&F 328초는 figshare 틀이 SI 링크를 가리고 스크린샷이 세 번 시간 초과, PNAS 194초는 SI 첫 클릭 무반응과 스크린샷 시간 초과, AIP 141초는 zip SI 를 잘못 받음.
- 구독 밖·게재 전: De Gruyter 1편(Purchase), APS PRL 1편(게재 전 accepted 페이지). `mark --status abstract_only` 로 초록만 저장.

### 1.2 전체 흐름 시험 (2026-09-27 오후, 출판사마다 3편, 81편)

- 12:37:25 시작 → 15:53:40 끝, 3시간 16분. 준비(무작위 선택·메타 확정 2.5분·자동 수집 1.3분) 15분, 웹 네 묶음 46.0·21.1·28.0·39.6분(49편 + SI 행 4 + 웹 본문 1), 묶음 사이 16분, 색인 2.5초, 한 줄 요약 22분(쓰기 19분).
- 결과: 전문 70, 웹 본문 1(Science Expert Voices), 초록만 9(미구독 6, Thieme 비OA 1, De Gruyter 구독 밖 2), 범위 밖 1(CCS 같은 논문 두 DOI), 실패 0. SI 23편 25파일. 한 줄 요약 79/81(철회 공지 1편은 비움).
- 확인 창: 1묶음 RSC 1번(사용자 약 3분), 2묶음 IOP 1번, 3·4묶음 0번.
- **느렸던 가장 큰 원인은 `web_find.js` 를 넣는 호출이다.** 에이전트는 논문마다 파일 전체를 도구 입력으로 다시 쓴다. 그 호출 하나를 쓰는 시간이 스크립트의 한글 양에 따라 크게 달랐다(클릭 등 다른 호출은 어느 묶음이나 중앙값 5~9초).

| 묶음 | 넣은 스크립트(중앙값) | 한 번 쓰는 시간(중앙값) | 합계 |
|---|---|---|---|
| 연습 4묶음 | 10,148자, 한글 981자 | 91초 | 22회 33.3분 |
| 1묶음 | 11,912자, 한글 1,412자 | 122초 | 16회 30.4분 (묶음 52분의 58%) |
| 3묶음 (에이전트가 주석을 빼고 넣음) | 8,431자, 한글 37자 | 24초 | 17회 6.5분 |
| 4묶음 (가벼운 판) | 9,294자, 한글 354자 | 56초 | 21회 17.9분 |

- 출력 토큰으로 보면 한글 한 글자가 약 6토큰이었다(3·4묶음 비교: 한글 +317자 → 출력 +1,885토큰, 호출당 +32초). browser_batch 안의 입력은 JSON 이라 한글이 `\uXXXX` 로 적히는 것으로 보인다. 그래서 스크립트 설명은 이 문서에 두고, 스크립트 주석은 짧은 영어로 둔다(2.4). 1묶음만 해도 주석 없는 판보다 약 26분이 더 들었다. 연습 4묶음이 62.6분 걸린 것도 이 몫(33분)이 컸다.
- 그 밖: 1묶음 ACS SI 링크 밀림으로 두 번 빗나감(약 5분, sciretrFocus 가 자리 멈출 때까지 기다리게 고친 뒤 3·4묶음 0번), 묶음마다 새 에이전트가 문서를 읽는 시간(첫 논문까지 3.7~7.5분), 이번에만 있던 일(SI 만 받는 행 4개, 웹 본문, figshare SI, 구독 밖 확인: 약 15분), 묶음 사이 공백(메인이 다음 묶음을 늦게 띄움 16분).
- 한 줄 요약은 같은 전용 에이전트가 오전에 35편 6.6분(11.7만 토큰)이었는데 이번에는 25~28편 묶음이 14.7~19.2분(5.7만~8.9만 토큰)이었다. 토큰이 더 적은데 느려 모델 응답 속도나 세 묶음 동시 실행의 영향으로 보인다(한 묶음만 따로 재 보지 않았다).

## 2. 공통 요령

### 2.1 시작 전

- Chrome 설정 두 가지를 `sci_collect.py doctor` 로 확인한다. `chrome://settings/content/pdfDocuments` 가 "PDF 다운로드" 가 아니면 PDF 보기 화면이 뜨고, 그 화면의 다운로드 버튼은 저장 창을 띄운다. `chrome://settings/downloads` 의 "다운로드 전에 각 파일의 저장 위치 확인" 이 켜져 있으면 파일마다 저장 창이 뜬다.
- 영어 Chrome 에서는 "열기" 버튼이 "Open" 이다. 위치는 같다.
- 연결된 브라우저가 둘 이상이면 이 컴퓨터의 것을 고른다(`list_connected_browsers` 다음 `select_browser`).
- `visibilityState` 가 hidden 이어도 스크린샷·클릭이 되는 때가 많다(2026-09-27 AIP·Oxford·IEEE·ChemRxiv 15편 내내 hidden 이었지만 모두 됨). 스크린샷이 하얗거나 시간 초과일 때만 사용자에게 창을 앞으로 가져와 달라고 한다.
- 단 `outerWidth` 가 0 이면(`web_find.js` 결과에 `min: 1`, `sciretrFocus` 가 ok false) 창이 최소화된 것이다. 스크린샷이 되더라도 클릭이 페이지에 닿지 않는다(2026-09-27 4묶음: 캡처 리스너 이벤트 0건, guard 로도 알 수 없었다). 바로 사용자에게 창을 앞으로 가져와 달라고 한다. 기다리는 동안은 스크립트로 읽은 파일 경로(쿼리 없는 것)를 navigate 로 연다(주소창에 친 것과 같다, 다섯 출판사 13개 저장). 페이지 스크립트 이동(`sciretrGo`)은 같은 탭의 두 번째 다운로드부터 Chrome '여러 파일 다운로드' 확인에 걸려 저장되지 않았다.
- 확장이 새로 만드는 Chrome 창은 대개 뒤에(최소화 상태로) 열린다(2026-09-26 두 번 확인. 2026-09-27 에는 처음부터 앞에 열린 적도 있다). 탭을 만든 뒤 스크립트로 `document.visibilityState` 와 `outerWidth` 를 읽어, hidden 이거나 0 일 때만 사용자에게 그 창을 앞으로 가져와 달라고 한다. 탭 그룹이 사라져 다시 만들 때도 같다.
- 새 탭 그룹 하나로 진행하고, 받는 탭은 화면 앞에 둔다. 한 창에서 앞에 나와 있지 않은 탭(이 문서에서 '뒤쪽 탭', `document.visibilityState` 가 hidden)은 Chrome 이 화면을 그리지 않아 스크린샷이 하얗거나 시간 초과가 난다. Chrome 창을 최소화하거나 다른 창에 완전히 덮여도 그렇게 될 수 있다. 그러면 사용자에게 그 탭을 앞으로 가져와 달라고 한다.
- 받을 논문과 파일(본문, SI)을 출판사별로 한 번에 알리고 확인을 받는다.
- 확인 창(Cloudflare "Just a moment…", Radware 등)이 뜬 탭은 닫거나 다른 주소로 옮기지 않고 확인을 통과할 때까지 둔다. 그동안 다른 출판사는 새 탭에서 받고, 통과하면(탭 제목이 논문으로 바뀜) 그 탭에서 이어 받는다(2026-09-27 6편 시험: RSC SI·IOP·Science 세 곳에서 확인 창이 떴는데 탭을 닫거나 다음 논문으로 옮겨 확인 화면이 사라졌다). 같은 시험에서 목록을 한 바퀴 돈 뒤 다시 가자 RSC SI 와 Science 본문은 확인 창 없이 받혔다. 확인 창 탭 제목이 계속 'Just a moment…'·Radware 로 보여도 파일은 이미 받아졌을 수 있다(IOP·ACS 본문) — 탭 제목만 보지 말고 다운로드 폴더를 확인한다. 같은 파일이 두세 번 받아지면 intake 가 글 내용으로 가려 하나만 옮긴다.

### 2.2 한 편 처리 순서

링크 찾기는 같은 폴더의 `web_find.js` 로 한다(세션에서 한 번 읽어 두고 페이지마다 javascript_tool 로 실행, 결과 형식과 함수는 2.4). 본문 PDF·SI 링크 후보를 번호와 좌표로 돌려주고, 클릭은 하지 않는다. 스크립트는 HTML 을 다 읽을 때까지(그림 등은 최대 3초 더) 기다린 뒤, 링크 후보가 나타날 때까지 1초 간격으로 스스로 확인하고 나타나는 즉시 돌려준다(합계 약 20초까지, `ms` 가 실제 기다린 시간). 다 읽기 전에 돌려주면 아래쪽 SI 가 아직 없고 좌표가 나중에 바뀐다(2026-09-27 AIP x 529→608). 좌표 x, y 는 `window.sciretrFocus(N)` 이 그 요소를 화면 가운데(상단 고정 막대 여백 아래)로 옮긴 뒤의 화면 좌표 예상이다. 페이지 맨 위·끝에서 가운데까지 못 가는 것도 반영한다. 그래서 페이지를 연 뒤 고정 시간을 기다리지 않고 바로 이 스크립트를 돌린다(2026-09-27 사용자 지적: 고정 대기는 빨리 뜨면 낭비, 늦게 뜨면 부족). 20초 뒤에도 비면 `title` 로 확인 화면인지 보고, 아니면 3절의 출판사별 선택자로 직접 찾는다. 2026-09-27 확인: RSC(SI `article-supplement`, 본문 `article-pdf`), ACS(`sifile1`, `Open PDF`), Wiley(접힌 "Supporting Information" 제목, `/doi/pdf/` Download PDF, 온라인 보기 `/doi/epdf/` 는 online 표시)에서 요령 문서와 같은 링크를 찾았다. 링크 후보를 매번 새 스크립트로 찾던 것을 이 스크립트 하나로 대신해 왕복과 판단을 줄인다.

1. **열고 찾기 (호출 1번)**: 논문 주소 열기와 `web_find.js`(준비될 때까지 스스로 기다림). 스크린샷은 사이트의 첫 논문이나 결과가 이상할 때만 작게(0.3~0.4배) 찍는다.
2. **누르기 (호출 1~2번)**: SI 먼저, 본문 나중. 한 호출에 `await sciretrFocus(N, x, y)` 와 (x, y) 클릭을 넣는다(sciretrFocus 는 async, await 가 없으면 결과가 {}). sciretrFocus 는 요소를 보이게 한 뒤 자리가 1초 동안 그대로일 때까지 기다리고(최대 3초) 좌표를 정한다 — 2026-09-27 ACS SI 링크가 가운데로 옮긴 뒤 1~3초 사이에 약 90 px 밀려 guard 0 인데도 두 번 빗나갔다. 한 호출에 클릭 두 개를 넣었는데 앞 클릭이 guard 로 막히면 뒤 클릭만 실행되므로(Elsevier 에서 SI 대신 View PDF 가 먼저 눌림), SI 와 본문은 앞 결과를 확인한 뒤 따로 누른다. 결과에서 guard 가 0 이고 hit 가 true 면 제대로 눌린 것이다. guard 가 1 이면 예상 자리에 그 요소가 없어 스크립트가 클릭을 막은 것이니(엉뚱한 곳은 눌리지 않는다) 돌려받은 x, y 로 다시 누른다. 확대 캡처나 스크린샷으로 자리를 확인하지 않는다. 2026-09-27 에 화면 가운데라고 가정한 클릭이 세 번 빗나갔다(ChemRxiv 페이지 끝 y 669, 상단 고정 막대 여백 108 px 때문에 y 522, AIP 옆 칸이 늦게 떠 x 529→608).
   - 페이지 요소가 아니라 Chrome 화면이라 이 방법을 쓸 수 없는 버튼: Wiley·IEEE "열기"(영어 Chrome 은 "Open", 가운데보다 40~50 px 아래), Science 온라인 보기의 다운로드 아이콘(오른쪽 위). 이것만 화면 기준 자리로 누른다.
3. **확인 (다음 논문과 한 차례에)**: 보조 탭 닫기, 다운로드 폴더 확인, 다음 논문 열기는 서로 독립이라 한 차례에 함께 보낸다.

- SI 를 먼저 받는 이유: Elsevier 는 View PDF 뒤 추천 논문 창이 페이지를 덮고, Wiley·Science 는 본문 받기가 논문 페이지를 떠난다. IOP 만 본문을 먼저 받는다. SI 가 다른 페이지에 있기 때문이다.
- 좌표는 누르기 직전에 읽는다. 늦게 뜨는 요소 때문에 배치가 수십 px 밀린다(ACS SI 미리보기 창, Wiley SI 펼침, Elsevier 추천 창 닫기, IOP). 예상 좌표가 어긋나면 `sciretrFocus` 의 guard 가 클릭을 막는다.
- 버튼 위치는 외워 두지 않는다. 누를 때마다 스크립트로 그 페이지에서 요소의 위치를 읽는다(확인은 `sciretrFocus` 의 hit·guard). 그래서 모니터 해상도, 창 크기, 브라우저 확대 비율이 사용자마다 달라도 같은 방법으로 된다. 사이트가 개편되어 요소 이름이나 문구가 바뀔 때만 이 문서를 고친다. 창이 아주 좁으면 사이트가 모바일 배치로 바뀌어 버튼이 메뉴 안으로 숨을 수 있다.
- 창이 작아도 된다. 1366×768 창(페이지 1355×586)에서 여섯 출판사 6편을 같은 절차로 받았다(2026-09-26). 여섯 사이트 모두 데스크톱 배치를 유지했고 버튼을 다시 찾은 일이 없었다. 작은 창에서 자리가 화면 기준인 버튼도 그대로였다. Wiley "열기"는 가운데 +45 px, Science 온라인 보기의 다운로드 아이콘은 오른쪽 끝에서 40 px 안쪽·위에서 30 px.
- 스크립트가 'Inspected target navigated or closed' 로 끝나면 페이지가 한 번 다시 뜬 것이다. 사이트의 첫 논문에서 흔하고(2026-09-27 Science·T&F·PNAS 첫 편), `doi.org` 를 거쳐 여는 사이트는 그 뒤에도 난다(De Gruyter). `doi.org` 를 거치는 사이트의 첫 논문은 navigate 뒤 같은 묶음 안에서 3초 기다린 다음(computer wait) `web_find.js` 를 돌린다. 끊기면 스크립트를 다시 써야 해 약 55초가 더 든다(2026-09-27 4조: 3회 끊김, 3초 기다림을 넣은 뒤로는 0회).
- navigate 로 파일 주소를 열면 도구가 다운로드 응답 전에 돌아온다. 다운로드 폴더에 그 파일이나 `.crdownload` 가 보인 뒤에 탭을 다음 논문으로 옮긴다(2026-09-27 12 MB PDF 1회 취소).
- 쿼리로 파일을 가리는 링크(Atypon `downloadSupplement?doi=…&file=…`)는 창이 보일 때 누른다. 주소를 결과로 받지 않는다(쿼리가 든 값은 가려진다). `web_find.js` 는 이런 링크를 파일 이름(글자)으로 나눠 보여 주고, 형식이 파일 이름에만 있으면(7z 등) 글자로 거른다.
- 누르기 직전 확인은 스크린샷·확대 캡처 대신 `sciretrFocus` 결과의 `hit`(elementFromPoint)로 한다. 확인과 클릭을 한 호출에 넣을 수 있고 30초 시간 초과를 피한다(2026-09-27 PNAS 13~37초). 스크린샷은 사이트의 첫 논문을 연 직후나 결과가 이상할 때만 찍는다. 스크롤한 뒤나 무거운 페이지(T&F figshare 틀, PNAS 끝부분)의 스크린샷은 다섯 번 시간 초과가 났다.
- 스크린샷이 시간 초과로 끝나면 보이는 영역이 축소 크기로 남기도 한다(2026-09-27 T&F innerWidth 1289→275, 모바일 배치). 스크립트의 `w` 가 갑자기 줄었으면 그 좌표로 누르지 말고 같은 주소로 다시 이동한다.
- 틀·안내 창이 링크를 가려 누르기 어려우면 `sciretrGo(N)` 으로 그 링크 주소로 탭을 옮긴다(누른 것과 같다). 첨부 파일 주소면 탭은 논문 페이지에 남고 몇 초 안에 저장된다.
- javascript_tool 결과는 약 1,000자에서 잘린다. `web_find.js` 는 그 안에 맞춰 짧게 낸다. 다른 스크립트도 결과를 짧게 받는다(항목 몇 개, 글자 수십 자).
- 수천 px 를 순간 스크롤한 직후의 스크린샷·확대 캡처는 하얗게 나올 수 있다. 1~2초 뒤 다시 찍고, 하얗게 나온 채로는 같은 호출에서 누르지 않는다.
- 쿠키 동의 창이 배경막으로 페이지 전체 클릭을 막으면(Thieme 의 OneTrust) 쿠키 창을 누르지 말고, 스크립트로 읽은 PDF·SI 링크의 경로로 탭을 옮겨 받는다(3.14). 그래도 안 되면 사용자에게 그 페이지의 다운로드 버튼을 직접 눌러 달라고 한다.
- 사이트별 확대(Chrome 의 사이트 설정)가 100% 가 아니면 스크린샷 좌표계가 달라진다(2026-09-27 Elsevier 125%: 페이지 폭 882). 아래의 `innerWidth` 비율 규칙으로 처리한다. 사용자 PC 마다 다를 수 있다.
- 확장의 둥근 배지(별 모양)가 페이지 왼쪽 아래에 떠서 버튼을 가릴 수 있다. Elsevier "View PDF" 의 왼쪽 절반을 가렸다(2026-09-26). 버튼의 오른쪽 부분을 누른다.
- 스크린샷 좌표계와 페이지 폭(`innerWidth`)이 다르면 스크립트 좌표에 그 비율을 곱한다. 2차 시험 창은 스크린샷 1316, 페이지 1343 이라 0.98 을 곱했다. 곱하지 않으면 오른쪽 버튼일수록 어긋난다.
- 누르기는 확장의 실제 클릭(좌표, 또는 `find` 가 준 ref)으로 한다. Elsevier 에서 ref 클릭이 배치 변화로 추천 논문 링크에 떨어진 적이 있다. 배치가 바뀌는 페이지는 좌표로 누른다.
- 부드러운 스크롤은 쓰지 않는다. 스크린샷과 겹쳐 DOI 링크를 누른 적이 있다.
- 스크립트 결과로 링크 주소를 통째로 받지 않는다. 확장이 쿼리 문자열이나 토큰이 든 값을 `[BLOCKED]` 로 가린다. 경로만(`?` 앞) 또는 글자만 받는다. outerHTML 이나 본문 글자 조각을 넣어도 결과 전체가 `[BLOCKED: Cookie/query string data]` 로 가려진다(2026-09-27 두 번). 참·거짓과 개수만 받는다.
- 창 크기가 바뀌면 좌표도 바뀐다(2026-09-25 에 818, 1022, 1074, 1148, 1316 px 로 바뀜). 좌표는 그 호출의 스크린샷 좌표계를 따른다.
- 새 탭을 만든 직후 같은 차례에 옛 탭을 닫으면 탭 그룹이 통째로 사라지고 새 탭도 그룹 밖으로 빠진다(2026-09-27). 옛 탭은 새 탭에서 한 동작을 마친 뒤 닫는다.
- 탭 닫기는 묶음 안에 넣지 않는다. 묶음 안에서 탭을 닫으면 뒤 동작이 깨진다. 닫은 뒤 탭 목록을 다시 읽는다.
- 페이지가 아직 그려지는 중이면 스크립트가 `document.body` 없음 오류를 내거나 45초 시간 초과로 끝난다. 뜰 때까지 기다림과 스크린샷으로 확인한다. 페이지가 뜬 직후의 확대 캡처도 시간 초과가 나기 쉽다(2026-09-27 두 번). 2~3초 기다렸다 찍고, 직전 스크린샷으로 자리가 확인됐으면 확대 캡처 없이 누른다.

### 2.3 다운로드 폴더

- 같은 이름이 이미 있으면 Chrome 이 " (1)", " (2)" 를 붙인다. intake 는 내용으로 가리므로 그대로 둔다.
- 확인은 최근 몇 분 안의 파일만 본다(`find ~/Downloads -maxdepth 1 -newermt '-3 minutes'`). 다운로드 폴더에는 사용자 파일이 많다. 파일 이름은 나열하지 않는다(개인 파일 보호).
- 다운로드 확인에 따로 `sleep` 을 두지 않는다. 확인 명령은 다음 논문 열기와 같은 차례에 보낸다(2026-09-27 따로 기다린 시간이 16편에 약 5분).
- 큰 SI 는 `.crdownload` 가 사라질 때까지 기다린다. 30 MB 에 약 15초 걸렸다.
- 정리는 묶음 끝에 intake 한 번이다. 먼저 `--dry-run` 으로 못 가린 파일을 본다. 한 시간 안에 받은 것만 보려면 `--hours 1`.

### 2.4 web_find.js 결과와 함수

`web_find.js` 에는 주석을 짧게 둔다. 에이전트가 논문마다 이 파일 전체를 javascript_tool 입력으로 다시 써 넣기 때문이다. 2026-09-27 전체 흐름 시험 1·2조에서 논문 사이 시간이 논문당 약 95초였고, 그 큰 몫이 18,089자(한글 약 2,000자)를 매번 쓰는 시간으로 보였다(2조 에이전트 제안). 머리 설명을 이 절로, 웹 본문 저장을 `web_text.js`(2.5)로 옮겨 8,761자가 됐다. 설명은 여기에 적고 스크립트에는 넣지 않는다. 가벼운 판으로 받은 4조는 논문 사이 간격 중앙값이 57초였다(1·2조 약 95초). 그래도 `web_find.js` 가 든 호출 하나를 쓰는 데 49~69초가 들어 브라우저 시간의 절반이었고, 짧은 클릭 호출은 5~8초였다. 스크립트에는 한글을 넣지 않는다(주석은 짧은 영어, 결과 문구만 한글). 넣는 호출 하나를 쓰는 시간이 한글 1,412자일 때 122초, 37자일 때 24초였다(1.2, 한글 한 글자 약 6토큰).

- 넣는 법: javascript_tool 에 파일을 그대로 넣는다. 맨 앞 `await` 가 없으면 결과가 `{}` 로 빈다. Codex 의 evaluate_script 는 함수를 받으므로 `async () => { return await (async () => { … })(); }` 로 감싼다.
- 결과(JSON, 1,000자 안): `t` 제목 40자, `v` visibilityState, `w` innerWidth, `dpr` devicePixelRatio, `ms` 실제로 기다린 시간, `sih` SI 절 제목(h1~h4·summary·button)이 있으면 1, `min` 1 이면 창이 최소화됨(outerWidth 0, 2.1).
- `s` 는 SI 후보, `m` 은 본문 후보다. 항목은 `[번호, 글자 24자, 경로 끝 36자, x, y]` 또는 `[번호, 글자, 경로, "접힘"]`.
  - x, y 는 `sciretrFocus(번호)` 뒤의 화면 좌표 예상이다. 이미 화면 안에 보이고 가려지지 않았으면 지금 자리(스크롤 안 함, sticky 옆 막대 등, 2026-09-27 CCS 예상 469·실제 912 를 고침), 아니면 화면 가운데(상단 고정 막대 여백 scroll-padding-top 아래)로 옮긴 뒤의 자리다. 페이지 맨 위·끝에서 가운데까지 못 가는 것도 반영한다. 두 줄로 꺾인 링크는 첫 줄 글자 위다. 폭 0 인 빈 줄은 빼고 고른다(2026-09-27 APS SI 는 그림 하나만 감싼 링크라 첫 줄이 빈 줄이었고, 좌표가 그림 모서리 1 px 밖으로 나와 guard 가 막았다).
  - 글자가 24자보다 길면 앞 11자…뒤 12자로 줄여 파일 이름의 형식(pdf·docx·7z)이 보이게 한다.
  - "접힘" 은 화면에 안 보이는 링크다(접힌 절, 닫힌 메뉴, 틀에 가려 크기 0). 눌러 펼치거나, 파일 주소면 `sciretrGo(번호)` 로 받는다.
  - Silverchair 사이트(AIP·ACS·RSC·Oxford)의 SI 는 경로 끝 대신 `{형식}/{코드}` 를 보인다. 형식 칸이 pdf·docx·doc 가 아닌 것은 뺀다(2026-09-27 AIP zip).
  - m 항목 끝의 "online" 은 온라인 보기(epdf·reader)라 대개 누르지 않는다(Science 만 온라인 보기를 거친다).
  - 경로가 빈 s 항목은 접힌 절의 제목(Wiley `a.accordion__control`)이나 누르면 목록이 열리는 버튼(IEEE "Supplemental Items")이다. 눌러 펼친 뒤 다시 돌린다.
  - 경로가 "#"·"js" 인 항목은 목차 이동·메뉴다(AIP 는 SI 가 없어도 늘 있다). 진짜 후보 뒤에 둔다. SI 유무는 s 의 파일 링크와 `sih` 로 본다.
  - 보이는 링크 → 접힘 → 목차·메뉴 순이고, 같은 주소가 여럿이면 앞의 것만 남는다(PNAS 화면 밖 옆 패널, IEEE 크기 0 복제본). 쿼리로 파일을 가리는 링크(`downloadSupplement?…&file=`)는 파일 이름(글자)까지 봐서 뭉치지 않게 한다(2026-09-27 CCS 3개→1개).
- 기다림: HTML 을 다 읽을 때까지, 이어서 그림 등이 뜰 때까지(최대 3초) 기다린 뒤, 후보가 나타날 때까지 1초 간격(사용자 지정)으로 확인하고 나타나는 즉시 돌려준다(합계 약 20초까지). 끝내 비면 `t` 로 확인 화면("Just a moment…")인지 본다.
- 거르는 것: 다른 사이트 링크(SI 파일 도메인 ars.els-cdn.com·silverchair-cdn.com·IOP S3 는 허용), 다른 논문 링크(주소에 이 논문 PII·DOI 가 없는 /pii/·/doi/ 링크, SI 포함, 2026-09-27 De Gruyter 관련 논문), 본문 속 'Figure S1'·'Table S2' 참조 링크, 호·권 링크(/vol/…/suppl/, /issue/ — 2026-09-27 Oxford `/mam/issue/27/S1` 이 MDPI SI 규칙에 걸림), 사이트 자료(/pb-assets/), 묶음 버튼('PDF and Supporting…'), 학회 초록집 호 이름(Oxford 'Supplement_1'), 'suppliers'·'/data-sharing-policy' 같은 바닥글, 규소 'Si'(대문자 SI 만 SI 로 본다), zip·7z·스프레드시트·동영상(.mpg 등)·데이터(.txt)·PowerPoint(경로 끝이나, 형식이 쿼리에만 있는 링크는 글자의 파일 이름으로 — Atypon downloadSupplement, MDPI 'ZIP-Document'). MDPI SI 주소 끝 `/s1` 은 SI 로 보되 숫자가 긴 Elsevier PII 주소(`/abs/pii/S0360…`)는 SI 가 아니다(2026-09-27 View Abstract 를 SI 로 잡음).
- `window.sciretrFocus(번호, x, y)`(async): 한 호출(browser_batch)에 `await window.sciretrFocus(번호, x, y)` 와 그 좌표 클릭을 함께 넣는다(2.2 의 2). 요소가 이미 보이면 그대로, 아니면 화면 가운데로 옮기고, 자리가 멈출 때까지 1초 간격으로 확인한 뒤(최대 3초) 실제 화면 좌표(x, y)와 `hit`(그 좌표에 그 요소가 있는지, elementFromPoint)를 준다. 예상 좌표(x, y)를 함께 주면 그 자리에 이 요소가 없을 때 다음 클릭 한 번을 투명한 막으로 받아 버린다(`guard` 1, 8초 뒤 저절로 없어짐). guard 가 1 이면 돌려받은 x, y 로 다시 누른다. hit 가 false 면 다른 것에 덮인 것이니 그 좌표로 누르지 않는다. 창이 최소화돼 있으면 ok false 와 이유를 준다. 스크린샷 좌표계가 innerWidth 와 다르면 클릭 좌표에만 (스크린샷 폭 ÷ innerWidth) 를 곱하고, sciretrFocus 에는 이 스크립트의 좌표를 그대로 준다.
- `window.sciretrGo(번호)`: 그 링크 주소로 탭을 옮긴다(링크를 누른 것과 같고, 주소는 출력하지 않는다). 틀·안내 창이 링크를 가리거나 "접힘" 인 파일 링크에 쓴다(T&F figshare 등). 같은 탭에서 두 번째 다운로드부터는 Chrome 의 '여러 파일 다운로드' 확인에 걸릴 수 있다. 저장되지 않으면 그 링크는 누른다.

### 2.5 웹 전용 글의 웹 본문 (web_text.js)

PDF 가 없고 본문이 웹에만 있는 글(2026-09-27 Science "Expert Voices")은 초록만으로 두지 않고 웹 본문을 저장한다(사용자 지시). 본문과 참고문헌만 담고, 관련·추천 논문, 지표·인용 수, 광고, 공유, 뉴스레터, 메뉴, 머리말·꼬리말은 뺀다.

1. `web_find.js` 결과에 본문 후보가 없고(`m` 빈 목록, 약 20초 뒤) 페이지에 본문이 보이면, 같은 탭에 `web_text.js` 를 그대로 넣는다. 넣으면 통계를 돌려준다: `chars` 글자 수, `paras` 문단 수, `refs` 참고문헌 항목 수, `removed` 뺀 상자 수, `heads` 남은 소제목.
2. `heads` 에 추천·관련 글, 뉴스, 지표 같은 소제목이 없으면 `window.sciretrSaveText('<paper_id>')` 로 `<paper_id>.sciretr.html` 을 내려받는다. 있으면 저장하지 말고 그 소제목을 보고한다.
3. intake 가 이 파일을 `papers/{id}/html/{id}.html` 로 옮기고 source.md 를 만든다. 원문상태는 '전문(웹 본문, PDF 없음)' 이다.

- 본문 상자는 문단 글이 가장 많은 상자와 거의 같은(90% 이상) article·main 중 가장 안쪽이다(main 보다 article, 글이 적은 추천 카드 article 은 빠짐). 본문만 든 상자(#bodymatter 등)는 초록·참고문헌이 밖에 있어 article·main 이 없을 때만 쓴다. 참고문헌이 본문 상자 밖에 있으면 따로 붙인다.
- 구독 밖이라 초록만 보이면 쓰지 않는다. 글이 500자보다 짧으면 `sciretrSaveText` 가 ok false 를 준다. 그때는 `mark --status abstract_only --note "웹 확인: 구독 밖"`.
- **새 탭에서 저장한다.** 그 탭에서 앞서 파일을 받았으면 `sciretrSaveText` 가 ok true 를 줘도 저장되지 않는다(Chrome 의 여러 파일 자동 다운로드 제한으로 보임, 2026-09-27 4조). 저장 뒤 다운로드 폴더에서 `<paper_id>.sciretr.html` 을 확인한다.
- 문단은 `<p>` 와 `div[role=paragraph]`(Science) 를 함께 센다. Atypon 옆 패널(`core-collateral-*`: Information & Authors, Metrics & Citations, View Options, 참고문헌 사본, Figures·Tables·Media, Share), 말풍선(aria-hidden, `references-pop-up` 등), 옆 패널 제목(Information, Authors, View options 등 정확히 그 글자)은 뺀다. 본문 문단의 절반 넘게 담은 상자는 이름이나 소제목이 걸려도 지우지 않는다. 제목은 `citation_title` → `dc.Title` → `og:title` → 탭 제목(" | 사이트" 뺌) 순.
- **PDF 받기 실패에도 쓴다**(2026-09-27 사용자 지시): 적어도 세 가지(기본 버튼 → 다른 길: PDF 경로 navigate·`sciretrGo`·온라인 보기 다운로드 → 페이지를 다시 열어 한 번 더)를 해도 PDF 가 안 받아지고 페이지에 전문(여러 문단의 본문)이 보이면 `sciretrSaveText('<paper_id>', 'pdffail')`. 파일 머리에 표시가 남아 intake 가 원문상태를 '전문(웹 본문, PDF 받기 실패)' 로 두고, 보고 블록이 논문 페이지 링크와 함께 알린다. 구독 밖(초록만 보임)이면 쓰지 않는다.
- 실제 Science 페이지(2026-09-27, Expert Voices 1편): 첫 판은 `div[role=paragraph]` 를 문단으로 세지 않아 옆 패널(게재 정보·저작권·저자 소속·이메일)과 빈 'View options'·'References' 제목까지 저장했다. 고친 판은 제목과 본문 11문단(10,931자)만 저장했다. 이 글에는 참고문헌 목록이 없다.
- 시험(2026-09-27, 흉내 페이지): 머리 메뉴, 본문 밖 추천 카드, 공유 막대, 본문 속 지표 상자, "Recommended" 절, "Latest News" 절, 뉴스레터 가입 상자, 꼬리말을 모두 뺐고 제목·초록·본문 4문단·참고문헌 2개는 남았다.

## 3. 출판사별

### 3.1 Elsevier (ScienceDirect)

- 주소 `https://www.sciencedirect.com/science/article/pii/{PII}`. KIST 망에서 확인 창 없이 3초 안에 뜬다.
- SI 파일은 다른 도메인(`ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc{n}.{확장자}`)에 있다. `web_find.js` 가 이 도메인을 허용하고, 추천·인용 논문의 View PDF(다른 PII)는 뺀다(2026-09-27).
- 사이트 확대가 125% 인 PC 에서는 뜬 직후 좌표가 확대 전 값으로 나온다. 누르기 직전에 `sciretrFocus` 로 좌표를 다시 읽고 (스크린샷 폭 ÷ innerWidth) 를 곱한다. View PDF 뒤 확인 단계 탭(pdfft)이 앞으로 나와 논문 탭 스크린샷이 하얗게 나오는 것은 정상이다.
- 새 배치(2026년 논문)는 상단 고정 막대의 View PDF 가 왼쪽이고 바로 오른쪽 약 160 px 에 "Download full issue" 가 붙어 있다. 누르지 않는다.
- News & Views·Preview 같은 짧은 기사는 SI 가 없고 두 쪽이라 intake 가 본문 길이 경고를 낸다. 정상이다.
- SI: 부록 "Appendix A. Supplementary material/data" 의 "Download: Download …(크기)" 링크. 선택자는 `a[href*="mmc"]` 가운데 글자가 "Download" 로 시작하는 것이다. 오른쪽 목록의 "Multimedia component 1" 도 같은 파일을 가리켜 먼저 잡힐 수 있다. 리뷰 논문은 SI 가 없기도 하다.
- SI 가 여럿일 수 있다(Word 와 동영상 등). 받을 SI 를 모두 먼저 받고 View PDF 는 마지막에 누른다.
- 동영상(mp4) SI 는 받지 않는다(2026-09-25 사용자 지시). 누르면 새 탭에서 재생만 되고, 저장하려면 재생기 ⋮ 메뉴를 거쳐 70초쯤 더 든다. 부록의 "Download all supplementary files" 는 동영상까지 묶어 받을 수 있어 쓰지 않는다.
- 본문: SI 로 내려간 뒤에는 상단 고정 막대의 "View PDF" 를 누른다. 바로 오른쪽 "Download full issue"(호 전체)는 누르지 않는다. SI 가 없으면 제목 아래 "View PDF"(`a.accessbar-utility-component`).
- "View PDF" 글자는 태그가 나뉘어 있다. 글자로 찾을 때는 공백을 정리한 뒤 `/view\s*pdf/i` 로 찾고, 화면 위쪽(y 60 이하)에 보이는 것을 고른다.
- 누르면 확인 단계 탭(`pdfft`)이 열리고 3~5초 안에 저장된다. 그 탭은 따로 닫는다.
- SI 와 View PDF 는 한 호출에 넣지 않는다. SI 클릭이 guard 로 막히면 View PDF 가 먼저 눌려 추천 창이 SI 를 덮는다(2026-09-27 전체 흐름 시험). SI 저장을 확인한 뒤 View PDF 를 누른다.
- View PDF 를 누른 뒤 탭 목록에 pdfft 탭이 없으면 추천 창을 X 로 닫고 View PDF 를 한 번 더 누른다(2026-09-27 1회).
- Int. J. Electrochem. Sci.(10.20964, 지금은 Elsevier 가 펴냄)는 View PDF 가 늦게 나타나 `web_find.js` 가 20초 가까이 걸리기도 한다(2026-09-27).
- View PDF 뒤 추천 논문 창이 페이지를 덮는다. X 만 누른다. 안의 "Download (N) PDFs" 는 다른 논문들이다. 창을 닫으면 배치가 바뀌므로 좌표를 다시 읽는다.
- 파일: `1-s2.0-{PII}-main.pdf`, `1-s2.0-{PII}-mmc1.pdf` 또는 `.docx`, 동영상은 `-mmc2.mp4`. 리뷰 본문은 30 MB 를 넘기도 한다.
- 링크 글자에 형식이 나온다("Download Acrobat PDF file", "Download Word document", "Download zip file", "Download video"). PDF 와 Word 만 누르고, zip·스프레드시트·동영상은 누르지 않는다.
- 확인 창이 계속 반복되면 멈추고 몇 시간 뒤 다시 한다(2026-09-24 에 한 번, 몇 시간 뒤 풀림).

### 3.2 Wiley (TDM 토큰이 없을 때)

- 주소 `https://onlinelibrary.wiley.com/doi/{DOI}`. Chemistry Europe 저널은 `chemistry-europe.onlinelibrary.wiley.com`, Advanced 계열은 `advanced.onlinelibrary.wiley.com` 에서 열린다.
- 페이지가 늦게 뜰 때가 있다(대개 8초 안, 1차 시험에 1분 넘게, 2차 시험에 약 45초 늦게 뜬 편이 하나씩). 고정 시간을 기다리지 않고 `web_find.js` 를 돌린다. 링크가 나타나는 즉시 돌아오고, 20초 뒤에도 비면 한 번 더 돌린다. Cloudflare "Verification successful. Waiting…" 에서 멈추면 새로고침한다.
- 아래쪽 "AI Companion" 안내는 무시한다. 다만 이 안내 창이 펼친 SI 링크 자리를 덮을 수 있다. 그러면 SI 링크를 화면 가운데로 다시 스크롤한 뒤 누른다. SI 링크가 두 줄이면 사각형 가운데가 글자 밖일 수 있으니 첫 줄 글자 위를 누른다.
- SI 제목은 주소가 없는 `a.accordion__control` 이다. `web_find.js` 가 경로 없는 s 항목으로 내고, 펼치기 전 파일 링크는 "접힘" 으로 낸다. 제목을 눌러 펼친 뒤 스크립트를 다시 돌린다(2026-09-27).
- 저자 사진이 있는 기사(Concept·Review)는 사진이 늦게 떠서 끝부분 Download PDF 가 수백 px 밀린다. 가운데로 스크롤 → 1.5초 → `sciretrFocus` 로 한 번 더 스크롤한 뒤 좌표를 읽는다.
- SI 파일 이름은 `-sup-0001-SuppMat.pdf` 와 `-supp-0001-SuppMat.docx` 두 가지가 있다.
- SI: 본문 끝 접힌 "Supporting Information"(h2)을 화면 가운데로 스크롤한 뒤 그 자리를 눌러 펼친다. 펼친 뒤 `a[href*="downloadSupplement"]`(`…-sup-0001-SuppMat.pdf`, `.docx`, `misc_information.pdf` 등)의 좌표를 읽고 누른다. 새 탭 없이 저장된다. 파일 이름이 .pdf·.doc·.docx 로 끝나는 것만 누른다. 리뷰는 SI 가 없기도 하다.
- 본문: 맨 끝 오른쪽의 작은 "Download PDF"(`/doi/pdf/`). 위쪽 "PDF" 는 온라인 보기라 쓰지 않는다. 가운데로 스크롤해 좌표를 읽고 누른다. 탭이 `/doi/pdf/` 로 넘어가고, 5~8초 뒤 어두운 화면에 파일 이름과 "열기" 버튼이 뜬다.
- "Download PDF" 를 누른 뒤 고정 7초를 기다리지 않는다. 3초 뒤부터 1초 간격으로 작은 스크린샷(0.3배)을 찍어 "열기"가 보이는 즉시 누른다(대개 5~8초). "열기" 화면은 Chrome 자체 화면이라 스크립트로는 볼 수 없다. "열기"는 화면 가운데보다 40~50 px 아래에 있다. 누르면 2~3초 안에 저장된다.
- 파일: `{저널} - {연도} - {제1저자} - {제목 앞부분}.pdf`, `{코드}-sup-0001-suppmat.pdf`.
- TDM 토큰이 있으면 웹 대신 자동 경로로 받는다.

### 3.3 ACS

- 주소가 Silverchair 형 `pubs.acs.org/{저널코드}/article/…` 로 넘어간다(2026-09-27). 본문 속 'Figure S1'·'Table S1' 링크가 모두 SI 주소라 `web_find.js` 가 뺀다. SI 는 글자나 aria-label 에 'sifile' 이 든 링크, 또는 'Supporting Information' 절 설명 끝의 '(PDF)' 글자나 설명 전체 링크다(경로 `/article-supplement/{번호}/pdf/{코드}_si_001/`, 2026-09-27 전체 흐름 시험 3편은 sifile 링크 없이 이 모양).
- SI 링크는 가운데로 옮긴 뒤 1~3초 사이에 약 90 px 위로 밀린다(늦게 커지는 SI 미리보기 창). 이것 때문에 guard 0·hit true 인데도 두 번 빗나갔고, `sciretrFocus` 가 자리가 멈출 때까지 기다리게 바꿨다(2.4). SI 와 Open PDF 는 따로 누른다.

- 주소 `https://pubs.acs.org/doi/{DOI}` 는 Silverchair 주소로 넘어간다. 4초 안에 뜬다. Cloudflare 확인 창은 2026-09-24 에 한 번 떴고, 09-25 6편에서는 없었다.
- SI: 본문 속 "Figure S1", "Table S1" 링크도 SI 주소에 걸리므로 무시한다. 실제 파일은 aria-label "Download sifile1"(글자 "sifile1") 링크로, SI 미리보기 창 바로 아래에 있다. 미리보기 창이 늦게 커져 링크가 밀린다. `await sciretrFocus(N, x, y)` 가 자리가 멈출 때까지 기다린 뒤 좌표를 준다. 미리보기 창의 Download 버튼은 쓰지 않는다.
- 본문: 제목 아래 "Open PDF"(`a.article-pdf-button`). SI 저장을 확인한 뒤 따로 누른다(2.2). 새 탭 없이 3~4초 안에 저장된다.
- SI 링크 글자 끝에 형식이 붙는다(예: "sifile1- pdf file"). SI 가 여럿이면 pdf 만 받는다.
- 파일: `{코드}.pdf`, `{코드}_si_001.pdf`.

### 3.4 RSC

- SI 링크 칸이 본문 폭 전체라 칸 가운데는 글자 오른쪽 빈칸이다. `web_find.js`·`sciretrFocus` 는 글자 쪽(왼쪽 40px) 좌표를 준다. 툴바 PDF 는 네 편 모두 같은 자리였다(2026-09-27).

- 주소는 `https://doi.org/{DOI}` 로 열면 `https://pubs.rsc.org/{저널}/article/{권}/{호}/{쪽}/{id}` 로 넘어간다. 조용한 SSO 확인 뒤 4초 안에 뜬다. 2026-09-27 전체 흐름 시험 첫 편에서는 Cloudflare 확인 창('Performing security verification', 탭 제목 'Just a moment...')이 떴다. 이 화면에서 `web_find.js` 는 20초 빈 결과, 스크린샷은 30초 시간 초과였다. 사용자가 한 번 눌러 준 뒤 이어진 2편에는 뜨지 않았다.
- SI: "Supplementary data" 절의 "Supplementary information (PDF)"(`a[href*="/article-supplement/"]`). 새 탭 없이 저장된다. 링크가 페이지 끝 가까이에 있으면 가운데까지 스크롤되지 않으니, 가운데라고 가정하지 말고 좌표를 읽는다.
- 본문: 툴바 "PDF"(`a.article-pdfLink`). 내려간 뒤에는 상단 고정 막대에 있고, SI 가 없어 스크롤하지 않았으면 제목 아래 원래 자리에 있다. 3~4초 안에 저장된다.
- SI 목록에서 "Supplementary information (PDF)" 처럼 PDF·Word 인 것만 받는다. "Crystal structure data (CIF)", 스프레드시트, zip 은 받지 않는다. 주소의 형식 칸(`/article-supplement/{번호}/{형식}/`)으로도 알 수 있다.
- 가장 고르게 빨랐다(1차 38~49초, 2차 32~39초).
- 파일: `{코드}.pdf`, `{코드}1_suppl.pdf`.

### 3.5 ECS/IOP

- 2026-09-27 연습(4편): SI 는 "Supplementary data" 버튼을 누르는 대신 탭을 `https://iopscience.iop.org/article/{DOI}/data` 로 옮긴다. 버튼은 그래픽 초록이 늦게 떠서 좌표를 읽은 뒤 약 290 px 밀렸다. /data 페이지의 파일 링크(IOP S3 서명 주소, `web_find.js` 가 허용)는 좌표로 누른다. SI 3편이 모두 Word(`jes{코드}supp1.docx`·`.doc`)였다.

- 주소 `https://iopscience.iop.org/article/{DOI}`. 쿠키 동의 창은 누르지 않는다. 2026-09-27 전체 흐름 시험에서 첫 PDF 클릭으로 열린 새 탭이 Radware 확인 창(탭 제목 'Radware Bot Manager Captcha')에 멈췄다. 확인 창은 클릭 뒤 탭 목록에 뜬 새 탭 제목으로 알아본다. 사용자가 통과시킨 뒤 같은 PDF 가 두 번 저장됐다(intake 가 같은 본문 중복으로 보고 하나만 옮긴다). 이후 2편은 확인 창 없이 3~4초에 저장됐다.
- 본문 먼저: "PDF" 버튼(`a[href$="/pdf"]`, 새 탭). 내려간 뒤에는 오른쪽 위 고정 "PDF". 새 탭이 잠깐 열렸다 닫히며 3~4초 안에 저장된다.
- SI 나중: 초록 아래 "Supplementary data" 버튼(`a[href$="/data"]`)을 누르면 SI 목록 페이지(`/article/{DOI}/data`)로 간다. 거기서 파일 링크("Supplemental Material" 등)를 누른다. PDF·Word 만 받고 README, zip, 스프레드시트는 받지 않는다.
- "Supplementary data" 버튼 가장자리를 누르면 넘어가지 않는다. 가운데를 누르고 주소가 `/data` 로 바뀌었는지 본다.
- SI 가 없는 논문이 많다. 2차 시험의 1999~2007년 논문 3편은 모두 SI 가 없어 PDF 버튼만 눌렀고 20초 안에 끝났다.
- SI 파일 링크는 저장소(S3) 주소에 서명 값이 붙어 있다. 주소만 따로 열면 접근 거부 화면이 뜨므로, 목록 페이지에서 링크를 눌러 받는다. 파일 이름이 `JES_{권}_{호}_{번호}_suppdata.pdf` 인 것도 있다.
- 파일: `{제1저자}_{연도}_{저널약어}_{권}_{논문번호}.pdf`. SI 는 `jes{코드}supp1.docx`, 옛 논문은 `1960.docx`(예시)처럼 숫자뿐이다. intake 가 Word 앞부분의 제목으로 가린다.

### 3.6 Science

- 2026-09-27 연습(4편): 온라인 보기가 "Loading publication (N MB)" 를 띄우는 동안 다운로드 아이콘("Download PDF • 크기", 오른쪽 위)은 반응하지 않는다. 누른 뒤 3초 안에 파일이 생기지 않으면 한 번 더 누른다. SI 를 받느라 내려간 뒤에는 SI 저장을 확인하고 상단 고정 막대의 빨간 아이콘을 누른다(2.2, 한 호출에 클릭 두 개를 넣지 않는다). SI 유무는 `a[href*=suppl_file]` 개수로 본다. Perspective 는 SI 가 없다.

- 주소 `https://www.science.org/doi/10.1126/science.{코드}`. 대개 확인 창 없이 뜨지만, 첫 접속에서 Cloudflare 의 "Just a moment…/Performing security verification" 화면에 20초 넘게 멈추기도 한다(2026-09-27). 그 화면에서는 스크린샷이 시간 초과로 실패하고 체크박스는 없었다. 15초쯤 기다렸다 새로고침하면 열린다. 오른쪽 "RECOMMENDED" 추천 창이나 아래쪽 뉴스레터 안내가 뜨지만 버튼을 가리지 않았다. 가리면 X 를 누른다.
- SI 먼저: "Supplementary Materials" 절의 "DOWNLOAD"(`a[href*="suppl_file"]`, 크기 표시). 새 탭 없이 저장된다. PDF 만 받고, 동영상 묶음(Movies)과 데이터 파일(Data S1 등, zip·Excel)은 받지 않는다. "MDAR Reproducibility Checklist" PDF 는 보고 양식이라 받지 않는다. 링크 주소에 토큰이 들어 있어 스크립트 결과로 파일 이름을 통째로 받으면 가려지므로, 확장자와 `mdar` 여부만 받는다.
- 본문: 빨간 PDF 아이콘(제목 아래 오른쪽, 내리면 상단 고정 막대)을 누르면 5초 안에 온라인 보기(`/doi/epdf/`)가 열린다(아이콘 링크는 `/doi/reader/` 이고 열리면 `/doi/epdf/` 로 넘어간다. 찾을 때 둘 다 본다). 오른쪽 위 둥근 청록색 다운로드 아이콘("Download PDF • 크기")을 누르면 2~3초 안에 저장된다. 대안은 도구 막대 "View Options" 의 "DOWNLOAD PDF".
- 빨간 아이콘과 온라인 보기의 다운로드 아이콘은 한 호출에서 이어서 누를 수 있다(빨간 아이콘 뒤 5초, 다운로드 아이콘은 화면 기준 자리). SI "DOWNLOAD" 는 그 앞 호출에서 따로 누른다. 2차 시험 3편이 모두 40~45초였다.
- Science Advances 에서 `web_find.js` 가 주는 `/doi/pdf/` "Download PDF" 는 2편 모두 다른 것에 가려져 있었다(hit false, guard 가 막음, 2026-09-27). 누르지 말고 빨간 아이콘으로 간다.
- SI 가 현재판과 원본판(v1) 두 개로 보이면 현재판만 받는다.
- 파일: `science.{코드}.pdf`. SI 는 `science.{코드}_sm.pdf`, `science.{코드}_sm.v2.pdf`, `{코드}-{저자}-sm.pdf`, `{코드}_fu_sm.pdf` 처럼 여러 가지다.
- PDF 가 없는 웹 전용 글(2026-09-27 E2E, Science "Expert Voices"): 빨간 PDF 아이콘·View Options 의 DOWNLOAD PDF 가 없고 본문이 웹에만 있다. 초록만으로 두지 않고 웹 본문을 저장한다(사용자 지시). `web_find.js` 가 본문 후보 없이 끝나면 같은 탭에 `web_text.js` 를 넣어 heads(남은 소제목)에 RECOMMENDED·관련 글·뉴스·지표가 없는지 보고, `sciretrSaveText('<paper_id>')` 로 `<paper_id>.sciretr.html` 을 받는다. intake 가 source.md 로 만든다(2.5, SKILL 5.5).

### 3.7 Taylor & Francis (2026-09-26, 1편)

- 2026-09-27 연습(4편): SI 파일은 `a[href*="/action/downloadSupplement"]`(글자 "Download MS Word (… KB)" 등)다. `/doi/suppl/` 는 파일이 아니라 "Supplemental" 탭이다. 페이지가 뜨고 몇 초 뒤 figshare 틀이 이 링크를 숨기고(크기 0) 그 페이지 스크린샷은 30초 시간 초과가 난다. 누르지 말고 `sciretrGo(N)` 으로 링크 주소로 탭을 옮긴다. 본문도 "Download PDF"(`/doi/pdf/`) 를 `sciretrGo` 로 옮기면 된다. 탭은 논문 페이지에 남고 2~4초 안에 저장된다(2편 12·20초).

- 주소 `https://www.tandfonline.com/doi/full/{DOI}`. KIST 망에서 확인 창 없이 뜬다.
- 본문: 페이지 맨 아래 참고문헌 뒤의 작은 "Download PDF"(`a[href*="/doi/pdf/"]`, 글자 "Download PDF"). 가운데로 스크롤해 좌표를 읽고 누르면 새 탭 없이 바로 저장된다(8 MB 에 몇 초). 상단 고정 막대의 초록 "View PDF" 는 온라인 보기(`/doi/epdf/`)라 쓰지 않는다.
- SI: "Supplemental material" 절의 `a[href*="/doi/suppl/"]` 링크(이번 논문에는 없었음).
- 파일 이름은 논문 제목이다. intake 는 본문 DOI·제목으로 가린다.
- 2026-09-27 전체 흐름 시험(3편, SI 없음): 맨 아래 "Download PDF" 를 `sciretrFocus` 와 클릭으로 바로 받았다(편당 약 1분). 누를 때 빈 탭('Untitled')이 잠깐 떴다가 저절로 닫힌다. 따로 닫지 않는다.

### 3.8 PNAS (2026-09-26, 1편)

- 2026-09-27 연습(4편): 본문은 참고문헌 뒤 "DOWNLOAD PDF"(`/doi/pdf/`) 다. 같은 경로의 옆 패널 "PDF" 가 화면 밖에 먼저 있어 `web_find.js` 가 화면 밖 링크를 뺀다. 4편 모두 확인 화면 없이 논문 페이지에 머문 채 저장됐다. SI 첫 클릭이 반응하지 않은 적이 있다. 3초 안에 파일이 없으면 한 번 더 누른다. "DOWNLOAD PDF AND SUPPORTING INFORMATION"(묶음)은 누르지 않는다. SI 파일 이름은 `pnas.{코드}.sapp.pdf` 이고 intake 가 SI 로 가린다.

- 주소 `https://www.pnas.org/doi/{DOI}`. 확인 창 없이 뜬다.
- SI 먼저: "Supporting Information" 절의 "DOWNLOAD"(`a[href*="/doi/suppl/"]`, 파일 `pnas.{번호}.sapp.pdf`). 가운데로 스크롤해 누르면 바로 저장된다. 데이터 파일(xlsx 등)은 받지 않는다.
- 본문: 참고문헌 뒤 "Download PDF"(`a[href*="/doi/pdf/"]`, 글자 "Download PDF"). 누르면 같은 탭이 Cloudflare "Performing security verification… Verification successful" 화면을 거쳐 저장된다(약 15초). 그 화면이 남아 있어도 파일이 왔으면 다음 논문으로 간다. 제목 아래 빨간 PDF 아이콘은 온라인 보기(`/doi/epdf/`)라 쓰지 않는다.
- 파일: `{저자}-et-al-{연도}-{제목 앞부분}.pdf`, `pnas.{번호}.sapp.pdf`.
- 2026-09-27 전체 흐름 시험(3편): "DOWNLOAD PDF" 뒤 확인 화면 없이 5~15초에 저장됐다. SI 목록에 데이터(`.sd01.txt`)와 동영상(`.sm01.mpg`)이 같은 "DOWNLOAD" 글자로 나온다. `web_find.js` 가 이제 이 둘을 거른다. `.sapp.pdf` 만 누른다.

### 3.9 AIP (2026-09-26, 1편)

- 2026-09-27 연습(4편): 본문 "PDF" 를 누르면 새 탭("Untitled")이 열렸다 저절로 닫히며 4~15초 뒤 저장된다(6 MB 에 11~15초). SI 는 본문 끝 "Supplementary Material" 절의 링크이고 형식이 주소의 형식 칸(`/article-supplement/{번호}/{형식}/`)에 있다. pdf·docx 일 때만 누른다(`web_find.js` 가 나머지를 뺀다. 경로 끝만 보고 zip 을 받은 적이 있다). 목차의 "SUPPLEMENTARY MATERIAL"(`#`)과 Views 메뉴의 "Supplementary Material"(`js`)은 SI 가 없는 논문에도 있어 SI 유무 판단에 쓰지 않는다. 4편 중 SI 는 1편(zip)뿐이었다. `sih` 가 1 인데 s 에 파일 링크가 없으면 SI 가 받지 않는 형식(zip 등)이라 거른 것이다(2026-09-27 전체 흐름 시험 1편).

- 주소는 `https://doi.org/{DOI}` 로 열면 `pubs.aip.org/aip/{저널}/article/…` 로 넘어간다(RSC 와 같은 Silverchair). 확인 창 없이 뜬다. 쿠키 동의 창은 누르지 않는다. 아래쪽 버튼을 가리면 가운데로 스크롤한다.
- 본문: 제목 아래 도구 막대의 "PDF"(`a.article-pdfLink`, 새 탭). 가운데로 스크롤해 누르면 새 탭이 잠깐 열렸다 닫히며 저장된다(3~4초).
- SI: "Supplementary Material" 절의 링크(이번 논문에는 없었음).
- 파일: `{논문번호}_1_{DOI 끝}.pdf` (예 `123303_1_5.0325740.pdf`).

### 3.10 Oxford (2026-09-26, 1편)

- 2026-09-27 연습(3편): Cloudflare 확인 화면은 첫 편에서만 약 7초 떴고, 둘째 편부터는 1~2초 안에 저장됐다. 저장됐으면 더 기다리지 않는다. 학회 초록집(주소에 `Supplement_1`)도 "PDF"(`/article-pdf/…`)가 본문이다. "< Previous"·"Next >" 는 다른 논문이다. 구독 밖이면 주소가 `/article-abstract/…?redirectedFrom=fulltext` 로 바뀌고 "Get access"·"You do not currently have access to this article" 가 보이며 PDF 링크가 없다. KIST 가 기관으로 인식돼도 그렇다(CSJ Chemistry Letters, 10.1246 은 이 사이트로 연결된다).

- 주소는 `https://doi.org/{DOI}` 로 연다(`academic.oup.com/{저널}/article/…`, Silverchair). 논문 주소를 직접 치면 저널 첫 화면으로 갈 때가 있어 DOI 로 연다. 확인 창 없이 뜬다.
- SI 먼저: 끝부분 "Supplementary data" 절(`#supplementary-data`)의 목록(`.dataSuppLink`)에 파일이 하나씩 있다. 이번 논문은 그림 S1~S4, 표 S1 이 PDF 5개로 나뉘어 있었고 통합 파일은 없었다. 목록의 PDF·Word 를 모두 받는다. 목록이 늦게 채워지므로 비어 보이면 잠깐 기다린다. 본문 속 "Supplementary Fig. S1" 같은 인라인 링크도 같은 파일(`silverchair-cdn.com … Content_public`)이라 그것을 눌러도 된다. 누르면 바로 저장된다.
- 본문: 상단 고정 막대의 "PDF"(`a[href*="article-pdf"]`, 왼쪽 위). 누르면 같은 탭이 Cloudflare 확인 화면을 거쳐 저장된다(약 15초). 2026-09-27 전체 흐름 시험 2편은 그 화면도 뜨지 않았다.
- SI 를 누른 뒤에는 본문 "PDF" 가 상단 고정 막대(왼쪽 위)로 옮겨 가 첫 `web_find.js` 좌표가 맞지 않는다. guard 가 준 좌표로 다시 누른다(2026-09-27).
- 파일: `{코드}.pdf`(예 `deag140.pdf`), `{코드}_supplementary_figure_s1.pdf`.

### 3.11 IEEE (2026-09-26, 1편)

- 2026-09-27 연습(4편): "PDF" 뒤 3초 안에 어두운 화면과 "열기"가 떴다. "열기"는 가운데 x, 가운데 y+42 px 로 일정하다(2026-09-27 전체 흐름 시험 3번 모두 맞음). "PDF" 는 `sciretrFocus` 결과(guard 0)를 확인한 뒤 누르고, "열기"는 3초 뒤 따로 한 호출로 누른다. "PDF" 클릭이 guard 로 막혔는데 같은 호출의 "열기" 자리 클릭이 실행되면 페이지의 엉뚱한 곳을 누른다. "열기"를 누르지 않으면 45초가 지나도 파일이 생기지 않는다(1편 확인). 파일이 안 생기면 "열기"를 한 번 더 누른다. 받는 중에 탭을 다음 논문으로 옮겨도 끊기지 않았다(17.5 MB, 약 50초). SI 는 본문 끝 "Supplemental Items" 버튼(주소 없음)을 누르면 주소가 `/document/{번호}/media` 로 바뀌며 파일 카드가 나온다. 카드 링크는 글자 없는 `…/supp1-{번호}.pdf` 이고, 크기 0 인 숨은 복제본이 먼저 있다(`web_find.js` 가 보이는 것을 앞에 둔다). SI 도 논문 제목 이름으로 저장되어 본문에 " (1)" 이 붙는다. intake 는 SI 첫 줄 "Supplementary File" 로 가린다.

- 주소는 `https://doi.org/{DOI}` 로 열면 `ieeexplore.ieee.org/document/{번호}` 로 넘어간다. 확인 창 없이 뜬다. 쿠키 동의 창은 누르지 않는다.
- 본문: 제목 아래 빨간 "PDF"(`a[href*="stamp/stamp.jsp"]`). 누르면 같은 탭에 PDF 보기 페이지가 열리고, Chrome 의 "PDF 다운로드" 설정 때문에 어두운 화면에 `getPDF.jsp` 와 "열기" 버튼이 뜬다(Wiley 와 같음). 화면 가운데보다 40 px 아래를 누르면 저장된다.
- SI: IEEE 는 "Supplemental Items" 절에 있을 때만 있다(이번 논문에는 없었음). 본문 속 그림 링크(`/mediastore/`)는 SI 가 아니다.
- 파일 이름은 제목의 공백을 밑줄로 바꾼 것이다.

### 3.12 ChemRxiv (2026-09-26, 1편)

- 2026-09-27 연습(4편): 본문 링크는 빨간 PDF 아이콘(글자 없음)과 미리보기 틀 아래 "Download PDF" 둘이고 주소가 같다. "Download PDF" 는 페이지 끝 가까이라 가운데까지 스크롤되지 않고(y 약 669), 이 사이트는 상단 고정 막대 여백이 108 px 라 가운데로 온 요소도 y 가 약 522 다. `web_find.js` 의 좌표가 이것을 반영한다. SI 는 "Supplementary Material" 절의 "DOWNLOAD"(`/doi/suppl/…/suppl_file/supporting_information.pdf`, 이름이 늘 같음)이고 4편 중 1편에만 있었다. 한 편에 15~20초, SI 가 있으면 약 1분.

- 주소는 `https://doi.org/{DOI}` 로 열면 `chemrxiv.org/doi/full/{DOI}` 로 넘어간다. 확인 창 없이 뜬다. 쿠키 동의 창은 누르지 않는다.
- 본문: 페이지 안의 PDF 미리보기 틀(어두운 상자, "열기" 버튼)은 쓰지 않고, 그 바로 아래의 "Download PDF"(`a[href*="/doi/pdf/"]`, 글자 "Download PDF")를 누른다. 새 탭 없이 바로 저장된다.
- SI: "Supplementary materials" 절의 링크(이번 논문에는 없었음).
- 파일: `chemrxiv.{번호}_v{판}.pdf`.

### 3.13 MDPI (2026-09-27, 1편)

- 2026-09-27 연습(4편, 창 최소화 중): "Download PDF" 는 닫힌 메뉴 속이라 `web_find.js` 가 "접힘" 으로 낸다. 첫 편은 `sciretrGo` 로 25초, 나머지는 경로 `/{ISSN}/{권}/{호}/{번호}/pdf` 를 navigate 로 열어 13초에 받았다. SI 는 "Supplementary Materials" 절의 "ZIP-Document"(`…/s1`)라 4편 중 2편이 zip(받지 않음), 2편은 SI 가 없었다. PDF SI 는 "PDF-Document"(`…/s2` 등)로 보인다.

- 주소는 `https://doi.org/{DOI}` 로 열면 `www.mdpi.com/{저널 번호}/{권}/{호}/{번호}` 로 넘어간다. 확인 창 없이 뜬다. 자동 경로가 막혔던 논문도 사용자 Chrome 에서는 바로 열렸다.
- 본문: 제목 왼쪽 위 "Download ▾" 를 누르면 메뉴가 열린다. 그 안의 "Download PDF" 를 누른다. 바로 아래 "Download PDF with Cover" 는 표지가 붙은 판이라 누르지 않는다. 새 탭 없이 저장된다.
- SI: "Supplementary Materials" 절의 링크(있을 때). 대개 zip 이라 받지 않는다.
- 파일: `{저널}-{권}-{번호}.pdf` (예: `catalysts-10-01276.pdf`).
- 2026-09-27 전체 흐름 시험(3편): 본문은 첫 편부터 `/{ISSN}/{권}/{호}/{번호}/pdf` 를 navigate 로 연다. `sciretrGo` 는 그 탭의 첫 다운로드만 저장됐다(둘째 편 30초 허비). SI 는 3편 모두 ZIP-Document 라 받지 않았다.

### 3.14 Thieme (2026-09-27, 1편, 미구독 출판사의 Open Access 논문)

- 2026-09-27 연습(SynOpen 1편): 초록 페이지의 "Download PDF" 경로는 `/products/ejournals/pdf/{DOI}.pdf` 이고 href 앞뒤에 줄바꿈이 있다(`web_find.js` 가 다듬는다). navigate 로 열면 쿠키 창과 관계없이 42초에 저장됐다.

- 주소는 `https://doi.org/{DOI}` 로 연다. Crossref 가 준 `thieme-connect.de/DOI/DOI?…` 주소는 404 다.
- OneTrust 쿠키 창이 배경막으로 페이지 전체 클릭을 막는다. 쿠키 창은 누르지 않는다. 페이지 스크립트로 SI 링크와 본문 PDF 링크의 경로(`/products/ejournals/pdf/…`, `/media/…`)를 읽어 그 주소로 탭을 옮기면 저장된다(2.2 의 주소 이동 방식). 페이지를 옮기면 쿠키 창은 저절로 사라진다.
- 파일: `{DOI 끝}.pdf` (예: `a-2309-6737.pdf`), SI 는 `…-si.pdf` 류.
- 2026-09-27 전체 흐름 시험(2편): 쿠키를 이미 골라 둔 뒤라 쿠키 창이 없으면 `sciretrFocus` 와 클릭으로 바로 받는다(29~35초).

### 3.15 CCS Chemistry 와 그 밖의 Atypon 형 사이트 (2026-09-27, 1편)

- 2026-09-27 연습(CCS Chemistry 2편, Renewables 2편 — 둘 다 chinesechemsoc.org): "PDF download" 와 오른쪽 "Supporting Information" 은 sticky 옆 막대(`article__sidebar`) 안이다. 스크롤해도 가운데로 오지 않아 예상 좌표가 443 px 틀렸다. `web_find.js` 는 이제 이미 보이는 요소는 스크롤하지 않고 지금 자리를 준다. SI 파일은 `/doi/suppl/{DOI}` 목록 페이지의 `/action/downloadSupplement?doi=…&file={파일 이름}` 이고 형식은 파일 이름에 있다(pdf·docx·7z). 같은 SI 가 PDF·Word 두 판이나 교정본 Word 로 겹쳐 올라온 논문이 있었다(intake 가 같은 내용은 옮기지 않는다). 본문 속 SI 링크가 두 줄로 꺾여 사각형 가운데가 줄 사이 틈에 떨어진 적이 있다(`web_find.js` 는 이제 첫 줄 글자 위를 준다). PDF 첫 쪽이 저널 홍보 쪽인 논문이 있다(요약 재료는 제목 자리부터 자른다).

- `www.chinesechemsoc.org`(CCS Chemistry)는 설정 표에 없는 "그 외" 사이트다. 자동 요청은 403 으로 막히지만 사용자 Chrome 에서는 확인 창 없이 열린다. `https://doi.org/{DOI}` 로 연다.
- Taylor & Francis·PNAS 와 같은 Atypon 구조다. 도구 막대의 "PDF" 는 온라인 보기(`/doi/epdf/`)라 쓰지 않고, 페이지 아래 작은 "PDF download"(`a[href*="/doi/pdf/"]`)를 누르면 바로 저장된다.
- 그림마다 "Download PowerPoint" 링크가 있어 "download" 글자로 찾으면 12개가 섞여 나온다. `/doi/pdf/` 경로로 찾는다.
- SI: "Supplemental material" 절의 링크(review 는 없기도 하다).
- 2026-09-27 전체 흐름 시험(2편): "PDF download" 는 예상 y(441)와 실제 y(855~856)가 달라 2편 모두 guard 1 이었다. 엉뚱한 곳은 눌리지 않았으니 돌려받은 좌표로 바로 다시 누른다. SI 는 목록 페이지에서 `web_find.js` 를 한 번 더 돌려 Word 를 받았다.
- 같은 논문이 온라인 먼저 판(`ccschem.025…`)과 최종판(`ccschem.026…`) 두 DOI 로 오기도 한다. 하나를 `mark --status out_of_scope` 로 두면 intake 가 남은 쪽으로 가린다(2026-09-27 고침, 전에는 '여러 논문에 해당' 으로 남았다).
- 처음 보는 사이트는 이 순서로 본다: ① `a[href*="/doi/pdf/"]` 또는 `citation_pdf_url` 메타 ② 글자가 "Download PDF"·"PDF download" 인 링크 ③ 그래도 없으면 사용자에게 버튼을 직접 눌러 달라고 한다.

### 3.16 De Gruyter (2026-09-27, 4편)

- `www.degruyterbrill.com`. 설정 표에 없는 "그 외" 사이트다. 자동 요청은 202 로 막히고, 사용자 Chrome 에서는 확인 창 없이 열린다. `https://doi.org/{DOI}` 는 `/document/doi/{DOI}/html` 로 넘어간다.
- 본문: "Download Article (PDF)" = `/document/doi/{DOI}/pdf`. 구독 밖이면 "Purchase Article 30,00 €" 가 보이고 PDF 링크가 없다(4편 중 1편 → `mark --status abstract_only`). 2026-09-27 전체 흐름 시험에서도 3편 중 2편(Pure Appl. Chem., Materials Testing)이 구독 밖이었다. 이때 `web_find.js` 는 20초 빈 결과를 낸다. 짧은 뉴스 글(Chemistry International)은 PDF 1쪽이라 본문 길이 경고가 나는 것이 정상이다.
- 바닥글·관련 논문 링크가 SI 후보로 잘못 잡혔었다('suppliers', '/data-sharing-policy', 관련 논문 제목의 'Si'). `web_find.js` 가 이제 거른다.
- 약 13분 동안 PDF 3개를 받은 뒤 넷째 요청에서 HTTP 202 빈 확인 화면(본문 0자)이 나왔다. 그 사이트는 멈추고 30분 뒤 논문 페이지부터 다시 열어 받았다(원칙 7). 차단되지 않는 간격을 찾는 시험은 하지 않는다.

### 3.17 APS (2026-09-27, 웹 2건)

- 게재 전 논문은 `/prl/accepted/{DOI}` 로 가며 초록만 있다(제목 'Accepted Paper', PDF 링크 없음). `web_find.js` 는 20초를 다 기다린 뒤 빈 결과를 낸다. `mark --status abstract_only --note "웹 확인: 게재 전"` 으로 두고 게재 뒤 다시 받는다(`mark --status resolved` 후 collect).
- SI: 도구가 목록 페이지를 못 읽으면 웹 목록에 SI 행이 올라간다. `link.aps.org/supplemental/{DOI}` 는 초록 페이지 `#supplemental` 로 가고, 파일은 `/{저널}/supplemental/{DOI}/{파일}.pdf` 다. navigate 로 열어 19초에 받았다.
- 2026-09-27 전체 흐름 시험: SI 링크가 그림 하나만 감싼 링크라 첫 사각형이 폭 0 인 빈 줄이었고, 좌표가 그림 모서리 1 px 밖으로 나와 guard 가 한 번 막았다. 돌려받은 좌표로 다시 눌러 받았다.

### 3.18 Cambridge (2026-09-27 전체 흐름 시험, SI 행 3건과 Oxford 로 넘어간 1편)

- 자동 경로로 받는 출판사다(SKILL 6.1). 웹 경로는 자동으로 받지 못한 논문과 도구가 SI 행을 올린 논문만이다.
- `https://doi.org/{DOI}` 는 `www.cambridge.org/core/journals/…/article/…/{ID}` 로 넘어가고 확인 창 없이 뜬다. 위의 'Temporary Disruption' 막대와 아래 쿠키 창은 누르지 않아도 된다.
- SI 유무는 제목 아래 탭으로 본다. 'Article · Figures · (Peer reviews) · Metrics' 뿐이고 본문에 supplementary 글자가 없으면 SI 가 없다. 그때는 `mark --ids <paper_id> --si-none --note "웹 확인: SI 없음"` 으로 웹 목록의 SI 행을 닫는다.
- 웹 목록의 SI 주소가 `/core/services/authors/publishing-supplementary-material` 이면 사이트 바닥글의 저자 안내 페이지다(2026-09-27 도구가 SI 목록 페이지로 잘못 잡아 3편에 SI 행이 생김, 지금은 거른다). 받지 않는다.
- Microscopy and Microanalysis 옛 DOI(`10.1017/S14319276…`)는 Oxford 로 넘어간다. 3.10 대로 "PDF" 를 누른다.
- 이번 세 편은 모두 SI 가 없어서 SI 가 있을 때의 탭 이름과 파일 주소 모양은 아직 모른다.

### 3.19 Royal Society (2026-09-27 전체 흐름 시험, 3편, 미구독 출판사의 Open Access 논문)

- 미구독 출판사라 초록만 저장하지만, Open Access 논문은 한 번 자동 시도하고 안 되면 웹 경로로 받는다(SKILL 6.1).
- `https://doi.org/{DOI}` 는 `royalsocietypublishing.org/{저널}/article/…` 로 간다. Silverchair 구조(AIP·Oxford 와 같음)이고 확인 창 없이 열렸다. 아래쪽 쿠키 창은 누르지 않는다.
- 본문: 도구 막대 "PDF"(`a.article-pdfLink`, 경로 `/article-pdf/doi/10.1098/{코드}/{번호}/{코드}.pdf`). 누르면 "Untitled" 탭이 잠깐 열렸다 닫히며 3~6초에 저장된다. 첫 편은 보조 탭이 Cloudflare "Just a moment…" 로 남았고(체크박스 없음, 누르지 않음) 약 2.5분 뒤 저절로 통과해 같은 PDF 를 한 번 더 저장했다(intake 가 하나만 옮긴다). 파일이 이미 왔으면 보조 탭을 닫고 다음 논문으로 간다.
- SI ①: 본문 끝 "Supplementary data"(`#supplementary-data`, `.dataSuppLink`)의 `/article-supplement/{번호}/{형식}/…`. 형식 칸으로 판단한다(zip 은 `web_find.js` 가 뺀다).
- SI ② figshare: 본문 문구 "Electronic supplementary material is available online at https://doi.org/10.6084/m9.figshare.c.{N}". 다른 사이트라 `web_find.js` 에 보이지 않으므로 `a[href*=figshare]` 로 본다. 컬렉션 페이지 → 항목(`a[href*="/articles/"]`) → 항목 페이지의 파일 이름으로 형식을 확인하고, PDF·Word 만 `https://rs.figshare.com/ndownloader/files/{번호}` 를 navigate 로 연다(2초). xlsx·zip 은 받지 않는다. "clear version" 과 "with revised section highlighted" 가 함께 있으면 clear version 만 받는다. figshare 쿠키 창은 누르지 않는다.
- Views 메뉴의 "Supplementary Material"(js)은 SI 가 없어도 있다. SI 유무는 `#supplementary-data` 와 figshare 링크로 본다.

## 4. 여러 탭 동시 진행 시험 (2026-09-25, 두 차례)

두 차례 모두 새 논문 18편(출판사당 3편)을 받았고, 한 번의 조작 묶음 안에서 여러 탭을 번갈아 진행했다. 시간은 시작부터 마지막 파일까지다.

| 방식 | 시간 | 확장 호출 (그 안의 동작 수) | 연결 끊김 | 시간 초과 |
|---|---|---|---|---|
| 한 탭 순서대로 (2차 시험) | 16.7분 | 63번 (281) | 0 | 0 |
| 6개 탭 (출판사마다 하나) | 17.1분 | 25번 (211) | 0 | 1 |
| 3개 탭 (탭마다 출판사 둘) | 14.4분 | 23번 (173) | 4 | 2 (1번은 마지막 파일 뒤) |

- 한 탭 2차 시험에는 지금은 받지 않는 동영상 SI 저장(약 70초)과 당시 30초 간격을 맞춘 기다림(약 11초)이 들어 있다. 지금 규칙이면 약 15.3분이다.
- 3개 탭 시험의 논문들을 한 탭으로 받았다면 1절 예상치로 12~16분이다. 3개 탭의 14.4분은 그 범위 안에 든다.

### 4.1 6개 탭

- 방법: 출판사마다 탭 하나씩 6개를 띄우고, 한 번의 조작 묶음 안에서 여섯 탭을 번갈아 진행했다.
- 결과: 18편 모두 받았지만 17.1분이 걸렸다. 한 탭에서 순서대로 받은 2차 시험은 16.7분이었다. 시간 이득이 없었다.
- Chrome 확장은 여러 요청을 동시에 처리하지 않고 하나씩 처리한다. 대신 페이지 열기는 바로 돌아오고, 뒤쪽 탭에서도 스크립트와 클릭이 된다. 그래서 번갈아 진행은 가능했지만, 뒤쪽 탭에서 문제가 많았다.
  - 좌표 클릭이 빗나갔다. 뒤쪽 탭은 늦게 뜨는 요소 때문에 배치가 밀리고, 탭마다 스크린샷 좌표계가 달랐다(1288 또는 1316 px).
  - Elsevier·RSC 의 상단 고정 막대가 뒤쪽 탭에서는 나타나지 않았다.
  - 요소 단위 클릭(`find` 의 ref)은 일반 다운로드 링크에서는 됐지만, 새 창을 여는 링크(RSC 본문 PDF, IOP PDF·SI 목록, ACS Open PDF 일부, Wiley Download PDF)와 접힌 메뉴 안의 링크(Science View Options)에서는 반응하지 않았다.
  - 대신 링크 주소로 탭을 옮기자 RSC SI 와 Science 본문에서 Cloudflare 확인 화면이 떴다. 제가 누르지 않았고 스스로 통과했지만, 순서대로 받을 때는 없던 일이다.
  - Science 온라인 보기의 다운로드를 누른 직후 그 탭을 다음 논문으로 옮기자 받기가 끊겼다.
  - 찾기 도구가 대상을 못 찾으면 묶음 전체가 그 자리에서 멈췄다.
  - 탭을 닫다가 확장의 탭 그룹이 사라져, 남은 탭 다섯 개는 사용자가 직접 닫아야 했다.
- 결론은 4.3 에 적었다.

### 4.2 3개 탭

- 방법: 탭 A 는 Elsevier 3편, RSC 3편, IOP 1편을 차례로, 탭 B 는 Wiley 3편, IOP 2편을, 탭 C 는 ACS 3편, Science 3편을 받았다. 파일은 33개(본문 18, SI 15)다.
- 결과: 18편 모두 받았다. 세 탭이 끝난 시각이 45초 안에 모여(09:13:14~09:13:59) 일이 고르게 나뉘었다. intake 는 33개를 5.5초에 정리했다.
- 시간 초과 한 번이 약 2.5분을 잡아먹었다. 12동작 묶음의 앞쪽 다운로드는 실행됐지만, 그 뒤 152초 동안 응답이 없었다. 이것이 없었다면 약 12분이다. 시간 초과가 난 두 묶음에는 모두 Science 온라인 보기(`/doi/epdf/`)를 연 탭의 스크린샷이 들어 있었다. 원인은 확실하지 않다.
- 확장 연결 끊김이 4번 있었고, 곧바로 다시 보내면 됐다. 6개 탭 시험과 한 탭 시험에서는 없어서, 탭 수 때문인지는 알 수 없다.
- 뒤쪽 탭에서 된 방법:
  - Elsevier: `find` 의 ref 클릭이 반응하지 않았다. SI 는 CDN 주소(`https://ars.els-cdn.com/content/image/1-s2.0-{PII}-mmc{n}.{확장자}`)로, 본문은 View PDF 링크(`a.accessbar-utility-component`)의 주소로 탭을 옮겨 받았다.
  - Wiley: SI 는 좌표로 누르고, 본문은 `/doi/pdf/` 로 옮긴 뒤 "열기"를 좌표로 눌렀다.
  - ACS: 본문 `/article-pdf/…/{코드}.pdf`, SI `/article-supplement/…/pdf/{코드}_si_001/` 주소로 탭을 옮겼다. 확인 창은 없었다. SI 를 누른 직후 같은 탭을 다른 주소로 옮기면 SI 받기가 끊긴다(1편, SI 주소로 다시 받음).
  - RSC: `doi.org` 로 연 뒤 SI `/article-supplement/…`, 본문 `/article-pdf/…` 주소로 탭을 옮겼다. 이번에는 확인 창이 없었다(6개 탭 시험에서는 SI 에서 한 번 떴다).
  - IOP: 본문은 `/pdf` 주소로 옮겼고, SI 는 `/data` 페이지에서 좌표로 눌렀다(서명 주소라 주소 이동은 안 된다).
  - Science: SI "DOWNLOAD", 빨간 PDF 아이콘, 온라인 보기의 다운로드 아이콘을 좌표로 눌렀다. 기사 페이지에 체크 상자 확인 화면이 한 번 떴고 스스로 통과했다(Claude 는 누르지 않음). 본문 PDF 주소로 바로 가면 확인 화면이 뜨므로 그렇게 하지 않는다.
  - 이번에는 세 탭의 스크린샷 좌표계가 같아(1288 px) 앞에서 읽은 좌표를 그대로 쓸 수 있었다.

### 4.3 판단

- 여러 탭의 이득은 페이지 열기와 파일 받기를 기다리는 시간을 겹치는 데서 나온다. 확장은 요청을 하나씩 처리하므로, 탭을 늘려도 호출 왕복과 Claude 가 판단하는 시간은 줄지 않는다. 6개 탭은 탭마다 상태를 확인하는 부담이 커서 이득이 없었다.
- 3개 탭은 이번에 한 탭보다 1~2분 빨랐지만 한 탭 예상 범위 안이었다. 시간 초과가 없으면 약 12분까지 줄 수 있다. 대신 연결 끊김과 시간 초과가 늘었고, 출판사마다 뒤쪽 탭용 방법을 따로 익혀야 한다.
- 확정(2026-09-26 사용자 결정): 한 탭에서 순서대로 받는다. 여러 탭·여러 창 방식은 쓰지 않는다.

### 4.4 탭을 앞으로 가져올 수 있는지 (2026-09-26)

- 사용자 제안: 여러 탭을 열되, 작업하는 탭을 그때그때 앞으로 가져오면 뒤쪽 탭 문제가 없지 않겠느냐. 원리는 맞지만 확장으로는 탭을 앞으로 가져올 수 없었다.
- 시험한 방법과 결과: 뒤쪽 탭의 페이지 안 누르기, Ctrl+2(확장이 보내는 키는 페이지 안으로만 들어가 Chrome 단축키가 안 됨), 페이지 쪽 `window.focus()`, 뒤쪽 탭 스크린샷, 앞 탭에서 `window.open`(팝업 차단). 모두 앞 탭이 바뀌지 않았다.
- 확장이 알려 주는 "선택된 탭"(`selectedTabId`)은 실제 앞 탭이 아니라 마지막에 조작한 탭이다. 앞 탭 여부는 페이지의 `document.visibilityState` 로 본다.
- 창을 여러 개 쓰는 방식: 확장은 세션마다 한 창의 탭 묶음 하나만 다루고, 창을 새로 만들거나 옮기거나 앞으로 가져올 수 없다(크기 바꾸기만 됨, 최소화된 창은 되살아나지만 최대화 창은 크기가 안 바뀜). 프로필이 다르면 확장이 따로 연결돼 `select_browser` 로 바꿔 가며 쓸 수는 있으나, 바꿀 때마다 호출이 들고 프로필마다 확장·출판사 로그인 준비가 필요해 이득이 없다.

## 5. 중단과 재개 (2026-09-26 시험)

- 시험: 6편 중 3편을 받은 뒤 탭을 닫아 탭 그룹을 없앴다. `intake` 가 받아 둔 파일 5개를 정리하고, `status` 와 `assist` 가 남은 3편만 냈다. 새 탭 그룹을 만들어 그 3편을 이어 받았다. 처음부터 끝까지 13.3분이었고, 사용자가 창을 앞으로 가져오는 대기가 두 번 들어 있다.
- 재개 절차: `intake` → `status` → `assist`. 순서대로 하면 `_collect/manual_download.csv` 에 남은 논문만 남는다(2026-09-26 부터 intake·status 가 끝난 논문을 목록에서 뺀다). 받다 만 논문은 받은 파일만 정리되고 본문 PDF 가 없으면 목록에 그대로 남는다.
- 새 탭 그룹의 창은 뒤에 열리므로 사용자에게 앞으로 가져와 달라고 한 뒤 시작한다. 창 크기도 다시 잡힌다.
- 주의: `list_connected_browsers` 에는 같은 Claude 계정으로 확장을 켠 다른 컴퓨터의 Chrome 도 나온다(2026-09-26 에 다른 컴퓨터의 Chrome 을 골라 탭을 열었다 닫은 사고). 브라우저를 고를 때는 `onThisComputer` 가 참인 것만 쓰고, 이 컴퓨터 것이 둘 이상이면 사용자에게 묻는다.
