"""The corpus: one plain-text file per entry in entries/, named H0393_the-feeling-soul.txt.

    # 393 Die fühlende Seele • The Feeling Soul
    # Spirit › 1. Subjective Spirit › I. Soul
    G: Die fühlende Seele
    Gloss: The soul that feels itself as a whole, before it thinks.

    N:
      the feeling soul; feeling, affect, affectivity, emotional life
      sensitiveness, impressibility, susceptibility
    V:
      feel, sense, intuit, be moved, be touched, be stirred
    F:
      German: Gefühl, Empfindung
      Latin: sensus
    Phr:
      the heart has its reasons which reason knows not of [Pascal]

Lines starting with # are comments (the two header lines are rewritten from data/hegel_nodes.csv on every save, so
they always show the entry's current place). G, Gloss and HGloss take one line. Gloss is the working gloss the
thesaurus was built from (kept unchanged, so the word lists don't drift); HGloss is the Hegelian gloss the page shows. N, V, Adj and Adv take one indented line per
sense-group (a group's closing period is optional); F one line per language; Phr one phrase per line. Blank lines are
ignored, so groups can be spaced out freely.

The Hegel slide comes last: Def (Hegel's definition of the concept, one paragraph), Texts (where Hegel treats it: a
work's title, then its locations indented deeper, one per line), Citations (quotations, one per line, each followed by a
deeper-indented line '— source'). The Citations header is written even when there are none yet:

    Def: The feeling soul is ...
    Texts:
      The Philosophy of Mind
        §§403–410
    Citations:
      The soul is ...
        — Encyclopedia §403

Inside the tools an entry is a dict of field strings in the old one-line form ({'N': 'a, b. c, d.', 'F': 'German: x;
Latin: y.', ...}), so the merge code (raid_merge, apply_review) works on it unchanged.

  python tools/entries.py check     parse every file, report errors
  python tools/entries.py tidy      rewrite every file in canonical form (headers refreshed)"""
import csv, glob, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from convert import split_paragraphs

DIR = os.path.join(ROOT, 'entries')
FIELDS = ['G', 'Gloss', 'HGloss', 'N', 'V', 'Adj', 'Adv', 'F', 'Phr', 'Def', 'Texts', 'Citations']
SINGLE = {'G', 'Gloss', 'HGloss', 'Def'}
LINES = {'Texts', 'Citations'}   # kept line by line (joined with newlines inside the tools)
CITE = '— '    # in Citations, a line starting with this is the source of the quote above it
SUB = '· '     # inside the tools, marks a location in Texts (in the file: a line indented deeper than its work's title)
GROUPED = {'N', 'V', 'Adj', 'Adv'}
END = ('.', '!', '?')


def nodes():
    return {r['node_id']: r for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'hegel_nodes.csv'), encoding='utf-8-sig'))}


# ---------- field string <-> lines ----------
def split_depth0(text, sep):
    out, buf, depth = [], '', 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in '[(': depth += 1
        elif ch in '])': depth = max(0, depth - 1)
        if depth == 0 and text.startswith(sep, i):
            out.append(buf); buf = ''; i += len(sep); continue
        buf += ch; i += 1
    out.append(buf)
    return [x.strip() for x in out if x.strip()]


def to_lines(field, value):
    v = value.strip()
    if field in SINGLE: return [v]
    if field in LINES: return v.split('\n')
    if field in GROUPED:
        lines = split_paragraphs(v)
    elif field == 'F':
        lines = re.split(r';\s*(?=[A-Z][\w ]*: )', v)
    else:   # Phr
        lines = split_depth0(v, '; ')
    if lines and lines[-1].endswith('.') and not lines[-1].endswith('..'):
        lines[-1] = lines[-1][:-1]        # the field's closing period is implied
    if from_lines(field, lines) != v:     # cannot be split losslessly: keep the field on one line
        lines = [v[:-1] if v.endswith('.') else v]
        if from_lines(field, lines) != v: lines = [v]
    return lines


def from_lines(field, lines):
    lines = [l.strip() for l in lines if l.strip()]
    if not lines: return ''
    if field in SINGLE: return ' '.join(lines)
    if field in LINES: return '\n'.join(lines)
    if field in GROUPED:
        return ' '.join(l if l.endswith(END) else l + '.' for l in lines)
    s = '; '.join(lines)
    return s if s.endswith(END) else s + '.'


# ---------- file <-> entry ----------
def parse(text, where='?'):
    raw, cur = {}, None
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'): continue
        if line[0] in ' \t':
            if cur is None: raise ValueError(f'{where}:{n}: indented line before any field')
            item = line.strip()
            if cur == 'Texts' and len(line) - len(line.lstrip()) >= 4:
                if not raw[cur]: raise ValueError(f'{where}:{n}: a location before any work title')
                item = SUB + item
            raw[cur].append(item); continue
        m = re.match(r'(' + '|'.join(FIELDS) + r'):\s*(.*)$', line)
        if not m: raise ValueError(f'{where}:{n}: not a field: {line[:60]!r}')
        cur = m.group(1)
        if cur in raw: raise ValueError(f'{where}:{n}: field {cur} appears twice')
        raw[cur] = [m.group(2)] if m.group(2).strip() else []
    return {k: from_lines(k, v) for k, v in raw.items() if from_lines(k, v)}


def label(node):
    lab, depth = node['label'], int(node['depth'])
    return '' if depth == 0 else lab.upper() if depth == 2 else lab


def header(nid, N):
    path, p = [], N[nid]['parent_id']
    while p:
        path.append(f"{label(N[p])} {N[p]['name']}".strip()); p = N[p]['parent_id']
    return [f"# {int(nid[1:])} {N[nid]['name']}", '# ' + (' › '.join(path[::-1]) or '(top of the system)')]


def render(nid, entry, N):
    out = header(nid, N)
    for k in ('G', 'Gloss', 'HGloss'):
        if entry.get(k): out.append(f'{k}: {entry[k]}')
    for k in ('N', 'V', 'Adj', 'Adv', 'F', 'Phr'):
        if entry.get(k):
            out.append('')
            out.append(f'{k}:')
            out += ['  ' + l for l in to_lines(k, entry[k])]
    if any(entry.get(k) for k in ('Def', 'Texts', 'Citations')):
        out += ['', '# ---- Hegel ----']
        if entry.get('Def'):
            out.append('Def: ' + entry['Def'])
        if entry.get('Texts'):
            out.append('Texts:')
            out += ['    ' + l[len(SUB):] if l.startswith(SUB) else '  ' + l for l in to_lines('Texts', entry['Texts'])]
        out.append('Citations:')
        if entry.get('Citations'):
            out += [('    ' if l.startswith(CITE) else '  ') + l for l in to_lines('Citations', entry['Citations'])]
    return '\n'.join(out) + '\n'


def slug(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', s)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:48].rstrip('-') or 'entry'


def path_for(nid, N, existing=None):
    if existing and nid in existing: return existing[nid]
    return os.path.join(DIR, f"{nid}_{slug(N[nid]['name'])}.txt")


def files():
    """node_id -> path of its file"""
    out = {}
    for p in glob.glob(os.path.join(DIR, 'H*.txt')):
        nid = os.path.basename(p)[:5]
        if nid in out: raise SystemExit(f'two files for {nid}: {out[nid]} and {p}')
        out[nid] = p
    return out


def load():
    """node_id -> entry dict of field strings"""
    N, out = nodes(), {}
    for nid, p in sorted(files().items()):
        if nid not in N: raise SystemExit(f'{p}: unknown node {nid}')
        out[nid] = parse(open(p, encoding='utf-8').read(), p)
    return out


def save(entries, only=None):
    """Write entries (all, or the node ids in `only`) back to their files. Returns the number of files changed."""
    N, have, changed = nodes(), files(), 0
    os.makedirs(DIR, exist_ok=True)
    for nid in sorted(only if only is not None else entries):
        p = path_for(nid, N, have)
        text = render(nid, entries[nid], N)
        old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
        if text != old:
            with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(text)
            changed += 1
    return changed


def check(entries=None):
    """Every entry must survive render -> parse unchanged."""
    N = nodes()
    entries = entries if entries is not None else load()
    bad = [nid for nid, e in entries.items() if parse(render(nid, e, N)) != {k: v for k, v in e.items() if v}]
    return bad


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    E = load()
    if cmd == 'check':
        bad = check(E)
        print(f'{len(E)} entries parsed; {len(bad)} do not round-trip: {bad[:20]}')
    elif cmd == 'tidy':
        print(f'{save(E)} files rewritten')
