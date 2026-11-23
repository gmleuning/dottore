"""Build data/hegel_thesaurus.csv from the corpus: one file per entry in entries/ (format in tools/entries.py).
The system's structure (names, numbering, parents) comes from data/hegel_nodes.csv; everything else from the entries.
Run from anywhere:  python tools/build_thesaurus.py"""
import csv, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import entries

KEYS = {'G': 'Head (German)', 'Gloss': 'Gloss', 'HGloss': 'Hegelian gloss', 'F': 'Foreign', 'N': 'Nouns', 'V': 'Verbs', 'Adj': 'Adjective',
        'Adv': 'Adverbs', 'Phr': 'Phrases',
        'Def': 'Hegel definition', 'Q': 'Hegel quotes', 'Loc': 'Hegel locations'}
FIELDS = ['node_id', 'Head', 'Head (German)', 'Path', 'Gloss', 'Hegelian gloss', 'Nouns', 'Verbs', 'Adjective', 'Adverbs', 'Foreign', 'Phrases',
          'Hegel definition', 'Hegel quotes', 'Hegel locations']

nodes = entries.nodes()
E = entries.load()
missing = sorted(set(nodes) - set(E))
bad_refs = sorted({(nid, ref) for nid, e in E.items() for v in e.values() for ref in re.findall(r'H\d{4}', v) if ref not in nodes})

with open(os.path.join(HERE, '..', 'data', 'hegel_thesaurus.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    for nid in sorted(E):
        w.writerow({'node_id': nid, 'Head': nodes[nid]['name'], 'Path': nodes[nid]['path'],
                    **{KEYS[k]: v for k, v in E[nid].items()}})

print(f'{len(E)} of {len(nodes)} nodes have entries' + (f'; no file for {missing[:10]}' if missing else ''))
if bad_refs:
    print('bad cross-references:', bad_refs)
