# Contributing

## Reporting a problem with the data

If a profile looks wrong, please open an issue with the technique slug and
which dimension. Profiles are machine-extracted from the manuscript and
cross-checked against the authors' analysis notebook, so a genuine error is
most likely either an extraction bug or a discrepancy between those two
sources — both worth knowing about.

## Regenerating

```bash
python3 -m pytest              # Python suite
node --test "tests/*.test.js"  # browser-module suite
python3 scripts/pipeline.py    # re-extract data/
python3 scripts/build.py       # regenerate docs/
python3 scripts/build.py --strict   # …and run the full site validation
```

Extraction reads the manuscript source, which is not distributed here. The
generated data files are committed, so the site builds without it.

**Run the pipeline, not individual extractors.** The stages share
`data/taxonomy.json`, and running a later stage on its own discards what an
earlier one merged in.

## What the validator enforces

`scripts/validate.py` runs in two stages and fails the build rather than
shipping something wrong.

Data stage: record and family counts, vocabulary closure, slug uniqueness,
the 294-cell cross-check, relation source quotes, unresolved LaTeX.

Site stage: `docs/data` parity, dead internal links, and two content rules —
no journal or review-status references anywhere in published material, and
no `triggers` / `constitutes` / `requires` / `must` inside a `.reg-claim`
block. Regulatory statements use the paper's own modal verbs, because the
taxonomy supplies vocabulary and does not determine legal consequence.

## Editing pages

Pages are generated from `scripts/pages.py` through a shared layout, so
there are no hand-written HTML files to keep in sync. Edit the renderer and
rebuild.

## Style

Python: standard library only in `scripts/`. Browser code: vanilla ES
modules, no framework, no CDN — the site makes no third-party requests.
