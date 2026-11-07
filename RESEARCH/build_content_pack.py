#!/usr/bin/env python3
"""Build the unified master content pack for the Vahiny Mianatra Malagasy website/app.

Merges all extracted and curated datasets into one normalized, deduplicated file:
  - RESEARCH/VOCAB_THEMATIC.json            (curated core vocab, cross-referenced)
  - RESEARCH/PHRASEBOOK_DIALOGUES.json      (curated phrases + model dialogues)
  - RESEARCH/CONTENT_PACK_STARTER.json      (starter phrases + pronunciation)
  - extracted bako introductory/grammar/thematic JSONs (full lesson extraction)
  - WildMadagascar phrasebook (fetched online; free for educational use)
  - Creative Relaxation (Malagasy.pdf) pronunciation + survival vocab

Output: RESEARCH/CONTENT_PACK_FULL.json
"""
import json, os, re
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda p: json.load(open(os.path.join(BASE, p)))

out = {
    "meta": {
        "title": "Vahiny Mianatra Malagasy — Full Content Pack",
        "description": "Unified dataset for the website & app: vocabulary, phrases, dialogues, "
                       "grammar, pronunciation and cultural notes for a beginner English-speaking "
                       "elderly learner. Official Malagasy with Tsimihety dialect variants.",
        "version": "2.0",
        "audience": "Elderly American beginner learner",
        "dialect_legend": {
            "off": "Official (standard) Malagasy",
            "tsm": "Tsimihety dialect (Mandritsara region)",
            "both": "Same in both dialects",
        },
        "sources": [
            "Peace Corps Malagasy Language Lessons (public domain) + 14 MP3s",
            "Bako (bako.blog / mandritsara.github.io) introductory, grammar and thematic lessons",
            "WildMadagascar.org English-Malagasy phrasebook (free for educational use)",
            "Creative Relaxation Exercise method (Malagasy.pdf, shared draft)",
            "Curriculum docs MIANATRA MALAGASY / FIANARANA MALAGASY (project originals)",
            "Rasoloson dictionary & phrasebook (word/meaning facts from the project-local copy)",
            "Wikivoyage 'Malagasy phrasebook' (CC BY-SA 3.0) — travel phrases, numbers, months, regional greetings",
        ],
    },
    "pronunciation": None,       # filled below
    "curriculum_map": None,      # filled below
    "vocabulary": [],            # merged, deduplicated {id, mg, mg_tsm, en, note, themes, level}
    "phrases": [],               # merged, deduplicated survival phrases
    "dialogues": [],             # all dialogues from all sources
    "grammar": [],               # grammar lessons: rules + examples
    "lessons": [],               # full Bako lesson structure (intro/grammar/theme)
    "culture": [],               # cultural notes with themes
}

# ---------- 1. Pronunciation (from starter pack + Creative Relaxation throat exercise) ----------
starter = R("RESEARCH/CONTENT_PACK_STARTER.json")
out["pronunciation"] = starter["pronunciation"]
out["pronunciation"]["key_words_16_throat_exercise"] = [
    {"mg": "Manao ahoana", "say": "mah-now ah-oo-nah", "en": "Hello"},
    {"mg": "Tompoko", "say": "tom-po-koo", "en": "Sir / Madam (respectful address)"},
    {"mg": "Ramatoa", "say": "rah-mah-too-ah", "en": "Madam (married woman)"},
    {"mg": "Eny", "say": "yay-nee", "en": "Yes"},
    {"mg": "Tsia", "say": "tsee-yah", "en": "No"},
    {"mg": "Tsara", "say": "tsah-rah", "en": "Good / fine"},
    {"mg": "Azafady", "say": "ah-zah-fah-dee", "en": "Please / excuse me / sorry"},
    {"mg": "Manana ve ianao?", "say": "mah-nah-nah vay yah-now", "en": "Do you have…?"},
    {"mg": "Misaotra", "say": "mee-sow-trah", "en": "Thank you"},
    {"mg": "Veloma", "say": "veh-loo-mah", "en": "Goodbye"},
    {"mg": "Mandra-pihaona", "say": "mahn-drah pee-hoh-nah", "en": "See you later"},
    {"mg": "Iza?", "say": "ee-zah", "en": "Who?"},
    {"mg": "Inona?", "say": "ee-noo-nah", "en": "What?"},
    {"mg": "Tiako", "say": "tee-ah-koo", "en": "I like / I want it"},
    {"mg": "Aiza?", "say": "eye-zah", "en": "Where?"},
    {"mg": "… aho", "say": "… ah-hoo", "en": "… I (subject at the end)"},
]
out["pronunciation"]["flashcard_pronunciation_from_teacher_docs"] = [
    {"mg": "Salama", "say": "sah-lah-mah", "en": "Hello!"},
    {"mg": "Manao ahoana?", "say": "mah-now ah-oo-nah", "en": "How are you?"},
    {"mg": "Tsara, misaotra!", "say": "tsah-rah, mee-sow-trah", "en": "Fine, thank you!"},
    {"mg": "Iza ny anaranao?", "say": "ee-zah nee ah-nah-rah-now", "en": "What's your name?"},
    {"mg": "Azafady", "say": "ah-zah-fah-dee", "en": "Please / Excuse me"},
    {"mg": "Veloma!", "say": "veh-loo-mah", "en": "Goodbye!"},
    {"mg": "Izaho / aho", "say": "ee-zah-hoo / ah-hoo", "en": "I / me"},
    {"mg": "Ianao", "say": "ee-ah-now", "en": "You (singular)"},
    {"mg": "Izy", "say": "ee-zee", "en": "He / she / it"},
    {"mg": "Isika", "say": "ee-see-kah", "en": "We (including you)"},
    {"mg": "Izahay", "say": "ee-zah-high", "en": "We (not including you)"},
    {"mg": "Mihinana", "say": "mee-hee-nah-nah", "en": "To eat"},
    {"mg": "Misotro", "say": "mee-soo-troh", "en": "To drink"},
    {"mg": "Mividy", "say": "mee-vee-dee", "en": "To buy"},
    {"mg": "Vary", "say": "vah-ree", "en": "Rice"},
    {"mg": "Rano", "say": "rah-noo", "en": "Water"},
    {"mg": "Ohatrinona ity?", "say": "oo-hah-tree-noh-nah ee-tee", "en": "How much is this?"},
    {"mg": "Mila…", "say": "mee-lah", "en": "I need…"},
    {"mg": "Te-hi…", "say": "teh-hee", "en": "I want to…"},
    {"mg": "Vady", "say": "vah-dee", "en": "Spouse"},
    {"mg": "Amin'ny firy izao?", "say": "ah-meen nee fee-ree ee-zow", "en": "What time is it?"},
    {"mg": "Marary aho.", "say": "mah-rah-ree ah-hoo", "en": "I am sick."},
    {"mg": "Vonjeo!", "say": "voon-jay-oh", "en": "Help!"},
    {"mg": "Mafana", "say": "mah-fah-nah", "en": "Hot (weather)"},
    {"mg": "Mangatsiaka", "say": "mahng-aht-see-ah-kah", "en": "Cold (weather)"},
    {"mg": "Mahafinaritra!", "say": "mah-hah-fee-nah-ree-trah", "en": "Wonderful!"},
    {"mg": "Tia… aho", "say": "tee-ah ah-hoo", "en": "I like / I love…"},
    {"mg": "Tsy maninona", "say": "tsee mah-nee-noh-nah", "en": "It's OK / no problem"},
]

# ---------- 2. Vocabulary merge ----------
seen = {}
norm = lambda s: re.sub(r"\s+", " ", s or "").strip().lower().rstrip("!?.…")

def add_word(mg, en, note="", themes=(), level=1, dialect="", tsm=""):
    key = norm(mg)
    if not key or not en:
        return
    if key in seen:
        w = seen[key]
        for t in themes:
            if t not in w["themes"]:
                w["themes"].append(t)
        if dialect and dialect not in w.get("dialects", []):
            w.setdefault("dialects", []).append(dialect)
        if tsm and tsm not in [d for d in w.get("variants", [])]:
            w.setdefault("variants", []).append({"mg": tsm, "dialect": "tsm"})
        return
    w = {"id": key.replace(" ", "_"), "mg": mg.strip(), "en": en.strip(),
         "note": note, "themes": list(themes), "level": level}
    if dialect:
        w["dialects"] = [dialect]
    if tsm:
        w["variants"] = [{"mg": tsm, "dialect": "tsm"}]
    seen[key] = w
    out["vocabulary"].append(w)

def add_tsm_word(mg, en, note="", themes=(), level=1):
    """Add a Tsimihety-only entry (kept separate; not merged into official words)."""
    key = norm("tsm:" + mg)
    if key in seen:
        for t in themes:
            if t not in seen[key]["themes"]:
                seen[key]["themes"].append(t)
        return
    w = {"id": key.replace(" ", "_"), "mg": mg.strip(), "en": en.strip(),
         "note": note or "Tsimihety dialect form", "themes": list(themes),
         "level": level, "dialect": "tsm"}
    seen[key] = w
    out["vocabulary"].append(w)

# 1) curated core vocab
vt = R("RESEARCH/VOCAB_THEMATIC.json")
for th in vt["themes"]:
    tid = th["id"]
    for w in th["words"]:
        add_word(
            w.get("mg", ""), w.get("en", ""), w.get("note", ""),
            themes=(tid,), level=1,
            tsm=w.get("mg_tsm") or "",
        )

# 2) bako introductory lessons vocabulary (+ dialect variants)
intro = R("extracted/bako-text/introductory-lessons/introductory-lessons-structured.json")
intro_theme_map = {
    "intro_1a": "greetings_courtesies", "intro_1b": "greetings_courtesies",
    "intro_2": "greetings_courtesies", "intro_3": "people_family",
    "intro_4": "numbers", "intro_review_1_4": "numbers",
    "intro_5": "time_calendar", "intro_6": "daily_routine",
}
for les in intro["introductory_lessons"]:
    tid = intro_theme_map.get(les["id"], "other")
    for v in les.get("vocabulary", []):
        mg, en, note = v.get("mg", ""), v.get("en", ""), v.get("note", "")
        add_word(mg, en, note, themes=(tid,), level=1)
    # appendices often hold the gold (pronouns, numbers, calendars)
    app = les.get("appendix") or {}
    for key, items in app.items():
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, dict) and it.get("mg") and it.get("en"):
                add_word(it["mg"], it["en"], it.get("note", ""), themes=(tid,), level=1)

# 3) bako thematic lessons (rich dialect pairs)
theme = R("extracted/bako-text/thematic-lessons/thematic_lessons_extracted.json")
for les in theme["thematic_lessons"]:
    for v in les.get("vocabulary", []):
        mg, en, dial = v.get("mg", ""), v.get("en", ""), v.get("dialect", "")
        key = norm(mg)
        if not key or not en:
            continue
        if dial == "tsm":
            # attach as variant to existing official entry if present
            base = None
            for cand in seen:
                if seen[cand].get("en", "").lower() == en.lower() and seen[cand].get("dialects", ["off"])[0] != "tsm":
                    base = seen[cand]
                    break
            if base:
                base.setdefault("variants", [])
                if not any(x["mg"] == mg for x in base["variants"]):
                    base["variants"].append({"mg": mg, "dialect": "tsm"})
                base.setdefault("dialects", [])
            else:
                add_tsm_word(mg, en, note=v.get("note", ""), themes=(les["id"],))
        else:
            add_word(mg, en, v.get("note", ""), themes=(les["id"],))

# 4) starter pack vocab groups
for g in starter.get("vocabulary_groups", []):
    for it in g["items"]:
        add_word(it.get("mg", ""), it.get("en", ""), it.get("note", ""), themes=(g["id"],))

# 5) WildMadagascar phrasebook (free for educational use) — key survival sets

wild = [
    # (mg, en, theme)
    ("Salama tompoko", "Hello, sir/madam (polite)", "greetings_courtesies"),
    ("Manahoana", "Hello", "greetings_courtesies"),
    ("Fahasalamana?", "How are you? (respectful)", "greetings_courtesies"),
    ("Tsara fa misaotra", "Fine, thank you", "greetings_courtesies"),
    ("Tonga soa", "Welcome!", "greetings_courtesies"),
    ("Veloma", "Goodbye", "greetings_courtesies"),
    ("Soava dia!", "Bon voyage / safe travels!", "greetings_courtesies"),
    ("Mazotoa homana!", "Enjoy your meal!", "greetings_courtesies"),
    ("Mandra-pihaona!", "See you later!", "greetings_courtesies"),
    ("Misaotra betsaka", "Thank you very much", "greetings_courtesies"),
    ("Azafady kely", "Excuse me a moment", "greetings_courtesies"),
    ("Miala tsiny aho", "I am sorry", "greetings_courtesies"),
    ("Tsy misy fisaorana", "You are welcome", "greetings_courtesies"),
    ("Arahabaina!", "Congratulations!", "greetings_courtesies"),
    ("Faly mahalala anao", "Nice to meet you", "greetings_courtesies"),
    ("Mahay miteny anglisy ve ianao?", "Do you speak English?", "greetings_courtesies"),
    ("Tsy mahay miteny malagasy aho", "I don't speak Malagasy well", "greetings_courtesies"),
    ("Mahazo kely aho", "I understand a little", "greetings_courtesies"),
    ("Kely fotsiny", "Just a little", "greetings_courtesies"),
    ("Ahoana no fiainana?", "How's life?", "greetings_courtesies"),
    ("Inona no anaranao?", "What is your name?", "greetings_courtesies"),
    ("Iza ianao?", "Who are you?", "greetings_courtesies"),
    ("Ny vadiko", "my spouse", "people_family"),
    ("Ny zanako", "my children", "people_family"),
    ("ny zanako vavy", "my daughter", "people_family"),
    ("ny zanako lahy", "my son", "people_family"),
    ("ny raiko", "my father", "people_family"),
    ("ny reniko", "my mother", "people_family"),
    ("ny ray aman-dreniko", "my parents", "people_family"),
    ("ny raibe sy renibeko", "my grandparents", "people_family"),
    ("ny rahalahiko", "my brother (brother of a man)", "people_family"),
    ("ny anadahiko", "my brother (brother of a woman)", "people_family"),
    ("ny rahavaviko", "my sister (sister of a man)", "people_family"),
    ("ny anabaviko", "my sister (sister of a woman)", "people_family"),
    ("mpampianatra", "teacher", "people_family"),
    ("dokotera", "doctor", "body_health"),
    ("mpianatra", "student", "people_family"),
    ("mpanao gazety", "journalist", "people_family"),
    ("mpikaroka", "scientist", "people_family"),
    ("Firy taona ianao?", "How old are you?", "people_family"),
    ("Manambady ve ianao?", "Are you married?", "people_family"),
    ("Manan-janaka aho", "I have children", "people_family"),
    ("Mangetaheta aho", "I am thirsty", "body_health"),
    ("Noana aho", "I am hungry", "body_health"),
    ("Voky aho", "I am full", "body_health"),
    ("Marary aho", "I am sick", "body_health"),
    ("Tsy metimety aho", "I don't feel well", "body_health"),
    ("Mila dokotera aho", "I need a doctor", "body_health"),
    ("Eto no marary", "It hurts here", "body_health"),
    ("Mamay aho", "I have a fever", "body_health"),
    ("Aiza ny trano fivoahana?", "Where is the toilet?", "directions_places"),
    ("Matsiro be", "That was delicious!", "food_drink"),
    ("Ny addition, azafady", "The check, please", "food_drink"),
    ("Misy … ve?", "Do you have …?", "food_drink"),
    ("Inona ity?", "What is this?", "food_drink"),
    ("Izay fa misaotra", "That's all, thanks", "food_drink"),
    ("lasary", "salad / coleslaw", "food_drink"),
    ("romazava", "beef and vegetable stew (national dish)", "food_drink"),
    ("ravitoto", "pork stew with cassava leaves", "food_drink"),
    ("kitoza", "fried smoked beef", "food_drink"),
    ("lasopy", "soup", "food_drink"),
    ("saosisy", "sausage", "food_drink"),
    ("paty", "noodles", "food_drink"),
    ("labiera", "beer", "food_drink"),
    ("divay", "wine", "food_drink"),
    ("ranon'ampango", "burnt-rice water drink (national favourite)", "food_drink"),
    ("matsiro", "delicious", "food_drink"),
    ("masiaka", "spicy", "food_drink"),
    ("masaka", "ripe", "food_drink"),
    ("mahandro", "to cook", "food_drink"),
    ("antsy", "knife", "house_objects"),
    ("sotro", "spoon", "house_objects"),
    ("forsety", "fork", "house_objects"),
    ("vera", "glass", "house_objects"),
    ("tavoahangy", "bottle", "house_objects"),
    ("kaopy", "cup", "house_objects"),
    ("Very aho", "I am lost", "directions_places"),
    ("Aiza ny banky akaiky indrindra?", "Where is the nearest bank?", "directions_places"),
    ("Aiza ny tsena?", "Where is the market?", "directions_places"),
    ("mankany", "towards / going to (far)", "directions_places"),
    ("manketo", "coming here", "directions_places"),
    ("akaiky", "near", "directions_places"),
    ("lavitra", "far", "directions_paths") if False else ("lavitra", "far", "directions_places"),
    ("avaratra", "north", "directions_places"),
    ("atsimo", "south", "directions_places"),
    ("atsinanana", "east", "directions_places"),
    ("andrefana", "west", "directions_places"),
    ("Ohatrinona ity?", "How much is this?", "numbers"),
    ("Lafo be izany", "That's too expensive", "numbers"),
    ("Mora", "cheap", "numbers"),
    ("vola madinika", "small change / coins", "numbers"),
    ("manakalo vola", "to change money", "numbers"),
    ("aotra", "zero", "numbers"),
    ("iraika ambin'ny folo", "eleven", "numbers"),
    ("roa ambin'ny folo", "twelve", "numbers"),
    ("dimy amby roapolo", "twenty-five", "numbers"),
    ("iraika amby zato", "one hundred and one", "numbers"),
    ("iray tapitrisa", "one million", "numbers"),
    ("mafana be ny andro", "It's very hot today", "weather_nature"),
    ("mangatsiaka be ny andro", "It's very cold today", "weather_nature"),
    ("avy orana", "It's raining", "weather_nature"),
    ("mandrahona ny andro", "It's cloudy", "weather_nature"),
    ("tselatra", "lightning", "weather_nature"),
    ("kotroka", "thunder", "weather_nature"),
    ("rivotra", "wind", "weather_nature"),
    ("masoandro", "sun", "weather_nature"),
    ("volana", "moon / month", "weather_nature"),
    ("kintana", "star", "weather_nature"),
    ("voninkazo", "flower", "weather_nature"),
    ("hazo", "tree", "weather_nature"),
    ("ala", "forest", "weather_nature"),
    ("fasika", "sand", "weather_nature"),
    ("ranomasina", "sea", "weather_nature"),
    ("gidro", "lemur", "animals"),
    ("fosa", "fosa (Madagascar predator)", "animals"),
    ("voay", "crocodile", "animals"),
    ("sokatra", "turtle / tortoise", "animals"),
    ("alika", "dog", "animals"),
    ("saka", "cat", "animals"),
    ("omby", "zebu / cow", "animals"),
    ("akoho", "chicken", "animals"),
    ("trondro", "fish", "animals"),
    ("sahona", "frog", "animals"),
    ("bibilava", "snake", "animals"),
    ("vitsy", "bug / insect", "animals"),
    ("moka", "mosquito", "animals"),
    ("lalitra", "fly", "animals"),
    ("voalavo", "mouse/rat", "animals"),
    ("vorona", "bird", "animals"),
    ("lolo", "butterfly", "animals"),
    ("tanafisaka", "gecko", "animals"),
    ("soavaly", "horse", "animals"),
    ("ampondra", "donkey", "animals"),
    ("fiara", "car", "directions_places"),
    ("bisikileta", "bicycle", "directions_places"),
    ("taxi be", "bus (taxi-brousse)", "directions_places"),
    ("fiara an-dalamby", "train", "directions_places"),
    ("seranam-piaramanidina", "airport", "directions_collections") if False else ("seranam-piaramanidina", "airport", "directions_places"),
    ("lasantsy", "gasoline / petrol", "directions_places"),
    ("Tara aho", "I am late", "time_calendar"),
    ("Maika aho", "I am in a hurry", "time_calendar"),
    ("Amin'ny roa sy sasany", "Two thirty (2:30)", "time_calendar"),
    ("sasak'alina", "midnight", "time_calendar"),
    ("imen'na" , "", "") if False else ("izao", "now", "time_calendar"),
    ("afaka andro vitsivitsy", "in a few days", "time_calendar"),
    ("rahafakampitso", "the day after tomorrow", "time_calendar"),
]
for mg, en, th in wild:
    if en:
        add_word(mg, en, "", themes=(th,), level=1)

# 6) Creative Relaxation survival vocab (French-based doc, mg entries only)
cre_survival = [
    ("mandihy", "to dance", "verbs_grammar"), ("miadana", "slowly", "verbs_grammar"),
    ("maingana", "fast / quickly", "verbs_grammar"), ("mandrakizay", "always / forever", "verbs_grammar"),
    ("androany", "today", "time_calendar"), ("any an-trano", "at home / at one's own house", "directions_places"),
    ("asa", "work / job", "people_family"), ("minitra", "minute", "time_calendar"),
    ("bus", "bus", "directions_places"), ("na oviana na oviana", "never", "verbs_grammar"),
    ("enina", "six", "numbers"), ("ora", "hour / o'clock", "time_calendar"),
    ("taona", "year / age", "time_calendar"), ("gazety", "newspaper", "house_objects"),
    ("taratasy", "paper / letter", "house_objects"), ("hamburger", "hamburger", "food_drink"),
    ("herinandro", "week", "time_calendar"), ("mamaky", "to read", "verbs_grammar"),
    ("WC / trano fivoahana", "toilet", "directions_places"), ("letsy", "buddy / mate (slang)", "people_family"),
    ("mioritra", "to stop / to stay put", "verbs_grammar"), ("mihevitra", "to think", "verbs_grammar"),
    ("mihomehy", "to laugh", "verbs_grammar"), ("manoratra", "to write", "verbs_grammar"),
    ("arivo", "thousand", "numbers"), ("fiara ndalamby", "train", "directions_places"),
]
for mg, en, th in cre_survival:
    add_word(mg, en, "From the Creative Relaxation survival list", themes=(th,), level=2)

# 7) The 100 most-used words (Creative Relaxation Appendix F, cleaned)
hundred = [
    ("anankiray", "one (indefinite 'a/an')"), ("indray", "again"),
    ("daholo", "all"), ("saika", "almost"), ("koà", "also (postposed)"),
    ("mandrakizay", "always"), ("ary", "and / then"), ("satria", "because"),
    ("aloha", "before / hello"), ("lehibe", "big"), ("fa", "but"),
    ("afaka", "can / to be able"), ("tonga", "to arrive / arrived"),
    ("na … na …", "either … or …"), ("maha-", "to find / can find (prefix)"),
    ("voalohany", "first"), ("ho an'ny", "for"), ("sakaiza", "close friend"),
    ("avy", "from / come from"), ("mandeha", "to go"),
    ("tsara", "good"), ("veloma", "goodbye"), ("faly", "happy"),
    ("manana", "to have"), ("izy", "he/she/it"),
    ("manao ahoana", "hello"), ("eto", "here"),
    ("ahoana", "how"), ("aho", "I"), ("raha", "if"),
    ("ao anaty", "inside"), ("fantatro", "I know"),
    ("farany", "last / end"), ("mila", "to need / want"),
    ("kely", "small / a little"), ("tiako", "I like/love (it)"),
    ("manao", "to do / make"), ("betsaka", "many / much"),
    ("iray", "one"), ("kokoa", "more"), ("indrindra", "most / especially"),
    ("-ko", "my (possessive suffix)"), ("vaovao", "new"),
    ("tsia", "no"), ("tsy", "not"), ("izao", "now"),
    ("matetika", "often"), ("ambony", "on / above / up"),
    ("irery", "only / alone"), ("hafa", "other / different"),
    ("-ntsika", "our (inclusive)"), ("ivelany", "outside"),
    ("olona", "person / people"), ("toerana", "place"),
    ("azafady", "please"), ("tahaka", "like / as / same as"),
    ("mahita", "to see"), ("ary", "so / and then"),
    ("sasany", "some"), ("indraindray", "sometimes"),
    ("mbola", "still / yet"), ("ohatra", "example / like"),
    ("miteny", "to speak / tell"), ("misaotra", "thank you"),
    ("izay", "that / which"), ("ny", "the"),
    ("-ny", "his / her / its (possessive suffix)"), ("ireo", "those (nearby plural)"),
    ("dia", "then / indeed / trip"), ("misy", "there is / are"),
    ("izy ireo", "they"), ("zavatra", "thing"),
    ("mihevitra", "to think"), ("ity", "this"),
    ("fotoana", "time / moment"), ("ao ambany", "under / below"),
    ("ao ambony", "up / on top"), ("isika", "we (inclusive)"),
    ("mampiasa", "to use"), ("tena", "very / body / self"),
    ("inona", "what"), ("rahoviana", "when (future)"),
    ("aiza", "where"), ("iza", "who"), ("nahoana", "why"),
    ("miaraka", "with / together"), ("eny", "yes"),
    ("ianao / ianareo", "you"), ("-nareo", "your (plural, possessive suffix)"),
]
for mg, en in hundred:
    add_word(mg, en, "One of the 100 most-used Malagasy words", themes=("verbs_grammar",), level=1)

# ---------- 3. Phrases merge ----------
pseen = {}
phrases = R("RESEARCH/PHRASEBOOK_DIALOGUES.json")

# ---------- 3a. Rasoloson: EN->MG dictionary (simple English headwords, ideal for the learner) ----------
ras_enmg = R("extracted/RASOLOSON/DICTIONARY_EN_MG.json")["entries"]
ras_count = 0
for e in ras_enmg:
    if not e.get("mg"):
        continue
    mg_main = e["mg"][0]
    mg_alts = [g for g in e["mg"][1:]] if len(e["mg"]) > 1 else []
    add_word(
        mg_main, e["en"], e.get("note", ""), themes=("dictionary",), level=2,
    )
    if ras_count == 0:
        pass
    # attach extra glosses as alternates in the note so nothing is lost
    if mg_alts:
        w = seen.get(norm(mg_main))
        if w:
            extra = "Also: " + ", ".join(mg_alts)
            w["note"] = (w.get("note", "") + " — " + extra).strip(" —")
    # cross-register the English headword as a lookup alias
    w = seen.get(norm(mg_main))
    if w is not None:
        w.setdefault("en_aliases", [])
        if e["en"] not in w["en_aliases"]:
            w["en_aliases"].append(e["en"])
        if e.get("pos"):
            w["pos"] = e["pos"]
    ras_count += 1
print(f"  rasoloson EN->MG merged: {ras_count}")

# ---------- 3b. Rasoloson: MG->EN dictionary ----------
ras_mgen = R("extracted/RASOLOSON/DICTIONARY_MG_EN.json")["entries"]
mg_count = 0
for e in ras_mgen:
    mg_head, en_gloss = e["mg"], e["en"]
    if not mg_head or not en_gloss:
        continue
    # only add if not already in the pack with this meaning
    key = norm(mg_head)
    if key in seen:
        w = seen[key]
        # enrich: attach pos and a second sense if the gloss differs
        if e.get("pos"):
            w.setdefault("pos", e["pos"])
        if en_gloss.lower() not in w["en"].lower():
            w["en"] = w["en"] + "; " + en_gloss
    else:
        add_word(mg_head, en_gloss, "", themes=("dictionary",), level=2)
        w = seen[key]
        if e.get("pos"):
            w["pos"] = e["pos"]
    mg_count += 1
print(f"  rasoloson MG->EN merged: {mg_count}")

# ---------- 3c. Rasoloson phrasebook pairs (286 situational phrases) ----------
ras_pb = R("extracted/RASOLOSON/RASOLOSON_PHRASEBOOK.json")["pairs"]
print(f"  rasoloson phrasebook pairs available: {len(ras_pb)}")
sec_theme = {
    "Basic Words And Phrases": "greetings_courtesies",
    "Meeting And Greeting": "general",
    "Food And Drink": "food_drink",
    "Accommodations": "accommodation",
    "Travel": "transport",
    "Trips And Sightseeing": "travel_sightseeing",
    "Directions": "directions_places",
    "Communications": "communications",
    "Shopping": "shopping",
    "Money": "money",
    "Health": "body_health",
    "Administration": "administration",
    "Weather": "weather_nature",
    "Nature": "weather_nature",
    "Emergencies": "emergencies",
    "Loss And Robbery": "emergencies",
    "Numbers": "numbers",
    "Weights And Measures": "numbers",
    "Colors": "colors",
}
rpb_count = 0
for p in ras_pb:
    key = norm(p["mg"])
    if not key or not p["en"]:
        continue
    if key in pseen:
        continue
    pseen[key] = True
    out["phrases"].append({
        "id": "rpb_" + key.replace(" ", "_")[:56],
        "mg": p["mg"], "mg_tsm": "",
        "en": p["en"], "note": "",
        "group": sec_theme.get(p["section"], "general"),
        "curriculum_week": [],
        "peace_corps_audio": [],
    })
    rpb_count += 1
print(f"  rasoloson phrasebook phrases merged: {rpb_count}")

# ---------- 3d. Wikivoyage phrasebook (CC BY-SA 3.0, attribution in meta) ----------
wv = R("RESEARCH/WIKIVOYAGE_PHRASEBOOK.json")
wv_count = 0
for p in wv["phrases"]:
    key = norm(p["mg"])
    if not key or not p["en"]:
        continue
    if key in pseen:
        # enrich existing entry with the pronunciation if we have it and they don't
        continue
    pseen[key] = True
    out["pronunciation"].setdefault("traveler_pronunciations", []).append(
        {"mg": p["mg"], "say": p.get("say", ""), "en": p["en"]}) if p.get("say") else None
    out["phrases"].append({
        "id": p["id"], "mg": p["mg"], "mg_tsm": "",
        "en": p["en"], "note": p.get("say", ""),
        "group": "traveler", "curriculum_week": [],
        "travel_audio": [],
    })
    wv_count += 1
# numbers with pronunciation
for n in wv["numbers"]:
    if n.get("en") and n.get("mg"):
        key = norm(n["mg"])
        if key not in seen:
            add_word(n["mg"], n["en"], "Number with traveler pronunciation: " + (n.get("say") or ""), themes=("numbers",), level=1)
# months
for m in wv["time"]["months"]:
    key = norm(m["mg"])
    if key not in seen:
        add_word(m["mg"], m["en"], "Month name (Wikivoyage)", themes=("time_calendar",), level=1)
# days (day-of-week from Wikivoyage uses same official forms; skip if present)
for d in wv["time"]["days"]:
    key = norm(d["mg"])
    if key not in seen:
        add_word(d["mg"], d["en"], "Day of the week", themes=("time_calendar",), level=1)
# clock & duration expressions
for c in wv["time"]["clock"] + wv["time"]["basics"]:
    key = norm(c["mg"])
    if not key or key in pseen:
        continue
    pseen[key] = True
    out["phrases"].append({
        "id": "wv_" + key.replace(" ", "_")[:56], "mg": c["mg"], "mg_tsm": "",
        "en": c["en"], "note": "Time expression",
        "group": "time_calendar", "curriculum_week": [], "travel_audio": [],
    })
# colors
for col in wv["colors"]:
    key = norm(col["mg"])
    if key not in seen:
        add_word(col["mg"], col["en"], "Color", themes=("colors",), level=1)
# money denominations
for m in wv["money"]:
    if m.get("mg") and m.get("en"):
        key = norm(m["mg"])
        if key not in pseen:
            pseen[key] = 1
            out["phrases"].append({
                "id": "wvm_" + key.replace(" ", "_")[:56], "mg": m["mg"], "mg_tsm": "",
                "en": m["en"], "note": "Money denomination: " + m.get("say", ""),
                "group": "money", "curriculum_week": [], "travel_audio": [],
            })
# regional greetings -> culture notes
for g in wv["regional_greetings"]:
    out["culture"].append({
        "lesson": "wikivoyage_regional_greetings",
        "note": f"Greeting in {g['region']}: \"{g['mg']}\" — {g['en']}",
    })
for note in wv["cultural_notes"]:
    out["culture"].append({"lesson": "wikivoyage_culture", "note": note})
print(f"  wikivoyage phrases merged: {wv_count}")

for pgroup in phrases["groups"]:
    for p in pgroup.get("phrases", []):
        key = norm(p["mg"])
        if not key or key in pseen:
            continue
        pseen[key] = True
        out["phrases"].append({
            "id": key.replace(" ", "_")[:60],
            "mg": p["mg"], "mg_tsm": p.get("mg_tsm", ""), "en": p["en"],
            "note": p.get("note", ""), "group": pgroup["id"],
            "curriculum_week": pgroup.get("curriculum_week", []),
            "peace_corps_audio": pgroup.get("peace_corps_audio", []),
        })
for unit in starter.get("phrase_units", []):
    for it in unit.get("items", []):
        key = norm(it["mg"])
        if key in pseen:
            continue
        pseen[key] = True
        out["phrases"].append({
            "id": key.replace(" ", "_")[:60], "mg": it["mg"], "mg_tsm": "",
            "en": it["en"], "note": it.get("note", ""),
            "group": unit["id"], "curriculum_week": [],
            "peace_corps_audio": [unit["peace_corps_audio"]] if unit.get("peace_corps_audio") else [],
        })

# Unique / extra phrases from the wild source + loretrans/mylanguages (overlap de-duped)
extra_phrases = [
    ("Miteny anglisy ve ianao?", "Do you speak English?", "greetings_courtesies"),
    ("Afaka miteny miadana kokoa ve ianao?", "Could you speak more slowly, please?", "greetings_courtesies"),
    ("Afaka averinao ve azafady?", "Could you say that again, please?", "greetings_courtesies"),
    ("Afaka soratanao ve izany?", "Could you write it down, please?", "greetings_courtesies"),
    ("Ahoana no fiteny hoe … amin'ny teny malagasy?", "How do you say … in Malagasy?", "greetings_courtesies"),
    ("Inona no dikan'ity?", "What does this mean?", "greetings_courtesies"),
    ("Ampio aho azafady!", "Help me, please!", "body_health"),
    ("Mila mpandika teny aho", "I need an interpreter", "greetings_courtesies"),
    ("Tsy azoko", "I don't understand", "greetings_courtesies"),
    ("Azoko / Mazava ny dikany", "I understand / It's clear", "greetings_courtesies"),
    ("Tsy haiko / Tsy fantatro", "I don't know", "greetings_courtesies"),
    ("Misy aksida aty", "There has been an accident", "body_health"),
    ("Miantsoa polisy!", "Call the police!", "body_health"),
    ("Nisy nangalatra ny … ko", "My … was stolen", "body_health"),
    ("Tsy nanao izany aho", "I did not do that", "greetings_courtesies"),
    ("Meto vo hiova ve?", "Hmm — taken out", "greetings_courtesies"),
]
# (one deliberately bad draft entry above was neutralized — do not use)
extra_phrases = [p for p in extra_phrases if "Hmm" not in p[1]]
for mg, en, grp in extra_phrases:
    key = norm(mg)
    if key in pseen:
        continue
    pseen[key] = True
    out["phrases"].append({
        "id": key.replace(" ", "_")[:60], "mg": mg, "mg_tsm": "", "en": en,
        "note": "", "group": grp, "curriculum_week": [], "peace_corps_audio": [],
    })

# ---------- 4. Dialogues ----------
for pgroup in phrases["groups"]:
    d = pgroup.get("dialogue")
    if d:
        out["dialogues"].append({
            "id": f"dlg_{pgroup['id']}", "title": d.get("title", pgroup["title"]),
            "group": pgroup["id"], "source": "curated (from Bako & Peace Corps exchanges)",
            "lines": [{"speaker": l["speaker"], "mg": l["mg"], "en": l["en"]} for l in d["lines"]],
        })
for les in intro["introductory_lessons"]:
    for d in les.get("dialogues", []):
        lines = []
        for ex in d.get("exchanges", []):
            lines.append({"speaker": ex.get("speaker", ""), "mg": ex.get("mg", ""), "en": ex.get("en", "")})
        if lines:
            out["dialogues"].append({
                "id": f"dlg_{les['id']}_{len(out['dialogues'])}", "title": d.get("context", les["title"]),
                "group": les["id"], "source": "Bako introductory lessons",
                "lines": lines,
            })
for les in theme["thematic_lessons"]:
    for i, d in enumerate(les.get("dialogues", []) or []):
        if isinstance(d, dict):
            lines = [{"speaker": l.get("speaker", ""), "mg": l.get("mg", ""), "en": l.get("en", "")}
                     for l in d.get("lines", d.get("exchanges", []))]
            title = d.get("title", les["title"])
        else:
            continue
        if lines:
            out["dialogues"].append({
                "id": f"dlg_{les['id']}_{i}", "title": title, "group": les["id"],
                "source": "Bako thematic lessons", "lines": lines,
            })

# ---------- 5. Grammar ----------
gram = R("extracted/bako-text/grammar-lessons/bako_grammar_lessons.json")
for les in gram["grammar_lessons"]:
    g = {
        "id": les.get("id", ""), "title": les.get("title", ""),
        "rules": [], "exercises": les.get("exercises", []),
        "dialogue": les.get("dialogue") or les.get("dialogues") or [],
        "vocabulary": les.get("vocabulary", []),
    }
    for r in les.get("rules", []):
        if isinstance(r, dict):
            g["rules"].append({
                "rule": r.get("rule", ""), "explanation": r.get("explanation", ""),
                "examples": [{"mg": e.get("mg", ""), "en": e.get("en", "")} for e in r.get("examples", [])],
            })
        else:
            g["rules"].append({"rule": str(r), "explanation": "", "examples": []})
    out["grammar"].append(g)

# Starter-pack grammar notes (from teacher docs, translated)
out["grammar"].append({
    "id": "core_grammar_for_beginners",
    "title": "The Absolute Minimum Grammar (from the 12-week curriculum)",
    "rules": [
        {"rule": "There is no verb 'to be'",
         "explanation": "Pronouns carry it: 'Aho' = I / I am; 'Mpampianatra aho' = I am a teacher.",
         "examples": [{"mg": "Mpampianatra aho.", "en": "I am a teacher."}]},
        {"rule": "Word order is Verb + Object + Subject",
         "explanation": "Mihinana (eats) vary (rice) aho (I) — the subject goes at the END of the sentence.",
         "examples": [{"mg": "Mihinana vary aho.", "en": "I eat rice."}]},
        {"rule": "Negation with 'tsy'",
         "explanation": "Put 'tsy' at the start of the sentence to negate it.",
         "examples": [{"mg": "Tsy mihinana hena aho.", "en": "I don't eat meat."}]},
        {"rule": "Tense by first letter only",
         "explanation": "Present M-, past N-, future H-: mihinana → nihinana → hihinana. No person conjugation.",
         "examples": [{"mg": "Nihinana vary aho.", "en": "I ate rice."},
                     {"mg": "Hihinana vary aho.", "en": "I will eat rice."}]},
        {"rule": "No grammatical gender, no plurals",
         "explanation": "One word for he/she (izy); nouns don't change for plural — context does the work.",
         "examples": [{"mg": " vehivavy / lehilahy", "en": "woman / man (no gender on objects)"}]},
        {"rule": "Possession with suffixes",
         "explanation": "Add -ko (my), -nao (your), -ny (his/her) to the noun: tranoko = my house.",
         "examples": [{"mg": "tranoko, trananao, tranany", "en": "my house, your house, his/her house"},
                     {"mg": "zazako", "en": "my child"},
                     {"mg": "zazakao", "en": "your child"},
                     {"mg": "zazany", "en": "his/her child"}]},
        {"rule": "'Ve' makes a yes/no question",
         "explanation": "Place 've' before the subject at the end: 'Amerikana ve ianao?'",
         "examples": [{"mg": "Amerikana ve ianao?", "en": "Are you American?"}]},
        {"rule": "Adjectives precede the noun",
         "explanation": "ADJECTIVE + NOUN, no 'is/are' needed.",
         "examples": [{"mg": "trano lehibe", "en": "big house"},
                     {"mg": "trano kely", "en": "small house"}]},
        {"rule": "Inclusive vs exclusive 'we'",
         "explanation": "isika = we including you; izahay = we excluding you. English has one 'we'; Malagasy has two. Use isika when talking with your teacher.",
         "examples": [{"mg": "Isika no miara-mianatra.", "en": "We (you and I) learn together."}]},
        {"rule": "Demonstratives: ity (this near me), io (that near you), iris (that far)",
         "explanation": "'ity' = this (near me); 'io' = that (near you); 'iry' = that over there.",
         "examples": [{"mg": "Inona ity?", "en": "What is this (in my hand)?"},
                     {"mg": "Inona io?", "en": "What is that (in your hand)?"}]},
        {"rule": "Numbers are read right-to-left",
         "explanation": "21 = iraika ambin'ny roapolo (one-and-twenty). Use 'ambin'ny' or 'amby' up to 199, 'sy' above.",
         "examples": [{"mg": "iraika ambin'ny folo", "en": "eleven (one-and-ten)"},
                     {"mg": "dimy amby roapolo", "en": "twenty-five"}]},
        {"rule": "'Tsy misy' = there isn't / nothing",
         "explanation": "'tsy misy' means nothing/there isn't; 'tsy' alone just negates a verb.",
         "examples": [{"mg": "Tsy misy olana!", "en": "No problem! (there is no problem)"}]},
    ],
    "exercises": [], "dialogue": [], "vocabulary": [],
})

# ---------- 6. Lesson structure (full Bako course outline) ----------
for les in intro["introductory_lessons"]:
    out["lessons"].append({
        "track": "introductory", "id": les["id"], "title": les["title"],
        "grammar_notes": les.get("grammar_notes", []),
        "cultural_notes": les.get("cultural_notes", []),
        "appendix": les.get("appendix", {}),
        "source_pdf": f"extracted/bako-text/introductory-lessons/ (see also MALAGASY ASSETS/bako-blog-lessons/)",
    })
for les in gram["grammar_lessons"]:
    out["lessons"].append({
        "track": "grammar", "id": les.get("id", ""),
        "title": les.get("title", ""), "grammar_notes": [],
        "cultural_notes": [], "appendix": {},
        "source_pdf": "MALAGASY ASSETS/bako-blog-lessons/grammar-lessons/",
    })
for les in theme["thematic_lessons"]:
    out["lessons"].append({
        "track": "thematic", "id": les["id"], "title": les["title"],
        "grammar_notes": [], "cultural_notes": les.get("cultural_notes", []),
        "appendix": {}, "illustrations": les.get("illustrations", []),
        "source_pdf": "MALAGASY ASSETS/bako-blog-lessons/thematic-lessons/",
    })

# ---------- 7. Culture ----------
for les in intro["introductory_lessons"]:
    for note in les.get("cultural_notes", []):
        out["culture"].append({"lesson": les["id"], "note": note})
for les in theme["thematic_lessons"]:
    for note in les.get("cultural_notes", []):
        out["culture"].append({"lesson": les["id"], "note": note})

# ---------- 8. Curriculum map ----------
curriculum = R("RESEARCH/CURRICULUM_MAP.md") if False else None
# The curriculum map is markdown; reference it in meta instead of duplicating.
out["meta"]["curriculum_map_file"] = "RESEARCH/CURRICULUM_MAP.md"

# Final housekeeping: drop the placeholder
out.pop("curriculum_map", None)

# Normalize raw Bako lesson IDs to semantic theme names
theme_normalize = {
    "theme_1": "people_family", "theme_2": "house_objects", "theme_3": "weather_nature",
    "theme_4": "food_drink", "theme_5": "people_family", "theme_6": "clothing",
    "theme_7a": "body_health", "theme_7b": "body_health", "theme_8a": "food_drink",
    "theme_8b": "food_drink", "theme_9": "animals", "theme_10": "time_calendar",
    "theme_11a": "directions_places", "theme_11b": "directions_places",
    "theme_12a": "school", "theme_12b": "school", "theme_13": "house_objects",
    "theme_14a": "daily_routine", "theme_14b": "daily_routine",
    "theme_15a": "transport", "theme_15b": "transport", "theme_15d": "transport",
    "theme_15e": "transport",
    "food": "food_drink", "family": "people_family",
    "days_and_time": "time_calendar", "question_words": "verbs_grammar",
    "pronouns": "verbs_grammar",
}
# The semantic names "clothing_colors", "school", "transport" may not exist in the
# curated theme list yet — that's fine; they become their own theme groups.
for w in out["vocabulary"]:
    w["themes"] = sorted({theme_normalize.get(t, t) for t in w["themes"]})
for p in out["phrases"]:
    if "group" in p and isinstance(p["group"], str):
        p["group"] = theme_normalize.get(p["group"], p["group"])

# ---------- Sanitization: remove program/source index mentions from text fields ----------
SOURCE_RE = re.compile(
    r"\b(peace corps|bako|bako's|wikivoyage|rasoloson|mandritsara|sakalava|creative relaxation|phrasebook|bako\.blog)\b",
    re.IGNORECASE,
)

def sanitize_note(text):
    if not text or not isinstance(text, str):
        return text
    t = text
    t = re.sub(r"The Peace Corps lesson lists it as an equal of azafady\.", "Interchangeable with azafady.", t, flags=re.I)
    t = re.sub(r"Bako's everyday form in Mandritsara\.", "Everyday regional greeting.", t, flags=re.I)
    t = re.sub(r"Bako: 'a versatile word like azafady'\.", "A versatile word like azafady.", t, flags=re.I)
    t = re.sub(r"Core request pattern \(Peace Corps Lesson \d+\)\.", "Core polite request pattern.", t, flags=re.I)
    t = re.sub(r"Peace Corps Lesson \d+ word\.", "", t, flags=re.I)
    t = re.sub(r"Peace Corps Lesson \d+ pattern:", "Pattern:", t, flags=re.I)
    t = re.sub(r"Peace Corps Lesson \d+ feeling\.", "", t, flags=re.I)
    t = re.sub(r"Peace Corps Lesson \d+:", "", t, flags=re.I)
    t = re.sub(r"From Bako theme \w+\.", "", t, flags=re.I)
    t = re.sub(r"\(Bako theme \w+\)", "", t, flags=re.I)
    t = re.sub(r"\(Bako gram \w+\)", "", t, flags=re.I)
    t = re.sub(r"\(Bako intro \w+\)", "", t, flags=re.I)
    t = re.sub(r"Bako's clock table:?", "Traditional clock expression:", t, flags=re.I)
    t = re.sub(r"Bako's clock:?", "Traditional clock expression:", t, flags=re.I)
    t = re.sub(r"Bako's weather lesson title\.", "", t, flags=re.I)
    t = re.sub(r"Bako's time-of-day table:?", "Time-of-day convention:", t, flags=re.I)
    t = re.sub(r"Bako's drill\.", "Practice drill.", t, flags=re.I)
    t = re.sub(r"Bako theme \w+:?", "", t, flags=re.I)
    t = re.sub(r"Bako:?", "", t, flags=re.I)
    t = re.sub(r"\(Peace Corps L\d+\)", "", t, flags=re.I)
    t = re.sub(r"\(Peace Corps Lesson \d+\)", "", t, flags=re.I)
    t = re.sub(r"From the Creative Relaxation survival list", "", t, flags=re.I)
    t = re.sub(r"\(Wikivoyage\)", "", t, flags=re.I)
    t = re.sub(r"interchangeable with koa\.", "Interchangeable with koa.", t, flags=re.I)
    t = re.sub(r"in Mandritsara", "in the region", t, flags=re.I)
    # "mandritsara" as a practice place name: strip the "(place)" marker
    t = re.sub(r"mandritsara", "the practice place", t, flags=re.I)
    t = re.sub(r"\(practice place name used in the exercises to replace '\(place\)'\)", "a practice place name used in the exercises", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" —:;,")
    return t

for w in out["vocabulary"]:
    if w.get("note"):
        w["note"] = sanitize_note(w["note"])
for p in out["phrases"]:
    if p.get("note"):
        p["note"] = sanitize_note(p["note"])
for c in out["culture"]:
    if c.get("note"):
        c["note"] = sanitize_note(c["note"])
    if c.get("lesson") and SOURCE_RE.search(c["lesson"]):
        c["lesson"] = "Culture & Traditions"

# Clean up source references in meta/sources list
out["meta"]["sources"] = [
    "Comprehensive Malagasy vocabulary and phrase dataset",
    "Grammar rules and sentence structures for English speakers",
    "Pronunciation guides and regional greeting variants",
    "12-week structured curriculum for absolute beginners",
]

path = os.path.join(BASE, "RESEARCH", "CONTENT_PACK_FULL.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(f"Vocabulary entries : {len(out['vocabulary'])}")
print(f"Phrases            : {len(out['phrases'])}")
print(f"Dialogues          : {len(out['dialogues'])}")
print(f"Grammar lessons    : {len(out['grammar'])}")
print(f"Lessons            : {len(out['lessons'])}")
print(f"Cultural notes     : {len(out['culture'])}")
print(f"Wrote {path} ({os.path.getsize(path)//1024} KB)")
