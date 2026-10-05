// Run on an application form page (built-in browser JavaScript tool). Returns the visible fields for tools.postular.
// Reads the page only: no typing, no clicking.
(() => {
  const labelOf = el => {
    const byFor = el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
    const wrap = el.closest('label');
    return ((byFor && byFor.innerText) || (wrap && wrap.innerText) || el.getAttribute('aria-label') || el.placeholder || el.name || '')
      .replace(/\s+/g, ' ').replace(/\*/g, '').trim();
  };
  const fields = [...document.querySelectorAll('input, select, textarea')]
    .filter(el => !['hidden', 'submit', 'button', 'image', 'reset'].includes(el.type) && el.offsetParent !== null)
    .map(el => ({
      label: labelOf(el),
      type: el.type === 'file' ? 'file' : (el.tagName === 'SELECT' ? 'select' : el.type || 'text'),
      required: el.required || el.getAttribute('aria-required') === 'true',
      selector: el.id ? '#' + CSS.escape(el.id) : `[name="${el.name}"]`,
    }));
  const challenge = /captcha|verify you are human|just a moment/i.test(document.body.innerText.slice(0, 3000));
  const terms = /t[eé]rminos|condiciones|privacidad|terms|privacy/i.test(fields.map(f => f.label).join(' '));
  return JSON.stringify({url: location.href, challenge, terms, fields});
})()
