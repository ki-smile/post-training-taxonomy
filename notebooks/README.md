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

## Running it

Needs `umap-learn`, `scikit-learn`, `pandas`, `numpy`, and `matplotlib`.
`random_state=42` is set, so the projection is deterministic for a given
`umap-learn` version. Figures are written to `fig/`, which the notebook
creates.

Because UMAP output is version-sensitive, pin `umap-learn` to whichever
version produced the published figures if you need to reproduce them exactly.
