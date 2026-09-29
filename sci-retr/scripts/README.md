# sci-retr scripts/

명령은 세 개다. 쓰는 법은 `../SKILL.md`(수집), `../../sci-index/SKILL.md`(색인), `../../sci-tldr/SKILL.md`(한국어 한 줄 요약, 원할 때만)에 있다.

| 파일 | 역할 |
|---|---|
| `sci_collect.py` | 수집 CLI. `resolve`, `collect`, `assist`, `intake`, `status`, `mark`, `reextract`, `refs`, `token`, `doctor` |
| `sci_index.py` | 색인 CLI. `build` (LLM 없음, 몇 초). 옛 `prep`·`apply` 는 sci_tldr.py 로 옮겼다 |
| `sci_tldr.py` | 한국어 한 줄 요약 CLI. `prep`(묶음·재료 글), `apply`(각 결과와 같은 번호의 재료 글에 숫자·화학식을 대조한 뒤 한줄요약 열에 병합). 재료가 없으면 보류한다. 요약은 전용 에이전트 sci-tldr-writer 가 쓴다 |
| `runner.py` | sci_collect 가 불러 쓰는 판정·정리 함수(본문 판정, HTML 본문 줄 정리, source.md 머리말, PDF 주소 후보). 직접 실행하지 않는다 |
| `validate.py` | 수집한 논문 검증(본문 길이, 절 제목, 첫 쪽 DOI, 덮어쓰기 방지 등). sci_collect 가 source.md 를 쓴 직후 부른다 |

- 환경 점검: `python sci_collect.py doctor --kb-root <논문 폴더>`. 읽기만 한다.
- 패키지는 설치 스크립트(`install.ps1`, `install.sh`)가 넣고 `doctor` 가 확인한다. `playwright` 는 예전 도구 창(`assist --window`)과, 웹 전용 출판사를 설정에서 뺐을 때의 창 없는 시도에만 쓰인다. 없어도 기본 흐름(resolve, collect, assist, intake, status)은 돈다.
- 인증서 확인은 끄지 않는다. sci_collect 는 `truststore` 로 OS 인증서 저장소(기관 망의 재서명 인증서 포함)를 쓰고, 도구가 띄우는 Chrome 도 인증서 오류를 무시하지 않는다.

## 옛 배치 스크립트 (2026-09-27 에 뺌)

2026-04~05 에 쓰던 다섯 단계 배치(`split_assignment.py` → `runner.py` 배치 실행 → `elsevier_html_retry_safe.py` → `failure_classifier.py` → `manual_ingest.py`)는 SKILL.md 가 쓰지 않아 패키지에서 뺐다. 인증서 확인을 끈 요청(`verify=False`)도 이 배치 실행부에 있었다. 지금은 sci_collect 의 `collect`(자동 경로), `assist`(웹 경로 목록), `intake`·`status`(직접 받은 PDF 반영)가 같은 일을 한다. 이전 판과 설명은 git 기록과 개발 PC 의 `scripts/_history/`(저장소·설치본에는 없음)에 있다.
