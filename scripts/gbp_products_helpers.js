// Helpers injected into the GBP merchant panel page (Google Search "edit profile" panel).
// window.__P must be set to the product list [{name,price,slug,desc}] and window.__SITE to the site origin.
window.__docs = () => { const docs = [document]; for (const i of document.querySelectorAll('iframe')) { try { if (i.contentDocument) docs.push(i.contentDocument) } catch (e) {} } return docs };
window.__pd = () => { let dd; for (const x of window.__docs()) { if (/Product name|Add next product|All products|Add product/.test(x.body.innerText)) dd = x } return dd };
window.__vis = (el) => !!(el.offsetParent || el.getClientRects().length);
window.__labelOf = (el) => { let p = el; for (let i = 0; i < 4 && p; i++) { const t = p.innerText || ''; if (/Product name|category|price|description|landing/i.test(t)) return t.split('\n')[0].slice(0, 30); p = p.parentElement } return '?' };
window.__setVal = (el, v) => { const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype; const s = Object.getOwnPropertyDescriptor(proto, 'value').set; el.focus(); s.call(el, v); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); el.blur() };
window.__fields = (dd) => [...dd.querySelectorAll('input:not([type=file]):not([type=checkbox]),textarea')].filter(window.__vis);
window.__waitForm = async () => { for (let k = 0; k < 24; k++) { const dd = window.__pd(); if (dd && window.__fields(dd).length >= 5 && !location.hash.includes('confirmation')) return dd; await new Promise(r => setTimeout(r, 500)) } return null };
window.__openAdd = async () => { const dd = window.__pd(); const b = dd && [...dd.querySelectorAll('button,[role=button],a')].filter(window.__vis).find(b => /^(Add next product|Add product)$/.test(b.innerText.trim())); if (b) b.click(); return await window.__waitForm() };
window.__fill = async (i) => {
  const p = window.__P[i]; const dd = await window.__openAdd(); if (!dd) return { name: p.name, err: 'noform' };
  let f = window.__fields(dd); const by = (re) => f.find(x => re.test(window.__labelOf(x)));
  window.__setVal(by(/^Product name/), p.name); window.__setVal(by(/price \(USD\)/), p.price); window.__setVal(by(/description/), p.desc); window.__setVal(by(/landing/), window.__SITE + '/' + p.slug + '/');
  const blob = await fetch(window.__SITE + '/img/products/' + p.slug + '.jpg').then(r => r.blob()); const file = new File([blob], p.slug + '.jpg', { type: 'image/jpeg' }); const dt = new DataTransfer(); dt.items.add(file);
  for (const fi of dd.querySelectorAll('input[type=file]')) { fi.files = dt.files; fi.dispatchEvent(new Event('change', { bubbles: true })) }
  window.__setVal(by(/category/), 'Locksmith Services'); await new Promise(r => setTimeout(r, 1500));
  const opt = [...dd.querySelectorAll('[role=option],li')].filter(window.__vis).find(o => o.innerText.trim() === 'Locksmith Services'); if (opt) opt.click(); await new Promise(r => setTimeout(r, 1000));
  for (let k = 0; k < 24; k++) { if (!dd.body.innerText.includes('Drag a photo')) break; await new Promise(x => setTimeout(x, 500)) } await new Promise(x => setTimeout(x, 800));
  f = window.__fields(dd); return { name: p.name, vals: f.map(x => x.value.slice(0, 12)), photo: !dd.body.innerText.includes('Drag a photo') };
};
window.__publishBtn = () => { const dd = window.__pd(); const b = [...dd.querySelectorAll('button')].filter(window.__vis).find(b => b.innerText.trim() === 'Publish'); if (!b) return null; const fr = [...document.querySelectorAll('iframe')].find(i => { try { return i.contentDocument === dd } catch (e) { return false } }); const fb = fr ? fr.getBoundingClientRect() : { x: 0, y: 0 }; const r = b.getBoundingClientRect(); return { x: fb.x + r.x + r.width / 2, y: fb.y + r.y + r.height / 2 } };
