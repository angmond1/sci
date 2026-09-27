// sci-retr: save the web body of a web-only article (no PDF, e.g. Science Expert Voices). Usage: web_download_playbook.md 2.5.
// Returns stats (chars, paras, refs, removed, heads). If heads has no related/recommended/news/metrics titles: window.sciretrSaveText('<paper_id>') -> <paper_id>.sciretr.html -> intake.
(() => {
  try {
    const JUNK = /related|recommend|similar|more-?from|you-?may|trending|most-?(read|viewed|cited|popular)|cited-?by|citing|metric|altmetric|advert|\bads?\b|promo|newsletter|subscri|sign-?up|social|share|cookie|breadcrumb|toolbar|sidebar|permission|reprint|viewer|lightbox|modal|popup|banner|jump-?to|table-?of-?contents|\btoc\b|citation-?tool|export|login|access-?widget|eletter/i;
    const JUNK_HEAD = /^(related|recommended|you (may|might) (also )?(like|be interested)|more (from|like this)|latest (news|articles)|trending|most (read|viewed|cited|popular)|cited by|eletters|metrics|see also|advertisement|stay connected|newsletter|sign up|share|similar articles)/i;
    const PANEL_HEAD = /^(information( (&|and) authors)?|authors?|affiliations|metrics( (&|and) citations)?|citations|view options|figures( (&|and) media)?|tables|media|share)$/i;   // side-panel titles (exact)
    const COLLATERAL = /collateral/i;   // Atypon side panels: core-collateral-info, -metrics, -fulltext-options, -references, -media ...
    const REFS = '#bibliography, #references, section.references, section[id*="ref" i], div.references, ol.references, [role="doc-bibliography"]';
    const PARA = 'p, [role="paragraph"]';   // Science body paragraphs are div[role=paragraph]
    const ptext = (el) => [...el.querySelectorAll(PARA)].reduce((a, p) => a + (p.textContent || '').length, 0);
    const inPanel = (el) => !!el.closest('[id*="collateral" i], [class*="collateral" i]');
    const cleanClone = (root) => {
      const c = root.cloneNode(true);
      c.querySelectorAll('script,style,noscript,svg,button,form,iframe,nav,aside,footer,header,input,select,textarea,img,video,audio,canvas,picture,source,link,meta').forEach((e) => e.remove());
      const bodyP = ptext(c) || 1;
      const small = (e) => ptext(e) < bodyP * 0.5;   // never drop a box holding most of the body paragraphs
      let removed = 0;
      for (const e of [...c.querySelectorAll('*')]) {
        if (!c.contains(e)) continue;
        const ident = [e.id, e.getAttribute('class'), e.getAttribute('aria-label'), e.getAttribute('data-type')].join(' ');
        const hiddenUi = e.getAttribute('aria-hidden') === 'true' || /pop-?up|tooltip|popover/i.test(ident);   // hover popups (Science references-pop-up)
        if ((COLLATERAL.test(ident) || hiddenUi) && small(e)) { e.remove(); removed += 1; continue; }
        const head = ((e.querySelector('h1,h2,h3,h4') || {}).textContent || '').trim();
        if (/ref|bibliograph/i.test(ident) || /^(references|bibliography|notes and references)/i.test(head)) continue;   // keep references
        const junkBox = JUNK.test(ident) && (e.textContent || '').length < 1500;
        const junkSec = /^(section|div)$/i.test(e.tagName) && head.length < 60 && (JUNK_HEAD.test(head) || PANEL_HEAD.test(head)) && small(e);
        if (junkBox || junkSec) { e.remove(); removed += 1; }
      }
      for (const d of [...c.querySelectorAll('[role="paragraph"]')]) {   // div[role=paragraph] -> <p> (keeps paragraphs after attributes are stripped)
        if (d.querySelector('div,figure,table,ul,ol,section')) continue;
        const p = document.createElement('p');
        while (d.firstChild) p.appendChild(d.firstChild);
        d.replaceWith(p);
      }
      for (const e of c.querySelectorAll('*')) for (const a of [...e.attributes]) e.removeAttribute(a.name);   // strip attributes (the extractor must not drop body by class name)
      return { c, removed };
    };
    const articleHtml = () => {
      // body box: innermost article/main whose paragraph text is >= 90% of the best; body-only boxes (#bodymatter) only when there is no article/main
      const pick = (sel) => {
        const list = [...document.querySelectorAll(sel)];
        const best = Math.max(0, ...list.map(ptext));
        const ok = list.filter((e) => best > 0 && ptext(e) >= best * 0.9);
        return ok.find((e) => !ok.some((o) => o !== e && e.contains(o)));
      };
      const root = pick('article, main, [role="main"]') || pick('[property="articleBody"], #bodymatter, .article__body, .c-article-body') || document.body;
      const { c, removed } = cleanClone(root);
      const refs = [...document.querySelectorAll(REFS)].find((e) => !inPanel(e));
      let extra = 0;
      if (refs && !root.contains(refs)) { const r = cleanClone(refs); c.appendChild(r.c); extra = r.removed; }   // references outside the body box
      const meta = (n) => ((document.querySelector('meta[name="' + n + '"]') || {}).content || '');
      const esc = (s) => String(s).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
      const title = meta('citation_title') || meta('dc.Title') || (document.querySelector('meta[property="og:title"]') || {}).content || document.title.replace(/\s+\|\s+[^|]+$/, '');
      const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();
      const titled = [...c.querySelectorAll('h1')].some((h) => norm(h.textContent) === norm(title));
      const html = '<!doctype html><html><head><meta charset="utf-8"><title>' + esc(title) + '</title><meta name="citation_doi" content="' + esc(meta('citation_doi') || meta('dc.Identifier')) +
        '"></head><body><article>' + (titled ? '' : '<h1>' + esc(title) + '</h1>') + c.innerHTML + '</article></body></html>';
      const heads = [...c.querySelectorAll('h2,h3')].map((h) => (h.textContent || '').trim().slice(0, 24)).filter(Boolean).slice(0, 14);
      const nref = refs ? refs.querySelectorAll('li, [role="doc-biblioentry"], [role="listitem"]').length : 0;
      return { html, chars: (c.textContent || '').replace(/\s+/g, ' ').trim().length, paras: c.querySelectorAll('p').length, refs: nref, removed: removed + extra, heads };
    };
    window.sciretrArticleStats = () => { const r = articleHtml(); return JSON.stringify({ chars: r.chars, paras: r.paras, refs: r.refs, removed: r.removed, heads: r.heads }); };
    window.sciretrSaveText = (pid) => {
      if (!pid || /[\\/:*?"<>|]/.test(pid)) return JSON.stringify({ ok: false, why: 'paper_id 를 준다' });
      const r = articleHtml();
      if (r.chars < 500) return JSON.stringify({ ok: false, why: '본문이 짧다 — 구독 밖이거나 아직 안 읽힘', chars: r.chars });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([r.html], { type: 'text/html' }));
      a.download = pid + '.sciretr.html';
      document.documentElement.appendChild(a); a.click(); a.remove();
      return JSON.stringify({ ok: true, chars: r.chars, paras: r.paras, refs: r.refs, removed: r.removed });
    };
    return window.sciretrArticleStats();
  } catch (e) {
    return JSON.stringify({ error: String(e).slice(0, 120) });
  }
})();
