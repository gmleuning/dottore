"""One-off: move German head term to G:, move tagged foreign words from N/V/Adj/Adv to F:.
Usage: python convert.py <entries_dir> [--dry]"""
import glob, os, re, sys

LANG = {
    'Ger.': 'German', 'Lat.': 'Latin', 'Gr.': 'Greek', 'Fr.': 'French', 'It.': 'Italian',
    'Sp.': 'Spanish', 'Port.': 'Portuguese', 'Occitan': 'Occitan', 'Middle English': 'Middle English',
    'Old Norse': 'Old Norse', 'Afrikaans': 'Afrikaans', 'Danish': 'Danish',
    'Heb.': 'Hebrew', 'Aram.': 'Aramaic', 'Ar.': 'Arabic', 'Persian': 'Persian', 'Turk.': 'Turkish',
    'Avestan': 'Avestan', 'Egyptian': 'Egyptian', 'Skt.': 'Sanskrit', 'Pali': 'Pali', 'Tib.': 'Tibetan',
    'Chin.': 'Chinese', 'Jap.': 'Japanese', 'Polynesian': 'Polynesian', 'Quechua': 'Quechua',
    'Iroquoian': 'Iroquoian', 'Zulu': 'Zulu', 'Nguni Bantu': 'Nguni', 'Yoruba': 'Yoruba',
    'Aboriginal Australian': 'Aboriginal Australian',
}
MULTI = {'Gr., Lat.': ('Greek', 'Latin'), 'It., Sp.': ('Italian', 'Spanish'),
         'Ar., Turk.': ('Arabic', 'Turkish'), 'Turk., from Ar. qisma': ('Turkish', None)}
OVERRIDE = {
    'H0425': 'Empfindsamkeit',
    'H1204': 'Nyāya und Vaiśeṣika (Gotama und Kaṇāda)',
    'H1270': 'Descartes',
    'H0555': 'Beobachtung des Selbstbewusstseins in seiner Reinheit und seiner Beziehung auf äußere Wirklichkeit; logische und psychologische Gesetze',
}
ORDER = ['German', 'Latin', 'Greek', 'French', 'Italian', 'Spanish', 'Portuguese', 'Occitan',
         'Middle English', 'Old Norse', 'Danish', 'Afrikaans', 'Hebrew', 'Aramaic', 'Arabic', 'Persian',
         'Turkish', 'Avestan', 'Egyptian', 'Sanskrit', 'Pali', 'Tibetan', 'Chinese', 'Japanese',
         'Polynesian', 'Iroquoian', 'Quechua', 'Zulu', 'Nguni', 'Yoruba', 'Aboriginal Australian']
TAG_RE = re.compile(r'\s*\[(' + '|'.join(re.escape(t) for t in sorted(list(LANG) + list(MULTI), key=len, reverse=True)) + r')\]')


def split_items(text):
    """Split on , and ; at bracket depth 0. Returns list of (item, sep_after)."""
    out, buf, depth = [], '', 0
    for ch in text:
        if ch == '[': depth += 1
        elif ch == ']': depth -= 1
        if ch in ',;' and depth == 0:
            out.append((buf.strip(), ch)); buf = ''
        else:
            buf += ch
    if buf.strip(): out.append((buf.strip(), ''))
    return out


def join_items(items):
    """items: list of (item, sep). Rebuild with clean separators; keep ';' where a group ended."""
    s = ''
    for i, (it, sep) in enumerate(items):
        s += it
        if i < len(items) - 1:
            s += sep + ' '
    return s


ABBR = {'i.e', 'e.g', 'etc', 'vs', 'cf', 'St', 'Mr', 'Dr', 'viz', 'ca', 'no', 'lit'}


def split_paragraphs(text):
    """Split on '. ' at bracket depth 0, unless the period ends an abbreviation or an initial."""
    out, buf, depth = [], '', 0
    for i, ch in enumerate(text):
        if ch == '[': depth += 1
        elif ch == ']': depth -= 1
        if ch == '.' and depth == 0 and i + 1 < len(text) and text[i + 1] == ' ':
            word = buf.split(' ')[-1]
            if word in ABBR or (len(word) == 1 and word.isupper()) or buf.endswith('.'):
                buf += ch; continue
            out.append(buf.strip()); buf = ''
        else:
            buf += ch
    if buf.strip(): out.append(buf.strip())
    return out


def process_paragraph(text):
    items = split_items(text)
    kept, foreign = [], []
    for it, sep in items:
        tags = TAG_RE.findall(it)
        if tags:
            clean = TAG_RE.sub('', it).strip()
            t = tags[0]
            lang, also = MULTI[t] if t in MULTI else (LANG[t], None)
            foreign.append((lang, also, clean))
            if sep == ';' and kept:
                kept[-1] = (kept[-1][0], ';')
        else:
            kept.append((it, sep))
    if kept:
        kept[-1] = (kept[-1][0], '')
    return join_items(kept), foreign


def process_field(text):
    """Return (kept_text, foreign list of (lang, also, item))."""
    text = text.strip()
    if text.endswith('.'): text = text[:-1]
    paras, foreign = [], []
    for para in split_paragraphs(text):
        kept, f = process_paragraph(para)
        if kept: paras.append(kept)
        foreign += f
    return ('. '.join(paras) + '.') if paras else '', foreign


def fmt_foreign(foreign):
    groups = {}
    for lang, also, item in foreign:
        if also: item = f'{item} [also {also}]'
        groups.setdefault(lang, [])
        if item not in groups[lang]: groups[lang].append(item)
    parts = [f'{lang}: ' + ', '.join(groups[lang]) for lang in ORDER if lang in groups]
    return '; '.join(parts) + '.' if parts else ''


def convert_file(path, dry, report):
    blocks, cur = [], None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('@'):
            cur = {'id': line[1:].strip(), 'f': {}}; blocks.append(cur); continue
        m = re.match(r'(N|V|Adj|Adv|Phr|G|F):\s*(.*)', line)
        if m and cur is not None: cur['f'][m.group(1)] = m.group(2)
    out = []
    for b in blocks:
        f = b['f']
        if 'G' in f or 'F' in f:
            raise SystemExit(f'{path}: {b["id"]} already converted')
        head, allforeign, new = '', [], {}
        for k in ['N', 'V', 'Adj', 'Adv']:
            if k not in f: continue
            kept, foreign = process_field(f[k])
            if k == 'N':
                # German head: first German item among the first four noun items
                for i, (lang, also, item) in enumerate(foreign):
                    if lang == 'German':
                        head = item; foreign.pop(i); break
            new[k] = kept
            allforeign += foreign
        if b['id'] in OVERRIDE: head = OVERRIDE[b['id']]
        if not head: report.append(('NOHEAD', b['id'], f.get('N', '')[:80]))
        head = re.sub(r'\s*\[[^\]]*\]', '', head).strip()
        if head: head = head[0].upper() + head[1:]
        out.append(f'@{b["id"]}')
        if head: out.append(f'G: {head}')
        for k in ['N', 'V', 'Adj', 'Adv']:
            if new.get(k): out.append(f'{k}: {new[k]}')
        fo = fmt_foreign(allforeign)
        if fo: out.append(f'F: {fo}')
        if f.get('Phr'): out.append(f'Phr: {f["Phr"]}')
        out.append('')
    if not dry:
        open(path, 'w', encoding='utf-8').write('\n'.join(out).replace('⁣', ','))
    return out


if __name__ == '__main__':
    d = sys.argv[1]; dry = '--dry' in sys.argv
    report = []
    for p in sorted(glob.glob(os.path.join(d, '*.txt'))):
        convert_file(p, dry, report)
    for r in report: print(*r)
    print(len(report), 'entries without a German head')
