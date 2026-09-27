// sci-retr web path: returns body-PDF/SI link candidates with numbers and screen coordinates (no clicks). Paste as-is into javascript_tool (keep the leading await).
// Result format and sciretrFocus/sciretrGo: web_download_playbook.md 2.4. Re-sent for every paper, so comments stay short and in English (2026-09-27).
await (async () => {
  try {
    const t0 = Date.now();
    const waitEvt = (name, cap) => new Promise((r) => { addEventListener(name, r, { once: true }); setTimeout(r, Math.max(0, cap)); });
    if (document.readyState === 'loading') await waitEvt('DOMContentLoaded', 20000);
    if (document.readyState !== 'complete') await waitEvt('load', Math.min(3000, 20000 - (Date.now() - t0)));
    const self = (() => {   // this paper: PII or DOI suffix from the URL
      const u = decodeURIComponent(location.pathname);
      const pii = u.match(/\/pii\/([A-Z0-9]+)/i);
      if (pii) return pii[1].toLowerCase();
      const doi = u.match(/10\.\d{4,9}\/[^/?#]+/);
      return doi ? doi[0].split('/').pop().toLowerCase() : '';
    })();
    const CROSS_OK = /ars\.els-cdn\.com|silverchair-cdn\.com|cfn-live-content-bucket-iop-org\.s3/i;
    const SKIP = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|txt|mp4|mpe?g|m4v|webm|wmv|avi|mov|mp3|wav|cif|pptx?|ppt)(\?|$)/i;   // PNAS .mpg video, .txt data
    const SKIP_TEXT = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|txt|mp4|mpe?g|m4v|webm|wmv|avi|mov|mp3|wav|cif|pptx?|ppt)\b|^(zip|excel|video|audio)-document/i;
    const SKIP_PATH = /\/vol\/\d+\/suppl\/|\/pb-assets\/|\/toc\/|\/loi\/|\/lookup\/doi\/|\/issue\/|\/article-supplement\/\d+\/(?!pdf\/|docx?\/)[a-z0-9]+\//i;
    const SI_HREF = /mmc\d|suppl(?!ier)|sifile|_si_|-sup-|_sm\b|\/data(?=\/|$)|supporting|suppdata|si\.pdf|-si\b|downloadSupplement|\.sapp\b|supp\d|\/s\d{1,3}$/i;   // MDPI /s1 (not long Elsevier PII paths)
    const SI_TEXT = /supp(orting|lementa)|Supplementary|Download \w+ (file|document)|Multimedia component/i;
    const SI_ABBR = /\bSI\b/;   // uppercase only (not silicon 'Si')
    const SI_HEAD = /^(appendix [a-z0-9]+\.? )?(supplementa|supporting)/i;
    const INLINE_REF = /^(fig(ure)?s?\.?|tables?|schemes?|eqs?\.?|movies?|S)\s*S?\d/i;
    const MAIN_HREF = /\/doi\/pdf\/|\/pdfft|\/content\/pdf\/|\/article-pdf\/|\/articlepdf\/|\/pdf(\/|\?|$)|\.pdf(\?|$)|epdf|\/reader\//i;
    const MAIN_TEXT = /^\s*(download pdf|view pdf|open pdf|pdf download|pdf|download)\s*$/i;
    const ONLINE = /epdf|\/reader\//i;
    const NOISE = /powerpoint|full issue|download \(\d+\)|download all|with cover|wechat|pdf and supp/i;
    const P = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;   // sticky header offset (ChemRxiv 108px)
    const box = (el) => { const rs = [...el.getClientRects()].filter((r) => r.width >= 4 && r.height >= 4); return rs.length ? rs[0] : el.getBoundingClientRect(); };   // first line of a wrapped link; skip empty 0-width lines (APS image link)
    const at = (b) => [Math.round(b.left + Math.min(b.width / 2, 40)), Math.round(b.top + b.height / 2)];
    const hitAt = (el, x, y) => { const h = document.elementFromPoint(x, y); return !!h && (h === el || el.contains(h)); };
    // on screen now and clickable there (false if covered by a sticky bar)
    const shownNow = (el, b) => b.width > 0 && b.top >= 0 && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth && hitAt(el, ...at(b));
    const pt = (el) => {   // predicted screen point after sciretrFocus
      const b = box(el);
      if (shownNow(el, b)) return at(b);   // already visible: no scroll (sticky sidebars)
      const r = el.getBoundingClientRect(), ih = innerHeight, sh = document.documentElement.scrollHeight;
      const st = Math.max(0, Math.min(r.top + scrollY + r.height / 2 - (P + (ih - P) / 2), sh - ih));   // scrollIntoView center, clamped at top/bottom
      return [Math.round(b.left + Math.min(b.width / 2, 40)), Math.round(b.top + scrollY + b.height / 2 - st)];
    };
    const short = (s) => (s.length > 24 ? s.slice(0, 11) + '…' + s.slice(-12) : s);
    const scan = () => {
      const out = { t: document.title.slice(0, 40), v: document.visibilityState, w: innerWidth, dpr: +devicePixelRatio.toFixed(2), sih: 0, s: [], m: [] };
      if (!outerWidth) out.min = 1;
      out.sih = [...document.querySelectorAll('h1,h2,h3,h4,summary,button')].some((e) => SI_HEAD.test((e.innerText || '').trim())) ? 1 : 0;
      document.querySelectorAll('[data-sciretr]').forEach((e) => e.removeAttribute('data-sciretr'));   // clear numbers from a previous run
      const cand = [];
      for (const a of document.querySelectorAll('a[href], button, a.accordion__control')) {
        const href = (a.getAttribute('href') || '').trim();   // Thieme hrefs have surrounding newlines
        if (/^https?:/i.test(href) && !href.startsWith(location.origin) && !CROSS_OK.test(href)) continue;
        const jump = a.tagName === 'A' && /^(#|javascript:)/i.test(href) && !a.classList.contains('accordion__control');
        const path = jump ? '' : href.split('?')[0].split('#')[0];
        const text = (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim();
        if (!text && !path) continue;
        if (NOISE.test(text) || SKIP.test(path) || SKIP_TEXT.test(text) || SKIP_PATH.test(path) || INLINE_REF.test(text)) continue;
        const sipath = path.replace(/\/supplement[_-]?\d+(?=\/|$)/ig, '');   // conference-abstract supplement issues are not SI
        let kind = '';
        if (SI_HREF.test(sipath) || SI_TEXT.test(text) || SI_ABBR.test(text)) kind = 's';
        else if (MAIN_HREF.test(path) || MAIN_TEXT.test(text)) kind = 'm';
        if (!kind) continue;
        if (self && /\/pii\/|\/doi\//i.test(path) && !path.toLowerCase().includes(self)) continue;   // links to other papers
        const r = a.getBoundingClientRect();
        const hidden = r.width < 4 || r.height < 4 || r.left >= innerWidth || r.right <= 0;
        // order: visible, hidden, toc/menu; one per address (query-addressed files also keyed by text)
        cand.push({ a, kind, path, text, hidden, q: href.includes('?'), js: /^javascript:/i.test(href), jump, pri: jump ? 2 : hidden ? 1 : 0, i: cand.length });
      }
      cand.sort((x, y) => x.pri - y.pri || x.i - y.i);
      const seen = new Set();
      let n = 0;
      for (const c of cand) {
        const key = c.kind + (c.jump ? '#' + c.text : (c.path || c.text) + (c.q ? '|' + c.text : ''));
        if (seen.has(key)) continue;
        seen.add(key);
        if (out[c.kind].length >= (c.kind === 's' ? 5 : 4)) continue;
        n += 1;
        c.a.setAttribute('data-sciretr', String(n));
        const where = c.jump ? (c.js ? 'js' : '#')
          : /\/article-supplement\//i.test(c.path) ? c.path.replace(/^.*\/article-supplement\/\d+\//i, '').slice(0, 36) : c.path.slice(-36);
        const item = [n, short(c.text), where].concat(c.hidden ? ['접힘'] : pt(c.a));
        if (c.kind === 'm' && ONLINE.test(c.path)) item.push('online');
        out[c.kind].push(item);
      }
      return out;
    };
    let out = scan();
    while (!out.m.length && !out.s.length && Date.now() - t0 < 20000) {
      await new Promise((r) => setTimeout(r, 1000));   // 1 s interval (user setting)
      out = scan();
    }
    out.ms = Date.now() - t0;
    window.sciretrFocus = async (k, ex, ey) => {
      if (!outerWidth) return JSON.stringify({ ok: false, why: '창 최소화 — 클릭이 닿지 않는다. 창을 앞으로 가져와 달라고 한다' });
      const el = document.querySelector('[data-sciretr="' + k + '"]');
      if (!el) return JSON.stringify({ ok: false, why: '번호 없음 — web_find 를 다시 돌린다' });
      let b = box(el);
      if (!shownNow(el, b)) { el.scrollIntoView({ block: 'center', behavior: 'instant' }); b = box(el); }
      for (let i = 0; i < 3; i++) {   // stable for 1 s = settled (checks every 1 s, max 3 s)
        await new Promise((r) => setTimeout(r, 1000));
        const nb = box(el);
        if (Math.abs(nb.top - b.top) < 2 && Math.abs(nb.left - b.left) < 2) { b = nb; break; }
        if (!shownNow(el, nb)) el.scrollIntoView({ block: 'center', behavior: 'instant' });
        b = box(el);
      }
      const [x, y] = at(b);
      const hit = hitAt(el, x, y);   // measure before adding the guard
      let guard = 0;
      if (ex !== undefined && ey !== undefined && !hitAt(el, ex, ey)) {   // element not at the predicted point: swallow the next click once
        const d = document.createElement('div');
        d.style.cssText = 'position:fixed;inset:0;z-index:2147483647;background:transparent';
        const off = () => d.remove();
        d.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); off(); }, true);
        setTimeout(off, 8000);
        document.documentElement.appendChild(d);
        guard = 1;
      }
      return JSON.stringify({ ok: true, n: k, x, y, w: innerWidth, hit, guard, text: short((el.innerText || '').trim()) });
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
