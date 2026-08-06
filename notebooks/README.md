# Analysis notebooks

| Notebook | Contents |
|---|---|
| `code_S5.ipynb` | Structural consistency analysis — Gower distance, UMAP projection, silhouette scores |
| `code_S2_13.ipynb` | Snowball saturation and seed-sensitivity simulation |

## Stored outputs are stale

`code_S5.ipynb` cell 2 carries the taxonomy dataset. Its `FSL` record was corrected
to `D3 = {Few Demo., Small Labeled}`, matching the taxonomy table.

The **source is correct**, but the **stored outputs and figures were produced before
that correction** and have not yet been regenerated. Re-running is deterministic
(`random_state=42`) and requires `umap-learn`.

After re-execution the raw Gower silhouette should read `+0.0173`.

Until the notebooks are re-run, treat `data/taxonomy.json` — not the stored
notebook outputs — as authoritative.
