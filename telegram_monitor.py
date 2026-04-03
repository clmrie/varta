"""
VARTA Telegram Monitor
Fetches messages from Ukrainian news/military Telegram channels,
scores them by importance, and outputs a filtered JSON feed.

Usage:
  First run (interactive login):
    python telegram_monitor.py --setup
  Normal run:
    python telegram_monitor.py

Environment variables:
  TELEGRAM_API_ID       - from my.telegram.org
  TELEGRAM_API_HASH     - from my.telegram.org
  TELEGRAM_SESSION      - StringSession (from --setup)
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from deep_translator import GoogleTranslator
from telethon import TelegramClient
from telethon.sessions import StringSession

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
FEED_FILE = DATA_DIR / "telegram_feed.json"
MAX_FEED_ITEMS = 25
EXPIRY_HOURS_CRITICAL = 24
EXPIRY_HOURS_DEFAULT = 12
# Max messages to fetch per channel per run
FETCH_LIMIT = 20
# Only consider messages from the last N hours
LOOKBACK_HOURS = 48
# Minimum importance score to include in feed
MIN_SCORE = 3.0
# Max items from a single channel per run (anti-flood)
MAX_PER_CHANNEL = 2

# ---------------------------------------------------------------------------
# Channels — organised by tier
# ---------------------------------------------------------------------------

CHANNELS = {
    # Tier 1: Official government / military (highest trust)
    "@GeneralStaffZSU": {"tier": 1, "name": "General Staff ZSU"},
    "@V_Zelenskiy_official": {"tier": 1, "name": "Zelenskyy Official"},
    "@Ukraine_MFA": {"tier": 1, "name": "Ukraine MFA"},
    "@kpszsu": {"tier": 1, "name": "Ukrainian Air Force"},

    # Tier 2: Major verified news sources
    "@KyivIndependent_official": {"tier": 2, "name": "Kyiv Independent"},
    "@uniannet": {"tier": 2, "name": "UNIAN"},
    "@pravda_eng": {"tier": 2, "name": "Ukrainska Pravda"},

    # Tier 3: Aggregators / analysts
    "@DeepStateUA": {"tier": 3, "name": "DeepState"},
}

# ---------------------------------------------------------------------------
# Civilian threat scoring
#
# This system is designed for a regular person asking:
#   "Am I in danger? Should I go to the shelter?"
#
# Priority 1: Incoming threats (missiles/drones heading somewhere NOW)
# Priority 2: Confirmed impacts (explosions, strikes on cities)
# Priority 3: Casualties & damage (people hurt, buildings destroyed)
# Priority 4: Infrastructure (power/water/heating down)
# Priority 5: Large-scale attack summaries
#
# Filtered OUT: frontline ops, military commentary, diplomacy,
#               fundraising, foreign affairs, analysis
# ---------------------------------------------------------------------------

# --- CIVILIAN THREAT keywords (what can hurt you) ---

# Incoming threat — drones/missiles heading towards a region RIGHT NOW
INCOMING_THREAT = re.compile(
    r"у напрямку|напрямок|курс на|heading|in.?bound|"
    r"балістик|ballistic|запуск|launch|злітав|took off|"
    r"загроза застосування|threat of|"
    r"тривога|alert|сирен|siren|"
    r"крилат[аі] ракет|cruise missile|"
    r"shahed|шахед|geran|герань|моп[еє]д|moped|"
    r"бпла|uav|drone.* heading|drone.* direction|дрон.* напрямку",
    re.IGNORECASE,
)

# Confirmed impact — something already hit
CONFIRMED_IMPACT = re.compile(
    r"вибух|explo|прильот|прилет|impact|влучання|влучив|hit|struck|"
    r"удар по|strike on|struck|обстріл.{0,20}міст|shell.{0,20}city|"
    r"пошкодж|damag|зруйнов|destroy|горить|on fire|burning|"
    r"пожежа після|fire after|"
    r"перехопл|intercept|збит|shoot.?down|shot down",
    re.IGNORECASE,
)

# Casualties — people are hurt or dead
CASUALTIES = re.compile(
    r"загибл|загинул|kill|dead|death|fatalit|"
    r"поранен|поранених|wound|injur|"
    r"постраждал|casualt|жертв|victim|"
    r"тіл[оа]|bod(y|ies)|"
    r"дитин|child|дітей|children|"
    r"лікарн|hospital|швидк|ambulance|"
    r"рятувальн|rescue",
    re.IGNORECASE,
)

# Infrastructure damage — affects daily life
INFRASTRUCTURE = re.compile(
    r"електр|electric|power|енерг|energy|"
    r"водопостач|water supply|відключен|shutdown|outage|"
    r"опалення|heating|газопостач|gas supply|"
    r"зв'язок|communication|інтернет|internet|"
    r"аварійн|emergency.{0,10}(power|water)|"
    r"без світла|without (power|light|electricity)|"
    r"blackout|блекаут|"
    r"графік відключ|rolling.?blackout",
    re.IGNORECASE,
)

# Large-scale attack summary — major combined attack
MASS_ATTACK = re.compile(
    r"масована|масирован|massive|large.?scale|combined|"
    r"(\d{2,})\s*(ракет|drone|missile|дрон|шахед|shahed|бпла)|"
    r"(ракет|drone|missile|дрон|шахед|shahed|бпла)\s*.*(\d{2,})|"
    r"рекордн|record|найбільш|largest|"
    r"за ніч|overnight|за добу|in 24|"
    r"комбінован|combined attack",
    re.IGNORECASE,
)

# Evacuation / shelter
EVACUATION = re.compile(
    r"евакуац|evacuat|укриття|shelter|"
    r"терміново|urgent|негайно|immediately|"
    r"не виходьте|do not go out|залишайтесь|stay (inside|home)|"
    r"небезпечн|danger",
    re.IGNORECASE,
)

# --- ANTI-SIGNALS (military/political noise) ---

# Frontline military operations — not civilian relevant
MILITARY_NOISE = re.compile(
    r"штурм.{0,20}(дії|action)|assault.{0,20}action|"
    r"бригад[аи]|brigade|батальйон|battalion|рота |company |"
    r"оперативна інформація станом|operational information as of|"
    r"напрямк.{0,5}(бойов|боїв|combat)|"
    r"ворожих? (атак|спроб|наступ)|enemy (attack|attempt|offensive)|"
    r"(відбит|repel).{0,20}(атак|assault)|"
    r"позиці[їй]|position|опорн|stronghold|"
    r"ліквідує|eliminat|знищено.{0,15}(техніки|ворог|особового)|"
    r"трофе[їй]|trophy|"
    r"волонтер|volunteer|збір|fundrais|збору|collection|"
    r"долучитися|join.{0,10}(collection|fundrais)|"
    r"підпис|subscri|"
    r"від початку доби кількість|since the beginning of the day the number",
    re.IGNORECASE,
)

# Pure diplomacy without security impact
DIPLOMACY_NOISE = re.compile(
    r"говорив із президентом|spoke with.{0,10}president|"
    r"говорив.{0,10}з.{0,10}(папою|pope)|spoke.{0,10}(pope|pontiff)|"
    r"зустріч.{0,10}(міністр|president|minister)|"
    r"meeting with|"
    r"дипломатич|diplomat|"
    r"домовилися|agreed|"
    r"переговор.{0,20}(мир|peace)|peace.{0,20}negoti|"
    r"саміт|summit|"
    r"форум|forum|конференц|conference|"
    r"сигнал.{0,20}(штат|state|країн|countr)|signal.{0,20}(state|countr)|"
    r"(ормуз|hormuz|протоки|strait)",
    re.IGNORECASE,
)

# Category detection — mirrors the frontend categories
CATEGORY_PATTERNS = [
    ("missile", re.compile(r"missile|ballistic|cruise|iskander|kalibr|kinzhal|s-300|s-400|rocket|ракет", re.I)),
    ("drone",   re.compile(r"drone|uav|shahed|lancet|mohajer|geran|fpv|дрон|шахед|бпла", re.I)),
    ("shelling",re.compile(r"shell|artiller|mlrs|grad|mortar|bomb|glide bomb|fab-|обстріл|артилер|бомб", re.I)),
    ("alert",   re.compile(r"air alert|air raid|siren|alarm|intercept|повітряна тривога|сирен|тривога", re.I)),
    ("political", re.compile(r"diplomat|sanction|negotiat|peace|nato|eu |зброя|weapon|aid package", re.I)),
]

# Ukrainian cities for location extraction (reuses frontend list)
CITY_NAMES = [
    "Kyiv", "Kharkiv", "Odesa", "Dnipro", "Zaporizhzhia", "Lviv",
    "Mykolaiv", "Kherson", "Sumy", "Chernihiv", "Donetsk", "Luhansk",
    "Poltava", "Kryvyi Rih", "Brovary", "Kramatorsk", "Bakhmut",
    "Avdiivka", "Pokrovsk", "Kursk", "Crimea", "Sevastopol", "Mariupol",
    "Izmail", "Kupyansk", "Vinnytsia", "Lutsk", "Zhytomyr", "Uzhhorod",
    "Ivano-Frankivsk", "Kropyvnytskyi", "Rivne", "Ternopil",
    "Khmelnytskyi", "Cherkasy", "Chernivtsi", "Energodar", "Sloviansk",
    "Nikopol", "Melitopol", "Berdiansk", "Irpin", "Bucha", "Tokmak",
    "Orikhiv", "Huliaipole",
]

# Ukrainian city names (Cyrillic) mapped to English for location extraction
CITY_NAMES_UK = {
    "Київ": "Kyiv", "Харків": "Kharkiv", "Одеса": "Odesa",
    "Дніпро": "Dnipro", "Запоріжжя": "Zaporizhzhia", "Львів": "Lviv",
    "Миколаїв": "Mykolaiv", "Херсон": "Kherson", "Суми": "Sumy",
    "Чернігів": "Chernihiv", "Донецьк": "Donetsk", "Луганськ": "Luhansk",
    "Полтава": "Poltava", "Кривий Ріг": "Kryvyi Rih",
    "Краматорськ": "Kramatorsk", "Бахмут": "Bakhmut",
    "Авдіївка": "Avdiivka", "Покровськ": "Pokrovsk",
    "Курськ": "Kursk", "Крим": "Crimea", "Севастополь": "Sevastopol",
    "Маріуполь": "Mariupol", "Ізмаїл": "Izmail",
    "Куп'янськ": "Kupyansk", "Вінниця": "Vinnytsia",
    "Мелітополь": "Melitopol", "Бердянськ": "Berdiansk",
    "Ірпінь": "Irpin", "Буча": "Bucha", "Нікополь": "Nikopol",
    "Енергодар": "Energodar", "Слов'янськ": "Sloviansk",
}

# Sort longest-first so "Kryvyi Rih" matches before "Kyiv"
CITY_NAMES.sort(key=len, reverse=True)
_CITY_UK_SORTED = sorted(CITY_NAMES_UK.keys(), key=len, reverse=True)


def extract_location(text: str) -> str:
    """Find the first city mentioned in text."""
    lower = text.lower()
    for city in CITY_NAMES:
        if city.lower() in lower:
            return city
    for uk_name in _CITY_UK_SORTED:
        if uk_name.lower() in lower:
            return CITY_NAMES_UK[uk_name]
    return "Ukraine"


def categorize(text: str) -> str:
    for cat, pat in CATEGORY_PATTERNS:
        if pat.search(text):
            return cat
    return "alert"


def assess_severity(text: str) -> str:
    """Severity from a civilian perspective: how threatened should I feel?"""
    if CASUALTIES.search(text) or (CONFIRMED_IMPACT.search(text) and MASS_ATTACK.search(text)):
        return "critical"
    if CONFIRMED_IMPACT.search(text) or INCOMING_THREAT.search(text):
        return "high"
    if INFRASTRUCTURE.search(text) or EVACUATION.search(text):
        return "high"
    if MASS_ATTACK.search(text):
        return "medium"
    return "low"


# --- RELEVANCE FILTERS ---

# Off-topic foreign affairs (unless they mention Ukraine)
OFF_TOPIC = re.compile(
    r"(?=.*(?:iran|[іи]ран|china|кита[йю]|north korea|КНДР|кндр|syria|сир[іи]|"
    r"gaza|газ[аі]|israel|[іи]зра[їи]л|india|[іи]нд[іи]|taiwan|тайван|"
    r"persian|перс|tehran|тегеран))(?!.*(?:укра[їи]н|ukraine|зсу|zsu|"
    r"ки[їі]в|kyiv|kharkiv|хар[кь]ів|зброя для|weapons? for|допомог|aid|"
    r"для україни|for ukraine))",
    re.IGNORECASE,
)


def compute_importance(msg, channel_info: dict) -> float:
    """
    Civilian threat scoring.

    The question is: "Does this message tell me something about my safety?"

    Returns -1 to reject entirely.
    Score 0-10+, only messages >= MIN_SCORE make it to the feed.
    """
    text = msg.text or ""

    # --- HARD REJECT ---

    # Off-topic foreign geopolitics
    if OFF_TOPIC.search(text):
        return -1.0

    # Spam / ads / promotions / clickbait
    if re.search(
        r"кар'єр|career|маркетинг|marketing|курс[иі]? |course |"
        r"знижк|discount|промо|promo|реклам|advert|"
        r"безкоштовн.{0,10}(марафон|вебінар|курс)|free.{0,10}(marathon|webinar|course)|"
        r"підпис[ау]тися|subscribe|"
        r"метео|meteo|solar storm|магнітн|magneti|геомагнітн|geomagnet|"
        r"гороскоп|horoscope|погода.{0,10}настр|weather.{0,10}mood|"
        r"розіграш|giveaway|конкурс.{0,10}приз|"
        r"спорт|sport|футбол|football|soccer|"
        r"рецепт|recipe|кулінар|culinar",
        text, re.I,
    ):
        return -1.0

    # Military operations / frontline analysis / fundraising
    if MILITARY_NOISE.search(text):
        return -1.0

    # Enemy loss reports — interesting but not a threat to civilians
    if re.search(
        r"(росі[йя]|russia|ворож|enemy|окупант|occupier|противник|opponent).{0,40}(втрат|loss|загибл|kill|ліквідов|elimin)|"
        r"(втрат|loss).{0,40}(росі[йя]|russia|ворог|enemy|окупант|occupier)",
        text, re.I,
    ):
        return -1.0

    # Pure diplomacy — reject entirely. If there's a real attack,
    # it will be reported by a military/news channel, not a diplomatic post.
    if DIPLOMACY_NOISE.search(text):
        return -1.0

    # Too short / no substance
    clean = re.sub(r"https?://\S+|\s+", "", text)
    if len(clean) < 20:
        return -1.0

    # --- CIVILIAN THREAT SCORING ---
    # A message MUST match at least one threat category to pass
    threat_score = 0.0

    # Priority 1: INCOMING THREAT — drones/missiles heading to a region
    if INCOMING_THREAT.search(text):
        threat_score += 5.0

    # Priority 2: CONFIRMED IMPACT — explosions, strikes on cities
    if CONFIRMED_IMPACT.search(text):
        threat_score += 4.0

    # Priority 3: CASUALTIES — people hurt or killed
    if CASUALTIES.search(text):
        threat_score += 5.0

    # Priority 4: INFRASTRUCTURE — power/water/heating down
    if INFRASTRUCTURE.search(text):
        threat_score += 3.5

    # Priority 5: MASS ATTACK — large-scale combined attacks
    if MASS_ATTACK.search(text):
        threat_score += 3.0

    # Priority 6: EVACUATION — shelter orders
    if EVACUATION.search(text):
        threat_score += 5.0

    # No civilian threat content at all → reject
    if threat_score == 0:
        return -1.0

    score = threat_score

    # --- BOOSTERS (secondary signals) ---

    # Named city = more specific = more useful to you
    location = extract_location(text)
    if location != "Ukraine":
        score += 1.0

    # High forwards = confirmed by many people, not rumour
    forwards = msg.forwards or 0
    if forwards > 200:
        score += 1.5
    elif forwards > 50:
        score += 0.5

    return score


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

_translator = GoogleTranslator(source="uk", target="en")


def _is_mostly_cyrillic(text: str) -> bool:
    """Check if text is primarily Cyrillic (Ukrainian/Russian)."""
    cyrillic = sum(1 for c in text if "\u0400" <= c <= "\u04ff")
    latin = sum(1 for c in text if "a" <= c.lower() <= "z")
    return cyrillic > latin


def clean_text(text: str) -> str:
    """Strip markdown, links, and formatting noise from Telegram text."""
    s = text
    # Remove markdown links [text](url) → text
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    # Remove bold/italic markers
    s = re.sub(r"\*{1,2}|_{1,2}|~{2}", "", s)
    # Remove leading emojis/symbols
    s = re.sub(r"^[\s⚡️🔴🟡🟢🛵🚀💥⚠️📢🇺🇦❗️🔥🌍📦📍☎️👁🛑✅❌😵‍💫]+", "", s)
    # Remove stray brackets from stripped links
    s = re.sub(r"[\[\]]", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def generate_alert_title(text: str, location: str) -> str:
    """
    Generate a short, direct alert title from message content.
    Reads like an emergency dashboard: 'Location: what is happening'
    """
    lower = text.lower()
    loc = location if location != "Ukraine" else ""

    def _t(msg: str) -> str:
        """Prefix with location if available."""
        return f"{loc}: {msg}" if loc else msg

    # --- Detect threat type and build title ---

    # Mass attack summary FIRST (e.g., "515 drones + 26 missiles")
    # Must check before individual drone/missile patterns
    drone_count = re.search(r"(\d{2,})\s*(?:бпла|uav|drone|дрон|shahed|шахед)", lower)
    missile_count = re.search(r"(\d{1,})\s*(?:ракет|missile|крилат)", lower)
    if drone_count or missile_count:
        parts = []
        if missile_count:
            parts.append(f"{missile_count.group(1)} missiles")
        if drone_count:
            parts.append(f"{drone_count.group(1)} drones")
        action = ""
        if re.search(r"збит|intercept|shot down|подавлен|suppress", lower):
            action = " intercepted"
        elif re.search(r"атак|attack|удар|strike", lower):
            action = " launched"
        title = " + ".join(parts) + action
        return _t(title)

    # Incoming drone
    if re.search(r"бпла|uav|drone|дрон", lower) and re.search(r"напрямку|direction|heading|курс|from the (north|south|east|west)", lower):
        return _t("Drone incoming")

    # Incoming missile / ballistic
    if re.search(r"балістик|ballistic", lower):
        return _t("Ballistic missile launch detected")
    if re.search(r"(крилат|cruise).{0,10}(ракет|missile)", lower) and re.search(r"напрямку|heading|direction|launch|запуск", lower):
        return _t("Cruise missile heading inbound")
    if re.search(r"ракет|missile", lower) and re.search(r"запуск|launch", lower):
        return _t("Missile launch detected")

    # Confirmed explosion / impact
    if re.search(r"вибух|explo", lower):
        return _t("Explosions reported")
    if re.search(r"прильот|прилет|impact|влучання|влучив", lower):
        detail = ""
        if re.search(r"житлов|residen|будин|building|дім|house|квартир|apartment", lower):
            detail = " on residential building"
        elif re.search(r"інфраструктур|infrastructure|об'єкт|facility", lower):
            detail = " on infrastructure"
        return _t(f"Strike confirmed{detail}")

    # Shelling / strike — build the most specific title possible
    if re.search(r"обстріл|shell|артилер|artiller", lower):
        # What weapon?
        weapon = "Shelling"
        if re.search(r"дрон|drone", lower):
            weapon = "Drone strike"
        elif re.search(r"ракет|missile", lower):
            weapon = "Missile strike"
        elif re.search(r"артилер|artiller", lower):
            weapon = "Artillery shelling"
        # What was hit?
        target = ""
        if re.search(r"цивільн|civilian|людин|person|people|мешканц|resident", lower):
            target = " near civilians"
        elif re.search(r"житлов|residen|будин|building|квартал|district|будинок|house", lower):
            target = " on residential area"
        elif re.search(r"інфраструктур|infrastructure|критичн|critical", lower):
            target = " on infrastructure"
        elif re.search(r"центр|center|downtown", lower):
            target = " on city center"
        return _t(f"{weapon}{target}")

    # Casualties
    dead = re.search(r"(\d+)\s*(?:загибл|загинул|kill|dead|жертв)", lower)
    injured = re.search(r"(\d+)\s*(?:поранен|wound|injur)", lower)
    if dead or injured:
        parts = []
        if dead:
            parts.append(f"{dead.group(1)} killed")
        if injured:
            parts.append(f"{injured.group(1)} injured")
        return _t(", ".join(parts))
    if re.search(r"загибл|загинул|kill|dead|casualt", lower):
        return _t("Casualties reported")

    # Interceptors working
    if re.search(r"перехоплювач|interceptor|перехопл|intercept|збит|shot down", lower):
        return _t("Air defense active")

    # Air alert
    if re.search(r"тривога|alert|сирен|siren", lower):
        return _t("Air raid alert")

    # Infrastructure damage
    if re.search(r"без світла|without power|blackout|блекаут|відключен|outage", lower):
        return _t("Power outage reported")
    if re.search(r"електр|power|енерг|energy", lower) and re.search(r"пошкодж|damag|удар|strike|зруйнов", lower):
        return _t("Energy infrastructure hit")

    # Evacuation
    if re.search(r"евакуац|evacuat", lower):
        return _t("Evacuation ordered")

    # Drone strike / near miss (should not reach here often — caught by shelling/impact above)
    if re.search(r"дрон|drone", lower) and re.search(r"прилет|влучи|hit|strike|удар|обстріл|shell", lower):
        target = " near civilians" if re.search(r"цивільн|civilian|людин|person|метр|meter", lower) else ""
        return _t(f"Drone strike{target}")

    # Attack — try to extract what kind
    if re.search(r"атак|attack|удар|strike", lower):
        weapon = ""
        if re.search(r"ракет|missile", lower):
            weapon = "Missile"
        elif re.search(r"дрон|drone|бпла|uav|shahed|шахед", lower):
            weapon = "Drone"
        elif re.search(r"артилер|artiller|обстріл|shell", lower):
            weapon = "Artillery"
        elif re.search(r"авіа|air|бомб|bomb|каб|glide", lower):
            weapon = "Airstrike"
        else:
            weapon = "Attack"

        target = ""
        if re.search(r"інфраструктур|infrastructure|критичн|critical", lower):
            target = " on infrastructure"
        elif re.search(r"житлов|residen|цивільн|civilian", lower):
            target = " on residential area"
        elif re.search(r"енерг|energy|електр|power", lower):
            target = " on energy grid"

        return _t(f"{weapon} attack{target}")

    # Fallback — extract a short, clean summary from the first line
    cleaned = clean_text(text.split("\n")[0])
    if len(cleaned) > 70:
        cleaned = cleaned[:70].rsplit(" ", 1)[0] + "..."
    return _t(cleaned) if cleaned else _t("Incident reported")


def clean_description(text: str, max_len: int = 400) -> str:
    """Clean up description text."""
    cleaned = clean_text(text)
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(" ", 1)[0] + "..."
    return cleaned


def translate_text(text: str) -> str:
    """Translate Ukrainian text to English. Returns original if already English."""
    if not text or not _is_mostly_cyrillic(text):
        return text
    try:
        # deep-translator has a 5000 char limit per call
        chunk = text[:4500]
        result = _translator.translate(chunk)
        time.sleep(0.3)  # rate-limit courtesy
        return result or text
    except Exception as e:
        print(f"    Translation error: {e}")
        return text


# ---------------------------------------------------------------------------
# Feed management
# ---------------------------------------------------------------------------

def load_existing_feed() -> list:
    """Load current feed from disk, filtering out expired items."""
    if not FEED_FILE.exists():
        return []
    try:
        items = json.loads(FEED_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []

    now = datetime.now(timezone.utc)
    valid = []
    for item in items:
        pub = datetime.fromisoformat(item["pubDate"])
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        expiry = EXPIRY_HOURS_CRITICAL if item.get("severity") == "critical" else EXPIRY_HOURS_DEFAULT
        if (now - pub).total_seconds() < expiry * 3600:
            valid.append(item)
    return valid


def deduplicate(items: list) -> list:
    """Remove duplicate messages by content similarity."""
    seen = set()
    unique = []
    for item in items:
        # Hash on first 60 chars of title, normalised
        key = re.sub(r"[^a-z0-9а-яіїєґ]", "", item["title"].lower())[:60]
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def save_feed(items: list):
    DATA_DIR.mkdir(exist_ok=True)
    items.sort(key=lambda x: x["pubDate"], reverse=True)
    # Enforce max items
    items = items[:MAX_FEED_ITEMS]
    FEED_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[VARTA] Saved {len(items)} items to {FEED_FILE}")


# ---------------------------------------------------------------------------
# Telegram fetching
# ---------------------------------------------------------------------------

async def fetch_channel_messages(client: TelegramClient) -> list:
    """Fetch and score messages from all configured channels."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    new_items = []

    for channel_id, channel_info in CHANNELS.items():
        try:
            count = 0
            async for msg in client.iter_messages(channel_id, limit=FETCH_LIMIT):
                if msg.date < cutoff:
                    break
                if not msg.text or len(msg.text.strip()) < 10:
                    continue

                score = compute_importance(msg, channel_info)
                if score < 0 or score < MIN_SCORE:
                    continue

                raw_text = msg.text
                location = extract_location(raw_text)

                # Translate raw text first (we need English for title generation)
                raw_desc = raw_text[:600]
                description_uk = clean_description(raw_desc)
                description_en = translate_text(description_uk)

                # Generate alert-style titles from English translation
                # (title generation works better on English text)
                title_en = generate_alert_title(description_en, location)
                title_uk = translate_text(title_en) if not _is_mostly_cyrillic(title_en) else title_en
                # Re-translate title to Ukrainian
                try:
                    _translator_reverse = GoogleTranslator(source="en", target="uk")
                    title_uk = _translator_reverse.translate(title_en) or title_en
                    time.sleep(0.2)
                except Exception:
                    title_uk = title_en

                # Use both languages for categorisation
                combined = (raw_text + " " + title_en + " " + description_en).lower()

                # Re-extract location from translated text too
                if location == "Ukraine":
                    location = extract_location(title_en + " " + description_en)

                item = {
                    "title": title_en,
                    "title_en": title_en,
                    "title_uk": title_uk,
                    "description": description_en,
                    "description_en": description_en,
                    "description_uk": description_uk,
                    "time": "",  # filled by frontend's formatDate
                    "pubDate": msg.date.isoformat(),
                    "category": categorize(combined),
                    "severity": assess_severity(combined),
                    "location": location,
                    "source": channel_info["name"],
                    "link": f"https://t.me/{channel_id.lstrip('@')}/{msg.id}",
                    "score": round(score, 1),
                    "views": msg.views or 0,
                    "forwards": msg.forwards or 0,
                }
                new_items.append(item)
                count += 1
                if count >= MAX_PER_CHANNEL:
                    break

            print(f"  [{channel_info['name']}] {count} important messages")

        except Exception as e:
            print(f"  [{channel_info['name']}] Error: {e}")

    return new_items


async def run_monitor():
    """Main monitoring loop — fetch, score, merge, save."""
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    session_str = os.environ.get("TELEGRAM_SESSION", "")

    if not api_id or not api_hash:
        print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")
        sys.exit(1)

    client = TelegramClient(StringSession(session_str), int(api_id), api_hash)
    await client.start()

    if not await client.is_user_authorized():
        print("Error: Not authorized. Run with --setup first.")
        await client.disconnect()
        sys.exit(1)

    print("[VARTA] Fetching Telegram channels...")
    new_items = await fetch_channel_messages(client)
    await client.disconnect()

    print(f"[VARTA] Got {len(new_items)} new important messages")

    # Merge with existing feed
    existing = load_existing_feed()
    combined = new_items + existing
    combined = deduplicate(combined)
    combined.sort(key=lambda x: x.get("score", 0), reverse=True)

    save_feed(combined)


async def setup_session():
    """Interactive setup — generates a StringSession for CI/CD use."""
    api_id = input("Enter your API ID (from my.telegram.org): ").strip()
    api_hash = input("Enter your API hash: ").strip()

    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.start()

    session_string = client.session.save()
    await client.disconnect()

    print("\n" + "=" * 60)
    print("SUCCESS! Save these as GitHub repository secrets:")
    print("=" * 60)
    print(f"\nTELEGRAM_API_ID = {api_id}")
    print(f"TELEGRAM_API_HASH = {api_hash}")
    print(f"TELEGRAM_SESSION = {session_string}")
    print("\n(The session string is a long base64 string — copy it entirely)")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--setup" in sys.argv:
        asyncio.run(setup_session())
    else:
        asyncio.run(run_monitor())
