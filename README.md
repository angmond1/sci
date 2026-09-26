# SCI 논문 본문·SI 수집·색인 스킬 패키지
SCI 논문 본문과 SI PDF 파일을 자동으로 수집하고,<br>
LLM이 다루기 쉬운 markdown 파일로 변환 및 색인화

<br>

## 구성

| skill | 용도 | 기능 | 권장모델 |
|-------|------|------|:--------:|
| **sci-retr** | 수집 | 본문 SI PDF 다운로드, 본문 text를 md 파일로 변환 | Opus |
| **sci-index** | 색인 | 서지 정보(제목 저널 저자 연도 키워드 초록 등)를 csv 파일로 정리 | Sonnet |

<br>

## 설치

claude code (claude 데스크탑 앱에서 code), codex 대화창에

```
https://github.com/angmond1/sci-retr 설치해줘
```

<br>

## 준비물

1. **Chrome 브라우저 + 확장 프로그램 Claude in Chrome 설치**
   - Chrome 브라우저 설치 https://www.google.com/chrome/
   - 확장 프로그램 Claude in Chrome 설치 → https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn

   그러고 나서 Claude Desktop: 좌하단 이니셜 → 설정 → "Claude in Chrome" 켜기
2. **Chrome 설정**
   - `chrome://settings/content/pdfDocuments` 에서 "PDF 다운로드" 선택
   - `chrome://settings/downloads` 에서 "다운로드 전에 각 파일의 저장 위치 확인" 선택 해제

<br>

## 사용

대화창에 DOI 목록 파일(txt·csv·xlsx, WoS·Scopus 내보내기)이나 DOI 를 주고 말한다.

```
D:\papers\my_topic\dois.txt 논문들 받아줘
```

<br>

## 출판사별 수집 방법

| 출판사 | 조건 | 수집 방법 | 간격 |
|---|---|---|---|
| Wiley | TDM 토큰 있음<br>[TDM 토큰 발급 페이지](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining) | 파이썬 API | 5초 |
| Wiley | TDM 토큰 없음 | 웹 다운로드 | 30-60초 |
| Elsevier | API key 있음 + Open access 논문<br>[API key 발급 페이지](https://dev.elsevier.com/) | 파이썬 API | 3초 |
| Elsevier | 유료 논문 또는 API key 없음 | 웹 다운로드 | 30-60초 |
| Springer, Nature, MDPI, Frontiers, PLOS, Beilstein, Copernicus, APS, Cambridge | - | 파이썬 | 2-15초 |
| ACS, RSC, IOP, Science, Taylor & Francis, PNAS, AIP, Oxford, IEEE, ChemRxiv | - | 웹 다운로드 | 30-60초 |

미구독 출판사는 초록만 저장.<br>
Elsevier 기관 API key, Wiley 기관 TDM 토큰, ACS API key는 발급 거절당함.
