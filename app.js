/* 羅曼多語言字典 — app.js
 * Vanilla JavaScript, no build step. Loads sharded JSON from data/ (see README.md).
 */
'use strict';
(() => {
  const DATA = 'data/';
  const ROMANCE = ['fr', 'it', 'es', 'pt'];          // display order: Français | Italiano | Español | Português
  const LEAF_ORDER = ['en', 'fr', 'it', 'es', 'pt'];
  const KEY = 'pentadict.';
  const MAX_HISTORY = 30;
  const RANK = { hw: 0, inf: 1, tr: 2, zh: 3, trinf: 4 };
  const WIKT_ANCHOR = { en: 'English', it: 'Italian', pt: 'Portuguese', fr: 'French', es: 'Spanish' };
  const NATIVE = { en: 'English', it: 'Italiano', pt: 'Português', fr: 'Français', es: 'Español' };
  const TTS = { it: 'it-IT', fr: 'fr-FR', es: 'es-ES', pt: { PT: 'pt-PT', BR: 'pt-BR' } };
  const EXAMPLES = ['night', 'summer', 'water', 'bank', 'go', 'été', '夏天', 'notti', 'went', 'cafe', 'fue', 'brother', 'coffee', 'eat'];

  /* ------------------------------------------------------------------ i18n */
  const LANG_UI = {
    en: ['英語', 'English'], it: ['義大利語', 'Italian'], pt: ['葡萄牙語', 'Portuguese'],
    fr: ['法語', 'French'], es: ['西班牙語', 'Spanish'], zh: ['中文', 'Chinese'],
  };
  const POS = {
    noun: ['名詞', 'noun'], verb: ['動詞', 'verb'], adj: ['形容詞', 'adjective'], adv: ['副詞', 'adverb'],
    num: ['數詞', 'numeral'], pron: ['代名詞', 'pronoun'], prep: ['介系詞', 'preposition'],
    conj: ['連接詞', 'conjunction'], intj: ['感嘆詞', 'interjection'], det: ['限定詞', 'determiner'],
    article: ['冠詞', 'article'], particle: ['小品詞', 'particle'], phrase: ['片語', 'phrase'],
    name: ['專有名詞', 'proper noun'], prefix: ['字首', 'prefix'], suffix: ['字尾', 'suffix'],
    abbrev: ['縮寫', 'abbreviation'],
  };
  const FORMS = {
    pl: ['複數', 'plural'], past: ['過去式', 'past'], pp: ['過去分詞', 'past participle'],
    ing: ['現在分詞', 'present participle'], '3s': ['第三人稱單數', '3rd person sg.'],
    '1s': ['第一人稱單數現在式', '1st person sg. present'], comp: ['比較級', 'comparative'],
    sup: ['最高級', 'superlative'], f: ['陰性形', 'feminine'], fpl: ['陰性複數', 'feminine plural'],
    mpl: ['陽性複數', 'masculine plural'], pret3s: ['第三人稱單數過去式', '3rd sg. preterite'],
    impf3s: ['第三人稱單數未完成過去式', '3rd sg. imperfect'], presp: ['現在式複數', 'present plural'],
    pastpl: ['過去式複數', 'past plural'], inf: ['不定式', 'infinitive'], form: ['變化形', 'inflected form'],
  };
  const CASES = {
    acc: ['賓格', 'accusative'], gen: ['屬格', 'genitive'], abl: ['奪格', 'ablative'], dat: ['與格', 'dative'],
    nom: ['主格', 'nominative'], accpl: ['賓格複數', 'accusative plural'], nompl: ['主格複數', 'nominative plural'],
    genpl: ['屬格複數', 'genitive plural'], ablpl: ['奪格複數', 'ablative plural'], pl: ['複數', 'plural'],
    inf: ['不定式', 'infinitive'], ppr: ['現在分詞', 'present participle'], ppf: ['完成分詞', 'perfect participle'],
  };
  const TAGS = {
    informal: '非正式', formal: '正式', colloquial: '口語', slang: '俚語', vulgar: '粗俗', offensive: '冒犯',
    derogatory: '貶義', humorous: '幽默', euphemistic: '委婉', figurative: '比喻', literary: '文學',
    poetic: '詩歌', archaic: '古語', dated: '過時', obsolete: '已廢', rare: '罕用', historical: '歷史',
    British: '英式', US: '美式', Canada: '加拿大', Australia: '澳洲', Ireland: '愛爾蘭', Scotland: '蘇格蘭',
    India: '印度', impersonal: '無人稱', transitive: '及物', intransitive: '不及物', uncountable: '不可數',
    countable: '可數', idiomatic: '慣用', technical: '術語', computing: '電腦', chess: '西洋棋', law: '法律',
    medicine: '醫學', mathematics: '數學', music: '音樂', sports: '運動', finance: '金融', business: '商業',
    biology: '生物', chemistry: '化學', physics: '物理', nautical: '航海', military: '軍事',
  };
  const REGISTER = new Set(['informal', 'formal', 'colloquial', 'slang', 'vulgar', 'offensive', 'derogatory',
    'humorous', 'euphemistic', 'archaic', 'dated', 'obsolete', 'rare', 'literary', 'poetic']);
  const REGION = new Set(['British', 'US', 'Canada', 'Australia', 'Ireland', 'Scotland', 'India']);

  const I18N = {
    zh: {
      appName: '羅曼多語言字典', skip: '跳至主要內容', searchLabel: '搜尋單字', searchBtn: '查詢',
      placeholder: '輸入任一語言的單字…',
      heroTitle: '一個字，<span>五種語言</span>，一條詞源。',
      tagline: '輸入中文、英文、法文、義大利文、西班牙文或葡萄牙文，一次看到完整英文詞條、四種羅曼語對照，以及它們的詞源與同源關係。',
      tryThese: '試試看', history: '搜尋紀錄', favorites: '我的收藏', clear: '清除',
      noHistory: '還沒有搜尋紀錄。', noFavorites: '尚未收藏任何單字。在詞條右上角點 ☆ 即可收藏。',
      howTitle: '怎麼用',
      how: [
        '可以輸入中文、英文、法文、義大利文、西班牙文或葡萄牙文；大小寫與重音符號都可省略（cafe 會找到 café）。',
        '會辨認變化形：went → go、notti → notte；像 été 這種同形詞會同時列出「summer」與「être 的過去分詞」。',
        '英文有多個詞義時（例如 bank：銀行／河岸），四種語言依詞義逐列對齊。',
        '詞源區以「←」串起祖先詞，並畫出同源家族樹：同一棵樹的詞同出一源，分開的樹則各有來歷。',
        '點任何譯詞或祖先詞形即可再查詢；🔊 使用瀏覽器內建語音朗讀。',
      ],
      themeToDark: '切換為深色模式', themeToLight: '切換為淺色模式', uiSwitch: 'Switch interface to English',
      uiSwitchShort: 'EN',
      loading: '載入中…', found: w => `已顯示「${w}」的詞條`,
      notFound: q => `找不到「${q}」`, didYouMean: '您要找的是不是：', noSuggest: '沒有相近的詞。請確認拼字，或改用英文原形查詢。',
      searchWiktionary: q => `到維基詞典搜尋「${q}」`,
      netError: '資料載入失敗，請檢查網路連線後再試一次。', retry: '重新載入',
      fileHint: '看起來您是直接以檔案開啟本頁（file://），瀏覽器會阻擋讀取資料。請在專案資料夾執行 python -m http.server 8000，再開啟 http://localhost:8000/。',
      queryIs: q => `查詢「${q}」：`, alsoMaybe: '也可能是：',
      viaInf: (f, form, m) => `「${f}」是英語 ${m} 的${form}。`,
      viaTr: (f, L, h) => `「${f}」是${L}，對應英語 ${h}。`,
      viaZh: (f, h) => `「${f}」對應英語 ${h}。`,
      viaTrinf: (f, L, m, form, h) => `「${f}」是${L} ${m} 的${form}，對應英語 ${h}。`,
      pronUK: '英式', pronUS: '美式', play: (w, L) => `播放「${w}」的${L}發音`,
      noTTS: '此瀏覽器不支援語音朗讀。', noVoice: loc => `找不到 ${loc} 的語音，將以預設語音朗讀。`,
      favAdd: '加入收藏', favRemove: '取消收藏', favAdded: w => `已收藏 ${w}`, favRemoved: w => `已取消收藏 ${w}`,
      forms: '詞形變化', synonyms: '同義詞', antonyms: '反義詞', phrases: '常見搭配與片語', ety: '詞源',
      source: '原始詞條', example: '例句', senseSyn: '近義：',
      translations: '羅曼語對照', translationsSub: '依英文詞義逐列對齊',
      ptVariant: '葡萄牙語', ptPT: '歐洲 PT', ptBR: '巴西 BR', langTabs: '選擇語言',
      missingTr: '此語言暫無對應翻譯資料', missingEty: '詞源資料未收錄', uncertain: '來源不確定',
      plural: '複數', feminine: '陰性形', variantBR: '巴西用法', variantPT: '葡萄牙用法',
      gender: { m: ['陽性', 'masculine'], f: ['陰性', 'feminine'], mf: ['陰陽同形', 'masculine or feminine'] },
      etymology: '詞源與同源詞', etymologySub: '以 ← 表示「源自」', chains: '詞源鏈', tree: '同源家族樹',
      treeHint: '樹根為共同祖先，葉節點為現代詞；窄螢幕可左右捲動。', treeLabel: n => `${n}的同源家族樹`,
      cognates: '同源詞 / Cognates', noCognates: '無共同祖源 / No shared root',
      groupN: g => `同源組 ${g}`, noGroup: '獨立來源', summaryLabel: '中文摘要', otherCogs: '其他語言同源詞：',
      expand: '展開詞源', collapse: '收合詞源', original: '原文（英文）', from: '源自',
      sameAs: '（與上方詞義相同）', langOf: (L, w) => `${L} ${w}`,
      caseOf: (lm, c) => `（${lm} 的${c}）`, seeLemma: lm => `（見 ${lm}）`,
      sumEn: (w, first, last) => `英語「${w}」源自${first}${last ? `，最早可追溯至${last}` : ''}。`,
      sumGroup: (names, lca, root) => `${names}彼此同源，最近的共同祖先是${lca}${root ? `，更早可追溯至${root}` : ''}。`,
      sumSub: (names, n) => `其中${names}更直接地同出於${n}。`,
      sumSingles: names => `${names}與其他詞沒有共同祖源，各有不同來歷。`,
      sumNone: '這幾個詞彼此並非同源詞，各有不同來歷。',
      sumMissing: names => `（${names}的詞源資料未收錄。）`,
      nameFmt: (L, w) => `${L}「${w}」`, nodeFmt: (L, f, g) => `${L}「${f}」${g ? `（“${g}”）` : ''}`,
      listJoin: '、', dataset: (n, d, src) => `資料集：${n} 個英文詞條 · 建置日期 ${d} · 來源 ${src === 'sample' ? '範例資料' : 'Kaikki.org'}`,
      retryFor: q => `重新查詢「${q}」`,
      liveLoading: q => `本地詞庫沒有「${q}」，正在向維基詞典即時查詢…`,
      liveNotice: '此詞條由維基詞典即時取得，未經預先整理：部分複數、發音或詞源可能缺漏，翻譯僅列出前幾個。',
      liveOpen: '在維基詞典查看原始頁面',
      liveSuggest: '維基詞典上的相近詞：',
      formedFrom: '構詞：',
      etyLoading: '正在追溯更早的祖先…',
      secCollapse: '收合', secExpand: '展開', englishEntry: '英語詞條',
      alsoSense: '同一組譯詞也用於此義', etyN: n => `詞源 ${n}`, etyRows: s => `對照第 ${s} 列`,
    },
    en: {
      appName: 'Romance Multilingual Dictionary', skip: 'Skip to main content', searchLabel: 'Search a word', searchBtn: 'Search',
      placeholder: 'Type a word in Chinese, EN, IT, PT, FR or ES…',
      heroTitle: 'One word, <span>five languages</span>, one story.',
      tagline: 'Search in Chinese, English, French, Italian, Spanish or Portuguese to see the full English entry, its Romance-language equivalents side by side, and how they are related.',
      tryThese: 'Try these', history: 'History', favorites: 'Favorites', clear: 'Clear',
      noHistory: 'No searches yet.', noFavorites: 'No favorites yet. Tap ☆ next to a headword to save it.',
      howTitle: 'How it works',
      how: [
        'Search in Chinese, English, French, Italian, Spanish or Portuguese; case and accents are ignored (cafe finds café).',
        'Inflected forms are recognised: went → go, notti → notte; ambiguous forms such as été list both “summer” and “past participle of être”.',
        'When an English word has several meanings (bank: money / river), the four languages are aligned row by row.',
        'Etymologies are shown as ← chains plus a cognate family tree: words in the same tree share an ancestor, separate trees do not.',
        'Click any translation or ancestral form to search it; 🔊 uses your browser’s speech synthesis.',
      ],
      themeToDark: 'Switch to dark mode', themeToLight: 'Switch to light mode', uiSwitch: '切換為中文介面',
      uiSwitchShort: '中',
      loading: 'Loading…', found: w => `Showing the entry for “${w}”`,
      notFound: q => `No results for “${q}”`, didYouMean: 'Did you mean:', noSuggest: 'No close matches. Check the spelling or try the English base form.',
      searchWiktionary: q => `Search Wiktionary for “${q}”`,
      netError: 'Could not load the dictionary data. Check your connection and try again.', retry: 'Retry',
      fileHint: 'It looks like this page was opened directly as a file (file://), so the browser blocks the data files. Run python -m http.server 8000 in the project folder and open http://localhost:8000/.',
      queryIs: q => `“${q}”: `, alsoMaybe: 'It may also be:',
      viaInf: (f, form, m) => `“${f}” is the ${form} of English ${m}.`,
      viaTr: (f, L, h) => `“${f}” is ${L} for English ${h}.`,
      viaZh: (f, h) => `“${f}” corresponds to English ${h}.`,
      viaTrinf: (f, L, m, form, h) => `“${f}” is the ${form} of ${L} ${m}, i.e. English ${h}.`,
      pronUK: 'UK', pronUS: 'US', play: (w, L) => `Play ${L} pronunciation of “${w}”`,
      noTTS: 'Speech synthesis is not supported in this browser.', noVoice: loc => `No ${loc} voice installed; using the default voice.`,
      favAdd: 'Add to favorites', favRemove: 'Remove from favorites', favAdded: w => `Saved ${w}`, favRemoved: w => `Removed ${w}`,
      forms: 'Inflections', synonyms: 'Synonyms', antonyms: 'Antonyms', phrases: 'Collocations & phrases', ety: 'Etymology',
      source: 'Source entry', example: 'Example', senseSyn: 'Synonyms: ',
      translations: 'Romance equivalents', translationsSub: 'aligned by English sense',
      ptVariant: 'Portuguese', ptPT: 'Europe PT', ptBR: 'Brazil BR', langTabs: 'Choose a language',
      missingTr: 'No translation data for this language', missingEty: 'No etymology data', uncertain: 'uncertain',
      plural: 'pl.', feminine: 'fem.', variantBR: 'Brazil', variantPT: 'Portugal',
      gender: { m: ['masc.', 'masculine'], f: ['fem.', 'feminine'], mf: ['m./f.', 'masculine or feminine'] },
      etymology: 'Etymology & cognates', etymologySub: '← means “from”', chains: 'Etymology chains', tree: 'Cognate family tree',
      treeHint: 'Roots are shared ancestors, leaves are modern words; scroll sideways on small screens.', treeLabel: n => `Cognate tree for ${n}`,
      cognates: '同源詞 / Cognates', noCognates: '無共同祖源 / No shared root',
      groupN: g => `Group ${g}`, noGroup: 'Separate origin', summaryLabel: 'Summary', otherCogs: 'Cognates elsewhere: ',
      expand: 'Show full etymology', collapse: 'Hide full etymology', original: 'Original (English)', from: 'from',
      sameAs: '(same as above)', langOf: (L, w) => `${L} ${w}`,
      caseOf: (lm, c) => ` (${c} of ${lm})`, seeLemma: lm => ` (see ${lm})`,
      sumEn: (w, first, last) => `English “${w}” comes from ${first}${last ? `, ultimately from ${last}` : ''}.`,
      sumGroup: (names, lca, root) => `${names} are cognates; their closest common ancestor is ${lca}${root ? `, going back further to ${root}` : ''}.`,
      sumSub: (names, n) => `Of these, ${names} come more directly from ${n}.`,
      sumSingles: names => `${names} ${names.includes(',') || names.includes(' and ') ? 'have' : 'has'} no shared ancestor with the others.`,
      sumNone: 'None of these words share an ancestor; each has its own history.',
      sumMissing: names => `(No etymology data for ${names}.)`,
      nameFmt: (L, w) => `${L} ${w}`, nodeFmt: (L, f, g) => `${L} ${f}${g ? ` (“${g}”)` : ''}`,
      listJoin: ', ', dataset: (n, d, src) => `Dataset: ${n} English headwords · built ${d} · source ${src === 'sample' ? 'bundled sample' : 'Kaikki.org'}`,
      retryFor: q => `Retry “${q}”`,
      liveLoading: q => `“${q}” is not in the offline dataset — looking it up on Wiktionary…`,
      liveNotice: 'This entry was fetched live from Wiktionary and has not been curated: some plurals, pronunciations or etymologies may be missing, and only the first translations are shown.',
      liveOpen: 'Open the source page on Wiktionary',
      liveSuggest: 'Close matches on Wiktionary:',
      formedFrom: 'formed from',
      etyLoading: 'Tracing older ancestors…',
      secCollapse: 'Collapse', secExpand: 'Expand', englishEntry: 'English entry',
      alsoSense: 'The same words are also used for this sense', etyN: n => `Etymology ${n}`, etyRows: s => `rows ${s}`,
    },
  };

  /* ---------------------------------------------------------------- utils */
  const store = {
    get(k, d) { try { const v = localStorage.getItem(KEY + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(KEY + k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ } },
  };
  const state = {
    ui: store.get('ui', 'zh') === 'en' ? 'en' : 'zh',
    pt: store.get('pt', 'PT') === 'BR' ? 'BR' : 'PT',
    tab: ROMANCE.includes(store.get('tab', 'fr')) ? store.get('tab', 'fr') : 'fr',
    meta: null, words: [], wordZh: new Map(), wordsReady: null, metaReady: null,
    view: { type: 'home' }, seq: 0,
    collapsed: (() => { const c = store.get('collapsed', {}); return c && typeof c === 'object' ? c : {}; })(),
  };
  const $ = sel => document.querySelector(sel);
  const main = $('#main');
  const input = $('#q');
  const suggestEl = $('#suggest');

  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const t = (k, ...a) => {
    const v = I18N[state.ui][k] !== undefined ? I18N[state.ui][k] : I18N.zh[k];
    return typeof v === 'function' ? v(...a) : (v === undefined ? k : v);
  };
  const uiIdx = () => (state.ui === 'zh' ? 0 : 1);
  // Chinese names for languages that commonly appear in etymologies (English names
  // come from meta.json or, for live entries, from Wiktionary's own tree data).
  const ETY_ZH = {
    enm: '中古英語', ang: '古英語', xno: '盎格魯-諾曼語', 'gem-pro': '原始日耳曼語', 'gmw-pro': '原始西日耳曼語',
    'ine-pro': '原始印歐語', 'itc-pro': '原始義大利語族語', la: '拉丁語', 'la-lat': '後期拉丁語', 'la-vul': '通俗拉丁語',
    'la-med': '中世紀拉丁語', 'la-eme': '早期中世紀拉丁語', 'la-new': '新拉丁語', 'la-ecc': '教會拉丁語', 'la-cla': '古典拉丁語', 'la-ear': '早期拉丁語', 'itc-ola': '古拉丁語', grc: '古希臘語',
    'grc-koi': '通用希臘語', el: '希臘語', 'roa-oit': '古義大利語', 'roa-opt': '古加利西亞-葡萄牙語', gl: '加利西亞語',
    fro: '古法語', frm: '中古法語', osp: '古西班牙語', ca: '加泰隆尼亞語', oc: '奧克語', pro: '古奧克語', ro: '羅馬尼亞語',
    frk: '法蘭克語', lng: '倫巴底語', got: '哥德語', non: '古諾斯語', de: '德語', gmh: '中古高地德語', goh: '古高地德語',
    nl: '荷蘭語', dum: '中古荷蘭語', gml: '中古低地德語', sv: '瑞典語', da: '丹麥語', is: '冰島語', ru: '俄語',
    'cel-pro': '原始凱爾特語', 'sla-pro': '原始斯拉夫語', 'grk-pro': '原始希臘語', ar: '阿拉伯語', ota: '鄂圖曼土耳其語',
    tr: '土耳其語', fa: '波斯語', pal: '中古波斯語', sa: '梵語', he: '希伯來語', hbo: '古希伯來語', arc: '亞拉姆語',
    'sem-pro': '原始閃米特語', egy: '古埃及語', ja: '日語', cmn: '華語', nah: '納瓦特爾語', qu: '克丘亞語', ga: '愛爾蘭語',
    cy: '威爾斯語', br: '布列塔尼語', sco: '蘇格蘭語', fy: '西菲士蘭語', yi: '意第緒語', hi: '印地語', ms: '馬來語',
  };
  const langName = code => {
    if (LANG_UI[code]) return LANG_UI[code][uiIdx()];
    const m = state.meta && state.meta.langs && state.meta.langs[code];
    const live = state.view && state.view.entry && state.view.entry.langNames && state.view.entry.langNames[code];
    if (state.ui === 'zh') return ETY_ZH[code] || (m && m.zh !== m.en ? m.zh : null) || (m && m.en) || live || code;
    return (m && m.en) || live || code;
  };
  const posLabel = p => (POS[p] ? POS[p][uiIdx()] : (p || ''));
  const formLabel = c => (FORMS[c] ? FORMS[c][uiIdx()] : String(c || '').replace(/[+_-]/g, ' '));
  const caseLabel = c => (CASES[c] ? CASES[c][uiIdx()] : c);
  const tagLabel = tg => (state.ui === 'zh' && TAGS[tg] ? TAGS[tg] : tg);
  const joinList = arr => arr.join(t('listJoin'));

  /** Normalization — must stay identical to norm() in tools/build_dataset.py */
  function norm(s) {
    return String(s || '').trim().toLowerCase()
      .replace(/œ/g, 'oe').replace(/æ/g, 'ae').replace(/ß/g, 'ss').replace(/’/g, "'")
      .normalize('NFKD').replace(/\p{M}/gu, '').replace(/\s+/g, ' ');
  }
  const akey = f => norm(String(f || '').replace(/^\*/, ''));
  function idxBucket(key) {
    const cp = key.codePointAt(0);
    if (cp >= 97 && cp <= 122) {
      const second = key.length > 1 && key[1] >= 'a' && key[1] <= 'z' ? key[1] : '_';
      return String.fromCharCode(cp) + second;
    }
    if (cp >= 48 && cp <= 57) return '0';
    return 'x' + (cp % 32).toString(16).padStart(2, '0');
  }
  /** Windows cannot store device names (con.json, aux.json...): such shards end in "_". */
  const safeName = b => (/^(con|prn|aux|nul|com[0-9]|lpt[0-9])$/.test(b) ? `${b}_` : b);
  function entBucket(hw) {
    const len = (state.meta && state.meta.entryPrefixLen) || 2;
    const chars = Array.from(norm(hw)).slice(0, len).map(ch => (/[a-z]/.test(ch) ? ch : '_'));
    return safeName(chars.join('').padEnd(len, '_'));
  }
  const stripStar = f => String(f || '').replace(/^\*/, '');
  const hitRank = (a, b) => (RANK[a.r] ?? 9) - (RANK[b.r] ?? 9);

  function lev(a, b, max) {
    const m = a.length, n = b.length;
    if (Math.abs(m - n) > max) return max + 1;
    let prev = Array.from({ length: n + 1 }, (_, j) => j);
    for (let i = 1; i <= m; i++) {
      const cur = [i];
      let best = i;
      for (let j = 1; j <= n; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (cur[j] < best) best = cur[j];
      }
      if (best > max) return max + 1;
      prev = cur;
    }
    return prev[n];
  }

  /* --------------------------------------------------------------- icons */
  const ICON = {
    speaker: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z" fill="currentColor"/><path d="M16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    star: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6-5.4-2.9-5.4 2.9 1.1-6L3.2 9.4l6.1-.8L12 3Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    starOn: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6-5.4-2.9-5.4 2.9 1.1-6L3.2 9.4l6.1-.8L12 3Z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
    ext: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    chevron: '<svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 5 5 9-10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };

  /* ---------------------------------------------------------------- data */
  const cache = new Map();
  function getJSON(path, optional) {
    if (cache.has(path)) return cache.get(path);
    const p = fetch(DATA + path).then(r => {
      if (r.status === 404 && optional) return {};
      if (!r.ok) throw new Error(`HTTP ${r.status} ${path}`);
      return r.json();
    });
    cache.set(path, p);
    p.catch(() => cache.delete(path));
    return p;
  }
  async function loadIndex(key) {
    const bucket = idxBucket(key);
    try { await state.metaReady; } catch (e) { /* meta.json is optional */ }
    const known = state.meta && state.meta.indexShards;
    if (Array.isArray(known) && !known.includes(bucket)) return {};
    return getJSON(`index/${bucket}.json`, true);
  }
  /** Index hits are stored as [h, l, f, r, gi] or [h, l, f, r, m, t]. */
  function decodeHit(a) {
    if (!Array.isArray(a)) return a;
    const hit = { h: a[0], l: a[1], f: a[2], r: a[3] };
    if (typeof a[4] === 'number') hit.gi = a[4];
    else if (a.length > 4) { hit.m = a[4]; hit.t = a[5]; }
    return hit;
  }
  const hitsOf = (idx, key) => ((idx && idx[key]) || []).map(decodeHit);
  async function loadEntry(hw) {
    const shard = await getJSON(`entries/${entBucket(hw)}.json`, false);
    return expandEntry(shard[hw] || null);
  }
  /** Rows refer to Romance words stored once per entry in `lx` ("it:notte"); resolve them. */
  function expandEntry(e) {
    if (!e) return e;
    if (e.lx && !e._expanded) {
      (e.grp || []).forEach(g => ROMANCE.forEach(l => {
        g.tr[l] = (g.tr[l] || []).map(k => (typeof k === 'string' ? (e.lx[k] || { w: k.split(':').slice(1).join(':').split('|')[0] }) : k));
      }));
      e._expanded = true;
    }
    return mergeRows(e);
  }
  /**
   * Wiktionary splits English senses finely (bank: institution / branch office / ...), and
   * the Romance languages often use exactly the same words for several of them. Rows whose
   * four word lists are identical (same part of speech and English etymology) are merged
   * into one; the merged sense labels are kept as tags. Rows that differ in any word stay.
   */
  function mergeRows(e) {
    if (!e || e._merged) return e;
    const sig = g => [g.p || '', g.e || 0, ...ROMANCE.map(l => ((g.tr && g.tr[l]) || [])
      .map(w => w.w + (w.v ? `|${w.v}` : '')).sort().join(','))].join('#');
    const out = [];
    const map = [];
    (e.grp || []).forEach((g, i) => {
      const s = sig(g);
      const hasWords = ROMANCE.some(l => ((g.tr && g.tr[l]) || []).length);
      let j = hasWords ? out.findIndex(o => o._sig === s) : -1;
      if (j === -1) {
        out.push({ ...g, labels: g.label ? [g.label] : [], zh: [...(g.zh || [])], _sig: s });
        j = out.length - 1;
      } else {
        const o = out[j];
        if (g.label && !o.labels.includes(g.label)) o.labels.push(g.label);
        (g.zh || []).forEach(z => { if (!o.zh.includes(z)) o.zh.push(z); });
      }
      map[i] = j;
    });
    e.grp = out;
    e._rowOf = map;                               // original row index -> merged row index
    (e.pos || []).forEach(b => (b.senses || []).forEach(sn => { if (typeof sn.grp === 'number') sn.grp = map[sn.grp]; }));
    e._merged = true;
    return e;
  }
  const rowOf = (e, gi) => (typeof gi !== 'number' ? -1 : (e && e._rowOf && e._rowOf[gi] !== undefined ? e._rowOf[gi] : gi));
  const sortedKeysCache = new WeakMap();
  function sortedKeys(idx) {
    let ks = sortedKeysCache.get(idx);
    if (!ks) { ks = Object.keys(idx).sort(); sortedKeysCache.set(idx, ks); }
    return ks;
  }

  /* ------------------------------------------------------------- speech */
  let voices = [];
  const hasTTS = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
  function loadVoices() { try { voices = window.speechSynthesis.getVoices() || []; } catch (e) { voices = []; } }
  if (hasTTS) {
    loadVoices();
    if (window.speechSynthesis.addEventListener) window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
  }
  function resolveLocale(code) {
    if (code === 'pt') return TTS.pt[state.pt];
    return TTS[code] || code;
  }
  function speak(text, code, btn) {
    if (!hasTTS) { announce(t('noTTS')); return; }
    const locale = resolveLocale(code);
    const synth = window.speechSynthesis;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = locale;
    u.rate = 0.9;
    const lc = locale.toLowerCase();
    const norml = v => String(v.lang || '').toLowerCase().replace('_', '-');
    const voice = voices.find(v => norml(v) === lc) || voices.find(v => norml(v).startsWith(lc.slice(0, 2)));
    if (voice) u.voice = voice;
    else if (voices.length) announce(t('noVoice', locale));
    document.querySelectorAll('.say.is-speaking').forEach(b => b.classList.remove('is-speaking'));
    if (btn) {
      btn.classList.add('is-speaking');
      const done = () => btn.classList.remove('is-speaking');
      u.onend = done; u.onerror = done;
    }
    synth.speak(u);
  }
  /* Collapsible main sections: en (English entry), tr (translations), ety (etymology). */
  const isCollapsed = id => !!state.collapsed[id];
  const toggleBtn = (id, label) => {
    const open = !isCollapsed(id);
    const action = t(open ? 'secCollapse' : 'secExpand');
    return `<button type="button" class="btn btn-ghost sec-toggle" data-toggle="${id}" data-label="${esc(label)}" aria-expanded="${open}" aria-controls="sec-${id}"
      aria-label="${esc(`${action} ${label}`)}" title="${esc(action)}">${ICON.chevron}<span class="sec-toggle-text" aria-hidden="true">${esc(action)}</span></button>`;
  };
  const secBody = (id, inner) => `<div class="sec-body" id="sec-${id}"${isCollapsed(id) ? ' hidden' : ''}>${inner}</div>`;
  function setCollapsed(id, collapsed) {
    state.collapsed[id] = collapsed;
    store.set('collapsed', state.collapsed);
    const body = document.getElementById(`sec-${id}`);
    if (body) body.hidden = collapsed;
    document.querySelectorAll(`[data-toggle="${id}"]`).forEach(b => {
      const action = t(collapsed ? 'secExpand' : 'secCollapse');
      b.setAttribute('aria-expanded', String(!collapsed));
      b.title = action;
      b.setAttribute('aria-label', `${action} ${b.dataset.label || ''}`);
      const label = b.querySelector('.sec-toggle-text');
      if (label) label.textContent = action;
    });
    const card = body && body.closest('.card');
    if (card) card.classList.toggle('is-collapsed', collapsed);
  }

  const sayBtn = (text, code, label) =>
    `<button type="button" class="say" data-say="${esc(text)}" data-say-lang="${esc(code)}" aria-label="${esc(t('play', text, label))}" title="${esc(t('play', text, label))}"${hasTTS ? '' : ' aria-disabled="true"'}>${ICON.speaker}</button>`;

  /* ---------------------------------------------- history & favorites */
  const getHistory = () => { const h = store.get('history', []); return Array.isArray(h) ? h : []; };
  const getFavs = () => { const f = store.get('favorites', []); return Array.isArray(f) ? f : []; };
  function addHistory(q, h) {
    const k = norm(q);
    const list = getHistory().filter(x => x && norm(x.q) !== k);
    list.unshift({ q, h, at: Date.now() });
    store.set('history', list.slice(0, MAX_HISTORY));
  }
  const isFav = w => getFavs().some(f => f && f.h === w);
  function toggleFav(w, zh) {
    let favs = getFavs();
    const on = favs.some(f => f.h === w);
    favs = on ? favs.filter(f => f.h !== w) : [{ h: w, zh: zh || '' }, ...favs];
    store.set('favorites', favs);
    document.querySelectorAll(`[data-fav="${CSS.escape(w)}"]`).forEach(btn => {
      btn.setAttribute('aria-pressed', String(!on));
      btn.setAttribute('aria-label', t(!on ? 'favRemove' : 'favAdd'));
      btn.title = t(!on ? 'favRemove' : 'favAdd');
      btn.innerHTML = !on ? ICON.starOn : ICON.star;
    });
    announce(t(on ? 'favRemoved' : 'favAdded', w));
  }

  /* ------------------------------------------------------------ status */
  let announceTimer;
  function announce(msg) {
    const el = $('#status');
    el.textContent = '';
    clearTimeout(announceTimer);
    announceTimer = setTimeout(() => { el.textContent = msg; }, 60);
  }

  /* ================================================================ views */
  function render(opts = {}) {
    const v = state.view;
    let html = '';
    if (v.type === 'home') html = viewHome();
    else if (v.type === 'loading') html = viewSkeleton();
    else if (v.type === 'notfound') html = viewNotFound(v);
    else if (v.type === 'error') html = viewError(v);
    else if (v.type === 'entry') html = viewEntry(v);
    main.innerHTML = html;
    main.setAttribute('aria-busy', v.type === 'loading' ? 'true' : 'false');
    if (v.type === 'entry') bindSwipe();
    if (opts.scrollTop) window.scrollTo(0, 0);
    if (opts.scrollTo) {
      const el = document.getElementById(opts.scrollTo);
      if (el && window.innerWidth < 1024) el.scrollIntoView({ block: 'start' });
    }
  }

  function viewHome() {
    const hist = getHistory();
    const favs = getFavs();
    const chip = (q, sub) => `<li><button type="button" class="chip" data-q="${esc(q)}">${esc(q)}${sub ? ` <small>${esc(sub)}</small>` : ''}</button></li>`;
    return `
      <section class="hero">
        <h1 class="hero-title">${t('heroTitle')}</h1>
        <p class="hero-sub">${esc(t('tagline'))}</p>
        <div class="try">
          <h2 class="mini-h">${esc(t('tryThese'))}</h2>
          <ul class="chips">${EXAMPLES.map(q => chip(q)).join('')}</ul>
        </div>
      </section>
      <div class="home-grid">
        <section class="card" aria-labelledby="h-hist">
          <div class="section-head">
            <h2 class="section-title" id="h-hist">${esc(t('history'))}</h2>
            ${hist.length ? `<button type="button" class="btn btn-ghost btn-small" data-clear="history">${esc(t('clear'))}</button>` : ''}
          </div>
          ${hist.length ? `<ul class="chips">${hist.map(x => chip(x.q, x.h && norm(x.h) !== norm(x.q) ? `→ ${x.h}` : '')).join('')}</ul>`
            : `<p class="empty">${esc(t('noHistory'))}</p>`}
        </section>
        <section class="card" aria-labelledby="h-fav">
          <div class="section-head">
            <h2 class="section-title" id="h-fav">${esc(t('favorites'))}</h2>
            ${favs.length ? `<button type="button" class="btn btn-ghost btn-small" data-clear="favorites">${esc(t('clear'))}</button>` : ''}
          </div>
          ${favs.length ? `<ul class="chips">${favs.map(f => chip(f.h, f.zh)).join('')}</ul>`
            : `<p class="empty">${esc(t('noFavorites'))}</p>`}
        </section>
        <section class="card how" aria-labelledby="h-how">
          <h2 class="section-title" id="h-how" style="margin-bottom:12px">${esc(t('howTitle'))}</h2>
          <ul>${t('how').map(x => `<li>${esc(x)}</li>`).join('')}</ul>
        </section>
      </div>`;
  }

  function viewSkeleton() {
    const cell = '<div class="card skel"><div class="skel-line" style="width:40%"></div><div class="skel-line" style="width:75%"></div><div class="skel-line" style="width:55%"></div></div>';
    const live = state.view.live ? `<p class="notice" role="status">${esc(t('liveLoading', state.view.live))}</p>` : '';
    return `<div class="results" aria-label="${esc(t('loading'))}">${live}
      <div class="card skel"><div class="skel-line h1"></div><div class="skel-line" style="width:30%"></div>
        <div class="skel-line" style="width:90%"></div><div class="skel-line" style="width:80%"></div><div class="skel-line" style="width:60%"></div></div>
      <div class="skel-grid">${cell.repeat(4)}</div></div>`;
  }

  function viewNotFound(v) {
    const sugg = v.sugg || [];
    return `<div class="results"><section class="card" aria-labelledby="nf-h">
      <h1 class="section-title" id="nf-h">${esc(t('notFound', v.q))}</h1>
      ${sugg.length ? `<p style="margin-top:12px">${esc(t('didYouMean'))}</p>
        <ul class="chips" style="margin-top:10px">${sugg.map(s => `<li><button type="button" class="chip" data-q="${esc(s.f)}">${esc(s.f)}${s.h && norm(s.h) !== norm(s.f) ? ` <small>→ ${esc(s.h)}</small>` : ''}</button></li>`).join('')}</ul>`
        : `<p class="muted" style="margin-top:12px">${esc(t('noSuggest'))}</p>`}
      ${v.liveSugg && v.liveSugg.length ? `<p style="margin-top:16px">${esc(t('liveSuggest'))}</p>
        <ul class="chips" style="margin-top:10px">${v.liveSugg.map(s => `<li><button type="button" class="chip" data-q="${esc(s.f)}">${esc(s.f)}</button></li>`).join('')}</ul>` : ''}
      <p style="margin-top:16px"><a class="src-link" href="https://en.wiktionary.org/w/index.php?search=${encodeURIComponent(v.q)}" target="_blank" rel="noopener">${esc(t('searchWiktionary', v.q))} ${ICON.ext}</a></p>
    </section></div>`;
  }

  function viewError(v) {
    return `<div class="results"><section class="card" role="alert">
      <h1 class="section-title">${esc(t('netError'))}</h1>
      ${location.protocol === 'file:' ? `<p class="muted" style="margin-top:10px">${esc(t('fileHint'))}</p>` : ''}
      <p style="margin-top:16px"><button type="button" class="btn btn-primary" data-retry="${esc(v.q || '')}">${esc(t('retry'))}</button></p>
    </section></div>`;
  }

  /* -------------------------------------------------------------- entry */
  function hitText(hit) {
    const L = hit.langs ? joinList(hit.langs.map(langName)) : langName(hit.l);
    switch (hit.r) {
      case 'inf': return t('viaInf', hit.f, formLabel(hit.t), hit.m);
      case 'tr': return t('viaTr', hit.f, L, hit.h);
      case 'zh': return t('viaZh', hit.f, hit.h);
      case 'trinf': return t('viaTrinf', hit.f, L, hit.m, formLabel(hit.t), hit.h);
      default: return '';
    }
  }

  function viewNotice(v) {
    const byHead = new Map();
    v.hits.forEach(h => { if (!byHead.has(h.h)) byHead.set(h.h, []); byHead.get(h.h).push(h); });
    // when the query is the English headword itself, "it is also French for ..." is noise
    const isHeadword = (byHead.get(v.entry.w) || []).some(h => h.r === 'hw');
    const primaryHits = isHeadword ? [] : (byHead.get(v.entry.w) || []).filter(h => h.r !== 'hw');
    const others = [...byHead.keys()].filter(h => h !== v.entry.w);
    if (!others.length && (!primaryHits.length || (byHead.get(v.entry.w) || []).some(h => h.r === 'hw'))) return '';
    // merge hits that differ only by language ("café" in pt, fr and es)
    const merged = new Map();
    primaryHits.forEach(h => {
      const sig = [h.r, h.f, h.m, h.t].join('|');
      if (merged.has(sig)) merged.get(sig).langs.push(h.l);
      else merged.set(sig, { ...h, langs: [h.l] });
    });
    const lines = [...merged.values()].slice(0, 3).map(h => esc(hitText(h)));
    return `<aside class="notice" aria-label="${esc(t('queryIs', v.q))}">
      ${lines.length ? `<p><b>${esc(t('queryIs', v.q))}</b>${lines.join(' ')}</p>` : ''}
      ${others.length ? `<p><b>${esc(t('alsoMaybe'))}</b></p><ul class="chips">${others.map(h => {
        const first = byHead.get(h)[0];
        return `<li><button type="button" class="chip chip-sm" data-q="${esc(h)}"><b>${esc(h)}</b> <small>${esc(hitText(first) || state.wordZh.get(h) || '')}</small></button></li>`;
      }).join('')}</ul>` : ''}
    </aside>`;
  }

  function viewEntry(v) {
    const live = v.live ? `<aside class="notice"><p>${esc(t('liveNotice'))}
      <a class="src-link" href="https://en.wiktionary.org/wiki/${encodeURIComponent(v.entry.w)}" target="_blank" rel="noopener">${esc(t('liveOpen'))} ${ICON.ext}</a></p></aside>` : '';
    return `<div class="results">${live}${viewNotice(v)}${viewEnglish(v.entry)}${viewTranslations(v)}${viewEtymology(v.entry)}</div>`;
  }

  function labelsHtml(tags) {
    if (!tags || !tags.length) return '';
    return `<div class="labels">${tags.map(tg => `<span class="label${REGISTER.has(tg) ? ' is-register' : ''}${REGION.has(tg) ? ' is-region' : ''}" title="${esc(tg)}">${esc(tagLabel(tg))}</span>`).join('')}</div>`;
  }
  const wordChips = (list, lang) => `<ul class="chips">${list.map(w =>
    `<li><button type="button" class="chip chip-sm" data-q="${esc(w.replace(/\s*\(.*\)$/, ''))}" lang="${lang}">${esc(w)}</button></li>`).join('')}</ul>`;

  function viewEnglish(e) {
    const fav = isFav(e.w);
    const ipa = e.ipa || {};
    const multiEty = (e.ety || []).length > 1;
    const pron = [['uk', 'en-GB', t('pronUK')], ['us', 'en-US', t('pronUS')]].filter(([k]) => ipa[k]).map(([k, loc, label]) =>
      `<span class="pron-item"><span class="pron-label">${esc(label)}</span><span class="ipa">${esc(ipa[k])}</span>${sayBtn(e.w, loc, `${langName('en')} (${label})`)}</span>`).join('');
    const blocks = (e.pos || []).map(b => {
      const forms = (b.forms || []).map(([code, form, lbl]) =>
        `<span><span class="form-label">${esc(formLabel(code))}</span> <span class="form-val" lang="en">${esc(form)}</span>${lbl ? ` <span class="label is-register">${esc(tagLabel(lbl))}</span>` : ''}</span>`).join('');
      const senses = (b.senses || []).map(s => `<li class="sense">
          ${labelsHtml(s.tags)}
          <p class="sense-def" lang="en">${esc(s.d)}</p>
          ${s.zh ? `<p class="sense-zh" lang="zh-Hant">${esc(s.zh)}</p>` : ''}
          ${(s.ex || []).map(x => `<p class="sense-ex" lang="en"><span class="sr-only">${esc(t('example'))}: </span>${esc(x)}</p>`).join('')}
          ${s.syn && s.syn.length ? `<p class="sense-syn">${esc(t('senseSyn'))}<span lang="en">${esc(s.syn.join(', '))}</span></p>` : ''}
        </li>`).join('');
      return `<section class="pos-block">
        <div class="pos-head"><h3 class="pos-name">${esc(posLabel(b.p))}${state.ui === 'zh' ? `<span lang="en">${esc(POS[b.p] ? POS[b.p][1] : b.p)}</span>` : ''}</h3>
          ${multiEty ? `<span class="ety-num">${esc(t('ety'))} ${b.e + 1}</span>` : ''}</div>
        ${forms ? `<p class="forms" aria-label="${esc(t('forms'))}">${forms}</p>` : ''}
        <ol class="senses">${senses}</ol>
      </section>`;
    }).join('');
    const rel = [['syn', 'synonyms'], ['ant', 'antonyms'], ['phr', 'phrases']].filter(([k]) => e[k] && e[k].length).map(([k, label]) =>
      `<div class="rel-group"><h3 class="mini-h">${esc(t(label))}</h3>${wordChips(e[k], 'en')}</div>`).join('');
    return `<article class="card entry${isCollapsed('en') ? ' is-collapsed' : ''}" aria-labelledby="hw">
      <div class="entry-head">
        <div class="entry-title">
          <p class="mini-h">${esc(state.ui === 'zh' ? '英語詞條 · English' : 'English entry')}</p>
          <h1 class="headword" id="hw" lang="en">${esc(e.w)}</h1>
          ${e.zh && e.zh.length ? `<p class="hw-zh" lang="zh-Hant">${esc(e.zh.join('；'))}</p>` : ''}
        </div>
        <button type="button" class="btn btn-ghost btn-icon fav" data-fav="${esc(e.w)}" data-fav-zh="${esc((e.zh || [])[0] || '')}"
          aria-pressed="${fav}" aria-label="${esc(t(fav ? 'favRemove' : 'favAdd'))}" title="${esc(t(fav ? 'favRemove' : 'favAdd'))}">${fav ? ICON.starOn : ICON.star}</button>
        ${toggleBtn('en', t('englishEntry'))}
      </div>
      ${secBody('en', `${pron ? `<div class="pron">${pron}</div>` : ''}
      <div class="entry-body">
        <div>${blocks}</div>
        <aside>
          ${rel}
          <div class="rel-group"><a class="src-link" href="https://en.wiktionary.org/wiki/${encodeURIComponent(e.w)}#English" target="_blank" rel="noopener">Wiktionary: ${esc(e.w)} ${ICON.ext}<span class="sr-only"> (${esc(t('source'))})</span></a></div>
        </aside>
      </div>`)}
    </article>`;
  }

  function wordDisplay(art, w) {
    if (!art) return '';
    return art.endsWith("'") ? art : art + ' ';
  }

  function viewWord(lang, w, match) {
    const g = w.g;
    const gl = t('gender')[g];
    const gender = gl ? `<span class="gender g-${g}"><abbr title="${esc(gl[1])}">${g === 'mf' ? 'm/f' : g + '.'}</abbr>${esc(gl[0])}</span>` : '';
    const pos = w.p ? `<span class="chip-pos">${esc(posLabel(w.p))}</span>` : '';
    const variant = w.v ? `<span class="variant">${esc(t(w.v === 'BR' ? 'variantBR' : 'variantPT'))}</span>` : '';
    const details = [];
    if (w.pl) details.push(`<span>${esc(t('plural'))} <span class="val" lang="${lang}">${esc(wordDisplay(w.plArt, w.pl))}${esc(w.pl)}</span></span>`);
    if (w.fem) details.push(`<span>${esc(t('feminine'))} <span class="val" lang="${lang}">${esc(w.fem)}</span></span>`);
    if (lang === 'pt' && (w.ipaBR || w.ipaPT)) {
      if (w.ipaPT) details.push(`<span class="ipa ipa-pt" title="pt-PT">${esc(w.ipaPT)}</span>`);
      if (w.ipaBR) details.push(`<span class="ipa ipa-br" title="pt-BR">${esc(w.ipaBR)}</span>`);
    } else if (w.ipa) details.push(`<span class="ipa">${esc(w.ipa)}</span>`);
    return `<div class="tw${match ? ' is-match' : ''}"${w.v ? ` data-v="${esc(w.v)}"` : ''}>
      <div class="tw-main">
        ${w.art ? `<span class="tw-art" lang="${lang}">${esc(w.art)}</span>` : ''}
        <button type="button" class="tw-word" data-q="${esc(w.w)}" lang="${lang}">${esc(w.w)}</button>
        ${sayBtn(w.w, lang, langName(lang))}
      </div>
      ${gender || pos || variant ? `<div class="tw-meta">${gender}${pos}${variant}</div>` : ''}
      ${details.length ? `<div class="tw-detail">${details.join('')}</div>` : ''}
      ${w.gl ? `<p class="tw-gloss" lang="en">“${esc(w.gl)}”</p>` : ''}
      <a class="src-link" href="https://en.wiktionary.org/wiki/${encodeURIComponent(w.w)}#${WIKT_ANCHOR[lang]}" target="_blank" rel="noopener">Wiktionary ${ICON.ext}<span class="sr-only"> ${esc(langName(lang))} ${esc(w.w)}</span></a>
    </div>`;
  }

  function viewTranslations(v) {
    const e = v.entry;
    const p = v.primary || {};
    const matchLang = (p.r === 'tr' || p.r === 'trinf') && p.h === e.w ? p.l : null;
    const matchWord = p.r === 'tr' ? p.f : (p.r === 'trinf' ? p.m : null);
    const matchGi = p.h === e.w ? rowOf(e, p.gi) : -1;
    const tab = matchLang || state.tab;
    const tabs = ROMANCE.map(l => `<button type="button" role="tab" id="tab-${l}" data-lang="${l}" data-tab="${l}"
        aria-selected="${l === tab}" tabindex="${l === tab ? 0 : -1}" aria-controls="tr-rows" title="${esc(NATIVE[l])}">${l.toUpperCase()}</button>`).join('');
    const rows = (e.grp || []).map((g, gi) => {
      const cells = ROMANCE.map(l => {
        const words = (g.tr && g.tr[l]) || [];
        const body = words.length
          ? words.map(w => viewWord(l, w, l === matchLang && matchWord && norm(w.w) === norm(matchWord))).join('')
          : `<p class="missing"><span class="dash" aria-hidden="true">—</span>${esc(t('missingTr'))}</p>`;
        return `<div class="tr-cell" data-lang="${l}">
          <h4 class="cell-lang"><span class="native" lang="${l}">${NATIVE[l]}</span><span class="local">${esc(langName(l))}</span></h4>
          ${body}</div>`;
      }).join('');
      return `<article class="tr-row${gi === matchGi ? ' is-match' : ''}" id="sense-${gi}" aria-labelledby="sense-h-${gi}">
        <h3 class="tr-row-head" id="sense-h-${gi}"><span class="row-num">${gi + 1}</span>
          <span class="row-label" lang="en">${esc((g.labels && g.labels[0]) || g.label || e.w)}</span>
          ${(g.labels || []).slice(1).map(lb => `<span class="sense-tag" lang="en" title="${esc(t('alsoSense'))}">${esc(lb)}</span>`).join('')}
          ${g.zh && g.zh.length ? `<span class="row-zh" lang="zh-Hant">${esc(g.zh.join('；'))}</span>` : ''}
          ${g.p ? `<span class="chip-pos">${esc(posLabel(g.p))}</span>` : ''}</h3>
        <div class="tr-grid">${cells}</div>
      </article>`;
    }).join('');
    return `<section class="card${isCollapsed('tr') ? ' is-collapsed' : ''}" aria-labelledby="tr-h">
      <div class="section-head">
        <h2 class="section-title" id="tr-h">${esc(t('translations'))}<small>${esc(t('translationsSub'))}</small></h2>
        <div class="head-tools"><div class="pt-switch"><span class="mini-h" id="pt-lbl">${esc(t('ptVariant'))}</span>
          <div class="seg" role="group" aria-labelledby="pt-lbl">
            <button type="button" data-pt="PT" aria-pressed="${state.pt === 'PT'}">${esc(t('ptPT'))}</button>
            <button type="button" data-pt="BR" aria-pressed="${state.pt === 'BR'}">${esc(t('ptBR'))}</button>
          </div></div>
          ${toggleBtn('tr', t('translations'))}</div>
      </div>
      ${secBody('tr', `<div class="lang-tabs" role="tablist" aria-label="${esc(t('langTabs'))}">${tabs}</div>
      <div class="tr-rows" id="tr-rows" data-tab="${tab}" role="tabpanel" aria-labelledby="tab-${tab}">${rows}</div>`)}
    </section>`;
  }

  /* ---------------------------------------------------------- etymology */
  function buildForest(leaves) {
    const nodes = new Map();
    const get = (key, data) => {
      let n = nodes.get(key);
      if (!n) { n = { key, data, parent: null, children: [], leaf: null }; nodes.set(key, n); }
      return n;
    };
    const cycles = (child, parent) => { for (let p = parent; p; p = p.parent) if (p === child) return true; return false; };
    const leafNodes = [];
    leaves.forEach(lf => {
      const ln = get(`${lf.lang}:${norm(lf.w)}`, { l: lf.lang, f: lf.w });
      if (ln.leaf) return;
      ln.leaf = lf;
      leafNodes.push(ln);
      let prev = ln;
      for (const a of lf.chain || []) {
        if (!a.f && !a.lm) break;
        const k = `${a.l}:${akey(a.lm || a.f)}`;
        if (k === prev.key) continue;
        const n = get(k, a);
        if (!prev.parent && !cycles(prev, n)) { prev.parent = n; n.children.push(prev); }
        prev = n;
      }
    });
    const order = n => {
      if (n._ord !== undefined) return n._ord;
      let o = n.leaf ? LEAF_ORDER.indexOf(n.leaf.lang) * 10 + (n.leaf.i || 0) / 10 : 999;
      n.children.forEach(c => { o = Math.min(o, order(c)); });
      n._ord = o;
      return o;
    };
    const leavesUnder = n => (n.leaf ? [n.leaf] : []).concat(...n.children.map(leavesUnder));
    const rootOf = n => { while (n.parent) n = n.parent; return n; };
    const sortKids = n => { n.children.sort((a, b) => order(a) - order(b)); n.children.forEach(sortKids); };
    const roots = [...new Set(leafNodes.map(rootOf))];
    roots.forEach(sortKids);
    const trees = roots.map(r => {
      const ls = leavesUnder(r);
      return { root: r, leaves: ls, langs: new Set(ls.map(l => l.lang)).size };
    });
    trees.sort((a, b) => (b.langs >= 2) - (a.langs >= 2) || b.leaves.length - a.leaves.length || order(a.root) - order(b.root));
    let letter = 0;
    const groupOf = new Map();
    trees.forEach(tr => {
      if (tr.langs >= 2) {
        tr.letter = String.fromCharCode(65 + letter++);
        tr.leaves.forEach(l => groupOf.set(l, tr.letter));
      }
    });
    return { trees, groupOf, leavesUnder };
  }

  const lcaOf = n => { while (!n.leaf && n.children.length === 1) n = n.children[0]; return n; };
  function nodeText(d, withGloss = true) {
    const f = d.f + (d.tr ? ` (${d.tr})` : '');
    return t('nodeFmt', langName(d.l), f, withGloss ? d.g : '');
  }

  function summarize(forest, leaves) {
    const out = [];
    const en = leaves.find(l => l.lang === 'en');
    if (en && en.chain && en.chain.length) {
      const first = en.chain[0];
      const last = en.chain[en.chain.length - 1];
      out.push(t('sumEn', en.w, nodeText(first, false), last !== first ? nodeText(last) : ''));
    }
    const nameOf = l => t('nameFmt', langName(l.lang), l.w);
    const groups = forest.trees.filter(tr => tr.letter);
    groups.forEach(tr => {
      const lca = lcaOf(tr.root);
      const root = tr.root !== lca ? nodeText(tr.root.data) : '';
      out.push(t('sumGroup', joinList(tr.leaves.map(nameOf)), nodeText(lca.data), root));
      lca.children.forEach(c => {
        const ls = forest.leavesUnder(c);
        if (ls.length >= 2 && ls.length < tr.leaves.length) {
          const sub = lcaOf(c);
          out.push(t('sumSub', joinList(ls.map(nameOf)), nodeText(sub.data)));
        }
      });
    });
    const singles = forest.trees.filter(tr => !tr.letter).flatMap(tr => tr.leaves).filter(l => l.chain && l.chain.length);
    if (!groups.length) out.push(t('sumNone'));
    else if (singles.length) out.push(t('sumSingles', joinList(singles.map(nameOf))));
    const missing = leaves.filter(l => (!l.chain || !l.chain.length) && !(l.form && l.form.parts && l.form.parts.length));
    if (missing.length) out.push(t('sumMissing', joinList(missing.map(nameOf))));
    return out.join(state.ui === 'zh' ? '' : ' ');
  }

  function treeNodeBox(n) {
    if (n.leaf) {
      const lf = n.leaf;
      return `<div class="tn is-leaf${lf.chain && lf.chain.length ? '' : ' is-unknown'}" data-lang="${lf.lang}">
        <span class="tn-lang">${esc(langName(lf.lang))}</span>
        <button type="button" class="tn-form" data-q="${esc(lf.w)}" lang="${lf.lang}">${esc(lf.w)}</button>
        ${lf.chain && lf.chain.length ? '' : `<span class="tn-gloss">${esc(t('missingEty'))}</span>`}</div>`;
    }
    return lineHtml(n.data);
  }
  function lineHtml(d) {
    return `<span class="tn-lang">${esc(langName(d.l))}</span>
      <button type="button" class="tn-form" data-q="${esc(stripStar(d.lm || d.f))}" lang="${esc(d.l)}">${esc(d.f)}${d.tr ? ` <span class="tn-gloss" style="display:inline">(${esc(d.tr)})</span>` : ''}</button>
      ${d.g ? `<span class="tn-gloss" lang="en">“${esc(d.g)}”</span>` : ''}`;
  }
  function treeNode(n) {
    let box;
    let cur = n;
    if (!n.leaf) {
      const stack = [n];
      while (!cur.leaf && cur.children.length === 1 && !cur.children[0].leaf) { cur = cur.children[0]; stack.push(cur); }
      box = `<div class="tn">${stack.map(s => `<div class="tn-line">${lineHtml(s.data)}</div>`).join('')}</div>`;
    } else {
      box = treeNodeBox(n);
    }
    const kids = cur.children;
    return `<li>${box}${kids.length ? `<ul>${kids.map(treeNode).join('')}</ul>` : ''}</li>`;
  }

  function chainHtml(lf, letter) {
    const chain = lf.chain || [];
    const parts = chain.map(n => {
      let note = '';
      if (n.lm && akey(n.lm) !== akey(n.f)) note = n.lmt ? t('caseOf', n.lm, caseLabel(n.lmt)) : t('seeLemma', n.lm);
      return `<span class="arrow" aria-hidden="true">←</span><span class="sr-only">${esc(t('from'))}</span><span class="anc">` +
        `<span class="anc-lang">${esc(langName(n.l))}</span> ` +
        `<button type="button" class="linkish anc-form" data-q="${esc(stripStar(n.lm || n.f))}" lang="${esc(n.l)}">${esc(n.f || '?')}</button>` +
        `${n.tr ? ` <span class="anc-note">(${esc(n.tr)})</span>` : ''}` +
        `${note ? `<span class="anc-note">${esc(note)}</span>` : ''}` +
        `${n.g ? ` <span class="anc-gloss" lang="en">“${esc(n.g)}”</span>` : ''}` +
        `${n.unc ? ` <span class="anc-note">(${esc(t('uncertain'))})</span>` : ''}</span>`;
    }).join('');
    const tag = letter ? `<span class="grp-tag" title="${esc(t('groupN', letter))}">${letter}</span>`
      : `<span class="grp-tag grp-none" title="${esc(t('noGroup'))}">–</span>`;
    const cogs = lf.cog && lf.cog.length
      ? `<p class="cogs">${esc(t('otherCogs'))}${esc(joinList(lf.cog.map(c => `${langName(c.l)} ${c.f}${c.tr ? ` (${c.tr})` : ''}`)))}</p>` : '';
    return `<li class="chain" data-lang="${lf.lang}">
      <div class="chain-top"><span class="chain-lang">${esc(langName(lf.lang))}</span>${tag}</div>
      <p class="chain-line"><button type="button" class="linkish chain-leaf" data-q="${esc(lf.w)}" lang="${lf.lang}">${esc(lf.w)}</button>${
        parts || (lf.form && lf.form.parts && lf.form.parts.length
          ? ` <span class="anc-note">${esc(t('formedFrom'))}</span> ${lf.form.parts.map(p => `<button type="button" class="linkish anc-form" data-q="${esc(p)}" lang="${esc(lf.form.l || lf.lang)}">${esc(p)}</button>`).join(' + ')}`
          : ` <span class="missing"><span class="dash" aria-hidden="true">—</span>${esc(t('missingEty'))}</span>`)}${
        lf.unc && chain.length ? ` <span class="anc-note">(${esc(t('uncertain'))})</span>` : ''}</p>
      ${cogs}
    </li>`;
  }

  // Etymology describes words, not senses: one card per English etymology, listing every
  // distinct Romance word of the rows that belong to it (at most MAX_ETY_WORDS per language).
  const MAX_ETY_WORDS = 3;
  function viewEtymology(e) {
    const byEty = new Map();
    (e.grp || []).forEach((g, gi) => {
      const k = g.e || 0;
      if (!byEty.has(k)) byEty.set(k, { e: k, rows: [], zh: [], words: new Map() });
      const c = byEty.get(k);
      c.rows.push(gi);
      (g.zh || []).forEach(z => { if (!c.zh.includes(z)) c.zh.push(z); });
      ROMANCE.forEach(l => ((g.tr && g.tr[l]) || []).forEach(w => {
        const key = `${l}:${norm(w.w)}`;
        const perLang = [...c.words.values()].filter(x => x.lang === l).length;
        if (!c.words.has(key) && perLang < MAX_ETY_WORDS) c.words.set(key, { lang: l, w });
      }));
    });
    const cards = [...byEty.values()].sort((a, b) => a.e - b.e).map(c => {
      const ety = (e.ety || [])[c.e] || {};
      const leaves = [{ lang: 'en', w: e.w, chain: ety.chain || [], text: ety.text, unc: ety.unc, cog: ety.cog, form: ety.form, i: 0 }];
      ROMANCE.forEach(l => [...c.words.values()].filter(x => x.lang === l).forEach(({ w }, i) => leaves.push({
        lang: l, w: w.w, chain: (w.ety && w.ety.chain) || [], text: w.ety && w.ety.text, unc: w.ety && w.ety.unc,
        form: w.ety && w.ety.form, i,
      })));
      return { ...c, leaves };
    });
    const multi = cards.length > 1;
    const html = cards.map(({ rows, zh, leaves }, ci) => {
      const gi = ci;
      const forest = buildForest(leaves);
      const hasCog = forest.trees.some(tr => tr.letter);
      const badge = hasCog
        ? `<span class="badge badge-cog">${ICON.check}${esc(t('cognates'))}</span>`
        : `<span class="badge badge-none">${esc(t('noCognates'))}</span>`;
      const trees = forest.trees.map(tr => `<div class="tree${tr.letter ? ' is-group' : ''}">
          <div class="tree-cap">${tr.letter ? `<span class="grp-tag">${tr.letter}</span>${esc(t('groupN', tr.letter))}` : `<span class="grp-tag grp-none">–</span>${esc(t('noGroup'))}`}</div>
          <ul>${treeNode(tr.root)}</ul></div>`).join('');
      const texts = leaves.filter(l => l.text).map(l =>
        `<div data-lang="${l.lang}"><dt>${esc(t('langOf', langName(l.lang), l.w))}</dt><dd lang="en">${esc(l.text)}</dd></div>`).join('');
      return `<article class="ety-group" aria-labelledby="ety-h-${gi}">
        <div class="ety-head">
          <h3 id="ety-h-${gi}">${multi ? `<span class="row-num">${ci + 1}</span><span>${esc(t('etyN', ci + 1))}</span>` : `<span lang="en">${esc(e.w)}</span>`}
            ${zh.length ? `<span class="row-zh" lang="zh-Hant">${esc(zh.slice(0, 4).join('；'))}</span>` : ''}
            <span class="ety-rows">${esc(t('etyRows', rows.map(i => i + 1).join('・')))}</span></h3>
          ${badge}
        </div>
        <p class="ety-summary" data-label="${esc(t('summaryLabel'))}">${esc(summarize(forest, leaves))}</p>
        <div class="ety-layout">
          <div><h4 class="mini-h">${esc(t('chains'))}</h4>
            <ul class="chains">${leaves.map(l => chainHtml(l, forest.groupOf.get(l))).join('')}</ul></div>
          <figure class="tree-fig">
            <figcaption><span class="mini-h">${esc(t('tree'))}</span><span class="hint">${esc(t('treeHint'))}</span></figcaption>
            <div class="forest" tabindex="0" role="group" aria-label="${esc(t('treeLabel', multi ? `${e.w} ${t('etyN', ci + 1)}` : e.w))}">${trees}</div>
          </figure>
        </div>
        ${texts ? `<details class="ety-full"><summary><span class="when-closed">${esc(t('expand'))}</span><span class="when-open">${esc(t('collapse'))}</span>
          <span class="muted" style="font-weight:500">· ${esc(t('original'))}</span></summary><dl>${texts}</dl></details>` : ''}
      </article>`;
    }).join('');
    const pending = state.view && state.view.entry === e && state.view.etyPending;
    return `<section class="card${isCollapsed('ety') ? ' is-collapsed' : ''}" id="ety-card" aria-labelledby="ety-title" aria-busy="${pending ? 'true' : 'false'}">
      <div class="section-head"><h2 class="section-title" id="ety-title">${esc(t('etymology'))}<small>${esc(t('etymologySub'))}</small></h2>
        <div class="head-tools">${pending ? `<span class="badge badge-none">${esc(t('etyLoading'))}</span>` : ''}${toggleBtn('ety', t('etymology'))}</div></div>
      ${secBody('ety', html)}
    </section>`;
  }

  /* ============================================================ search */
  function setUrl(q, push) {
    const url = new URL(location.href);
    if (q) url.searchParams.set('q', q); else url.searchParams.delete('q');
    if (url.href === location.href) return;
    if (push) history.pushState({ q }, '', url); else history.replaceState({ q }, '', url);
  }

  async function fuzzy(key, idx) {
    try { await state.wordsReady; } catch (e) { /* words.json optional for suggestions */ }
    const cands = new Map();
    state.words.forEach(([w]) => cands.set(norm(w), { f: w, h: w }));
    if (idx) Object.keys(idx).forEach(k => { if (!cands.has(k)) { const h0 = decodeHit(idx[k][0]); cands.set(k, { f: h0.f, h: h0.h }); } });
    const maxD = key.length <= 3 ? 1 : key.length <= 7 ? 2 : 3;
    const out = [];
    cands.forEach((c, k) => {
      let score;
      if (k.startsWith(key)) score = 0.3;
      else if (key.length >= 2 && k.includes(key)) score = 0.6;
      else if (key.startsWith(k) && k.length >= 3) score = 0.9;
      else if (key.length >= 3 && k.length >= 3) {
        const d = lev(key, k, maxD);
        if (d <= maxD) score = d;
      }
      if (score !== undefined) out.push({ score, len: k.length, ...c });
    });
    out.sort((a, b) => a.score - b.score || a.len - b.len);
    const seen = new Set();
    return out.filter(s => (seen.has(s.f) ? false : seen.add(s.f))).slice(0, 8);
  }

  async function search(raw, opts = {}) {
    const q = String(raw == null ? '' : raw).trim();
    closeSuggest();
    if (!q) { goHome(opts.push !== false); return; }
    input.value = q;
    const seq = ++state.seq;
    setUrl(q, opts.push !== false);
    document.title = `${q} · ${t('appName')}`;
    const key = norm(q);
    const skel = setTimeout(() => {
      if (seq === state.seq) { state.view = { type: 'loading' }; render(); }
    }, 90);
    try {
      const idx = await loadIndex(key);
      if (seq !== state.seq) return;
      const hits = hitsOf(idx, key).sort(hitRank);
      if (!hits.length) {
        // not in the offline dataset: try English Wiktionary live
        let live = null;
        if (window.PentaLive && navigator.onLine !== false) {
          clearTimeout(skel);
          state.view = { type: 'loading', live: q };
          render();
          announce(t('liveLoading', q));
          try { live = await window.PentaLive.lookup(q); } catch (e) { console.warn('live lookup failed', e); }
          if (seq !== state.seq) return;
        }
        if (live && live.entry) {
          mergeRows(live.entry);
          const view = { type: 'entry', q, key, hits: live.hits, primary: live.hits[0], entry: live.entry, live: true, etyPending: !!live.pending };
          state.view = view;
          render({ scrollTop: true });
          addHistory(q, live.entry.w);
          announce(t('found', live.entry.w));
          if (live.pending) {
            // phase 2: older ancestors arrive later; refresh only the etymology section
            live.pending.then(() => {
              view.etyPending = false;
              if (state.view !== view) return;
              const old = document.getElementById('ety-card');
              if (!old) return;
              const tmp = document.createElement('div');
              tmp.innerHTML = viewEtymology(view.entry);
              old.replaceWith(tmp.firstElementChild);
            });
          }
          return;
        }
        const sugg = await fuzzy(key, idx);
        if (seq !== state.seq) return;
        clearTimeout(skel);
        state.view = { type: 'notfound', q, sugg, liveSugg: (live && live.suggestions) || [] };
        render({ scrollTop: true });
        announce(t('notFound', q));
        return;
      }
      const primary = hits[0];
      const entry = await loadEntry(primary.h);
      if (seq !== state.seq) return;
      clearTimeout(skel);
      if (!entry) throw new Error(`entry missing: ${primary.h}`);
      state.view = { type: 'entry', q, key, hits, primary, entry };
      const row = rowOf(entry, primary.gi);
      render({ scrollTop: true, scrollTo: row > 0 ? `sense-${row}` : null });
      addHistory(q, entry.w);
      announce(t('found', entry.w));
    } catch (err) {
      clearTimeout(skel);
      if (seq !== state.seq) return;
      console.error(err);
      state.view = { type: 'error', q };
      render();
    }
  }

  function goHome(push) {
    state.seq++;
    input.value = '';
    setUrl('', push);
    document.title = t('appName');
    state.view = { type: 'home' };
    render({ scrollTop: true });
  }

  function route() {
    const q = new URLSearchParams(location.search).get('q');
    if (q && q.trim()) search(q, { push: false });
    else goHome(false);
  }

  /* ------------------------------------------------------ autocomplete */
  let sugItems = [];
  let sugActive = -1;
  let sugSeq = 0;
  let sugTimer;
  function closeSuggest() {
    sugItems = []; sugActive = -1;
    suggestEl.hidden = true;
    suggestEl.innerHTML = '';
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }
  function lowerBound(arr, key) {
    let lo = 0, hi = arr.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] < key) lo = mid + 1; else hi = mid; }
    return lo;
  }
  async function updateSuggest() {
    const key = norm(input.value);
    if (!key) { closeSuggest(); return; }
    const seq = ++sugSeq;
    let idx;
    try { idx = await loadIndex(key); } catch (e) { return; }
    if (seq !== sugSeq || norm(input.value) !== key) return;
    const keys = sortedKeys(idx || {});
    const found = [];
    for (let i = lowerBound(keys, key); i < keys.length && keys[i].startsWith(key) && found.length < 60; i++) found.push(keys[i]);
    found.sort((a, b) => (a === key ? -1 : b === key ? 1 : 0) || a.length - b.length || a.localeCompare(b));
    sugItems = found.slice(0, 8).map(k => {
      const hs = hitsOf(idx, k).sort(hitRank);
      return { ...hs[0], n: new Set(hs.map(h => h.h)).size };
    });
    if (!sugItems.length) { closeSuggest(); return; }
    sugActive = -1;
    suggestEl.innerHTML = sugItems.map((s, i) => {
      const code = s.l === 'zh' ? 'zh' : s.l;
      const target = s.r === 'hw'
        ? `<span class="sug-target">${esc(state.wordZh.get(s.h) || '')}</span>`
        : `<span class="sug-target"><span aria-hidden="true">→ </span><b lang="en">${esc(s.h)}</b>${s.n > 1 ? ` +${s.n - 1}` : ''}</span>`;
      return `<li role="option" id="sug-${i}" class="sug" aria-selected="false" data-i="${i}">
        <span class="sug-word" lang="${code === 'zh' ? 'zh-Hant' : code}">${esc(s.f)}</span>
        <span class="sug-lang" data-lang="${code}">${esc(code.toUpperCase())}</span>${target}</li>`;
    }).join('');
    suggestEl.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }
  function setActive(i) {
    sugActive = i;
    suggestEl.querySelectorAll('.sug').forEach((el, j) => el.setAttribute('aria-selected', String(j === i)));
    if (i >= 0) {
      input.setAttribute('aria-activedescendant', `sug-${i}`);
      const el = document.getElementById(`sug-${i}`);
      if (el) el.scrollIntoView({ block: 'nearest' });
    } else input.removeAttribute('aria-activedescendant');
  }

  input.addEventListener('input', () => { clearTimeout(sugTimer); sugTimer = setTimeout(updateSuggest, 90); });
  input.addEventListener('focus', () => { if (input.value.trim()) updateSuggest(); });
  input.addEventListener('blur', () => setTimeout(closeSuggest, 150));
  input.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      if (suggestEl.hidden) { updateSuggest(); return; }
      setActive(Math.min(sugItems.length - 1, sugActive + 1));
    } else if (ev.key === 'ArrowUp') {
      if (suggestEl.hidden) return;
      ev.preventDefault();
      setActive(Math.max(-1, sugActive - 1));
    } else if (ev.key === 'Enter' && sugActive >= 0 && sugItems[sugActive]) {
      ev.preventDefault();
      search(sugItems[sugActive].f);
    } else if (ev.key === 'Escape') {
      if (!suggestEl.hidden) { ev.preventDefault(); closeSuggest(); }
    }
  });
  suggestEl.addEventListener('mousedown', ev => ev.preventDefault());
  suggestEl.addEventListener('click', ev => {
    const li = ev.target.closest('.sug');
    if (li && sugItems[+li.dataset.i]) search(sugItems[+li.dataset.i].f);
  });
  $('#search-form').addEventListener('submit', ev => { ev.preventDefault(); search(input.value); });

  /* ----------------------------------------------------- tabs & swipe */
  function setTab(lang, focus) {
    const rows = document.getElementById('tr-rows');
    if (!rows || !ROMANCE.includes(lang)) return;
    rows.dataset.tab = lang;
    rows.setAttribute('aria-labelledby', `tab-${lang}`);
    document.querySelectorAll('.lang-tabs [role="tab"]').forEach(b => {
      const on = b.dataset.tab === lang;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    state.tab = lang;
    store.set('tab', lang);
  }
  function bindSwipe() {
    const rows = document.getElementById('tr-rows');
    if (!rows) return;
    let x0 = null, y0 = null;
    rows.addEventListener('touchstart', ev => { const p = ev.changedTouches[0]; x0 = p.clientX; y0 = p.clientY; }, { passive: true });
    rows.addEventListener('touchend', ev => {
      if (x0 === null || window.innerWidth >= 640) return;
      const p = ev.changedTouches[0];
      const dx = p.clientX - x0, dy = p.clientY - y0;
      x0 = null;
      if (Math.abs(dx) < 60 || Math.abs(dy) > 45) return;
      const i = ROMANCE.indexOf(rows.dataset.tab);
      const next = ROMANCE[(i + (dx < 0 ? 1 : -1) + ROMANCE.length) % ROMANCE.length];
      setTab(next, false);
    }, { passive: true });
  }

  /* --------------------------------------------------- global events */
  document.addEventListener('click', ev => {
    const el = ev.target.closest('[data-q],[data-say],[data-fav],[data-tab],[data-pt],[data-clear],[data-retry],[data-home],[data-toggle]');
    if (!el) return;
    if (el.hasAttribute('data-home')) {
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button !== 0) return;
      ev.preventDefault(); goHome(true); input.focus(); return;
    }
    if (el.dataset.q !== undefined) { search(el.dataset.q); return; }
    if (el.dataset.say !== undefined) { speak(el.dataset.say, el.dataset.sayLang, el); return; }
    if (el.dataset.fav !== undefined) { toggleFav(el.dataset.fav, el.dataset.favZh); return; }
    if (el.dataset.tab !== undefined) { setTab(el.dataset.tab, false); return; }
    if (el.dataset.pt !== undefined) {
      state.pt = el.dataset.pt === 'BR' ? 'BR' : 'PT';
      store.set('pt', state.pt);
      document.documentElement.dataset.pt = state.pt;
      document.querySelectorAll('[data-pt]').forEach(b => { if (b.tagName === 'BUTTON') b.setAttribute('aria-pressed', String(b.dataset.pt === state.pt)); });
      return;
    }
    if (el.dataset.toggle) { setCollapsed(el.dataset.toggle, !isCollapsed(el.dataset.toggle)); return; }
    if (el.dataset.clear) { store.set(el.dataset.clear, []); render(); return; }
    if (el.dataset.retry !== undefined) {
      if (el.dataset.retry) search(el.dataset.retry, { push: false }); else route();
    }
  });
  document.addEventListener('keydown', ev => {
    const tab = ev.target.closest && ev.target.closest('.lang-tabs [role="tab"]');
    if (!tab) return;
    const i = ROMANCE.indexOf(tab.dataset.tab);
    let n = null;
    if (ev.key === 'ArrowRight') n = (i + 1) % 4;
    else if (ev.key === 'ArrowLeft') n = (i + 3) % 4;
    else if (ev.key === 'Home') n = 0;
    else if (ev.key === 'End') n = 3;
    if (n !== null) { ev.preventDefault(); setTab(ROMANCE[n], true); }
  });
  window.addEventListener('popstate', route);

  /* ---------------------------------------------- theme & UI language */
  const mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  const effectiveTheme = () => document.documentElement.dataset.theme || (mq && mq.matches ? 'dark' : 'light');
  function updateThemeButton() {
    const btn = $('#theme-toggle');
    const label = t(effectiveTheme() === 'dark' ? 'themeToLight' : 'themeToDark');
    btn.setAttribute('aria-label', label);
    btn.title = label;
  }
  $('#theme-toggle').addEventListener('click', () => {
    const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    store.set('theme', next);
    updateThemeButton();
  });
  if (mq && mq.addEventListener) mq.addEventListener('change', updateThemeButton);

  function applyStaticText() {
    document.documentElement.lang = state.ui === 'zh' ? 'zh-Hant' : 'en';
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    input.placeholder = t('placeholder');
    const ui = $('#ui-lang');
    ui.textContent = t('uiSwitchShort');
    ui.lang = state.ui === 'zh' ? 'en' : 'zh-Hant';
    ui.setAttribute('aria-label', t('uiSwitch'));
    ui.title = t('uiSwitch');
    updateThemeButton();
    const attr = $('[data-i18n-html="attribution"]');
    if (attr) {
      attr.innerHTML = state.ui === 'zh'
        ? '詞典內容取自 <a href="https://en.wiktionary.org/" target="_blank" rel="noopener">英文維基詞典 Wiktionary</a>，依 <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a> 授權，經 <a href="https://github.com/tatuylonen/wiktextract" target="_blank" rel="noopener">Wiktextract</a> / <a href="https://kaikki.org/" target="_blank" rel="noopener">Kaikki.org</a> 擷取整理；各詞條皆附原始頁面連結。語音由瀏覽器內建的 Web Speech API 產生。'
        : 'Dictionary content from <a href="https://en.wiktionary.org/" target="_blank" rel="noopener">English Wiktionary</a>, licensed <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>, extracted with <a href="https://github.com/tatuylonen/wiktextract" target="_blank" rel="noopener">Wiktextract</a> / <a href="https://kaikki.org/" target="_blank" rel="noopener">Kaikki.org</a>; every entry links to its source page. Audio uses your browser’s Web Speech API.';
    }
    const meta = $('#footer-meta');
    if (meta && state.meta) meta.textContent = t('dataset', state.meta.counts.entries, state.meta.built, state.meta.source);
  }
  $('#ui-lang').addEventListener('click', () => {
    state.ui = state.ui === 'zh' ? 'en' : 'zh';
    store.set('ui', state.ui);
    applyStaticText();
    const y = window.scrollY;
    render();
    window.scrollTo(0, y);
    if (state.view.type === 'home') document.title = t('appName');
  });

  /* -------------------------------------------------------------- boot */
  document.documentElement.dataset.pt = state.pt;
  applyStaticText();
  state.wordsReady = getJSON('words.json', true).then(ws => {
    state.words = Array.isArray(ws) ? ws : [];
    state.wordZh = new Map(state.words.map(([w, zh]) => [w, zh]));
  });
  state.metaReady = getJSON('meta.json', true)
    .then(m => { state.meta = m && m.counts ? m : null; applyStaticText(); })
    .catch(() => { state.meta = null; });
  route();
})();
