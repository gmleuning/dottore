# Making Dottore: the corpus, the build and the tools

How the book is edited and built. The project README describes the book itself. The current edition
(3ed) is published as **Dottore**. Tools can be run from anywhere (they `chdir` to the project folder themselves). The project is a
git repository: commit after each round of edits.

Two kinds of folder: the finished book and what builds it are in the repository; everything preparatory
lives in `work/`, which is git-ignored and never uploaded.

```text
dottore/
├── editions/      THE PAGE, published: dottore_3ed.html with its logos beside it (dottore_logo_big.png,
│                  dottore_logo_white.svg, and dottore_logo.svg as the tab icon)
├── entries/       THE BOOK: one plain-text file per entry (H0393_the-feeling-soul.txt), glosses included. Edit here.
├── data/          what the build reads besides entries/: hegel_nodes.csv (the system's structure: numbering,
│                  names, parents), native_scripts/ (original scripts for foreign words); hegel_thesaurus.csv is
│                  built from entries/, never edit it
├── tools/         the build: build_thesaurus.py, build_rogetta.py, entries.py, convert.py, native_script.py and
│                  the page's interface source dottore_page.html
├── docs/          this file
└── work/          LOCAL ONLY (git-ignored): preparatory and superseded work
    ├── editions/  dottore_3ed.md (text edition), the frozen 2ed Hegelsaurus page and text
    ├── work/review/    proposal sheets, applied/ (every sheet already merged), raid/ (the Roget raid's tables)
    ├── sources/   outside texts the book was made from: rogets1911.txt, the outlines, roget/ tables and placements
    ├── tools/     generators and research scripts (raid, WordNet, frequency, review application)
    ├── design/    logo drafts and reference images
    ├── docs/      the Project Description
    └── archive/   superseded files and old pipelines
```

In short: you write in `entries/`; generators write into `work/review/` for you to vet; `editions/`
and `data/hegel_thesaurus.csv` are rebuilt.

## Editing the corpus

Open the entry's file in `entries/` and edit it. The format (see `tools/entries.py`):

```text
# 393 The Feeling Soul
# Spirit › 1. Subjective Spirit › I. Soul (Anthropology)
G: Die fühlende Seele
Gloss: The soul that feels itself as a whole, before it thinks.

N:
  the feeling soul; feeling, affect, affectivity, emotional life
  sensitiveness, impressibility, susceptibility
F:
  German: Gefühl, Stimmung
Phr:
  the heart has its reasons which reason knows not of [Pascal]
```

One sense-group per indented line under N, V, Adj, Adv; one language per line under F; one phrase per line under Phr.
`#` lines are comments; the two header lines are refreshed from `data/hegel_nodes.csv` whenever a tool saves the file.
`python tools/entries.py check` parses every file and reports mistakes; `python tools/entries.py tidy` rewrites them
all in canonical form.

The system's structure (names, numbering, which entry sits under which) stays in `data/hegel_nodes.csv`.

## Build

```bash
python tools/build_thesaurus.py               # entries/ -> data/hegel_thesaurus.csv
python tools/build_rogetta.py --edition 3ed   # -> editions/dottore_3ed.html (+ work/editions/dottore_3ed.md)
```

Host the `editions/` folder as it is. `dottore_3ed.html` loads its logos from beside it. There are two characters,
each with a light and a dark image: il Dottore (`dottore_logo_big.png`, the watercolour cut out of its paper, and
`dottore_lines_white.png`, its ink lines in white) and Dialectica (`dottore_logo.svg` in black, `dottore_logo_white.svg`
in white). By default light mode shows il Dottore and dark mode Dialectica; settings let the reader choose either
character for either mode, and the name beside the logo follows. The logo is a bookplate in the left margin when the
window (less any open side pane) is wide enough, and sits in the search bar when it is not. `dottore_logo.svg` is also
the tab icon. The two PNGs are made by `work/design/make_logo_cutouts.py` from the original scan. The page is published
with GitHub Pages at <https://gmleuning.github.io/dottore/editions/dottore_3ed.html>.
The page's interface is `tools/dottore_page.html`: gloss reveal on headword click,
settings panel (stored per browser), double-click Wiktionary panel with etymology, IPA and audio (Wiktionary's public
REST API, so any static host works).

Original scripts for foreign words: Sanskrit and Pali are converted from IAST by `tools/native_script.py`; the other
languages come from `data/native_scripts/<Language>.tsv` (romanization, original, optional display romanization such
as tone-marked pinyin), which can be corrected by hand.

`python tools/build_rogetta.py` without `--edition` rebuilds the old Hegelsaurus page in `work/editions/` from the current corpus, so it
would no longer be the 2ed; leave it frozen.

## Adding words in bulk

The generators live in `work/` and are not published. They write proposal sheets; you edit a sheet, apply it once, check the diff, and commit:

```bash
python work/tools/apply_review.py work/review/my_sheet.md --dry-run   # count what would change
python work/tools/apply_review.py work/review/my_sheet.md             # merge into entries/ (only changed files are rewritten)
git diff --stat
git commit -am "Add ..."
mv work/review/my_sheet.md work/review/applied/
```

Sheet format: `## Add` lines `H0123 | N: a, b | V: c | F: German: d; Latin: e | Phr: x; y` (each part becomes a new
sense-group), then `## Remove` lines `H0123 | word | reason`. Words an entry already has are skipped. Additions tables
(`.tsv` with node_id, field, target_para, words) are applied the same way. Applying a sheet a second time is not
entirely harmless: it can restore words a later sheet removed, which is why applied sheets move to `work/review/applied/`.

Generators used for the 3ed (need `pip install wn wordfreq` and `python -c "import wn; wn.download('oewn:2024')"`,
Open English WordNet 2024, CC BY 4.0):

```bash
python work/tools/raid_3ed.py          # Roget heads the 1ed raid never used -> work/review/raid/additions_3ed.tsv
python work/tools/wordnet_3ed.py       # WordNet kinds under work/tools/wordnet_seeds.tsv -> work/review/wordnet_3ed.md
python work/tools/frequency_3ed.py     # gaps among the 30,000 commonest words -> work/review/frequency_3ed.md (+ _unplaced.tsv)
python work/tools/coverage_probe.py    # domain spot-check of everyday vocabulary
```

`work/review/frequency_3ed_unplaced.tsv` lists about 10,000 common words not yet in the book, for hand placement.
`work/tools/frequency_3ed_exclude.txt` keeps names and misplacements out of the frequency generator.

Paths in `work/archive/docs_1ed/` use the old layouts.
