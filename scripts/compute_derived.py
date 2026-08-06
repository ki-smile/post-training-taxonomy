#!/usr/bin/env python3
"""Compute everything derivable from the taxonomy profiles.

All of this is computed, never authored: Gower distances, nearest profiles,
three-state separators, the silhouette the manuscript reports, and the set of
techniques that fall outside gradient-compute thresholds.

UMAP coordinates are deliberately left null. The published projection predates
the FSL correction, and recomputing it would put a figure on the site that the
paper never published. That is gated on the notebook being re-executed.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAX = ROOT / "data/taxonomy.json"
DIMS = ROOT / "data/dimensions.json"
OUT = ROOT / "data/derived.json"

DIM_KEYS = ["d1", "d2", "d3", "d4", "d5", "d6"]

# Table 3 organises D1 into four groups. Groups II and III carry the paper's
# annotation that they may fall outside compute-based threshold proxies.
NON_GRADIENT_GROUPS = ("II.", "III.")


def jaccard(a, b):
    A, B = set(a), set(b)
    return 1.0 - len(A & B) / len(A | B)


def gower(profiles):
    n = len(profiles)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = sum(jaccard(profiles[i][k], profiles[j][k]) for k in DIM_KEYS) / 6
            m[i][j] = m[j][i] = d
    return m


def separator(a, b):
    """Three states. Only `disjoint` dimensions actually separate a pair --
    some pairs have none, which containment (PEFT over Partial FT) must not
    be allowed to look like separation."""
    out = {"identical": [], "overlapping": [], "disjoint": []}
    for k in DIM_KEYS:
        A, B = set(a[k]), set(b[k])
        if A == B:
            out["identical"].append(k)
        elif A & B:
            out["overlapping"].append(k)
        else:
            out["disjoint"].append(k)
    return out


def silhouette(matrix, labels):
    """Mean silhouette over a precomputed distance matrix.

    Matches sklearn's convention: a cluster of one contributes 0.
    """
    n = len(labels)
    scores = []
    for i in range(n):
        same = [j for j in range(n) if labels[j] == labels[i] and j != i]
        if not same:
            scores.append(0.0)
            continue
        a = sum(matrix[i][j] for j in same) / len(same)
        b = None
        for lab in set(labels):
            if lab == labels[i]:
                continue
            other = [j for j in range(n) if labels[j] == lab]
            if not other:
                continue
            mean = sum(matrix[i][j] for j in other) / len(other)
            b = mean if b is None else min(b, mean)
        scores.append(0.0 if b is None or max(a, b) == 0 else (b - a) / max(a, b))
    return sum(scores) / len(scores)


def main():
    tax = json.loads(TAX.read_text())
    dims = json.loads(DIMS.read_text())
    techs = tax["techniques"]
    order = [t["slug"] for t in techs]
    index = {s: i for i, s in enumerate(order)}

    matrix = gower(techs)

    nearest = {}
    for i, t in enumerate(techs):
        ranked = sorted(
            ((matrix[i][j], order[j]) for j in range(len(order)) if j != i),
        )
        nearest[t["slug"]] = [
            {"slug": s, "distance": round(d, 4)} for d, s in ranked[:5]
        ]

    # Pairs the site states in prose. Others are computed in the browser.
    PAIRS = [
        ("training", "retraining"), ("retraining", "fullft"),
        ("fullft", "partft"), ("partft", "peft"),
        ("retraining", "cl"), ("fsl", "icl"),
        ("pe", "icl"), ("munlrn", "taskarith"), ("ke", "munlrn"),
        ("da", "ssl"), ("metalrn", "icl"), ("reft", "actsteer"),
    ]
    by_slug = {t["slug"]: t for t in techs}
    separators = {
        f"{a}|{b}": separator(by_slug[a], by_slug[b])
        for a, b in PAIRS if a in by_slug and b in by_slug
    }

    families = [t["family"] for t in techs]
    post = [i for i, t in enumerate(techs) if not t["is_reference_row"]]
    sub = [[matrix[i][j] for j in post] for i in post]

    # Techniques whose mechanism falls outside gradient-compute thresholds.
    group_of = {
        c["slug"]: (c["meta_group"] or "")
        for c in dims["d1"]["categories"]
    }
    exclusive, dual = [], []
    for t in techs:
        groups = {group_of.get(s, "") for s in t["d1"]}
        non_grad = any(g.startswith(NON_GRADIENT_GROUPS) for g in groups)
        grad = any(g.startswith("I.") and not g.startswith(("II.", "III.", "IV."))
                   for g in groups)
        if non_grad:
            (dual if grad else exclusive).append(t["slug"])

    # Coordinates come from the authors' notebook run, if it has been exported.
    coords_path = ROOT / "data" / "umap_coords.json"
    umap_payload = None
    if coords_path.exists():
        raw = json.loads(coords_path.read_text())
        # Same normalisation the extractor uses: the notebook writes
        # "SSL/CPT" where the table has "SSL / CPT".
        def norm(n):
            n = re.sub(r"\s*/\s*", "/", n)
            return re.sub(r"\s+", " ", n).strip().lower()

        pos = {}
        for name, x, y in zip(raw["technique"], raw["x"], raw["y"]):
            pos[norm(name)] = [x, y]
        points, missing = [], []
        for t in techs:
            key = norm(t["name"])
            if key in pos:
                points.append({"slug": t["slug"], "x": pos[key][0],
                               "y": pos[key][1], "family": t["family"]})
            else:
                missing.append(t["name"])
        if missing:
            raise SystemExit(
                f"umap_coords.json is missing {len(missing)} technique(s): "
                f"{missing[:3]} -- names must match the taxonomy"
            )
        umap_payload = {
            "points": points,
            "silhouette": raw.get("silhouette_umap"),
            "params": raw.get("params"),
            "versions": raw.get("versions"),
            # "authors" or "recomputed" -- drives how the figure is captioned.
            "source": raw.get("source", "authors"),
            "published_silhouette": raw.get("published_silhouette_umap"),
        }

    payload = {
        "order": order,
        "gower": [[round(v, 6) for v in row] for row in matrix],
        "nearest": nearest,
        "separators": separators,
        "silhouette": {
            "raw_gower_all": round(silhouette(matrix, families), 4),
            "raw_gower_post_training_only": round(
                silhouette(sub, [families[i] for i in post]), 4
            ),
            "note": (
                "Computed from the taxonomy profiles. The all-rows figure "
                "includes the Training reference baseline, which the paper "
                "defines as not a post-training technique."
            ),
        },
        "compute_blind_spot": {
            "total": len(exclusive) + len(dual),
            "exclusive": sorted(exclusive),
            "dual": sorted(dual),
            "basis": (
                "D1 mechanism groups II (Gradient-Free / Weight Manipulation) "
                "and III (Inference-Time / Zero-Footprint), which the paper "
                "annotates as possibly falling outside compute-based "
                "threshold proxies."
            ),
        },
        "umap": umap_payload,
        "umap_note": (
            "Coordinates exported from the notebook run that produced the "
            "published figure. UMAP is not reproducible across library or "
            "platform versions, so recomputing elsewhere yields a different "
            "embedding -- these must come from the authors' own run."
            if umap_payload else
            "Not yet exported. Run the export cell in the analysis notebook; "
            "the coordinates cannot be recomputed elsewhere because UMAP "
            "differs across library and platform versions."
        ),
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"wrote {OUT.relative_to(ROOT)}  "
        f"silhouette all={payload['silhouette']['raw_gower_all']:+.4f} "
        f"post-only={payload['silhouette']['raw_gower_post_training_only']:+.4f}  "
        f"blind-spot={payload['compute_blind_spot']['total']}"
    )


if __name__ == "__main__":
    main()
