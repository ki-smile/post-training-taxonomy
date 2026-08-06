#!/usr/bin/env python3
"""Extract technique definitions (Appendix C) and category definitions (Appendix B).

Prose comes from LaTeX source, never the PDF text layer, so soft hyphenation
and running page headers never enter the data.

Inline dimension references (\\tax{5}{modSwap}) become live chips, which is
what turns the definitions into navigation rather than flat text. Citations
are preserved as markup: silently dropping them would convert the authors'
attributed claims into unattributed ones.
"""

import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts import sources  # noqa: E402

from scripts.latexlib import (  # noqa: E402
    expand, parse_acronyms, parse_newcommands, split_set,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAX = ROOT / "data/taxonomy.json"
SUMMARIES = ROOT / "data/summaries.json"
DIMS = ROOT / "data/dimensions.json"

CHIP = "\x01"   # sentinel: chip payload survives LaTeX stripping and escaping
CITE = "\x02"

DIM_KEYS = ["d1", "d2", "d3", "d4", "d5", "d6"]


def build_renderer(defs, gls, anchor_index, label_index, dim_mismatches):
    """Return latex -> HTML, safe for embedding in a page."""

    def render(src):
        chips, cites = [], []

        def emit(dim, slug, label):
            chips.append((dim, slug, label))
            return f"{CHIP}{len(chips) - 1}{CHIP}"

        def take_chip(m):
            dim, anchor = f"d{m.group(1)}", m.group(2)
            entry = anchor_index.get(anchor)
            if entry is not None:
                # The anchor uniquely determines its dimension, so trust it
                # over the number written in \tax{n}{...}. Where they disagree
                # the manuscript has mislabelled the dimension; record it
                # rather than emit a chip under the wrong axis.
                if entry["dim"] != dim:
                    dim_mismatches.append((dim, anchor, entry["dim"]))
                    dim = entry["dim"]
                return emit(dim, entry["slug"], entry["label"])
            # Composite anchors (partlMod, taskCompEff, dflm, ...) name a SET
            # of categories via their own macro. Expand into one chip each
            # rather than leaking the raw macro name into the prose.
            body = defs.get(anchor)
            if body:
                parts = []
                for lab in split_set(expand(body, defs, gls)):
                    slug = label_index[dim].get(lab.strip().lower())
                    if slug:
                        parts.append(emit(dim, slug, lab.strip()))
                if parts:
                    return "{" + ", ".join(parts) + "}" if len(parts) > 1 else parts[0]
            return anchor

        def take_cite(m):
            cites.append(m.group(1))
            return f"{CITE}{len(cites) - 1}{CITE}"

        # Before expand(), which would rewrite \tax into its own definition.
        s = re.sub(r"\\tax(?:No)?\{(\d)\}\{([A-Za-z]+)\}", take_chip, src)
        s = re.sub(r"\\cite[tp]?\{([^}]*)\}", take_cite, s)

        s = expand(s, defs, gls)

        # Row numbers are build-dependent; drop the parenthetical entirely.
        s = re.sub(r"\s*\(Rows?~\\ref\{tech:[A-Za-z]+\}(--~?\\ref\{tech:[A-Za-z]+\})?\)", "", s)
        s = re.sub(r"Rows?~\\ref\{tech:[A-Za-z]+\}(--~?\\ref\{tech:[A-Za-z]+\})?", "", s)
        s = re.sub(r"\\ref\{[^}]*\}", "", s)
        s = re.sub(r"\\label\{[^}]*\}", "", s)

        # Text-level markup collapses to its content.
        for _ in range(6):
            s = re.sub(
                r"\\(?:textbf|textit|emph|texttt|textsc|mbox|text)\{([^{}]*)\}",
                r"\1", s,
            )
        s = re.sub(r"\\(?:footnote|hypertarget|makebox)\{[^{}]*\}", "", s)
        # Inline math: keep the content, drop the delimiters and sub/superscript
        # markers, so IA$^3$ reads as IA3 rather than leaking LaTeX.
        s = re.sub(r"\$([^$]*)\$", lambda m: re.sub(r"[\^_{}\\]", "", m.group(1)), s)
        s = re.sub(r"\\[A-Za-z]+\s*", "", s)          # bare commands
        s = s.replace("~", " ").replace("\\%", "%")
        s = re.sub(r"[{}]", "", s)
        s = re.sub(r"\s+", " ", s).strip()

        s = html.escape(s)

        def put_chip(m):
            dim, slug, label = chips[int(m.group(1))]
            return (f'<span class="chip" data-dim="{dim}" data-slug="{slug}">'
                    f"{html.escape(label)}</span>")

        def put_cite(m):
            key = html.escape(cites[int(m.group(1))])
            return f'<sup class="cite" data-cite="{key}">[ref]</sup>'

        s = re.sub(f"{CHIP}(\\d+){CHIP}", put_chip, s)
        s = re.sub(f"{CITE}(\\d+){CITE}", put_cite, s)
        return s

    return render


def technique_definitions(supp, render):
    """Map tech_key -> (definition_html, subsection_title) from Appendix C.

    The Classification Tensions subsection at the end also opens its entries
    with Row~\\ref{tech:...}. Those are discussion of boundary cases, not
    definitions, and letting them through overwrote real definitions with
    fragments. They are split out and returned separately.
    """
    start = supp.find(r"\section{Technique Definitions and Relationships}")
    if start < 0:
        raise SystemExit("Appendix C not found")
    body = supp[start:]
    end = re.search(r"\n\\section\{", body[10:])
    if end:
        body = body[: end.start() + 10]

    tension_at = body.find(r"\subsection{Classification Tensions}")
    if tension_at > 0:
        body, tension_body = body[:tension_at], body[tension_at:]
    else:
        tension_body = ""

    # Subsection titles give each definition its source reference.
    sections = [(m.start(), re.sub(r"\s*\(Rows.*", "", m.group(1)).strip())
                for m in re.finditer(r"\\subsection\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", body)]

    opener = re.compile(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*?Row~\\ref\{tech:([A-Za-z]+)\}[^{}]*)\}")
    hits = list(opener.finditer(body))

    out = {}
    for i, m in enumerate(hits):
        key = m.group(2)
        stop = hits[i + 1].start() if i + 1 < len(hits) else len(body)
        nxt = body.find(r"\subsection{", m.end())
        if 0 < nxt < stop:
            stop = nxt
        chunk = body[m.start():stop]
        section = ""
        for pos, title in sections:
            if pos < m.start():
                section = title
        text = render(chunk)
        if text and key not in out:      # first match wins
            out[key] = (text, section)

    tensions = {}
    if tension_body:
        thits = list(opener.finditer(tension_body))
        for i, m in enumerate(thits):
            stop = thits[i + 1].start() if i + 1 < len(thits) else len(tension_body)
            text = render(tension_body[m.start():stop])
            if text and m.group(2) not in tensions:
                tensions[m.group(2)] = text
    return out, tensions


def category_definitions(supp, render):
    """Map dim anchor -> definition, from the Appendix B tables."""
    out = {}
    for m in re.finditer(r"\\hypertarget\{dim:([A-Za-z]+)\}\{\}", supp):
        anchor = m.group(1)
        tail = supp[m.end(): m.end() + 4000]
        amp = tail.find("&")
        if amp < 0:
            continue
        cell = tail[amp + 1:]
        stop = cell.find("\\\\")
        if stop < 0:
            continue
        text = render(cell[:stop])
        if text and anchor not in out:
            out[anchor] = text
    return out


def main():
    config = sources.config().read_text()
    supp = sources.supplement().read_text()
    supp = re.sub(r"(?m)^\s*%.*$", "", supp)

    defs = parse_newcommands(config)
    gls = parse_acronyms(config)

    dims = json.loads(DIMS.read_text())
    anchor_index = {}
    for key in DIM_KEYS:
        for c in dims[key]["categories"]:
            if c["anchor"]:
                anchor_index[c["anchor"]] = {"dim": key, **c}

    label_index = {}
    for key in DIM_KEYS:
        m = {}
        for c in dims[key]["categories"]:
            m[c["abbr"].strip().lower()] = c["slug"]
            m[c["label"].strip().lower()] = c["slug"]
        label_index[key] = m

    dim_mismatches = []
    render = build_renderer(defs, gls, anchor_index, label_index, dim_mismatches)

    tech_defs, tensions = technique_definitions(supp, render)
    cat_defs = category_definitions(supp, render)

    summaries = json.loads(SUMMARIES.read_text())["summaries"]

    tax = json.loads(TAX.read_text())
    missing = []
    for t in tax["techniques"]:
        text, section = tech_defs.get(t["tech_key"], ("", ""))
        t["definition_verbatim"] = text
        t["source_ref"] = section
        t["classification_tension"] = tensions.get(t["tech_key"], "")
        if t["slug"] not in summaries:
            raise SystemExit(f"summaries.json is missing an entry for {t['slug']}")
        t["summary_editorial"] = summaries[t["slug"]]
        if not text:
            note = "definition not found in Appendix C"
            if note not in t["notes"]:
                t["notes"].append(note)
            missing.append(t["slug"])
    TAX.write_text(json.dumps(tax, indent=2, ensure_ascii=False) + "\n")

    undef = []
    for key in DIM_KEYS:
        for c in dims[key]["categories"]:
            if c["anchor"]:
                c["definition"] = cat_defs.get(c["anchor"], "")
                if not c["definition"]:
                    undef.append(f"{key}/{c['slug']}")
            else:
                c.setdefault("definition", "")
    DIMS.write_text(json.dumps(dims, indent=2, ensure_ascii=False) + "\n")

    print(f"definitions: {len(tech_defs)}/49 techniques, "
          f"{len(cat_defs)}/67 categories, "
          f"{len(tensions)} classification tensions")
    if missing:
        print(f"  no Appendix C definition: {', '.join(missing)}")
    if undef:
        print(f"  no Appendix B definition: {', '.join(undef)}")
    for written, anchor, actual in sorted(set(dim_mismatches)):
        print(f"  MANUSCRIPT: \\tax{{{written[1]}}}{{{anchor}}} but anchor "
              f"dim:{anchor} belongs to {actual.upper()} -- rendered under "
              f"{actual.upper()}")


if __name__ == "__main__":
    main()
