// sci-retr 웹 경로 보조 스크립트 (2026-09-27 전 출판사 연습 반영). Claude in Chrome 의 javascript_tool 로 논문 페이지에서 실행한다. 클릭은 하지 않는다.
// 결과(JSON, 1,000자 안으로 짧게 — javascript_tool 출력이 약 1,000자에서 잘린다):
//   t 제목 40자, v visibilityState, w innerWidth, dpr devicePixelRatio, ms 실제로 기다린 시간
//   s: SI 후보, m: 본문 후보 — 항목은 [번호, 글자 24자, 경로 끝 36자, x, y(문서 좌표)] 또는 [번호, 글자, 경로, "접힘"](펼쳐야 보이는 링크)
//      m 항목 끝의 "online" 은 온라인 보기(epdf·reader)라 대개 누르지 않는다(Science 만 온라인 보기를 거친다)
//   경로가 빈 s 항목은 접힌 절의 제목(Wiley "Supporting Information" = a.accordion__control)이다. 눌러 펼친 뒤 다시 돌린다.
// 고정 대기 대신: 후보가 나타날 때까지 1초 간격으로 스스로 확인하고 나타나면 바로 돌려준다(최대 20초). 끝내 비면 t 로 확인 화면("Just a moment…")인지 본다.
// 거르는 것: 다른 사이트 링크(SI 파일 도메인 ars.els-cdn.com·silverchair-cdn.com 은 허용), 다른 논문의 PDF(주소에 이 논문 PII·DOI 가 없는 것),
//   본문 속 'Figure S1'·'Table S2' 참조 링크, 호·권 링크(/vol/…/suppl/), 사이트 자료(/pb-assets/), zip·스프레드시트·동영상·PowerPoint.
// 누르기 전: window.sciretrFocus(N) 으로 그 요소를 화면 가운데로 스크롤하고 화면 좌표를 받는다. 넓은 링크는 글자 쪽(왼쪽 40px)을 준다.
//   스크린샷 좌표계가 innerWidth 와 다르면 (스크린샷 폭 ÷ innerWidth) 를 곱한다. 긴 거리를 스크롤한 직후 화면이 하얗면 1~2초 뒤 다시 본다.
(async () => {
  try {
    const self = (() => {   // 이 논문의 식별자: 주소의 PII 나 DOI 끝부분
      const u = decodeURIComponent(location.pathname);
      const pii = u.match(/\/pii\/([A-Z0-9]+)/i);
      if (pii) return pii[1].toLowerCase();
      const doi = u.match(/10\.\d{4,9}\/[^/?#]+/);
      return doi ? doi[0].split('/').pop().toLowerCase() : '';
    })();
    const CROSS_OK = /ars\.els-cdn\.com|silverchair-cdn\.com/i;
    const SKIP = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|mp4|avi|mov|mp3|wav|cif|pptx?|ppt)(\?|$)/i;
    const SKIP_PATH = /\/vol\/\d+\/suppl\/|\/pb-assets\/|\/toc\/|\/loi\//i;
    const SI_HREF = /mmc\d|suppl|supplement|sifile|_si_|-sup-|_sm\b|\/data\b|supporting|suppdata|si\.pdf|-si\b|downloadSupplement/i;
    const SI_TEXT = /supp(orting|lementa)|\bSI\b|Supplementary|Download \w+ (file|document)|Multimedia component/i;
    const INLINE_REF = /^(fig(ure)?s?\.?|tables?|schemes?|eqs?\.?|movies?|S)\s*S?\d/i;
    const MAIN_HREF = /\/doi\/pdf\/|\/pdfft|\/content\/pdf\/|\/article-pdf\/|\/articlepdf\/|\/pdf(\/|\?|$)|\.pdf(\?|$)|epdf|\/reader\//i;
    const MAIN_TEXT = /^\s*(download pdf|view pdf|open pdf|pdf download|pdf|download)\s*$/i;
    const ONLINE = /epdf|\/reader\//i;
    const NOISE = /powerpoint|full issue|download \(\d+\)|download all|with cover|wechat/i;
    const pt = (r) => [Math.round(r.left + Math.min(r.width / 2, 40) + scrollX), Math.round(r.top + r.height / 2 + scrollY)];
    const scan = () => {
      const out = { t: document.title.slice(0, 40), v: document.visibilityState, w: innerWidth, dpr: +devicePixelRatio.toFixed(2), s: [], m: [] };
      const seen = new Set();
      let n = 0;
      for (const a of document.querySelectorAll('a[href], button, a.accordion__control')) {
        const href = a.getAttribute('href') || '';
        if (/^https?:/i.test(href) && !href.startsWith(location.origin) && !CROSS_OK.test(href)) continue;
        const path = href.split('?')[0].split('#')[0];
        const text = (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim();
        if (!text && !href) continue;
        if (NOISE.test(text) || SKIP.test(path) || SKIP_PATH.test(path) || INLINE_REF.test(text)) continue;
        let kind = '';
        if (SI_HREF.test(path) || SI_TEXT.test(text)) kind = 's';
        else if (MAIN_HREF.test(path) || MAIN_TEXT.test(text)) kind = 'm';
        if (!kind) continue;
        if (kind === 'm' && self && /\/pii\/|\/doi\//i.test(path) && !path.toLowerCase().includes(self)) continue;
        const key = kind + (path || text);
        if (seen.has(key)) continue;
        seen.add(key);
        const r = a.getBoundingClientRect();
        const hidden = r.width < 4 || r.height < 4;
        if (hidden && kind === 'm') continue;
        n += 1;
        a.setAttribute('data-sciretr', String(n));
        const item = [n, text.slice(0, 24), path.slice(-36)].concat(hidden ? ['접힘'] : pt(r));
        if (kind === 'm' && ONLINE.test(path)) item.push('online');
        out[kind].push(item);
      }
      out.s = out.s.slice(0, 5);
      out.m = out.m.slice(0, 4);
      return out;
    };
    const t0 = Date.now();
    let out = scan();
    while (!out.m.length && !out.s.length && Date.now() - t0 < 20000) {
      await new Promise((r) => setTimeout(r, 1000));   // 확인 간격 1초 (2026-09-27 사용자 지정)
      out = scan();
    }
    out.ms = Date.now() - t0;
    window.sciretrFocus = (k) => {
      const el = document.querySelector('[data-sciretr="' + k + '"]');
      if (!el) return JSON.stringify({ ok: false });
      el.scrollIntoView({ block: 'center', behavior: 'instant' });
      const r = el.getBoundingClientRect();
      return JSON.stringify({ ok: true, n: k, x: Math.round(r.left + Math.min(r.width / 2, 40)), y: Math.round(r.top + r.height / 2), w: innerWidth, text: (el.innerText || '').trim().slice(0, 30) });
    };
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ error: String(e).slice(0, 120) });
  }
})();
