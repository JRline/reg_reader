# Regulation Reader

A bilingual (Japanese/English) reader for Japanese financial regulation, built around
Japan's FSA capital-adequacy notification (the domestic implementation of the Basel
framework). It's designed to make genuinely difficult regulatory text easier to actually
read and cross-check — not just translate it.

## What it does

- **Bilingual, paragraph-paired translation** — switch between Japanese and English per
  article, not a side-by-side wall of text.
- **Visual cues for long Japanese sentences** — conditions, provisos, exceptions,
  enumerated lists, and parenthetical asides are color-coded and given real list
  structure, instead of running together as one dense paragraph.
- **Clickable cross-references** — citations like "前項" (the preceding paragraph) or
  "第五条第二項" (Article 5, paragraph 2) jump straight to the target, including
  references that point at a *different law entirely*.
- **Real external law content, not just links** — citations to the Banking Act, the
  Financial Instruments and Exchange Act, and several other laws/notifications are
  backed by actual text fetched from Japan's e-Gov law database and the FSA's own site,
  not placeholder summaries.
- **Honest about what it doesn't know** — an unresolved or out-of-scope citation says so
  explicitly, rather than silently failing or pretending to link somewhere.

## Quick start

```bash
python3 pipeline/serve_no_cache.py 8877
```
Then open **http://localhost:8877/app/index.html**.

(A plain `python3 -m http.server` also works, but browsers can aggressively cache the
static files during active development — `serve_no_cache.py` avoids that.)

## What's actually in it right now

Chapter 2 of the FSA's Basel capital-adequacy notification (`fsa-basel-cap-jp`) — all 27
articles — plus seven supporting feeds of real, sourced excerpts from the laws it cites:
the Banking Act, the Financial Instruments and Exchange Act (and its enforcement order),
the Consolidated Financial Statement Regulation, the Payment Services Act, and the TLAC
notification. Of the ~246 cross-references in Chapter 2, 190 resolve to an actual target;
the rest are honestly flagged as either not-yet-digitized or a citation style (item-level
前号/次号) the current data model can't address precisely — see `CLAUDE.md` for why.

## Project layout

```
app/            The reader itself — plain HTML/CSS/JS, no build step, no framework.
feeds/          The content. One folder per regulation/law, each a feed.json matching
                pipeline/schema/rule-feed.schema.json. feeds/index.json lists them all.
pipeline/       Everything that turns a source PDF into a feed: extraction, the
                chatbot-processing template, ingestion/validation, and a handful of
                deterministic post-processing passes (reference resolution, clause
                refinement) that don't need any model calls at all.
```

See **[pipeline/EXTRACTION_GUIDE.md](pipeline/EXTRACTION_GUIDE.md)** for the full,
step-by-step content pipeline, and **[CLAUDE.md](CLAUDE.md)** for the condensed
architecture/gotchas context meant for picking this project back up later.

## License

MIT — see `LICENSE`. The regulatory text itself is sourced from public Japanese
government publications (FSA, e-Gov); this project's own code and structuring of that
content is what's under the MIT license here.
