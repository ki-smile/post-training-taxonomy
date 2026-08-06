# Analysis notebooks

| Notebook | Contents |
|---|---|
| `code_S5.ipynb` | Structural consistency analysis — Gower distance, UMAP projection, silhouette scores |
| `code_S2_13.ipynb` | Snowball saturation and seed-sensitivity simulation |

## Reproducibility

`code_S5.ipynb` reproduces the values reported in the paper's structural
analysis appendix:

| Metric | Reported | Notebook |
|---|---|---|
| Raw Gower silhouette | +0.0173 | +0.0173 |
| UMAP silhouette | −0.0346 | −0.0346 |

Cell 2 holds the taxonomy dataset. Its 49 records are cross-checked against
the manuscript table on every site build — currently 294 of 294 profile
cells agree.

## Exporting coordinates for the website

The site renders the projection interactively, but the coordinates have to come
from **this notebook's own run**. UMAP is not reproducible across library or
platform versions: recomputing with identical settings on a different machine
gives a visibly different embedding. Measured here — the published silhouette
is −0.0346, while umap-learn 0.5.12 / 0.5.7 / 0.5.5 elsewhere produced −0.0851,
−0.0701 and −0.0832 respectively.

**The site currently shows a recomputed embedding**, captioned as such —
it is built from the same distance matrix but a different umap-learn build,
so the layout differs from the published figure. To replace it with the
paper's own projection, run the notebook through the **"Export coordinates
for the website"** cell. It overwrites `data/umap_coords.json`, after which:

    python3 scripts/compute_derived.py
    python3 scripts/build.py

updates the scatter on `/map/` and switches its caption from "recomputed" to
the authors' own run. Set `"source": "authors"` in the exported file (or drop
the field — it defaults to `authors`). If a technique name does not match the
taxonomy the build fails rather than silently dropping a point.

## Running it

Needs `umap-learn`, `scikit-learn`, `pandas`, `numpy`, and `matplotlib`.
`random_state=42` is set, so the projection is deterministic for a given
`umap-learn` version. Figures are written to `fig/`, which the notebook
creates.

Because UMAP output is version-sensitive, pin `umap-learn` to whichever
version produced the published figures if you need to reproduce them exactly.
