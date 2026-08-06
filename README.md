# Post-Training Adaptation Taxonomy

A six-dimensional taxonomy of post-training adaptation techniques for machine learning models, with applications in AI governance — and a website that makes it searchable, comparable, and citable.

**→ [ki-smile.github.io/post-training-taxonomy](https://ki-smile.github.io/post-training-taxonomy/)**

Post-training adaptation covers everything done to a model *after* it is trained: retraining, fine-tuning, parameter-efficient adaptation, alignment, retrieval augmentation, model editing, unlearning, calibration, and multimodal instruction tuning. The literature is fragmented across technique families, model classes, and deployment contexts, which makes methods hard to compare and model changes hard to describe.

This taxonomy assigns every technique a **coordinate on six axes** rather than a slot in a hierarchy:

| Axis | Question | Categories |
|---|---|---|
| **D1** Mechanism | What changes? | 9 |
| **D2** Goal | Why adapt? | 19 |
| **D3** Data Requirements | What data is needed? | 21 |
| **D4** Persistence | How long does the change last? | 8 |
| **D5** Scope | How much of the model structure is modified? | 10 |
| **D6** Model Type | What model is being adapted? | 5 |

**48 techniques**, plus `Training` as a reference baseline, each with a full six-dimensional profile.

## Why coordinates instead of categories

"The model was fine-tuned" does not say whether the base weights changed (D5), whether the change is permanent or session-scoped (D4), or whether knowledge was learned parametrically or retrieved at inference (D1). Those distinctions matter for documentation, change control, and regulatory analysis — and a single label cannot carry them.

## What's here

| Path | Contents |
|---|---|
| `data/` | The taxonomy as JSON and CSV, dimension vocabularies, glossary, derived distances |
| `docs/` | The website (GitHub Pages source) |
| `scripts/` | Extraction, validation, and page generation |
| `notebooks/` | Structural analysis (Gower distance, UMAP projection) |
| `tests/` | Test suite |

## Using the data

`data/taxonomy.json` is the primary artifact. Every dimension value is an **array**, including single-valued ones — set-valued cells are the normal case:

```json
{
  "slug": "peft",
  "name": "PEFT (LoRA, adapters)",
  "d1": ["parametric-update"],
  "d2": ["task-specialization", "computational-efficiency"],
  "d5": ["partial", "modular"],
  "d6": ["dl", "fm", "llm", "mllm"]
}
```

The `slug` is the stable identifier — use it for cross-references and URLs. See `data/SCHEMA.md` for the full schema.

## Regenerating

```bash
python3 -m pytest          # test suite
python3 scripts/build.py   # regenerate all pages from data/
```

Extraction scripts read the manuscript source, which is not distributed in this repository. The published data files are committed, so the site builds without it.

## Citation

The preprint is `arXiv:XXXX.XXXXX` *(placeholder — updated when the preprint is posted)*.

```bibtex
@misc{afdideh2026taxonomy,
  title  = {A Six-Dimensional Taxonomy of Post-Training Adaptation
            Techniques with Applications in AI Governance},
  author = {Afdideh, Fardin and Seoane, Fernando and Abtahi, Farhad},
  year   = {2026},
  eprint = {XXXX.XXXXX},
  archivePrefix = {arXiv}
}
```

## Scope note

This taxonomy provides technical vocabulary for describing model changes. It does not provide legal advice and does not determine whether a given change constitutes a substantial modification, a significant change, or a reportable device change. Those determinations rest with manufacturers, regulators, and notified or auditing bodies under the applicable framework.

## Licence

Code is MIT (`LICENSE`). The taxonomy data and extracted prose are CC BY 4.0 (`LICENSE-CONTENT`).

## Authors

Fardin Afdideh, Fernando Seoane, and Farhad Abtahi — Karolinska Institutet, Stockholm.
