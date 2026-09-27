#!/usr/bin/env python3
"""
build_dataset.py — generate the static JSON dataset for 羅曼多語言字典 (Romance Multilingual Dictionary).

Two input modes share exactly the same processing pipeline:

  1. Sample mode (no downloads needed; regenerates the bundled demo data):

         python tools/build_dataset.py --sample --out data

  2. Full mode, from Wiktextract / Kaikki.org JSONL dumps of English Wiktionary
     (https://kaikki.org/dictionary/<Language>/kaikki.org-dictionary-<Language>.jsonl):

         python tools/build_dataset.py \
             --en raw/kaikki.org-dictionary-English.jsonl.gz \
             --it raw/kaikki.org-dictionary-Italian.jsonl.gz \
             --pt raw/kaikki.org-dictionary-Portuguese.jsonl.gz \
             --fr raw/kaikki.org-dictionary-French.jsonl.gz \
             --es raw/kaikki.org-dictionary-Spanish.jsonl.gz \
             --ancestors raw/kaikki.org-dictionary-Latin.jsonl.gz \
                         raw/kaikki.org-dictionary-OldFrench.jsonl.gz \
             --wordlist wordlist.txt --top 10000 --out data

Output layout (see README.md for the schema):

    data/meta.json              build info, shard parameters, language names
    data/words.json             [[headword, zh], ...] for fuzzy matching
    data/index/<bucket>.json    normalized search key -> hits
    data/entries/<xx>.json      headword -> full entry (2-letter prefix shards)

Etymology handling: the structured `etymology_templates` of every record are
parsed into an ordered ancestor chain ({{inh}}, {{der}}, {{bor}}, ... ), glossed
and lemmatised with {{m}} / {{l}} mentions, and then extended by looking the
last ancestor up in the ancestor dictionaries (e.g. Latin "noctem" is a form of
"nox", whose own etymology continues to Proto-Italic and Proto-Indo-European).
The web app compares chain nodes by (language code, normalized lemma) to find
cognates, never by matching free text.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from datetime import date

ROMANCE = ("fr", "it", "es", "pt")                # display order used by the app
ENTRY_PREFIX_LEN = 3

# --------------------------------------------------------------------------
# Language names (English, Traditional Chinese). Unknown codes fall back to
# the name found in the template expansion or to the code itself.
# --------------------------------------------------------------------------
LANG_NAMES = {
    "en": ("English", "英語"),
    "enm": ("Middle English", "中古英語"),
    "ang": ("Old English", "古英語"),
    "xno": ("Anglo-Norman", "盎格魯-諾曼語"),
    "gem-pro": ("Proto-Germanic", "原始日耳曼語"),
    "gmw-pro": ("Proto-West Germanic", "原始西日耳曼語"),
    "ine-pro": ("Proto-Indo-European", "原始印歐語"),
    "itc-pro": ("Proto-Italic", "原始義大利語族語"),
    "la": ("Latin", "拉丁語"),
    "la-lat": ("Late Latin", "後期拉丁語"),
    "la-vul": ("Vulgar Latin", "通俗拉丁語"),
    "la-med": ("Medieval Latin", "中世紀拉丁語"),
    "la-new": ("New Latin", "新拉丁語"),
    "grc": ("Ancient Greek", "古希臘語"),
    "itc-ola": ("Old Latin", "古拉丁語"),
    "la-cla": ("Classical Latin", "古典拉丁語"),
    "la-eme": ("Early Medieval Latin", "早期中世紀拉丁語"),
    "la-ecc": ("Ecclesiastical Latin", "教會拉丁語"),
    "el": ("Greek", "希臘語"),
    "it": ("Italian", "義大利語"),
    "roa-oit": ("Old Italian", "古義大利語"),
    "pt": ("Portuguese", "葡萄牙語"),
    "roa-opt": ("Old Galician-Portuguese", "古加利西亞-葡萄牙語"),
    "gl": ("Galician", "加利西亞語"),
    "fr": ("French", "法語"),
    "fro": ("Old French", "古法語"),
    "frm": ("Middle French", "中古法語"),
    "es": ("Spanish", "西班牙語"),
    "osp": ("Old Spanish", "古西班牙語"),
    "ca": ("Catalan", "加泰隆尼亞語"),
    "oc": ("Occitan", "奧克語"),
    "pro": ("Old Occitan", "古奧克語"),
    "ro": ("Romanian", "羅馬尼亞語"),
    "frk": ("Frankish", "法蘭克語"),
    "lng": ("Lombardic", "倫巴底語"),
    "got": ("Gothic", "哥德語"),
    "non": ("Old Norse", "古諾斯語"),
    "de": ("German", "德語"),
    "gmh": ("Middle High German", "中古高地德語"),
    "goh": ("Old High German", "古高地德語"),
    "nl": ("Dutch", "荷蘭語"),
    "dum": ("Middle Dutch", "中古荷蘭語"),
    "sv": ("Swedish", "瑞典語"),
    "da": ("Danish", "丹麥語"),
    "no": ("Norwegian", "挪威語"),
    "is": ("Icelandic", "冰島語"),
    "ru": ("Russian", "俄語"),
    "cel-pro": ("Proto-Celtic", "原始凱爾特語"),
    "ar": ("Arabic", "阿拉伯語"),
    "ota": ("Ottoman Turkish", "鄂圖曼土耳其語"),
    "tr": ("Turkish", "土耳其語"),
    "fa": ("Persian", "波斯語"),
    "sa": ("Sanskrit", "梵語"),
    "he": ("Hebrew", "希伯來語"),
    "zh": ("Chinese", "漢語"),
    "cmn": ("Mandarin", "華語"),
    "ja": ("Japanese", "日語"),
    "nah": ("Nahuatl", "納瓦特爾語"),
    "sem-pro": ("Proto-Semitic", "原始閃米特語"),
}

# --------------------------------------------------------------------------
# Etymology template classes
# --------------------------------------------------------------------------
ANCESTRY_TEMPLATES = {
    "inh": "inh", "inh+": "inh", "inh-lite": "inh", "inherited": "inh",
    "der": "der", "der+": "der", "der-lite": "der", "derived": "der", "uder": "der",
    "bor": "bor", "bor+": "bor", "borrowed": "bor", "lbor": "bor", "slbor": "bor",
    "obor": "bor", "ubor": "bor", "lbor+": "bor",
    "ltc": "ltc", "lt": "ltc",
    "calque": "calque", "cal": "calque", "clq": "calque",
    "sl": "sl", "semantic loan": "sl", "psm": "psm",
}
MENTION_TEMPLATES = {"m", "mention", "l", "link", "ll", "m+"}
COGNATE_TEMPLATES = {"cog", "cognate", "cog+"}
NONCOGNATE_TEMPLATES = {"noncog", "ncog", "nc", "noncognate"}
STOP_TEMPLATES = COGNATE_TEMPLATES | NONCOGNATE_TEMPLATES | {"doublet", "dbt", "piecewise doublet"}
FORMATION_TEMPLATES = {"af", "affix", "suffix", "suf", "prefix", "pre", "compound", "com",
                       "confix", "con", "blend", "clipping", "clip", "back-form", "bf",
                       "univerbation", "univ"}
UNCERTAIN_TEMPLATES = {"unc", "uncertain", "unk", "unknown"}
ROOT_TEMPLATES = {"root"}

# Usage labels kept on senses (everything else, e.g. "countable", is dropped).
USAGE_TAGS = {
    "informal", "formal", "colloquial", "slang", "vulgar", "offensive", "derogatory",
    "humorous", "euphemistic", "figuratively", "figurative", "literary", "poetic",
    "archaic", "dated", "obsolete", "rare", "historical", "British", "UK", "US",
    "American", "Canada", "Australia", "Ireland", "Scotland", "India", "impersonal",
    "transitive", "intransitive", "uncountable", "countable", "idiomatic", "technical",
    "computing", "chess", "law", "medicine", "mathematics", "music", "sports",
    "finance", "business", "biology", "chemistry", "physics", "nautical", "military",
}
TAG_RENAME = {"figuratively": "figurative", "UK": "British", "American": "US"}

UK_TAGS = {"UK", "Received-Pronunciation", "British", "England"}
US_TAGS = {"US", "General-American", "American"}
BR_TAGS = {"Brazil", "Brazilian-Portuguese", "Rio-de-Janeiro", "São-Paulo"}
PTPT_TAGS = {"Portugal", "European-Portuguese", "Lisbon"}

STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "by", "with", "and", "or",
    "is", "are", "be", "that", "which", "who", "it", "its", "as", "from", "into", "one's",
    "something", "someone", "etc", "especially", "usually", "used", "very", "not",
    "when", "where", "can", "you", "your", "their", "this", "some", "any",
}

SKIP_FORM_TAGS = {"canonical", "romanization", "table-tags", "inflection-template",
                  "class", "auxiliary", "error-unrecognized-form"}
MARKED_TR_TAGS = {"dialectal", "regional", "slang", "vulgar", "archaic", "obsolete", "rare", "dated",
                  "poetic", "literary", "pejorative", "derogatory", "colloquial", "informal", "humorous",
                  "Northern", "Southern", "Tuscany", "Sicily", "Canary-Islands", "Andalusia", "Mexico",
                  "Argentina", "Rioplatense", "Quebec", "Belgium", "Switzerland", "Chile", "Caribbean"}
SKIP_POS = {"name", "character", "symbol", "prefix", "suffix", "infix", "interfix", "affix",
            "circumfix", "abbrev", "romanization", "punct", "contraction"}


# --------------------------------------------------------------------------
# Normalization — MUST stay identical to norm() in app.js.
# --------------------------------------------------------------------------
def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("œ", "oe").replace("æ", "ae").replace("ß", "ss").replace("’", "'")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith("M"))
    return re.sub(r"\s+", " ", s)


def akey(form: str) -> str:
    """Comparison key for an etymon: normalized, without the reconstruction asterisk."""
    return norm((form or "").lstrip("*"))


def index_bucket(key: str) -> str:
    """Shard name for a normalized search key — mirrors idxBucket() in app.js.

    Keys starting with a-z are sharded by their first two characters (the second
    one folded to '_' when it is not a-z, or missing); digits share "0"; any other
    script (Chinese, Greek, ...) is hashed on its first code point into 32 shards.
    A prefix of two or more characters therefore always lives in a single shard.
    """
    cp = ord(key[0])
    if 97 <= cp <= 122:
        second = key[1] if len(key) > 1 and "a" <= key[1] <= "z" else "_"
        return chr(cp) + second
    if 48 <= cp <= 57:
        return "0"
    return "x%02x" % (cp % 32)


# Windows cannot store files named like devices (con.json, aux.json, ...), so such
# shard names get a trailing "_" — mirrors safeName() in app.js.
WINDOWS_RESERVED = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(10)} | {f"lpt{i}" for i in range(10)}


def safe_name(bucket: str) -> str:
    return bucket + "_" if bucket in WINDOWS_RESERVED else bucket


def entry_bucket(headword: str) -> str:
    """Shard name for an English headword — mirrors entBucket() in app.js."""
    k = norm(headword)[:ENTRY_PREFIX_LEN]
    b = "".join(ch if "a" <= ch <= "z" else "_" for ch in k)
    return safe_name(b.ljust(ENTRY_PREFIX_LEN, "_"))


def lang_name(code: str) -> tuple[str, str]:
    return LANG_NAMES.get(code, (code, code))


# --------------------------------------------------------------------------
# Input helpers
# --------------------------------------------------------------------------
def open_jsonl(path: str):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


_TEMPLATE_RE = re.compile(r"\{\{([^{}]*)\}\}")


def templates_from_wikitext(text: str) -> list[dict]:
    """Parse '{{inh|en|enm|sumer}} ...' into Wiktextract-style template dicts."""
    out = []
    for m in _TEMPLATE_RE.finditer(text or ""):
        parts = m.group(1).split("|")
        name = parts[0].strip()
        args, pos = {}, 1
        for p in parts[1:]:
            if "=" in p and re.match(r"^\s*[A-Za-z][\w-]*\s*=", p):
                k, v = p.split("=", 1)
                args[k.strip()] = v.strip()
            else:
                args[str(pos)] = p.strip()
                pos += 1
        out.append({"name": name, "args": args})
    return out


def tags_code(tags) -> str | None:
    """Map Wiktextract inflection tags to the short codes used by the app."""
    t = set(tags or [])
    if not t or t & SKIP_FORM_TAGS:
        return None
    if "comparative" in t:
        return "comp"
    if "superlative" in t:
        return "sup"
    if "participle" in t and "past" in t:
        return "pp"
    if ("participle" in t and "present" in t) or "gerund" in t:
        return "ing"
    if "infinitive" in t:
        return "inf"
    if "preterite" in t and "third-person" in t and "singular" in t:
        return "pret3s"
    if "imperfect" in t and "third-person" in t and "singular" in t:
        return "impf3s"
    if "first-person" in t and "singular" in t and "present" in t:
        return "1s"
    if "third-person" in t and "singular" in t and "present" in t:
        return "3s"
    if "past" in t and "plural" in t:
        return "pastpl"
    if "past" in t:
        return "past"
    if "present" in t and "plural" in t:
        return "presp"
    if "feminine" in t and "plural" in t:
        return "fpl"
    if "masculine" in t and "plural" in t:
        return "mpl"
    if "plural" in t:
        return "pl"
    if "feminine" in t:
        return "f"
    return None


def case_code(tags) -> str | None:
    """Describe which inflected form of a lemma an etymon is (e.g. noctem = acc of nox)."""
    t = set(tags or [])
    if "infinitive" in t:
        return "inf"
    if "participle" in t:
        return "ppr" if "present" in t else "ppf"
    for tag, code in (("accusative", "acc"), ("genitive", "gen"), ("ablative", "abl"),
                      ("dative", "dat"), ("nominative", "nom")):
        if tag in t:
            return code + ("pl" if "plural" in t else "")
    if "plural" in t:
        return "pl"
    return None


def first_gloss(rec: dict) -> str:
    for s in rec.get("senses") or []:
        if s.get("form_of") or s.get("alt_of"):
            continue
        gl = s.get("glosses") or s.get("raw_glosses") or []
        if gl:
            return gl[-1]
    return ""


def is_form_of_record(rec: dict) -> bool:
    senses = rec.get("senses") or []
    return bool(senses) and all(s.get("form_of") or s.get("alt_of") or
                                "form-of" in (s.get("tags") or []) for s in senses)


# --------------------------------------------------------------------------
# Etymology parsing
# --------------------------------------------------------------------------
ETYMON_TEMPLATES = {"etymon", "ety"}
ETYMON_REL = {
    "inh": "inh", "inherited": "inh", "der": "der", "derived": "der", "uder": "der",
    "bor": "bor", "borrowed": "bor", "lbor": "bor", "slbor": "bor", "obor": "bor", "ubor": "bor",
    "calque": "calque", "cal": "calque", "sl": "sl", "psm": "psm", "ltc": "ltc",
}
ETYMON_FORMATION = {"af", "affix", "afeq", "compound", "com", "suf", "suffix", "pre", "prefix",
                    "con", "confix", "blend", "univerbation", "univ", "clipping", "back-form", "bf"}
CASE_WORDS = {"accusative": "acc", "genitive": "gen", "ablative": "abl", "dative": "dat",
              "nominative": "nom", "infinitive": "inf", "plural": "pl"}

# English language name -> Wiktionary code. Seeded from LANG_NAMES and extended at
# build time from template expansions and etymon trees (register_lang_name), so the
# prose fallback below only ever maps names that Wiktionary itself paired with a code.
NAME2CODE: dict[str, str] = {v[0]: k for k, v in LANG_NAMES.items()}
_NAMES_SORTED: list[str] = []


def register_lang_name(name: str, code: str):
    name = (name or "").strip()
    if name and code and re.fullmatch(r"[A-Z][\w'’. -]{1,40}", name) and name not in NAME2CODE:
        NAME2CODE[name] = code
        _NAMES_SORTED.clear()


def register_names_from_templates(templates):
    for t in templates or []:
        name = t.get("name") or ""
        a = t.get("args") or {}
        exp = t.get("expansion") or ""
        if name in ANCESTRY_TEMPLATES and a.get("2"):
            form = a.get("4") or a.get("3") or ""
            if form and exp.endswith(form) or (form and form in exp):
                lang = exp.split(form)[0].strip()
                lang = re.sub(r"^(?:Inherited|Borrowed|Derived|Learned borrowing|Semi-learned borrowing|"
                              r"Calque|Partial calque|Semantic loan)\s+(?:from|of)\s+", "", lang)
                register_lang_name(lang, a["2"])
        if '"lang_name"' in exp:
            for ln, code in re.findall(r'"lang_name"\s*:\s*"([^"]+)"\s*,\s*"term"\s*:\s*"[^"]*"\s*,\s*"lang"\s*:\s*"([^"]+)"', exp):
                register_lang_name(ln, code)


_ETY_JSON_START = re.compile(
    r'"\s*,\s*"(?=(?:terms|keyword|keyword_label|keyword_abbrev|status|children|id|lang_name|term|lang|'
    r'transliteration|is_invisible|t|gloss|pos|alt)"\s*:)')


def etymon_tree(expansion: str):
    """Recover the ancestor tree that Wiktextract leaves (truncated at the front)
    inside the expansion of {{etymon}} / {{ety}}. Returns the root term object."""
    if not expansion or '"lang_name"' not in expansion:
        return None
    cut = expansion.rfind('" data-id="')
    s = expansion[:cut] if cut > 0 else expansion
    m = _ETY_JSON_START.search(s)
    if not m:
        return None
    s = s[m.end() - 1:]
    depth, unmatched, last_close, in_str, i = [], [], -1, False, 0
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "{[":
            depth.append(c)
        elif c in "}]":
            if depth:
                depth.pop()
            else:
                unmatched.append("{" if c == "}" else "[")
                last_close = i
        i += 1
    if last_close < 0:
        return None
    prefix, prev = "", None
    for o in reversed(unmatched):
        if prev == "{":
            prefix += '"_":'
        prefix += o
        prev = o
    try:
        return json.loads(prefix + s[:last_close + 1])
    except json.JSONDecodeError:
        return None


def tree_chain(tree) -> list[dict]:
    """Follow the first visible single-parent relation from the word to its oldest ancestor."""
    nodes, cur = [], tree
    for _ in range(24):
        if not isinstance(cur, dict):
            break
        groups = [g for g in (cur.get("children") or cur.get("_") or []) if isinstance(g, dict)
                  and not g.get("is_invisible") and g.get("keyword") != "root"]
        groups = [g for g in groups if g.get("terms") or g.get("_")]
        if not groups:
            break
        g = groups[0]
        terms = [t for t in (g.get("terms") or g.get("_") or []) if isinstance(t, dict) and t.get("lang") and t.get("term")]
        kw = (g.get("keyword") or "").lower()
        if len(terms) != 1 or kw in ETYMON_FORMATION:
            break
        t = terms[0]
        register_lang_name(t.get("lang_name"), t["lang"])
        node = {"l": t["lang"], "f": t["term"], "t": ETYMON_REL.get(kw, "der" if kw else "inh")}
        if t.get("transliteration"):
            node["tr"] = t["transliteration"]
        if t.get("t") or t.get("gloss"):
            node["g"] = t.get("t") or t.get("gloss")
        nodes.append(node)
        cur = t
    return nodes


_TERM_RE = re.compile(r"^([a-z]{2,3}(?:-[a-z]{2,5}){0,2}):(.+)$")


def etymon_args_chain(a: dict, self_lang: str):
    """{{etymon|it|:inh|la:nox<id:night><t:night>}} -> ([parent node], formation or None)."""
    rel, parts = None, []
    for k in sorted((k for k in a if k.isdigit() and int(k) >= 2), key=int):
        v = (a[k] or "").strip()
        if not v:
            continue
        if v.startswith(":"):
            if parts or (rel and rel in ETYMON_REL):
                break
            rel = v[1:].lower()
            continue
        if rel is None:
            continue
        mods = dict(re.findall(r"<(\w+):([^>]*)>", v))
        v = re.sub(r"<[^>]*>", "", v)
        m = _TERM_RE.match(v)
        lang, term = (m.group(1), m.group(2)) if m else (self_lang, v)
        node = {"l": lang, "f": term, "t": ETYMON_REL.get(rel, "der")}
        if mods.get("t") or mods.get("gloss"):
            node["g"] = mods.get("t") or mods.get("gloss")
        if mods.get("tr"):
            node["tr"] = mods["tr"]
        if rel in ETYMON_REL:
            return [node], None
        parts.append(term)
    if rel in ETYMON_FORMATION and parts:
        return [], {"l": self_lang, "parts": parts}
    return [], None


def _names_sorted():
    if not _NAMES_SORTED:
        _NAMES_SORTED.extend(sorted(NAME2CODE, key=len, reverse=True))
    return _NAMES_SORTED


def text_chain(text: str) -> list[dict]:
    """Fallback: read 'from <Language> <term> (“gloss”)' steps out of the etymology prose.
    Only languages already paired with a code (NAME2CODE) are accepted."""
    if not text:
        return []
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if lines and lines[0].lower() == "etymology tree":
        lines = [ln for ln in lines[1:] if re.search(r"\bfrom\b", ln) or ln.endswith(".")]
    prose = " ".join(lines)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", prose)
    kept = []
    for i, s in enumerate(sentences):
        if i == 0 or re.match(r"^(?:Ultimately|In turn|Itself|Probably|Possibly|Perhaps)?\s*(?:from|inherited|borrowed|derived)\b", s, re.I):
            kept.append(s)
        else:
            break
    segs = re.split(r"\bfrom\s+", " ".join(kept))
    nodes = []
    for idx, seg in enumerate(segs[1:], 1):
        seg = seg.strip()
        name = next((n for n in _names_sorted() if seg.startswith(n + " ")), None)
        if not name:
            break
        rest = seg[len(name):].strip()
        m = re.match(r"^(\*?[^\s,;(]+(?:\s+(?!\()[^\s,;(]+)?)", rest)
        if not m:
            break
        term = m.group(1).rstrip(".")
        if len(term.split()) == 2 and not term.split()[1][:1].islower():
            term = term.split()[0]
        before = segs[idx - 1].lower()
        rel = "bor" if re.search(r"borrow", before) else ("inh" if "inherit" in before else "der")
        node = {"l": NAME2CODE[name], "f": term, "t": rel}
        g = re.search(r"\(“([^”]+)”", rest)
        if g:
            node["g"] = g.group(1)
        lm = re.match(r"^[^,;]*,\s*(?:the\s+)?(\w+)\s+(?:singular\s+|plural\s+)?of\s+\*?([^\s,;.(]+)", rest)
        if lm and lm.group(1).lower() in CASE_WORDS:
            node["lm"] = lm.group(2)
            node["lmt"] = CASE_WORDS[lm.group(1).lower()]
        nodes.append(node)
    return nodes


def _same_node(a: dict, b: dict) -> bool:
    if a["l"] != b["l"]:
        return False
    ka = {akey(a.get("f")), akey(a.get("lm"))} - {""}
    kb = {akey(b.get("f")), akey(b.get("lm"))} - {""}
    return bool(ka & kb)


def clean_ety_text(text: str, limit: int = 700) -> str:
    lines = [ln.strip() for ln in (text or "").split("\n") if ln.strip()]
    if lines and lines[0].lower() == "etymology tree":
        i = 1
        while i < len(lines) and not (re.search(r"\bfrom\b", lines[i]) or lines[i].endswith(".")):
            i += 1
        lines = lines[i:]
    out = " ".join(lines)
    if len(out) > limit:
        cut = out.rfind(". ", 0, limit)
        out = out[:cut + 1] if cut > 200 else out[:limit].rstrip() + "…"
    return out


def parse_etymology(templates: list[dict], text: str | None = None, self_lang: str = "") -> dict:
    """Turn etymology templates (+ optional prose) into {chain, cog, form, unc}.

    Sources, in order of preference: classic {{inh}}/{{der}}/{{bor}} chains or the
    ancestor tree recovered from {{etymon}}/{{ety}} (whichever is longer); then the
    chain is continued with steps read from the prose (codes via NAME2CODE)."""
    et_chain: list[dict] = []
    et_form = None
    for t in templates or []:
        if (t.get("name") or "") in ETYMON_TEMPLATES:
            a = {str(k): (v if isinstance(v, str) else str(v)) for k, v in (t.get("args") or {}).items()}
            nodes = tree_chain(etymon_tree(t.get("expansion") or ""))
            if not nodes:
                nodes, form = etymon_args_chain(a, a.get("1") or self_lang)
                et_form = et_form or form
            if len(nodes) > len(et_chain):
                et_chain = nodes
    chain: list[dict] = []
    cogs: list[dict] = []
    roots: list[dict] = []
    formation = None
    pending_unc = False
    stopped = False
    for t in templates or []:
        name = (t.get("name") or "").strip()
        a = {str(k): (v if isinstance(v, str) else str(v)) for k, v in (t.get("args") or {}).items()}
        if name in UNCERTAIN_TEMPLATES:
            pending_unc = True
            continue
        if name in STOP_TEMPLATES:
            stopped = True
            if name in COGNATE_TEMPLATES and a.get("1") and a.get("2") and len(cogs) < 8:
                c = {"l": a["1"], "f": a["2"]}
                if a.get("tr"):
                    c["tr"] = a["tr"]
                cogs.append(c)
            continue
        if name in ROOT_TEMPLATES and a.get("2") and a.get("3"):
            roots.append({"l": a["2"], "f": a["3"], "t": "root"})
            continue
        if stopped:
            continue
        if name in ANCESTRY_TEMPLATES:
            src = (a.get("2") or "").strip()
            lemma_arg = (a.get("3") or "").strip().split(",")[0].strip()   # "nighte,night,nyght" -> first spelling
            form = (a.get("4") or lemma_arg).strip()       # arg 4 = displayed form
            if not src or src == "-" or not form or form == "-":
                continue                          # language-only step ("from Latin"): nothing to show
            node = {"l": src, "f": form, "t": ANCESTRY_TEMPLATES[name]}
            if lemma_arg and lemma_arg != "-" and akey(lemma_arg) != akey(form):
                node["lm"] = lemma_arg
            gloss = a.get("5") or a.get("t") or a.get("gloss")
            if gloss:
                node["g"] = gloss
            if a.get("tr"):
                node["tr"] = a["tr"]
            if pending_unc:
                node["unc"] = True
                pending_unc = False
            if chain and chain[-1]["l"] == src and akey(chain[-1]["f"]) == akey(form):
                continue
            chain.append(node)
        elif name in MENTION_TEMPLATES:
            # "... from {{inh|it|la|noctem}}, accusative of {{m|la|nox||night}}"
            if chain and a.get("1") == chain[-1]["l"] and a.get("2"):
                last = chain[-1]
                if akey(a["2"]) != akey(last["f"]) and "lm" not in last:
                    last["lm"] = a["2"]
                g = a.get("4") or a.get("t") or a.get("gloss")
                if g and "g" not in last:
                    last["g"] = g
        elif name in FORMATION_TEMPLATES and not chain and formation is None:
            parts = [a[k] for k in sorted((k for k in a if k.isdigit() and int(k) >= 2), key=int) if a[k]]
            if parts:
                formation = {"l": a.get("1", ""), "parts": parts}
    if len(et_chain) > len(chain):
        chain = et_chain
    if formation is None and not chain:
        formation = et_form
    if text:
        tc = text_chain(text)
        if not chain and not formation:
            chain = tc
        elif chain and tc:
            idx = next((i for i, n in enumerate(tc) if _same_node(n, chain[-1])), None)
            if idx is not None:
                if tc[idx].get("lm") and not chain[-1].get("lm"):
                    chain[-1]["lm"], chain[-1]["lmt"] = tc[idx]["lm"], tc[idx].get("lmt")
                have = {node_key(n) for n in chain}
                chain = chain + [n for n in tc[idx + 1:] if node_key(n) not in have]
    for r in roots:
        if not any(n["l"] == r["l"] for n in chain):
            chain.append(r)
    out = {"chain": chain}
    if cogs:
        out["cog"] = cogs
    if formation:
        out["form"] = formation
    if pending_unc or (not chain and not formation and any(
            (t.get("name") or "") in UNCERTAIN_TEMPLATES for t in templates or [])):
        out["unc"] = True
    return out


def node_key(n: dict) -> str:
    return n["l"] + ":" + akey(n.get("lm") or n.get("f") or "?")


class AncestorIndex:
    """(lang, normalized form) -> {lemma, g, chain, case} for chain extension."""

    def __init__(self):
        self.map: dict[tuple[str, str], dict] = {}

    def add(self, lang: str, lemma: str, gloss: str, chain: list[dict], forms=()):
        rec = {"lemma": lemma, "g": gloss, "chain": chain}
        key = (lang, akey(lemma))
        cur = self.map.get(key)
        if cur is None or cur.get("case") or (not cur["chain"] and chain):
            self.map[key] = rec
        for form, tags in forms:
            if not form or set(tags or []) & SKIP_FORM_TAGS or akey(form) == akey(lemma):
                continue
            self.alias(lang, form, lemma, tags, rec)

    def alias(self, lang: str, form: str, lemma: str, tags=None, rec=None):
        """Make an inflected form (Latin 'noctem') resolve to its lemma ('nox')."""
        rec = rec or self.map.get((lang, akey(lemma)))
        k = (lang, akey(form))
        if rec is None or (k in self.map and not self.map[k].get("case")):
            return
        if k not in self.map:
            alias = dict(rec)
            code = case_code(tags)
            if code:
                alias["case"] = code
            self.map[k] = alias

    def get(self, lang: str, form: str):
        if not form:
            return None
        return self.map.get((lang, akey(form)))

    def enrich(self, node: dict):
        rec = self.get(node["l"], node.get("lm") or node.get("f"))
        if not rec:
            return None
        if not node.get("lm") and akey(rec["lemma"]) != akey(node.get("f", "")):
            node["lm"] = rec["lemma"]
            if rec.get("case"):
                node["lmt"] = rec["case"]
        if not node.get("g") and rec.get("g"):
            node["g"] = rec["g"]
        return rec

    def extend(self, chain: list[dict], limit: int = 14) -> list[dict]:
        out = [dict(n) for n in chain]
        seen = {node_key(n) for n in out}
        for n in out:
            self.enrich(n)
        while out and len(out) < limit:
            rec = self.get(out[-1]["l"], out[-1].get("lm") or out[-1].get("f"))
            if not rec or not rec["chain"]:
                break
            added = False
            for n in rec["chain"]:
                k = node_key(n)
                if k in seen:
                    continue
                m = dict(n)
                self.enrich(m)
                out.append(m)
                seen.add(k)
                added = True
            if not added:
                break
        return out


def synth_ety_text(ety: dict) -> str:
    """Readable English etymology when the dump has no etymology_text."""
    parts = []
    for i, n in enumerate(ety.get("chain") or []):
        name = lang_name(n["l"])[0]
        verb = {"bor": "borrowed from", "der": "derived from", "calque": "calqued on",
                "ltc": "learned borrowing from", "root": "ultimately from the root"}.get(n.get("t"), "from")
        if i == 0:
            verb = verb[0].upper() + verb[1:]
        form = n.get("f") or ""
        if n.get("tr"):
            form += f" ({n['tr']})"
        if n.get("lm"):
            form += f", a form of {n['lm']}"
        gloss = f" (“{n['g']}”)" if n.get("g") else ""
        unc = "possibly " if n.get("unc") else ""
        parts.append(f"{unc}{verb} {name} {form}{gloss}".replace("  ", " ").strip())
    text = ", ".join(parts) + ("." if parts else "")
    if ety.get("form"):
        text = (text + " " if text else "") + "From " + " + ".join(ety["form"]["parts"]) + "."
    if ety.get("unc"):
        text = (text + " " if text else "") + "Further origin uncertain."
    if ety.get("cog"):
        cg = ", ".join(f"{lang_name(c['l'])[0]} {c['f']}" for c in ety["cog"])
        text += f" Cognate with {cg}."
    return text.strip()


# --------------------------------------------------------------------------
# Record slimming (keeps memory low when streaming multi-GB dumps)
# --------------------------------------------------------------------------
_KEEP_TEMPLATES = (set(ANCESTRY_TEMPLATES) | MENTION_TEMPLATES | STOP_TEMPLATES | FORMATION_TEMPLATES
                   | UNCERTAIN_TEMPLATES | ROOT_TEMPLATES | ETYMON_TEMPLATES)


def slim_templates(templates):
    out = []
    for t in templates or []:
        name = t.get("name") or ""
        if name not in _KEEP_TEMPLATES:
            continue
        d = {"name": name, "args": t.get("args") or {}}
        if name in ETYMON_TEMPLATES or name in ANCESTRY_TEMPLATES:
            d["expansion"] = t.get("expansion") or ""
        out.append(d)
    return out


def slim_en(rec: dict) -> dict:
    keep = {k: rec[k] for k in ("word", "lang_code", "pos", "etymology_number",
                                "etymology_text", "sounds",
                                "forms", "synonyms", "antonyms", "derived") if k in rec}
    keep["etymology_templates"] = slim_templates(rec.get("etymology_templates"))
    keep["translations"] = [t for t in rec.get("translations") or [] if _tr_lang(t)]
    senses = []
    for s in rec.get("senses") or []:
        ss = {k: s[k] for k in ("glosses", "raw_glosses", "tags", "topics", "examples",
                                "synonyms", "antonyms", "form_of", "alt_of") if k in s}
        for t in s.get("translations") or []:
            if _tr_lang(t):
                t = dict(t)
                t.setdefault("sense", (s.get("glosses") or [""])[-1])
                keep["translations"].append(t)
        senses.append(ss)
    keep["senses"] = senses
    return keep


def slim_other(rec: dict) -> dict:
    keep = {k: rec[k] for k in ("word", "lang_code", "pos", "etymology_text", "sounds",
                                "head_templates", "tags") if k in rec}
    keep["etymology_templates"] = slim_templates(rec.get("etymology_templates"))
    keep["forms"] = [{"form": f["form"], "tags": f.get("tags") or []} for f in rec.get("forms") or []
                     if f.get("form") and not set(f.get("tags") or []) & SKIP_FORM_TAGS][:120]
    keep["senses"] = [{k: s[k] for k in ("glosses", "tags", "form_of", "alt_of") if k in s}
                      for s in (rec.get("senses") or [])[:12]]
    return keep


ZH_DIALECT_TAGS = {"Cantonese", "Hokkien", "Dungan", "Hakka", "Wu", "Teochew", "Min-Nan", "Min-Dong",
                   "Taishanese", "Jin", "Xiang", "Gan", "Min-Bei", "Puxian-Min", "Shanghainese"}
_CJK_RE = re.compile(r"[㐀-鿿豈-﫿]")


def _tr_lang(t: dict) -> str | None:
    code = t.get("lang_code") or t.get("code") or ""
    lang = t.get("lang") or ""
    if code in ROMANCE:
        return code
    tags = set(t.get("tags") or [])
    if code == "cmn" or lang in ("Chinese Mandarin", "Mandarin") or (code == "zh" and "Mandarin" in tags):
        return "zh" if _CJK_RE.search(t.get("word") or "") else None
    if code == "zh" and lang == "Chinese" and not tags & ZH_DIALECT_TAGS and _CJK_RE.search(t.get("word") or ""):
        return "zh"
    return None


def zh_trad(word: str) -> str:
    """'詞典 /词典' (traditional / simplified) -> '詞典'."""
    return (word or "").split(" /")[0].split("/")[0].strip()


# --------------------------------------------------------------------------
# Romance word processing
# --------------------------------------------------------------------------
IT_IMPURE = re.compile(r"^(s[bcdfgklmnpqrstvz]|z|gn|ps|pn|x|y|i[aeiou])")
ES_STRESSED_A = {"agua", "águila", "alma", "arma", "hambre", "hacha", "área", "aula",
                 "ave", "hada", "ala", "ancla", "arca", "asma", "aya", "haba", "habla", "alba"}
FR_ASPIRATED_H = {"haricot", "héros", "hibou", "hache", "haine", "honte", "hasard",
                  "hauteur", "hêtre", "homard", "hamac", "harpe", "haut", "halte"}
VOWELS = set("aeiouàáâãäåèéêëìíîïòóôõöùúûüœæy")


def article(lang: str, word: str, g: str | None, plural: bool = False) -> str | None:
    if g not in ("m", "f"):
        return None
    w = word.lower()
    first = w[:1]
    if lang == "it":
        vowel = first in VOWELS and first != "y"
        if g == "m":
            if plural:
                return "gli" if (vowel or IT_IMPURE.match(w)) else "i"
            if IT_IMPURE.match(w):
                return "lo"
            return "l'" if vowel or first == "h" else "il"
        if plural:
            return "le"
        return "l'" if vowel else "la"
    if lang == "pt":
        return ("os" if plural else "o") if g == "m" else ("as" if plural else "a")
    if lang == "fr":
        if plural:
            return "les"
        if (first in VOWELS or (first == "h" and w not in FR_ASPIRATED_H)):
            return "l'"
        return "le" if g == "m" else "la"
    if lang == "es":
        if g == "m":
            return "los" if plural else "el"
        if plural:
            return "las"
        return "el" if w in ES_STRESSED_A else "la"
    return None


def detect_gender(rec: dict, extra_tags=()) -> str | None:
    tags = set(extra_tags)
    tags.update(rec.get("tags") or [])
    for s in rec.get("senses") or []:
        tags.update(s.get("tags") or [])
    for h in rec.get("head_templates") or []:
        exp = h.get("expansion") or ""
        rest = exp[len(rec.get("word", "")):].strip().split(" (")[0].strip()
        if rest in ("m", "m sg"):
            tags.add("masculine")
        elif rest in ("f", "f sg"):
            tags.add("feminine")
        elif rest in ("m or f", "mf", "m/f", "f or m", "m-f", "by sense"):
            tags.update(("masculine", "feminine"))
        args = h.get("args") or {}
        g = args.get("1") or args.get("g")
        if g in ("m", "f"):
            tags.add("masculine" if g == "m" else "feminine")
        elif g in ("mf", "m-f", "mfbysense", "mfequiv"):
            tags.update(("masculine", "feminine"))
    m, f = "masculine" in tags, "feminine" in tags
    if m and f:
        return "mf"
    return "m" if m else ("f" if f else None)


def pick_ipa(sounds, lang):
    out = {}
    for snd in sounds or []:
        ipa = snd.get("ipa")
        if not ipa:
            continue
        tags = set(snd.get("tags") or [])
        if lang == "pt":
            if tags & BR_TAGS and "ipaBR" not in out:
                out["ipaBR"] = ipa
            if tags & PTPT_TAGS and "ipaPT" not in out:
                out["ipaPT"] = ipa
        out.setdefault("ipa", ipa)
    return out


class RomanceLexicon:
    def __init__(self):
        self.by_word: dict[tuple[str, str], list[dict]] = defaultdict(list)

    def add(self, rec: dict):
        lang = rec.get("lang_code")
        if lang not in ROMANCE or is_form_of_record(rec):
            return
        self.by_word[(lang, rec["word"])].append(rec)

    def records(self):
        for (lang, word), recs in self.by_word.items():
            for r in recs:
                yield lang, word, r

    def pick(self, lang, word, pos):
        recs = self.by_word.get((lang, word)) or []
        for r in recs:
            if r.get("pos") == pos:
                return r
        return recs[0] if recs else None


def romance_word(lang, word, pos, tr_tags, lex: RomanceLexicon, anc: AncestorIndex,
                 variant=None) -> dict:
    rec = lex.pick(lang, word, pos)
    out = {"w": word}
    if variant:
        out["v"] = variant
    if not rec:
        g = detect_gender({"word": word}, tr_tags)
        if g:
            out["g"] = g
            art = article(lang, word, g)
            if art:
                out["art"] = art
        return out
    out["p"] = rec.get("pos")
    g = detect_gender(rec, tr_tags) if rec.get("pos") in ("noun", None) else None
    if g:
        out["g"] = g
    forms = {}
    for f in rec.get("forms") or []:
        code = tags_code(f.get("tags"))
        if code and code not in forms and f.get("form") and f["form"] != word:
            forms[code] = f["form"]
    if out.get("g") in ("m", "f") and out.get("p") == "noun":
        art = article(lang, word, out["g"])
        if art:
            out["art"] = art
        if "pl" in forms:
            out["pl"] = forms["pl"]
            pa = article(lang, forms["pl"], out["g"], plural=True)
            if pa:
                out["plArt"] = pa
    elif "pl" in forms:
        out["pl"] = forms["pl"]
    if "f" in forms and out.get("p") in ("adj", "noun"):
        out["fem"] = forms["f"]
    out.update(pick_ipa(rec.get("sounds"), lang))
    gl = first_gloss(rec)
    if gl:
        out["gl"] = gl if len(gl) <= 90 else gl[:88].rstrip() + "…"
    ety = parse_etymology(rec.get("etymology_templates"), rec.get("etymology_text"), lang)
    ety["chain"] = anc.extend(ety["chain"])
    text = clean_ety_text(rec.get("etymology_text") or "", 320) or synth_ety_text(ety)
    e = {"chain": ety["chain"]}
    if text:
        e["text"] = text
    if ety.get("unc"):
        e["unc"] = True
    if ety.get("form"):
        e["form"] = ety["form"]
    out["ety"] = e
    return out


# --------------------------------------------------------------------------
# English entry processing
# --------------------------------------------------------------------------
def tokens(s: str) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z0-9']+", (s or "").lower()):
        if w in STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def match_score(label: str, gloss: str) -> float:
    a, b = tokens(label), tokens(gloss)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a)


def split_zh(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[；;，,、/]", s or "") if p.strip()]


class ZhConverter:
    def __init__(self):
        self.cc = None
        try:
            import opencc  # type: ignore
            for cfg in ("s2twp", "s2twp.json", "s2t", "s2t.json"):
                try:
                    self.cc = opencc.OpenCC(cfg)
                    break
                except Exception:
                    continue
        except ImportError:
            pass

    def __call__(self, s: str) -> str:
        return self.cc.convert(s) if self.cc else s


def process_english(word: str, records: list[dict], lex: RomanceLexicon,
                    anc: AncestorIndex, zh_conv: ZhConverter, max_groups: int = 6):
    records = [r for r in records if not is_form_of_record(r) and r.get("pos") not in SKIP_POS]
    if not records:
        return None

    # ---- etymologies (one per etymology_number)
    ety_list, ety_of_rec = [], []
    ety_seen: dict = {}
    for r in records:
        k = r.get("etymology_number") or (r.get("etymology_text") or "")[:80] or 0
        if k not in ety_seen:
            parsed = parse_etymology(r.get("etymology_templates"), r.get("etymology_text"), "en")
            parsed["chain"] = anc.extend(parsed["chain"])
            text = clean_ety_text(r.get("etymology_text") or "", 600) or synth_ety_text(parsed)
            e = {"n": len(ety_list) + 1, "chain": parsed["chain"]}
            if text:
                e["text"] = text
            for opt in ("cog", "unc", "form"):
                if parsed.get(opt):
                    e[opt] = parsed[opt]
            ety_seen[k] = len(ety_list)
            ety_list.append(e)
        ety_of_rec.append(ety_seen[k])

    # ---- pronunciation
    ipa = {}
    for r in records:
        for snd in r.get("sounds") or []:
            if not snd.get("ipa"):
                continue
            tags = set(snd.get("tags") or [])
            if tags & UK_TAGS:
                ipa.setdefault("uk", snd["ipa"])
            if tags & US_TAGS:
                ipa.setdefault("us", snd["ipa"])
            ipa.setdefault("_any", snd["ipa"])
    if "_any" in ipa:
        anyipa = ipa.pop("_any")
        ipa.setdefault("uk", anyipa)
        ipa.setdefault("us", anyipa)

    # ---- POS blocks, senses and translation groups
    pos_blocks, groups = [], []
    zh_all: list[str] = []
    for ri, r in enumerate(records):
        senses = []
        for s in r.get("senses") or []:
            if s.get("form_of") or s.get("alt_of"):
                continue
            gl = (s.get("glosses") or s.get("raw_glosses") or [""])[-1]
            if not gl:
                continue
            sense = {"d": gl}
            tags = []
            for t in list(s.get("tags") or []) + list(s.get("topics") or []):
                if t in USAGE_TAGS:
                    t = TAG_RENAME.get(t, t)
                    if t not in tags:
                        tags.append(t)
            if tags:
                sense["tags"] = tags
            exs = [e for e in s.get("examples") or [] if e.get("text") and len(e["text"]) < 170]
            exs.sort(key=lambda e: e.get("type") not in (None, "example"))
            ex = [e["text"] for e in exs if e.get("type") in (None, "example") or len(e["text"]) < 140][:2]
            if ex:
                sense["ex"] = ex
            ssyn = [x["word"] for x in s.get("synonyms") or [] if x.get("word")][:6]
            if ssyn:
                sense["syn"] = ssyn
            senses.append(sense)
            if len(senses) >= 10:
                break
        if not senses:
            continue
        forms, seen_forms = [], set()
        for f in r.get("forms") or []:
            code = tags_code(f.get("tags"))
            form = f.get("form")
            if not code or not form or form == word or (code, form) in seen_forms:
                continue
            seen_forms.add((code, form))
            item = [code, form]
            lbl = [t for t in f.get("tags") or [] if t in ("archaic", "rare", "dated", "obsolete", "British", "US")]
            if lbl:
                item.append(TAG_RENAME.get(lbl[0], lbl[0]))
            forms.append(item)
        block = {"p": r.get("pos"), "e": ety_of_rec[ri], "senses": senses}
        if forms:
            block["forms"] = forms[:10]
        bi = len(pos_blocks)
        pos_blocks.append(block)

        # translation tables of this record, keyed by their sense label
        tables: "OrderedDict[str, dict]" = OrderedDict()
        for t in r.get("translations") or []:
            lang = _tr_lang(t)
            w = (t.get("word") or "").strip()
            if not lang or not w or w.startswith("-"):
                continue
            tags = set(t.get("tags") or [])
            label = (t.get("sense") or "").strip()
            tab = tables.setdefault(label, {l: [] for l in ROMANCE + ("zh",)})
            if lang == "zh":
                if "Simplified-Chinese" in tags or "Simplified Chinese" in tags:
                    tab.setdefault("_zhs", []).append(w)
                    continue
                w = zh_trad(w)
                if not w or w in tab["zh"] or w in tab.get("_zhmain", []):
                    continue
                if "Taiwan" in tags:
                    tab["zh"].insert(0, w)           # Taiwanese usage first for our readers
                elif "Mainland-China" in tags:
                    tab.setdefault("_zhmain", []).append(w)
                else:
                    tab["zh"].append(w)
                continue
            variant = None
            if lang == "pt":
                if tags & BR_TAGS:
                    variant = "BR"
                elif tags & PTPT_TAGS:
                    variant = "PT"
            if all(x[0] != w for x in tab[lang]):
                tab[lang].append((w, sorted(tags), variant))
        for label, tab in tables.items():
            if not tab["zh"] and tab.get("_zhmain"):
                tab["zh"] = tab["_zhmain"]
            if not tab["zh"] and tab.get("_zhs"):
                tab["zh"] = list(OrderedDict.fromkeys(zh_conv(x) for x in tab["_zhs"]))
            if not any(tab[l] for l in ROMANCE):
                continue
            scores = [match_score(label, s["d"]) for s in senses]
            best = max(range(len(senses)), key=lambda i: (scores[i], -i)) if senses else 0
            groups.append({"label": label, "_block": bi, "_best": best, "_tab": tab, "_order": len(groups),
                           "_scores": scores, "p": r.get("pos"), "e": ety_of_rec[ri]})

    if not pos_blocks:
        return None

    # rank groups: keep those with the widest language coverage, then order by sense
    groups.sort(key=lambda g: -sum(1 for l in ROMANCE if g["_tab"][l]))
    groups = groups[:max_groups]
    # Row 1 = the main meaning: the most-translated table of the first part of speech
    # (table order in the dumps does not reliably follow the senses). The other rows
    # follow the senses they best match, ties keeping Wiktionary's table order.
    size = lambda g: sum(len(g["_tab"][l]) for l in ROMANCE + ("zh",))
    first_block = min((g["_block"] for g in groups), default=0)
    firsts = [g for g in groups if g["_block"] == first_block]
    by_sense = max(firsts, key=lambda g: (g["_scores"][0] if g["_scores"] else 0, -g["_order"]), default=None)
    if by_sense is not None and by_sense["_scores"] and by_sense["_scores"][0] >= 0.34:
        main = by_sense                  # the table that matches the first (main) sense
    else:
        main = max(firsts, key=lambda g: (size(g), -g["_order"]), default=None)
    groups.sort(key=lambda g: (g is not main, g["_block"], g["_best"], g["_order"]))

    out_groups = []
    lx: dict[str, dict] = {}
    for gi, g in enumerate(groups):
        tab = g["_tab"]
        tr = {}
        for lang in ROMANCE:
            refs = []
            # prefer ordinary words: skip dialectal/slang/archaic/rare ones when a plain word exists
            plain = [x for x in tab[lang] if not set(x[1]) & MARKED_TR_TAGS]
            for w, tags, variant in (plain or tab[lang])[:3]:
                # each Romance word is stored once per entry (entry["lx"]); rows refer to it
                k = f"{lang}:{w}" + (f"|{variant}" if variant else "")
                if k not in lx:
                    lx[k] = romance_word(lang, w, g["p"], tags, lex, anc, variant)
                refs.append(k)
            tr[lang] = refs
        zh = [zh_conv(x) for x in tab["zh"][:4]]
        og = {"label": g["label"], "zh": zh, "p": g["p"], "e": g["e"], "tr": tr}
        out_groups.append(og)
        for z in zh:
            if z not in zh_all:
                zh_all.append(z)
        g["_gi"] = gi

    # attach each sense to its best-matching group of the same POS block (for zh glosses)
    for bi, block in enumerate(pos_blocks):
        cands = [g for g in groups if g["_block"] == bi]
        for si, sense in enumerate(block["senses"]):
            best, best_score = None, 0.0
            for g in cands:
                sc = g["_scores"][si] if si < len(g["_scores"]) else 0.0
                if g["_best"] == si:
                    sc += 1.0
                if sc > best_score:
                    best, best_score = g, sc
            if best is None and len(cands) == 1 and len(block["senses"]) == 1:
                best = cands[0]
            if best is not None:
                sense["grp"] = best["_gi"]
                zh = out_groups[best["_gi"]]["zh"]
                if zh:
                    sense["zh"] = "；".join(zh[:3])

    def words_of(key, limit):
        out = []
        for r in records:
            for x in r.get(key) or []:
                w = x.get("word") if isinstance(x, dict) else x
                if w and w != word and w not in out:
                    out.append(w)
        return out[:limit]

    entry = {"w": word, "zh": zh_all[:5], "ipa": ipa, "ety": ety_list, "pos": pos_blocks,
             "grp": out_groups, "lx": lx}
    for key, name, limit in (("synonyms", "syn", 10), ("antonyms", "ant", 8), ("derived", "phr", 12)):
        vals = words_of(key, limit)
        if vals:
            entry[name] = vals
    return entry


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def build(en_records, rom_records, anc_records, out_dir, wanted=None, source="kaikki",
          extra_forms=None, zh_conv=None, rank=None):
    zh_conv = zh_conv or ZhConverter()
    en_records = list(en_records)
    rom_records = list(rom_records)
    anc_records = list(anc_records)
    # language names Wiktionary pairs with codes (for the prose fallback)
    for r in en_records + rom_records + anc_records:
        register_names_from_templates(r.get("etymology_templates"))
    anc = AncestorIndex()
    form_of_anc = []
    for r in anc_records:
        if is_form_of_record(r):
            form_of_anc.append(r)
            continue
        chain = parse_etymology(r.get("etymology_templates"), r.get("etymology_text"), r["lang_code"])["chain"]
        forms = [(f.get("form"), f.get("tags")) for f in r.get("forms") or [] if f.get("form")]
        anc.add(r["lang_code"], r["word"], first_gloss(r), chain, forms)
    for r in form_of_anc:
        for s in r.get("senses") or []:
            for fo in s.get("form_of") or []:
                if fo.get("word"):
                    anc.alias(r["lang_code"], r["word"], fo["word"], s.get("tags"))
    lex = RomanceLexicon()
    for r in rom_records:
        lex.add(r)
    for lang, word, r in lex.records():
        chain = parse_etymology(r.get("etymology_templates"), r.get("etymology_text"), lang)["chain"]
        anc.add(lang, word, first_gloss(r), chain)

    by_word: "OrderedDict[str, list]" = OrderedDict()
    form_of: list[tuple[str, str, str]] = list(extra_forms or [])
    for r in en_records:
        if r.get("lang_code", "en") != "en":
            continue
        if is_form_of_record(r):
            for s in r.get("senses") or []:
                for fo in s.get("form_of") or []:
                    if fo.get("word"):
                        form_of.append((r["word"], fo["word"], tags_code(s.get("tags")) or "form"))
            continue
        if wanted is not None and r["word"] not in wanted:
            continue
        by_word.setdefault(r["word"], []).append(r)

    entries = {}
    for word, recs in by_word.items():
        e = process_english(word, recs, lex, anc, zh_conv)
        if e and e["grp"]:
            entries[word] = e
    print(f"  {len(entries)} English entries with Romance translations", file=sys.stderr)

    # ---- reverse / inflection index
    index: dict[str, list] = defaultdict(list)

    def add(form, hit):
        k = norm(form)
        if not k:
            return
        lst = index[k]
        sig = (hit["h"], hit["l"], hit["r"], hit.get("f"), hit.get("m"))
        if any((h["h"], h["l"], h["r"], h.get("f"), h.get("m")) == sig for h in lst):
            return
        if len(lst) < 16:
            lst.append(hit)

    rom_forms_cache = {}
    for hw, e in entries.items():
        add(hw, {"h": hw, "l": "en", "f": hw, "r": "hw"})
        for b in e["pos"]:
            for item in b.get("forms") or []:
                add(item[1], {"h": hw, "l": "en", "f": item[1], "r": "inf", "m": hw, "t": item[0]})
        for gi, g in enumerate(e["grp"]):
            for z in g["zh"]:
                add(z, {"h": hw, "l": "zh", "f": z, "r": "zh", "gi": gi})
            for lang in ROMANCE:
                for w in (e["lx"][k] for k in g["tr"][lang]):
                    add(w["w"], {"h": hw, "l": lang, "f": w["w"], "r": "tr", "gi": gi})
                    key = (lang, w["w"], w.get("p"))
                    if key not in rom_forms_cache:
                        rec = lex.pick(lang, w["w"], w.get("p"))
                        fl = []
                        for f in (rec or {}).get("forms") or []:
                            code = tags_code(f.get("tags"))
                            # only the forms a learner types (plural, feminine, participles,
                            # 1st/3rd person present, preterite) - not whole conjugation tables
                            if code and f.get("form") and f["form"] != w["w"] and " " not in f["form"]:
                                if (f["form"], code) not in fl:
                                    fl.append((f["form"], code))
                        rom_forms_cache[key] = fl[:16]
                    for form, code in rom_forms_cache[key]:
                        add(form, {"h": hw, "l": lang, "f": form, "r": "trinf", "m": w["w"], "t": code})
    for form, lemma, code in form_of:
        if lemma in entries:
            add(form, {"h": lemma, "l": "en", "f": form, "r": "inf", "m": lemma, "t": code})

    # ---- write
    for sub in ("entries", "index"):
        p = os.path.join(out_dir, sub)
        if os.path.isdir(p):
            shutil.rmtree(p)
        os.makedirs(p, exist_ok=True)

    def dump(path, obj):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=False)

    shards = defaultdict(dict)
    for hw, e in entries.items():
        shards[entry_bucket(hw)][hw] = e
    for b, obj in shards.items():
        dump(os.path.join(out_dir, "entries", b + ".json"), obj)
    ishards = defaultdict(dict)
    order = {"hw": 0, "inf": 1, "tr": 2, "zh": 3, "trinf": 4}
    def compact(h):
        # [headword, lang, form, relation, (group index) | (lemma, tag)] - decoded by decodeHit() in app.js
        out = [h["h"], h["l"], h["f"], h["r"]]
        if "gi" in h:
            out.append(h["gi"])
        elif "m" in h:
            out += [h["m"], h.get("t", "")]
        return out

    rank = rank or {}
    for k, hits in index.items():
        # relation first; then headwords that several languages point to ("café" -> coffee,
        # not brown), the main sense row, and finally English word frequency
        same = defaultdict(int)
        for h in hits:
            same[h["h"]] += 1
        hits.sort(key=lambda h: (order.get(h["r"], 9), -same[h["h"]], h.get("gi", 0), rank.get(h["h"], 10 ** 6)))
        ishards[index_bucket(k)][k] = [compact(h) for h in hits]
    for b, obj in ishards.items():
        dump(os.path.join(out_dir, "index", b + ".json"), dict(sorted(obj.items())))

    words = sorted(([hw, (e["zh"] or [""])[0]] for hw, e in entries.items()), key=lambda x: x[0].lower())
    dump(os.path.join(out_dir, "words.json"), words)

    used_langs = set()
    for e in entries.values():
        for et in e["ety"]:
            used_langs.update(n["l"] for n in et["chain"])
            used_langs.update(c["l"] for c in et.get("cog", []))
        for g in e["grp"]:
            for lang in ROMANCE:
                for w in (e["lx"][k] for k in g["tr"][lang]):
                    used_langs.update(n["l"] for n in (w.get("ety") or {}).get("chain", []))
    used_langs.update(("en",) + ROMANCE)
    meta = {
        "version": 1,
        "built": date.today().isoformat(),
        "source": source,
        "entryPrefixLen": ENTRY_PREFIX_LEN,
        "counts": {"entries": len(entries), "indexKeys": len(index),
                   "entryShards": len(shards), "indexShards": len(ishards)},
        "indexShards": sorted(ishards),
        "langs": {c: {"en": lang_name(c)[0], "zh": lang_name(c)[1]} for c in sorted(used_langs)},
        "license": "CC BY-SA 4.0 (Wiktionary contributors, via Wiktextract/Kaikki.org)",
    }
    dump(os.path.join(out_dir, "meta.json"), meta)
    print(f"  wrote {len(shards)} entry shards, {len(ishards)} index shards, "
          f"{len(index)} search keys -> {out_dir}", file=sys.stderr)
    return entries


# --------------------------------------------------------------------------
# Full-dump loading
# --------------------------------------------------------------------------
def load_wordlist(path, top):
    words = []
    if path:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                w = line.strip().split("\t")[0].split(" ")[0]
                if w and not w.startswith("#"):
                    words.append(w)
    else:
        try:
            from wordfreq import top_n_list  # type: ignore
        except ImportError:
            sys.exit("error: pass --wordlist FILE or `pip install wordfreq` for frequency ranking")
        words = top_n_list("en", int(top * 1.6))
    out = []
    for w in words:
        if re.fullmatch(r"[a-z][a-z' -]*", w) and w not in out:
            out.append(w)
    return out[: int(top * 1.6)]


_WORD_VAL = re.compile(r'"word":\s*"((?:[^"\\]|\\.)*)"')


def open_jsonl_prefiltered(path: str, words: set, keyfn=None):
    """Stream records, but only json-decode lines that mention one of `words` as a
    "word" value somewhere (a cheap superset filter that makes multi-GB dumps fast)."""
    opener = gzip.open if path.endswith(".gz") else open
    keyfn = keyfn or (lambda x: x)
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            vals = _WORD_VAL.findall(line)
            if not any(keyfn(json.loads(f'"{v}"') if "\\" in v else v) in words for v in vals):
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def run_full(args):
    import pickle
    cache = args.cache
    if cache and os.path.exists(cache) and not args.refresh:
        print(f"[cache] loading extracted records from {cache} (use --refresh to rescan the dumps)", file=sys.stderr)
        with gzip.open(cache, "rb") as fh:
            c = pickle.load(fh)
        if c.get("top") == args.top:
            build(c["en"], c["rom"], c["anc"], args.out, wanted=c["keep"], source="kaikki", extra_forms=c["forms"],
                  rank={w: i for i, w in enumerate(c.get("ranked") or load_wordlist(args.wordlist, args.top))})
            return
        print("[cache] --top differs from the cached build; rescanning", file=sys.stderr)
    wanted_ranked = load_wordlist(args.wordlist, args.top)
    wanted = set(wanted_ranked)
    print(f"[1/4] scanning English dump for {len(wanted)} candidate headwords", file=sys.stderr)
    en_records, extra_forms = [], []
    for rec in open_jsonl_prefiltered(args.en, wanted):
        if rec.get("lang_code") != "en":
            continue
        w = rec.get("word")
        if is_form_of_record(rec):
            for s in rec.get("senses") or []:
                for fo in s.get("form_of") or []:
                    if fo.get("word") in wanted:
                        extra_forms.append((w, fo["word"], tags_code(s.get("tags")) or "form"))
            continue
        if w in wanted:
            en_records.append(slim_en(rec))
    have_tr = {r["word"] for r in en_records if any(_tr_lang(t) in ROMANCE for t in r["translations"])}
    keep = [w for w in wanted_ranked if w in have_tr][: args.top]
    keep_set = set(keep)
    en_records = [r for r in en_records if r["word"] in keep_set]
    print(f"      kept {len(keep)} headwords", file=sys.stderr)

    need = defaultdict(set)
    for r in en_records:
        for t in r["translations"]:
            lang = _tr_lang(t)
            if lang in ROMANCE and t.get("word"):
                need[lang].add(t["word"])
    print("[2/4] scanning Romance dumps", file=sys.stderr)
    rom_records = []
    for lang in ROMANCE:
        path = getattr(args, lang)
        if not path:
            print(f"      (no --{lang} dump given; {lang} words will lack gender/IPA/etymology)", file=sys.stderr)
            continue
        n = 0
        for rec in open_jsonl_prefiltered(path, need[lang]):
            if rec.get("lang_code") == lang and rec.get("word") in need[lang]:
                rom_records.append(slim_other(rec))
                n += 1
        print(f"      {lang}: {n} records", file=sys.stderr)

    print("[3/4] resolving ancestors", file=sys.stderr)
    anc_records = []
    loaded = set()

    for r in en_records + rom_records:
        register_names_from_templates(r.get("etymology_templates"))

    def needed_keys(records):
        keys = set()
        for r in records:
            ety = parse_etymology(r.get("etymology_templates"), r.get("etymology_text"), r.get("lang_code", ""))
            for n in ety["chain"]:
                for f in (n.get("f"), n.get("lm")):
                    if f:
                        keys.add((n["l"], akey(f)))
            for s in r.get("senses") or []:               # form-of pages: fetch the lemma next
                for fo in s.get("form_of") or []:
                    if fo.get("word"):
                        keys.add((r.get("lang_code"), akey(fo["word"])))
        return keys

    pending = needed_keys(en_records) | needed_keys(rom_records)
    for p in range(args.ancestor_passes):
        if not pending or not args.ancestors:
            break
        found = []
        # Wiktionary page titles drop Latin macrons etc., so compare on akey()
        want_forms = {k[1] for k in pending}
        for path in args.ancestors:
            for rec in open_jsonl_prefiltered(path, want_forms, akey):
                lc = rec.get("lang_code")
                w = rec.get("word")
                if not lc or not w:
                    continue
                aw = akey(w)
                if aw not in want_forms:
                    continue
                k = (lc, aw)
                if k in pending and (k, rec.get("pos")) not in loaded:
                    loaded.add((k, rec.get("pos")))
                    found.append(slim_other(rec))
        anc_records.extend(found)
        print(f"      pass {p + 1}: {len(found)} ancestor records", file=sys.stderr)
        have = {(r["lang_code"], akey(r["word"])) for r in anc_records}
        pending = needed_keys(found) - have

    if cache:
        with gzip.open(cache, "wb") as fh:
            pickle.dump({"top": args.top, "en": en_records, "rom": rom_records, "anc": anc_records,
                         "keep": keep_set, "ranked": keep, "forms": extra_forms}, fh, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"      cached extracted records in {cache}", file=sys.stderr)
    print("[4/4] building dataset", file=sys.stderr)
    build(en_records, rom_records, anc_records, args.out, wanted=keep_set,
          source="kaikki", extra_forms=extra_forms, rank={w: i for i, w in enumerate(keep)})


def run_sample(args):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sample_seed  # noqa: E402
    en, rom, anc = sample_seed.kaikki_records()
    print(f"sample seed: {len({r['word'] for r in en})} English words, {len(rom)} Romance records, "
          f"{len(anc)} ancestor records", file=sys.stderr)
    build(en, rom, anc, args.out, source="sample")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true", help="build the bundled demo dataset from tools/sample_seed.py")
    ap.add_argument("--en", help="Kaikki English JSONL(.gz)")
    for lang in ROMANCE:
        ap.add_argument(f"--{lang}", help=f"Kaikki {lang} JSONL(.gz) from English Wiktionary")
    ap.add_argument("--ancestors", nargs="*", default=[], help="ancestor-language dumps (Latin, Old French, ...)")
    ap.add_argument("--ancestor-passes", type=int, default=3)
    ap.add_argument("--wordlist", help="frequency-ranked English word list, one per line")
    ap.add_argument("--top", type=int, default=10000, help="number of English headwords to keep")
    ap.add_argument("--cache", default=os.path.join("raw", "build_cache.pkl.gz"),
                    help="where to cache the records extracted from the dumps ('' to disable)")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and rescan the dumps")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    if args.sample:
        run_sample(args)
    elif args.en:
        run_full(args)
    else:
        ap.error("use --sample, or give at least --en (plus --it/--pt/--fr/--es and --ancestors)")


if __name__ == "__main__":
    main()
