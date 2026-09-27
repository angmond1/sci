<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/sci-retriever-logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/sci-retriever-logo.jpg">
    <img src="assets/sci-retriever-logo.jpg" alt="SCI Retriever" width="900">
  </picture>
</p>

# SCI 논문 원문 수집 스킬 패키지
논문 본문·SI PDF 파일을 자동으로 수집하고,<br>
LLM이 다루기 쉬운 markdown 파일로 자동 변환 및 색인화

<br>

## 구성

| skill | 용도 | 기능 | 권장모델<br>Claude / Codex |
|-------|------|------|:--------:|
| **sci-retr** | 수집, 변환 | 본문·SI PDF 다운로드, 본문 text를 md 파일로 변환 | Opus / Sol |
| **sci-index** | 색인 | 서지 정보(제목 저널 저자 연도 키워드 초록 등)를 csv 파일로 정리 | Sonnet / Luna |
| **sci-tldr** | 한줄요약 (선택사항) | 한국어 한 줄 요약 생성, csv에 추가 | Sonnet / Luna |

Codex는 GPT-6 기준이다. [공식 모델 안내](https://learn.chatgpt.com/docs/models#recommended-models)와 작업 특성을 바탕으로 수집·브라우저 판단에는 Sol, 색인 명령 실행·짧은 요약에는 Luna를 권장한다. 색인 생성·검수 자체는 LLM을 쓰지 않는다. Codex에서의 성능은 아직 실측하지 않았다.

<br>

## 설치

claude code (claude 데스크탑 앱에서 code), codex 대화창에

```
https://github.com/angmond1/sci 설치해줘
```

<br>

## 준비물

1. **KIST 사내 인터넷 망 또는 kvpn 접속**
2. **claude 또는 chatgpt 유료 계정과 데스크탑 앱 (또는 CLI) 설치**
   * claude 설치 https://claude.com/download
   * codex (chatgpt) 설치 https://openai.com/ko-KR/codex/
3. **Chrome 브라우저 + 확장 프로그램 Claude in Chrome 설치**
   * Chrome 브라우저 설치 https://www.google.com/chrome/
   * 확장 프로그램 Claude in Chrome 설치 https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn

   그러고 나서 Claude Desktop: 좌하단 이니셜 클릭 → "설정" 클릭 → 좌측 탭에서 "Claude in Chrome 설정" 클릭 → "Claude in Chrome 사용설정" 켜기.
4. **Chrome 설정**
   * `chrome://settings/content/pdfDocuments` 에서 "PDF 다운로드" 선택
   * `chrome://settings/downloads` 에서 "다운로드 전에 각 파일의 저장 위치 확인" 선택 해제

<br>

## 사용법 예시

* 논문 PDF 파일이나 웹 링크를 claude code, codex 대화창에 주면서,<br>
  "이 논문의 reference 논문들 모두 수집해줘. sci-retr 스킬 사용해."

* Web of Science, Scopus에서 수집하고자 하는 논문 리스트를 파일로 저장하고,<br>
  ([Web of Science 검색](https://www.webofscience.com/wos/woscc/smart-search) · [Scopus 검색](https://www.scopus.com/pages/home#basic))<br>
  claude code, codex 대화창에 리스트 파일을 주면서,<br>
  "sci-retr 스킬로 논문 수집해줘"

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

KIST 미구독 출판사는 초록만 저장.<br>
Elsevier 기관 API key, Wiley 기관 TDM 토큰, ACS API key는 발급 거절당함 (26.04).

<br>

## 문의

이동기 / 청정에너지연구센터 e-chemical 연구팀<br>
dnklee@kist.re.kr
