"""Build hegelsaurus.html and hegelsaurus_1ed.md: the Hegelsaurus in the Rogetta interface (one self-contained page).
Run from the project root after build_thesaurus.py:
  python tools/build_rogetta.py [path/to/template.html] [out.html]
Defaults: work/editions/hegelsaurus.html (rebuilt in place, see below), plus work/editions/hegelsaurus_1ed.md (text edition with the gloss definitions).
  --edition 3ed  -> editions/dottore.html (the published page) and work/editions/dottore_3ed.md (text edition, not published)
Heads are shown without parentheticals, [Tetrad] tags and quotation marks, except where trimming would make two
heads identical (Logic, Nature, Spirit, Subjectivity, Phenomenology of Spirit); the source files keep the full names.

Each entry is headed "6 Reines Nichts • Pure Nothing", with its place in the Hegelian system
(the node's ancestors) as the path line below. Rows: N., V., Adj., Adv., F. (one line per language), Phr.
Cross-references "&c (becoming) H0007" become "&c (becoming) 7", which Rogetta links to entry 7."""
import csv, json, os, re, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # run from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert import split_paragraphs
from entries import split_depth0
import native_script

ROOT = os.getcwd()
EDITION = sys.argv[sys.argv.index('--edition') + 1] if '--edition' in sys.argv else '1ed'   # e.g. --edition 3ed
ARGS = [a for i, a in enumerate(sys.argv[1:], 1) if a != '--edition' and sys.argv[i - 1] != '--edition']
# 1ed keeps refreshing its own page (as the Hegelsaurus); later editions are Dottore, built from the interface
# source tools/dottore_page.html (which loads editions/dottore_logo.svg from beside the page)
NAME = 'Hegelsaurus' if EDITION == '1ed' else 'Dottore'
TEMPLATE = ARGS[0] if len(ARGS) > 0 else os.path.join(ROOT, 'work', 'editions', 'hegelsaurus.html') if EDITION == '1ed' \
    else os.path.join(ROOT, 'tools', 'dottore_page.html')
OUT = ARGS[1] if len(ARGS) > 1 else (os.path.join(ROOT, 'work', 'editions', 'hegelsaurus.html') if EDITION == '1ed' else os.path.join(ROOT, 'editions', 'dottore.html'))
MD = os.path.join(ROOT, 'work', 'editions', 'hegelsaurus_1ed.md' if EDITION == '1ed' else f'dottore_{EDITION}.md')
TAGLINE = {'1ed': "*Roget's 1911 Thesaurus reorganized under Hegel's system. First edition.*",
           '3ed': "*A thesaurus of English and German ordered by Hegel's system. Third edition: contemporary, colloquial and vulgar "
                  "vocabulary added to Roget's 1911, Open English WordNet 2024 (CC BY 4.0) and a frequency audit of everyday English.*"}


def label(node, edition=EDITION):
    """Section numbers as shown. From the 3ed on, the three parts (Logic, Nature, Spirit) carry no number and the
    third level's roman numerals are capitals (I., II.), leaving the sixth level's lowercase (i., ii.)."""
    lab, depth = node['label'], int(node['depth'])
    if edition == '1ed': return lab
    if depth == 0: return ''
    if depth == 2: return lab.upper()
    return lab

ROWS = [('Nouns', 'N.'), ('Verbs', 'V.'), ('Adjective', 'Adj.'), ('Adverbs', 'Adv.'), ('Foreign', 'F.'), ('Phrases', 'Phr.')]
HOLD = '\x01'


def num(nid):
    return str(int(nid[1:]))


def xrefs(s):
    return re.sub(r'\bH(\d{4})\b', lambda m: str(int(m.group(1))), s)


def senses(text):
    """Sense-paragraphs, each ending with a period, as in Rogetta."""
    text = re.sub(r'&c (adj|n|v|adv)\.', lambda m: f'&c {m.group(1)}{HOLD}', text.strip())
    out = []
    for p in split_paragraphs(text):
        p = p.replace(HOLD, '.').strip()
        if p: out.append(p if p.endswith(('.', '!', '?')) else p + '.')
    return out


def foreign(text):
    """'German: a, b; Latin: c.' -> ['[German] a, b.', '[Latin] c.']"""
    parts = [p for p in re.split(r';\s*(?=[A-Z][\w ]*: )', text.strip().rstrip('.')) if p.strip()]
    out = []
    for p in parts:
        lang, sep, words = p.partition(': ')
        if sep and EDITION != '1ed': words = native_script.mark(lang.strip(), words.strip())   # original scripts
        out.append(f'[{lang.strip()}] {words.strip()}.' if sep else p.strip() + '.')
    return out


PHRASE_LANG = {'Gr.': 'Greek', 'Chin.': 'Chinese', 'Rus.': 'Russian'}


def phrases(text):
    """One line per phrase. A phrase tagged [Gr.], [Chin.] or [Rus.] gets its romanized words in the original script
    (from data/native_scripts/<Language>*.tsv), clause by clause."""
    out = []
    for ph in split_depth0(text.strip(), '; '):
        ph = ph.rstrip('.') if ph.endswith('.') and not ph.endswith('..') else ph
        m = re.match(r'^(.*?)\s*(\[(Gr|Chin|Rus)\.\].*)$', ph) if EDITION != '1ed' else None
        if m:
            lang = PHRASE_LANG[m.group(3) + '.']
            items = [x.strip() for x in m.group(1).split(', ')]
            for i in range(len(items)):
                if all(native_script.native(lang, t) for t in items[i:]):
                    ph = ', '.join(items[:i] + [native_script.mark(lang, ', '.join(items[i:]))]) + ' ' + m.group(2)
                    break
        out.append(ph)
    return out


def trim(s):
    s = s.split(';')[0]                                   # German heads sometimes carry a second clause after ';'
    s = re.sub(r'\s*[(\[][^)\]]*[)\]]', '', s).replace('"', '')
    return re.sub(r'\s+', ' ', s).strip()


def main():
    rows = list(csv.DictReader(open('data/hegel_thesaurus.csv', encoding='utf-8-sig')))
    nodes = {r['node_id']: r for r in csv.DictReader(open('data/hegel_nodes.csv', encoding='utf-8-sig'))}
    # head names: trimmed, unless trimming would make two heads identical
    seen = {}
    for r in rows: seen.setdefault((trim(r['Head (German)']), trim(r['Head'])), []).append(r['node_id'])
    clash = {n for v in seen.values() if len(v) > 1 for n in v}
    en, de = {}, {}
    for r in rows:
        n = r['node_id']
        en[n] = r['Head'] if n in clash else trim(r['Head'])
        de[n] = r['Head (German)'].split(';')[0].strip() if n in clash else trim(r['Head (German)'])
        if n in clash: de[n] = re.sub(r'\s*\(Gotama.*', '', de[n])

    def path_of(nid):
        out, p = [], nodes[nid]['parent_id']
        while p:
            out.append(f"{label(nodes[p])} {en[p]}".strip()); p = nodes[p]['parent_id']
        return out[::-1]

    entries, md = [], [f'# {NAME}', '', TAGLINE.get(EDITION, TAGLINE['1ed']), '']
    for r in rows:
        nid = r['node_id']
        path = path_of(nid)
        pos = []
        for col, tag in ROWS:
            t = r[col].strip()
            if not t: continue
            if col == 'Foreign': ss = foreign(t)
            elif col == 'Phrases': ss = phrases(t)
            else: ss = senses(t)
            ss = [xrefs(s) for s in ss]
            if ss: pos.append([tag, ss])
        head = f"{de[nid]} • {en[nid]}"
        d = r.get('Hegelian gloss', '').strip()   # the page shows the Hegelian gloss; the working Gloss stays in the entries for revision
        e = {'id': num(nid), 'h': head, 'g': '', 'o': None, 'p': path, 'pos': pos}
        e['l'], e['k'] = label(nodes[nid]), int(nodes[nid]['depth'])   # label and depth, for the map
        if EDITION != '1ed': e['d'] = d      # the gloss, revealed by clicking the headword
        hd, hq, hl = (r.get(k, '').strip() for k in ('Hegel definition', 'Hegel quotes', 'Hegel locations'))
        quotes = []
        for line in hq.split('\n') if hq else []:
            if line.startswith('— ') and quotes: quotes[-1][1] = line[2:].strip()
            else: quotes.append([line.strip(), ''])
        locs = [x.strip() for x in hl.split('\n') if x.strip()]
        if EDITION != '1ed' and (hd or quotes or locs):
            e['H'] = {'d': hd, 'q': quotes, 'l': locs}    # the Hegel slide
        entries.append(e)
        md += [f"## {num(nid)} {head}", '']
        if path: md += ['*' + ' › '.join(path) + '*', '']
        if d: md += [d, '']
        for tag, ss in pos:
            line = ' '.join(ss).replace(native_script.NAT, '').replace(native_script.MID, ' ').replace(native_script.END, '')
            md += [f'**{tag}** ' + line, '']
        if 'H' in e:
            md += ['**Hegel.** ' + e['H']['d'], ''] if e['H']['d'] else []
            for q, c in e['H']['q']: md += [f'> {q}' + (f' — {c}' if c else ''), '']
            md += ['*Where Hegel treats it:* ' + '; '.join(e['H']['l']), ''] if e['H']['l'] else []

    html = open(TEMPLATE, encoding='utf-8').read()
    data = json.dumps(entries, ensure_ascii=False, separators=(',', ':'))
    if 'const D=/*__DATA__*/[];' in html:
        # the interface source (tools/hegelsaurus_page.html): drop the data in
        html = html.replace('const D=/*__DATA__*/[];', 'const D=' + data + ';')
    elif '<title>Hegelsaurus</title>' in html:
        # Already a built Hegelsaurus page (the default): keep its interface, replace only the data array.
        m = re.search(r'^const D=\[.*\];$', html, re.M)
        if not m: sys.exit('data array not found in ' + TEMPLATE)
        html = html[:m.start()] + 'const D=' + data + ';' + html[m.end():]
    else:
        subs = [
            ("<title>Roget's Thesaurus</title>", '<title>Hegelsaurus</title>'),
            ("Roget's Thesaurus <small>1911</small>", 'Hegelsaurus <small>Roget 1911 × Hegel</small>'),
            ("document.title=\"Roget's Thesaurus\";", 'document.title="Hegelsaurus";'),
            ('— Roget`', '— Hegelsaurus`'),
            ("localStorage.setItem('roget.'", "localStorage.setItem('hegelsaurus.'"),
            ("localStorage.getItem('roget.'", "localStorage.getItem('hegelsaurus.'"),
            ("the rest follow in Roget's order.", 'the rest follow in the order of the Hegelian system.'),
            ('Type an entry number (e.g. <kbd>494</kbd>)', 'Type an entry number (e.g. <kbd>6</kbd>)'),
            ("Underlined numbers are Roget's cross-references", 'Underlined numbers are cross-references'),
            ('placeholder="Search a word, phrase, or entry number…"', 'placeholder="Search a word (English or German), phrase, or entry number…"'),
        ]
        for a, b in subs:
            n = html.count(a)
            if not n: sys.exit(f'template text not found: {a!r}')
            html = html.replace(a, b)
        if '/*__DATA__*/[]' not in html: sys.exit('data placeholder not found')
        html = html.replace('/*__DATA__*/[]', data)
    open(OUT, 'w', encoding='utf-8', newline='\n').write(html)
    open(MD, 'w', encoding='utf-8', newline='\n').write('\n'.join(md))
    print(f'{len(entries)} entries -> {OUT} ({os.path.getsize(OUT) // 1024} KB), {MD}')


if __name__ == '__main__':
    main()
