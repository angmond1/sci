---
name: sci-index
description: 수집한 논문 폴더(papers/{paper_id}/)에서 검색용 색인 index.csv 를 만들고, 결정적 검수와 sonnet 검수·한국어 한 줄 요약을 붙이는 도구. "색인 만들어", "논문 목록 정리해", "이 폴더에 무슨 논문 있어", "관련 논문 찾아줘" 에 사용. 평소 세션에서 로컬 논문을 찾는 진입점.
---

# sci-index — 논문 색인 지침서

> 🐶 **리트리버 인사(정체성)**: 대화에서 아직 sci-retr·sci-index 인사를 하지 않았으면, 이 skill 을 시작할 때 첫 줄은 *"안녕하세요 🐶 sci-index 가 물어 온 논문을 정리할게요."* 한 줄, 그 다음부터는 평소 문체. sci-retr 에 이어 바로 색인할 때는 인사를 다시 하지 않는다. 작업 보고의 첫 줄은 sci-retr 과 같은 머리표를 쓴다: `🐶 완료 — sci-index`(색인과 요약_ko 를 다 채움) / `🐕 부분 완료 — sci-index`(일부만, 예: 요약_ko 30/42) / `🐕‍🦺 중단 — sci-index`(막혀서 멈춤). `sci_index.py` 의 build·apply 는 마지막 줄 끝에 `▼・ᴥ・▼` 를 찍는다. `index.csv`·`index_check.csv`·요약_ko·색인 폴더의 `README.md`·오류 문구에는 넣지 않는다.

## 1. 무엇을 하는가

- `sci-retr` 가 만든 `papers/{paper_id}/` 폴더와 `collection_registry.csv` 를 읽어 **한 편 = 한 행**인 `index.csv` 를 만든다. 논문이 무엇인지 빨리 파악하고 고르기 위한 단순 정보만 담는다.
- 색인 생성은 파이썬(`sci_index.py build`)만으로 끝난다. LLM 은 그 뒤의 검수와 한 줄 요약(요약_ko) 1패스에만 쓴다. 모델은 sonnet.
- 결과물은 CSV 하나다. 엑셀·DB·임베딩·MCP 서버는 만들지 않는다.

## 2. 원칙

1. CSV 만 만든다. UTF-8 BOM 이라 엑셀에서 한글이 바로 열린다. 초록은 한 줄로 정리한다.
2. 키워드는 논문 본문에 Keywords 줄이 있을 때만 넣는다. 외부에서 보강하지 않는다.
3. 요약_ko 는 200자 이내 한 문장이다. 이 논문이 무엇을 했고 무엇을 찾았는지만 쓴다.
4. 색인을 읽고 몇 편을 볼지는 질문에 맞춰 판단한다. 읽는 수나 검색 폭을 강제하는 규칙은 두지 않는다.
5. paper_id 는 sci-retr 가 부여한 값(`연도_저널약어_교신저자`)을 그대로 쓴다. 여기서 바꾸지 않는다.
6. 개인 연구 결과나 특정 논문의 수치는 지침에 넣지 않는다.

## 3. 명령

스크립트는 `sci-retr` skill 폴더의 `scripts/sci_index.py` 다(`sci_collect.py` 와 같은 폴더). 파이썬 인터프리터는 sci-retr skill 폴더의 `python.txt` 에 적힌 것을 쓴다(설치 스크립트가 기록, sci-retr 지침 5절 첫머리).

```bash
python <sci-retr>/scripts/sci_index.py build --kb-root <논문 폴더 root>
```

```bash
python <sci-retr>/scripts/sci_index.py prep --kb-root <논문 폴더 root> [--size 50]
```

```bash
python <sci-retr>/scripts/sci_index.py apply --kb-root <논문 폴더 root> --gists "<root>/_collect/index_gists_*.csv"
```

- `build`: `index.csv`, `index_check.csv`(결정적 검수), `README.md`(에이전트용 5줄 사용법)를 만든다. 이미 채워진 요약_ko 와 검수 flag 는 보존한다. 648편에 2.5초(2026-09-27 실측). 옛 수집기 폴더(PDF 이름이 다르거나 DOI 칸이 틀린 것, 폴더 바로 아래 PDF 만 있는 것)도 읽는다.
- `prep`: 요약 패스용 묶음 파일을 만든다(5.3).
- `apply`: 에이전트가 만든 검수 결과(`paper_id, 요약_ko, check_flags`)를 index.csv 와 index_check.csv 에 병합한다. 여러 파일·와일드카드를 받는다.

## 4. 열 정의

| 열 | 내용 | 출처 |
|---|---|---|
| paper_id | 폴더 이름 | registry |
| DOI | | registry |
| 제목 | 한 줄 | Crossref |
| 저자 | 6명 이하 전원, 7명 이상은 앞 3명 + … + 뒤 3명, `;` 구분 | Crossref |
| 교신저자 | 성. OpenAlex is_corresponding, 없으면 마지막 저자 | OpenAlex / Crossref |
| 연도, 저널, 저널약어, 권, 호, 페이지 | 페이지가 없는 전자 논문은 논문 번호(article-number) | Crossref |
| 초록 | 한 줄 | Crossref, 없으면 OpenAlex |
| 키워드 | 본문에 Keywords 줄이 있을 때만. 한 줄에 하나씩 이어지는 형식(Elsevier PDF)도 모아 `; ` 로 잇는다 | source.md |
| 원문상태 | 전문 / 초록만 / 전문(PDF 없음, 재시도 대상) / 미수집(사용자 확인 필요) / 범위밖-미수집 / 실패 / 미수집 | registry |
| 본문 단어수 | 전문일 때만 | source.md |
| SI 유무 | `Y(개수)` 또는 `N`. `pdf/{paper_id}_SI*` 파일(pdf·docx 등) 개수로 판정 | 폴더 |
| 수집일 | | source.json |
| 수집 URL | 실제로 받은 페이지 | source.json |
| 파일경로 | 본문 PDF 경로, 없으면 source.md | 폴더 |
| 요약_ko | 검수 패스에서 채움 | apply |

## 5. 절차

### 5.1 build

사용자가 색인을 원할 때 실행한다. sci-retr 는 수집 뒤 20편 이상이면 묻고, 20편 미만이면 이유와 함께 생략을 알린 뒤 요청을 기다린다(sci-retr 5.7). 출력의 세 줄을 읽는다.

- 상태별 편수 (전문 / 초록만 / PDF 없음 / 미수집 …)
- flag 가 있는 논문 목록 (index_check.csv)
- 요약_ko 채워진 수 (비어 있으면 5.3 으로)

### 5.2 결정적 flag 조치

| flag | 뜻 | 조치 |
|---|---|---|
| DOI 형식, DOI 중복 | 입력 목록 문제 | 중복은 한 편만 남기고 나머지는 폴더 삭제 대신 `sci_collect.py mark --status out_of_scope` 로 표시 |
| 제목·연도·저널 누락 | Crossref 메타 부족 | 요약 패스에서 본문 첫 부분으로 보완하고 flag 유지 |
| 연도 범위 | 연도가 비정상 | 확인 후 registry 수정은 하지 않고 flag 유지 |
| 전문인데 단어수 < 1500 | 본문이 잘렸을 가능성 | sci-retr 로 재수집 (`collect --ids <id> --force`) |
| PDF 없음 | 텍스트만 있고 PDF 미확보 | sci-retr 5.5 (사용자 확인 단계) 또는 5.6 (직접 저장) |
| 초록 길이, 초록 없음 | Crossref·OpenAlex 에 초록 없음 또는 비정상(RSC 는 Crossref 초록이 짧은 소개 문구뿐일 때가 있다) | 요약 패스에서 본문 첫 부분을 읽어 요약. 2026-09-26 부터 resolve 가 Crossref·OpenAlex 중 긴 초록을 쓴다 |
| 깨진 문자/합자 | PDF 텍스트의 합자·인코딩·제어 문자(NUL) | `sci_collect.py reextract --ids <id>` 로 다시 뽑는다(2026-09-26 부터 추출기가 제어 문자를 지운다). 그래도 남으면 flag 유지 |
| 파일 경로 없음 | 폴더 이동됨 | 폴더 확인 후 build 재실행 |

### 5.3 검수 + 요약 패스 (sonnet)

요약_ko 가 빈 행을 스크립트가 묶음 파일로 나눈다. 하위 에이전트는 묶음 파일 하나만 읽고 결과 CSV 하나를 쓴다. index.csv 나 source.md 를 따로 읽지 않는다(초록이 없거나 짧은 행은 본문 앞부분을 스크립트가 묶음 파일에 넣어 둔다).

```bash
python <sci-retr>/scripts/sci_index.py prep --kb-root <root> [--size 50]
```

- 출력: `_collect/index_batch_<n>.md`(묶음마다 결과 파일 경로가 적혀 있다). 이미 있는 결과 파일(`index_gists_<n>.csv`)의 다음 번호부터 붙여 덮어쓰지 않는다. 다시 돌리면 아직 빈 행만 묶는다.
- 묶음 하나를 sonnet 하위 에이전트 하나에 맡기고, 묶음이 여럿이면 동시에 돌린다.
- 실측(2026-09-27, 옛 KB 648편 중): 35편 묶음은 9.2분·16.2만 토큰(한 편 약 4.6천), 70편 묶음은 15.3분·19.9만 토큰(한 편 약 2.8천). 예전 방식(에이전트가 index.csv 와 source.md 를 직접 읽음)은 10편에 7분·14만 토큰(한 편 1.4만)이었다. 묶음이 클수록 한 편당 토큰이 준다. 기본 50편은 묶음 파일(약 40KB)이 한 번에 읽히는 크기다.
- 도구 호출이 늘수록 같은 내용이 다시 들어가 토큰이 는다. 프롬프트에 "읽기 한 번, 쓰기 한 번"을 적는다.
- 판단: 제목과 초록이 같은 논문인가, 초록이 잘렸거나 보일러플레이트(저작권 문구·목차·다른 논문)인가, 원문상태와 본문 길이가 맞는가.
- 출력: 묶음 파일에 적힌 `_collect/index_gists_<n>.csv`, 열은 `paper_id, 요약_ko, check_flags`. 문제가 없으면 check_flags 는 빈칸.
- 하위 에이전트 프롬프트 골격:

```
논문 색인 검수·요약 묶음 하나를 처리한다. 도구 호출은 읽기 한 번(묶음 파일 전체), 쓰기 한 번(Bash 로 파이썬 csv 모듈)만 한다. 다른 파일은 읽지 않는다.
입력: <묶음 파일 경로>. 출력: 묶음 파일 머리에 적힌 index_gists_<n>.csv.
각 논문(## paper_id 블록)에 대해
1) 요약_ko: 이 논문이 무엇을 했고 무엇을 찾았는지 한국어 한 문장(200자 이내, 마침표로 끝냄). 제목 번역이 아니다. 초록이 없으면 '본문 앞부분'을, 그것도 없으면 제목을 쓴다.
2) check_flags: 제목-초록 불일치, 초록 잘림, 초록 보일러플레이트, 초록 없음-본문으로 요약, 단어수 비정상(전문인데 1500 미만). 없으면 빈칸, 여러 개면 `;`.
CSV 는 encoding="utf-8-sig", newline="" 로 쓰고 묶음의 모든 논문을 쓴다. 끝나면 쓴 행 수만 한 줄로 보고한다.
```

### 5.4 apply

결과 파일을 한꺼번에 병합한다. 여러 파일·와일드카드를 받는다. UTF-8(BOM 있든 없든)과 cp949 를 모두 읽고, index.csv 에 없는 paper_id 는 건너뛰며 알린다. 아직 빈 행 수도 알려 준다.

```bash
python <sci-retr>/scripts/sci_index.py apply --kb-root <root> --gists "<root>/_collect/index_gists_*.csv"
```

index.csv 의 요약_ko 가 채워지고, check_flags 는 index_check.csv 에 `LLM:` 접두로 붙는다. build 를 다시 돌려도 요약_ko 와 `LLM:` flag 는 남는다.

### 5.5 보고

사용자에게는 다음만 말한다.

- 총 편수와 상태별 편수
- 요약_ko 채운 수
- 남은 flag 와 각 조치 (재수집 필요 / 사용자 확인 필요 / 그대로 둠)

## 6. 평소 세션에서 색인 쓰는 법

- 질문이 로컬 논문과 관련되면 `index.csv` 를 읽어 관련 행을 고른다. 본문은 `papers/{paper_id}/source.md`, PDF 는 `papers/{paper_id}/pdf/{paper_id}.pdf`, SI 는 같은 폴더의 `{paper_id}_SI*` 파일(pdf·docx 등)이다.
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
  _collect/index_batch_*.md  요약 패스 묶음 (prep 이 생성)
  _collect/index_gists_*.csv 검수 패스 출력
```

## 8. 예시 (예시)

```bash
python <sci-retr>/scripts/sci_index.py build --kb-root D:/papers/my_topic
```

출력 예시: `index.csv: 42행 — 전문 38, 초록만 3, 전문(PDF 없음, 재시도 대상) 1`, flag 5편, 요약_ko 0/42. `prep` 이 묶음 1개(42편)를 만들고, sonnet 하위 에이전트 1개가 `_collect/index_gists_1.csv` 를 쓰면 병합한다.

```bash
python <sci-retr>/scripts/sci_index.py prep --kb-root D:/papers/my_topic
python <sci-retr>/scripts/sci_index.py apply --kb-root D:/papers/my_topic --gists "D:/papers/my_topic/_collect/index_gists_*.csv"
```

## 9. 하지 않는 것

- 엑셀·DB·임베딩·MCP 서버 생성.
- 키워드나 주제 태그를 LLM 으로 만들어 열에 추가.
- 요약만 보고 본문 읽기를 생략하라는 규칙. 요약은 고르기용이다.
