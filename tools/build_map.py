"""Write the map as Markdown: the whole system as a nested list, each entry with its name, gloss and location in the books.
Run from the project root:  python tools/build_map.py
Output: work/text/dottore_map.md (text, not published). Follows the map on the page (tools/dottore_page.html, #map):
the same tree (data/hegel_nodes.csv), the same names and section numbers (build_dottore.py), and the Hegelian gloss.
"""
import csv, os, re, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))   # run from the project root
from entries import SUB   # a line starting with this is a location under the work above it in Hegel texts
OUT = os.path.join('work', 'text', 'dottore_map.md')


def label(node):
    """Section number as on the page (build_dottore.label)."""
    lab, depth = node['label'], int(node['depth'])
    if depth == 0: return ''
    if depth == 2: return lab.upper()
    return lab


def hegel_texts(raw):
    """'Work\\n· location\\n· location\\nWork2' -> [[work, [locations]], ...] (as build_dottore.py reads them)."""
    out = []
    for line in raw.split('\n') if raw else []:
        if not line.strip(): continue
        if line.startswith(SUB) and out: out[-1][1].append(line[len(SUB):].strip())
        else: out.append([line.strip(), []])
    return out


def trim(s):
    """Head without parentheticals, [Tetrad] tags or quotation marks (build_dottore.trim)."""
    s = s.split(';')[0]
    s = re.sub(r'\s*[(\[][^)\]]*[)\]]', '', s).replace('"', '')
    return re.sub(r'\s+', ' ', s).strip()


def main():
    rows = list(csv.DictReader(open('data/dottore.csv', encoding='utf-8-sig')))
    nodes = {r['node_id']: r for r in csv.DictReader(open('data/hegel_nodes.csv', encoding='utf-8-sig'))}

    # head names as on the page: trimmed, unless trimming would make two heads identical
    seen = {}
    for r in rows: seen.setdefault((trim(r['Head (German)']), trim(r['Head'])), []).append(r['node_id'])
    clash = {n for v in seen.values() if len(v) > 1 for n in v}
    en, de, gloss, texts = {}, {}, {}, {}
    for r in rows:
        n = r['node_id']
        en[n] = r['Head'] if n in clash else trim(r['Head'])
        de[n] = r['Head (German)'].split(';')[0].strip() if n in clash else trim(r['Head (German)'])
        if n in clash: de[n] = re.sub(r'\s*\(Gotama.*', '', de[n])
        gloss[n] = r['Hegelian gloss'].strip()
        texts[n] = hegel_texts(r['Hegel texts'])

    kids = {}
    for nid, nd in nodes.items(): kids.setdefault(nd['parent_id'], []).append(nid)

    md = ['# Dottore: the map', '',
          f'The whole system as a tree, {len(nodes)} entries. Each entry gives its section number, its name '
          '(German and English), its gloss and its location in the books (the Hegel texts that place it). '
          'Nesting follows the system.', '']

    def walk(nid, level):
        ind, cont = '  ' * level, '  ' * (level + 1)   # a list item's text lines up two spaces in from its marker
        lab = label(nodes[nid])
        head = f"**{lab + ' ' if lab else ''}{en[nid]}** · *{de[nid]}* · entry {int(nid[1:])}"
        md.append(f'{ind}- {head}')
        md.append('')
        if gloss[nid]: md.extend([f'{cont}{gloss[nid]}', ''])
        for i, (work, locs) in enumerate(texts[nid]):
            pre = '*Location in the books:* ' if i == 0 else ''
            where = ': ' + '; '.join(locs) if locs else ''
            md.extend([f'{cont}{pre}**{work}**{where}', ''])
        for k in kids.get(nid, []): walk(k, level + 1)

    for top in kids.get('', []): walk(top, 0)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md).rstrip() + '\n')
    print(f'{len(nodes)} entries -> {OUT}')


if __name__ == '__main__':
    main()
