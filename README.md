# Regulation Reader

A bilingual (Japanese/English) reader for Japanese financial regulation, built around
Japan's FSA capital-adequacy notification for Ultimate Designated Parent Companies
(最終指定親会社 — the domestic implementation of the Basel framework). It's designed to
make genuinely difficult regulatory text easier to actually read and cross-check — not
just translate it.

> **Status:** the whole notification is in (see below), but every English text is a
> machine-assisted **first draft that nobody has reviewed**. Don't rely on it for compliance
> decisions; check the Japanese, which is transcribed from the source PDF.

## What it does

- **Bilingual, paragraph-paired translation** — switch between Japanese and English per
  article, not a side-by-side wall of text.
- **Visual cues for long Japanese sentences** — conditions, provisos, exceptions, defined
  terms and parenthetical asides are color-coded; numbered and イロハ list items get a side
  bar and real indentation, so nesting is visible at a glance instead of running together as
  one dense paragraph.
- **Cues inside lists and asides, too** — a condition inside a list item, or an
  exclusion (…を除く) / limitation (…に限る) / definition (…をいう) inside a
  parenthetical, gets its own colored underline without breaking the item or the paren.
- **Formulas** — calculation paragraphs show their formula where the source has it, with
  fractions drawn as fractions. Hover (or tap) any variable for what it means and where it's
  defined. The notation is a separate file, so it can be swapped for a house standard. Where a
  reading needed judgement (a blurry exponent, a likely misprint in the notice) the formula
  carries a visible note.
- **Tables** — the notification's risk-weight, bucket and correlation tables are rebuilt
  with merged cells, in both languages.
- **Clickable cross-references** — citations like "前項" (the preceding paragraph) or
  "第五条第二項" (Article 5, paragraph 2) jump straight to the target — across chapters,
  sections and the supplementary provisions, and into other laws that are in the reader.
- **Real external law content, not just links** — citations to the Banking Act, the
  Financial Instruments and Exchange Act and a few other instruments are backed by actual
  excerpts, not placeholder summaries.
- **Unofficial-translation notice and source line** — a dismissible banner (shown on first
  open, then remembered; it scrolls away with the page, it isn't sticky) and a source line
  at the bottom of every page.
- **Honest about what it doesn't know** — an unresolved or out-of-scope citation says so
  explicitly, rather than silently failing or pretending to link somewhere.
- **Works on a phone, and offline** — see [Use it on your phone](#use-it-on-your-phone).

## Quick start

Open **`site/index.html`** directly in a browser — double-click it, no Python or server
needed. `site/` is the finished, self-contained reader (HTML/CSS/JS plus every feed bundled
as a script file, which is what lets it work from `file://`).

After changing anything in `app/` or `feeds/`, regenerate it:

```bash
python3 pipeline/build_site.py     # standard library only; also validates feeds, formulas, tables
```

For live development on `app/` itself you can still serve the repo
(`python3 pipeline/serve_no_cache.py 8877`, then http://localhost:8877/app/index.html) —
same code, but it reads `feeds/*.json` directly so there's no rebuild step.

## What's actually in it right now

**The whole of the notification** (`fsa-basel-cap-jp`, 548 articles/entries, in 節/款/目
groupings):

| Part | Content |
|---|---|
| Chapter 1 | 定義 — the definitions (one article, ~120 defined terms) |
| Chapter 2 | 算式等 — the formulas for the capital ratios |
| Chapter 3 | 信用リスクの標準的手法 — standardized approach to credit risk |
| Chapter 4 | 信用リスクの内部格付手法 — internal ratings-based approach |
| Chapter 5 | 証券化エクスポージャーの取扱い — securitization |
| Chapter 5-2 | CVAリスク |
| Chapter 5-3 | 中央清算機関関連エクスポージャーの取扱い — central counterparties |
| Chapter 6 | マーケット・リスク — market risk |
| Chapter 7 | オペレーショナル・リスク — operational risk, with 別表第一 and 別表第二 as appended tables |
| 附則 | the supplementary provisions: the original ones, 18 amending notices' and 13 application clauses (改正文), one section per notice |

with the following:

- the Japanese text, and an English draft translation for every article
- 234 formulas, transcribed from the PDF's formula images, and 105 tables
- 3,175 cross-references, of which 2,393 resolve to an actual target

**Supporting feeds** — real, sourced excerpts of the laws and notices it cites most:

- the Banking Act
- the Financial Instruments and Exchange Act and its enforcement order
- the Consolidated Financial Statement Regulation
- the Payment Services Act
- the TLAC notification

**What's deliberately not resolved.** The remaining cross-references are flagged, not
guessed:

- other laws and notices that aren't in the reader yet — the list of what to fetch is
  `pipeline/EXTERNAL_INFO_REQUESTS.md`
- item-level citations (前号/次号/第N号) that the current data model can't address
  precisely (see `CLAUDE.md` for why)
- 「」-quoted replacement phrases (読替え), which name provisions rather than cite them
- citations inside the amending 附則 that point into amending notices that aren't part of
  this feed

## Use it on your phone

The built site is a static web app with a manifest, icons and an offline cache, so it can be
hosted anywhere and added to an iPhone/Android home screen:

1. **Host `site/`.** A workflow (`.github/workflows/pages.yml`) rebuilds the site and
   publishes it to **GitHub Pages** (`https://<user>.github.io/reg_reader/`) whenever
   `main` changes. One-time setup in the repo: *Settings → Pages → Source: GitHub Actions*.
   Note that a public repository means a public site.
2. **Add it to the Home Screen.** In Safari, *Share → Add to Home Screen*. It then opens
   full-screen, and after the first visit (about 7 MB) works with no connection; a new deploy
   replaces the cached copy the next time you open it online.

Without hosting, copy the `site/` folder to the phone and open `index.html` in a file-browser
app that renders HTML (the site needs no server).

## Project layout

```
site/           The built output — open site/index.html straight from disk. Generated by
                pipeline/build_site.py; don't edit by hand.
app/            The reader's source — plain HTML/CSS/JS, no framework — plus app/pwa/
                (manifest, icons, offline-cache template).
feeds/          The content. One folder per regulation/law, each a feed.json matching
                pipeline/schema/rule-feed.schema.json. feeds/index.json lists them all.
                The notification's formulas.json, notation.json and tables.json live beside
                its feed.json.
pipeline/       Everything that turns a source PDF into a feed (see below).
.github/        The GitHub Pages deploy workflow.
```

### The content pipeline in brief

The source is one PDF (`pipeline/source/saishu1.pdf`, kept in the repo). Content is built
without any model calls at run time; translations are written as plain per-article JSON files:

- **Extract** — `extract_chapter_v2.py` reads a chapter's text, tables, formula images and
  list structure from the PDF (`extract_fusoku.py` does the supplementary provisions);
  `fix_extractions.py` repairs known layout artifacts.
- **Translate and author** — `pipeline/translations/` holds the per-article English, the
  hand-checked tables and the formula transcriptions. A big chapter can be split into slices
  and translated in parallel (`AGENT_BRIEF.md`, `check_translations.py`, `crop_token.py`,
  `merge_extras.py`).
- **Build** — `build_chapter.py` turns extraction + translations into feed nodes, with
  citations found by `ja_refs.py`.
- **Post-process** (deterministic, repeatable) — `reresolve_refs.py`, `link_external_refs.py`,
  `refine_clauses.py`, `annotate_cues.py`.
- **Publish** — `build_site.py`.

See **[pipeline/EXTRACTION_GUIDE.md](pipeline/EXTRACTION_GUIDE.md)** for the step-by-step
walkthrough, **[pipeline/EXTERNAL_INFO_REQUESTS.md](pipeline/EXTERNAL_INFO_REQUESTS.md)** for
the lookups still needed from outside, and **[CLAUDE.md](CLAUDE.md)** for the condensed
architecture/gotchas context meant for picking this project back up later.

## License

MIT — see `LICENSE`. The regulatory text itself is sourced from public Japanese
government publications (FSA, e-Gov); this project's own code and structuring of that
content is what's under the MIT license here.
