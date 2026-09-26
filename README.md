# sci-retr (Sci Retriever) — 논문 원문 수집·색인 스킬 패키지

DOI 목록이나 WoS·Scopus 검색 결과를 주면 논문 본문 PDF, 본문 텍스트, SI 를 받아 폴더로 정리하고, 색인 CSV 를 만든다. 리트리버가 논문을 물어 온다는 뜻의 이름이다. Claude Code / Claude Desktop 에서 쓴다.

<br>

## 구성

| skill | 용도 | 기능 | 권장모델 |
|-------|------|------|:--------:|
| **sci-retr** | 논문 수집 | DOI 목록 → 출판사별로 파이썬 API·직접 다운로드 또는 평소 쓰는 Chrome 에서 받기 → 논문 폴더 정리 | Opus |
| **sci-index** | 논문 색인 | 수집 폴더 → `index.csv` (서지·초록·키워드·원문상태·SI 유무) + 한 줄 요약 | Sonnet |

sci-index 는 수집이 끝나면 sci-retr 지침이 이어서 부르므로 따로 기억하지 않아도 된다.

<br>

## 설치

claude code (claude 데스크탑 앱에서 code) 대화창에 아래 문구를 붙여넣는다.

```
https://github.com/angmond1/sci-retr 설치해줘
```

에이전트가 [CLAUDE.md](CLAUDE.md) 의 절차대로 설치한다. 직접 하려면:

```powershell
git clone https://github.com/angmond1/sci-retr.git C:\sci-retr
powershell -ExecutionPolicy Bypass -File C:\sci-retr\install.ps1
```

macOS / Linux 는 `bash ./install.sh`. 설치 뒤 Claude 를 재시작해야 새 skill 이 보인다.

<br>

## 준비물

1. **교내 망**(KIST IP). 밖에서는 유료 논문을 받지 못한다.
2. **Python 3.11 이상**. 패키지는 설치 스크립트가 넣는다.
3. **Google Chrome + "Claude in Chrome" 확장**: https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn . Claude 계정으로 로그인.
4. **Chrome 설정 두 가지**: `chrome://settings/content/pdfDocuments` 를 "PDF 다운로드" 로, `chrome://settings/downloads` 의 "다운로드 전에 각 파일의 저장 위치 확인" 은 끈다.
5. (선택) Elsevier API 키, Wiley TDM 토큰. 없어도 된다. 있으면 그 두 출판사도 자동으로 받는다. `sci-retr/examples/.env.example` 참고.

점검은 한 줄이다. 문제 0 이면 시작해도 된다.

```
python ~/.claude/skills/sci-retr/scripts/sci_collect.py doctor --kb-root <논문 폴더>
```

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
| Elsevier | API key 있음 + OA 논문 | 파이썬 API | 3초 |
| Elsevier | 유료 논문 또는 API key 없음 | 웹 다운로드 | 30~60초 |
| Wiley | TDM 토큰 있음 | 파이썬 API | 5초 |
| Wiley | TDM 토큰 없음 | 웹 다운로드 | 30~60초 |
| Springer, Nature, MDPI | - | 파이썬 | 2~15초 |
| Frontiers, PLOS, Beilstein, Copernicus, APS, Cambridge | - | 파이썬 | 5초 |
| ACS, RSC, IOP, Science | - | 웹 다운로드 | 30~60초 |
| Taylor & Francis, PNAS, AIP, Oxford, IEEE, ChemRxiv | - | 웹 다운로드 | 30~60초 |

웹 다운로드의 30~60초는 한 편을 받는 데 자연히 드는 시간이다. 표에 없는 출판사는 파이썬으로 먼저 시도하고, 막히면 그 사이트만 웹으로 넘어간다. 미구독 출판사는 초록만 저장한다. 상세는 [sci-retr/SKILL.md](sci-retr/SKILL.md) 6절과 [sci-retr/references/web_download_playbook.md](sci-retr/references/web_download_playbook.md).

<br>

## 규칙

- 봇 탐지 우회를 하지 않는다. 확인 창은 사용자가 직접 누르고, 쿠키 복사·User-Agent 위장 같은 기법은 쓰지 않는다. 같은 IP 대역을 쓰는 기관 전체가 차단될 수 있기 때문이다.
- 자동 요청을 막는 출판사에는 요청을 보내지 않고 바로 웹 다운로드로 간다. 한 사이트가 막히면 그 사이트의 나머지 논문도 웹으로 넘긴다.
- SI 는 문서(PDF, Word)만 받는다. 동영상, 결정 구조 파일, 압축 파일, 스프레드시트는 받지 않는다.
- 자격증명은 `.env` 파일로만 다루고 채팅에 적지 않는다.

<br>

## 문서

- [sci-retr/SKILL.md](sci-retr/SKILL.md) — 수집 지침서 (준비, 절차, 출판사별 방법, 문제 대응)
- [sci-retr/references/web_download_playbook.md](sci-retr/references/web_download_playbook.md) — 웹 다운로드 사이트별 요령
- [sci-retr/references/publisher_matrix.md](sci-retr/references/publisher_matrix.md) — 출판사별 실측 이력
- [sci-index/SKILL.md](sci-index/SKILL.md) — 색인 지침서
