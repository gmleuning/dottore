"""Where the built page lives: pages/ in the site-workbench repository, its only copy, with its images."""
import os, sys

SITE = os.environ.get('DOTTORE_SITE', r'I:\My Drive\Art Work\web site\site-workbench')
PAGES = os.path.join(SITE, 'pages')
if not os.path.isdir(PAGES): sys.exit(f'no pages/ folder in {SITE} (set DOTTORE_SITE if the site repository moved)')
