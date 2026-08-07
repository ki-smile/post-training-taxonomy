# Data schema

Five files, all UTF-8 JSON unless noted. Regenerate with `python3 scripts/pipeline.py`.

## `taxonomy.json`

The primary artifact: 49 records — 48 post-training techniques plus `Training`, a reference baseline.

```jsonc
{
  "meta": {
    "n_techniques": 48,
    "n_reference_rows": 1,
    "centerpiece_note": "…",          // the general note attached to the table
    "crosscheck": {
      "cells_compared": 294,          // 49 × 6; a smaller number means rows were skipped
      "cells_identical": 294,
      "outstanding": 0
    }
  },
  "techniques": [{
    "slug": "peft",                   // STABLE IDENTIFIER — use this
    "tech_key": "peft",               // the manuscript's own row key
    "name": "PEFT (LoRA, adapters)",
    "family": "Knowledge Transfer and Task Specialization",
    "is_reference_row": false,
    "d1": ["parametric-update"],
    "d2": ["task-specialization", "computational-efficiency"],
    "d3": ["small-labeled"],
    "d4": ["ad-hoc-permanent", "scheduled-permanent"],
    "d5": ["partial", "modular"],
    "d6": ["dl", "fm", "llm", "mllm"],
    "summary_editorial": "…",         // site editorial, NOT paper text
    "definition_verbatim": "…",       // paper text, HTML with chips and citations
    "classification_tension": "…",    // boundary-case discussion, where the paper has one
    "source_ref": "Knowledge Transfer and Task Specialization",
    "footnote_markers": ["\\S"],
    "footnotes": [{"marker": "\\S", "text": "…"}],
    "notes": []                       // extraction warnings, empty when clean
  }]
}
```

### Three things to know before using it

**Every dimension value is an array**, including single-valued ones. Set-valued cells are the normal case, not an exception — roughly half the table is set-valued. Code that assumes scalars will silently mishandle most rows.

**The `slug` is the identity anchor.** Use it for cross-references, URLs, and joins.

**Row numbers are not in this file, deliberately.** The paper's centerpiece table is typeset more than once in the combined build, so a given technique carries different row numbers depending on which copy you are reading. Any row number is display metadata tied to a particular build, never an identifier.

**Three classes of text**, kept distinct so you can tell what came from where:

| Field | Provenance |
|---|---|
| `definition_verbatim`, `classification_tension`, `footnotes` | The paper, verbatim |
| `summary_editorial` | Written for this site, labelled as such wherever it is shown |
| Anything in `derived.json` | Computed from the profiles |

## `dimensions.json`

The six vocabularies. Keyed `d1`–`d6`.

```jsonc
{
  "d1": {
    "key": "d1",
    "name": "Mechanism",
    "question": "What changes?",
    "categories": [{
      "slug": "parametric-update",     // kebab-case of the label; the identifier
      "anchor": "paramUpd",            // the manuscript's own anchor; null for D6
      "label": "Parametric Update",
      "abbr": "Param. Upd.",
      "meta_group": "I. Gradient-Based / Compute-Intensive",
      "definition": "…"
    }]
  }
}
```

Counts: D1 9 · D2 19 · D3 21 · D4 8 · D5 10 · D6 5.

`anchor` is `null` for D6 because model tiers carry no anchors in the manuscript — all 67 belong to D1–D5. D6 is built from the glossary instead.

## `derived.json`

Everything computed from the profiles. Nothing here is authored.

| Key | Contents |
|---|---|
| `order` | Technique slugs, in table order; indexes `gower` |
| `gower` | 49 × 49 distance matrix — mean per-dimension Jaccard distance |
| `nearest` | Five closest profiles per technique |
| `separators` | Three-state comparisons for named pairs (see below) |
| `silhouette` | Family cohesion, all rows and post-training-only |
| `compute_blind_spot` | Techniques outside gradient-compute thresholds |
| `umap` | Projection coordinates and their provenance — see below |

### Three-state separators

Comparing two profiles yields three lists, not two:

- **`identical`** — the value sets are equal
- **`overlapping`** — they differ but intersect
- **`disjoint`** — no shared value

Only `disjoint` dimensions separate a pair. Some pairs have none: PEFT and Partial FT overlap on D2 and D5 with nothing disjoint, because PEFT strictly *extends* Partial FT. Reporting that as "separated by D2 and D5" would misdescribe containment as difference.

### The projection, and where it came from

`umap` carries `points`, the silhouette, the library versions used, and a
`source` field that is either `"authors"` or `"recomputed"`.

That distinction matters. UMAP is not reproducible across library or platform
versions: the same distance matrix and the same seed give a visibly different
layout elsewhere. The shipped coordinates are currently `"recomputed"`, and the
published silhouette is carried alongside for comparison. Read the projection
for which techniques sit near each other, not for exact positions.

Pairwise distances are independent of the projection and are exact.

## `relations.json`

Typed relationships between techniques. Hand-curated, and each carries a quote that must appear verbatim in the extracted definition of the named `quote_in` technique — a relation whose quote cannot be located is not included.

Types: `umbrella`, `sub-technique`, `bridge`, `supersession`, `hybrid`.

## `glossary.json`

171 acronyms as `{key, short, long}`, sorted by `short`.

## `discrepancies.json`

Adjudicated differences between the two extraction sources, retained so the reasoning survives. Currently one resolved entry.

## `taxonomy.csv`

The same table flattened for spreadsheets. Set-valued cells are joined with `|`:

```csv
slug,name,family,is_reference_row,d1,d2,d3,d4,d5,d6
peft,"PEFT (LoRA, adapters)",Knowledge Transfer and Task Specialization,False,parametric-update,computational-efficiency|task-specialization,…
```

## How the data is verified

Two independent sources: the manuscript table and the authors' analysis notebook. All 294 cells are compared on every build, and the comparison count itself is asserted so a silently reduced denominator fails rather than passes. Every dimension value is checked against its published vocabulary. Nothing is re-typed by hand.

## Versioning

Regenerated from the manuscript. When the manuscript changes, values change — check `meta.crosscheck` to confirm a dataset was verified rather than partially extracted.

## Licence

CC BY 4.0. Cite the preprint: [arXiv:2608.06246](https://arxiv.org/abs/2608.06246).
