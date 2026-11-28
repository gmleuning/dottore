"""Build Dottore from entries/:

  python tools/build_dottore.py

In order: data/dottore.csv (build_thesaurus.py); the page, pages/dottore.html in the site repository
(sitepath.py), from the interface source tools/dottore_page.html; a text copy, work/text/dottore.md (not
published); and the play's page (build_play.py). tools/publish_site.py then puts the pages online.

Heads are shown without parentheticals, [Tetrad] tags and quotation marks, except where trimming would make two
heads identical (Logic, Nature, Spirit, Subjectivity, Phenomenology of Spirit); the source files keep the full names.

Each entry is headed "6 Reines Nichts • Pure Nothing", with its place in the Hegelian system
(the node's ancestors) as the path line below. Rows: N., V., Adj., Adv., F. (one line per language), Phr.
Cross-references "&c (becoming) H0007" become "&c (becoming) 7", which the page links to entry 7."""
import csv, json, os, re, runpy, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # run from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert import split_paragraphs
from entries import split_depth0, CITE, SUB
import native_script
from sitepath import PAGES

ROOT = os.getcwd()
TEMPLATE = os.path.join(ROOT, 'tools', 'dottore_page.html')
OUT = os.path.join(PAGES, 'dottore.html')
MD = os.path.join(ROOT, 'work', 'text', 'dottore.md')
TAGLINE = ("*A thesaurus of English and German ordered by Hegel's system: Roget's 1911, with contemporary, colloquial and vulgar "
           "vocabulary, Open English WordNet 2024 (CC BY 4.0) and a frequency audit of everyday English.*")


def label(node):
    """Section numbers as shown: the three parts (Logic, Nature, Spirit) carry no number and the third level's
    roman numerals are capitals (I., II.), leaving the sixth level's lowercase (i., ii.)."""
    lab, depth = node['label'], int(node['depth'])
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
    """Sense-paragraphs, each ending with a period, as in Roget."""
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
        if sep: words = native_script.mark(lang.strip(), words.strip())   # original scripts
        out.append(f'[{lang.strip()}] {words.strip()}.' if sep else p.strip() + '.')
    return out


PHRASE_LANG = {'Gr.': 'Greek', 'Chin.': 'Chinese', 'Rus.': 'Russian'}


def phrases(text):
    """One line per phrase. A phrase tagged [Gr.], [Chin.] or [Rus.] gets its romanized words in the original script
    (from data/native_scripts/<Language>*.tsv), clause by clause."""
    out = []
    for ph in split_depth0(text.strip(), '; '):
        ph = ph.rstrip('.') if ph.endswith('.') and not ph.endswith('..') else ph
        m = re.match(r'^(.*?)\s*(\[(Gr|Chin|Rus)\.\].*)$', ph)
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
    runpy.run_path(os.path.join(ROOT, 'tools', 'build_thesaurus.py'))   # entries/ -> the table read below
    rows = list(csv.DictReader(open('data/dottore.csv', encoding='utf-8-sig')))
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

    entries, md = [], ['# Dottore', '', TAGLINE, '']
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
        e['d'] = d      # the gloss, revealed by clicking the headword
        hd, ht, hc = (r.get(k, '').strip() for k in ('Hegel definition', 'Hegel texts', 'Hegel citations'))
        texts = []                                        # [work, [locations]]
        for line in ht.split('\n') if ht else []:
            if line.startswith(SUB) and texts: texts[-1][1].append(line[len(SUB):].strip())
            else: texts.append([line.strip(), []])
        quotes = []                                       # [quotation, source]
        for line in hc.split('\n') if hc else []:
            if line.startswith(CITE) and quotes: quotes[-1][1] = line[len(CITE):].strip()
            else: quotes.append([line.strip(), ''])
        if hd or texts or quotes:
            e['H'] = {'d': hd, 't': texts, 'q': quotes}   # the Hegel slide
        entries.append(e)
        md += [f"## {num(nid)} {head}", '']
        if path: md += ['*' + ' › '.join(path) + '*', '']
        if d: md += [d, '']
        for tag, ss in pos:
            line = ' '.join(ss).replace(native_script.NAT, '').replace(native_script.MID, ' ').replace(native_script.END, '')
            md += [f'**{tag}** ' + line, '']
        if 'H' in e:
            md += ['**Hegel.** ' + e['H']['d'], ''] if e['H']['d'] else []
            for w, ls in e['H']['t']: md += [f'**{w}** ' + '; '.join(ls), '']
            for q, c in e['H']['q']: md += [f'> {q}' + (f' — {c}' if c else ''), '']

    html = open(TEMPLATE, encoding='utf-8').read()
    data = json.dumps(entries, ensure_ascii=False, separators=(',', ':'))
    if 'const D=/*__DATA__*/[];' not in html: sys.exit('data placeholder not found in ' + TEMPLATE)
    html = html.replace('const D=/*__DATA__*/[];', 'const D=' + data + ';')
    open(OUT, 'w', encoding='utf-8', newline='\n').write(html)
    open(MD, 'w', encoding='utf-8', newline='\n').write('\n'.join(md))
    print(f'{len(entries)} entries -> {OUT} ({os.path.getsize(OUT) // 1024} KB), {MD}')
    runpy.run_path(os.path.join(ROOT, 'tools', 'build_play.py'))


if __name__ == '__main__':
    main()
