// sci-retr 웹 경로 보조 스크립트 (2026-09-27, RSC·ACS·Wiley 논문 페이지에서 확인). Claude in Chrome 의 javascript_tool 로 논문 페이지에서 실행한다.
// 하는 일: 본문 PDF 링크와 SI 링크 후보를 찾아 번호(data-sciretr)를 붙이고 글자·경로·종류·문서 좌표를 돌려준다. 클릭은 하지 않는다.
//   - main 의 online:true 는 온라인 보기(epdf·reader)라 대개 누르지 않는다(Science 만 온라인 보기를 거친다). 저장되는 링크는 /doi/pdf/, article-pdf, pdfft, content/pdf 류.
//   - si 의 path 가 빈 항목은 접힌 절의 제목(Wiley "Supporting Information" 등)이다. 그것을 눌러 펼친 뒤 이 스크립트를 다시 돌린다.
//   - 다른 사이트로 가는 링크(Google Scholar 등)는 뺀다. zip·스프레드시트·동영상·PowerPoint 링크도 뺀다.
// 누르기 전: window.sciretrFocus(N) 으로 그 요소를 화면 가운데로 스크롤하고 화면 좌표(cx, cy)와 innerWidth 를 받는다. 스크린샷 좌표계가 innerWidth 와 다르면 비율을 곱한다.
// 값에 주소 전체(쿼리)는 넣지 않는다. 결과가 비면 요령 문서 3절대로 직접 찾는다. 페이지가 아직 뜨는 중이면 몇 초 뒤 다시 돌린다.
(() => {
  try {
    const SKIP = /\.(zip|rar|7z|gz|tgz|xlsx?|xlsm|csv|mp4|avi|mov|mp3|wav|cif|pptx?|ppt)(\?|$)/i;
    const SI_HREF = /mmc\d|suppl|supplement|sifile|_si_|-sup-|_sm\b|\/data\b|supporting|suppdata|si\.pdf|-si\b/i;
    const SI_TEXT = /supp(orting|lementa)|\bSI\b|Supplementary|Download \w+ (file|document)|Multimedia component/i;
    const MAIN_HREF = /\/doi\/pdf\/|\/pdfft|\/content\/pdf\/|\/article-pdf\/|\/articlepdf\/|\/pdf(\/|\?|$)|\.pdf(\?|$)|epdf|\/reader\//i;
    const MAIN_TEXT = /^\s*(download pdf|view pdf|open pdf|pdf download|pdf|download)\s*$/i;
    const ONLINE = /epdf|\/reader\//i;
    const NOISE = /powerpoint|figure|full issue|download \(\d+\)|download all|with cover/i;
    const out = { vis: document.visibilityState, w: innerWidth, h: innerHeight, si: [], main: [] };
    let n = 0;
    for (const a of document.querySelectorAll('a[href], button')) {
      const href = a.getAttribute('href') || '';
      if (/^https?:/i.test(href) && !href.startsWith(location.origin)) continue;
      const path = href.split('?')[0].split('#')[0].slice(0, 120);
      const text = (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60);
      if (!text && !href) continue;
      if (NOISE.test(text) || SKIP.test(path)) continue;
      const r = a.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      let kind = '';
      if (SI_HREF.test(path) || SI_TEXT.test(text)) kind = 'si';
      else if (MAIN_HREF.test(path) || MAIN_TEXT.test(text)) kind = 'main';
      if (!kind) continue;
      n += 1;
      a.setAttribute('data-sciretr', String(n));
      const item = { n, text, path, x: Math.round(r.left + r.width / 2 + scrollX), y: Math.round(r.top + r.height / 2 + scrollY) };
      if (kind === 'main' && ONLINE.test(path)) item.online = true;
      out[kind].push(item);
    }
    out.si = out.si.slice(0, 12); out.main = out.main.slice(0, 8);
    window.sciretrFocus = (k) => {
      const el = document.querySelector('[data-sciretr="' + k + '"]');
      if (!el) return JSON.stringify({ ok: false });
      el.scrollIntoView({ block: 'center', behavior: 'instant' });
      const r = el.getBoundingClientRect();
      return JSON.stringify({ ok: true, n: k, cx: Math.round(r.left + r.width / 2), cy: Math.round(r.top + r.height / 2), w: innerWidth, h: innerHeight, text: (el.innerText || '').trim().slice(0, 60) });
    };
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ error: String(e).slice(0, 120) });
  }
})();
