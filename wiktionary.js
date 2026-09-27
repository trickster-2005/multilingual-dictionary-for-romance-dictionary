/* 羅曼多語言字典 — wiktionary.js
 * Live fallback: when a word is not in the prebuilt dataset, fetch it from the
 * English Wiktionary MediaWiki API (CORS via origin=*) and convert it into the
 * same entry schema that data/entries/*.json uses, so app.js renders it unchanged.
 *
 * Sources per entry (all cached in memory):
 *   - the language section's rendered HTML: senses, labels, examples, headword
 *     inflections, IPA, gender, and the etymology tree (data-ety-tree-json, or the
 *     language-tagged mentions of the etymology paragraph);
 *   - the language section's wikitext: translation tables ({{t}}, {{t+}}, ...),
 *     including /translations subpages.
 */
'use strict';
(() => {
  const API = 'https://en.wiktionary.org/w/api.php';
  const ROMANCE = ['fr', 'it', 'es', 'pt'];
  const LANG_SECTION = { en: 'English', it: 'Italian', pt: 'Portuguese', fr: 'French', es: 'Spanish', zh: 'Chinese', la: 'Latin' };
  const POS_HEADINGS = {
    Noun: 'noun', Verb: 'verb', Adjective: 'adj', Adverb: 'adv', Numeral: 'num', Pronoun: 'pron',
    Preposition: 'prep', Conjunction: 'conj', Interjection: 'intj', Determiner: 'det', Article: 'article',
    Particle: 'particle', Phrase: 'phrase', 'Prepositional phrase': 'phrase', 'Proper noun': 'name',
  };
  const USAGE = new Set(['informal', 'formal', 'colloquial', 'slang', 'vulgar', 'offensive', 'derogatory', 'humorous',
    'euphemistic', 'figurative', 'literary', 'poetic', 'archaic', 'dated', 'obsolete', 'rare', 'historical', 'British',
    'US', 'Canada', 'Australia', 'Ireland', 'Scotland', 'India', 'impersonal', 'transitive', 'intransitive',
    'uncountable', 'countable', 'idiomatic', 'technical', 'computing', 'chess', 'law', 'medicine', 'mathematics',
    'music', 'sports', 'finance', 'business', 'biology', 'chemistry', 'physics', 'nautical', 'military']);
  const TAG_ALIAS = { figuratively: 'figurative', uk: 'British', british: 'British', us: 'US', american: 'US', 'north america': 'US' };
  const REL = { inherited: 'inh', inh: 'inh', from: 'inh', derived: 'der', der: 'der', borrowed: 'bor', bor: 'bor',
    'learned borrowing': 'bor', calque: 'calque' };
  const STOP = new Set(['a', 'an', 'the', 'of', 'to', 'in', 'on', 'at', 'for', 'by', 'with', 'and', 'or', 'is', 'are',
    'be', 'that', 'which', 'who', 'it', 'its', 'as', 'from', 'into', 'something', 'someone', 'etc', 'especially',
    'usually', 'used', 'very', 'not', 'when', 'where', 'can', 'you', 'your', 'their', 'this', 'some', 'any']);
  const FORM_OF_RE = /^(?:infl(?:ection)? of|(?:en-)?(?:simple )?past(?: participle)? of|plural of|(?:en-)?third-person singular of|(?:en-)?ing form of|present participle of|comparative of|superlative of|feminine(?: singular| plural)? of|masculine plural of|form of|alt(?:ernative)? form of|alt form|es-verb form of|pt-verb form of|it-verb form of|fr-verb form of|verb form of|noun form of|adj form of|conjugation of|zh-see|ja-see)$/i;

  /* ------------------------------------------------------------ fetching */
  const cache = new Map();
  function api(params) {
    const u = new URL(API);
    Object.entries({ ...params, format: 'json', formatversion: '2', origin: '*' })
      .forEach(([k, v]) => u.searchParams.set(k, v));
    const key = u.toString();
    if (!cache.has(key)) {
      const p = fetch(key).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });
      cache.set(key, p);
      p.catch(() => cache.delete(key));
    }
    return cache.get(key);
  }
  /**
   * Raw page wikitext, many titles per request (no server-side rendering, so fast).
   * Returns Map(requested title -> {title: canonical title, content}).
   */
  const pageCache = new Map();
  async function pagesWikitext(titles) {
    const out = new Map();
    const todo = [];
    titles.forEach(t => { if (pageCache.has(t)) out.set(t, pageCache.get(t)); else todo.push(t); });
    for (let i = 0; i < todo.length; i += 50) {
      const batch = todo.slice(i, i + 50);
      const j = await api({ action: 'query', prop: 'revisions', rvprop: 'content', rvslots: 'main', titles: batch.join('|'), redirects: '1' });
      const q = (j && j.query) || {};
      const back = new Map();                                   // canonical title -> requested titles
      const hop = new Map();
      (q.normalized || []).concat(q.redirects || []).forEach(x => hop.set(x.from, x.to));
      batch.forEach(t => { let c = t; for (let k = 0; k < 4 && hop.has(c); k++) c = hop.get(c); back.set(c, (back.get(c) || []).concat(t)); });
      (q.pages || []).forEach(p => {
        const content = p.revisions && p.revisions[0] && p.revisions[0].slots && p.revisions[0].slots.main.content;
        const val = content ? { title: p.title, content } : null;
        (back.get(p.title) || []).forEach(t => { pageCache.set(t, val); if (val) out.set(t, val); });
      });
      batch.forEach(t => { if (!pageCache.has(t)) pageCache.set(t, null); });
    }
    return out;
  }
  async function pageText(title) { return (await pagesWikitext([title])).get(title) || null; }
  function l2Names(wikitext) { return [...wikitext.matchAll(/^==\s*([^=].*?)\s*==\s*$/gm)].map(m => m[1]); }

  /** Render a trimmed piece of wikitext in the context of `title` (POST, returns the parser root). */
  const renderCache = new Map();
  function renderWikitext(title, text) {
    const key = `${title}\u0000${text}`;
    if (!renderCache.has(key)) {
      const body = new URLSearchParams({ action: 'parse', title, text, prop: 'text', contentmodel: 'wikitext',
        disablelimitreport: '1', disableeditsection: '1', format: 'json', formatversion: '2' });
      const p = fetch(`${API}?origin=*`, { method: 'POST', body })
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(j => {
          if (j.error) throw new Error(j.error.info || 'parse error');
          const doc = new DOMParser().parseFromString(j.parse.text, 'text/html');
          return doc.querySelector('.mw-parser-output') || doc.body;
        });
      renderCache.set(key, p);
      p.catch(() => renderCache.delete(key));
    }
    return renderCache.get(key);
  }
  // sub-sections that are expensive to render and never used from HTML
  const DROP_SECTIONS = /^(Translations|Quotations|Descendants|References|Further reading|Anagrams|See also|Conjugation|Declension|Inflection|Mutation|Hypernyms|Hyponyms|Meronyms|Holonyms|Troponyms|Coordinate terms|Alternative forms|Gallery|Trivia|Statistics|Usage notes|Collocations|Paronyms|Idioms|Proverbs)/;
  function trimForRender(langName, sec, short) {
    const out = [`==${langName}==`];
    headingBlocks(sec).forEach(b => {
      if (b.level === 1) return;
      if (DROP_SECTIONS.test(b.title)) return;
      if (short && !(POS_HEADINGS[b.title] || /^Pronunciation/.test(b.title))) return;
      const head = `${'='.repeat(b.level)}${b.title}${'='.repeat(b.level)}`;
      if (/^Etymology/.test(b.title)) { out.push(head); return; }      // parsed from wikitext instead
      let body = b.body.split('\n').filter(l => !/^#+\*/.test(l) && !/^\{\{(multiple images|wp|wikipedia|slim-wikipedia|was fwotd|number box)/i.test(l));
      if (short && POS_HEADINGS[b.title]) {
        let defs = 0;
        body = body.filter(l => (/^#(?![:*])/.test(l) ? ++defs <= 3 : !/^#/.test(l)));
      }
      out.push(head, body.join('\n'));
    });
    return out.join('\n');
  }
  /** L2 language section of a page: {title, html: Element|null, wikitext} or null. */
  async function langSection(title, langName, wantHtml = true, short = false) {
    const page = await pageText(title);
    if (!page) return null;
    const sec = l2Section(page.content, langName);
    if (sec == null) return null;
    const html = wantHtml ? await renderWikitext(page.title, trimForRender(langName, sec, short)) : null;
    return { title: page.title, html, wikitext: sec };
  }
  async function pageWikitext(title) {
    const p = await pageText(title);
    return p ? p.content : null;
  }
  async function pool(items, limit, fn) {
    const out = new Array(items.length);
    let i = 0;
    const worker = async () => { while (i < items.length) { const k = i++; try { out[k] = await fn(items[k]); } catch (e) { out[k] = null; } } };
    await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
    return out;
  }

  /* -------------------------------------------------------- wikitext tools */
  /** Top-level {{templates}} of a wikitext string: [{name, args:{1:..,t:..}}]. */
  function templates(text) {
    const out = [];
    let i = 0;
    while ((i = text.indexOf('{{', i)) !== -1) {
      let depth = 0, j = i;
      for (; j < text.length - 1; j++) {
        if (text[j] === '{' && text[j + 1] === '{') { depth++; j++; } else if (text[j] === '}' && text[j + 1] === '}') { depth--; j++; if (!depth) break; }
      }
      const inner = text.slice(i + 2, j - 1);
      const parts = [];
      let d = 0, start = 0;
      for (let k = 0; k < inner.length; k++) {
        const two = inner.slice(k, k + 2);
        if (two === '{{' || two === '[[') { d++; k++; } else if (two === '}}' || two === ']]') { d--; k++; } else if (inner[k] === '|' && d === 0) { parts.push(inner.slice(start, k)); start = k + 1; }
      }
      parts.push(inner.slice(start));
      const args = {};
      let n = 1;
      parts.slice(1).forEach(p => {
        const m = p.match(/^\s*([A-Za-z][\w-]*)\s*=([\s\S]*)$/);
        if (m) args[m[1]] = m[2].trim(); else args[String(n++)] = p.trim();
      });
      out.push({ name: parts[0].trim(), args, start: i, end: j + 1 });
      i = j + 1;
    }
    return out;
  }
  /** Split wikitext into [{level, title, body}] by == headings ==. */
  function headingBlocks(text) {
    const re = /^(={2,6})\s*(.+?)\s*\1\s*$/gm;
    const out = [];
    let m, last = { level: 1, title: '', idx: 0 };
    while ((m = re.exec(text))) {
      out.push({ ...last, body: text.slice(last.idx, m.index) });
      last = { level: m[1].length, title: m[2].replace(/<!--.*?-->/g, '').trim(), idx: re.lastIndex };
    }
    out.push({ ...last, body: text.slice(last.idx) });
    return out;
  }

  /* ------------------------------------------------------------ html tools */
  const txt = el => (el ? el.textContent.replace(/\s+/g, ' ').trim() : '');
  function headingOf(el) {
    let h = null;
    if (el.matches && el.matches('div.mw-heading')) h = el.querySelector('h1,h2,h3,h4,h5,h6');
    else if (el.matches && el.matches('h2,h3,h4,h5,h6')) h = el;
    if (!h) return null;
    const c = h.cloneNode(true);
    c.querySelectorAll('.mw-editsection').forEach(x => x.remove());
    return { level: +h.tagName[1], title: txt(c) };
  }
  /** Children of the section grouped under their headings. */
  function htmlBlocks(root) {
    const out = [];
    let cur = { level: 2, title: '', els: [] };
    for (const el of Array.from(root.children)) {
      const h = headingOf(el);
      if (h) { out.push(cur); cur = { ...h, els: [] }; } else cur.els.push(el);
    }
    out.push(cur);
    return out;
  }

  /* ---------------------------------------------------------- etymology */
  function treeChain(tree) {
    const nodes = [];
    let cur = tree;
    for (let guard = 0; cur && guard < 24; guard++) {
      const groups = (cur.children || []).filter(g => g && !g.is_invisible && g.keyword !== 'root' && (g.terms || []).length);
      if (!groups.length) break;
      const g = groups[0];
      const terms = g.terms.filter(t => t && t.lang && t.term);
      const kw = String(g.keyword || '').toLowerCase();
      if (terms.length !== 1) break;
      const t = terms[0];
      const node = { l: t.lang, f: t.term, t: REL[kw] || 'der' };
      if (t.transliteration) node.tr = t.transliteration;
      if (t.t || t.gloss) node.g = t.t || t.gloss;
      if (t.is_uncertain) node.unc = true;
      nodes.push(node);
      cur = t;
    }
    return nodes;
  }
  const CASES = { accusative: 'acc', genitive: 'gen', ablative: 'abl', dative: 'dat', nominative: 'nom', infinitive: 'inf', plural: 'pl' };
  /** Fallback: language-tagged mentions of the etymology paragraph, in reading order. */
  function mentionChain(els, selfLang) {
    const nodes = [];
    let between = '';
    let stopped = false;
    const walk = node => {
      if (stopped) return;
      if (node.nodeType === 3) { between += node.textContent; return; }
      if (node.nodeType !== 1) return;
      const el = node;
      if (el.matches('style, sup, .reference, [data-ety-tree-json], .etytree, .NavFrame')) return;
      const isMention = el.hasAttribute('lang') && (el.matches('.mention, i, b, span') && el.getAttribute('lang') !== 'en' || el.matches('.mention'))
        && !el.closest('.mention-gloss') && el.getAttribute('lang') !== selfLang;
      if (isMention && txt(el)) {
        if (/\b(cognate|compare|doublet|cf\.|akin to|related to|see also|displaced|unrelated|not related|replaced|superseded)\b/i.test(between)) { stopped = true; return; }
        const lang = el.getAttribute('lang').replace(/-Latn$|-Arab$|-Grek$|-Cyrl$/, '');
        const form = txt(el);
        const prev = nodes[nodes.length - 1];
        const caseM = between.match(/\b(accusative|genitive|ablative|dative|nominative|infinitive|plural)\b(?:\s+(?:singular|plural))?\s+of\s*$/i);
        if (prev && prev.l === lang && caseM) { prev.lm = form; prev.lmt = CASES[caseM[1].toLowerCase()]; between = ''; return; }
        const t = /borrow/i.test(between) ? 'bor' : /inherit/i.test(between) ? 'inh' : 'der';
        const n = { l: lang, f: form, t };
        if (/\b(possibly|probably|perhaps|uncertain)\b/i.test(between)) n.unc = true;
        let sib = el.nextSibling, hops = 0;
        while (sib && hops < 6) {
          if (sib.nodeType === 1 && sib.matches('.mention-gloss, .mention-gloss-double-quote, .mention-tr, .tr')) {
            if (sib.matches('.mention-gloss')) { n.g = txt(sib); break; }
            if (sib.matches('.mention-tr, .tr')) n.tr = txt(sib);
          } else if (sib.nodeType === 1 && sib.hasAttribute('lang')) break;
          sib = sib.nextSibling; hops++;
        }
        if (!prev || !(prev.l === n.l && prev.f === n.f)) nodes.push(n);
        between = '';
        return;
      }
      Array.from(el.childNodes).forEach(walk);
    };
    els.forEach(walk);
    return nodes;
  }
  /* Wikitext templates -> chain (same rules as tools/build_dataset.py) */
  const ANC_T = { inh: 'inh', 'inh+': 'inh', 'inh-lite': 'inh', der: 'der', 'der+': 'der', 'der-lite': 'der', uder: 'der',
    bor: 'bor', 'bor+': 'bor', lbor: 'bor', slbor: 'bor', obor: 'bor', ubor: 'bor', ltc: 'ltc', calque: 'calque', cal: 'calque', clq: 'calque' };
  const MENTION_T = new Set(['m', 'mention', 'l', 'link', 'll', 'm+']);
  const COG_T = new Set(['cog', 'cognate', 'cog+']);
  const STOP_T = new Set(['cog', 'cognate', 'cog+', 'noncog', 'ncog', 'nc', 'noncognate', 'doublet', 'dbt']);
  const FORM_T = new Set(['af', 'affix', 'suffix', 'suf', 'prefix', 'pre', 'compound', 'com', 'confix', 'con', 'blend', 'surf', 'univerbation']);
  const UNC_T = new Set(['unc', 'uncertain', 'unk', 'unknown']);
  const ETYMON_T = new Set(['etymon', 'ety']);
  const ETYMON_FORM = new Set(['af', 'affix', 'afeq', 'compound', 'com', 'suf', 'suffix', 'pre', 'prefix', 'con', 'confix', 'blend', 'univerbation']);
  const norm = s => String(s || '').trim().toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae').replace(/ß/g, 'ss')
    .normalize('NFKD').replace(/\p{M}/gu, '').replace(/\s+/g, ' ');
  const akey = f => norm(String(f || '').replace(/^\*/, ''));
  const nkey = n => `${n.l}:${akey(n.lm || n.f)}`;

  function etymonArgs(a, selfLang) {
    let rel = null;
    const parts = [];
    const keys = Object.keys(a).filter(k => /^\d+$/.test(k) && +k >= 2).sort((x, y) => x - y);
    for (const k of keys) {
      let v = (a[k] || '').trim();
      if (!v) continue;
      if (v.startsWith(':')) { if (parts.length || (rel && REL[rel])) break; rel = v.slice(1).toLowerCase(); continue; }
      if (!rel) continue;
      const mods = {};
      v.replace(/<(\w+):([^>]*)>/g, (_, mk, mv) => { mods[mk] = mv; return ''; });
      v = v.replace(/<[^>]*>/g, '');
      const m = v.match(/^([a-z]{2,3}(?:-[a-z]{2,5}){0,2}):(.+)$/);
      const node = { l: m ? m[1] : selfLang, f: m ? m[2] : v, t: REL[rel] || ANC_T[rel] || 'der' };
      if (mods.t || mods.gloss) node.g = mods.t || mods.gloss;
      if (mods.tr) node.tr = mods.tr;
      if (mods.id) node.id = mods.id;
      if (REL[rel] || ANC_T[rel]) return { chain: [node], form: null };
      parts.push(node.f);
    }
    return { chain: [], form: ETYMON_FORM.has(rel) && parts.length ? { l: selfLang, parts } : null };
  }
  function parseEtyTemplates(tpls, selfLang) {
    let chain = [], et = [], form = null, pendingUnc = false, stopped = false;
    const cog = [];
    for (const t of tpls) {
      const n = t.name, a = t.args;
      if (ETYMON_T.has(n)) { const r = etymonArgs(a, a['1'] || selfLang); if (r.chain.length > et.length) et = r.chain; form = form || r.form; continue; }
      if (UNC_T.has(n)) { pendingUnc = true; continue; }
      if (STOP_T.has(n)) {
        stopped = true;
        if (COG_T.has(n) && a['1'] && a['2'] && cog.length < 8) cog.push({ l: a['1'].split(',')[0], f: a['2'], ...(a.tr ? { tr: a.tr } : {}) });
        continue;
      }
      if (stopped) continue;
      if (ANC_T[n]) {
        const src = (a['2'] || '').trim();
        const lemma = (a['3'] || '').split(',')[0].trim();          // "nighte,night,nyght" -> first spelling
        let f = (a['4'] || lemma).trim();
        if (!src || src === '-' || !f || f === '-') continue;      // language-only step: nothing to show
        const node = { l: src, f, t: ANC_T[n] };
        if (lemma && lemma !== '-' && akey(lemma) !== akey(f)) node.lm = lemma;
        const g = a['5'] || a.t || a.gloss;
        if (g) node.g = g;
        if (a.tr) node.tr = a.tr;
        if (pendingUnc) { node.unc = true; pendingUnc = false; }
        const last = chain[chain.length - 1];
        if (!(last && last.l === src && akey(last.f) === akey(f))) chain.push(node);
      } else if (MENTION_T.has(n)) {
        const last = chain[chain.length - 1];
        if (last && a['1'] === last.l && a['2']) {
          if (akey(a['2']) !== akey(last.f) && !last.lm) last.lm = a['2'];
          const g = a['4'] || a.t || a.gloss;
          if (g && !last.g) last.g = g;
        }
      } else if (FORM_T.has(n) && !chain.length && !form) {
        const parts = Object.keys(a).filter(k => /^\d+$/.test(k) && +k >= 2).sort((x, y) => x - y).map(k => a[k]).filter(Boolean);
        if (parts.length) form = { l: a['1'] || selfLang, parts };
      }
    }
    if (et.length > chain.length) chain = et;
    return { chain, cog, form, unc: pendingUnc && !chain.length };
  }
  const cleanWiki = s => String(s || '')
    .replace(/\{\{(?:l|m|ll|w)\|[^|}]*\|([^|}]*)[^}]*\}\}/g, '$1')
    .replace(/\{\{[^{}]*\}\}/g, '').replace(/\[\[(?:[^\]|]*\|)?([^\]]*)\]\]/g, '$1')
    .replace(/'{2,}/g, '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  function synthText(chain, form) {
    const parts = chain.map((n, i) => `${i ? 'from' : (n.t === 'bor' ? 'Borrowed from' : 'From')} ${LANG_EN[n.l] || n.l} ${n.f}${n.g ? ` (“${n.g}”)` : ''}`);
    let s = parts.join(', ');
    if (form) s = (s ? s + '. ' : '') + `From ${form.parts.join(' + ')}`;
    return s ? s + '.' : '';
  }
  /**
   * Etymology of one Etymology section. `wikiBody` is the section's wikitext (always
   * reliable); the rendered HTML adds the full tree JSON when the page renders cleanly.
   */
  function etymologyFrom(els, wikiBody, selfLang) {
    const fromTpl = parseEtyTemplates(templates(wikiBody || ''), selfLang);
    let chain = fromTpl.chain;
    for (const el of els) {
      const holder = el.matches('[data-ety-tree-json]') ? el : el.querySelector('[data-ety-tree-json]');
      if (!holder) continue;
      try {
        const tree = JSON.parse(holder.getAttribute('data-ety-tree-json'));
        const tc = treeChain(tree);
        collectNames(tree);
        if (tc.length > chain.length) chain = tc;
      } catch (e) { /* malformed attribute: keep template chain */ }
      break;
    }
    // prose only: skip the drawn "Etymology tree" box (root-first) and Lua errors from partial rendering
    const BOX = '[data-ety-tree-json], .etymonid, .etytree, .NavFrame, style, figure, .thumb, table';
    const textEls = els.filter(el => !el.matches(BOX) && !el.querySelector('.etymonid, .etytree')).map(el => {
      const c = el.cloneNode(true);
      c.querySelectorAll('.error, .scribunto-error').forEach(x => x.remove());
      return c;
    });
    const hadError = els.some(el => el.querySelector && el.querySelector('.error, .scribunto-error'));
    if (!chain.length && !hadError) chain = mentionChain(textEls, selfLang);
    let text = textEls.map(txt).join(' ').replace(/\s+/g, ' ').replace(/^[\s.,;]+/, '').trim();
    if (hadError || !text) text = [synthText(chain, fromTpl.form), text].filter(Boolean).join(' ');
    text = text.slice(0, 700);
    const unc = fromTpl.unc || (!chain.length && /\b(unknown|uncertain) origin\b/i.test(text));
    return { chain, text, unc, cog: fromTpl.cog, form: chain.length ? null : fromTpl.form };
  }
  const liveNames = {};
  function collectNames(tree) {
    const walk = t => { if (!t || typeof t !== 'object') return; if (t.lang && t.lang_name) liveNames[t.lang] = t.lang_name; (t.children || t.terms || []).forEach(walk); };
    walk(tree);
  }

  /* Follow the oldest known ancestor to its own Wiktionary page (Latin nox ->
   * Reconstruction:Proto-Italic/nokʷts -> ...), several chains per batch request. */
  const LANG_EN = {
    en: 'English', enm: 'Middle English', ang: 'Old English', 'gem-pro': 'Proto-Germanic', 'gmw-pro': 'Proto-West Germanic',
    'ine-pro': 'Proto-Indo-European', 'itc-pro': 'Proto-Italic', la: 'Latin', grc: 'Ancient Greek', fro: 'Old French',
    frm: 'Middle French', fr: 'French', it: 'Italian', 'roa-oit': 'Old Italian', pt: 'Portuguese', 'roa-opt': 'Old Galician-Portuguese',
    es: 'Spanish', osp: 'Old Spanish', frk: 'Frankish', lng: 'Lombardic', non: 'Old Norse', ar: 'Arabic', ota: 'Ottoman Turkish',
    nl: 'Dutch', dum: 'Middle Dutch', xno: 'Anglo-Norman', got: 'Gothic', 'cel-pro': 'Proto-Celtic', 'sla-pro': 'Proto-Slavic',
    fa: 'Persian', sa: 'Sanskrit', de: 'German', goh: 'Old High German', gmh: 'Middle High German', ca: 'Catalan', pro: 'Old Occitan',
    'grk-pro': 'Proto-Hellenic', 'itc-ola': 'Old Latin', 'sem-pro': 'Proto-Semitic', he: 'Hebrew', tr: 'Turkish',
  };
  const PARENT_LANG = { 'la-vul': 'la', 'la-lat': 'la', 'la-med': 'la', 'la-eme': 'la', 'la-ecc': 'la', 'la-new': 'la', 'la-cla': 'la', 'la-ear': 'la', 'grc-koi': 'grc' };
  function ancestorTarget(node) {
    const lang = PARENT_LANG[node.l] || node.l;
    const name = LANG_EN[lang];
    const form = String(node.lm || node.f || '').trim();
    if (!name || !form || lang === 'ine-pro' || /\s/.test(form.replace(/^\*/, '')) && lang !== 'la') return null;
    if (form.startsWith('*') || /-pro$/.test(lang)) return { title: `Reconstruction:${name}/${form.replace(/^\*/, '')}`, section: name, lang };
    const title = /^(la|grc|ang|enm|non|got)$/.test(lang) ? form.normalize('NFD').replace(/[\u0304\u0306]/g, '').normalize('NFC') : form;
    return { title, section: name, lang };
  }
  function l2Section(wikitext, name) {
    const re = new RegExp(`^==\\s*${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*==\\s*$`, 'm');
    const m = re.exec(wikitext);
    if (!m) return null;
    const rest = wikitext.slice(m.index + m[0].length);
    const next = rest.search(/^==[^=]/m);
    return next === -1 ? rest : rest.slice(0, next);
  }
  async function extendChains(chains) {
    const done = new WeakSet();
    for (let hop = 0; hop < 5; hop++) {
      const need = new Map();
      chains.forEach(ch => {
        const last = ch[ch.length - 1];
        if (!last || done.has(last)) return;
        const target = ancestorTarget(last);
        if (!target) { done.add(last); return; }
        if (!need.has(target.title)) need.set(target.title, { ...target, chains: [] });
        need.get(target.title).chains.push(ch);
      });
      if (!need.size) break;
      const pages = await pagesWikitext([...need.keys()]);
      need.forEach((info, title) => {
        const page = pages.get(title);
        const sec = page && l2Section(page.content, info.section);
        const fo = sec && formOfTarget(sec, info.lang);
        let ext = [], gloss = '';
        if (sec && !fo) {
          const ets = templates(sec).filter(t => ETYMON_T.has(t.name));
          const wantedId = info.chains.map(c => c[c.length - 1].id).find(Boolean);
          const et = wantedId && ets.find(t => t.args.id === wantedId);
          const blocks = headingBlocks(sec);
          const etyBlock = blocks.find(b => /^Etymology/.test(b.title));
          ext = et ? etymonArgs(et.args, info.lang).chain : parseEtyTemplates(templates(etyBlock ? etyBlock.body : sec), info.lang).chain;
          const def = sec.split('\n').find(l => /^#(?![:*])/.test(l));
          gloss = def ? cleanWiki(def.slice(1)).slice(0, 60) : '';
        }
        info.chains.forEach(ch => {
          const last = ch[ch.length - 1];
          if (fo && fo.lemma && !last.lm) { last.lm = fo.lemma; return; }      // e.g. Latin noctem -> nox, retried next hop
          if (gloss && !last.g) last.g = gloss;
          const have = new Set(ch.map(nkey));
          const add = ext.filter(n => !have.has(nkey(n)));
          if (!add.length) { done.add(last); return; }
          done.add(last);
          ch.push(...add.map(n => ({ ...n })));
        });
      });
    }
    chains.forEach(ch => ch.forEach(n => { delete n.id; }));
  }

  /* ----------------------------------------------------- sense parsing */
  function tagsFromLabels(li) {
    const tags = [];
    li.querySelectorAll(':scope > .usage-label-sense .ib-content, :scope > span > .usage-label-sense .ib-content').forEach(c => {
      txt(c).split(/[,;]/).forEach(raw => {
        const w = raw.trim();
        const k = TAG_ALIAS[w.toLowerCase()] || (USAGE.has(w) ? w : USAGE.has(w.toLowerCase()) ? w.toLowerCase() : null);
        if (k && !tags.includes(k)) tags.push(k);
      });
    });
    return tags;
  }
  function senseText(li) {
    const c = li.cloneNode(true);
    c.querySelectorAll('ol, ul, dl, .usage-label-sense, sup, style, .HQToggle, .maintenance-line, .nyms-toggle, .citation-whole').forEach(x => x.remove());
    return txt(c).replace(/^[\s:;,.]+/, '');
  }
  function sensesFrom(ol) {
    const out = [];
    for (const li of Array.from(ol.children)) {
      if (li.tagName !== 'LI' || li.classList.contains('mw-empty-elt')) continue;
      const d = senseText(li);
      if (!d) continue;
      const s = { d };
      const tags = tagsFromLabels(li);
      if (tags.length) s.tags = tags;
      const ex = Array.from(li.querySelectorAll(':scope > dl .h-usage-example .e-example, :scope > dl .e-example'))
        .map(txt).filter(x => x && x.length < 220).slice(0, 2);
      if (ex.length) s.ex = [...new Set(ex)];
      const syn = Array.from(li.querySelectorAll(':scope > dl .nyms.synonym [lang]')).map(txt).filter(Boolean).slice(0, 6);
      if (syn.length) s.syn = syn;
      out.push(s);
      if (out.length >= 10) break;
    }
    return out;
  }
  function formCode(cls) {
    const tok = String(cls || '').split(/\s+/).find(c => /-form-of$/.test(c));
    if (!tok) return null;
    const parts = tok.replace(/-form-of$/, '').split('|');
    const has = p => parts.includes(p);
    if (has('ptcp') && has('past')) return 'pp';
    if (has('ptcp') && has('pres')) return 'ing';
    if (has('3') && has('s') && has('pres')) return '3s';
    if (has('comparative') || has('comd')) return 'comp';
    if (has('superlative') || has('supd')) return 'sup';
    if (has('past')) return 'past';
    if (has('f') && has('p')) return 'fpl';
    if (has('m') && has('p')) return 'mpl';
    if (has('p')) return 'pl';
    if (has('f')) return 'f';
    return null;
  }
  function headwordForms(els) {
    const forms = [];
    for (const el of els) {
      const hl = el.matches('.headword-line') ? el : el.querySelector && el.querySelector('.headword-line');
      if (!hl) continue;
      hl.querySelectorAll('b[class*="form-of"]').forEach(b => {
        const code = formCode(b.className);
        const f = txt(b);
        if (code && f && !forms.some(x => x[0] === code && x[1] === f)) forms.push([code, f]);
      });
      break;
    }
    return forms.slice(0, 10);
  }
  function linkWords(els) {
    const out = [];
    els.forEach(el => el.querySelectorAll('li a, .term-list a, [lang="en"] a').forEach(a => {
      const w = txt(a);
      if (w && !/^(Thesaurus|Appendix|Category|See|edit)\b/.test(w) && !a.closest('.mw-editsection') && !out.includes(w)) out.push(w);
    }));
    return out;
  }
  function ipaFrom(els) {
    const out = { any: null, uk: null, us: null, br: null, pt: null };
    els.forEach(el => el.querySelectorAll('li').forEach(li => {
      const ipaEl = li.querySelector(':scope > .IPA, :scope > span > .IPA, .IPA');
      if (!ipaEl || ipaEl.closest('li') !== li) return;
      const ipa = txt(ipaEl);
      if (!/^[/[]/.test(ipa)) return;
      const acc = txt(li.querySelector('.usage-label-accent, .qualifier-content, .ib-content'));
      out.any = out.any || ipa;
      if (/\b(UK|Received|RP|British|England|SSBE)\b/i.test(acc)) out.uk = out.uk || ipa;
      if (/\b(US|General American|GA|GenAm|American)\b/.test(acc)) out.us = out.us || ipa;
      if (/Brazil/i.test(acc)) out.br = out.br || ipa;
      if (/Portugal|Lisbon/i.test(acc)) out.pt = out.pt || ipa;
    }));
    if (!out.any) els.forEach(el => { const i = el.querySelector('.IPA'); const v = txt(i); if (!out.any && /^[/[]/.test(v)) out.any = v; });
    return out;
  }

  /* -------------------------------------------------- translations */
  function translationTables(wikitext) {
    // returns [{pos, label, items:[{lang, word, g, v}]}] in page order
    const out = [];
    let pos = null;
    headingBlocks(wikitext).forEach(b => {
      if (POS_HEADINGS[b.title]) pos = POS_HEADINGS[b.title];
      if (!/^Translations/.test(b.title)) return;
      const body = b.body;
      const tops = templates(body);
      let cur = null;
      const scan = list => list.forEach((t, i) => {
        const n = t.name;
        if (/^(check)?trans-top(-see|-also)?$/.test(n)) {
          const label = (t.args['1'] || t.args.id || '')
            .replace(/\[\[(?:[^\]|]*\|)?([^\]]*)\]\]/g, '$1')      // [[link|text]] -> text
            .replace(/'{2,}/g, '')                                  // ''italic'' / '''bold'''
            .replace(/\{\{[^{}]*\}\}/g, '').trim();
          cur = { pos, label, items: [] };
          out.push(cur);
          return;
        }
        if (n === 'multitrans' && t.args.data) { scan(templates(t.args.data)); return; }
        if (!cur || !/^(t|t\+|tt|tt\+|t-simple|t-check|t\+check)$/.test(n)) return;
        let lang = t.args['1'];
        const word = (t.args.alt || t.args['2'] || '').replace(/\[\[|\]\]/g, '').trim();
        if (!word) return;
        if (lang === 'cmn') lang = 'zh';
        if (!ROMANCE.includes(lang) && lang !== 'zh') return;
        const g = ['3', '4'].map(k => t.args[k]).filter(Boolean).join(' ');
        const item = { lang, word, g };
        if (lang === 'pt') {
          // a following {{q|Brazil}} / {{qualifier|Portugal}} marks a variant-specific word
          const next = list[i + 1];
          const q = next && /^(q|qual|qualifier|i|lb)$/.test(next.name) ? Object.values(next.args).join(' ') : '';
          if (/Brazil/.test(q)) item.v = 'BR'; else if (/Portugal/.test(q)) item.v = 'PT';
        }
        const nextT = list[i + 1];
        const qual = nextT && /^(q|qual|qualifier|i|lb)$/.test(nextT.name) ? Object.values(nextT.args).join(' ') : '';
        if (/(dialect|regional|slang|vulgar|archaic|obsolete|rare|dated|poetic|literary|pejorative|colloquial|informal)/i.test(qual)) item.marked = true;
        cur.items.push(item);
      });
      scan(tops);
    });
    return out;
  }
  function subpageRequested(wikitext) {
    return /\{\{\s*(see translation subpage|trans-see)\b/i.test(wikitext) && /see translation subpage/i.test(wikitext);
  }

  /* ------------------------------------------------------ articles */
  const VOWELS = /^[aeiouàáâãäåèéêëìíîïòóôõöùúûüœæ]/i;
  const IT_IMPURE = /^(s[bcdfgklmnpqrstvz]|z|gn|ps|pn|x|y|i[aeiou])/i;
  const ES_STRESSED_A = new Set(['agua', 'águila', 'alma', 'arma', 'hambre', 'hacha', 'área', 'aula', 'ave', 'hada', 'ala', 'ancla', 'arca', 'asma', 'aya', 'haba', 'habla', 'alba']);
  const FR_H_ASP = new Set(['haricot', 'héros', 'hibou', 'hache', 'haine', 'honte', 'hasard', 'hauteur', 'hêtre', 'homard', 'hamac', 'harpe', 'haut', 'halte']);
  function article(lang, word, g, plural) {
    if (g !== 'm' && g !== 'f') return null;
    const w = word.toLowerCase();
    if (lang === 'it') {
      const vowel = VOWELS.test(w);
      if (g === 'm') {
        if (plural) return vowel || IT_IMPURE.test(w) ? 'gli' : 'i';
        if (IT_IMPURE.test(w)) return 'lo';
        return vowel || w[0] === 'h' ? "l'" : 'il';
      }
      return plural ? 'le' : (vowel ? "l'" : 'la');
    }
    if (lang === 'pt') return g === 'm' ? (plural ? 'os' : 'o') : (plural ? 'as' : 'a');
    if (lang === 'fr') {
      if (plural) return 'les';
      if (VOWELS.test(w) || (w[0] === 'h' && !FR_H_ASP.has(w))) return "l'";
      return g === 'm' ? 'le' : 'la';
    }
    if (lang === 'es') {
      if (g === 'm') return plural ? 'los' : 'el';
      if (plural) return 'las';
      return ES_STRESSED_A.has(w) ? 'el' : 'la';
    }
    return null;
  }
  const genderOf = s => {
    const v = String(s || '');
    const m = /\bm\b|masculine/.test(v), f = /\bf\b|feminine/.test(v);
    return m && f ? 'mf' : m ? 'm' : f ? 'f' : null;
  };

  /* ---------------------------------------------------- matching */
  function tokens(s) {
    const out = new Set();
    (String(s || '').toLowerCase().match(/[a-z0-9']+/g) || []).forEach(w => {
      if (STOP.has(w)) return;
      if (w.length > 3 && w.endsWith('s') && !w.endsWith('ss')) w = w.slice(0, -1);
      out.add(w);
    });
    return out;
  }
  function score(label, gloss) {
    const a = tokens(label), b = tokens(gloss);
    if (!a.size || !b.size) return 0;
    let n = 0;
    a.forEach(x => { if (b.has(x)) n++; });
    return n / a.size;
  }

  /* ------------------------------------------------ Romance words */
  async function romanceWord(lang, item, pos) {
    const w = { w: item.word };
    const g0 = genderOf(item.g);
    if (item.v) w.v = item.v;
    const sec = await langSection(item.word, LANG_SECTION[lang], true, true).catch(() => null);
    if (sec && sec.html) {
      const blocks = htmlBlocks(sec.html);
      const posBlock = blocks.find(b => POS_HEADINGS[b.title] === pos) || blocks.find(b => POS_HEADINGS[b.title]);
      if (posBlock) {
        w.p = POS_HEADINGS[posBlock.title];
        const hl = posBlock.els.map(el => (el.querySelector ? el.querySelector('.headword-line') : null)).find(Boolean);
        if (hl) {
          const gEl = hl.querySelector('.gender');
          const gg = genderOf(gEl ? gEl.textContent + ' ' + Array.from(gEl.querySelectorAll('abbr')).map(a => a.title).join(' ') : '');
          if (gg && w.p === 'noun') w.g = gg;
          hl.querySelectorAll('b[class*="form-of"]').forEach(b => {
            const code = formCode(b.className);
            if (code === 'pl' && !w.pl) w.pl = txt(b);
            if (code === 'f' && !w.fem && (w.p === 'adj' || w.p === 'noun')) w.fem = txt(b);
          });
        }
        const ol = posBlock.els.find(el => el.tagName === 'OL');
        if (ol) { const s = sensesFrom(ol)[0]; if (s) w.gl = s.d.slice(0, 120); }
      }
      const pron = blocks.filter(b => /^Pronunciation/.test(b.title)).flatMap(b => b.els);
      const ipa = ipaFrom(pron.length ? pron : blocks.flatMap(b => b.els));
      if (lang === 'pt') { if (ipa.br) w.ipaBR = ipa.br; if (ipa.pt) w.ipaPT = ipa.pt; }
      if (ipa.any) w.ipa = ipa.any;
      const etyBlock = blocks.find(b => /^Etymology/.test(b.title));
      const wikiEty = headingBlocks(sec.wikitext).find(b => /^Etymology/.test(b.title));
      const ety = etyBlock || wikiEty ? etymologyFrom(etyBlock ? etyBlock.els : [], wikiEty ? wikiEty.body : '', lang) : { chain: [], text: '' };
      w.ety = { chain: ety.chain, text: ety.text };
      if (ety.unc) w.ety.unc = true;
      if (ety.form) w.ety.form = ety.form;
    }
    if (!w.g && g0 && (w.p === 'noun' || !w.p)) w.g = g0;
    if (!w.p && pos) w.p = pos;
    if (w.g && w.p === 'noun') {
      const art = article(lang, w.w, w.g);
      if (art) w.art = art;
      if (w.pl) { const pa = article(lang, w.pl, w.g, true); if (pa) w.plArt = pa; }
    }
    return w;
  }

  /* ------------------------------------------------- English entry */
  async function englishEntry(title) {
    const page = await pageText(title);
    const secText = page && l2Section(page.content, 'English');
    if (secText == null || !page) return null;
    const sec = { title: page.title, wikitext: secText, html: null };
    // an inflected form only ("ran" = past of run): send the caller to the lemma
    // (also when the first/main sense is one: "ran" has a rare noun sense too)
    const defLines = sec.wikitext.split('\n').filter(l => /^#(?![:*])/.test(l));
    const isFormOf = l => templates(l).some(t => FORM_OF_RE.test(t.name) || /\bof$/.test(t.name));
    if (defLines.length && isFormOf(defLines[0])) {
      const fo = formOfTarget(sec.wikitext, 'en');
      if (fo && fo.lemma && akey(fo.lemma) !== akey(sec.title)) return { formOf: fo, title: sec.title };
    }
    // Run in parallel: render the (trimmed) English section, and meanwhile read the
    // translation tables and fetch + render the Romance words they list.
    const htmlP = renderWikitext(sec.title, trimForRender('English', secText, false));
    let tables = translationTables(sec.wikitext);
    if (!tables.some(t => t.items.length) && subpageRequested(sec.wikitext)) {
      const sub = await pageWikitext(`${sec.title}/translations`);
      if (sub) tables = translationTables(sub);
    }
    tables = tables.filter(t => t.items.some(i => ROMANCE.includes(i.lang)));
    tables.forEach((t, i) => { t._order = i; });
    tables.sort((a, b) => ROMANCE.filter(l => b.items.some(i => i.lang === l)).length - ROMANCE.filter(l => a.items.some(i => i.lang === l)).length);
    tables = tables.slice(0, 4);
    const wanted = [];
    // enrich up to 2 words per language for the main sense, 1 for the others (speed);
    // skip a feminine form listed right after its masculine ("bello m, bella f")
    const isFemTwin = (i, list) => /\bf\b/.test(i.g || '') && list.some(o => o !== i && /\bm\b/.test(o.g || '') && o.word.slice(0, 3) === i.word.slice(0, 3));
    tables.forEach((t, ti) => ROMANCE.forEach(l => {
      const all = t.items.filter(i => i.lang === l);
      const list = all.some(i => !i.marked) ? all.filter(i => !i.marked) : all;
      list.filter(i => !isFemTwin(i, list)).slice(0, ti ? 1 : 2).forEach(i => wanted.push({ t, l, i }));
    }));
    const enrichP = (async () => {
      await pagesWikitext([...new Set(wanted.map(x => x.i.word))]).catch(() => {});   // one batch request
      const wordCache = new Map();
      return pool(wanted, 8, x => {
        const k = `${x.l}:${x.i.word}`;
        if (!wordCache.has(k)) wordCache.set(k, romanceWord(x.l, x.i, x.t.pos));
        return wordCache.get(k).then(w => ({ ...w, ...(x.i.v ? { v: x.i.v } : {}) }));
      });
    })();
    sec.html = await htmlP;
    const blocks = htmlBlocks(sec.html);
    const multiEty = blocks.filter(b => /^Etymology \d+$/.test(b.title)).length > 1;
    const wikiEtys = headingBlocks(sec.wikitext).filter(b => /^Etymology/.test(b.title));
    const ety = [];
    const pos = [];
    let e = -1;
    let syn = [], ant = [], phr = [];
    const pronEls = [];
    for (const b of blocks) {
      if (/^Etymology/.test(b.title)) {
        const wb = wikiEtys[ety.length];
        const r = etymologyFrom(b.els, wb ? wb.body : '', 'en');
        ety.push({ n: ety.length + 1, chain: r.chain, text: r.text, ...(r.unc ? { unc: true } : {}),
          ...(r.cog && r.cog.length ? { cog: r.cog } : {}), ...(r.form ? { form: r.form } : {}) });
        e = ety.length - 1;
      } else if (/^Pronunciation/.test(b.title)) {
        pronEls.push(...b.els);
      } else if (POS_HEADINGS[b.title] && POS_HEADINGS[b.title] !== 'name') {
        const ol = b.els.find(el => el.tagName === 'OL');
        const senses = ol ? sensesFrom(ol) : [];
        if (!senses.length) continue;
        const block = { p: POS_HEADINGS[b.title], e: Math.max(0, multiEty ? e : 0), senses };
        const forms = headwordForms(b.els);
        if (forms.length) block.forms = forms;
        pos.push(block);
      } else if (/^Synonyms/.test(b.title)) syn = syn.concat(linkWords(b.els));
      else if (/^Antonyms/.test(b.title)) ant = ant.concat(linkWords(b.els));
      else if (/^(Derived terms|Related terms|Idioms|Phrases)/.test(b.title)) phr = phr.concat(linkWords(b.els));
    }
    if (!pos.length) return { formOf: formOfTarget(sec.wikitext, 'en'), title: sec.title };
    if (!ety.length) ety.push({ n: 1, chain: [], text: '' });
    const ipa = ipaFrom(pronEls);
    const entry = { w: sec.title, zh: [], ipa: {}, ety: ety.map(x => ({ ...x, chain: x.chain })), pos, grp: [], live: true };
    if (ipa.uk || ipa.any) entry.ipa.uk = ipa.uk || ipa.any;
    if (ipa.us || ipa.any) entry.ipa.us = ipa.us || ipa.any;

    // order rows like the senses they translate
    const bestSense = t => {
      let best = [9, 99, 0];
      pos.forEach((b, bi) => b.senses.forEach((s, si) => {
        const sc = (t.pos && b.p !== t.pos) ? -1 : score(t.label, s.d);
        if (sc > best[2] || (sc === best[2] && bi * 100 + si < best[0] * 100 + best[1] && sc >= 0)) best = [bi, si, sc];
      }));
      return best;
    };
    tables.forEach(t => { t._best = bestSense(t); });
    // row 1 = main meaning (the most-translated table of the first POS), then by sense
    const size = t => t.items.filter(i => ROMANCE.includes(i.lang) || i.lang === 'zh').length;
    const firstBlock = Math.min(...tables.map(t => t._best[0]));
    const firsts = tables.filter(t => t._best[0] === firstBlock);
    const s0 = t => (pos[firstBlock] && pos[firstBlock].senses[0] ? score(t.label, pos[firstBlock].senses[0].d) : 0);
    const bySense = firsts.slice().sort((a, b) => s0(b) - s0(a) || a._order - b._order)[0];
    const main = bySense && s0(bySense) >= 0.34 ? bySense : firsts.sort((a, b) => size(b) - size(a) || a._order - b._order)[0];
    tables.sort((a, b) => (a !== main) - (b !== main) || a._best[0] - b._best[0] || a._best[1] - b._best[1] || a._order - b._order);

    const enriched = await enrichP;
    // continue every chain to its oldest attested ancestor, in batched requests; this
    // runs after the entry is returned (second phase) and mutates the chains in place
    const chains = entry.ety.map(x => x.chain).concat(enriched.filter(Boolean).map(w => (w.ety ? w.ety.chain : null)).filter(Boolean));
    entry.langNames = liveNames;
    const pending = extendChains([...new Set(chains)]).catch(() => {});
    tables.forEach((t, gi) => {
      const tr = {};
      ROMANCE.forEach(l => { tr[l] = []; });
      wanted.forEach((x, k) => { if (x.t === t && enriched[k]) tr[x.l].push(enriched[k]); });
      const zh = [...new Set(t.items.filter(i => i.lang === 'zh').map(i => i.word.split('/')[0].trim()))].slice(0, 4);
      const b = pos[t._best[0]] || pos[0];
      entry.grp.push({ label: t.label, zh, p: t.pos || b.p, e: b.e, tr });
      zh.forEach(z => { if (!entry.zh.includes(z)) entry.zh.push(z); });
      const s = b.senses[t._best[1]];
      if (s && s.grp === undefined) { s.grp = gi; if (zh.length) s.zh = zh.slice(0, 3).join('；'); }
    });
    if (!entry.grp.length) {
      entry.grp.push({ label: '', zh: [], p: pos[0].p, e: pos[0].e, tr: { it: [], pt: [], fr: [], es: [] } });
    }
    const uniq = (arr, n) => [...new Set(arr.filter(x => x && x !== entry.w))].slice(0, n);
    if (syn.length) entry.syn = uniq(syn, 10);
    if (ant.length) entry.ant = uniq(ant, 8);
    if (phr.length) entry.phr = uniq(phr, 16);
    entry.zh = entry.zh.slice(0, 5);
    return { entry, pending };
  }

  /* ---------------------------------------------- form-of & glosses */
  function formOfTarget(wikitext, lang) {
    for (const line of wikitext.split('\n')) {
      if (!/^#(?![:*])/.test(line)) continue;
      const ts = templates(line);
      const fo = ts.find(t => FORM_OF_RE.test(t.name) || /\bof$/.test(t.name));
      if (fo) {
        const lemma = fo.name === 'zh-see' ? fo.args['1'] : (fo.args['2'] || '').replace(/\[\[|\]\]/g, '');
        if (lemma) {
          // inflection tags use Wiktionary abbreviations: spast, past|ptcp, pres|ptcp, 3|s|pres, p, ...
          const tags = new Set(Object.keys(fo.args).filter(k => /^\d+$/.test(k) && +k >= 4)
            .flatMap(k => fo.args[k].split(/[|\s/]+/)).map(x => x.toLowerCase()));
          const nm = fo.name.replace(/^en-/, '');
          let code = 'form';
          if (/past participle/.test(nm) || (tags.has('ptcp') && (tags.has('past') || tags.has('perf')))) code = 'pp';
          else if (/present participle|ing form/.test(nm) || (tags.has('ptcp') && tags.has('pres')) || tags.has('ger')) code = 'ing';
          else if (/past/.test(nm) || tags.has('spast') || tags.has('past') || tags.has('pret')) code = tags.has('3') && tags.has('s') && tags.has('pret') ? 'pret3s' : 'past';
          else if (/third-person/.test(nm) || (tags.has('3') && tags.has('s') && tags.has('pres'))) code = '3s';
          else if (/comparative/.test(nm) || tags.has('comd') || tags.has('comparative')) code = 'comp';
          else if (/superlative/.test(nm) || tags.has('supd') || tags.has('superlative')) code = 'sup';
          else if (/feminine plural/.test(nm) || (tags.has('f') && tags.has('p'))) code = 'fpl';
          else if (/plural/.test(nm) || tags.has('p') || tags.has('pl')) code = 'pl';
          else if (/feminine/.test(nm) || tags.has('f')) code = 'f';
          else if (tags.has('acc')) code = 'acc';
          return { lemma, code, lang };
        }
      }
      return null;
    }
    return null;
  }
  function englishGlosses(wikitext) {
    const out = [];
    for (const line of wikitext.split('\n')) {
      if (!/^#(?![:*])/.test(line)) continue;
      const cleaned = line.replace(/\{\{(?:lb|lbl|label|senseid|q|qual|qualifier|i|gloss|defdate|tlb)\|[^{}]*\}\}/g, '');
      const l = cleaned.match(/\{\{l\|en\|([^|}]+)/);
      const link = cleaned.match(/\[\[([^\]|#]+)(?:#English)?(?:\|[^\]]*)?\]\]/);
      const w = (l && l[1]) || (link && link[1]);
      if (w && /^[A-Za-z][A-Za-z' -]*$/.test(w.trim()) && !out.includes(w.trim())) out.push(w.trim());
      if (out.length >= 4) break;
    }
    return out;
  }

  /* ------------------------------------------------------ lookup */
  const results = new Map();
  /**
   * lookup(query) -> {entry, hits} | {suggestions:[{f,h}]} | null
   */
  function lookup(query) {
    const q = String(query || '').trim();
    if (!q) return Promise.resolve(null);
    if (!results.has(q)) {
      const p = doLookup(q);
      results.set(q, p);
      p.catch(() => results.delete(q));
    }
    return results.get(q);
  }
  async function doLookup(q) {
    const titles = [...new Set([q, q.toLowerCase()])];
    const hasTr = e => e.grp.some(g => ROMANCE.some(l => (g.tr[l] || []).length));
    let enFallback = null;
    for (const title of titles) {
      // 1) English headword (or English inflected form such as "went")
      const en = await englishEntry(title).catch(err => { if (/HTTP|Failed to fetch|NetworkError/i.test(String(err))) throw err; return null; });
      let found = null;
      if (en && en.entry) found = { entry: en.entry, pending: en.pending, hits: [{ h: en.entry.w, l: 'en', f: q, r: 'hw' }] };
      if (en && en.formOf && en.formOf.lemma) {
        const lemma = await englishEntry(en.formOf.lemma).catch(() => null);
        if (lemma && lemma.entry) found = { entry: lemma.entry, pending: lemma.pending, hits: [{ h: lemma.entry.w, l: 'en', f: q, r: 'inf', m: lemma.entry.w, t: en.formOf.code }] };
      }
      const page = await pageText(title);
      const names = page ? l2Names(page.content) : [];
      const romanceHere = names.some(n => ['Italian', 'Portuguese', 'French', 'Spanish'].includes(n));
      // an English loanword without translations ("manzana") should not hide the Romance word
      if (found && (hasTr(found.entry) || !romanceHere)) return found;
      enFallback = enFallback || found;
      // 2) a Romance or Chinese word: follow its English gloss
      if (!page) continue;
      for (const lang of ['fr', 'it', 'es', 'pt', 'zh']) {
        if (!names.includes(LANG_SECTION[lang])) continue;
        let sec = await langSection(page.title, LANG_SECTION[lang], false);
        if (!sec) continue;
        let hit = { l: lang, f: q, r: 'tr' };
        const fo = formOfTarget(sec.wikitext, lang);
        if (fo && fo.lemma) {
          const lemSec = await langSection(fo.lemma, LANG_SECTION[lang], false);
          if (lemSec) { sec = lemSec; hit = fo.lemma === q ? hit : { l: lang, f: q, r: lang === 'zh' ? 'zh' : 'trinf', m: fo.lemma, t: fo.code }; }
        }
        if (lang === 'zh' && hit.r === 'tr') hit.r = 'zh';
        for (const cand of englishGlosses(sec.wikitext)) {
          const r = await englishEntry(cand).catch(() => null);
          if (r && r.entry) return { entry: r.entry, pending: r.pending, hits: [{ ...hit, h: r.entry.w }] };
        }
      }
    }
    if (enFallback) return enFallback;
    // 3) nothing: offer Wiktionary's own title suggestions
    const os = await api({ action: 'opensearch', search: q, limit: '8', namespace: '0' }).catch(() => null);
    const titlesFound = Array.isArray(os) ? (os[1] || []) : [];
    return { suggestions: titlesFound.filter(t => t !== q).map(t => ({ f: t, h: t })) };
  }

  window.PentaLive = { lookup, _internals: { templates, headingBlocks, treeChain, translationTables, formOfTarget, englishGlosses } };
})();
