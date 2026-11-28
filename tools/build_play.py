"""Build the site repository's pages/ten_times_doctor.html (the play on its own page) from the play in README.md.

  python tools/build_play.py

The play is kept in one place, the end of README.md, from the line '<h1 align="center">...' to the end: a centered
title, a centered subtitle (HTML, copied as it is), then one paragraph per speech, '**Name:** text', with *italics*.
Edit the README and run this to refresh the page."""
import html, os, re, sys
from sitepath import PAGES
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
readme = open(os.path.join(ROOT, 'README.md'), encoding='utf-8').read()
m = re.search(r'^<h1 align="center">(.*?)</h1>\s*\n(<p align="center">.*?</p>)\s*\n(.*)\Z', readme, re.S | re.M)
if not m: sys.exit('play not found at the end of README.md')
title, sub, body = m.group(1), m.group(2), m.group(3)

def inline(t):
    t = html.escape(t.strip(), quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)

sub = re.sub(r'^<p align="center">(.*)</p>$', r'<p class="sub">\1</p>', sub.strip())
speeches = [f'<p class="sp">{inline(p)}</p>' for p in re.split(r'\n\s*\n', body.strip()) if p.strip()]
page = open(os.path.join(ROOT, 'tools', 'play_page.html'), encoding='utf-8').read()
play = f'<h1>{html.escape(title)}</h1>\n{sub}\n' + '\n'.join(speeches)
out = os.path.join(PAGES, 'ten_times_doctor.html')
open(out, 'w', encoding='utf-8', newline='\n').write(page.replace('<!--PLAY-->', play).replace('<title>Doctor Ten-Times</title>', f'<title>{html.escape(title)}</title>'))
print(len(speeches), 'speeches ->', os.path.abspath(out))
