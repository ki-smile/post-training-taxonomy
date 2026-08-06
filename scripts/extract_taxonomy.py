#!/usr/bin/env python3
"""Extract the centerpiece table and cross-check it against the notebook.

The manuscript LaTeX is primary; the authors' analysis notebook is an
independent encoding of the same table and serves as a cross-check. All
49 x 6 = 294 cells are compared. A smaller denominator means rows were
silently skipped -- that is a bug, not an acceptable partial result.

Any disagreement not already adjudicated in data/discrepancies.json is fatal.
"""

import ast
import csv
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts.latexlib import (  # noqa: E402
    expand, normalize_name, parse_acronyms, parse_newcommands,
    split_set, strip_footnote_markers,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ref/latex/<config>.tex"
CENTERPIECE = ROOT / "ref/latex/<centerpiece>.tex"
NOTEBOOK = ROOT / "notebooks/code_S5.ipynb"
DIMS = ROOT / "data/dimensions.json"
OUT = ROOT / "data/taxonomy.json"
OUT_CSV = ROOT / "data/taxonomy.csv"
OUT_DISC = ROOT / "data/discrepancies.json"

DIM_KEYS = ["d1", "d2", "d3", "d4", "d5", "d6"]

# Adjudicated, resolved before this script existed. Retained so the decision
# survives outside the git-ignored spec.
SEEDED_DISCREPANCIES = [
    {
        "slug": "fsl",
        "dimension": "d3",
        "latex": ["Few Demo.", "Small Labeled"],
        "notebook": ["Few Demo."],
        "resolution": "latex",
        "status": "resolved",
        "reason": (
            "Appendix C states FSL relies on either 1-5 examples for "
            "metric-based support sets or tens of examples for gradient-based "
            "updates, so both values belong. The notebook was corrected "
            "2026-08-06 and now reproduces the manuscript's reported "
            "raw-Gower silhouette of +0.0173."
        ),
    }
]


def parse_centerpiece(defs, gls):
    """Return ordered rows: (tech_key, display_name, markers, [6 value lists])."""
    tex = CENTERPIECE.read_text()
    tex = re.sub(r"(?m)%.*", "", tex)
    # The footnote block after the table would otherwise parse as cells.
    tex = tex.split(r"\end{xltabular}")[0]

    starts = [m.start() for m in re.finditer(r"\\tech\{", tex)]
    rows, family = [], None

    for a, b in zip(starts, starts[1:] + [len(tex)]):
        chunk = tex[a:b]
        # A family header may follow this row; stop before it.
        chunk = re.split(r"\\midrule|\\multicolumn|\\bottomrule", chunk)[0]
        key = re.match(r"\\tech\{([A-Za-z]+)\}", chunk).group(1)

        # Literal ampersands inside names must not split the row.
        cells = chunk.replace(r"\&", "\x00").split("&")
        if len(cells) < 8:
            raise SystemExit(f"row {key}: expected 8 cells, got {len(cells)}")

        raw_name = expand(cells[1], defs, gls).replace("\x00", "&")
        name, markers = strip_footnote_markers(raw_name)
        name = re.sub(r"\s+", " ", name).strip()

        values = [split_set(expand(c, defs, gls)) for c in cells[2:8]]
        rows.append((key, name, markers, values))

    # Family headers sit between rows. They are the only \textit{} in the file
    # whose content opens with a roman numeral, so key on that rather than on
    # the surrounding \multicolumn -- its \cellcolor{gray!20} argument contains
    # a brace that a [^}]* pattern cannot cross.
    families = {}
    current = None
    for m in re.finditer(
        r"\\textit\{\s*([IVX]+\.\s*[^}]+)\}|\\tech\{([A-Za-z]+)\}", tex
    ):
        if m.group(1):
            current = re.sub(r"^[IVX]+\.\s*", "", m.group(1)).strip()
        else:
            families[m.group(2)] = current

    return [(k, n, mk, v, families.get(k)) for k, n, mk, v in rows]


def parse_footnotes(defs, gls, anchor_to_label):
    """Parse the block after \\end{xltabular}.

    These footnotes are content, not noise: they scope SSL to its adaptation
    role, explain why self-play skips the FM tier, redirect in-context FSL to
    ICL, and -- in the general Note -- state that flexible techniques can
    dynamically adopt Explainability as a goal. Dropping them changes meaning.

    Returns (marker -> text, general_note).
    """
    tex = re.sub(r"(?m)%.*", "", CENTERPIECE.read_text())
    if r"\end{xltabular}" not in tex:
        return {}, ""
    block = tex.split(r"\end{xltabular}")[1]

    def clean(s):
        s = expand(s, defs, gls)
        # Dimension references render as their plain label.
        s = re.sub(
            r"\\tax(?:No)?\{\d\}\{([A-Za-z]+)\}",
            lambda m: anchor_to_label.get(m.group(1), m.group(1)),
            s,
        )
        s = re.sub(r"\\cite\{[^}]*\}", "", s)
        # Row numbers are build-dependent (the centerpiece is typeset twice),
        # so drop the parenthetical rather than print a meaningless number.
        s = re.sub(r"\s*\(Row~\\ref\{tech:[A-Za-z]+\}\)", "", s)
        s = re.sub(r"Row~\\ref\{tech:[A-Za-z]+\}", "", s)
        s = re.sub(r"\\[A-Za-z]+", " ", s)
        s = re.sub(r"[{}$~\\]", " ", s)
        return re.sub(r"\s+", " ", s).strip(" ,;")

    footnotes, general = {}, ""
    for para in re.split(r"\\par", block):
        m = re.match(r"\s*\$\^\\?([A-Za-z]+|\*)\$~?(.*)", para, re.S)
        if m:
            marker = m.group(1) if m.group(1) == "*" else "\\" + m.group(1)
            footnotes[marker] = clean(m.group(2))
        elif r"\textbf{Note:}" in para:
            general = clean(para.split(r"\textbf{Note:}", 1)[1])
    return footnotes, general


def parse_notebook():
    """The authors' independent encoding: 49 eight-tuples in cell 2."""
    nb = json.loads(NOTEBOOK.read_text())
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        m = re.search(r"records = (\[.*?\n\])", src, re.S)
        if m:
            return ast.literal_eval(m.group(1))
    raise SystemExit("notebook: could not locate the records list")


def nb_set(value):
    v = value.strip()
    parts = v[1:-1].split(",") if v.startswith("{") else [v]
    return sorted({p.strip() for p in parts if p.strip()})


def main():
    config = CONFIG.read_text()
    defs = parse_newcommands(config)
    gls = parse_acronyms(config)

    dims = json.loads(DIMS.read_text())
    # Both the abbreviation and the full label may appear; accept either.
    label_to_slug = {}
    for key in DIM_KEYS:
        m = {}
        for c in dims[key]["categories"]:
            m[c["abbr"].strip().lower()] = c["slug"]
            m[c["label"].strip().lower()] = c["slug"]
        label_to_slug[key] = m

    anchor_to_label = {
        c["anchor"]: c["label"]
        for key in DIM_KEYS for c in dims[key]["categories"] if c["anchor"]
    }
    footnotes, general_note = parse_footnotes(defs, gls, anchor_to_label)

    rows = parse_centerpiece(defs, gls)
    if len(rows) != 49:
        raise SystemExit(f"expected 49 centerpiece rows, got {len(rows)}")

    records = parse_notebook()
    if len(records) != 49:
        raise SystemExit(f"expected 49 notebook records, got {len(records)}")
    by_name = {normalize_name(r[0]): r for r in records}

    adjudicated = {
        (e["slug"], e["dimension"]) for e in SEEDED_DISCREPANCIES
        if e["status"] == "resolved"
    }

    techniques = []
    compared = identical = 0
    outstanding = []

    for key, name, markers, values, family in rows:
        slug = key.lower()
        nb_row = by_name.get(normalize_name(name))
        if nb_row is None:
            raise SystemExit(
                f"{slug}: no notebook row matches name {name!r} -- "
                "normalisation failed, not a genuine alias"
            )

        record = {
            "slug": slug,
            "tech_key": key,
            "name": name,
            "family": family or "Reference Baseline",
            "is_reference_row": family is None,
            "footnote_markers": markers,
            "footnotes": [
                {"marker": mk, "text": footnotes[mk]}
                for mk in markers if mk in footnotes
            ],
            "notes": [],
        }

        # The general Note names CE and RLHF explicitly: both can adopt
        # Explainability as a goal when engineered for transparency.
        if general_note and slug in ("ce", "rlhf"):
            # Drop the abbreviations-location preamble; only the second
            # sentence -- that flexible techniques can adopt Explainability
            # as a goal -- bears on these two rows.
            text = general_note
            cut = text.find("Highly flexible techniques")
            if cut > 0:
                text = text[cut:]
            record["footnotes"].append({"marker": "Note", "text": text})

        for i, dim in enumerate(DIM_KEYS):
            latex_vals = values[i]
            slugs = []
            for label in latex_vals:
                s = label_to_slug[dim].get(label.strip().lower())
                if s is None:
                    raise SystemExit(
                        f"{slug}/{dim}: {label!r} is not in the {dim} vocabulary"
                    )
                slugs.append(s)
            record[dim] = sorted(set(slugs))

            compared += 1
            if sorted(latex_vals) == nb_set(nb_row[i + 2]):
                identical += 1
            elif (slug, dim) not in adjudicated:
                outstanding.append(
                    {"slug": slug, "dimension": dim,
                     "latex": sorted(latex_vals),
                     "notebook": nb_set(nb_row[i + 2])}
                )

        techniques.append(record)

    if compared != 294:
        raise SystemExit(f"compared {compared} cells, expected 294")
    if outstanding:
        for o in outstanding:
            print(f"  DISAGREEMENT {o['slug']}/{o['dimension']}: "
                  f"latex={o['latex']} notebook={o['notebook']}", file=sys.stderr)
        raise SystemExit(
            f"{len(outstanding)} unadjudicated LaTeX/notebook disagreement(s)"
        )

    payload = {
        "meta": {
            "n_techniques": sum(1 for t in techniques if not t["is_reference_row"]),
            "n_reference_rows": sum(1 for t in techniques if t["is_reference_row"]),
            "centerpiece_note": general_note,
            "crosscheck": {
                "cells_compared": compared,
                "cells_identical": identical,
                "outstanding": len(outstanding),
            },
        },
        "techniques": techniques,
    }

    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    OUT_DISC.write_text(
        json.dumps({"entries": SEEDED_DISCREPANCIES}, indent=2) + "\n"
    )

    with OUT_CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "name", "family", "is_reference_row"] + DIM_KEYS)
        for t in techniques:
            w.writerow(
                [t["slug"], t["name"], t["family"], t["is_reference_row"]]
                + ["|".join(t[d]) for d in DIM_KEYS]
            )

    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"{len(techniques)} rows, {identical}/{compared} cells agree")


if __name__ == "__main__":
    main()
