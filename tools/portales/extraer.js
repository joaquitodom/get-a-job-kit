// Run on a Bumeran or ZonaJobs results page (same platform). Returns raw result cards; tools/portales.py parses them.
// Reads what is on the page only: no clicks, no navigation.
(() => {
  const challenge = /just a moment|verify you are human|captcha/i.test(document.body.innerText.slice(0, 2000));
  const cards = [...document.querySelectorAll('a[href*="/empleos/"]')]
    .filter(a => a.querySelector('h2'))
    .map(a => {
      const headings = [...a.querySelectorAll('h2, h3')].map(h => ({tag: h.tagName, text: h.innerText.trim()}));
      const known = new Set(headings.map(h => h.text));
      const description = a.innerText.split('\n').map(s => s.trim()).filter(s => s && !known.has(s)).join(' ').slice(0, 1500);
      return {href: a.getAttribute('href'), headings, description};
    });
  return {url: location.href, challenge, cards};
})()
