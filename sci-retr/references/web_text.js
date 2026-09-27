// sci-retr: PDF 가 없는 웹 전용 글(Science Expert Voices 등)의 웹 본문 저장. 사용법은 web_download_playbook.md 2.5 (2026-09-27 사용자 지시).
// 넣으면 통계(chars·paras·refs·removed·heads)를 돌려준다. heads 에 추천·관련 글이 없으면 window.sciretrSaveText('<paper_id>') → <paper_id>.sciretr.html → intake.
(() => {
  try {
    const JUNK = /related|recommend|similar|more-?from|you-?may|trending|most-?(read|viewed|cited|popular)|cited-?by|citing|metric|altmetric|advert|\bads?\b|promo|newsletter|subscri|sign-?up|social|share|cookie|breadcrumb|toolbar|sidebar|permission|reprint|viewer|lightbox|modal|popup|banner|jump-?to|table-?of-?contents|\btoc\b|citation-?tool|export|login|access-?widget|eletter/i;
    const JUNK_HEAD = /^(related|recommended|you (may|might) (also )?(like|be interested)|more (from|like this)|latest (news|articles)|trending|most (read|viewed|cited|popular)|cited by|eletters|metrics|see also|advertisement|stay connected|newsletter|sign up|share|similar articles)/i;
    const REFS = '#bibliography, #references, section.references, section[id*="ref" i], div.references, ol.references, [role="doc-bibliography"]';
    const ptext = (el) => [...el.querySelectorAll('p')].reduce((a, p) => a + (p.textContent || '').length, 0);
    const cleanClone = (root) => {
      const c = root.cloneNode(true);
      c.querySelectorAll('script,style,noscript,svg,button,form,iframe,nav,aside,footer,header,input,select,textarea,img,video,audio,canvas,picture,source,link,meta').forEach((e) => e.remove());
      let removed = 0;
      for (const e of [...c.querySelectorAll('*')]) {
        if (!c.contains(e)) continue;
        const ident = [e.id, e.getAttribute('class'), e.getAttribute('aria-label'), e.getAttribute('data-type')].join(' ');
        const head = ((e.querySelector('h1,h2,h3,h4') || {}).textContent || '').trim();
        if (/ref|bibliograph/i.test(ident) || /^(references|bibliography|notes and references)/i.test(head)) continue;   // 참고문헌은 남긴다
        const junkBox = JUNK.test(ident) && (e.textContent || '').length < 1500;   // 본문 전체를 감싼 큰 상자는 이름이 걸려도 지우지 않는다
        const junkSec = /^(section|div)$/i.test(e.tagName) && head.length < 60 && JUNK_HEAD.test(head);
        if (junkBox || junkSec) { e.remove(); removed += 1; }
      }
      for (const e of c.querySelectorAll('*')) for (const a of [...e.attributes]) e.removeAttribute(a.name);   // 속성은 모두 뺀다 (정리기가 이름으로 본문을 지우지 않게)
      return { c, removed };
    };
    const articleHtml = () => {
      // 본문 상자: 문단 글이 가장 많은 상자와 거의 같은(90% 이상) 것 중 가장 안쪽 (main 보다 article, 추천 카드 article 은 글이 적어 빠짐).
      // 본문만 든 상자(#bodymatter 등)는 초록·참고문헌이 밖에 있어 article·main 이 없을 때만 쓴다.
      const pick = (sel) => {
        const list = [...document.querySelectorAll(sel)];
        const best = Math.max(0, ...list.map(ptext));
        const ok = list.filter((e) => best > 0 && ptext(e) >= best * 0.9);
        return ok.find((e) => !ok.some((o) => o !== e && e.contains(o)));
      };
      const root = pick('article, main, [role="main"]') || pick('[property="articleBody"], #bodymatter, .article__body, .c-article-body') || document.body;
      const { c, removed } = cleanClone(root);
      const refs = document.querySelector(REFS);
      let extra = 0;
      if (refs && !root.contains(refs)) { const r = cleanClone(refs); c.appendChild(r.c); extra = r.removed; }   // 참고문헌이 본문 상자 밖에 있을 때
      const meta = (n) => ((document.querySelector('meta[name="' + n + '"]') || {}).content || '');
      const esc = (s) => String(s).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
      const title = meta('citation_title') || document.title;
      const norm = (s) => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();
      const titled = [...c.querySelectorAll('h1')].some((h) => norm(h.textContent) === norm(title));   // 본문 상자에 제목이 이미 있으면 다시 붙이지 않는다
      const html = '<!doctype html><html><head><meta charset="utf-8"><title>' + esc(title) + '</title><meta name="citation_doi" content="' + esc(meta('citation_doi') || meta('dc.Identifier')) +
        '"></head><body><article>' + (titled ? '' : '<h1>' + esc(title) + '</h1>') + c.innerHTML + '</article></body></html>';
      const heads = [...c.querySelectorAll('h2,h3')].map((h) => (h.textContent || '').trim().slice(0, 24)).filter(Boolean).slice(0, 14);   // 확인용: 남은 소제목
      const nref = refs ? refs.querySelectorAll('li, [role="doc-biblioentry"], [role="listitem"]').length : 0;
      return { html, chars: (c.textContent || '').replace(/\s+/g, ' ').trim().length, paras: c.querySelectorAll('p').length, refs: nref, removed: removed + extra, heads };
    };
    window.sciretrArticleStats = () => { const r = articleHtml(); return JSON.stringify({ chars: r.chars, paras: r.paras, refs: r.refs, removed: r.removed, heads: r.heads }); };   // 내려받기 전 확인용: 남은 소제목에 추천·관련 글이 없는지 본다
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
