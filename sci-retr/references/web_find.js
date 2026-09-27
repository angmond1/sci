// sci-retr web path: PDF/SI link candidates with numbers and screen points (no clicks). Paste as-is, keep the leading await. Docs: web_download_playbook.md 2.4
await (async () => {
  try {
    const t0 = Date.now();
    const waitEvt = (name, cap) => new Promise((r) => { addEventListener(name, r, { once: true }); setTimeout(r, Math.max(0, cap)); });
    if (document.readyState === 'loading') await waitEvt('DOMContentLoaded', 20000);
    if (document.readyState !== 'complete') await waitEvt('load', Math.min(3000, 20000 - (Date.now() - t0)));
    const self = (() => {   // this paper's PII or DOI suffix
      const u = decodeURIComponent(location.pathname);
      const pii = u.match(/\/pii\/([A-Z0-9]+)/i);
      if (pii) return pii[1].toLowerCase();
      const doi = u.match(/10\.\d{4,9}\/[^/?#]+/);
      return doi ? doi[0].split('/').pop().toLowerCase() : '';
    })();
    const CROSS_OK = /ars\.els-cdn\.com|silverchair-cdn\.com|cfn-live-content-bucket-iop-org\.s3|figshare\.com|doi\.org\/10\.(6084|60893)\//i;   // + figshare SI
    const SKIP = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|txt|mp4|mpe?g|m4v|webm|wmv|avi|mov|mp3|wav|cif|pptx?|ppt)(\?|$)/i;
    const SKIP_TEXT = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|txt|mp4|mpe?g|m4v|webm|wmv|avi|mov|mp3|wav|cif|pptx?|ppt)\b|^(zip|excel|video|audio)-document/i;
    const SKIP_PATH = /\/vol\/\d+\/suppl\/|\/pb-assets\/|\/toc\/|\/loi\/|\/lookup\/doi\/|\/issue\//i;
    const SKIP_FMT = /\/article-supplement\/\d+\/(?!pdf\/|docx?\/)[a-z0-9]+\//i;   // AIP zip/xlsx SI pages
    const SI_HREF = /mmc\d|suppl(?!ier)|sifile|_si_|-sup-|_sm\b|\/data(?=\/|$)|supporting|suppdata|si\.pdf|-si\b|downloadSupplement|\.sapp\b|supp\d|\/s\d{1,3}$|figshare\.com\/(articles|collections|ndownloader)|10\.(6084|60893)\//i;   // MDPI /s1
    const SI_TEXT = /supp(orting|lementa)|Supplementary|Download \w+ (file|document)|Multimedia component/i;
    const SI_ABBR = /\bSI\b/;   // not silicon 'Si'
    const SI_HEAD = /^(appendix [a-z0-9]+\.? )?(supplementa|supporting)/i;
    const REF_HEAD = /^(\d+\.?\s*)?(references?( and notes)?|notes and references|bibliography|literature cited)$/i;
    const heads = () => [...document.querySelectorAll('h1,h2,h3,h4,summary,button')];
    const INLINE_REF = /^(fig(ure)?s?\.?|tables?|schemes?|eqs?\.?|movies?|S)\s*S?\d/i;
    const MAIN_HREF = /\/doi\/pdf\/|\/pdfft|\/content\/pdf\/|\/article-pdf\/|\/articlepdf\/|\/pdf(\/|\?|$)|\.pdf(\?|$)|epdf|\/reader\//i;
    const MAIN_TEXT = /^\s*(download pdf|view pdf|open pdf|pdf download|pdf|download)\s*$/i;
    const ONLINE = /epdf|\/reader\//i;
    const NOISE = /powerpoint|full issue|download \(\d+\)|download all|with cover|wechat|pdf and supp/i;
    const P = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;   // sticky header
    const box = (el) => { const rs = [...el.getClientRects()].filter((r) => r.width >= 4 && r.height >= 4); return rs.length ? rs[0] : el.getBoundingClientRect(); };   // first non-empty line
    const at = (b) => [Math.round(b.left + Math.min(b.width / 2, 40)), Math.round(b.top + b.height / 2)];
    const hitAt = (el, x, y) => { const h = document.elementFromPoint(x, y); return !!h && (h === el || el.contains(h)); };
    const shownNow = (el, b) => b.width > 0 && b.top >= 0 && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth && hitAt(el, ...at(b));
    const pt = (el) => {   // point after sciretrFocus
      const b = box(el);
      if (shownNow(el, b)) return at(b);
      const r = el.getBoundingClientRect(), ih = innerHeight, sh = document.documentElement.scrollHeight;
      const st = Math.max(0, Math.min(r.top + scrollY + r.height / 2 - (P + (ih - P) / 2), sh - ih));   // centered, clamped
      return [Math.round(b.left + Math.min(b.width / 2, 40)), Math.round(b.top + scrollY + b.height / 2 - st)];
    };
    const short = (s) => (s.length > 24 ? s.slice(0, 11) + '..' + s.slice(-12) : s);
    const scan = () => {
      const out = { t: document.title.slice(0, 40), v: document.visibilityState, w: innerWidth, dpr: +devicePixelRatio.toFixed(2), sih: 0, s: [], m: [] };
      if (!outerWidth) out.min = 1;
      out.sih = heads().some((e) => SI_HEAD.test((e.innerText || '').trim())) ? 1 : 0;
      document.querySelectorAll('[data-sciretr]').forEach((e) => e.removeAttribute('data-sciretr'));
      const cand = [];
      for (const a of document.querySelectorAll('a[href], button, a.accordion__control')) {
        const href = (a.getAttribute('href') || '').trim();
        if (/^https?:/i.test(href) && !href.startsWith(location.origin) && !CROSS_OK.test(href)) continue;
        const jump = a.tagName === 'A' && /^(#|javascript:)/i.test(href) && !a.classList.contains('accordion__control');
        const path = jump ? '' : href.split('?')[0].split('#')[0];
        const text = (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim();
        if (!text && !path) continue;
        if (NOISE.test(text) || SKIP_PATH.test(path) || INLINE_REF.test(text)) continue;
        if (SKIP.test(path) || SKIP_TEXT.test(text) || SKIP_FMT.test(path)) { if (SI_HREF.test(path) || SI_TEXT.test(text)) out.sk = (out.sk || 0) + 1; continue; }   // sk: skipped-format SI
        const sipath = path.replace(/\/supplement[_-]?\d+(?=\/|$)/ig, '');   // abstract-issue supplements
        let kind = '';
        if (SI_HREF.test(sipath) || SI_TEXT.test(text) || SI_ABBR.test(text)) kind = 's';
        else if (MAIN_HREF.test(path) || MAIN_TEXT.test(text)) kind = 'm';
        if (!kind) continue;
        if (self && /\/pii\/|\/doi\//i.test(path) && !path.toLowerCase().includes(self)) continue;   // other papers
        const r = a.getBoundingClientRect();
        const hidden = r.width < 4 || r.height < 4 || r.left >= innerWidth || r.right <= 0;
        cand.push({ a, kind, path, text, hidden, q: href.includes('?'), js: /^javascript:/i.test(href), jump, pri: jump ? 2 : hidden ? 1 : 0, i: cand.length });
      }
      for (const f of document.querySelectorAll('iframe[src*="figshare"]')) {   // figshare widget
        const r = f.getBoundingClientRect();
        const hidden = r.width < 4 || r.height < 4;
        cand.push({ a: f, kind: 's', path: f.src.split('?')[0], text: 'figshare', hidden, q: false, js: false, jump: false, frame: 1, pri: hidden ? 1 : 0, i: cand.length });
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
        const item = [n, short(c.text), where].concat(c.hidden ? ['hidden'] : pt(c.a));
        if (c.kind === 'm' && ONLINE.test(c.path)) item.push('online');
        if (c.frame) item.push('frame');
        out[c.kind].push(item);
      }
      return out;
    };
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));   // 1 s polls (user setting)
    const refIn = () => heads().some((e) => REF_HEAD.test((e.innerText || '').trim()));
    const settle = async (tFind, tEnd) => {   // then late SI lists
      let out = scan();
      while (!out.m.length && !out.s.length && Date.now() < tFind) { await sleep(1000); out = scan(); }
      const t1 = Date.now();   // body not in yet: <= 6 s
      while (out.m.length && !out.s.length && !out.sih && !out.sk && !refIn() && Date.now() - t1 < 6000 && Date.now() < tEnd) { await sleep(1000); out = scan(); }
      if (out.sih && !out.s.length && !out.sk) {   // SI heading, no link: scroll there, <= 6 s
        const y0 = scrollY;
        const h = heads().find((e) => SI_HEAD.test((e.innerText || '').trim()));
        if (h) h.scrollIntoView({ block: 'center', behavior: 'instant' });
        const t2 = Date.now();
        while (!out.s.length && Date.now() - t2 < 6000 && Date.now() < tEnd) { await sleep(1000); out = scan(); }
        scrollTo({ top: y0, behavior: 'instant' });
        out = scan();
        if (!out.s.length) out.sx = 1;   // not 'no SI'
      }
      return out;
    };
    const out = await settle(t0 + 20000, t0 + 26000);
    out.ms = Date.now() - t0;
    window.sciretrScan = async () => { const t = Date.now(); const o = await settle(t + 3000, t + 9000); o.ms = Date.now() - t; return JSON.stringify(o); };   // cheap re-check
    window.sciretrFocus = async (k, ex, ey) => {
      if (!outerWidth) return JSON.stringify({ ok: false, why: 'window minimized: ask to bring it to front' });
      const el = document.querySelector('[data-sciretr="' + k + '"]');
      if (!el) return JSON.stringify({ ok: false, why: 'no such number: rerun web_find' });
      let b = box(el);
      if (!shownNow(el, b)) { el.scrollIntoView({ block: 'center', behavior: 'instant' }); b = box(el); }
      for (let i = 0; i < 3; i++) {   // settled = same place 1 s later (max 3 s)
        await new Promise((r) => setTimeout(r, 1000));
        const nb = box(el);
        if (Math.abs(nb.top - b.top) < 2 && Math.abs(nb.left - b.left) < 2) { b = nb; break; }
        if (!shownNow(el, nb)) el.scrollIntoView({ block: 'center', behavior: 'instant' });
        b = box(el);
      }
      const [x, y] = at(b);
      const hit = hitAt(el, x, y);
      let guard = 0;
      if (ex !== undefined && ey !== undefined && !hitAt(el, ex, ey)) {   // not at the predicted point: eat the next click
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
      const u = el && (el.href || el.src);   // iframe: widget page
      if (!u) return JSON.stringify({ ok: false });
      location.href = u;
      return JSON.stringify({ ok: true, n: k });
    };
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ error: String(e).slice(0, 120) });
  }
})();
