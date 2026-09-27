---
name: sci-index
description: 수집한 논문 폴더(papers/{paper_id}/)에서 서지정보(제목·저자·연도·저널·키워드·초록 등) 색인 index.csv 를 만들고 결정적 검수를 붙이는 도구. 스크립트만으로 몇 초에 끝나 편수와 관계없이 수집 뒤 항상 만든다(LLM 없음). 한국어 한 줄 요약은 사용자가 원할 때만 sci-tldr. "색인 만들어", "논문 목록 정리해", "이 폴더에 무슨 논문 있어", "관련 논문 찾아줘" 에 사용. 평소 세션에서 로컬 논문을 찾는 진입점.
---

# sci-index — 논문 색인 지침서

> 🐶 **리트리버 인사(정체성)**: 대화에서 아직 sci-retr·sci-index 인사를 하지 않았으면, 이 skill 을 시작할 때 첫 줄은 *"안녕하세요 🐶 sci-index 가 물어 온 논문을 정리할게요."* 한 줄, 그 다음부터는 평소 문체. sci-retr 에 이어 바로 색인할 때는 인사를 다시 하지 않는다. 작업 보고의 첫 줄은 sci-retr 과 같은 머리표를 쓴다: `🐶 완료 — sci-index`(색인을 만듦) / `🐕 부분 완료 — sci-index`(일부 폴더를 못 읽음 등) / `🐕‍🦺 중단 — sci-index`(막혀서 멈춤). `sci_index.py build` 는 마지막 줄 끝에 `▼・ᴥ・▼` 를 찍는다. `index.csv`·`index_check.csv`·색인 폴더의 `README.md`·오류 문구에는 넣지 않는다.

## 1. 무엇을 하는가

- `sci-retr` 가 만든 `papers/{paper_id}/` 폴더와 `collection_registry.csv` 를 읽어 **한 편 = 한 행**인 `index.csv` 를 만든다. 논문이 무엇인지 빨리 파악하고 고르기 위한 단순 정보만 담는다.
- 색인 생성과 검수는 파이썬(`sci_index.py build`)만으로 끝난다. LLM 을 쓰지 않고 96편에 1~3초, 648편에 3초다(2026-09-27 실측). 그래서 **편수와 관계없이 수집이 끝나면 항상 만든다**(2026-09-27 사용자 결정).
- 한국어 한 줄 요약(한줄요약 열)은 이 skill 이 하지 않는다. 사용자가 원할 때만 `sci-tldr` 이 같은 index.csv 에 열을 하나 더 붙인다. build 는 그 열이 있으면 그대로 둔다.
- 결과물은 CSV 하나다. 엑셀·DB·임베딩·MCP 서버는 만들지 않는다.

## 2. 원칙

1. CSV 만 만든다. UTF-8 BOM 이라 엑셀에서 한글이 바로 열린다. 초록은 한 줄로 정리한다.
2. 키워드는 논문 본문에 Keywords 줄이 있을 때만 넣는다. 외부에서 보강하지 않는다.
3. LLM 이 논문을 파악할 때는 초록과 본문(`source.md`)을 읽는다. 색인은 고르기용이다.
4. 색인을 읽고 몇 편을 볼지는 질문에 맞춰 판단한다. 읽는 수나 검색 폭을 강제하는 규칙은 두지 않는다.
5. paper_id 는 sci-retr 가 부여한 값(`연도_저널약어_교신저자`)을 그대로 쓴다. 여기서 바꾸지 않는다.
6. 개인 연구 결과나 특정 논문의 수치는 지침에 넣지 않는다.

## 3. 명령

스크립트는 `sci-retr` skill 폴더의 `scripts/sci_index.py` 다(`sci_collect.py` 와 같은 폴더). 파이썬 인터프리터는 sci-retr skill 폴더의 `python.txt` 에 적힌 것을 쓴다(설치 스크립트가 기록, sci-retr 지침 5절 첫머리).

```bash
python <sci-retr>/scripts/sci_index.py build --kb-root <논문 폴더 root>
```

- `build`: `index.csv`, `index_check.csv`(결정적 검수), `README.md`(에이전트용 5줄 사용법)를 만든다. sci-tldr 이 붙인 한줄요약 열과 `LLM:` flag 는 보존한다(옛 열 이름 요약_ko 는 한줄요약으로 옮긴다). 옛 수집기 폴더(PDF 이름이 다르거나 DOI 칸이 틀린 것, 폴더 바로 아래 PDF 만 있는 것)도 읽는다.
- 옛 명령 `prep`·`apply`(한 줄 요약)는 sci-tldr 로 옮겼다. 부르면 새 명령을 알려 주고 끝난다.

## 4. 열 정의

| 열 | 내용 | 출처 |
|---|---|---|
| 참고문헌 번호 | 참고문헌 수집(sci-retr 5.10)일 때만 맨 왼쪽 열. 원 논문의 참고문헌 목록 번호(`-` = 번호 모름). paper_id·파일 이름도 이 번호로 시작한다 | registry `ref_no` |
| paper_id | 폴더 이름 | registry |
| DOI | | registry |
| 웹페이지 | 논문 페이지 주소 `https://doi.org/<DOI>` (DOI 가 없으면 레지스트리의 논문 주소). 엑셀에서 복사해 바로 연다(2026-09-27 사용자 지시) | DOI |
| 제목 | 한 줄 | Crossref |
| 저자 | 6명 이하 전원, 7명 이상은 앞 3명 + … + 뒤 3명, `;` 구분 | Crossref |
| 교신저자 | 성. OpenAlex is_corresponding, 없으면 마지막 저자 | OpenAlex / Crossref |
| 연도, 저널, 저널약어, 권, 호, 페이지 | 페이지가 없는 전자 논문은 논문 번호(article-number) | Crossref |
| 초록 | 한 줄 | Crossref, 없으면 OpenAlex |
| 키워드 | 본문에 Keywords 줄이 있을 때만. 한 줄에 하나씩 이어지는 형식(Elsevier PDF)도 모아 `; ` 로 잇는다 | source.md |
| 원문상태 | 전문 / 전문(웹 본문, PDF 없음) / 전문(웹 본문, PDF 받기 실패) / 초록만 / 전문(PDF 없음, 재시도 대상) / 미수집(사용자 확인 필요) / 범위밖-미수집 / 실패 / 미수집. '전문(웹 본문, PDF 없음)' 은 PDF 가 없는 웹 전용 글(Science Expert Voices 등)의 본문·참고문헌이 source.md 에만 있는 것, '전문(웹 본문, PDF 받기 실패)' 는 PDF 를 여러 번 못 받아 웹 본문을 저장한 것(웹페이지 열로 사용자가 확인) | registry |
| 본문 단어수 | 전문·전문(웹 본문)일 때만 | source.md |
| SI 유무 | `Y(개수)` 또는 `N`. `pdf/{paper_id}_SI*` 파일(pdf·docx 등) 개수로 판정 | 폴더 |
| 수집일 | | source.json |
| 수집 URL | 실제로 받은 페이지 | source.json |
| 파일경로 | 본문 PDF 경로, 없으면 source.md | 폴더 |
| 한줄요약 | 사용자가 원할 때만 sci-tldr 이 붙이는 열(없으면 열 자체가 없다) | sci-tldr |

## 5. 절차

### 5.1 build

수집이 끝나면 편수와 관계없이 바로 실행한다(sci-retr 5.7). 묻지 않는다. 새로 받은 논문이 생길 때마다 다시 돌리면 된다(몇 초). 출력의 세 줄을 읽는다.

- 상태별 편수 (전문 / 초록만 / PDF 없음 / 미수집 …)
- flag 가 있는 논문 목록 (index_check.csv)
- 한줄요약 상태 (없음이면 sci-retr 5.7 대로 사용자에게 한 번 묻는다)

### 5.2 결정적 flag 조치

| flag | 뜻 | 조치 |
|---|---|---|
| DOI 형식, DOI 중복 | 입력 목록 문제 | 중복은 한 편만 남기고 나머지는 폴더 삭제 대신 `sci_collect.py mark --status out_of_scope` 로 표시 |
| 제목·연도·저널 누락 | Crossref 메타 부족 | 본문 첫 부분(source.md)으로 확인하고 flag 유지. 프리프린트(ChemRxiv·arXiv·bioRxiv 등)는 build 가 서버 이름을 저널명으로 채운다(2026-09-27) |
| 연도 범위 | 연도가 비정상 | 확인 후 registry 수정은 하지 않고 flag 유지 |
| 전문인데 단어수 < 1500 (PDF N쪽) | 본문이 잘렸을 가능성. 2~4쪽 PDF 에 쪽당 200 단어 이상이면 짧은 기사(뉴스·하이라이트·학회 초록)라 알리지 않는다(2026-09-27 연습 4편) | 한 쪽짜리면 첫 쪽만 온 것이니 sci-retr 로 재수집 (`collect --ids <id> --force`, 웹 경로 논문은 웹에서 다시). 쪽은 많은데 단어가 적으면 `reextract` |
| PDF 없음 | 텍스트만 있고 PDF 미확보 | sci-retr 5.5 (사용자 확인 단계) 또는 5.6 (직접 저장) |
| 초록 길이, 초록 없음 | Crossref·OpenAlex 에 초록 없음 또는 비정상(RSC 는 Crossref 초록이 짧은 소개 문구뿐일 때가 있다. Springer·Elsevier 는 OpenAlex 에 초록이 없다) | 그대로 둔다(본문은 source.md 에 있다). build 가 본문의 초록 절에서 채울 수 있으면 채운다(아래 줄). 2026-09-26 부터 resolve 가 Crossref·OpenAlex 중 긴 초록을 쓴다 |
| 초록 본문에서 채움 | 초록 칸이 비어 build 가 본문의 초록 절(Abstract, A B S T R A C T, Abstract—)을 넣었다. 두 단 섞임·참고문헌 끼임·붙은 단어는 버리고 빈칸으로 둔다(2026-09-27 연습 12편 중 6편, 옛 KB 69편 중 8편 채움) | 조치 없음. 궁금하면 제목과 맞는지 한 번 본다 |
| 깨진 문자/합자 | PDF 텍스트의 합자·인코딩·제어 문자(NUL), 웹페이지를 잘못된 인코딩으로 읽은 글자(Ã©, Â°) | `sci_collect.py reextract --ids <id>` 로 다시 뽑는다(2026-09-26 부터 추출기가 제어 문자를 지우고, 2026-09-27 부터 웹페이지 인코딩을 바로 읽고 저장된 옛 페이지의 깨진 글자와 합자도 되돌린다: Copernicus·Beilstein 4편 시험). 그래도 남으면 flag 유지 |
| 파일 경로 없음 | 폴더 이동됨 | 폴더 확인 후 build 재실행 |

### 5.3 한 줄 요약 (선택, sci-tldr)

한국어 한 줄 요약은 이 skill 이 만들지 않는다. 사용자가 원하면 `sci-tldr` 지침을 따른다. 사용자가 엑셀에서 한국어로 훑어볼 목록을 원할 때 쓰고, LLM 이 논문을 파악하는 데는 초록과 본문이 낫다(2026-09-27 사용자 결정: 편수와 관계없이 사용자에게 물어서 원할 때만).

### 5.5 보고

사용자에게는 다음만 말한다.

- 총 편수와 상태별 편수
- 남은 flag 와 각 조치 (재수집 필요 / 사용자 확인 필요 / 그대로 둠)
- 걸린 시간 (몇 초)

## 6. 평소 세션에서 색인 쓰는 법

- 질문이 로컬 논문과 관련되면 `index.csv` 에서 관련 행을 고른다. 논문이 많아 한 번에 읽기 어려우면 제목·초록·키워드를 Grep 한다. 본문은 `papers/{paper_id}/source.md`, PDF 는 `papers/{paper_id}/pdf/{paper_id}.pdf`, SI 는 같은 폴더의 `{paper_id}_SI*` 파일(pdf·docx 등)이다.
- 키워드로 훑을 때는 `papers/*/source.md` 를 Grep 한다.
- 몇 편을 읽을지는 질문에 맞춰 판단한다. 웹 검색이나 자체 지식과 자연스럽게 섞는다.
- 색인에 없는 논문이 필요하면 DOI 를 정리해 `sci-retr` 수집을 제안한다. 수집은 사용자가 동의한 뒤에 한다.
- Claude Desktop 일반 채팅에서 쓰려면 공식 filesystem MCP 로 논문 폴더를 노출하면 된다. 별도 코드는 없다.

## 7. 파일 위치

```
<root>/
  index.csv                  색인 (정본)
  index_check.csv            검수 flag
  README.md                  에이전트용 5줄 사용법 (build 가 생성)
  collection_registry.csv    sci-retr 레지스트리
  papers/{paper_id}/         source.md, source.json, pdf/, html/, xml/
  _collect/tldr_*            한 줄 요약 묶음·결과 (sci-tldr, 사용자가 원할 때만)
```

## 8. 예시 (예시)

```bash
python <sci-retr>/scripts/sci_index.py build --kb-root D:/papers/my_topic
```

출력 예시: `index.csv: 42행 — 전문 38, 초록만 3, 전문(PDF 없음, 재시도 대상) 1`, flag 5편, `한줄요약: 없음 — 사용자가 원할 때만 sci-tldr`. 1초 안팎에 끝난다.

## 9. 하지 않는 것

- 엑셀·DB·임베딩·MCP 서버 생성.
- 키워드나 주제 태그를 LLM 으로 만들어 열에 추가.
- 한 줄 요약을 편수에 따라 자동으로 만드는 것(sci-tldr 은 사용자가 원할 때만).
- 색인만 보고 본문 읽기를 생략하라는 규칙. 색인은 고르기용이다.
