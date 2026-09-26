# SCI 논문 본문·SI 수집·색인 스킬 패키지
SCI 논문 본문과 SI PDF 파일을 자동으로 수집하고,<br>
본문 text는 LLM이 읽기 편한 md 파일로 변환,<br>
서지정보(제목 저널 저자 연도 키워드 초록 등)를 LLM 검색이 쉬운 csv 파일로 저장.

<br>

## 구성

| skill | 용도 | 기능 | 권장모델 |
|-------|------|------|:--------:|
| **sci-retr** | 수집 | 본문 SI PDF 다운로드 → 본문 text는 markdown 파일로 저장 | Opus |
| **sci-index** | 색인 | 서지 정보(제목 저널 저자 연도 키워드 초록 등) 정리해서 csv 파일로 저장 | Sonnet |

<br>

## 설치

claude code (claude 데스크탑 앱에서 code) 대화창에 아래 문구를 붙여넣는다.

```
https://github.com/angmond1/sci-retr 설치해줘
```

<br>

## 준비물

1. **교내 망**(KIST IP). 밖에서는 유료 논문을 받지 못한다.
2. **Python 3.11 이상**. 패키지는 설치 스크립트가 넣는다.
3. **Google Chrome + "Claude in Chrome" 확장**: https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn . Claude 계정으로 로그인.
4. **Chrome 설정 두 가지**: `chrome://settings/content/pdfDocuments` 를 "PDF 다운로드" 로, `chrome://settings/downloads` 의 "다운로드 전에 각 파일의 저장 위치 확인" 은 끈다.
5. (선택) Elsevier API 키, Wiley TDM 토큰. 없어도 된다. 있으면 그 두 출판사도 자동으로 받는다. `sci-retr/examples/.env.example` 참고.

<br>

## 사용

대화창에 DOI 목록 파일(txt·csv·xlsx, WoS·Scopus 내보내기)이나 DOI 를 주고 말한다.

```
D:\papers\my_topic\dois.txt 논문들 받아줘
```

흐름은 다음과 같다. 자동으로 받히는 출판사는 파이썬이 받고, 자동 요청을 막는 출판사는 Claude 가 사용자 Chrome 에서 한 편씩 받는다. 확인 창(Cloudflare 등)이 뜨면 사용자가 누른다. 끝나면 색인이 만들어진다.

```
DOI 목록 → resolve(서지·출판사 판정) → collect(파이썬) → 웹 다운로드(Chrome) + intake(정리) → sci-index
```

결과는 `<논문 폴더>/papers/{paper_id}/` (본문 PDF, SI, `source.md`, `source.json`) 와 `index.csv` 다.

<br>

## 출판사별 수집 방법

| 출판사 | 조건 | 수집 방법 | 간격 |
|---|---|---|---|
| Wiley | TDM 토큰 있음<br>[TDM 토큰 발급 페이지](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining) | 파이썬 API | 5초 |
| Wiley | TDM 토큰 없음 | 웹 다운로드 | 30~60초 |
| Elsevier | API key 있음 + Open access 논문<br>[API key 발급 페이지](https://dev.elsevier.com/) | 파이썬 API | 3초 |
| Elsevier | 유료 논문 또는 API key 없음 | 웹 다운로드 | 30~60초 |
| Springer, Nature, MDPI, Frontiers, PLOS, Beilstein, Copernicus, APS, Cambridge | - | 파이썬 | 2~15초 |
| ACS, RSC, IOP, Science, Taylor & Francis, PNAS, AIP, Oxford, IEEE, ChemRxiv | - | 웹 다운로드 | 30~60초 |

미구독 출판사는 초록만 저장.<br>
Elsevier 기관 API key, Wiley 기관 TDM 토큰, ACS API key는 발급 거절당함.
