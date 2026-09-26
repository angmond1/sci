// sci-retr 웹 경로 보조 스크립트 (2026-09-27 전 출판사 연습 반영). Claude in Chrome 의 javascript_tool 로 논문 페이지에서 실행한다. 클릭은 하지 않는다.
// javascript_tool 에는 이 파일을 그대로 넣는다. 맨 앞 await 가 없으면 결과가 {} 로 빈다(2026-09-27).
//   (Codex 의 evaluate_script 는 함수를 받으므로 async () => { return await (async () => { … })(); } 모양으로 감싼다.)
// 결과(JSON, 1,000자 안으로 짧게 — javascript_tool 출력이 약 1,000자에서 잘린다):
//   t 제목 40자, v visibilityState, w innerWidth, dpr devicePixelRatio, ms 실제로 기다린 시간, sih SI 절 제목(h1~h4·summary·button)이 있으면 1
//   s: SI 후보, m: 본문 후보 — 항목은 [번호, 글자 24자, 경로 끝 36자, x, y] 또는 [번호, 글자, 경로, "접힘"]
//      x, y 는 sciretrFocus(번호) 가 그 요소를 화면 가운데(상단 고정 막대 여백 scroll-padding-top 아래)로 옮긴 뒤의 화면 좌표 예상이다.
//        페이지 맨 위·끝에서는 가운데까지 못 가는 것도 반영한다. 화면 가운데를 가정하지 않는다(2026-09-27 ChemRxiv y 669·522, 세 번 빗나감).
//      "접힘" 은 화면에 안 보이는 링크다(접힌 절, 닫힌 메뉴, 틀에 가려 크기 0). 눌러 펼치거나, 파일 주소면 sciretrGo(번호) 로 받는다.
//      Silverchair 사이트(AIP·ACS·RSC·Oxford)의 SI 는 경로 끝 대신 '{형식}/{코드}' 를 보인다. 형식 칸이 pdf·docx·doc 가 아닌 것은 뺀다(2026-09-27 AIP zip).
//      m 항목 끝의 "online" 은 온라인 보기(epdf·reader)라 대개 누르지 않는다(Science 만 온라인 보기를 거친다).
//   경로가 빈 s 항목은 접힌 절의 제목(Wiley a.accordion__control)이나 누르면 목록이 열리는 버튼(IEEE "Supplemental Items")이다. 눌러 펼친 뒤 다시 돌린다.
//   경로가 "#"·"js" 인 항목은 목차 이동·메뉴다(AIP 는 SI 가 없어도 늘 있다). 진짜 후보 뒤에 둔다. SI 유무는 s 의 파일 링크와 sih 로 본다.
// 기다림: HTML 을 다 읽을 때까지, 이어서 그림 등이 뜰 때까지(최대 3초) 기다린 뒤, 후보가 나타날 때까지 1초 간격으로 확인하고 나타나는 즉시 돌려준다(합계 약 20초까지).
//   다 읽기 전에 돌려주면 아래쪽 SI 가 아직 없고 좌표가 나중에 바뀐다(2026-09-27 AIP x 529→608). 끝내 비면 t 로 확인 화면("Just a moment…")인지 본다.
// 거르는 것: 다른 사이트 링크(SI 파일 도메인 ars.els-cdn.com·silverchair-cdn.com·IOP S3 는 허용), 다른 논문의 PDF(주소에 이 논문 PII·DOI 가 없는 것),
//   본문 속 'Figure S1'·'Table S2' 참조 링크, 호·권 링크(/vol/…/suppl/), 사이트 자료(/pb-assets/), 묶음 버튼('PDF and Supporting…'),
//   학회 초록집 호 이름(Oxford 'Supplement_1' — SI 가 아니다), zip·스프레드시트·동영상·PowerPoint.
// 누르기: 한 호출(browser_batch)에 window.sciretrFocus(번호, x, y) 와 그 좌표 클릭을 함께 넣는다.
//   sciretrFocus 는 요소를 화면 가운데로 옮기고 실제 화면 좌표(x, y)와 hit(그 좌표에 그 요소가 있는지, elementFromPoint)를 준다.
//   예상 좌표(x, y)를 함께 주면 그 자리에 이 요소가 없을 때 다음 클릭 한 번을 투명한 막으로 받아 버린다(guard 1, 8초 뒤 저절로 없어짐).
//   그러면 엉뚱한 곳이 눌리지 않는다. guard 가 1 이면 돌려받은 x, y 로 다시 누른다. 넓은 링크는 글자 쪽(왼쪽 40px) 좌표다.
//   스크린샷 좌표계가 innerWidth 와 다르면 클릭 좌표에만 (스크린샷 폭 ÷ innerWidth) 를 곱하고, sciretrFocus 에는 이 스크립트의 좌표를 그대로 준다.
// window.sciretrGo(번호) — 그 링크 주소로 탭을 옮긴다(링크를 누른 것과 같다. 주소는 출력하지 않는다). 틀·안내 창이 링크를 가리거나 "접힘" 인 파일 링크에 쓴다(T&F figshare 등).
await (async () => {
  try {
    const t0 = Date.now();
    const waitEvt = (name, cap) => new Promise((r) => { addEventListener(name, r, { once: true }); setTimeout(r, Math.max(0, cap)); });
    if (document.readyState === 'loading') await waitEvt('DOMContentLoaded', 20000);
    if (document.readyState !== 'complete') await waitEvt('load', Math.min(3000, 20000 - (Date.now() - t0)));
    const self = (() => {   // 이 논문의 식별자: 주소의 PII 나 DOI 끝부분
      const u = decodeURIComponent(location.pathname);
      const pii = u.match(/\/pii\/([A-Z0-9]+)/i);
      if (pii) return pii[1].toLowerCase();
      const doi = u.match(/10\.\d{4,9}\/[^/?#]+/);
      return doi ? doi[0].split('/').pop().toLowerCase() : '';
    })();
    const CROSS_OK = /ars\.els-cdn\.com|silverchair-cdn\.com|cfn-live-content-bucket-iop-org\.s3/i;
    const SKIP = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|mp4|avi|mov|mp3|wav|cif|pptx?|ppt)(\?|$)/i;
    const SKIP_PATH = /\/vol\/\d+\/suppl\/|\/pb-assets\/|\/toc\/|\/loi\/|\/lookup\/doi\/|\/article-supplement\/\d+\/(?!pdf\/|docx?\/)[a-z0-9]+\//i;
    const SI_HREF = /mmc\d|suppl|supplement|sifile|_si_|-sup-|_sm\b|\/data\b|supporting|suppdata|si\.pdf|-si\b|downloadSupplement|\.sapp\b|supp\d/i;
    const SI_TEXT = /supp(orting|lementa)|\bSI\b|Supplementary|Download \w+ (file|document)|Multimedia component/i;
    const SI_HEAD = /^(appendix [a-z0-9]+\.? )?(supplementa|supporting)/i;
    const INLINE_REF = /^(fig(ure)?s?\.?|tables?|schemes?|eqs?\.?|movies?|S)\s*S?\d/i;
    const MAIN_HREF = /\/doi\/pdf\/|\/pdfft|\/content\/pdf\/|\/article-pdf\/|\/articlepdf\/|\/pdf(\/|\?|$)|\.pdf(\?|$)|epdf|\/reader\//i;
    const MAIN_TEXT = /^\s*(download pdf|view pdf|open pdf|pdf download|pdf|download)\s*$/i;
    const ONLINE = /epdf|\/reader\//i;
    const NOISE = /powerpoint|full issue|download \(\d+\)|download all|with cover|wechat|pdf and supp/i;
    const P = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;   // 상단 고정 막대 여백 (ChemRxiv 108px)
    const pt = (r) => {   // sciretrFocus 뒤의 화면 좌표 예상 (scrollIntoView 가운데 맞춤은 scroll-padding-top 아래 영역 기준, 맨 위·끝에서는 멈춤)
      const dy = r.top + scrollY + r.height / 2, ih = innerHeight, sh = document.documentElement.scrollHeight;
      const st = Math.max(0, Math.min(dy - (P + (ih - P) / 2), sh - ih));
      return [Math.round(r.left + Math.min(r.width / 2, 40)), Math.round(dy - st)];
    };
    const scan = () => {
      const out = { t: document.title.slice(0, 40), v: document.visibilityState, w: innerWidth, dpr: +devicePixelRatio.toFixed(2), sih: 0, s: [], m: [] };
      out.sih = [...document.querySelectorAll('h1,h2,h3,h4,summary,button')].some((e) => SI_HEAD.test((e.innerText || '').trim())) ? 1 : 0;
      document.querySelectorAll('[data-sciretr]').forEach((e) => e.removeAttribute('data-sciretr'));   // 앞 실행의 번호가 남아 다른 요소를 가리키지 않게
      const cand = [];
      for (const a of document.querySelectorAll('a[href], button, a.accordion__control')) {
        const href = a.getAttribute('href') || '';
        if (/^https?:/i.test(href) && !href.startsWith(location.origin) && !CROSS_OK.test(href)) continue;
        const jump = a.tagName === 'A' && /^(#|javascript:)/i.test(href) && !a.classList.contains('accordion__control');
        const path = jump ? '' : href.split('?')[0].split('#')[0];
        const text = (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim();
        if (!text && !path) continue;
        if (NOISE.test(text) || SKIP.test(path) || SKIP_PATH.test(path) || INLINE_REF.test(text)) continue;
        const sipath = path.replace(/\/supplement[_-]?\d+(?=\/|$)/ig, '');   // 학회 초록집 호는 SI 가 아니다 (2026-09-27 Oxford M&M)
        let kind = '';
        if (SI_HREF.test(sipath) || SI_TEXT.test(text)) kind = 's';
        else if (MAIN_HREF.test(path) || MAIN_TEXT.test(text)) kind = 'm';
        if (!kind) continue;
        if (kind === 'm' && self && /\/pii\/|\/doi\//i.test(path) && !path.toLowerCase().includes(self)) continue;
        const r = a.getBoundingClientRect();
        const hidden = r.width < 4 || r.height < 4 || r.left >= innerWidth || r.right <= 0;
        // 보이는 링크 → 안 보이는 링크 → 목차·메뉴 순. 같은 주소가 여럿이면 앞의 것만 남는다(PNAS 화면 밖 옆 패널, IEEE 크기 0 복제본)
        cand.push({ a, kind, path, text, r, hidden, js: /^javascript:/i.test(href), jump, pri: jump ? 2 : hidden ? 1 : 0, i: cand.length });
      }
      cand.sort((x, y) => x.pri - y.pri || x.i - y.i);
      const seen = new Set();
      let n = 0;
      for (const c of cand) {
        const key = c.kind + (c.jump ? '#' + c.text : (c.path || c.text));
        if (seen.has(key)) continue;
        seen.add(key);
        if (out[c.kind].length >= (c.kind === 's' ? 5 : 4)) continue;
        n += 1;
        c.a.setAttribute('data-sciretr', String(n));
        const shown = c.jump ? (c.js ? 'js' : '#')
          : /\/article-supplement\//i.test(c.path) ? c.path.replace(/^.*\/article-supplement\/\d+\//i, '').slice(0, 36) : c.path.slice(-36);
        const item = [n, c.text.slice(0, 24), shown].concat(c.hidden ? ['접힘'] : pt(c.r));
        if (c.kind === 'm' && ONLINE.test(c.path)) item.push('online');
        out[c.kind].push(item);
      }
      return out;
    };
    let out = scan();
    while (!out.m.length && !out.s.length && Date.now() - t0 < 20000) {
      await new Promise((r) => setTimeout(r, 1000));   // 확인 간격 1초 (2026-09-27 사용자 지정)
      out = scan();
    }
    out.ms = Date.now() - t0;
    const hitAt = (el, x, y) => { const h = document.elementFromPoint(x, y); return !!h && (h === el || el.contains(h)); };
    window.sciretrFocus = (k, ex, ey) => {
      const el = document.querySelector('[data-sciretr="' + k + '"]');
      if (!el) return JSON.stringify({ ok: false });
      el.scrollIntoView({ block: 'center', behavior: 'instant' });
      const r = el.getBoundingClientRect();
      const x = Math.round(r.left + Math.min(r.width / 2, 40)), y = Math.round(r.top + r.height / 2);
      const hit = hitAt(el, x, y);   // 막을 덮기 전에 잰다
      let guard = 0;
      if (ex !== undefined && ey !== undefined && !hitAt(el, ex, ey)) {   // 예상 좌표에 이 요소가 없으면 다음 클릭 한 번을 막는다
        const d = document.createElement('div');
        d.style.cssText = 'position:fixed;inset:0;z-index:2147483647;background:transparent';
        const off = () => d.remove();
        d.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); off(); }, true);
        setTimeout(off, 8000);
        document.documentElement.appendChild(d);
        guard = 1;
      }
      return JSON.stringify({ ok: true, n: k, x, y, w: innerWidth, hit, guard, text: (el.innerText || '').trim().slice(0, 30) });
    };
    window.sciretrGo = (k) => {
      const el = document.querySelector('[data-sciretr="' + k + '"]');
      if (!el || !el.href) return JSON.stringify({ ok: false });
      location.href = el.href;
      return JSON.stringify({ ok: true, n: k });
    };
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ error: String(e).slice(0, 120) });
  }
})();
