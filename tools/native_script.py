"""Original-script forms for romanized foreign words (the F. rows), used by build_rogetta.py.
- Sanskrit and Pali: IAST converted to Devanagari by rule.
- Other languages: data/native_scripts/<Language>.tsv, lines "roman<TAB>native[<TAB>display]". 'display' optionally
  replaces the romanization shown (e.g. pinyin with tone marks); leave it out to keep the book's romanization.
In the built page a word with an original becomes \\uE000native\\uE001romanization\\uE002, and the page's settings
choose which half to show per language."""
import glob, os, re

NAT, MID, END = '', '', ''

# ---------- IAST -> Devanagari ----------
V_IND = {'a': 'अ', 'ā': 'आ', 'i': 'इ', 'ī': 'ई', 'u': 'उ', 'ū': 'ऊ', 'ṛ': 'ऋ', 'ṝ': 'ॠ', 'ḷ': 'ऌ',
         'e': 'ए', 'ai': 'ऐ', 'o': 'ओ', 'au': 'औ'}
V_SIGN = {'a': '', 'ā': 'ा', 'i': 'ि', 'ī': 'ी', 'u': 'ु', 'ū': 'ू', 'ṛ': 'ृ', 'ṝ': 'ॄ', 'ḷ': 'ॢ',
          'e': 'े', 'ai': 'ै', 'o': 'ो', 'au': 'ौ'}
CONS = {'kh': 'ख', 'gh': 'घ', 'ch': 'छ', 'jh': 'झ', 'ṭh': 'ठ', 'ḍh': 'ढ', 'th': 'थ', 'dh': 'ध', 'ph': 'फ', 'bh': 'भ',
        'k': 'क', 'g': 'ग', 'ṅ': 'ङ', 'c': 'च', 'j': 'ज', 'ñ': 'ञ', 'ṭ': 'ट', 'ḍ': 'ड', 'ṇ': 'ण',
        't': 'त', 'd': 'द', 'n': 'न', 'p': 'प', 'b': 'ब', 'm': 'म', 'y': 'य', 'r': 'र', 'l': 'ल', 'ḻ': 'ळ', 'v': 'व',
        'ś': 'श', 'ṣ': 'ष', 's': 'स', 'h': 'ह'}
MARKS = {'ṃ': 'ं', 'ṁ': 'ं', 'ḥ': 'ः', "'": 'ऽ'}
VOWELS = sorted(V_IND, key=len, reverse=True)
CONSONANTS = sorted(CONS, key=len, reverse=True)
ENGLISH = {'and', 'of', 'the', 'or'}


def iast_word(w):
    w = w.lower()
    out, i, prev_cons = [], 0, False
    while i < len(w):
        for c in CONSONANTS:
            if w.startswith(c, i):
                if prev_cons: out.append('्')
                out.append(CONS[c]); i += len(c); prev_cons = True; break
        else:
            for v in VOWELS:
                if w.startswith(v, i):
                    out.append(V_SIGN[v] if prev_cons else V_IND[v]); i += len(v); prev_cons = False; break
            else:
                ch = w[i]
                if ch in MARKS:
                    out.append(MARKS[ch]); i += 1; prev_cons = False; continue
                return None   # not IAST
    if prev_cons: out.append('्')
    return ''.join(out)


def iast(text):
    words = re.split(r'([ \-/])', text)
    out = []
    for w in words:
        if w in (' ', '-', '/'): out.append(w); continue
        if w.lower() in ENGLISH: out.append(w); continue      # "rāga and dveṣa" -> "राग and द्वेष"
        d = iast_word(w)
        if d is None: return None
        out.append(d)
    return ''.join(out).replace('-', '')


# ---------- tables ----------
TABLE = {}
for p in glob.glob(os.path.join('data', 'native_scripts', '*.tsv')):   # Chinese.tsv: roman<TAB>native[<TAB>display]
    lang = os.path.basename(p).split('.')[0]          # Arabic.2.tsv continues Arabic.tsv
    for line in open(p, encoding='utf-8'):
        f = line.rstrip('\n').split('\t')
        if len(f) >= 2 and f[1] and not line.startswith('#'):
            TABLE[(lang, f[0])] = (f[1], f[2] if len(f) > 2 and f[2] else f[0])


def native(lang, roman):
    if (lang, roman) in TABLE: return TABLE[(lang, roman)]
    if lang in ('Sanskrit', 'Pali'):
        d = iast(roman)
        if d: return d, roman
    return None


def mark(lang, words):
    """'mingjia [School of Names], xing' -> each item with a known original wrapped in the markers."""
    out = []
    for item in re.split(r',\s*(?![^\[]*\])', words):
        m = re.match(r'^(.*?)(\s*\[.*)?$', item)
        core, rest = m.group(1).strip(), m.group(2) or ''
        n = native(lang, core) if core else None
        out.append(f'{NAT}{n[0]}{MID}{n[1]}{END}{rest}' if n else item)
    return ', '.join(out)


def plain(lang, words):
    """For the Markdown edition: 'mingjia' -> '名家 míngjiā'."""
    return mark(lang, words).replace(NAT, '').replace(MID, ' ').replace(END, '')
