"""
sample_seed.py — hand-curated demo data for 羅曼多語言字典, written in a compact form and
expanded into Wiktextract/Kaikki-shaped records by kaikki_records().

`python tools/build_dataset.py --sample` feeds these records through exactly the
same pipeline that processes the real Kaikki.org dumps (etymology-template
parsing, ancestor-chain extension, sense alignment, sharding, reverse indexes).

Content is summarised from English Wiktionary (CC BY-SA 4.0); example sentences
are original. Etymology strings use the same templates Wiktionary uses.

Compact syntax
  W(word, uk_ipa, us_ipa, ety_templates, [P(...)], [G(...)], syn=, ant=, der=, etytext=)
  P(pos, "code:form;code:form", S(...), S(...))      one part-of-speech block
  S(gloss, ex="sentence || sentence", tags="informal,US", syn="a;b")
  G(label, zh, it, pt, fr, es, pos="noun")            one translation table
      several words: "an|année";  Portuguese variant: "cachorro@BR"
  R(lang, word, pos, gender, forms, ipa, ety, gloss)  a Romance-language entry
      Portuguese ipa = ("BR", "PT") tuple
  A(lang, lemma, gloss, ety, forms)                   an ancestor (Latin, ...) entry
Form codes: pl past pp ing 3s 1s comp sup f fpl pret3s impf3s presp pastpl,
Latin: acc gen abl nom inf ppr;  "pl.archaic:brethren" adds a label.
"""
from __future__ import annotations

from build_dataset import templates_from_wikitext

FORM_TAGS = {
    "pl": ["plural"], "past": ["past"], "pp": ["participle", "past"],
    "ing": ["participle", "present"], "3s": ["third-person", "singular", "present"],
    "1s": ["first-person", "singular", "present", "indicative"],
    "comp": ["comparative"], "sup": ["superlative"], "f": ["feminine", "singular"],
    "fpl": ["feminine", "plural"], "mpl": ["masculine", "plural"],
    "pret3s": ["third-person", "singular", "preterite"],
    "impf3s": ["third-person", "singular", "imperfect"],
    "presp": ["present", "plural"], "pastpl": ["past", "plural"],
    "acc": ["accusative", "singular"], "gen": ["genitive", "singular"],
    "abl": ["ablative", "singular"], "nom": ["nominative", "plural"],
    "inf": ["infinitive", "present", "active"],
    "ppr": ["participle", "present", "accusative", "singular"],
}


def _forms(spec: str) -> list[dict]:
    out = []
    for part in filter(None, (p.strip() for p in (spec or "").split(";"))):
        code, form = part.split(":", 1)
        label = None
        if "." in code:
            code, label = code.split(".", 1)
        tags = list(FORM_TAGS[code])
        if label:
            tags.append(label)
        out.append({"form": form.strip(), "tags": tags})
    return out


class S:
    def __init__(self, gloss, ex="", tags="", syn=""):
        self.gloss = gloss
        self.ex = [e.strip() for e in ex.split("||") if e.strip()] if ex else []
        self.tags = [t.strip() for t in tags.split(",") if t.strip()]
        self.syn = [s.strip() for s in syn.split(";") if s.strip()]


class P:
    def __init__(self, pos, forms, *senses):
        self.pos, self.forms, self.senses = pos, forms, senses


class G:
    def __init__(self, label, zh, it, pt, fr, es, pos="noun"):
        self.label, self.zh, self.pos = label, zh, pos
        self.tr = {"it": it, "pt": pt, "fr": fr, "es": es}


EN: list[dict] = []
ROM: dict[tuple[str, str], dict] = {}
ANC: list[dict] = []


def W(word, uk, us, ety=None, blocks=(), groups=(), syn="", ant="", der="", etytext=None, etys=None):
    EN.append({"word": word, "uk": uk, "us": us,
               "etys": etys or [(ety, blocks, groups, etytext)],
               "syn": syn, "ant": ant, "der": der})


def R(lang, word, pos, g, forms, ipa, ety, gloss):
    if isinstance(ipa, tuple):
        sounds = [{"ipa": f"/{ipa[0]}/", "tags": ["Brazil"]}, {"ipa": f"/{ipa[1]}/", "tags": ["Portugal"]}]
    else:
        sounds = [{"ipa": ipa}] if ipa else []
    rec = {"word": word, "lang_code": lang, "pos": pos, "forms": _forms(forms), "sounds": sounds,
           "senses": [{"glosses": [gloss]}], "etymology_templates": templates_from_wikitext(ety)}
    if g:
        rec["head_templates"] = [{"name": f"{lang}-{pos}", "args": {"1": g}, "expansion": f"{word} {g}"}]
    ROM[(lang, word)] = rec


def A(lang, lemma, gloss, ety="", forms=""):
    ANC.append({"word": lemma, "lang_code": lang, "pos": "noun", "forms": _forms(forms),
                "senses": [{"glosses": [gloss]}] if gloss else [],
                "etymology_templates": templates_from_wikitext(ety)})


# ==========================================================================
# English headwords
# ==========================================================================
W("night", "/naɪt/", "/naɪt/",
  "{{inh|en|enm|night}} {{inh|en|ang|niht}} {{inh|en|gem-pro|*nahts}} {{inh|en|ine-pro|*nókʷts||night}} "
  "{{cog|de|Nacht}} {{cog|nl|nacht}} {{cog|la|nox}}",
  [P("noun", "pl:nights",
     S("The period of darkness between sunset and sunrise.", "The stars came out as night fell."),
     S("An evening, especially as the time of an event or activity.", "It was opening night at the theatre."))],
  [G("period of darkness between sunset and sunrise", "夜；夜晚；晚上", "notte", "noite", "nuit", "noche")],
  syn="nighttime", ant="day", der="tonight;nightfall;night owl;good night;at night;overnight;nightlife")

W("day", "/deɪ/", "/deɪ/",
  "{{inh|en|enm|day}} {{inh|en|ang|dæġ}} {{inh|en|gem-pro|*dagaz}} {{der|en|ine-pro|*dʰegʷʰ-||to burn}} "
  "{{cog|de|Tag}} {{cog|nl|dag}}",
  [P("noun", "pl:days",
     S("The period of light between sunrise and sunset.", "We walked all day and reached the coast at dusk."),
     S("A period of 24 hours, beginning at midnight.", "There are seven days in a week."),
     S("A particular period or era.", "In my grandfather's day, few people owned a car."))],
  [G("period of light; period of 24 hours", "天；日；白天", "giorno", "dia", "jour", "día")],
  syn="daytime", ant="night", der="today;daily;daylight;day off;one day;day by day;birthday",
  etytext="From Middle English day, from Old English dæġ, from Proto-Germanic *dagaz, probably from "
          "Proto-Indo-European *dʰegʷʰ- (“to burn”). Despite the similar sound, it is not related to Latin diēs.")

W("summer", "/ˈsʌm.ə/", "/ˈsʌm.ɚ/",
  "{{inh|en|enm|sumer}} {{inh|en|ang|sumor}} {{inh|en|gem-pro|*sumaraz}} {{inh|en|ine-pro|*sm̥h₂-||summer}} "
  "{{cog|de|Sommer}} {{cog|nl|zomer}}",
  [P("noun", "pl:summers",
     S("The warmest season of the year, between spring and autumn.", "We go to the beach every summer."),
     S("The peak or best period of something.", "She was in the summer of her career.", tags="figurative"))],
  [G("warmest season of the year", "夏天；夏季", "estate", "verão", "été", "verano")],
  ant="winter", der="summertime;midsummer;Indian summer;summer holiday;summer camp")

W("winter", "/ˈwɪn.tə/", "/ˈwɪn.tɚ/",
  "{{inh|en|enm|winter}} {{inh|en|ang|winter}} {{inh|en|gem-pro|*wintruz}} {{unc|en}} "
  "{{der|en|ine-pro|*wed-||water, wet}} {{cog|de|Winter}}",
  [P("noun", "pl:winters",
     S("The coldest season of the year, between autumn and spring.", "The lake freezes in winter."))],
  [G("coldest season of the year", "冬天；冬季", "inverno", "inverno", "hiver", "invierno")],
  ant="summer", der="wintertime;midwinter;winter sports;winter solstice")

W("spring", "/spɹɪŋ/", "/spɹɪŋ/",
  "{{inh|en|enm|springen}} {{inh|en|ang|springan}} {{inh|en|gem-pro|*springaną}} "
  "{{inh|en|ine-pro|*sprengʰ-||to move quickly}} {{cog|de|springen}}",
  [P("noun", "pl:springs",
     S("The season of the year between winter and summer, when plants begin to grow.",
       "The cherry trees bloom in spring."),
     S("A place where water comes up naturally from the ground.",
       "The village gets its water from a mountain spring."),
     S("A coiled piece of metal that returns to its shape after being pressed or stretched.",
       "The old mattress has a broken spring.")),
   P("verb", "3s:springs;past:sprang;pp:sprung;ing:springing",
     S("To jump or move suddenly upward or forward.", "The cat sprang onto the table.", syn="jump;leap;bound"))],
  [G("season between winter and summer", "春天；春季", "primavera", "primavera", "printemps", "primavera"),
   G("place where water comes up from the ground", "泉；泉水", "sorgente", "fonte", "source", "manantial"),
   G("coiled piece of metal", "彈簧", "molla", "mola", "ressort", "muelle"),
   G("jump or move suddenly", "跳；躍", "saltare", "saltar", "sauter", "saltar", pos="verb")],
  der="springtime;hot spring;spring roll;spring cleaning;spring up")

W("water", "/ˈwɔː.tə/", "/ˈwɔ.tɚ/",
  "{{inh|en|enm|water}} {{inh|en|ang|wæter}} {{inh|en|gem-pro|*watōr}} {{inh|en|ine-pro|*wódr̥||water}} "
  "{{cog|de|Wasser}} {{cog|ru|вода|tr=voda}}",
  [P("noun", "pl:waters",
     S("A clear liquid without colour or taste that falls as rain and is necessary for all life.",
       "Could I have a glass of water, please?")),
   P("verb", "3s:waters;past:watered;pp:watered;ing:watering",
     S("To pour water on plants or soil.", "Remember to water the tomatoes."))],
  [G("clear liquid necessary for life", "水", "acqua", "água", "eau", "agua")],
  der="waterfall;watermelon;fresh water;drinking water;in hot water;underwater")

W("fire", "/ˈfaɪə/", "/ˈfaɪɚ/",
  "{{inh|en|enm|fyr}} {{inh|en|ang|fȳr}} {{inh|en|gem-pro|*fōr}} {{inh|en|ine-pro|*péh₂wr̥||fire}} "
  "{{cog|de|Feuer}} {{cog|grc|πῦρ|tr=pûr}}",
  [P("noun", "pl:fires",
     S("The heat, light and flames produced when something burns.", "We sat around the fire to keep warm.")),
   P("verb", "3s:fires;past:fired;pp:fired;ing:firing",
     S("To shoot a gun or other weapon.", "The soldiers fired into the air."),
     S("To dismiss someone from their job.", "She was fired for being late too often.",
       tags="informal", syn="dismiss;sack"))],
  [G("heat, light and flames", "火", "fuoco", "fogo", "feu", "fuego")],
  ant="hire", der="fireplace;firework;campfire;catch fire;on fire;fire alarm")

W("sun", "/sʌn/", "/sʌn/",
  "{{inh|en|enm|sonne}} {{inh|en|ang|sunne}} {{inh|en|gem-pro|*sunnǭ}} {{inh|en|ine-pro|*sóh₂wl̥||sun}} "
  "{{cog|de|Sonne}} {{cog|la|sōl}}",
  [P("noun", "pl:suns",
     S("The star at the centre of our solar system, which gives the Earth light and heat.",
       "The sun rises in the east."),
     S("Light and heat from the sun.", "Let's sit in the sun for a while."))],
  [G("star at the centre of the solar system; light and heat", "太陽；陽光", "sole", "sol", "soleil", "sol")],
  der="sunlight;sunrise;sunset;sunny;Sunday;sunflower;sunglasses")

W("moon", "/muːn/", "/mun/",
  "{{inh|en|enm|mone}} {{inh|en|ang|mōna}} {{inh|en|gem-pro|*mēnô}} {{inh|en|ine-pro|*mḗh₁n̥s||moon, month}} "
  "{{cog|de|Mond}}",
  [P("noun", "pl:moons",
     S("The natural satellite that orbits the Earth and shines at night by reflecting sunlight.",
       "The moon was full and bright."))],
  [G("natural satellite of the Earth", "月亮；月球", "luna", "lua", "lune", "luna")],
  der="moonlight;full moon;new moon;honeymoon;once in a blue moon")

W("star", "/stɑː/", "/stɑɹ/",
  "{{inh|en|enm|sterre}} {{inh|en|ang|steorra}} {{inh|en|gem-pro|*sternǭ}} {{inh|en|ine-pro|*h₂stḗr||star}} "
  "{{cog|de|Stern}} {{cog|grc|ἀστήρ|tr=astḗr}}",
  [P("noun", "pl:stars",
     S("A huge ball of burning gas in space, seen as a point of light in the night sky.",
       "On a clear night you can see thousands of stars."),
     S("A very famous performer, such as an actor or singer.", "She became a film star at the age of twenty."))],
  [G("ball of burning gas in space; point of light in the sky", "星星；恆星", "stella", "estrela", "étoile", "estrella")],
  der="starlight;superstar;starfish;shooting star;five-star")

W("sea", "/siː/", "/si/",
  "{{inh|en|enm|see}} {{inh|en|ang|sǣ}} {{inh|en|gem-pro|*saiwiz}} {{cog|de|See}} {{cog|nl|zee}}",
  [P("noun", "pl:seas",
     S("The large body of salt water that covers most of the Earth's surface.", "We swam in the sea every morning."))],
  [G("large body of salt water", "海；海洋", "mare", "mar", "mer", "mar")],
  syn="ocean", ant="land", der="seaside;seafood;seashell;at sea;sea level",
  etytext="From Middle English see, from Old English sǣ, from Proto-Germanic *saiwiz, of uncertain origin "
          "beyond Germanic. Not related to Latin mare.")

W("tree", "/tɹiː/", "/tɹi/",
  "{{inh|en|enm|tre}} {{inh|en|ang|trēow}} {{inh|en|gem-pro|*trewą}} {{inh|en|ine-pro|*dóru||tree, wood}} "
  "{{cog|grc|δόρυ|tr=dóru}}",
  [P("noun", "pl:trees",
     S("A tall plant with a hard trunk, branches and leaves.", "An old oak tree stood in the garden."),
     S("A data structure made of a root and branching nodes.", "The program stores the words in a tree.",
       tags="computing"))],
  [G("tall plant with a trunk, branches and leaves", "樹；樹木", "albero", "árvore", "arbre", "árbol")],
  der="family tree;treetop;Christmas tree;tree house")

W("mother", "/ˈmʌð.ə/", "/ˈmʌð.ɚ/",
  "{{inh|en|enm|moder}} {{inh|en|ang|mōdor}} {{inh|en|gem-pro|*mōdēr}} {{inh|en|ine-pro|*méh₂tēr||mother}} "
  "{{cog|de|Mutter}} {{cog|la|māter}}",
  [P("noun", "pl:mothers",
     S("A female parent.", "My mother taught me how to cook.", syn="mum (British);mom (US)"))],
  [G("female parent", "母親；媽媽", "madre", "mãe", "mère", "madre")],
  ant="father", der="motherland;mother tongue;grandmother;motherhood;stepmother")

W("father", "/ˈfɑː.ðə/", "/ˈfɑ.ðɚ/",
  "{{inh|en|enm|fader}} {{inh|en|ang|fæder}} {{inh|en|gem-pro|*fadēr}} {{inh|en|ine-pro|*ph₂tḗr||father}} "
  "{{cog|de|Vater}} {{cog|la|pater}}",
  [P("noun", "pl:fathers", S("A male parent.", "Her father works as a doctor.", syn="dad"))],
  [G("male parent", "父親；爸爸", "padre", "pai", "père", "padre")],
  ant="mother", der="grandfather;fatherland;fatherhood;Father's Day")

W("brother", "/ˈbɹʌð.ə/", "/ˈbɹʌð.ɚ/",
  "{{inh|en|enm|brother}} {{inh|en|ang|brōþor}} {{inh|en|gem-pro|*brōþēr}} "
  "{{inh|en|ine-pro|*bʰréh₂tēr||brother}} {{cog|de|Bruder}} {{cog|la|frāter}}",
  [P("noun", "pl:brothers;pl.archaic:brethren",
     S("A male sibling; a boy or man who has the same parents as another person.", "I have two older brothers."))],
  [G("male sibling", "兄弟；哥哥；弟弟", "fratello", "irmão", "frère", "hermano")],
  ant="sister", der="brotherhood;brother-in-law;half-brother;big brother")

W("name", "/neɪm/", "/neɪm/",
  "{{inh|en|enm|name}} {{inh|en|ang|nama}} {{inh|en|gem-pro|*namô}} {{inh|en|ine-pro|*h₁nómn̥||name}} "
  "{{cog|de|Name}} {{cog|la|nōmen}}",
  [P("noun", "pl:names",
     S("The word or words by which a person, place or thing is known.", "What's your name?")),
   P("verb", "3s:names;past:named;pp:named;ing:naming",
     S("To give a name to someone or something.", "They named their daughter Sofia."))],
  [G("word by which a person, place or thing is known", "名字；名稱", "nome", "nome", "nom", "nombre")],
  der="surname;first name;nickname;username;namesake;in the name of")

W("heart", "/hɑːt/", "/hɑɹt/",
  "{{inh|en|enm|herte}} {{inh|en|ang|heorte}} {{inh|en|gem-pro|*hertô}} {{inh|en|ine-pro|*ḱḗr||heart}} "
  "{{cog|de|Herz}} {{cog|la|cor}} {{cog|grc|καρδία|tr=kardía}}",
  [P("noun", "pl:hearts",
     S("The organ in the chest that pumps blood around the body.", "Her heart was beating fast."),
     S("The centre of a person's feelings and emotions.", "He has a kind heart."),
     S("The central or most important part of something.", "The hotel is in the heart of the city."))],
  [G("organ that pumps blood; centre of feelings", "心臟；心", "cuore", "coração", "cœur", "corazón")],
  der="heartbeat;heartbreak;by heart;heart attack;sweetheart;wholehearted")

W("new", "/njuː/", "/nu/",
  "{{inh|en|enm|newe}} {{inh|en|ang|nīwe}} {{inh|en|gem-pro|*niwjaz}} {{inh|en|ine-pro|*néwyos||new}} "
  "{{cog|de|neu}} {{cog|la|novus}}",
  [P("adj", "comp:newer;sup:newest",
     S("Recently made, built or created; not existing before.", "They moved into a new house last year."),
     S("Not yet used or owned by anyone else.", "Is your bike new or second-hand?"),
     S("Not familiar; seen or experienced for the first time.", "Everything was new to me in the city."))],
  [G("recently made; not existing before; not used", "新的", "nuovo", "novo", "nouveau|neuf", "nuevo", pos="adj")],
  syn="fresh;recent;modern", ant="old", der="news;newborn;newcomer;brand-new;New Year;renew")

W("house", "/haʊs/", "/haʊs/",
  "{{inh|en|enm|hous}} {{inh|en|ang|hūs}} {{inh|en|gem-pro|*hūsą}} {{cog|de|Haus}} {{cog|nl|huis}}",
  [P("noun", "pl:houses",
     S("A building where people live, usually one family.", "They live in a small house near the river."))],
  [G("building where people live", "房子；房屋；住宅", "casa", "casa", "maison", "casa")],
  syn="home;dwelling", der="household;housework;greenhouse;lighthouse;on the house")

W("dog", "/dɒɡ/", "/dɔɡ/",
  "{{inh|en|enm|dogge}} {{inh|en|ang|docga}} {{unc|en}}",
  [P("noun", "pl:dogs",
     S("A domesticated animal related to the wolf, kept as a pet or for work.",
       "We take the dog for a walk every evening."))],
  [G("domesticated animal kept as a pet", "狗；犬", "cane", "cão|cachorro@BR", "chien", "perro")],
  syn="hound", der="hot dog;guide dog;dog-eared;underdog;watchdog",
  etytext="From Middle English dogge, from Old English docga, a word of uncertain origin that replaced "
          "the older hound.")

W("cat", "/kæt/", "/kæt/",
  "{{inh|en|enm|cat}} {{inh|en|ang|catt}} {{inh|en|gem-pro|*kattuz}} {{der|en|la-lat|cattus}}",
  [P("noun", "pl:cats",
     S("A small furry animal with whiskers, often kept as a pet.", "The cat was asleep on the sofa."),
     S("A person, especially a fashionable man.", "He's a really cool cat.", tags="slang,dated"))],
  [G("small furry domestic animal", "貓", "gatto", "gato", "chat", "gato")],
  der="catfish;catwalk;wildcat;copycat;let the cat out of the bag")

W("eye", "/aɪ/", "/aɪ/",
  "{{inh|en|enm|eye}} {{inh|en|ang|ēage}} {{inh|en|gem-pro|*augô}} {{inh|en|ine-pro|*h₃ekʷ-||to see}} "
  "{{cog|de|Auge}} {{cog|la|oculus}}",
  [P("noun", "pl:eyes",
     S("One of the two organs of sight in the face.", "She has blue eyes."),
     S("The ability to notice or judge things.", "He has a good eye for design."))],
  [G("organ of sight", "眼睛；眼", "occhio", "olho", "œil", "ojo")],
  der="eyebrow;eyelash;eyesight;keep an eye on;eye contact;see eye to eye")

W("hand", "/hænd/", "/hænd/",
  "{{inh|en|enm|hand}} {{inh|en|ang|hand}} {{inh|en|gem-pro|*handuz}} {{cog|de|Hand}}",
  [P("noun", "pl:hands",
     S("The part of the body at the end of the arm, with four fingers and a thumb.",
       "Raise your hand if you know the answer.")),
   P("verb", "3s:hands;past:handed;pp:handed;ing:handing",
     S("To give something to someone with your hand.", "Could you hand me that book?"))],
  [G("part of the body at the end of the arm", "手", "mano", "mão", "main", "mano")],
  der="handbag;handwriting;handshake;on the other hand;give a hand;second-hand")

W("foot", "/fʊt/", "/fʊt/",
  "{{inh|en|enm|fot}} {{inh|en|ang|fōt}} {{inh|en|gem-pro|*fōts}} {{inh|en|ine-pro|*pṓds||foot}} "
  "{{cog|de|Fuß}} {{cog|la|pēs}}",
  [P("noun", "pl:feet",
     S("The part of the leg below the ankle, on which a person stands.", "My feet hurt after the long walk."),
     S("A unit of length equal to 12 inches (about 30.5 cm).", "The wall is six feet high."))],
  [G("part of the leg below the ankle", "腳；足", "piede", "pé", "pied", "pie")],
  der="football;footprint;barefoot;on foot;footstep")

W("tooth", "/tuːθ/", "/tuθ/",
  "{{inh|en|enm|toth}} {{inh|en|ang|tōþ}} {{inh|en|gem-pro|*tanþs}} {{inh|en|ine-pro|*h₃dónts||tooth}} "
  "{{cog|de|Zahn}} {{cog|la|dēns}}",
  [P("noun", "pl:teeth",
     S("One of the hard white objects in the mouth, used for biting and chewing.",
       "Brush your teeth twice a day."))],
  [G("hard object in the mouth used for biting", "牙齒；牙", "dente", "dente", "dent", "diente")],
  der="toothbrush;toothpaste;toothache;sweet tooth;wisdom tooth")

W("milk", "/mɪlk/", "/mɪlk/",
  "{{inh|en|enm|milk}} {{inh|en|ang|meolc}} {{inh|en|gem-pro|*meluks}} {{inh|en|ine-pro|*h₂melǵ-||to milk}} "
  "{{cog|de|Milch}}",
  [P("noun", "",
     S("The white liquid produced by female mammals to feed their young, especially cow's milk as a drink.",
       "Would you like milk in your tea?")),
   P("verb", "3s:milks;past:milked;pp:milked;ing:milking",
     S("To take milk from a cow, goat or other animal.", "The farmer milks the cows at dawn."))],
  [G("white liquid produced by mammals", "牛奶；奶", "latte", "leite", "lait", "leche")],
  der="milkshake;milky;Milky Way;skimmed milk")

W("bread", "/bɹɛd/", "/bɹɛd/",
  "{{inh|en|enm|breed}} {{inh|en|ang|brēad}} {{inh|en|gem-pro|*braudą}} {{cog|de|Brot}}",
  [P("noun", "",
     S("A food made from flour, water and usually yeast, mixed together and baked.", "She bought a loaf of bread."))],
  [G("food made from flour and baked", "麵包", "pane", "pão", "pain", "pan")],
  der="breadcrumb;bread and butter;breadwinner;flatbread")

W("wine", "/waɪn/", "/waɪn/",
  "{{inh|en|enm|wyn}} {{inh|en|ang|wīn}} {{inh|en|gem-pro|*wīną}} {{der|en|la|vīnum}} {{cog|de|Wein}}",
  [P("noun", "pl:wines",
     S("An alcoholic drink made from fermented grape juice.", "They ordered a bottle of red wine."))],
  [G("alcoholic drink made from grapes", "葡萄酒；酒", "vino", "vinho", "vin", "vino")],
  der="wine glass;winery;red wine;white wine")

W("salt", "/sɔːlt/", "/sɔlt/",
  "{{inh|en|enm|salt}} {{inh|en|ang|sealt}} {{inh|en|gem-pro|*saltą}} {{inh|en|ine-pro|*séh₂ls||salt}} "
  "{{cog|de|Salz}} {{cog|la|sāl}}",
  [P("noun", "pl:salts",
     S("A white substance, sodium chloride, used to flavour and preserve food.", "Could you pass the salt?")),
   P("verb", "3s:salts;past:salted;pp:salted;ing:salting",
     S("To add salt to food.", "Salt the water before adding the pasta."))],
  [G("substance used to flavour food", "鹽", "sale", "sal", "sel", "sal")],
  der="salty;salt water;salt and pepper;take with a grain of salt;sea salt")

W("coffee", "/ˈkɒf.i/", "/ˈkɔ.fi/",
  "{{bor|en|nl|koffie}} {{bor|en|ota|قهوه|tr=kahve}} {{der|en|ar|قهوة|tr=qahwa}}",
  [P("noun", "pl:coffees",
     S("A hot drink made from the roasted and ground seeds of a tropical plant.",
       "I drink a cup of coffee every morning."))],
  [G("drink made from roasted seeds", "咖啡", "caffè", "café", "café", "café")],
  der="coffee shop;coffee bean;coffee break;black coffee;coffee table")

W("book", "/bʊk/", "/bʊk/",
  "{{inh|en|enm|book}} {{inh|en|ang|bōc}} {{inh|en|gem-pro|*bōks}} {{cog|de|Buch}}",
  [P("noun", "pl:books",
     S("A set of printed pages fastened together inside a cover, for reading.",
       "I'm reading a book about Roman history.")),
   P("verb", "3s:books;past:booked;pp:booked;ing:booking",
     S("To arrange to have a seat, room or ticket at a later time.", "We booked a table for eight o'clock.",
       syn="reserve"))],
  [G("printed pages fastened inside a cover", "書；書本", "libro", "livro", "livre", "libro"),
   G("arrange to have a seat, room or ticket", "預訂；預約", "prenotare", "reservar", "réserver", "reservar",
     pos="verb")],
  der="bookshop;bookcase;notebook;textbook;booklet;by the book")

W("city", "/ˈsɪt.i/", "/ˈsɪɾ.i/",
  "{{inh|en|enm|citee}} {{bor|en|fro|cité}} {{der|en|la|cīvitātem}}",
  [P("noun", "pl:cities",
     S("A large and important town.", "Tokyo is one of the largest cities in the world."))],
  [G("large and important town", "城市；都市", "città", "cidade", "ville", "ciudad")],
  syn="town", ant="countryside", der="city centre;city hall;inner city;capital city")

W("friend", "/fɹɛnd/", "/fɹɛnd/",
  "{{inh|en|enm|frend}} {{inh|en|ang|frēond}} {{inh|en|gem-pro|*frijōndz}} {{inh|en|ine-pro|*priH-||to love}} "
  "{{cog|de|Freund}}",
  [P("noun", "pl:friends",
     S("A person you know well and like, who is not a member of your family.", "She's my best friend from school."))],
  [G("person you know well and like", "朋友", "amico", "amigo", "ami", "amigo")],
  syn="mate (British, informal);pal", ant="enemy", der="friendly;friendship;boyfriend;girlfriend;make friends")

W("love", "/lʌv/", "/lʌv/",
  "{{inh|en|enm|love}} {{inh|en|ang|lufu}} {{inh|en|gem-pro|*lubō}} {{inh|en|ine-pro|*lewbʰ-||to love}} "
  "{{cog|de|Liebe}}",
  [P("noun", "pl:loves",
     S("A strong feeling of affection and care for someone.", "Their love for each other grew over the years.")),
   P("verb", "3s:loves;past:loved;pp:loved;ing:loving",
     S("To have a strong feeling of affection for someone.", "I love my family."),
     S("To like something very much.", "She loves swimming in the sea."))],
  [G("strong feeling of affection", "愛；愛情", "amore", "amor", "amour", "amor"),
   G("have a strong feeling of affection", "愛；喜愛", "amare", "amar", "aimer", "amar|querer", pos="verb")],
  ant="hate", der="lovely;lover;in love;fall in love;love letter")

W("king", "/kɪŋ/", "/kɪŋ/",
  "{{inh|en|enm|king}} {{inh|en|ang|cyning}} {{inh|en|gem-pro|*kuningaz}} {{cog|de|König}}",
  [P("noun", "pl:kings",
     S("The male ruler of a country, who usually inherits the position.", "The king lived in a large palace."),
     S("The most important piece in the game of chess.", "The game ends when the king is checkmated.",
       tags="chess"))],
  [G("male ruler of a country", "國王；君主", "re", "rei", "roi", "rey")],
  ant="queen", der="kingdom;king-size;kingfisher")

W("time", "/taɪm/", "/taɪm/",
  "{{inh|en|enm|time}} {{inh|en|ang|tīma}} {{inh|en|gem-pro|*tīmô}} {{inh|en|ine-pro|*deh₂-||to divide}} "
  "{{cog|sv|timme}}",
  [P("noun", "pl:times",
     S("The continuing progress of existence, measured in seconds, minutes, hours, days and years.",
       "Time passes quickly when you're having fun."),
     S("An occasion when something happens.", "This is the first time I've been to Paris."),
     S("The hour shown on a clock.", "What time is it?")),
   P("verb", "3s:times;past:timed;pp:timed;ing:timing",
     S("To measure how long something takes.", "She timed the race with a stopwatch."))],
  [G("progress of existence measured in hours", "時間", "tempo", "tempo", "temps", "tiempo"),
   G("occasion when something happens", "次；回", "volta", "vez", "fois", "vez")],
  der="sometimes;timetable;on time;in time;full-time;spare time;once upon a time")

W("year", "/jɪə/", "/jɪɹ/",
  "{{inh|en|enm|yeer}} {{inh|en|ang|ġēar}} {{inh|en|gem-pro|*jērą}} {{inh|en|ine-pro|*yóh₁r̥||year, season}} "
  "{{cog|de|Jahr}}",
  [P("noun", "pl:years",
     S("A period of twelve months, especially from 1 January to 31 December.", "She was born in the year 2000."))],
  [G("period of twelve months", "年；年度", "anno", "ano", "an|année", "año")],
  der="yearly;New Year;leap year;school year;years old")

W("month", "/mʌnθ/", "/mʌnθ/",
  "{{inh|en|enm|moneth}} {{inh|en|ang|mōnaþ}} {{inh|en|gem-pro|*mēnōþs}} {{inh|en|ine-pro|*mḗh₁n̥s||moon, month}} "
  "{{cog|de|Monat}} {{cog|la|mēnsis}}",
  [P("noun", "pl:months",
     S("One of the twelve periods into which a year is divided.", "We're going on holiday next month."))],
  [G("one of the twelve periods of a year", "月；月份", "mese", "mês", "mois", "mes")],
  der="monthly;last month;next month;month-long")

W("hour", "/ˈaʊ.ə/", "/ˈaʊ.ɚ/",
  "{{inh|en|enm|houre}} {{bor|en|xno|hore}} {{der|en|la|hōra}}",
  [P("noun", "pl:hours",
     S("A period of sixty minutes.", "The flight takes about two hours."),
     S("A particular time of day.", "Most shops are closed at this hour."))],
  [G("period of sixty minutes", "小時；鐘頭", "ora", "hora", "heure", "hora")],
  der="hourly;rush hour;office hours;happy hour;half an hour")

W("rain", "/ɹeɪn/", "/ɹeɪn/",
  "{{inh|en|enm|reyn}} {{inh|en|ang|reġn}} {{inh|en|gem-pro|*regną}} {{cog|de|Regen}}",
  [P("noun", "pl:rains",
     S("Water that falls from clouds in small drops.", "We got caught in the rain.")),
   P("verb", "3s:rains;past:rained;pp:rained;ing:raining",
     S("For rain to fall from the sky.", "It rained all weekend.", tags="impersonal"))],
  [G("water falling from clouds", "雨", "pioggia", "chuva", "pluie", "lluvia"),
   G("fall as rain", "下雨", "piovere", "chover", "pleuvoir", "llover", pos="verb")],
  der="rainbow;raincoat;rainfall;rainforest;rainy;rain or shine")

W("snow", "/snəʊ/", "/snoʊ/",
  "{{inh|en|enm|snowe}} {{inh|en|ang|snāw}} {{inh|en|gem-pro|*snaiwaz}} {{inh|en|ine-pro|*snóygʷʰos||snow}} "
  "{{cog|de|Schnee}} {{cog|la|nix}}",
  [P("noun", "",
     S("Soft white flakes of frozen water that fall from the sky in cold weather.",
       "The children built a snowman in the snow.")),
   P("verb", "3s:snows;past:snowed;pp:snowed;ing:snowing",
     S("For snow to fall from the sky.", "It snowed heavily last night.", tags="impersonal"))],
  [G("white flakes of frozen water", "雪", "neve", "neve", "neige", "nieve")],
  der="snowman;snowflake;snowball;snowy;snowboard")

W("fish", "/fɪʃ/", "/fɪʃ/",
  "{{inh|en|enm|fish}} {{inh|en|ang|fisċ}} {{inh|en|gem-pro|*fiskaz}} {{inh|en|ine-pro|*peysk-||fish}} "
  "{{cog|de|Fisch}} {{cog|la|piscis}}",
  [P("noun", "pl:fish;pl:fishes",
     S("An animal that lives in water, breathes through gills and has fins.",
       "There are many kinds of fish in the lake."),
     S("The flesh of fish eaten as food.", "We had fish and chips for dinner.")),
   P("verb", "3s:fishes;past:fished;pp:fished;ing:fishing",
     S("To try to catch fish.", "They went fishing on the river."))],
  [G("animal that lives in water", "魚", "pesce", "peixe", "poisson", "pez"),
   G("flesh of fish eaten as food", "魚肉", "pesce", "peixe", "poisson", "pescado")],
  der="fisherman;fishing;goldfish;shellfish;like a fish out of water")

W("bird", "/bɜːd/", "/bɝd/",
  "{{inh|en|enm|brid}} {{inh|en|ang|bridd}} {{unc|en}}",
  [P("noun", "pl:birds",
     S("An animal with feathers, wings and a beak, which lays eggs and can usually fly.",
       "The birds were singing in the trees."))],
  [G("animal with feathers, wings and a beak", "鳥；鳥類", "uccello", "pássaro|ave", "oiseau", "pájaro|ave")],
  der="birdsong;bird's-eye view;early bird;blackbird;birdwatching",
  etytext="From Middle English brid, from Old English bridd (“young bird, chick”), of unknown origin.")

W("horse", "/hɔːs/", "/hɔɹs/",
  "{{inh|en|enm|hors}} {{inh|en|ang|hors}} {{inh|en|gem-pro|*hrussą}} {{cog|de|Ross}}",
  [P("noun", "pl:horses",
     S("A large animal with four legs, a mane and a tail, used for riding and pulling loads.",
       "She learned to ride a horse when she was six."))],
  [G("large four-legged animal used for riding", "馬", "cavallo", "cavalo", "cheval", "caballo")],
  der="horseback;horsepower;racehorse;seahorse;dark horse")

W("good", "/ɡʊd/", "/ɡʊd/",
  "{{inh|en|enm|good}} {{inh|en|ang|gōd}} {{inh|en|gem-pro|*gōdaz}} {{cog|de|gut}}",
  [P("adj", "comp:better;sup:best",
     S("Of high quality or standard.", "This is a really good book."),
     S("Morally right; kind.", "She is a good person who always helps others."),
     S("Skilled at something.", "He's good at maths."))],
  [G("of high quality; morally right", "好的；良好的", "buono", "bom", "bon", "bueno", pos="adj")],
  syn="fine;excellent;kind", ant="bad", der="goodness;goodbye;good morning;for good;goods")

W("big", "/bɪɡ/", "/bɪɡ/",
  "{{inh|en|enm|big}} {{unc|en}}",
  [P("adj", "comp:bigger;sup:biggest",
     S("Large in size, amount or degree.", "They live in a big house."),
     S("Popular or successful.", "The band is big in Japan.", tags="informal"))],
  [G("large in size", "大的", "grande", "grande", "grand", "grande", pos="adj")],
  syn="large;huge", ant="small;little", der="big deal;big city;think big",
  etytext="From Middle English big (“strong, powerful”), of uncertain origin, perhaps from a Scandinavian source.")

W("eat", "/iːt/", "/it/",
  "{{inh|en|enm|eten}} {{inh|en|ang|etan}} {{inh|en|gem-pro|*etaną}} {{inh|en|ine-pro|*h₁ed-||to eat}} "
  "{{cog|de|essen}} {{cog|la|edō}}",
  [P("verb", "3s:eats;past:ate;pp:eaten;ing:eating",
     S("To put food in your mouth, chew it and swallow it.", "We usually eat dinner at seven."))],
  [G("put food in the mouth and swallow", "吃", "mangiare", "comer", "manger", "comer", pos="verb")],
  der="eater;eatable;eat out;eat up")

W("drink", "/dɹɪŋk/", "/dɹɪŋk/",
  "{{inh|en|enm|drinken}} {{inh|en|ang|drincan}} {{inh|en|gem-pro|*drinkaną}} {{cog|de|trinken}}",
  [P("verb", "3s:drinks;past:drank;pp:drunk;ing:drinking",
     S("To take liquid into the mouth and swallow it.", "You should drink more water.")),
   P("noun", "pl:drinks",
     S("A liquid for drinking, or an amount of it.", "Can I get you a drink?"))],
  [G("take liquid into the mouth and swallow", "喝；飲", "bere", "beber", "boire", "beber", pos="verb")],
  der="drinkable;drinking water;soft drink;drink up")

W("see", "/siː/", "/si/",
  "{{inh|en|enm|seen}} {{inh|en|ang|sēon}} {{inh|en|gem-pro|*sehwaną}} {{inh|en|ine-pro|*sekʷ-||to follow, see}} "
  "{{cog|de|sehen}}",
  [P("verb", "3s:sees;past:saw;pp:seen;ing:seeing",
     S("To notice or become aware of something using your eyes.", "I can't see anything without my glasses."),
     S("To understand.", "I see what you mean."),
     S("To meet or visit someone.", "I'm seeing the doctor tomorrow."))],
  [G("perceive with the eyes", "看見；看到", "vedere", "ver", "voir", "ver", pos="verb")],
  syn="notice;look;watch", der="see you;let me see;see off;sightseeing;foresee")

W("three", "/θɹiː/", "/θɹi/",
  "{{inh|en|enm|thre}} {{inh|en|ang|þrīe}} {{inh|en|gem-pro|*þrīz}} {{inh|en|ine-pro|*tréyes||three}} "
  "{{cog|de|drei}} {{cog|la|trēs}}",
  [P("num", "", S("The number 3; one more than two.", "She has three children."))],
  [G("the number 3", "三", "tre", "três", "trois", "tres", pos="num")],
  der="third;thirteen;thirty;threefold;three-dimensional")

W("two", "/tuː/", "/tu/",
  "{{inh|en|enm|two}} {{inh|en|ang|twā}} {{inh|en|gem-pro|*twai}} {{inh|en|ine-pro|*dwóh₁||two}} "
  "{{cog|de|zwei}} {{cog|la|duo}}",
  [P("num", "", S("The number 2; one more than one.", "I have two cats."))],
  [G("the number 2", "二；兩", "due", "dois", "deux", "dos", pos="num")],
  der="twice;twelve;twenty;twin;two-way;in two")

W("go", "/ɡəʊ/", "/ɡoʊ/",
  "{{inh|en|enm|gon}} {{inh|en|ang|gān}} {{inh|en|gem-pro|*gāną}} {{inh|en|ine-pro|*ǵʰeh₁-||to leave}} "
  "{{cog|de|gehen}}",
  [P("verb", "3s:goes;past:went;pp:gone;ing:going",
     S("To move or travel from one place to another.", "We went to Italy last summer."),
     S("To leave; to depart.", "It's late — I have to go."),
     S("To say (used when reporting speech).", "And then he goes, “I don't believe you!”", tags="informal"),
     S("To become.", "The milk has gone sour."))],
  [G("move or travel from one place to another", "去；走", "andare", "ir", "aller", "ir", pos="verb")],
  syn="travel;move;leave", ant="come;stay", der="go on;go out;go back;go ahead;on the go;let go",
  etytext="From Middle English gon, from Old English gān, from Proto-Germanic *gāną, from Proto-Indo-European "
          "*ǵʰeh₁- (“to leave”). The past tense went was originally the past tense of wend.")

W("be", "/biː/", "/bi/",
  "{{inh|en|enm|been}} {{inh|en|ang|bēon}} {{inh|en|gem-pro|*beuną}} {{inh|en|ine-pro|*bʰuH-||to become, grow}}",
  [P("verb", "1s:am;3s:is;presp:are;past:was;pastpl:were;pp:been;ing:being",
     S("To exist; to have a particular quality or state.", "The sky is blue."),
     S("To be located in a place.", "The keys are on the table."),
     S("Used with a past participle to form the passive.", "The book was written in 1920."))],
  [G("exist; have a quality or state", "是；存在", "essere", "ser|estar", "être", "ser|estar", pos="verb")],
  der="being;well-being;has-been;to-be",
  etytext="From Middle English been, from Old English bēon, from Proto-Germanic *beuną, from Proto-Indo-European "
          "*bʰuH- (“to become, grow”). The verb is suppletive: am and is go back to Proto-Indo-European *h₁es- "
          "(the same root as Latin esse), and was/were to Proto-Germanic *wesaną.")

W("bank", "/bæŋk/", "/bæŋk/", etys=[
    ("{{inh|en|enm|banke}} {{bor|en|frm|banque}} {{bor|en|it|banca}} {{der|en|lng|*banka}} "
     "{{der|en|gem-pro|*bankiz||bench}}",
     [P("noun", "pl:banks",
        S("An organization where people and businesses can keep, save and borrow money.",
          "I need to go to the bank to pay in this cheque."),
        S("A place where something is stored for later use.", "The hospital has a blood bank.")),
      P("verb", "3s:banks;past:banked;pp:banked;ing:banking",
        S("To deposit money in a bank, or to have an account with a bank.",
          "She banks with a local credit union."))],
     [G("financial institution; organization that keeps money", "銀行", "banca", "banco", "banque", "banco")],
     "From Middle English banke, from Middle French banque, from Italian banca (“bench, money-changer's "
     "table”), from Lombardic *banka, from Proto-Germanic *bankiz (“bench”)."),
    ("{{inh|en|enm|banke}} {{der|en|non|*banki}} {{inh|en|gem-pro|*bankô||hill, slope}} {{cog|sv|backe||hill}}",
     [P("noun", "pl:banks",
        S("The sloping land along the edge of a river or lake.", "We had a picnic on the bank of the river."))],
     [G("edge of a river or lake", "河岸；岸", "riva", "margem", "rive", "orilla")],
     "From Middle English banke, from Old Norse *banki, from Proto-Germanic *bankô (“hill, slope”)."),
], der="bank account;banker;banking;bank holiday;piggy bank;riverbank;sandbank")

W("school", "/skuːl/", "/skul/",
  "{{inh|en|enm|scole}} {{inh|en|ang|scōl}} {{der|en|la|schola}}",
  [P("noun", "pl:schools",
     S("A place where children go to be educated.", "My little brother starts school next week."),
     S("A college or university.", "Where did you go to school?", tags="US,informal"))],
  [G("place where children are educated", "學校", "scuola", "escola", "école", "escuela")],
  der="schoolboy;schoolgirl;high school;school year;schoolteacher;old school")

W("music", "/ˈmjuː.zɪk/", "/ˈmju.zɪk/",
  "{{inh|en|enm|musike}} {{bor|en|fro|musique}} {{der|en|la|mūsica}}",
  [P("noun", "",
     S("Sounds arranged in a pleasant or interesting way, made by instruments or voices.",
       "She listens to music while she studies."))],
  [G("sounds made by instruments or voices", "音樂", "musica", "música", "musique", "música")],
  der="musical;musician;music box;folk music;face the music")

# ==========================================================================
# Italian
# ==========================================================================
for args in [
    ("notte", "noun", "f", "pl:notti", "/ˈnɔt.te/", "{{inh|it|la|noctem}}", "night"),
    ("giorno", "noun", "m", "pl:giorni", "/ˈd͡ʒor.no/", "{{inh|it|la|diurnum}}", "day"),
    ("estate", "noun", "f", "pl:estati", "/eˈsta.te/", "{{inh|it|la|aestātem}}", "summer"),
    ("inverno", "noun", "m", "pl:inverni", "/inˈvɛr.no/", "{{inh|it|la|hībernum}}", "winter"),
    ("primavera", "noun", "f", "pl:primavere", "/pri.maˈvɛ.ra/", "{{inh|it|la-vul|*prīma vēra}}", "spring (season)"),
    ("sorgente", "noun", "f", "pl:sorgenti", "/sorˈd͡ʒɛn.te/", "{{inh|it|la|surgentem}}", "spring, source"),
    ("molla", "noun", "f", "pl:molle", "/ˈmɔl.la/", "{{der|it|it|mollare||to let go}}", "spring (device)"),
    ("saltare", "verb", None, "pp:saltato;1s:salto;3s:salta", "/salˈta.re/", "{{inh|it|la|saltāre}}", "to jump"),
    ("acqua", "noun", "f", "pl:acque", "/ˈak.kwa/", "{{inh|it|la|aqua}}", "water"),
    ("fuoco", "noun", "m", "pl:fuochi", "/ˈfwɔ.ko/", "{{inh|it|la|focum}}", "fire"),
    ("sole", "noun", "m", "pl:soli", "/ˈso.le/", "{{inh|it|la|sōlem}}", "sun"),
    ("luna", "noun", "f", "pl:lune", "/ˈlu.na/", "{{inh|it|la|lūna}}", "moon"),
    ("stella", "noun", "f", "pl:stelle", "/ˈstel.la/", "{{inh|it|la|stēlla}}", "star"),
    ("mare", "noun", "m", "pl:mari", "/ˈma.re/", "{{inh|it|la|mare}}", "sea"),
    ("albero", "noun", "m", "pl:alberi", "/ˈal.be.ro/", "{{inh|it|la|arborem}}", "tree"),
    ("madre", "noun", "f", "pl:madri", "/ˈma.dre/", "{{inh|it|la|mātrem}}", "mother"),
    ("padre", "noun", "m", "pl:padri", "/ˈpa.dre/", "{{inh|it|la|patrem}}", "father"),
    ("fratello", "noun", "m", "pl:fratelli", "/fraˈtɛl.lo/", "{{inh|it|la-vul|*frātellus}}", "brother"),
    ("nome", "noun", "m", "pl:nomi", "/ˈno.me/", "{{inh|it|la|nōmen}}", "name"),
    ("cuore", "noun", "m", "pl:cuori", "/ˈkwɔ.re/", "{{inh|it|la|cor}}", "heart"),
    ("nuovo", "adj", None, "f:nuova;pl:nuovi;fpl:nuove", "/ˈnwɔ.vo/", "{{inh|it|la|novum}}", "new"),
    ("casa", "noun", "f", "pl:case", "/ˈka.sa/", "{{inh|it|la|casa}}", "house"),
    ("cane", "noun", "m", "pl:cani", "/ˈka.ne/", "{{inh|it|la|canem}}", "dog"),
    ("gatto", "noun", "m", "pl:gatti;f:gatta", "/ˈɡat.to/", "{{inh|it|la-lat|cattus}}", "cat"),
    ("occhio", "noun", "m", "pl:occhi", "/ˈɔk.kjo/", "{{inh|it|la|oculum}}", "eye"),
    ("mano", "noun", "f", "pl:mani", "/ˈma.no/", "{{inh|it|la|manum}}", "hand"),
    ("piede", "noun", "m", "pl:piedi", "/ˈpjɛ.de/", "{{inh|it|la|pedem}}", "foot"),
    ("dente", "noun", "m", "pl:denti", "/ˈdɛn.te/", "{{inh|it|la|dentem}}", "tooth"),
    ("latte", "noun", "m", "pl:latti", "/ˈlat.te/", "{{inh|it|la-vul|*lacte}}", "milk"),
    ("pane", "noun", "m", "pl:pani", "/ˈpa.ne/", "{{inh|it|la|pānem}}", "bread"),
    ("vino", "noun", "m", "pl:vini", "/ˈvi.no/", "{{inh|it|la|vīnum}}", "wine"),
    ("sale", "noun", "m", "pl:sali", "/ˈsa.le/", "{{inh|it|la|salem}}", "salt"),
    ("caffè", "noun", "m", "pl:caffè", "/kafˈfɛ/",
     "{{bor|it|ota|قهوه|tr=kahve}} {{der|it|ar|قهوة|tr=qahwa}}", "coffee"),
    ("libro", "noun", "m", "pl:libri", "/ˈli.bro/", "{{inh|it|la|librum}}", "book"),
    ("prenotare", "verb", None, "pp:prenotato;1s:prenoto;3s:prenota", "/pre.noˈta.re/",
     "{{der|it|la|praenotāre}}", "to book, reserve"),
    ("città", "noun", "f", "pl:città", "/t͡ʃitˈta/", "{{inh|it|roa-oit|cittade}} {{inh|it|la|cīvitātem}}", "city"),
    ("amico", "noun", "m", "pl:amici;f:amica;fpl:amiche", "/aˈmi.ko/", "{{inh|it|la|amīcum}}", "friend"),
    ("amore", "noun", "m", "pl:amori", "/aˈmo.re/", "{{inh|it|la|amōrem}}", "love"),
    ("amare", "verb", None, "pp:amato;1s:amo;3s:ama", "/aˈma.re/", "{{inh|it|la|amāre}}", "to love"),
    ("re", "noun", "m", "pl:re", "/re/", "{{inh|it|la|rēgem}}", "king"),
    ("tempo", "noun", "m", "pl:tempi", "/ˈtɛm.po/", "{{inh|it|la|tempus}}", "time"),
    ("volta", "noun", "f", "pl:volte", "/ˈvɔl.ta/", "{{der|it|it|voltare||to turn}} {{inh|it|la-vul|*volvitāre}}",
     "time, occasion"),
    ("anno", "noun", "m", "pl:anni", "/ˈan.no/", "{{inh|it|la|annum}}", "year"),
    ("mese", "noun", "m", "pl:mesi", "/ˈme.se/", "{{inh|it|la|mēnsem}}", "month"),
    ("ora", "noun", "f", "pl:ore", "/ˈo.ra/", "{{inh|it|la|hōra}}", "hour"),
    ("pioggia", "noun", "f", "pl:piogge", "/ˈpjɔd.d͡ʒa/", "{{inh|it|la-vul|*ploia}}", "rain"),
    ("piovere", "verb", None, "3s:piove;pp:piovuto", "/ˈpjɔ.ve.re/", "{{inh|it|la-vul|*plovere}}", "to rain"),
    ("neve", "noun", "f", "pl:nevi", "/ˈne.ve/", "{{inh|it|la|nivem}}", "snow"),
    ("pesce", "noun", "m", "pl:pesci", "/ˈpeʃ.ʃe/", "{{inh|it|la|piscem}}", "fish"),
    ("uccello", "noun", "m", "pl:uccelli", "/utˈt͡ʃɛl.lo/", "{{inh|it|la-vul|*aucellus}}", "bird"),
    ("cavallo", "noun", "m", "pl:cavalli", "/kaˈval.lo/", "{{inh|it|la|caballum}}", "horse"),
    ("buono", "adj", None, "f:buona;pl:buoni;fpl:buone", "/ˈbwɔ.no/", "{{inh|it|la|bonum}}", "good"),
    ("grande", "adj", None, "pl:grandi", "/ˈɡran.de/", "{{inh|it|la|grandem}}", "big"),
    ("mangiare", "verb", None, "pp:mangiato;1s:mangio;3s:mangia", "/manˈd͡ʒa.re/",
     "{{bor|it|fro|mangier}} {{der|it|la|mandūcāre}}", "to eat"),
    ("bere", "verb", None, "pp:bevuto;1s:bevo;3s:beve", "/ˈbe.re/", "{{inh|it|la|bibere}}", "to drink"),
    ("vedere", "verb", None, "pp:visto;1s:vedo;3s:vede", "/veˈde.re/", "{{inh|it|la|vidēre}}", "to see"),
    ("tre", "num", None, "", "/tre/", "{{inh|it|la|trēs}}", "three"),
    ("due", "num", None, "", "/ˈdu.e/", "{{inh|it|la|duae}}", "two"),
    ("andare", "verb", None, "pp:andato;1s:vado;3s:va", "/anˈda.re/", "{{unc|it}} {{der|it|la|ambulāre}}", "to go"),
    ("essere", "verb", None, "pp:stato;1s:sono;3s:è", "/ˈɛs.se.re/", "{{inh|it|la-vul|*essere}}", "to be"),
    ("banca", "noun", "f", "pl:banche", "/ˈbaŋ.ka/", "{{inh|it|lng|*banka}}", "bank (financial institution)"),
    ("riva", "noun", "f", "pl:rive", "/ˈri.va/", "{{inh|it|la|rīpa}}", "bank, shore"),
    ("scuola", "noun", "f", "pl:scuole", "/ˈskwɔ.la/", "{{inh|it|la|schola}}", "school"),
    ("musica", "noun", "f", "pl:musiche", "/ˈmu.zi.ka/", "{{inh|it|la|mūsica}}", "music"),
]:
    R("it", *args)

# ==========================================================================
# Portuguese  (IPA: Brazil, Portugal)
# ==========================================================================
for args in [
    ("noite", "noun", "f", "pl:noites", ("ˈnoj.t͡ʃi", "ˈnoj.tɨ"), "{{inh|pt|roa-opt|noite}} {{inh|pt|la|noctem}}", "night"),
    ("dia", "noun", "m", "pl:dias", ("ˈd͡ʒi.ɐ", "ˈdi.ɐ"), "{{inh|pt|roa-opt|dia}} {{inh|pt|la-vul|*dia}}", "day"),
    ("verão", "noun", "m", "pl:verões", ("veˈɾɐ̃w̃", "vɨˈɾɐ̃w̃"), "{{inh|pt|roa-opt|verão}} {{inh|pt|la-vul|*verānum}}", "summer"),
    ("inverno", "noun", "m", "pl:invernos", ("ĩˈvɛʁ.nu", "ĩˈvɛɾ.nu"), "{{inh|pt|roa-opt|inverno}} {{inh|pt|la|hībernum}}", "winter"),
    ("primavera", "noun", "f", "pl:primaveras", ("pɾi.maˈvɛ.ɾɐ", "pɾi.mɐˈvɛ.ɾɐ"),
     "{{inh|pt|roa-opt|primavera}} {{inh|pt|la-vul|*prīma vēra}}", "spring (season)"),
    ("fonte", "noun", "f", "pl:fontes", ("ˈfõ.t͡ʃi", "ˈfõ.tɨ"), "{{inh|pt|roa-opt|fonte}} {{inh|pt|la|fontem}}", "spring, fountain"),
    ("mola", "noun", "f", "pl:molas", ("ˈmɔ.lɐ", "ˈmɔ.lɐ"), "{{bor|pt|it|molla}}", "spring (device)"),
    ("saltar", "verb", None, "pp:saltado;1s:salto;3s:salta", ("sawˈtaʁ", "saɫˈtaɾ"),
     "{{inh|pt|roa-opt|saltar}} {{inh|pt|la|saltāre}}", "to jump"),
    ("água", "noun", "f", "pl:águas", ("ˈa.ɡwɐ", "ˈa.ɣwɐ"), "{{inh|pt|roa-opt|agua}} {{inh|pt|la|aqua}}", "water"),
    ("fogo", "noun", "m", "pl:fogos", ("ˈfo.ɡu", "ˈfo.ɣu"), "{{inh|pt|roa-opt|fogo}} {{inh|pt|la|focum}}", "fire"),
    ("sol", "noun", "m", "pl:sóis", ("ˈsɔw", "ˈsɔɫ"), "{{inh|pt|roa-opt|sol}} {{inh|pt|la|sōlem}}", "sun"),
    ("lua", "noun", "f", "pl:luas", ("ˈlu.ɐ", "ˈlu.ɐ"), "{{inh|pt|roa-opt|lũa}} {{inh|pt|la|lūna}}", "moon"),
    ("estrela", "noun", "f", "pl:estrelas", ("isˈtɾe.lɐ", "ɨʃˈtɾe.lɐ"), "{{inh|pt|roa-opt|estrela}} {{inh|pt|la|stēlla}}", "star"),
    ("mar", "noun", "m", "pl:mares", ("ˈmaʁ", "ˈmaɾ"), "{{inh|pt|roa-opt|mar}} {{inh|pt|la|mare}}", "sea"),
    ("árvore", "noun", "f", "pl:árvores", ("ˈaʁ.vo.ɾi", "ˈaɾ.vu.ɾɨ"), "{{inh|pt|roa-opt|arvor}} {{inh|pt|la|arborem}}", "tree"),
    ("mãe", "noun", "f", "pl:mães", ("ˈmɐ̃j̃", "ˈmɐ̃j̃"), "{{inh|pt|roa-opt|madre}} {{inh|pt|la|mātrem}}", "mother"),
    ("pai", "noun", "m", "pl:pais", ("ˈpaj", "ˈpaj"), "{{inh|pt|roa-opt|padre}} {{inh|pt|la|patrem}}", "father"),
    ("irmão", "noun", "m", "pl:irmãos;f:irmã", ("iʁˈmɐ̃w̃", "iɾˈmɐ̃w̃"), "{{inh|pt|roa-opt|irmão}} {{inh|pt|la|germānum}}", "brother"),
    ("nome", "noun", "m", "pl:nomes", ("ˈno.mi", "ˈno.mɨ"), "{{inh|pt|roa-opt|nome}} {{inh|pt|la|nōmen}}", "name"),
    ("coração", "noun", "m", "pl:corações", ("ko.ɾaˈsɐ̃w̃", "ku.ɾɐˈsɐ̃w̃"),
     "{{inh|pt|roa-opt|coraçon}} {{inh|pt|la-vul|*corātiōnem}}", "heart"),
    ("novo", "adj", None, "f:nova;pl:novos;fpl:novas", ("ˈno.vu", "ˈno.vu"), "{{inh|pt|roa-opt|novo}} {{inh|pt|la|novum}}", "new"),
    ("casa", "noun", "f", "pl:casas", ("ˈka.zɐ", "ˈka.zɐ"), "{{inh|pt|roa-opt|casa}} {{inh|pt|la|casa}}", "house"),
    ("cão", "noun", "m", "pl:cães", ("ˈkɐ̃w̃", "ˈkɐ̃w̃"), "{{inh|pt|roa-opt|can}} {{inh|pt|la|canem}}", "dog"),
    ("cachorro", "noun", "m", "pl:cachorros", ("kaˈʃo.ʁu", "kɐˈʃo.ʁu"), "{{bor|pt|es|cachorro||puppy}}", "dog (Brazil); puppy"),
    ("gato", "noun", "m", "pl:gatos;f:gata", ("ˈɡa.tu", "ˈɡa.tu"), "{{inh|pt|roa-opt|gato}} {{inh|pt|la-lat|cattus}}", "cat"),
    ("olho", "noun", "m", "pl:olhos", ("ˈo.ʎu", "ˈo.ʎu"), "{{inh|pt|roa-opt|ollo}} {{inh|pt|la|oculum}}", "eye"),
    ("mão", "noun", "f", "pl:mãos", ("ˈmɐ̃w̃", "ˈmɐ̃w̃"), "{{inh|pt|roa-opt|mão}} {{inh|pt|la|manum}}", "hand"),
    ("pé", "noun", "m", "pl:pés", ("ˈpɛ", "ˈpɛ"), "{{inh|pt|roa-opt|pee}} {{inh|pt|la|pedem}}", "foot"),
    ("dente", "noun", "m", "pl:dentes", ("ˈdẽ.t͡ʃi", "ˈdẽ.tɨ"), "{{inh|pt|roa-opt|dente}} {{inh|pt|la|dentem}}", "tooth"),
    ("leite", "noun", "m", "pl:leites", ("ˈlej.t͡ʃi", "ˈlɐj.tɨ"), "{{inh|pt|roa-opt|leite}} {{inh|pt|la-vul|*lacte}}", "milk"),
    ("pão", "noun", "m", "pl:pães", ("ˈpɐ̃w̃", "ˈpɐ̃w̃"), "{{inh|pt|roa-opt|pan}} {{inh|pt|la|pānem}}", "bread"),
    ("vinho", "noun", "m", "pl:vinhos", ("ˈvĩ.ɲu", "ˈvi.ɲu"), "{{inh|pt|roa-opt|vinno}} {{inh|pt|la|vīnum}}", "wine"),
    ("sal", "noun", "m", "pl:sais", ("ˈsaw", "ˈsaɫ"), "{{inh|pt|roa-opt|sal}} {{inh|pt|la|salem}}", "salt"),
    ("café", "noun", "m", "pl:cafés", ("kaˈfɛ", "kɐˈfɛ"), "{{bor|pt|fr|café}}", "coffee"),
    ("livro", "noun", "m", "pl:livros", ("ˈli.vɾu", "ˈli.vɾu"), "{{inh|pt|roa-opt|livro}} {{inh|pt|la|librum}}", "book"),
    ("reservar", "verb", None, "pp:reservado;1s:reservo;3s:reserva", ("he.zeʁˈvaʁ", "ʁɨ.zɨɾˈvaɾ"),
     "{{bor|pt|la|reservāre}}", "to book, reserve"),
    ("cidade", "noun", "f", "pl:cidades", ("siˈda.d͡ʒi", "siˈða.ðɨ"), "{{inh|pt|roa-opt|cidade}} {{inh|pt|la|cīvitātem}}", "city"),
    ("amigo", "noun", "m", "pl:amigos;f:amiga", ("aˈmi.ɡu", "ɐˈmi.ɣu"), "{{inh|pt|roa-opt|amigo}} {{inh|pt|la|amīcum}}", "friend"),
    ("amor", "noun", "m", "pl:amores", ("aˈmoʁ", "ɐˈmoɾ"), "{{inh|pt|roa-opt|amor}} {{inh|pt|la|amōrem}}", "love"),
    ("amar", "verb", None, "pp:amado;1s:amo;3s:ama", ("aˈmaʁ", "ɐˈmaɾ"), "{{inh|pt|roa-opt|amar}} {{inh|pt|la|amāre}}", "to love"),
    ("rei", "noun", "m", "pl:reis;f:rainha", ("ˈʁej", "ˈʁɐj"), "{{inh|pt|roa-opt|rei}} {{inh|pt|la|rēgem}}", "king"),
    ("tempo", "noun", "m", "pl:tempos", ("ˈtẽ.pu", "ˈtẽ.pu"), "{{inh|pt|roa-opt|tempo}} {{inh|pt|la|tempus}}", "time"),
    ("vez", "noun", "f", "pl:vezes", ("ˈves", "ˈveʃ"), "{{inh|pt|roa-opt|vez}} {{inh|pt|la|vicem}}", "time, occasion"),
    ("ano", "noun", "m", "pl:anos", ("ˈɐ.nu", "ˈɐ.nu"), "{{inh|pt|roa-opt|ano}} {{inh|pt|la|annum}}", "year"),
    ("mês", "noun", "m", "pl:meses", ("ˈmes", "ˈmeʃ"), "{{inh|pt|roa-opt|mes}} {{inh|pt|la|mēnsem}}", "month"),
    ("hora", "noun", "f", "pl:horas", ("ˈɔ.ɾɐ", "ˈɔ.ɾɐ"), "{{inh|pt|roa-opt|hora}} {{inh|pt|la|hōra}}", "hour"),
    ("chuva", "noun", "f", "pl:chuvas", ("ˈʃu.vɐ", "ˈʃu.vɐ"), "{{inh|pt|roa-opt|chuvia}} {{inh|pt|la|pluvia}}", "rain"),
    ("chover", "verb", None, "3s:chove;pp:chovido", ("ʃoˈveʁ", "ʃuˈveɾ"), "{{inh|pt|roa-opt|chover}} {{inh|pt|la-vul|*plovere}}", "to rain"),
    ("neve", "noun", "f", "pl:neves", ("ˈnɛ.vi", "ˈnɛ.vɨ"), "{{inh|pt|roa-opt|neve}} {{inh|pt|la|nivem}}", "snow"),
    ("peixe", "noun", "m", "pl:peixes", ("ˈpej.ʃi", "ˈpɐj.ʃɨ"), "{{inh|pt|roa-opt|peixe}} {{inh|pt|la|piscem}}", "fish"),
    ("pássaro", "noun", "m", "pl:pássaros", ("ˈpa.sa.ɾu", "ˈpa.sɐ.ɾu"), "{{inh|pt|roa-opt|passaro}} {{inh|pt|la-vul|*passar}}", "bird"),
    ("ave", "noun", "f", "pl:aves", ("ˈa.vi", "ˈa.vɨ"), "{{inh|pt|roa-opt|ave}} {{inh|pt|la|avem}}", "bird"),
    ("cavalo", "noun", "m", "pl:cavalos", ("kaˈva.lu", "kɐˈva.lu"), "{{inh|pt|roa-opt|cavalo}} {{inh|pt|la|caballum}}", "horse"),
    ("bom", "adj", None, "f:boa;pl:bons;fpl:boas", ("ˈbõ", "ˈbõ"), "{{inh|pt|roa-opt|bõo}} {{inh|pt|la|bonum}}", "good"),
    ("grande", "adj", None, "pl:grandes", ("ˈɡɾɐ̃.d͡ʒi", "ˈɡɾɐ̃.dɨ"), "{{inh|pt|roa-opt|grande}} {{inh|pt|la|grandem}}", "big"),
    ("comer", "verb", None, "pp:comido;1s:como;3s:come", ("koˈmeʁ", "kuˈmeɾ"), "{{inh|pt|roa-opt|comer}} {{inh|pt|la|comedere}}", "to eat"),
    ("beber", "verb", None, "pp:bebido;1s:bebo;3s:bebe", ("beˈbeʁ", "bɨˈβeɾ"), "{{inh|pt|roa-opt|bever}} {{inh|pt|la|bibere}}", "to drink"),
    ("ver", "verb", None, "pp:visto;1s:vejo;3s:vê", ("ˈveʁ", "ˈveɾ"), "{{inh|pt|roa-opt|veer}} {{inh|pt|la|vidēre}}", "to see"),
    ("três", "num", None, "", ("ˈtɾes", "ˈtɾeʃ"), "{{inh|pt|roa-opt|tres}} {{inh|pt|la|trēs}}", "three"),
    ("dois", "num", None, "f:duas", ("ˈdojs", "ˈdojʃ"), "{{inh|pt|roa-opt|dous}} {{inh|pt|la|duōs}}", "two"),
    ("ir", "verb", None, "pp:ido;1s:vou;3s:vai;pret3s:foi", ("ˈiʁ", "ˈiɾ"), "{{inh|pt|roa-opt|ir}} {{inh|pt|la|īre}}", "to go"),
    ("ser", "verb", None, "pp:sido;1s:sou;3s:é;pret3s:foi", ("ˈseʁ", "ˈseɾ"), "{{inh|pt|roa-opt|seer}} {{inh|pt|la|sedēre}}", "to be"),
    ("estar", "verb", None, "pp:estado;1s:estou;3s:está", ("isˈtaʁ", "ɨʃˈtaɾ"), "{{inh|pt|roa-opt|estar}} {{inh|pt|la|stāre}}", "to be (state, location)"),
    ("banco", "noun", "m", "pl:bancos", ("ˈbɐ̃.ku", "ˈbɐ̃.ku"), "{{inh|pt|roa-opt|banco}} {{der|pt|frk|*bank}}", "bank; bench"),
    ("margem", "noun", "f", "pl:margens", ("ˈmaʁ.ʒẽj̃", "ˈmaɾ.ʒɐ̃j̃"), "{{inh|pt|roa-opt|margen}} {{inh|pt|la|marginem}}", "bank (of a river); margin"),
    ("escola", "noun", "f", "pl:escolas", ("isˈkɔ.lɐ", "ɨʃˈkɔ.lɐ"), "{{inh|pt|roa-opt|escola}} {{inh|pt|la|schola}}", "school"),
    ("música", "noun", "f", "pl:músicas", ("ˈmu.zi.kɐ", "ˈmu.zi.kɐ"), "{{bor|pt|la|mūsica}}", "music"),
]:
    R("pt", *args)

# ==========================================================================
# French
# ==========================================================================
for args in [
    ("nuit", "noun", "f", "pl:nuits", "/nɥi/", "{{inh|fr|fro|nuit}} {{inh|fr|la|noctem}}", "night"),
    ("jour", "noun", "m", "pl:jours", "/ʒuʁ/", "{{inh|fr|fro|jor}} {{inh|fr|la|diurnum}}", "day"),
    ("été", "noun", "m", "pl:étés", "/e.te/", "{{inh|fr|fro|esté}} {{inh|fr|la|aestātem}}", "summer"),
    ("hiver", "noun", "m", "pl:hivers", "/i.vɛʁ/", "{{inh|fr|fro|ivern}} {{inh|fr|la|hībernum}}", "winter"),
    ("printemps", "noun", "m", "pl:printemps", "/pʁɛ̃.tɑ̃/", "{{inh|fr|fro|printens}} {{inh|fr|la|prīmum tempus}}", "spring (season)"),
    ("source", "noun", "f", "pl:sources", "/suʁs/", "{{inh|fr|fro|sorse}} {{der|fr|fro|sordre}} {{inh|fr|la|surgere}}", "spring, source"),
    ("ressort", "noun", "m", "pl:ressorts", "/ʁə.sɔʁ/", "{{der|fr|fr|ressortir||to spring back}}", "spring (device)"),
    ("sauter", "verb", None, "pp:sauté;1s:saute;3s:saute", "/so.te/", "{{inh|fr|fro|saulter}} {{inh|fr|la|saltāre}}", "to jump"),
    ("eau", "noun", "f", "pl:eaux", "/o/", "{{inh|fr|fro|eve}} {{inh|fr|la|aqua}}", "water"),
    ("feu", "noun", "m", "pl:feux", "/fø/", "{{inh|fr|fro|fu}} {{inh|fr|la|focum}}", "fire"),
    ("soleil", "noun", "m", "pl:soleils", "/sɔ.lɛj/", "{{inh|fr|fro|soleil}} {{inh|fr|la-vul|*sōliculus}}", "sun"),
    ("lune", "noun", "f", "pl:lunes", "/lyn/", "{{inh|fr|fro|lune}} {{inh|fr|la|lūna}}", "moon"),
    ("étoile", "noun", "f", "pl:étoiles", "/e.twal/", "{{inh|fr|fro|esteile}} {{inh|fr|la|stēlla}}", "star"),
    ("mer", "noun", "f", "pl:mers", "/mɛʁ/", "{{inh|fr|fro|mer}} {{inh|fr|la|mare}}", "sea"),
    ("arbre", "noun", "m", "pl:arbres", "/aʁbʁ/", "{{inh|fr|fro|arbre}} {{inh|fr|la|arborem}}", "tree"),
    ("mère", "noun", "f", "pl:mères", "/mɛʁ/", "{{inh|fr|fro|mere}} {{inh|fr|la|mātrem}}", "mother"),
    ("père", "noun", "m", "pl:pères", "/pɛʁ/", "{{inh|fr|fro|pere}} {{inh|fr|la|patrem}}", "father"),
    ("frère", "noun", "m", "pl:frères", "/fʁɛʁ/", "{{inh|fr|fro|frere}} {{inh|fr|la|frātrem}}", "brother"),
    ("nom", "noun", "m", "pl:noms", "/nɔ̃/", "{{inh|fr|fro|nom}} {{inh|fr|la|nōmen}}", "name"),
    ("cœur", "noun", "m", "pl:cœurs", "/kœʁ/", "{{inh|fr|fro|cuer}} {{inh|fr|la|cor}}", "heart"),
    ("nouveau", "adj", None, "f:nouvelle;pl:nouveaux;fpl:nouvelles", "/nu.vo/", "{{inh|fr|fro|novel}} {{inh|fr|la|novellum}}", "new"),
    ("neuf", "adj", None, "f:neuve;pl:neufs;fpl:neuves", "/nœf/", "{{inh|fr|fro|nuef}} {{inh|fr|la|novum}}", "brand-new"),
    ("maison", "noun", "f", "pl:maisons", "/mɛ.zɔ̃/", "{{inh|fr|fro|maison}} {{inh|fr|la|mānsiōnem}}", "house"),
    ("chien", "noun", "m", "pl:chiens;f:chienne", "/ʃjɛ̃/", "{{inh|fr|fro|chien}} {{inh|fr|la|canem}}", "dog"),
    ("chat", "noun", "m", "pl:chats;f:chatte", "/ʃa/", "{{inh|fr|fro|chat}} {{inh|fr|la-lat|cattus}}", "cat"),
    ("œil", "noun", "m", "pl:yeux", "/œj/", "{{inh|fr|fro|oil}} {{inh|fr|la|oculum}}", "eye"),
    ("main", "noun", "f", "pl:mains", "/mɛ̃/", "{{inh|fr|fro|main}} {{inh|fr|la|manum}}", "hand"),
    ("pied", "noun", "m", "pl:pieds", "/pje/", "{{inh|fr|fro|pié}} {{inh|fr|la|pedem}}", "foot"),
    ("dent", "noun", "f", "pl:dents", "/dɑ̃/", "{{inh|fr|fro|dent}} {{inh|fr|la|dentem}}", "tooth"),
    ("lait", "noun", "m", "pl:laits", "/lɛ/", "{{inh|fr|fro|lait}} {{inh|fr|la-vul|*lacte}}", "milk"),
    ("pain", "noun", "m", "pl:pains", "/pɛ̃/", "{{inh|fr|fro|pain}} {{inh|fr|la|pānem}}", "bread"),
    ("vin", "noun", "m", "pl:vins", "/vɛ̃/", "{{inh|fr|fro|vin}} {{inh|fr|la|vīnum}}", "wine"),
    ("sel", "noun", "m", "pl:sels", "/sɛl/", "{{inh|fr|fro|sel}} {{inh|fr|la|salem}}", "salt"),
    ("café", "noun", "m", "pl:cafés", "/ka.fe/", "{{bor|fr|it|caffè}}", "coffee"),
    ("livre", "noun", "m", "pl:livres", "/livʁ/", "{{inh|fr|fro|livre}} {{inh|fr|la|librum}}", "book"),
    ("réserver", "verb", None, "pp:réservé;1s:réserve;3s:réserve", "/ʁe.zɛʁ.ve/", "{{bor|fr|la|reservāre}}", "to book, reserve"),
    ("ville", "noun", "f", "pl:villes", "/vil/", "{{inh|fr|fro|vile}} {{inh|fr|la|vīlla}}", "city, town"),
    ("ami", "noun", "m", "pl:amis;f:amie", "/a.mi/", "{{inh|fr|fro|ami}} {{inh|fr|la|amīcum}}", "friend"),
    ("amour", "noun", "m", "pl:amours", "/a.muʁ/", "{{inh|fr|fro|amor}} {{inh|fr|la|amōrem}}", "love"),
    ("aimer", "verb", None, "pp:aimé;1s:aime;3s:aime", "/ɛ.me/", "{{inh|fr|fro|amer}} {{inh|fr|la|amāre}}", "to love"),
    ("roi", "noun", "m", "pl:rois;f:reine", "/ʁwa/", "{{inh|fr|fro|rei}} {{inh|fr|la|rēgem}}", "king"),
    ("temps", "noun", "m", "pl:temps", "/tɑ̃/", "{{inh|fr|fro|tens}} {{inh|fr|la|tempus}}", "time; weather"),
    ("fois", "noun", "f", "pl:fois", "/fwa/", "{{inh|fr|fro|feiz}} {{inh|fr|la|vicēs}}", "time, occasion"),
    ("an", "noun", "m", "pl:ans", "/ɑ̃/", "{{inh|fr|fro|an}} {{inh|fr|la|annum}}", "year"),
    ("année", "noun", "f", "pl:années", "/a.ne/", "{{inh|fr|fro|anee}} {{inh|fr|la-vul|*annāta}}", "year (duration)"),
    ("mois", "noun", "m", "pl:mois", "/mwa/", "{{inh|fr|fro|meis}} {{inh|fr|la|mēnsem}}", "month"),
    ("heure", "noun", "f", "pl:heures", "/œʁ/", "{{inh|fr|fro|ore}} {{inh|fr|la|hōra}}", "hour"),
    ("pluie", "noun", "f", "pl:pluies", "/plɥi/", "{{inh|fr|fro|pluie}} {{inh|fr|la-vul|*ploia}}", "rain"),
    ("pleuvoir", "verb", None, "3s:pleut;pp:plu", "/plœ.vwaʁ/", "{{inh|fr|fro|plovoir}} {{inh|fr|la-vul|*plovere}}", "to rain"),
    ("neige", "noun", "f", "pl:neiges", "/nɛʒ/", "{{der|fr|fr|neiger||to snow}} {{inh|fr|la-vul|*niviāre}}", "snow"),
    ("poisson", "noun", "m", "pl:poissons", "/pwa.sɔ̃/", "{{inh|fr|fro|poisson}} {{inh|fr|la-vul|*pisciō}}", "fish"),
    ("oiseau", "noun", "m", "pl:oiseaux", "/wa.zo/", "{{inh|fr|fro|oisel}} {{inh|fr|la-vul|*aucellus}}", "bird"),
    ("cheval", "noun", "m", "pl:chevaux", "/ʃə.val/", "{{inh|fr|fro|cheval}} {{inh|fr|la|caballum}}", "horse"),
    ("bon", "adj", None, "f:bonne;pl:bons;fpl:bonnes", "/bɔ̃/", "{{inh|fr|fro|bon}} {{inh|fr|la|bonum}}", "good"),
    ("grand", "adj", None, "f:grande;pl:grands;fpl:grandes", "/ɡʁɑ̃/", "{{inh|fr|fro|grant}} {{inh|fr|la|grandem}}", "big, tall"),
    ("manger", "verb", None, "pp:mangé;1s:mange;3s:mange", "/mɑ̃.ʒe/", "{{inh|fr|fro|mangier}} {{inh|fr|la|mandūcāre}}", "to eat"),
    ("boire", "verb", None, "pp:bu;1s:bois;3s:boit", "/bwaʁ/", "{{inh|fr|fro|boivre}} {{inh|fr|la|bibere}}", "to drink"),
    ("voir", "verb", None, "pp:vu;1s:vois;3s:voit", "/vwaʁ/", "{{inh|fr|fro|veoir}} {{inh|fr|la|vidēre}}", "to see"),
    ("trois", "num", None, "", "/tʁwa/", "{{inh|fr|fro|treis}} {{inh|fr|la|trēs}}", "three"),
    ("deux", "num", None, "", "/dø/", "{{inh|fr|fro|deus}} {{inh|fr|la|duōs}}", "two"),
    ("aller", "verb", None, "pp:allé;1s:vais;3s:va", "/a.le/", "{{inh|fr|fro|aler}} {{unc|fr}} {{inh|fr|la|ambulāre}}", "to go"),
    ("être", "verb", None, "pp:été;1s:suis;3s:est;impf3s:était", "/ɛtʁ/", "{{inh|fr|fro|estre}} {{inh|fr|la-vul|*essere}}", "to be"),
    ("banque", "noun", "f", "pl:banques", "/bɑ̃k/", "{{bor|fr|it|banca}}", "bank (financial institution)"),
    ("rive", "noun", "f", "pl:rives", "/ʁiv/", "{{inh|fr|fro|rive}} {{inh|fr|la|rīpa}}", "bank, shore"),
    ("école", "noun", "f", "pl:écoles", "/e.kɔl/", "{{inh|fr|fro|escole}} {{inh|fr|la|schola}}", "school"),
    ("musique", "noun", "f", "pl:musiques", "/my.zik/", "{{bor|fr|la|mūsica}}", "music"),
]:
    R("fr", *args)

# ==========================================================================
# Spanish
# ==========================================================================
for args in [
    ("noche", "noun", "f", "pl:noches", "/ˈno.t͡ʃe/", "{{inh|es|osp|noche}} {{inh|es|la|noctem}}", "night"),
    ("día", "noun", "m", "pl:días", "/ˈdi.a/", "{{inh|es|osp|dia}} {{inh|es|la-vul|*dia}}", "day"),
    ("verano", "noun", "m", "pl:veranos", "/beˈɾa.no/", "{{inh|es|osp|verano}} {{inh|es|la-vul|*verānum}}", "summer"),
    ("invierno", "noun", "m", "pl:inviernos", "/imˈbjeɾ.no/", "{{inh|es|osp|invierno}} {{inh|es|la|hībernum}}", "winter"),
    ("primavera", "noun", "f", "pl:primaveras", "/pɾi.maˈβe.ɾa/", "{{inh|es|osp|primavera}} {{inh|es|la-vul|*prīma vēra}}", "spring (season)"),
    ("manantial", "noun", "m", "pl:manantiales", "/ma.nanˈtjal/", "{{der|es|es|manante||flowing}} {{der|es|la|mānāre}}", "spring (of water)"),
    ("muelle", "noun", "m", "pl:muelles", "/ˈmwe.ʎe/", "", "spring (device); pier"),
    ("saltar", "verb", None, "pp:saltado;1s:salto;3s:salta", "/salˈtaɾ/", "{{inh|es|osp|saltar}} {{inh|es|la|saltāre}}", "to jump"),
    ("agua", "noun", "f", "pl:aguas", "/ˈa.ɣwa/", "{{inh|es|osp|agua}} {{inh|es|la|aqua}}", "water"),
    ("fuego", "noun", "m", "pl:fuegos", "/ˈfwe.ɣo/", "{{inh|es|osp|fuego}} {{inh|es|la|focum}}", "fire"),
    ("sol", "noun", "m", "pl:soles", "/sol/", "{{inh|es|osp|sol}} {{inh|es|la|sōlem}}", "sun"),
    ("luna", "noun", "f", "pl:lunas", "/ˈlu.na/", "{{inh|es|osp|luna}} {{inh|es|la|lūna}}", "moon"),
    ("estrella", "noun", "f", "pl:estrellas", "/esˈtɾe.ʎa/", "{{inh|es|osp|estrella}} {{inh|es|la|stēlla}}", "star"),
    ("mar", "noun", "m", "pl:mares", "/maɾ/", "{{inh|es|osp|mar}} {{inh|es|la|mare}}", "sea"),
    ("árbol", "noun", "m", "pl:árboles", "/ˈaɾ.βol/", "{{inh|es|osp|arbol}} {{inh|es|la|arborem}}", "tree"),
    ("madre", "noun", "f", "pl:madres", "/ˈma.ðɾe/", "{{inh|es|osp|madre}} {{inh|es|la|mātrem}}", "mother"),
    ("padre", "noun", "m", "pl:padres", "/ˈpa.ðɾe/", "{{inh|es|osp|padre}} {{inh|es|la|patrem}}", "father"),
    ("hermano", "noun", "m", "pl:hermanos;f:hermana", "/eɾˈma.no/", "{{inh|es|osp|hermano}} {{inh|es|la|germānum}}", "brother"),
    ("nombre", "noun", "m", "pl:nombres", "/ˈnom.bɾe/", "{{inh|es|osp|nombre}} {{inh|es|la|nōmen}}", "name"),
    ("corazón", "noun", "m", "pl:corazones", "/ko.ɾaˈθon/", "{{inh|es|osp|coraçon}} {{inh|es|la-vul|*corātiōnem}}", "heart"),
    ("nuevo", "adj", None, "f:nueva;pl:nuevos;fpl:nuevas", "/ˈnwe.βo/", "{{inh|es|osp|nuevo}} {{inh|es|la|novum}}", "new"),
    ("casa", "noun", "f", "pl:casas", "/ˈka.sa/", "{{inh|es|osp|casa}} {{inh|es|la|casa}}", "house"),
    ("perro", "noun", "m", "pl:perros;f:perra", "/ˈpe.ro/", "{{inh|es|osp|perro}} {{unc|es}}", "dog"),
    ("gato", "noun", "m", "pl:gatos;f:gata", "/ˈɡa.to/", "{{inh|es|osp|gato}} {{inh|es|la-lat|cattus}}", "cat"),
    ("ojo", "noun", "m", "pl:ojos", "/ˈo.xo/", "{{inh|es|osp|oio}} {{inh|es|la|oculum}}", "eye"),
    ("mano", "noun", "f", "pl:manos", "/ˈma.no/", "{{inh|es|osp|mano}} {{inh|es|la|manum}}", "hand"),
    ("pie", "noun", "m", "pl:pies", "/pje/", "{{inh|es|osp|pie}} {{inh|es|la|pedem}}", "foot"),
    ("diente", "noun", "m", "pl:dientes", "/ˈdjen.te/", "{{inh|es|osp|diente}} {{inh|es|la|dentem}}", "tooth"),
    ("leche", "noun", "f", "pl:leches", "/ˈle.t͡ʃe/", "{{inh|es|osp|leche}} {{inh|es|la-vul|*lacte}}", "milk"),
    ("pan", "noun", "m", "pl:panes", "/pan/", "{{inh|es|osp|pan}} {{inh|es|la|pānem}}", "bread"),
    ("vino", "noun", "m", "pl:vinos", "/ˈbi.no/", "{{inh|es|osp|vino}} {{inh|es|la|vīnum}}", "wine"),
    ("sal", "noun", "f", "pl:sales", "/sal/", "{{inh|es|osp|sal}} {{inh|es|la|salem}}", "salt"),
    ("café", "noun", "m", "pl:cafés", "/kaˈfe/", "{{bor|es|fr|café}}", "coffee"),
    ("libro", "noun", "m", "pl:libros", "/ˈli.βɾo/", "{{inh|es|osp|libro}} {{inh|es|la|librum}}", "book"),
    ("reservar", "verb", None, "pp:reservado;1s:reservo;3s:reserva", "/re.seɾˈβaɾ/", "{{bor|es|la|reservāre}}", "to book, reserve"),
    ("ciudad", "noun", "f", "pl:ciudades", "/θjuˈðad/", "{{inh|es|osp|cibdad}} {{inh|es|la|cīvitātem}}", "city"),
    ("amigo", "noun", "m", "pl:amigos;f:amiga", "/aˈmi.ɣo/", "{{inh|es|osp|amigo}} {{inh|es|la|amīcum}}", "friend"),
    ("amor", "noun", "m", "pl:amores", "/aˈmoɾ/", "{{inh|es|osp|amor}} {{inh|es|la|amōrem}}", "love"),
    ("amar", "verb", None, "pp:amado;1s:amo;3s:ama", "/aˈmaɾ/", "{{inh|es|osp|amar}} {{inh|es|la|amāre}}", "to love"),
    ("querer", "verb", None, "pp:querido;1s:quiero;3s:quiere", "/keˈɾeɾ/", "{{inh|es|osp|querer}} {{inh|es|la|quaerere}}", "to want; to love"),
    ("rey", "noun", "m", "pl:reyes;f:reina", "/rei̯/", "{{inh|es|osp|rey}} {{inh|es|la|rēgem}}", "king"),
    ("tiempo", "noun", "m", "pl:tiempos", "/ˈtjem.po/", "{{inh|es|osp|tiempo}} {{inh|es|la|tempus}}", "time; weather"),
    ("vez", "noun", "f", "pl:veces", "/beθ/", "{{inh|es|osp|vez}} {{inh|es|la|vicem}}", "time, occasion"),
    ("año", "noun", "m", "pl:años", "/ˈa.ɲo/", "{{inh|es|osp|anno}} {{inh|es|la|annum}}", "year"),
    ("mes", "noun", "m", "pl:meses", "/mes/", "{{inh|es|osp|mes}} {{inh|es|la|mēnsem}}", "month"),
    ("hora", "noun", "f", "pl:horas", "/ˈo.ɾa/", "{{inh|es|osp|hora}} {{inh|es|la|hōra}}", "hour"),
    ("lluvia", "noun", "f", "pl:lluvias", "/ˈʎu.βja/", "{{inh|es|osp|lluvia}} {{inh|es|la|pluvia}}", "rain"),
    ("llover", "verb", None, "3s:llueve;pp:llovido", "/ʎoˈβeɾ/", "{{inh|es|osp|llover}} {{inh|es|la-vul|*plovere}}", "to rain"),
    ("nieve", "noun", "f", "pl:nieves", "/ˈnje.βe/", "{{inh|es|osp|nieve}} {{inh|es|la|nivem}}", "snow"),
    ("pez", "noun", "m", "pl:peces", "/peθ/", "{{inh|es|osp|pez}} {{inh|es|la|piscem}}", "fish (living)"),
    ("pescado", "noun", "m", "pl:pescados", "/pesˈka.ðo/", "{{inh|es|la|piscātum}}", "fish (as food)"),
    ("pájaro", "noun", "m", "pl:pájaros", "/ˈpa.xa.ɾo/", "{{inh|es|osp|páxaro}} {{inh|es|la-vul|*passar}}", "bird"),
    ("ave", "noun", "f", "pl:aves", "/ˈa.βe/", "{{inh|es|osp|ave}} {{inh|es|la|avem}}", "bird"),
    ("caballo", "noun", "m", "pl:caballos;f:yegua", "/kaˈβa.ʎo/", "{{inh|es|osp|cavallo}} {{inh|es|la|caballum}}", "horse"),
    ("bueno", "adj", None, "f:buena;pl:buenos;fpl:buenas", "/ˈbwe.no/", "{{inh|es|osp|bueno}} {{inh|es|la|bonum}}", "good"),
    ("grande", "adj", None, "pl:grandes", "/ˈɡɾan.de/", "{{inh|es|osp|grande}} {{inh|es|la|grandem}}", "big"),
    ("comer", "verb", None, "pp:comido;1s:como;3s:come", "/koˈmeɾ/", "{{inh|es|osp|comer}} {{inh|es|la|comedere}}", "to eat"),
    ("beber", "verb", None, "pp:bebido;1s:bebo;3s:bebe", "/beˈβeɾ/", "{{inh|es|osp|bever}} {{inh|es|la|bibere}}", "to drink"),
    ("ver", "verb", None, "pp:visto;1s:veo;3s:ve", "/beɾ/", "{{inh|es|osp|veer}} {{inh|es|la|vidēre}}", "to see"),
    ("tres", "num", None, "", "/tɾes/", "{{inh|es|osp|tres}} {{inh|es|la|trēs}}", "three"),
    ("dos", "num", None, "", "/dos/", "{{inh|es|osp|dos}} {{inh|es|la|duōs}}", "two"),
    ("ir", "verb", None, "pp:ido;1s:voy;3s:va;pret3s:fue", "/iɾ/", "{{inh|es|osp|ir}} {{inh|es|la|īre}}", "to go"),
    ("ser", "verb", None, "pp:sido;1s:soy;3s:es;pret3s:fue", "/seɾ/", "{{inh|es|osp|seer}} {{inh|es|la|sedēre}}", "to be"),
    ("estar", "verb", None, "pp:estado;1s:estoy;3s:está", "/esˈtaɾ/", "{{inh|es|osp|estar}} {{inh|es|la|stāre}}", "to be (state, location)"),
    ("banco", "noun", "m", "pl:bancos", "/ˈbaŋ.ko/", "{{inh|es|osp|banco}} {{der|es|frk|*bank}}", "bank; bench"),
    ("orilla", "noun", "f", "pl:orillas", "/oˈɾi.ʎa/", "{{inh|es|osp|oriella}} {{inh|es|la|ōrella}}", "bank, shore, edge"),
    ("escuela", "noun", "f", "pl:escuelas", "/esˈkwe.la/", "{{inh|es|osp|escuela}} {{inh|es|la|schola}}", "school"),
    ("música", "noun", "f", "pl:músicas", "/ˈmu.si.ka/", "{{bor|es|la|mūsica}}", "music"),
]:
    R("es", *args)

# ==========================================================================
# Ancestors (Latin and others) — used to extend chains and to gloss etyma
# ==========================================================================
for args in [
    ("la", "nox", "night", "{{inh|la|itc-pro|*nokts}} {{inh|la|ine-pro|*nókʷts||night}}", "acc:noctem;gen:noctis"),
    ("la", "diēs", "day", "{{inh|la|itc-pro|*djēm}} {{inh|la|ine-pro|*dyḗws||sky, day}}", "acc:diem"),
    ("la", "diurnus", "daily, of the day", "{{der|la|la|diēs}}", "acc:diurnum"),
    ("la-vul", "*dia", "day", "{{der|la-vul|la|diēs}}", ""),
    ("la", "aestās", "summer", "{{der|la|ine-pro|*h₂eydʰ-||to burn}}", "acc:aestātem;gen:aestātis"),
    ("la", "vēr", "spring", "{{inh|la|itc-pro|*wēsr}} {{inh|la|ine-pro|*wésr̥||spring}}", "gen:vēris"),
    ("la-vul", "*verānum", "(season) of spring; summer", "{{der|la-vul|la|vēr}}", ""),
    ("la", "hībernus", "wintry, of winter", "{{der|la|la|hiems||winter}}", "acc:hībernum"),
    ("la", "hiems", "winter", "{{inh|la|ine-pro|*ǵʰeyṓm||winter}}", ""),
    ("la-vul", "*prīma vēra", "first spring", "{{der|la-vul|la|vēr}}", ""),
    ("la", "prīmum tempus", "first season", "{{der|la|la|tempus}}", ""),
    ("la", "surgō", "to rise", "", "inf:surgere;ppr:surgentem"),
    ("la", "fōns", "spring, fountain", "", "acc:fontem"),
    ("la", "saltō", "to dance, leap", "{{der|la|la|saliō||to jump}}", "inf:saltāre"),
    ("la", "saliō", "to jump", "{{inh|la|ine-pro|*sel-||to jump}}", ""),
    ("la", "aqua", "water", "{{inh|la|itc-pro|*akʷā}} {{inh|la|ine-pro|*h₂ékʷeh₂||water}}", ""),
    ("la", "focus", "hearth, fireplace", "", "acc:focum"),
    ("la", "sōl", "sun", "{{inh|la|itc-pro|*sāwel}} {{inh|la|ine-pro|*sóh₂wl̥||sun}}", "acc:sōlem"),
    ("la-vul", "*sōliculus", "little sun", "{{der|la-vul|la|sōl}}", ""),
    ("la", "lūna", "moon", "{{inh|la|itc-pro|*louksnā}} {{inh|la|ine-pro|*lewk-||light}}", ""),
    ("la", "stēlla", "star", "{{inh|la|itc-pro|*stērlā}} {{inh|la|ine-pro|*h₂stḗr||star}}", ""),
    ("la", "mare", "sea", "{{inh|la|itc-pro|*mari}} {{inh|la|ine-pro|*móri||sea}}", ""),
    ("la", "arbor", "tree", "", "acc:arborem"),
    ("la", "māter", "mother", "{{inh|la|itc-pro|*mātēr}} {{inh|la|ine-pro|*méh₂tēr||mother}}", "acc:mātrem"),
    ("la", "pater", "father", "{{inh|la|itc-pro|*patēr}} {{inh|la|ine-pro|*ph₂tḗr||father}}", "acc:patrem"),
    ("la", "frāter", "brother", "{{inh|la|itc-pro|*frātēr}} {{inh|la|ine-pro|*bʰréh₂tēr||brother}}", "acc:frātrem"),
    ("la-vul", "*frātellus", "little brother", "{{der|la-vul|la|frāter}}", ""),
    ("la", "germānus", "full brother, of the same parents", "{{der|la|la|germen||sprout, offspring}}", "acc:germānum"),
    ("la", "nōmen", "name", "{{inh|la|itc-pro|*nōmen}} {{inh|la|ine-pro|*h₁nómn̥||name}}", "abl:nōmine;gen:nōminis"),
    ("la", "cor", "heart", "{{inh|la|itc-pro|*kord}} {{inh|la|ine-pro|*ḱḗr||heart}}", "gen:cordis"),
    ("la-vul", "*corātiō", "heart (augmentative)", "{{der|la-vul|la|cor}}", "acc:*corātiōnem"),
    ("la", "novus", "new", "{{inh|la|itc-pro|*nowos}} {{inh|la|ine-pro|*néwos||new}}", "acc:novum"),
    ("la", "novellus", "new, young", "{{der|la|la|novus}}", "acc:novellum"),
    ("ine-pro", "*néwyos", "new", "{{der|ine-pro|ine-pro|*néwos}}", ""),
    ("la", "casa", "hut, cottage", "", ""),
    ("la", "mānsiō", "dwelling, stay", "{{der|la|la|maneō||to stay}}", "acc:mānsiōnem"),
    ("la", "canis", "dog", "{{inh|la|itc-pro|*kwō}} {{inh|la|ine-pro|*ḱwṓ||dog}}", "acc:canem"),
    ("la-lat", "cattus", "cat", "", ""),
    ("la", "oculus", "eye", "{{inh|la|itc-pro|*okelos}} {{inh|la|ine-pro|*h₃ekʷ-||to see}}", "acc:oculum"),
    ("la", "manus", "hand", "", "acc:manum"),
    ("la", "pēs", "foot", "{{inh|la|itc-pro|*pōds}} {{inh|la|ine-pro|*pṓds||foot}}", "acc:pedem;gen:pedis"),
    ("la", "dēns", "tooth", "{{inh|la|itc-pro|*dents}} {{inh|la|ine-pro|*h₃dónts||tooth}}", "acc:dentem;gen:dentis"),
    ("la-vul", "*lacte", "milk", "{{der|la-vul|la|lac}}", ""),
    ("la", "lac", "milk", "{{der|la|ine-pro|*ǵlákt-||milk}}", "gen:lactis"),
    ("la", "pānis", "bread", "{{inh|la|itc-pro|*pāstnis}} {{inh|la|ine-pro|*peh₂-||to protect, feed}}", "acc:pānem"),
    ("la", "vīnum", "wine", "{{inh|la|itc-pro|*wīnom}} {{der|la|ine-pro|*wóyh₁nom||wine}}", ""),
    ("la", "sāl", "salt", "{{inh|la|itc-pro|*sals}} {{inh|la|ine-pro|*séh₂ls||salt}}", "acc:salem;gen:salis"),
    ("la", "liber", "bark (of a tree); book", "", "acc:librum"),
    ("la", "cīvitās", "citizenship; city-state", "{{der|la|la|cīvis||citizen}}", "acc:cīvitātem"),
    ("la", "vīlla", "country house, farm", "", ""),
    ("la", "amīcus", "friend", "{{der|la|la|amō||I love}}", "acc:amīcum"),
    ("la", "amor", "love", "{{der|la|la|amō||I love}}", "acc:amōrem"),
    ("la", "amō", "I love", "", "inf:amāre"),
    ("la", "rēx", "king", "{{inh|la|itc-pro|*rēks}} {{inh|la|ine-pro|*h₃rḗǵs||ruler}}", "acc:rēgem"),
    ("la", "tempus", "time; season", "", ""),
    ("la", "vicis", "change, turn, alternation", "", "acc:vicem;nom:vicēs"),
    ("la-vul", "*volvitāre", "to turn, roll", "{{der|la-vul|la|volvō||to roll}}", ""),
    ("la", "annus", "year", "{{inh|la|itc-pro|*atnos}} {{inh|la|ine-pro|*h₂et-||to go}}", "acc:annum"),
    ("la-vul", "*annāta", "a year's duration", "{{der|la-vul|la|annus}}", ""),
    ("la", "mēnsis", "month", "{{inh|la|itc-pro|*mēns}} {{inh|la|ine-pro|*mḗh₁n̥s||moon, month}}", "acc:mēnsem"),
    ("la", "hōra", "hour", "{{bor|la|grc|ὥρα|tr=hṓra|t=any period of time; season}}", ""),
    ("grc", "ὥρα", "any period of time; season", "", ""),
    ("la", "pluvia", "rain", "{{der|la|la|pluō||to rain}}", ""),
    ("la-vul", "*ploia", "rain", "{{inh|la-vul|la|pluvia}}", ""),
    ("la-vul", "*plovere", "to rain", "{{der|la-vul|la|pluō}}", ""),
    ("la", "pluō", "to rain", "{{inh|la|ine-pro|*plew-||to flow, float}}", "inf:pluere"),
    ("la", "nix", "snow", "{{inh|la|itc-pro|*snixʷs}} {{inh|la|ine-pro|*snéygʷʰ-||to snow}}", "acc:nivem;gen:nivis"),
    ("la-vul", "*niviāre", "to snow", "{{der|la-vul|la|nix}}", ""),
    ("ine-pro", "*snóygʷʰos", "snow", "{{der|ine-pro|ine-pro|*snéygʷʰ-||to snow}}", ""),
    ("la", "piscis", "fish", "{{inh|la|itc-pro|*piskis}} {{inh|la|ine-pro|*peysk-||fish}}", "acc:piscem"),
    ("la-vul", "*pisciō", "fish", "{{der|la-vul|la|piscis}}", ""),
    ("la", "piscātus", "fished; a catch of fish", "{{der|la|la|piscis}}", "acc:piscātum"),
    ("la", "avis", "bird", "{{inh|la|itc-pro|*awis}} {{inh|la|ine-pro|*h₂éwis||bird}}", "acc:avem"),
    ("la-vul", "*aucellus", "little bird", "{{der|la-vul|la|avis}}", ""),
    ("la", "passer", "sparrow", "", ""),
    ("la-vul", "*passar", "sparrow; small bird", "{{inh|la-vul|la|passer}}", ""),
    ("la", "caballus", "horse, nag", "", "acc:caballum"),
    ("la", "bonus", "good", "{{inh|la|itc-pro|*dwenos}} {{inh|la|ine-pro|*dew-||to show favour}}", "acc:bonum"),
    ("la", "grandis", "large, great", "", "acc:grandem"),
    ("la", "mandūcō", "to chew", "", "inf:mandūcāre"),
    ("la", "comedō", "to eat up", "{{der|la|la|edō||to eat}}", "inf:comedere"),
    ("la", "edō", "to eat", "{{inh|la|itc-pro|*edō}} {{inh|la|ine-pro|*h₁ed-||to eat}}", ""),
    ("la", "bibō", "to drink", "{{inh|la|itc-pro|*pibō}} {{inh|la|ine-pro|*peh₃-||to drink}}", "inf:bibere"),
    ("la", "videō", "to see", "{{inh|la|itc-pro|*weidē-}} {{inh|la|ine-pro|*weyd-||to see}}", "inf:vidēre"),
    ("la", "trēs", "three", "{{inh|la|itc-pro|*trēs}} {{inh|la|ine-pro|*tréyes||three}}", ""),
    ("la", "duo", "two", "{{inh|la|itc-pro|*duō}} {{inh|la|ine-pro|*dwóh₁||two}}", "acc:duōs;nom:duae"),
    ("la", "ambulō", "to walk", "", "inf:ambulāre"),
    ("la", "eō", "to go", "{{inh|la|itc-pro|*eō}} {{inh|la|ine-pro|*h₁ey-||to go}}", "inf:īre"),
    ("la", "sum", "to be", "{{inh|la|itc-pro|*esom}} {{inh|la|ine-pro|*h₁es-||to be}}", "inf:esse"),
    ("la-vul", "*essere", "to be", "{{der|la-vul|la|esse}}", ""),
    ("la", "sedeō", "to sit", "{{inh|la|itc-pro|*sedēō}} {{inh|la|ine-pro|*sed-||to sit}}", "inf:sedēre"),
    ("la", "stō", "to stand", "{{inh|la|itc-pro|*stāō}} {{inh|la|ine-pro|*steh₂-||to stand}}", "inf:stāre"),
    ("la", "rīpa", "bank, shore", "", ""),
    ("la", "margō", "edge, border", "{{inh|la|ine-pro|*merǵ-||boundary}}", "acc:marginem"),
    ("la", "ōrella", "little edge", "{{der|la|la|ōra||edge, coast}}", ""),
    ("la", "ōra", "edge, border, coast", "", ""),
    ("la", "schola", "school; leisure given to learning", "{{bor|la|grc|σχολή|tr=skholḗ|t=leisure, school}}", ""),
    ("la", "mūsica", "music", "{{bor|la|grc|μουσική|tr=mousikḗ|t=art of the Muses}}", ""),
    ("la", "praenotō", "to note down beforehand", "", "inf:praenotāre"),
    ("la", "reservō", "to keep back, reserve", "", "inf:reservāre"),
    ("la", "quaerō", "to seek", "", "inf:quaerere"),
    ("la", "mānō", "to flow", "", "inf:mānāre"),
    ("lng", "*banka", "bench; counter", "{{inh|lng|gem-pro|*bankiz||bench}}", ""),
    ("frk", "*bank", "bench", "{{inh|frk|gem-pro|*bankiz||bench}}", ""),
    ("non", "*banki", "bank, ridge", "{{inh|non|gem-pro|*bankô||hill, slope}}", ""),
    ("ota", "قهوه", "coffee", "{{bor|ota|ar|قهوة|tr=qahwa}}", ""),
    ("ar", "قهوة", "coffee (originally a kind of wine)", "", ""),
]:
    A(*args)


# ==========================================================================
# Expansion into Kaikki-shaped records
# ==========================================================================
def _translation_items(g: G) -> list[dict]:
    items = []
    for lang, spec in g.tr.items():
        for part in filter(None, (p.strip() for p in spec.split("|"))):
            word, _, variant = part.partition("@")
            rec = ROM.get((lang, word))
            tags = []
            if rec and rec.get("head_templates"):
                gg = rec["head_templates"][0]["args"]["1"]
                tags.append({"m": "masculine", "f": "feminine"}.get(gg, gg))
            if variant == "BR":
                tags.append("Brazil")
            elif variant == "PT":
                tags.append("Portugal")
            items.append({"lang": lang, "code": lang, "word": word, "sense": g.label, "tags": tags})
    for z in g.zh.split("；"):
        if z.strip():
            items.append({"lang": "Chinese Mandarin", "code": "cmn", "word": z.strip(), "sense": g.label})
    return items


def kaikki_records():
    en_records = []
    for w in EN:
        sounds = [{"ipa": w["uk"], "tags": ["Received-Pronunciation"]},
                  {"ipa": w["us"], "tags": ["General-American"]}]
        first = True
        for n, (ety, blocks, groups, etytext) in enumerate(w["etys"], 1):
            for b in blocks:
                senses = []
                for s in b.senses:
                    sd = {"glosses": [s.gloss]}
                    if s.tags:
                        sd["tags"] = s.tags
                    if s.ex:
                        sd["examples"] = [{"text": e} for e in s.ex]
                    if s.syn:
                        sd["synonyms"] = [{"word": x} for x in s.syn]
                    senses.append(sd)
                rec = {"word": w["word"], "lang_code": "en", "pos": b.pos, "etymology_number": n,
                       "etymology_templates": templates_from_wikitext(ety), "sounds": sounds,
                       "forms": _forms(b.forms), "senses": senses,
                       "translations": [t for g in groups if g.pos == b.pos for t in _translation_items(g)]}
                if etytext:
                    rec["etymology_text"] = etytext
                if first:
                    for key, field in (("syn", "synonyms"), ("ant", "antonyms"), ("der", "derived")):
                        vals = [x.strip() for x in w[key].split(";") if x.strip()]
                        if vals:
                            rec[field] = [{"word": x} for x in vals]
                    first = False
                en_records.append(rec)
    missing = [(g_lang, word) for w in EN for (_, _, groups, _) in w["etys"] for g in groups
               for g_lang, spec in g.tr.items()
               for word in (p.partition("@")[0] for p in spec.split("|")) if (g_lang, word) not in ROM]
    if missing:
        raise SystemExit(f"sample_seed: translations without a Romance entry: {missing}")
    return en_records, list(ROM.values()), ANC
