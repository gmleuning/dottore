"""Publish the built page, at gmleuning.github.io/dottore.html.

The builds write straight into pages/ of the site-workbench repository. This commits Dottore's files there and pushes
that repository's main branch, which rebuilds the public site (its .github/workflows/publish.yml). Build first.

  python tools/publish_site.py

Other uncommitted work in site-workbench is left as it is."""
import os, re, subprocess, sys
from sitepath import SITE, PAGES

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FILES = ['dottore.html', 'ten_times_doctor.html', 'dottore_watercolour.png', 'dottore_lines_white.png',
         'dottore_logo.svg', 'dottore_logo_white.svg']
PATHS = ['pages/' + f for f in FILES]


def git(*args, repo=SITE):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, encoding='utf-8')
    if r.returncode: sys.exit(f'git {" ".join(args)} failed:\n{r.stderr.strip()}')
    return r.stdout.strip()


def main():
    for f in FILES:
        if not os.path.isfile(os.path.join(PAGES, f)): sys.exit(f'missing: pages/{f}')
    for page in ('dottore.html', 'ten_times_doctor.html'):   # a new image or page must be added to FILES
        text = open(os.path.join(PAGES, page), encoding='utf-8').read()
        extra = set(re.findall(r'(?:src|href)="([\w-]+\.(?:png|jpg|svg|html|css|js|woff2?))"', text)) - set(FILES)
        if extra: sys.exit(f'{page} also uses {sorted(extra)}: add to FILES in {__file__}')
    if git('branch', '--show-current') != 'main': sys.exit('site-workbench is not on main')
    git('fetch', '-q', 'origin', 'main')
    behind, ahead = (int(n) for n in git('rev-list', '--left-right', '--count', 'origin/main...main').split())
    if behind: sys.exit(f'site-workbench is {behind} commit(s) behind GitHub: pull there first')
    changed = git('status', '--short', '--', *PATHS)
    if changed:
        print(changed)
        version = git('log', '-1', '--format=%h', repo=ROOT)
        git('add', '--', *PATHS)
        git('commit', '-q', '-m', f'Dottore: publish the page ({version})', '--', *PATHS)
    elif not ahead:
        print('nothing to publish: the site already has this page')
        return
    git('push', '-q', 'origin', 'main')
    print('pushed; the public site updates in a minute or two')


if __name__ == '__main__':
    main()
