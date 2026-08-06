#!/usr/bin/env python3
"""Extract the D1-D6 category vocabularies from the manuscript.

D1-D5 come from paired macros in the config file:

    \\newcommand{\\task}{Task Specialization}                    <- long label
    \\newcommand{\\taskAbbr}{\\hyperlink{dim:task}{Task Spec.}}   <- short + anchor

Each category therefore carries three identifiers:

    anchor  'task'                 verbatim from the manuscript; prose chips
                                   (\\tax{n}{key}) key on this
    slug    'task-specialization'  kebab of the label; the site's identifier
    abbr    'Task Spec.'           for chips and table cells

D6 is built differently. Model tiers carry NO dim: anchors -- all 67 belong to
D1-D5 -- so the five tiers come from the glossary instead.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts.latexlib import (  # noqa: E402
    expand, kebab, parse_acronyms, parse_newcommands,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ref/latex/<config>.tex"
MAIN = ROOT / "ref/latex/<main>.tex"
OUT = ROOT / "data/dimensions.json"

# Per-dimension name and question. Hardcoded from Table 2 -- no macro carries
# them, and inventing a parse for prose would be less reliable than this.
DIMS = {
    "d1": ("Mechanism", "What changes?"),
    "d2": ("Goal", "Why adapt?"),
    "d3": ("Data Requirements", "What data is needed?"),
    "d4": ("Persistence", "How long does the change last?"),
    "d5": ("Scope", "How much of the model structure is modified?"),
    "d6": ("Model Type", "What model is being adapted?"),
}

# Which table label delimits each dimension's category table, in document order.
TABLE_LABELS = [
    ("d1", "tab:D1"),
    ("d2", "tab:D2"),
    ("d3", "tab:D3"),
    ("d4", "tab:d4_persistence"),
    ("d5", "tab:d5_scope"),
]

D6_KEYS = ["ml", "dl", "fm", "llm", "mllm"]


def anchor_regions(main_tex):
    """Map dim key -> ordered list of (anchor, meta_group) for D1-D5.

    Each table runs from its \\label to the next table's \\label; the last runs
    to the \\end{table} that follows it. Group headers are \\multicolumn rows
    carrying a bold roman numeral, and apply to every anchor beneath them.
    """
    lines = main_tex.splitlines()
    starts = {}
    for i, line in enumerate(lines):
        for key, label in TABLE_LABELS:
            if f"\\label{{{label}}}" in line:
                starts[key] = i

    ordered = [k for k, _ in TABLE_LABELS if k in starts]
    bounds = {}
    for idx, key in enumerate(ordered):
        begin = starts[key]
        if idx + 1 < len(ordered):
            end = starts[ordered[idx + 1]]
        else:
            end = next(
                (j for j in range(begin, len(lines))
                 if "\\end{table}" in lines[j]),
                len(lines),
            )
        bounds[key] = (begin, end)

    out = {}
    for key, (begin, end) in bounds.items():
        found, group = [], None
        block = "\n".join(lines[begin:end])
        # Group headers span lines; normalise whitespace before scanning.
        for m in re.finditer(
            r"\\multicolumn.*?\\textbf\{\s*([IVX]+)\.\s*([^}]*)\}"
            r"|\\hypertarget\{dim:([A-Za-z]+)\}",
            block,
            re.S,
        ):
            if m.group(3):
                found.append((m.group(3), group))
            else:
                label = re.sub(r"\s+", " ", m.group(2)).strip().rstrip(":")
                group = f"{m.group(1)}. {label}" if label else m.group(1)
        out[key] = found
    return out


def main():
    config = CONFIG.read_text()
    main_tex = MAIN.read_text()

    defs = parse_newcommands(config)
    gls = parse_acronyms(config)

    # Every macro whose body contains a dim: hyperlink defines one category.
    by_anchor = {}
    for name, body in defs.items():
        m = re.search(r"\\hyperlink\{dim:([A-Za-z]+)\}\{(.*)\}", body, re.S)
        if not m:
            continue
        anchor, short = m.group(1), m.group(2)
        # Long form lives in the base macro: \taskAbbr -> \task. One entry
        # (remKAbbr) breaks that convention, so fall back to the anchor name.
        base = name[:-4] if name.endswith("Abbr") else name
        if base not in defs:
            base = anchor
        label = expand(defs.get(base, short), defs, gls).strip()
        by_anchor[anchor] = {
            "anchor": anchor,
            "slug": kebab(label),
            "label": label,
            "abbr": expand(short, defs, gls).strip(),
        }

    regions = anchor_regions(main_tex)

    dimensions = {}
    for key, (name, question) in DIMS.items():
        if key == "d6":
            cats = [
                {
                    "anchor": None,
                    "slug": k,
                    "label": gls[k]["long"],
                    "abbr": gls[k]["short"],
                    "meta_group": None,
                }
                for k in D6_KEYS
            ]
        else:
            cats = []
            for anchor, group in regions.get(key, []):
                if anchor not in by_anchor:
                    raise SystemExit(
                        f"{key}: anchor dim:{anchor} has no macro definition"
                    )
                cat = dict(by_anchor[anchor])
                cat["meta_group"] = group
                cats.append(cat)
        cats.sort(key=lambda c: c["slug"])
        dimensions[key] = {
            "key": key,
            "name": name,
            "question": question,
            "categories": cats,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dimensions, indent=2, ensure_ascii=False) + "\n")

    counts = {k: len(v["categories"]) for k, v in dimensions.items()}
    print(f"wrote {OUT.relative_to(ROOT)}  {counts}")


if __name__ == "__main__":
    main()
