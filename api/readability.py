"""
Content Readability Analyzer — Vercel Python Serverless Function
Endpoint: POST /api/readability
Body:     {"text": "..."} or {"url": "https://..."}
"""
from http.server import BaseHTTPRequestHandler
import json
import re
from collections import Counter
import urllib.request
import urllib.error

# ── Optional libs (installed via requirements.txt) ───────────────────────────
try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# ── Stop words ───────────────────────────────────────────────────────────────
STOP = {
    'a','an','the','and','or','but','in','on','at','to','for','of','with','by',
    'from','as','is','was','are','were','be','been','being','have','has','had',
    'do','does','did','will','would','could','should','may','might','shall','can',
    'it','its','this','that','these','those','i','you','he','she','we','they',
    'me','him','her','us','them','my','your','his','our','their','who','which',
    'what','when','where','why','how','all','each','both','few','more','most',
    'other','some','such','no','not','only','same','so','than','too','very',
    'just','also','then','if','about','up','out','into','through','during',
    'before','after','above','below','between','own','s','t','re','ve','ll',
    'd','m','am','pm','said','says','one','two','three','four','five','new',
    'get','got','go','goes','went','come','came','take','took','make','made',
    'know','knew','think','thought','see','saw','look','looked','use','used',
    'find','found','give','gave','tell','told','work','working','works','still',
    'back','way','even','well','long','great','good','old','right','small',
    'large','big','little','high','low','many','much','per','like','need'
}

# ── Passive voice: "be"-form + optional adverb + past participle ─────────────
_BE = r'\b(am|is|are|was|were|be|been|being)\b'
_PP_IRREG = (
    'written|spoken|known|shown|given|taken|broken|driven|grown|thrown|worn|'
    'chosen|frozen|gotten|forgotten|hidden|ridden|risen|shaken|stolen|woken|'
    'born|brought|built|bought|caught|dealt|felt|found|heard|held|kept|left|'
    'lost|made|meant|met|paid|said|sent|shot|shut|slept|sold|spent|stood|'
    'taught|thought|told|understood|won|seen|done|gone|become|begun|blown|'
    'drawn|drunk|eaten|fallen|flown|lain|rung|sung|sunk|swum|torn|beaten'
)
_PP = rf'\b({_PP_IRREG}|\w+(?:ed|en))\b'
PASSIVE_RE = re.compile(
    rf'{_BE}(?:\s+(?:not|also|already|often|never|always|usually|sometimes|just|only|now|then|here|there|well|still|also|even)\s+|\s+){_PP}',
    re.IGNORECASE
)

# ── Core NLP helpers ─────────────────────────────────────────────────────────
def split_sentences(text):
    """Heuristic sentence splitter (no NLTK needed)"""
    # Protect common abbreviations
    abbr = re.sub(
        r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|al|Fig|vol|pp|Jan|Feb|Mar|Apr|'
        r'Jun|Jul|Aug|Sep|Oct|Nov|Dec|Co|Ltd|Inc|Corp|Dept|approx|approx|avg)\.',
        r'\1<DOT>', text
    )
    # Split on sentence-ending punctuation followed by whitespace + capital
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'\(\[])', abbr)
    result = []
    for p in parts:
        p = p.replace('<DOT>', '.').strip()
        # Must have at least 4 words to be a real sentence
        if len(re.findall(r'\b\w+\b', p)) >= 4:
            result.append(p)
    return result if result else [text]

def split_paragraphs(text):
    paras = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in paras if len(p.strip()) > 30]

def tokenize(text):
    return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

def count_syllables(word):
    """Simple vowel-group syllable counter"""
    word = word.lower().strip(".,!?;:")
    if len(word) <= 3:
        return 1
    vowel_groups = len(re.findall(r'[aeiouy]+', word))
    # Silent trailing 'e'
    if word.endswith('e') and vowel_groups > 1 and not word.endswith(('ee', 'ie', 'oe', 'ue')):
        vowel_groups -= 1
    return max(1, vowel_groups)

def reading_level(score):
    if score >= 90: return "Very Easy",    "5th grade"
    if score >= 80: return "Easy",          "6th grade"
    if score >= 70: return "Fairly Easy",   "7th grade"
    if score >= 60: return "Standard",      "8–9th grade"
    if score >= 50: return "Fairly Difficult", "10–12th grade"
    if score >= 30: return "Difficult",     "College level"
    return             "Very Confusing",    "College grad+"

def score_color(score):
    if score >= 65: return "#10B981"
    if score >= 45: return "#F59E0B"
    return                  "#EF4444"


# ── Main analysis ────────────────────────────────────────────────────────────
def analyze(text):
    words      = tokenize(text)
    sentences  = split_sentences(text)
    paragraphs = split_paragraphs(text)

    wc = len(words)
    sc = max(1, len(sentences))
    pc = max(1, len(paragraphs))

    if wc < 10:
        return {"error": "Text is too short. Please provide at least a paragraph."}

    syllables = sum(count_syllables(w) for w in words)
    avg_syl   = syllables / wc
    avg_sl    = wc / sc

    # ── Readability scores ──────────────────────────────────────────────────
    if HAS_TEXTSTAT:
        fre = textstat.flesch_reading_ease(text)
        fkg = textstat.flesch_kincaid_grade(text)
        fog = textstat.gunning_fog(text)
        cli = textstat.coleman_liau_index(text)
    else:
        # Fallback: manual formulas
        fre = 206.835 - 1.015 * avg_sl - 84.6 * avg_syl
        fkg = 0.39 * avg_sl + 11.8 * avg_syl - 15.59
        fog = 0.4 * (avg_sl + (sum(1 for w in words if count_syllables(w) >= 3) / wc * 100))
        cli = 0.0588 * (wc / sc * 100 / wc) - 0.296 * (sc / wc * 100) - 15.8

    fre = round(max(0.0, min(100.0, fre)), 1)
    fkg = round(max(0.0, fkg), 1)
    fog = round(max(0.0, fog), 1)
    cli = round(max(0.0, cli), 1)

    level, grade = reading_level(fre)
    color        = score_color(fre)
    read_time    = round(wc / 200, 1)

    # ── Keyword density ─────────────────────────────────────────────────────
    filtered = [w for w in words if w not in STOP and len(w) > 2]
    freq     = Counter(filtered)
    keywords = [
        {"word": w, "count": c, "density": round(c / wc * 100, 2)}
        for w, c in freq.most_common(20)
    ]

    unique_words   = len(set(words))
    vocab_richness = round(unique_words / wc, 3)

    # ── Sentence complexity ─────────────────────────────────────────────────
    sent_lengths = [len(tokenize(s)) for s in sentences]
    short_s = sum(1 for l in sent_lengths if l < 10)
    mid_s   = sum(1 for l in sent_lengths if 10 <= l <= 20)
    long_s  = sum(1 for l in sent_lengths if l > 20)

    # ── Passive voice ────────────────────────────────────────────────────────
    passive_list = []
    for s in sentences:
        if PASSIVE_RE.search(s):
            snippet = s.strip()
            passive_list.append(snippet[:150] + ('…' if len(snippet) > 150 else ''))
    passive_pct = round(len(passive_list) / sc * 100, 1)

    # ── Issues & recommendations ─────────────────────────────────────────────
    issues = []
    if fre < 40:
        issues.append({"type": "error",
            "msg": f"Very low readability ({fre}/100). Simplify vocabulary and break up long sentences."})
    elif fre < 60:
        issues.append({"type": "warning",
            "msg": f"Below-average readability ({fre}/100). Aim for 60+ for web content."})
    else:
        issues.append({"type": "success",
            "msg": f"Good readability score ({fre}/100) — accessible to a broad audience."})

    if avg_sl > 25:
        issues.append({"type": "error",
            "msg": f"Sentences average {round(avg_sl,1)} words — too long. Target: under 20 words each."})
    elif avg_sl > 18:
        issues.append({"type": "warning",
            "msg": f"Average sentence is {round(avg_sl,1)} words. Try keeping most sentences under 20 words."})
    else:
        issues.append({"type": "success",
            "msg": f"Good average sentence length ({round(avg_sl,1)} words per sentence)."})

    if passive_pct > 20:
        issues.append({"type": "warning",
            "msg": f"High passive voice: {passive_pct}% of sentences. Rewrite in active voice for clarity."})
    elif passive_pct > 10:
        issues.append({"type": "info",
            "msg": f"Passive voice in {passive_pct}% of sentences. Under 10% is ideal for readability."})
    else:
        issues.append({"type": "success",
            "msg": f"Low passive voice usage ({passive_pct}%) — well done!"})

    if vocab_richness < 0.35:
        issues.append({"type": "info",
            "msg": "Vocabulary variety is low. Use synonyms to avoid repetitive phrasing."})
    elif vocab_richness > 0.6:
        issues.append({"type": "success",
            "msg": f"Excellent vocabulary richness ({round(vocab_richness*100)}% unique words)."})

    if long_s > sc * 0.35:
        issues.append({"type": "warning",
            "msg": f"{long_s} sentences exceed 20 words ({round(long_s/sc*100)}%). Complex sentences hurt readability."})

    return {
        "scores": {
            "flesch_reading_ease":   fre,
            "flesch_kincaid_grade":  fkg,
            "gunning_fog":           fog,
            "coleman_liau":          cli,
            "reading_level":         level,
            "grade_label":           grade,
            "level_color":           color,
            "reading_time_minutes":  read_time,
        },
        "stats": {
            "word_count":             wc,
            "sentence_count":         sc,
            "paragraph_count":        pc,
            "avg_words_per_sentence": round(avg_sl, 1),
            "avg_syllables_per_word": round(avg_syl, 2),
            "unique_words":           unique_words,
            "vocabulary_richness":    vocab_richness,
        },
        "keywords":           keywords,
        "passive_voice": {
            "count":      len(passive_list),
            "percentage": passive_pct,
            "samples":    passive_list[:8],
        },
        "sentence_complexity": {
            "short":  short_s,
            "medium": mid_s,
            "long":   long_s,
        },
        "issues": issues,
    }


# ── URL fetcher ──────────────────────────────────────────────────────────────
def fetch_url(url):
    req = urllib.request.Request(url, headers={
        'User-Agent':      'Mozilla/5.0 (compatible; ContentAnalyzer/1.0; +https://bhagya.engineer)',
        'Accept':          'text/html,application/xhtml+xml,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        raise ValueError(f"HTTP {e.code} error fetching URL")
    except urllib.error.URLError as e:
        raise ValueError(f"Could not reach URL: {e.reason}")
    except Exception as e:
        raise ValueError(f"Fetch failed: {str(e)}")

    headings = []
    if HAS_BS4:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'aside', 'noscript', 'iframe', 'form']):
            tag.decompose()
        for h in soup.find_all(['h1','h2','h3','h4','h5','h6']):
            headings.append({"level": h.name.upper(), "text": h.get_text(strip=True)[:120]})
        main_el = (
            soup.find('article') or
            soup.find('main') or
            soup.find(class_=re.compile(r'\b(post|content|article|entry|body)\b', re.I)) or
            soup.find('body')
        )
        raw = main_el.get_text(' ', strip=True) if main_el else soup.get_text(' ', strip=True)
    else:
        raw = re.sub(r'<[^>]+>', ' ', html)

    text = re.sub(r'[ \t]+', ' ', raw)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text, headings


# ── Vercel handler ───────────────────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # suppress noisy default logs

    def _cors_headers(self, code, ctype='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._cors_headers(204)

    def do_GET(self):
        body = json.dumps({"status": "ok", "message": "POST text or url to analyze"}).encode()
        self._cors_headers(200)
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw    = self.rfile.read(length)
            data   = json.loads(raw or b'{}')
        except Exception:
            self._send(400, {"error": "Invalid JSON body"})
            return

        text     = (data.get('text') or '').strip()
        url      = (data.get('url')  or '').strip()
        headings = []

        if url and not text:
            try:
                text, headings = fetch_url(url)
            except ValueError as e:
                self._send(400, {"error": str(e)})
                return

        if len(text) < 50:
            self._send(400, {"error": "Text too short. Provide at least a paragraph of content."})
            return

        # Truncate very long texts to avoid timeouts (keep first ~15 000 words)
        words_approx = text.split()
        if len(words_approx) > 15000:
            text = ' '.join(words_approx[:15000])

        result = analyze(text)
        if headings:
            result['headings'] = headings
        result['meta'] = {
            'source':     url or 'pasted_text',
            'char_count': len(text),
        }
        self._send(200, result)

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self._cors_headers(code)
        self.wfile.write(body)
