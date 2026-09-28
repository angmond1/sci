# Publisher Matrix — DOI prefix별 본문 수집 method 상세

이 문서는 sci-retr skill이 사용하는 publisher 분류 (A/B/C/D) 의 상세 명세다. 각 publisher의 URL 패턴 + method tag + 환경 의존성 + 검증 결과를 정리한다.

검증 데이터: 2026-04-29~30 의 590편 batch 결과 기준. KIST IP에서 작동 검증됨.

---

## ⛔ 공통 정책 — 봇 탐지 우회 금지 (2026-09-24)

도구는 공식 API 와 일반 요청·일반 브라우저 세션에서 정상적으로 내려오는 파일만 받고, 확인 페이지가 나오면 재시도 없이 웹 경로로 넘긴다. 폐기한 기법: 확인 통과 쿠키를 headless 프로필·스크립트로 복사, User-Agent·자동화 플래그 위장, TLS 지문 흉내(`curl_cffi`), PDF 확인 응답 가로채기, 타 기관 IP 헤더. 이유: 출판사 약관 위반 + KIST 기관 IP 대역 전체 차단 위험. 아래 개별 절에 남아 있는 옛 기록은 실측 이력이며, 이 정책과 충돌하면 정책이 우선한다.

---

## ★ 사용자 평소 Chrome 에서 받기 — 2026-09-24 연습 결과 (Elsevier·RSC·ACS·Wiley·Science·ECS/IOP 각 1편)

**현재 규칙 (2026-09-28 갱신, 사용자 지시)**: (1) Elsevier API 는 OA 논문에만 쓴다. OA 가 아닌 구독 논문에는 API 를 호출하지 않는다. OA 논문은 키로 바로 빠르게 받는다는 점과 발급 주소 https://dev.elsevier.com/ 를 사용자에게 알린다. API 속도: 공식 한도 키당 초당 10회·주 50,000회(https://dev.elsevier.com/api_key_settings.html, 초과 시 429), 도구는 논문당 2회 요청 + 논문 사이 3초. (2) ACS·RSC·Science·ECS/IOP 는 자동 요청을 보내지 않는다(설정 `web_only_publishers`). (3) 웹 경로는 같은 출판사 안에서 한 편씩 받는다. ScienceDirect는 본문·SI 다운로드 완료 뒤 30초를 추가로 기다리고 다음 논문을 연다. 다른 사이트에는 별도 대기가 없다. (4) SI 는 문서(PDF, Word)만 받는다. 동영상, 결정 구조 파일(CIF 등), 압축 파일(zip 등), 스프레드시트(Excel, CSV 등)는 받지 않는다(설정 `si_skip_exts`).

**출판사 텍스트 마이닝 신청 창구 (2026-09-25 조사, SKILL.md 요약표 메모의 상세)**:
- Elsevier: 기관 API 키(Elsevier 공식 명칭은 institutional token, insttoken — API 키와 함께 보내는 추가 토큰이며 API 키에 묶임) 발급 요청 거절됨(2026-09). 신청 메일 datasupportRD@elsevier.com (University of Calgary 도서관 안내: API 키를 적고 소속 기관 메일로 보낼 것). Elsevier 개발자 사이트 공식 경로는 지원 센터 문의 양식 https://service.elsevier.com/app/contact/supporthub/researchproductsapis/ . 개인 API 키는 https://dev.elsevier.com/ 에서 셀프 발급, OA 논문만 본문 제공.
- Wiley: 기관 TDM 토큰 발급 요청 거절됨. 개인 TDM 토큰은 https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining 에서 셀프 발급. 기본 서비스로 안 되는 요청(미구독 자료, 다른 형식 등)은 TDM@wiley.com 로 협의 (Wiley 사서용 TDM 페이지 문구).
- ACS: API 키 발급 요청 거절됨. ACS 는 API 키 대신 프로젝트별로 콘텐츠를 전달하고 비용이 있음. 공식 경로는 문의 양식 https://solutions.acs.org/contact-us/inquire-about-subscriptions/ , 메일 acs_pubs_assist@acs.org (Cambridge 대학 도서관 안내, ACS Publications 고객지원 주소).
- RSC: 셀프 발급 토큰·API 없음. 텍스트 마이닝은 개별 요청으로 협의, RSC 텍스트 마이닝 페이지의 문의 양식으로 2주 전에 연락 (https://www.rsc.org/journals-books-databases/research-tools/text-and-data-mining/). 기관 대상 라이선스도 있음.
- IOP (ECS 저널 호스팅): 셀프 발급 토큰·API 없음, API 접근은 별도 서면 계약·비용. contentsupport@ioppublishing.org 로 이름·소속·DOI 또는 기간·형식(XML/PDF)·사용 기간·목적을 보내면 SFTP 로 일괄 제공 가능, 소액 비용 가능 (https://ioppublishing.org/legal/textanddataminingpolicy/, 2026-07 판). ECS 저널 포함 여부는 정책에 명시 없음 → 문의 필요.
- Science (AAAS): 토큰·API 없음. 기관 구독자는 정해진 논문 목록을 웹에서 받아 내부 비상업 연구에 사용 가능, 자동화 도구 다운로드 금지·적정 속도 조항 있음 (Institutional License Agreement 4.3.7, Annex A). 문의 scienceonline@aaas.org, 상업 용도는 AAAS 라이선스 부서. 사용자 결정(2026-09-25): 지금처럼 웹 경로로 받는다.

Claude in Chrome 확장으로 사용자가 평소 쓰는 Chrome 을 조작해 PDF·SI 를 받았다. 도구가 띄운 Chrome 과 앱 내장 브라우저는 Elsevier·Wiley 확인 창이 반복됐지만, 사용자 Chrome 에서는 Elsevier·RSC·Wiley 는 확인 창 없이 열렸고 ACS 만 확인 창 1회(사용자 클릭)였다. 네 편 모두 PDF + SI 확보, 첫 쪽 DOI 로 검증, `status` 로 반영.

공통 준비와 규칙:
- Chrome 설정 `chrome://settings/content/pdfDocuments` 를 "PDF 다운로드" 로 둔다. PDF 가 저장 창 없이 다운로드 폴더(기본 `C:/Users/<사용자>/Downloads`)로 바로 저장된다. Chrome PDF 보기 화면의 다운로드 버튼은 "저장 위치 확인" 설정과 관계없이 항상 저장 창을 띄우므로 쓰지 않는다.
- 받기 전에 파일 목록(출처, 파일명, 알면 크기)을 사용자에게 알리고 확인을 받는다.
- 링크는 화면에 띄워 스크린샷으로 위치를 확인한 뒤 좌표로 누른다. 페이지 배치가 바뀌어 참조로 누른 클릭이 추천 논문 링크에 떨어진 적이 있다(Elsevier).
- 받은 PDF 는 기대 DOI 가 PDF 안에 있는지(공백 제거 후 전체 텍스트) 또는 첫 쪽에 제목이 있는지 확인하고, **확인이 통과했을 때만** `papers/{id}/pdf/{id}.pdf`, SI 는 `{id}_SI.pdf` 로 옮긴 뒤 `status` 를 실행한다. Science·IOP PDF 는 첫 쪽에 DOI 글자가 없다.
- 다운로드 폴더에 같은 이름이 이미 있으면 Chrome 이 `이름 (1).pdf`, `(2)` … 를 붙인다. 방금 받은 파일은 수정 시각이 가장 최근인 것으로 고른다.
- 쿠키 동의 창은 누르지 않는다(동의는 사용자 결정). IOP 에서는 페이지를 누른 뒤 동의 창이 접히며 왼쪽 아래 쿠키 아이콘만 남은 적이 있다.
- 작업이 끝나면 연 탭을 닫는다.

| 출판사 | 페이지 | 본문 PDF | SI | 다운로드 폴더 파일명 |
|---|---|---|---|---|
| Elsevier | 확인 창 없음. KIST 기관 접속 표시 | 상단 "View PDF" (`a.accessbar-utility-component`). 확인 단계 탭(`pdfft?crasolve`)이 잠깐 열린 뒤 파일 저장, 그 탭은 닫는다. 누른 뒤 추천 논문 안내 창이 떠서 다음 클릭을 막음 → 닫기(X). 창 안 "Download (6) PDFs" 는 다른 논문 6편이라 누르지 않는다 | 부록(Appendix A. Supplementary material)의 "Download Acrobat PDF file (…MB)" 또는 "Download Word document (…MB)" = `ars.els-cdn.com/…-mmc1.pdf`·`.docx`. SI 를 먼저 받고 본문은 상단 고정 막대의 "View PDF" 로 받는다. 바로 오른쪽 "Download full issue"(호 전체)는 누르지 않는다 | `1-s2.0-{PII}-main.pdf`, `1-s2.0-{PII}-mmc1.pdf`·`.docx` |
| RSC | 조용한 SSO 확인(`sso.rsc.org`) 후 자동으로 열림, 확인 창 없음 | 툴바 "PDF" (`/{저널}/article-pdf/…/{코드}.pdf`, citation_pdf_url 과 같음) | "Supplementary information (PDF)" = `/{저널}/article-supplement/{id}/pdf/{코드}1_suppl/` | `{코드}.pdf`, `{코드}1_suppl.pdf` |
| ACS | Cloudflare "Verify you are human" 이 뜨면 사용자 클릭 (2026-09-25 시험 3편은 뜨지 않음). 2026 Silverchair 새 플랫폼(주소 `/{저널코드}/article/{권}/{호}/{쪽}/{id}/…`) | "Open PDF" (`a.article-pdf-button`, `/{저널코드}/article-pdf/…/{코드}.pdf`) | Supporting Information 절의 "sifile1" 링크 (`/article-supplement/{id}/pdf/{코드}_si_001/`). 미리보기 창의 Download 버튼 말고 이 링크 | `{코드}.pdf`, `{코드}_si_001.pdf` |
| Science | 확인 창 없음. FULL ACCESS 표시. 아래쪽 ScienceAdviser 뉴스레터 안내는 닫기(X) | 제목 아래 오른쪽 빨간 PDF 아이콘(내리면 상단 고정 막대에 있음) → 온라인 보기(`/doi/epdf/`)가 열림 → 오른쪽 위 둥근 다운로드 아이콘("Download PDF • 크기")을 누르면 저장 (2026-09-25 시험 3편). 또는 검은 도구 막대의 눈 아이콘 "View Options" → "DOWNLOAD PDF" (`/doi/pdf/{doi}?download=true`) | Supplementary Material 절 Resources 의 "DOWNLOAD" (`/doi/suppl/{doi}/suppl_file/{코드}-sm.pdf`, 크기 표시) | `science.{코드}.pdf`, SI 는 `science.{코드}_sm.pdf` (전에 본 형식 `{코드}-{저자}-sm.pdf`) |
| ECS/IOP | 확인 창 없음 (2026-09-24, 09-25). 쿠키 동의 창 뜸 | "PDF" 버튼 (`/article/{doi}/pdf`, 새 탭 → 바로 저장) | 본문 위 "Supplementary data" 버튼 → SI 목록 페이지(`/article/{doi}/data`) → 파일 링크("Supplemental Material" 등). README 는 받지 않는다. SI 없는 논문도 있다 | `{제1저자}_{연도}_{저널약어}_{권}_{논문번호}.pdf`, SI 는 `jes{코드}supp1.docx` 또는 옛 논문은 `1960.docx` 처럼 숫자뿐 (intake 가 Word 앞부분의 제목으로 가림) |
| Wiley | 확인 창 없음. Advanced 계열은 `advanced.onlinelibrary.wiley.com`, Chemistry Europe 계열은 `chemistry-europe.onlinelibrary.wiley.com`. 페이지가 늦게 뜰 때가 있다 (2026-09-25 시험: 8~11초, 한 번은 1분 넘게 빈 화면) | 상단 "PDF" 는 온라인 보기(`/doi/epdf/`)라 쓰지 않는다. 본문 끝 "Download PDF" (`/doi/pdf/`) → PDF 가 든 페이지에 Chrome "열기" 버튼 → 누르면 빈 탭이 잠깐 열렸다 닫히며 저장 | 접힌 "Supporting Information" 항목을 펼친 뒤 `…-sup-0001-SuppMat.pdf`·`.docx` (크기 표시됨) | `{저널} - {연도} - {제1저자} - {제목 앞부분}.pdf`, `{코드}-sup-0001-suppmat.pdf` |

출판사별 요령·교훈·예상 시간은 `web_download_playbook.md` 에 모았다 (2026-09-25). 웹 경로를 시작하기 전에 그 문서를 읽는다.

웹 다운로드 시간 실측 (2026-09-25, 여섯 출판사 3편씩 18편, 페이지 열기부터 SI·본문 저장까지): Elsevier 66·32초 (첫 편 201초는 도구 재시작 대기 약 2분 반 포함), Wiley 212·262·82초 (첫 편은 "열기" 단계 확인, 둘째 편은 페이지가 1분 넘게 안 뜸), ACS 79·50·38초, RSC 49·38·44초, ECS/IOP 97·26·81초 (SI 목록 페이지를 한 번 더 거침, SI 없는 편 26초), Science 93·49·54초 (첫 편은 온라인 보기의 다운로드 아이콘 찾기 포함). 18편 중앙값 60초, 합계 약 26분. 막힘 없이 진행하면 대개 30~60초, Wiley 는 80초 안팎. intake 는 34개 파일(211 MB) 정리와 본문 텍스트 반영에 약 5초. 같은 날 요령 문서대로 새 논문 18편을 받은 2차 시험은 16.7분, 한 편 중앙값 42.5초 (상세는 `web_download_playbook.md`).

도구 규칙과의 대조 (2026-09-24 반영): 본문 영역 Elsevier `#body` (옛 `#aep-article-fulltext` 없음), RSC·ACS `.article-body` (옛 후보 없음, 전에는 왼쪽 목차·참고문헌이 섞인 `[role=main]` 을 잡았음), Science `#bodymatter` (전에는 머리말·참고문헌이 섞인 `article`), ECS/IOP `.article-content` (전에는 전용 후보가 없어 `main`), Wiley `.article__body` 그대로. IOP 페이지에 출판사 텍스트 마이닝 정책 링크가 있다 (https://ioppublishing.org/legal/textanddataminingpolicy/). ACS PDF 는 옛 `/doi/pdf/{doi}` 대신 페이지의 citation_pdf_url. SI 링크 형식은 네 곳 모두 현 규칙에 걸림.

PDF 텍스트 추출 버그 (2026-09-24 발견·수정): `get_text("text", sort=True)` 가 두 단 편집에서 왼쪽·오른쪽 단 줄을 한 줄로 섞었다 (연습 4편에서 섞인 줄 152~375, 공백 비율 30~88%). PDF 기본 순서로 바꾼 뒤 섞인 줄 0, 공백 14~18%. 기존 수집분은 `sci_collect.py reextract` 로 저장된 원본에서 다시 뽑는다.

---

## A. 완전 자동 (key/IP 무관, 어디서나 작동)

### A.1 RSC (Royal Society of Chemistry) — `10.1039`

**2026-09-24 현재 (봇 탐지 우회 설정 제거 후)**: 창 없는 요청과 headless Chrome 은 확인 페이지로 막힌다. 도구가 띄운 보이는 Chrome 에서는 사용자가 확인을 한 번 누르면 논문 페이지가 열리고 전문 HTML 을 받는다(52,779자, 1편). 그러나 같은 세션의 PDF 요청(`citation_pdf_url`)은 request·페이지 안 fetch 모두 403 → PDF 는 직접 다운로드 목록으로 넘기고 사용자가 평소 쓰는 Chrome 에서 받아 저장한다. 새 플랫폼(2026-06-30 Silverchair 이전)의 SI 링크는 `/{저널}/article-supplement/{기사 id}/{형식}/{파일명}_suppl/` 형식이라 옛 SI 규칙에 걸리지 않았다 → 2026-09-24 규칙에 추가(확장자는 {형식} 칸). 저장된 RSC 페이지 5개에서 모두 SI 링크를 찾음, 다른 출판사 25개는 결과 변화 없음. 아래 절들은 이전 기록이다.

**method tag**: `rsc_html_first` (primary) 또는 `rsc_articlepdf` (fallback)

**1. landing HTML (preferred)**:
- URL: `https://doi.org/{DOI}` (자동 redirect to RSC landing)
- HTML body 직접 추출 (full text 노출)
- method tag: `rsc_html_first`

**2. articlepdf (fallback)**:
- URL pattern: `https://pubs.rsc.org/en/content/articlepdf/{year}/{journal_code}/{article_id}`
- landing HTML의 `<meta name="citation_pdf_url">` 추출 우선
- 또는 DOI 안의 journal/article 식별자 활용
- method tag: `rsc_articlepdf`

**검증**: 86/86 (100%) — Communications, full articles, reviews 모두 포함.

**주의**:
- RSC Communication은 2-page short article 정상. `page_count >= 4` 단독 필터 금지.
- `Tier B (short_fulltext_possible)` 인정 필요.

#### ⚠️ 알려진 실패 케이스 (2026-05-01 e-epoxidation 검증)

검증된 100%여도 paper별로 다음 케이스에서 자동 method가 fail (HTML scrape에 abstract만 들어감):

1. **ChemComm review/perspective (`cc` journal)** — 일반 article과 layout 다름
   - 사례: `10_1039_d4cc02025a` (Electrifying oxidation of ethylene and propylene, ChemComm 2024 review, 36p)
   - 증상: HTML scrape이 abstract (4544 chars / 548 words)만 추출
   - 원인: review/perspective는 일반 article의 fulltext div와 다른 ID 사용
   - **회복 방법**: Tier 1 (Claude in Chrome MCP) 또는 사용자 직접 다운 → `pubs.rsc.org/en/content/articlepdf/2024/cc/d4cc02025a` 패턴 그대로 PDF 직접 다운로드 가능 (검증 완료, 3.6MB / 11k words)

2. **RSC sub-journal (`qm` Materials Chemistry Frontiers, `mh` Materials Horizons, `nh` Nanoscale Horizons 등 RSC + 中国化学会 공동 발행)**
   - 사례: `10_1039_d2qm01316a` (Ag-doped Pd nano-dendritic, MCF 2023)
   - 증상: HTML scrape 4113 chars / 541 words (abstract만)
   - 원인: 일반 RSC와 다른 path / 다른 fulltext div ID 가능. publisher_matrix가 메인 RSC만 처리
   - **회복 방법**: 동일 articlepdf URL pattern으로 PDF 직접 다운 가능 (`pubs.rsc.org/en/content/articlepdf/2023/qm/d2qm01316a` — 1.7MB / 6k words 정상 회수)

**adapter 갱신 권장**: scripts에서 RSC `journal_code` 별로 layout 분기 (cc-review / qm/mh/nh sub-journal / 일반 article).

---

### A.2 MDPI — `10.3390`

**method tag**: `mdpi_direct_pdf`

**URL pattern**:
- preferred: `https://mdpi-res.com/d_attachment/{journal}-{vol:02d}-{article:05d}/article_deploy/{journal}-{vol:02d}-{article:05d}.pdf`
- fallback (`www.mdpi.com/.../pdf` 직접) — Cloudflare 차단됨, 사용 금지

**DOI parsing 예시**:
- DOI `10.3390/molecules28041797` → journal=`molecules`, vol=28, article=041797 → `mdpi-res.com/d_attachment/molecules/molecules-28-01797/article_deploy/molecules-28-01797.pdf`
- DOI `10.3390/polym14235328` → journal=`polym`, vol=14, article=05328

**검증**: 5/5 (100%).

---

### A.3 Springer — `10.1007` 또는 `10.1023`

**method tag**: `springer_content_pdf` (primary) 또는 `springer_pdf_pypdf_cmap_decode` (fallback)

**URL pattern**:
- direct PDF: `https://link.springer.com/content/pdf/{DOI}.pdf`
- DOI quote: `https://link.springer.com/content/pdf/{quote(DOI, safe='/:')}.pdf`

**fallback 처리**:
- 일부 옛 paper PDF는 text 깨짐 → pypdf CMap decode 보강
- method tag: `springer_pdf_pypdf_cmap_decode`

**검증**: 16/16 (100%).

#### ⚠️ 예외: JAOCS (Journal of the American Oil Chemists' Society) — D 그룹

- DOI prefix: `10.1007/s11746-`
- AOCS Press 발행, Springer Nature 호스팅, **KIST library subscription 미포함**
- 발견 paper (2026-04-30): `10_1007_s11746_999_0140_1`
- 처리: 즉시 D.5로 분류, abstract-only

DOI 분기 로직:
```python
if doi.startswith('10.1007/s11746-'):
    publisher_class = 'D'  # JAOCS, KIST 미구독
else:
    publisher_class = 'A'  # 일반 Springer
```

---

### A.4 Thieme — `10.1055`

**method tag**: `thieme_generic_html`

**URL pattern**:
- DOI resolve → Thieme landing page
- HTML body 직접 추출 (KIST IP에서 본문 노출)

**검증**: 4/4 (100%, 옛 paper 기준).

#### ⚠️ 2023+ 신간 일부 — D 그룹 검증

KIST IP에서도 fulltext 미접근 검증된 신간 (사용자 manual 시도, 2026-04-30 발견):
- `10_1055_a_2004_6485` (2023, Asymmetric Organic Electrochemistry...)
- `10_1055_a_2197_7356` (2024, Organoselenium Compounds in Catalysis)

**가설**: 일부 최근 paper (a-2004-, a-2197- 형식 신 ID)가 KIST 구독 범위 외이거나 OA 미적용. 옛 paper는 정상.
**대응**: 자동 시도 fail 시 즉시 abstract-only 전환 (재시도 회피). 향후 유사 패턴 paper 만나면 사용자 확인 후 D 그룹으로.

---

### A.5 Pharm Soc Japan / J-STAGE — `10.1248`

**method tag**: `pharm_soc_japan_generic_html`

**URL pattern**:
- DOI resolve → J-STAGE article page (`https://www.jstage.jst.go.jp/article/...`)
- HTML body 직접 추출

**검증**: 3/3 (100%) — Chemical and Pharmaceutical Bulletin paper 포함.

**주의**: BCSJ / Chemistry Letters (10.1246) 도 J-STAGE 호스팅 가능했으나 OUP 이전됨 → 별도 분류 (D 그룹).

#### ⚠️ 알려진 실패 케이스 (2026-05-01)

J-STAGE는 volume/issue 정보가 URL path에 들어가는데 자동 fetch 시 paper별로 path 추정 실패 가능:
- 사례: `10_1248_cpb_c12_00806` (Chem Pharm Bull 2013, vol 61 issue 8)
- 증상: HTML scrape 3480 chars / 414 words (abstract만)
- 원인: J-STAGE article URL은 `/article/cpb/{volume}/{issue}/{volume}_{article_id}/_article` 형태인데 DOI에서 volume/issue 직접 추출 불가
- **회복 방법**: 정확한 URL은 `https://www.jstage.jst.go.jp/article/cpb/61/8/61_c12-00806/_pdf` (volume=61, issue=8). DOI fetcher가 J-STAGE landing 거쳐 volume/issue 추출하는 path 확보 필요. 또는 사용자 직접 다운로드 (검증 완료, 315KB / 2395 words 정상)
- **adapter 갱신 권장**: J-STAGE는 DOI resolver redirect → article landing → `<meta name="citation_pdf_url">` 추출 (현재 generic_html은 abstract만 잡힘)

---

### A.6 Pleiades RU / Russian Springer — `10.1134`

**method tag**: `pleiades_springer_ru_generic_html`

**URL pattern**:
- DOI resolve → SpringerLink Pleiades Russian journal landing
- HTML body 추출

**검증**: 2/2 (100%).

---

### A.7 Tsinghua OAE — `10.20964` 또는 `10.26599`

**method tag**: `oa_metadata_pdf` (primary) 또는 `tsinghua_oae_generic_html` (fallback)

**1. OA metadata fetcher (preferred)**:
- Codex가 발견한 OA fallback method. OpenAlex / Crossref OA url 활용
- direct PDF 회수

**2. landing HTML (fallback)**:
- HTML body 추출

**검증**: 3/3 (100%).

**주의**: 일부 10.20964 paper는 IJES (Int. J. Electrochem. Sci.)이며, 2022년부터 Elsevier ScienceDirect로 호스팅 이전. → C.2 분류로 처리 (사용자 수동).

#### ⚠️ 알려진 실패 케이스 — SciOpen 호스팅 (2026-05-01)

`10.26599` 일부 paper (Tsinghua Nano Research 등)는 sciopen.com 자체 platform으로 이전:
- 사례: `10_26599_nr_2025_94907832` (Recent progress in electrocatalytic olefin epoxidation, Nano Research 2025 review, 31p)
- 증상: 자동 fetch이 abstract만 회수 (9332 chars / 1140 words)
- 원인: sci-retr publisher_matrix가 SciOpen.com URL pattern 미지원. Crossref/Unpaywall fallback도 sciopen 직접 URL 못 잡음
- **회복 방법**: `https://www.sciopen.com/article/10.26599/NR.2025.94907832` 직접 접근 → PDF 다운 (검증 완료, 20.9MB / 21k words 정상)
- **adapter 갱신 권장**: SciOpen.com pattern 추가 (`https://www.sciopen.com/article/{DOI}` → article 페이지 + `<meta name="citation_pdf_url">` 추출). 큰 review PDF (20MB+) timeout 방지 위해 `--max-time 240`

---

## B. 자동 수집 가능 (token/IP 환경 필요)

### B.1 Wiley — `10.1002`

**method tag**: `wiley_tdm_api_pdf`

**환경**:
- `WILEY_TDM_TOKEN` (= `TDM_API_TOKEN` alias) 필요
- 발급: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining

**method**:
- TDM API endpoint(`api.wiley.com/onlinelibrary/tdm/v1/articles/{DOI}`)를 requests 로 직접 불러 PDF 회수 (2026-09-27: `wiley-tdm` 패키지와 그 `verify = False` 우회는 쓰지 않는다. 인증서는 truststore 로 확인)

**검증**: 3/3 (100%).

**Wiley 는 TDM 토큰이 필요하다 (2026-09-24 실측·사용자 결정)**: 토큰이 없으면 도구로는 받을 수 없다. (1) 창 없는 일반 요청은 onlinelibrary.wiley.com 이 첫 응답부터 403. (2) 도구가 띄운 보이는 Chrome 은 사용자가 확인을 세 번 눌러도 확인 창이 반복되어 논문 페이지로 넘어가지 않았다 (5편 시험, 첫 편에서 중단). 그래서 자동 단계는 Wiley 에 요청을 보내지 않고, 사용자 확인 단계도 창을 열지 않고 `_collect/manual_download.csv` (논문 주소 + 저장 경로) 만 만든다. 사용자가 평소 쓰는 Chrome 에서 받아 저장하면 `status` 가 본문 추출까지 반영한다. 토큰은 구독 논문의 경우 기관 IP 대역에서만 유효하고 OA 는 어디서나 된다. 첫 사용 때 발급 페이지를 한 번 안내한다.

---

### B.2 ACS — `10.1021`

**method tag**: `acs_browser_session_pdf_via_credentials_fetch` (자동, Playwright) 또는 `acs_browser_mcp_open_pdf` (NEW 2026-05-02 검증, Claude in Chrome MCP 자동) 또는 `manual_acs_user_download_pdf_promote` (timeout 시 수동)

**⭐ Tier 1 (NEW 2026-05-02) — Claude in Chrome MCP 자동화**:
- navigate to `https://pubs.acs.org/doi/{doi}`
- KIST IP institutional access 자동 (구독)
- JS: `Array.from(document.querySelectorAll('a, button')).find(e=>/^Open PDF/i.test(e.innerText))` → click (target 제거) → 같은 탭 PDF URL redirect (`pubs.acs.org/doi/pdf/{doi}?ref=article_openPDF`)
- fetch(location.href, credentials:'include') → arrayBuffer → %PDF magic 검증 → Blob download
- 보통 text-PDF (OCR 불필요)
- 검증: `ja00012a038` 10,650→29,226 chars / 4,640 words / 4 sections (5p text-PDF, 577KB)

**환경**:
- KIST IP institutional access (구독)
- 시스템 Chrome (Playwright)
- chrome_profile (KIST SSO 로그인 완료 — `chrome_profile_kistsso`)

#### ⚠️ 절대 금지: HTML scrape (`pubs.acs.org/doi/abs/{doi}` 또는 `pubs.acs.org/doi/{doi}`)

**과거 실수 (2026-04-29 batch)**: ACS landing HTML을 `page.content()`로 받아 본문 추출 시도. 본문이 `Recommended Articles` section으로 잘못 들어가는 truncation 발견 (2026-04-30 검증).

**증상 (paper_sections 진단)**:
```
SEC_001 'title' 138 words
SEC_002 'Publication History' 20
...
SEC_007 'References' 8202   ← 비대
SEC_008 'Cited By' 3426     ← 비대
SEC_010 'Recommended Articles' 16790  ← 진짜 본문 여기에 잘못 들어감
```

**검출 query (HTML scrape 결과 sanity check)**:
```python
import re
body_titles = re.compile(r'(introduction|result|discussion|method|mechan|conclusion|abstract|catalytic|performance|synth|characteri|experiment|theor)', re.I)
junk_titles = re.compile(r'(recommend|cited.by|citation|publication.history|terms.*conditions|author.information|acknowledg|export|share|qr.code|how.to.cite|download|metric|references)', re.I)
# truncation 조건: body_titles_words < 200 AND junk_titles_words > 1500
```

**규모**: ACS 112편 batch에서 **90편 (80%)이 truncation**. 결과적으로 v0.2 batch의 ACS HTML scrape 결과 거의 전부 폐기 + Phase 1.5에서 PDF 직접 fetch로 재수집.

#### ✅ 정상 method: PDF 직접 fetch (browser session + credentials)

**method 절차**:
1. Playwright `launch_persistent_context` (user_data_dir = `chrome_profile_kistsso`, headless=False)
2. publisher 도메인 warmup 먼저 (`pubs.acs.org`, 8s wait)
3. paper별 JavaScript fetch with credentials:
   ```javascript
   const resp = await fetch("https://pubs.acs.org/doi/pdf/{doi}", {
       credentials: 'include',
       headers: { 'Accept': 'application/pdf,application/octet-stream,*/*;q=0.8' }
   });
   const buf = await resp.arrayBuffer();
   // base64 → Python bytes
   ```
4. 1차 fail → `/doi/epdf/{doi}`, 그래도 fail → `expect_download` event (timeout 30s)
5. PDF magic bytes (`%PDF-`) 검증 후 `papers/{paper_id}/pdf/{paper_id}.pdf` 저장

**rate-limit 정책 (2026-04-30 Phase 1.5 검증)**:
- 도메인 자주 전환 금지 — ACS 끝낸 후 다른 publisher (사용자 명시 요구)
- paper-interval 45s 안전 (90s는 과다, 30s 미만은 위험)
- chunk-size 30 + chunk-wait 15min 충분
- 무인 1.5h batch 가능

**검증 (2026-04-30 Phase 1.5)**:
- 85편 시도 → 자동 83/85 (97.6%) + 사용자 수동 2/85 (timeout) = **100%**
- timeout 2편 패턴: `acs_doi_pdf` browser fetch fail → `acs_nav_download` 30s timeout → 사용자 수동
- 정상 회수된 PDF는 본문 truncation 없음 (citation_pdf_url 직결)

**참조 스크립트**:
- 개념 검증: `scripts/acs_browser_download_test_codex.py` (2 sample, 100%)
- 본 batch: `scripts/v02_590batch_pdf_download_safe.py` (85편 batch)

---

### B.3 Science / AAAS — `10.1126`

**method tag**: `science_direct_pdf_corrected_doi_browser_accept` 또는 `..._direct_no_referer`

**환경**:
- KIST IP (AAAS 구독)
- 시스템 Chrome

**method**:
1. **DOI 보정 필수**: paper_id가 short id (`adh4355`, `adk5097`) 면 풀 DOI `10.1126/science.{shortid}` 로 변환
2. URL pattern: `https://www.science.org/doi/pdf/10.1126/science.{shortid}` (또는 `/doi/epdf/...`)
3. Playwright + browser session + browser-style HTML Accept header
4. (옵션) Referer header 제거 시도

**ePDF viewer 경로**: `https://www.science.org/doi/epdf/10.1126/science.{shortid}` (사용자 확인)

**검증**: 2/2 (100%).

---

### B.4 Elsevier ScienceDirect — `10.1016` 또는 `10.1006`

**method tag**: `elsevier_article_retrieval_api_pdf` (OA 논문 자동), `elsevier_sciencedirect_browser_html_userassist` (구독 논문, 사용자 확인 협력), `elsevier_oa_copy_*` (Unpaywall/OpenAlex 사본)

**⭐ 2026-09-24 갱신 — 구독 논문은 직접 다운로드**: 봇 탐지 우회 설정을 제거한 뒤, 도구가 띄운 보이는 Chrome 에서 ScienceDirect 확인 창은 사용자가 세 번 눌러도 반복되어 논문 페이지로 넘어가지 않았다(새 프로필, 1편). 그래서 구독 논문은 창을 열지 않고 `_collect/manual_download.csv` (ScienceDirect 논문 주소 + 저장 경로) 로 넘기고, 사용자가 평소 쓰는 Chrome 에서 받아 저장하면 `status` 가 본문 추출까지 반영한다. OA 논문은 아래 1·2 단계대로 자동. 아래 3번의 창 협력 절차는 2026-09-23 기록(당시는 우회 설정이 남아 있었음)으로 현재는 쓰지 않는다.

**2026-09-23 확립 절차 (기록) — "저널/논문에 따라 사람 확인이 필요하다" 를 알리고 협력으로 받는다**

배경: Elsevier 가 KIST 에 기관 토큰(X-ELS-Insttoken) 발급을 거절 (2026-09). API 키만으로는 구독 논문에 대해 `X-ELS-Status: WARNING - Response limited to first page because requestor not entitled` 로 **첫 페이지만** 온다. ScienceDirect 를 자동화 브라우저(Playwright)로 열면 **방문마다 Cloudflare Turnstile** 이 뜬다 (clearance 쿠키가 있어도 재확인, 2026-09-23 실측). 일반 `requests` HTML 경로(5월 224편 성공)는 현재 403.

1. **API 먼저** (`X-ELS-APIKey` 만): OA 논문은 전문 PDF+XML 이 그대로 온다 → 자동. 응답 헤더 `X-ELS-Status` 에 "first page" / "not entitled" 가 있으면 preview 를 `pdf/{id}.pdf` 로 **저장하지 말고** `manual_pdf_dropbox/{id}/request.json` 에 사유 `Elsevier: API not entitled` 로 큐 등록 (당시 runner.py `collect_elsevier`, 2026-09-27 삭제. 지금은 sci_collect.py `h_elsevier` 가 OA 논문에만 API 를 부르고, 첫 페이지만 오면 ScienceDirect 밖 OA 사본을 찾은 뒤 웹 경로로 넘긴다).
2. **OA 사본**: Unpaywall / OpenAlex `best_oa_location` 이 있으면 저자 원고·PMC 사본을 자동 수집 (`elsevier_oa_copy_*`).
3. **사용자 확인 묶음** (나머지 구독 논문): 사용자가 자리에 있을 때 보이는 Chrome(수집 프로필 `chrome_profile_kistsso`) 으로 논문 페이지(`/science/article/pii/{PII}`, PII 는 Crossref `alternative-id`) 를 연다 → Turnstile 이 뜨면 **사용자가 클릭 (2026-09-23 실측: 서로 다른 저널 3편에 2회 — 첫 편은 반드시, 이후 편은 Cloudflare 점수에 따라 다시 뜰 수 있음; 저널과 무관, 도메인 공통 쿠키)** → 본문 `#aep-article-fulltext` 로드 확인 → `page.content()` 를 `write_html_source()` 로 저장 → 좌상단 'View PDF'(`a.accessbar-utility-component`) 링크를 같은 세션에서 요청(request → 페이지 안 fetch)해 PDF 가 정상적으로 내려오면 저장. **PDF 링크에 Elsevier 확인(JS)이 걸려 HTML 이 오면 우회하지 않는다** → 사용자가 창에서 'View PDF' 를 눌러 `papers/{id}/pdf/{id}.pdf` 로 직접 저장하면 `sci_collect.py status` 가 full 로 반영 (2026-09-24 실측: 구독 3편 모두 본문 HTML 은 자동, PDF 는 확인이 걸려 직접 저장 대상). 논문 간격 30초 (2026-09-24 실험: 3편 연속, 확인 창 첫 편 1회, 차단 문구 없음). 구현: `scripts/sci_collect.py` `a_elsevier`.
4. 사용자 안내 문구: "Elsevier 구독 논문 N편은 사람 확인이 필요합니다. 창이 열리면 확인 체크박스를 눌러 주세요 (첫 논문에서 1회, 이후 논문에서도 뜰 수 있음; 30초 간격, 창 옆에 계셔 주세요). PDF 에 확인이 걸린 논문은 저장 경로를 알려 드리니 'View PDF' 로 직접 저장해 주세요."

⛔ **폐기**: `X-Forwarded-For: 143.248.0.1` 헤더 레시피(구 Tier 0). 143.248.0.0/16 은 **KAIST** 대역이며(RDAP 확인) 타 기관 IP 사칭이다. KIST 망(161.122.0.0/16)에서는 헤더 없이 실 IP 로 접근하며, API 는 KIST IP 로도 entitled 되지 않는다.

**Tier 1 — Claude in Chrome MCP** (Tier 0 실패 시 fallback):

**⭐ Tier 1 (NEW 2026-05-02) — Claude in Chrome MCP 자동화 (Playwright보다 우선)**:

방법 A (modern paper 2010+, HTML 본문 노출):
- navigate to `https://www.sciencedirect.com/science/article/pii/{PII}`
- 첫 1회 사용자 CAPTCHA 해결 필요 (clearance cookie 발급 후 같은 도메인 자동 통과)
- JS: `el.innerText` from `#aep-article-fulltext` → Blob download
- 검증: `apcatb_2019_118337` 6,983→57,607 chars / 8,625 words / 6 sections

방법 B (legacy paper 1990s/2000s, PDF only):
- navigate to article page
- ⭐ 좌상단 'View PDF' 클릭 — `document.querySelector('a.accessbar-utility-component')` 강제 (sidebar 추천 paper의 'View PDF' 함정 회피)
- 같은 탭이 S3 PDF URL로 redirect → fetch(location.href, credentials:'include') → Blob download
- ⭐ navigate 후 `location.href.includes(expectedPii)` 검증 — 미일치면 wrong-paper drift abort
- image-only면 ocrmypdf+tesseract 자동 적용
- 검증: `jcat_1995_1188` 3,672→59,146 chars / 9,478 words / 6 sections (15p image-only OCR)

자세한 procedure: `references/browser_mcp_recovery.md`

#### 핵심 우회법 (2026-04-30 검증):

❌ TDM endpoint (`/pdfft?isDTMRedir=true&download=true`, `/pdf?download=true`)는 publisher TDM 정책 (`<meta name="tdm-reservation" content="1">`) 으로 차단

✅ **article HTML page** (`/science/article/pii/{PII}?via=ihub`) 은 KIST IP institutional access로 본문 정상 노출

**환경**:
- KIST IP institutional access
- Playwright + 시스템 Chrome
- chrome_profile (Cloudflare clearance cookie 보유)
- **rate-limit 안전 정책 강제** (별도 문서: `safe_rate_policy.md`)

**method**:
1. 각 paper의 `papers/{paper_id}/source.json`의 `final_url` 활용 (정확한 article URL)
2. Playwright `page.goto(article_url, wait_until="networkidle", timeout=120000)`
3. `time.sleep(8)` (현대 paper) 또는 `time.sleep(12)` (1990s-2000s)
4. `page.content()` → `write_html_source()` (HTML body 추출 + figures + 검증 + papers/{pid}/로 promote)

**fallback 순서** (B 그룹은 다음 순서로 시도):
1. Elsevier API (key + httpAccept=pdf|xml) — partial PDF detect
2. ScienceDirect direct PDF candidates (`/pdfft`, `/pdf?download=true`) — 보통 차단됨
3. **NEW: ScienceDirect article HTML page (KIST IP + Playwright)** ⭐ 핵심
4. Browser PDF fallback

**검증**:
- 184편 중 51편 API success
- 133편 fail → article HTML retry로 ~110편 추가 회복 (rate-limit 정책 적용 후)

**critical**: §C 외 publisher와 달리 ScienceDirect는 rate-limit 위험. `references/safe_rate_policy.md` 강제 적용.

#### ⚠️ 알려진 실패 케이스 — 옛날 Elsevier PII 매핑 (2026-05-01)

1990s-2000s Elsevier paper들은 PII 형식이 `030451029285005Z` (DOI `10.1016/0304-5102(92)85005-Z`) 또는 `S0040403900730747` (DOI `10.1016/S0040-4039(00)73074-7`) 같은 옛날 형식. ScienceDirect URL은 `https://www.sciencedirect.com/science/article/pii/{PII}` 형태인데 DOI에서 PII 자동 매핑 실패 케이스 있음.

- 사례 1: `10_1016_0304_5102_92_85005_z` (Elsevier J Mol Catal 1992)
  - DOI: `10.1016/0304-5102(92)85005-Z` → PII: `030451029285005Z` (괄호/하이픈 제거 + Z 보존)
  - 자동 fetch 결과: abstract만 (9174 chars / 1401 words)
  - 사용자 직접 다운: 868KB PDF / 6006 words 정상 회수
  - 다운로드 파일명: `1-s2.0-030451029285005Z-main.pdf` (ScienceDirect 표준)

- 사례 2: `10_1016_s0040_4039_00_73074_7` (Elsevier Tetrahedron Lett 1994)
  - DOI: `10.1016/S0040-4039(00)73074-7` → PII: `S0040403900730747` (S 접두사 + 괄호/하이픈 제거)
  - 자동 fetch 결과: abstract만 (5174 chars / 668 words)
  - 사용자 직접 다운: 305KB PDF / 1910 words 정상 (1994 Tet Lett short comm 본질적으로 작음)
  - 다운로드 파일명: `1-s2.0-S0040403900730747-main.pdf`

**원인**:
- Elsevier API에는 본문 link 부재 (옛날 paper)
- ScienceDirect article page는 KIST IP institutional access로 본문 노출되지만 자동 fetch 시 봇 fingerprinting 차단 (Cloudflare anti-bot은 옛날 paper에서 더 엄격)
- DOI → PII 매핑 코드가 두 형식 (괄호 포함, S 접두사 등)을 모두 처리하지 못함

**회복 방법**:
- Tier 1 (권장): Claude in Chrome MCP — 사용자 KIST 망 Chrome 세션 (institutional access 유지) 통해 자동화
- DOI → PII 매핑 함수 갱신:
  ```python
  def doi_to_elsevier_pii(doi):
      # 10.1016/{rest} → PII
      rest = doi.replace('10.1016/', '')
      # 괄호 제거: (92)85005-Z → 9285005-Z
      pii = rest.replace('(', '').replace(')', '').replace('-', '')
      # S 접두사 보존, Z 등 끝문자 보존
      return pii
  ```
- ScienceDirect URL: `https://www.sciencedirect.com/science/article/pii/{PII}` 또는 `https://www.sciencedirect.com/science/article/abs/pii/{PII}` (abs landing → "Get rights and content" → fulltext 링크)

#### ⚠️⚠️ Elsevier TDM API 1-page preview 사고 (2026-05-01 신규 발견 — 가장 큰 사고)

Elsevier TDM API (`api.elsevier.com/content/article/doi/{doi}`) 가 `is-open-access=0` paper에 대해 entitlement 부족 시 **1-page preview PDF만 전달**. PDF는 정상 다운로드되어 (header 200 OK) success 마킹되지만 본문은 front-matter + abstract + introduction 시작만 (보통 5-7k chars / 600-1000 words / 1 physical page).

**사고 규모 (e-epoxidation Phase 2 batch)**:
- 8편 1-page preview로 받은 채 success 마킹 후 KB 진입
- coelec_2025_101733, electacta_2021_139018, apcatb_2025_125896, jallcom_2025_181219 (⭐ core target!), apsusc_2025_162865, molstruc_2025_142176, 0009_2509_92_87158_m, compositesb_2022_110281
- 사용자 manual download (KIST 망 institutional access)로 모두 회복

**검출 방법 (collection 단계 강제)**:

```python
import pypdf
from pathlib import Path

def detect_elsevier_1page_preview(pdf_path: Path, source_md: str, publisher: str) -> bool:
    """
    Elsevier 1-page preview 사고 검출.
    True = 사고, retry/manual 필요
    """
    if publisher != 'elsevier':
        return False
    
    # 1. PDF page_count 검증
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        if len(reader.pages) <= 1:
            return True  # Elsevier paper가 1페이지일 수 없음
    except Exception:
        pass
    
    # 2. source.md chars 검증
    if len(source_md) < 8000:
        return True
    
    # 3. 섹션 헤더 검증 — Methods/Results/Discussion/Conclusions 부재
    import re
    section_patterns = [r'\bMethods?\b', r'\bResults?\b', r'\bDiscussion\b', r'\bConclusions?\b', r'\bExperimental\b']
    section_hits = sum(1 for p in section_patterns if re.search(p, source_md, re.I))
    if section_hits < 2:
        return True  # front-matter only
    
    return False
```

**대응 절차**:
1. 검출 시 즉시 `collection_status='inadequate_1page_preview_elsevier'` 마킹
2. **Tier 1 fallback**: ScienceDirect article HTML page (B.4 method) 자동 retry — KIST IP institutional access로 fulltext HTML 노출
3. **Tier 2 fallback**: 사용자 manual download queue (`manual_pdf_dropbox/{paper_id}/request.json`)
4. 절대로 1-page preview를 success로 마킹 금지

**원인 추정**:
- Elsevier API entitlement 정책: `is-open-access=0` AND institutional subscription 무관 IP에서 호출 시 1-page preview만 제공
- API 응답 헤더에 `X-RateLimit-Type` 또는 `X-ELS-Status: PARTIAL` 같은 명시 가능 (검증 필요)
- 또는 응답 PDF의 metadata `/Producer`나 `/Title`에 "preview" 또는 "Sample" 표시 가능

---

### B.5 (옵션) ELSEVIER_INSTTOKEN

KIST 도서관 → Elsevier에서 발급 가능한 institutional token. 받으면 API에서 paywalled paper 직접 access 가능.

- 환경변수: `ELSEVIER_INSTTOKEN`
- 발급: KIST 도서관 사서에게 요청
- 효과: API 호출 시 `X-ELS-APIKey` + `X-ELS-Insttoken` 두 헤더 → fulltext API 풀림
- 받지 못하면 article HTML 우회법(B.4) 사용

---

## C. 자동 차단 → 사용자 수동 PDF + ingest

### C.1 ECS / IOPScience — `10.1149`

**상태 (2026-09-23 실측 갱신)**: IOP 는 Radware Bot Manager(perfdrive) 가 **요청마다 점수를 매겨** 통과/CAPTCHA 를 결정한다. 논문의 연도나 종류 문제가 아니다.
- 점수 요인: 브라우저 지문(파이썬 `requests` 는 즉시 차단, Chrome TLS 흉내 `curl_cffi` 는 처음엔 통과), 같은 IP 의 짧은 간격 반복 자동 요청, 이전 차단 이력.
- 증거: 같은 DOI(10.1149/2.0561913jes) 가 첫 curl_cffi 요청에서는 PDF 1.45 MB 성공, 한 시간 뒤 같은 방법·headless Chrome·보이는 Chrome 모두 CAPTCHA. 그날 첫 IOP 요청(2024 DOI) 은 일반 requests 로도 성공.
- 자동 재시도는 점수만 올린다.

**규칙 (2026-09-24, sci_collect.py `h_ecs`·`a_ecs`, 간격 90s)**:
1. 일반 요청으로 landing → `/pdf` 순서로 **1회만** 시도. TLS 지문 흉내(`curl_cffi`)·쿠키 복사·UA 위장은 하지 않는다(공통 정책).
2. 응답이 `validate.perfdrive.com` 으로 가거나 본문에 Radware 표식이 있으면 **즉시 중단, 재시도 금지** → 웹 경로 대상으로 넘긴다(`assist` 가 만드는 `_collect/manual_download.csv`).
3. 사용자가 보이는 Chrome(수집 프로필)에서 확인을 직접 통과하면 같은 창의 정상 세션에서 PDF 를 **페이지 안 `fetch(pdf_url, {credentials:'include'})`** 로 받는다 (2026-09-23 실측 1.46 MB). ⚠️ IOP 에서 `/pdf` 로 navigation 다운로드를 하면 Playwright 브라우저가 닫히는 현상이 있어 사용 금지. 정상 세션에서도 PDF 가 안 내려오면 사용자가 창에서 직접 저장 → `status` 반영.
4. 최후 수단: 사용자가 KIST 망 Chrome 으로 직접 PDF 다운 → `intake`(다운로드 폴더에서 논문 폴더로 옮기고 반영). `papers/{id}/pdf/{id}.pdf` 로 직접 저장했으면 `status`.

**검증**: 2026-09-23 3편 테스트 2/3 자동(일반 요청 1 + 당시 curl_cffi 1 — 이후 폐기), 1편 CAPTCHA → 사용자 클릭 후 페이지 안 fetch 로 완료.

---

### C.2 IJES (Int. J. Electrochem. Sci.) — `10.20964` 일부

**배경**: 2022년부터 Elsevier ScienceDirect로 호스팅 이전.

**절차**: ScienceDirect 직접 다운 → `intake`. (C.1과 동일 절차, source URL만 다름)

**파일명 형식 (사용자 다운로드)**: `1-s2.0-S{ISSN_year_id}-main.pdf` (IJES eISSN 1452-3981 기반)

**검증**: 2/2 (수동 ingest 성공).

---

## D. 시도 생략 — abstract-only resolution

자동/수동 모두 KIST 권한 미확보. 시도 자체 생략하고 abstract-only로 KB에 보존. KIST 도서관 구독 변경 시 재검토.

| publisher | DOI prefix | 호스팅 | 결정 사유 |
|---|---|---|---|
| World Scientific | 10.1142 | worldscientific.com | KIST 미구독 (옛 paper만, 최신 OA 일부는 A 그룹) |
| CSJ Chem Lett / BCSJ | 10.1246 | OUP (academic.oup.com) | OUP / J-STAGE 모두 권한 미확보 (BCSJ 옛 paper 1985 이전 포함) |
| Bentham Science | 10.2174 | benthamdirect.com | KIST 미구독 |
| Royal Society | 10.1098 | royalsocietypublishing.org | KIST 미구독 |
| **AOCS / JAOCS** | **10.1007/s11746-** | link.springer.com (호스팅) | **2026-04-30 신규**: AOCS Press, Springer 호스팅이지만 KIST 미구독 |
| Thieme 신간 일부 | 10.1055 (a-2004-, a-2197-, a-2309-, a-2508- 등 신 ID) | thieme-connect.com | 2026-04-30 신규 + 2026-05-01 추가 (a-2309, a-2508 KIST 미구독 검증) |
| **De Gruyter Z Phys Chem 옛 paper** | **10.1524** | degruyter.com | **2026-05-01 신규**: zpch (Z Phys Chem) 옛 paper (1994 등) 미구독. 일부 최신 OA는 가능할 수 있음 |

**처리 (`abstract_only_marker.json` 표준 — 2026-04-30 Phase 1.5 도입)**:

paper-folder에 marker 파일 생성:
```json
{
  "paper_id": "10_1007_s11746_999_0140_1",
  "doi": "10.1007/s11746-999-0140-1",
  "publisher": "Springer JAOCS",
  "status": "abstract_only_resolution",
  "decided_at": "2026-04-30",
  "reason": "KIST 미구독 (AOCS journal, Springer 호스팅)",
  "user_decision": "본문 회복 보류, abstract로 만족"
}
```

또는 기존 manual queue 패턴 (`manual_pdf_dropbox/{paper_id}/request.json` 의 `status: abstract_only_resolution`).

LLM extraction 단계에서 `abstract_only_resolution` 마크된 paper는 abstract만 처리, claim/metric confidence를 lower로 표시. PDF 회복 batch (source.md 교체) 자동 skip.

---

## E. 그 밖의 출판사·프리프린트 실측 (2026-09-26, 출판사 21곳 섞인 목록)

`generic` 경로(논문 페이지 → `citation_pdf_url` 등 PDF 후보 → SI)로 KIST 망에서 1편씩 시도한 결과. 사이트(호스트)별로 한 번 막히면 같은 사이트의 나머지 논문은 요청하지 않고 웹 경로로 넘긴다. 막힌 논문 자체도 실패가 아니라 웹 경로 대상으로 표시한다. 2026-09-26 부터 아래 사이트는 접두어로 이름이 붙고(frontiers, plos, beilstein, copernicus, aps, cambridge, tandf, pnas, aip, oup, ieee, chemrxiv), 막히는 여섯 곳은 설정 `web_only_publishers` 에 들어 있어 요청 자체를 보내지 않는다.

**간격 확인 (2026-09-26, 사이트마다 새 논문 3편, 일곱 사이트 동시)**: 설정 간격(5초, Springer 2초)으로 연속 요청해 차단·429 없음. 한 편 완료 간격은 PLOS 8~9초, Springer 4~6초, Frontiers 9~11초, Cambridge 8초, APS 5~7초, Beilstein 23~29초, Copernicus 40~54초(8~11 MB PDF). 차단 직전의 최소 간격은 정책상 찾지 않는다. 이 간격으로 수십 편 규모까지는 안전하다고 본다.

| 사이트 | 결과 | 비고 |
|---|---|---|
| Frontiers (`10.3389`) | 자동 OK, PDF + HTML 본문 | OA |
| PLOS (`10.1371`) | 자동 OK | OA |
| Beilstein (`10.3762`) | 자동 OK | OA |
| Copernicus (`10.5194`) | 자동 OK | OA |
| APS Physical Review (`10.1103`) | 자동 OK (Phys. Rev. B) | 구독, KIST IP. Phys. Rev. D·Applied 는 페이지에 PDF 링크가 없어 실패 → 구독 밖으로 보임, 웹 경로로 확인 |
| Cambridge (`10.1017`) | 자동 OK | 구독, KIST IP |
| Springer (`10.1007`) | 자동 OK | 기존과 같음 |
| Taylor & Francis (`10.1080`) | 403 → 웹 경로 | 첫 요청부터 차단. 웹: 페이지 아래 "Download PDF" 바로 저장 (playbook 3.7) |
| PNAS (`10.1073`) | 403 → 웹 경로 | 웹: SI "DOWNLOAD" → "Download PDF"(Cloudflare 확인 스스로 통과) (playbook 3.8) |
| AIP (`10.1063`) | 403 → 웹 경로 | 웹: 도구 막대 "PDF" 새 탭, 바로 저장 (playbook 3.9) |
| Oxford (`10.1093`) | 403 → 웹 경로 | 웹: Supplementary data 목록 파일들 → 상단 "PDF"(Cloudflare 확인 스스로 통과) (playbook 3.10) |
| IEEE (`10.1109`) | 202(확인 응답) → 웹 경로 | 논문 페이지 대신 확인용 응답. 웹: "PDF" → 보기 페이지의 "열기" (playbook 3.11) |
| ChemRxiv (`10.26434`) | 403 → 웹 경로 | Crossref 출판사 이름이 ACS 라 웹 전용에 묶이던 것을 접두어로 chemrxiv 고정. 약어 ChemRxiv. 웹: 미리보기 틀 아래 "Download PDF" (playbook 3.12) |
| Nature Communications 갓 나온 논문 | 실패(본문 6.6천 자) | 페이지에 초록만 있고 `.pdf` 주소가 HTML 로 응답. 며칠 뒤 다시 |
| Hindawi (`10.1155`) | Crossref 출판사가 Wiley → 토큰 없으면 웹 경로 | |
| IOP 비-ECS 저널 (`10.1088`) | Crossref 출판사가 IOP → ecs 로 분류, 웹 경로 | |
| Thieme (`10.1055`), World Scientific (`10.1142`) | 초록만 저장 | 미구독 설정 |

웹 경로 요령은 playbook 3절에 열두 사이트(원래 여섯 + Taylor & Francis, PNAS, AIP, Oxford, IEEE, ChemRxiv) 것이 있다. 그 밖의 사이트는 논문 페이지에서 PDF 링크를 찾아 받고, 자주 쓰게 되면 요령을 적는다.

## 새 publisher 추가 가이드

새 publisher 만나면:
1. DOI prefix 식별
2. 자동 method 시도 (일반 경로: 논문 페이지 → PDF 후보)
3. KIST 권한 + 자동 요청을 막는지 (첫 요청이 403·202·확인 페이지면 웹 경로, 우회하지 않는다)
4. 검증 결과에 따라 A/B/C/D 분류
5. 이 문서 갱신
6. `scripts/sci_collect.py` 갱신: `PREFIX_PUBLISHER`(접두어 → 이름), 막히면 `DEFAULT_CONFIG["web_only_publishers"]` 와 `WEB_NOTE`, 미구독이면 `abstract_only_publishers`, 전용 처리가 필요할 때만 `collect_one` 에 `h_*` 함수

가장 흔한 패턴 (낮은 비용 검증 우선) — `h_landing_generic`:
- 논문 페이지(doi.org) HTML 의 본문 컨테이너 + `citation_pdf_url` 등 PDF 후보 (`runner.html_pdf_candidates`)
- PDF 는 필수 보관, 텍스트는 XML > HTML > PDF 순, 본문 판정은 `runner.classify_content` (길이 ≥ 3000 + DOI/제목 일치)
- 403·429·503·202·확인 페이지 → 같은 사이트의 나머지 논문은 요청하지 않고 웹 경로
