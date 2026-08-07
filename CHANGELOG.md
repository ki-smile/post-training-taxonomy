# Changelog

Versions describe the **taxonomy dataset**, not the website. Rewording a page
does not move the version; changing a technique's profile does, because anyone
who pinned to a version and joined against it would otherwise get different
data without noticing.

The current version and release date are in `data/taxonomy.json` under `meta`,
and shown in the site footer.

## What moves which number

| Change | Bump |
|---|---|
| A technique added or removed | **Major** |
| A dimension category added or removed | **Major** |
| A profile value changed — any cell of the 49 × 6 grid | **Major** |
| A slug renamed | **Major** |
| Technique definitions or category definitions revised | Minor |
| Editorial summaries rewritten | Minor |
| Relations added or retyped | Minor |
| Derived values recomputed from unchanged inputs | Minor |
| Typos, formatting, non-semantic corrections | Patch |

The rule behind the table: **if a consumer's code or conclusions could change,
it is major.** Profile values are the taxonomy's contract. Prose is not.

Renaming a slug is major even though it looks cosmetic, because slugs are the
identity anchor — URLs, cross-references and joins all key on them.

## Format

Entries follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed

- Citations now carry the published preprint identifier,
  [arXiv:2608.06246](https://arxiv.org/abs/2608.06246), in place of the
  placeholder. **No version bump**: the identifier is not part of
  `taxonomy.json`, so the dataset is byte-identical to 1.0.0.

---

## [1.0.0] — 2026-08-06

First release.

### Added

- **48 post-training adaptation techniques**, plus `Training` as a reference
  baseline, each with a complete six-dimensional profile.
- **Six dimension vocabularies** — D1 Mechanism (9 categories), D2 Goal (19),
  D3 Data Requirements (21), D4 Persistence (8), D5 Scope (10), D6 Model Type
  (5) — with definitions and meta-group groupings.
- **Technique definitions** extracted verbatim from the paper's appendix, with
  inline dimension references rendered as links.
- **Editorial summaries** — one plain-language sentence per technique, marked
  as site editorial rather than paper text.
- **11 typed relations** between techniques (umbrella, sub-technique, bridge,
  supersession, hybrid), each carrying a quote locatable in the source.
- **Derived values**: Gower distance matrix, five nearest profiles per
  technique, three-state pairwise separators, family silhouette scores, and
  the set of techniques falling outside gradient-compute thresholds.
- **171-entry glossary** of abbreviations.
- Machine-readable `taxonomy.json` and `taxonomy.csv`, documented in
  `data/SCHEMA.md`.

### Verification

- All **294 profile cells** (49 × 6) extracted from the manuscript and
  independently cross-checked against the authors' analysis notebook. All 294
  agree.
- Every dimension value checked against its published vocabulary.
- No profile value re-typed by hand.

### Known limitations

- The similarity projection on `/map/` is **recomputed**, not the embedding
  printed in the paper. The underlying distances are verified identical — the
  raw Gower silhouette reproduces the published +0.0173 exactly — but UMAP is
  not reproducible across library versions, so the layout differs (−0.0851
  here against −0.0346 published). Adjacency is meaningful; exact positions
  are not.
- One historical discrepancy between the two extraction sources is recorded
  and adjudicated in `data/discrepancies.json`.

---

## How to release

1. Decide the bump using the table above.
2. Update `VERSION` and `RELEASED` in `scripts/version.py` — the only place
   they are defined.
3. Move `[Unreleased]` entries into a new dated section here.
4. Update `version` and `date-released` in `CITATION.cff`.
5. Rebuild and verify:

   ```bash
   python3 scripts/pipeline.py
   python3 scripts/build.py --strict
   python3 -m pytest -q && node --test tests/*.test.js
   ```

6. Tag the release: `git tag -a v1.0.0 -m "Taxonomy v1.0.0"`

A test asserts `data/taxonomy.json` carries the same version as
`scripts/version.py`, so a forgotten rebuild fails rather than shipping a
dataset stamped with the wrong number.
