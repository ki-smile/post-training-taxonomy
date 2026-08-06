#!/usr/bin/env python3
"""The fidelity gate. Fails loudly rather than shipping something wrong.

Two stages, because some checks can only pass after rendering:

    validate_data  before rendering -- counts, vocabulary, cross-source
    validate_site  after rendering  -- parity, links, venue, modal verbs

A single all-or-nothing gate deadlocks: build.py produces the docs/data copy
that parity checks, and internal links cannot resolve until every page exists.
"""

import json
import pathlib
import re
import sys

DIM_KEYS = ["d1", "d2", "d3", "d4", "d5", "d6"]
EXPECTED_FAMILY_SIZES = [3, 4, 4, 5, 5, 5, 6, 8, 8]
EXPECTED_CELLS = 294  # 49 x 6

# The paper is referenced as a preprint only; no venue or review status.
VENUE_PATTERNS = [
    r"submitted to", r"under review", r"in revision", r"forthcoming in",
    r"computing surveys", r"\bacm\b", r"\bieee\b", r"\belsevier\b",
    r"\bspringer\b", r"manuscript number",
]

# Regulatory claims use the paper's own modal verbs.
FORBIDDEN_MODALS = r"\b(triggers|constitutes|requires|must)\b"


def _load(root, name):
    p = root / "data" / name
    return json.loads(p.read_text()) if p.exists() else None


def validate_data(root=pathlib.Path(".")):
    errs = []

    # Version drift: the data on disk must carry the version currently
    # declared. Checked here rather than in a test, because the test suite
    # rebuilds the data first and so can never observe a stale build.
    try:
        sys.path.insert(0, str(root.resolve()))
        import importlib
        import scripts.version as _v
        importlib.reload(_v)
        declared, released = _v.VERSION, _v.RELEASED
    except Exception:
        declared = released = None

    tax = _load(root, "taxonomy.json")
    dims = _load(root, "dimensions.json")
    if tax is None or dims is None:
        return ["data/taxonomy.json or data/dimensions.json is missing"]

    meta = tax.get("meta", {})
    if declared and meta.get("version") != declared:
        errs.append(
            f"data/taxonomy.json is stamped {meta.get('version')!r} but "
            f"scripts/version.py declares {declared!r} -- rerun the pipeline"
        )
    if released and meta.get("released") != released:
        errs.append(
            f"data/taxonomy.json release date {meta.get('released')!r} != "
            f"{released!r}"
        )

    techs = tax["techniques"]

    if len(techs) != 49:
        errs.append(f"expected 49 records, got {len(techs)}")
    refs = [t for t in techs if t["is_reference_row"]]
    if len(refs) != 1:
        errs.append(f"expected exactly 1 reference row, got {len(refs)}")

    sizes = {}
    for t in techs:
        if not t["is_reference_row"]:
            sizes[t["family"]] = sizes.get(t["family"], 0) + 1
    if sorted(sizes.values()) != EXPECTED_FAMILY_SIZES:
        errs.append(
            f"family sizes {sorted(sizes.values())} != {EXPECTED_FAMILY_SIZES}"
        )

    vocab = {k: {c["slug"] for c in dims[k]["categories"]} for k in DIM_KEYS}
    for t in techs:
        for k in DIM_KEYS:
            vals = t.get(k)
            if not isinstance(vals, list) or not vals:
                errs.append(f"{t['slug']}/{k}: must be a non-empty list")
                continue
            for v in vals:
                if v not in vocab[k]:
                    errs.append(f"{t['slug']}/{k}: {v!r} not in vocabulary")

    slugs = [t["slug"] for t in techs]
    if len(slugs) != len(set(slugs)):
        errs.append("technique slugs are not unique")
    for s in slugs:
        if not re.fullmatch(r"[a-z0-9-]+", s):
            errs.append(f"slug {s!r} is not URL-safe")

    cc = tax.get("meta", {}).get("crosscheck", {})
    if cc.get("cells_compared") != EXPECTED_CELLS:
        errs.append(
            f"cross-check compared {cc.get('cells_compared')} cells, "
            f"expected {EXPECTED_CELLS} -- a reduced denominator hides skipped rows"
        )
    if cc.get("outstanding", 1) != 0:
        errs.append(f"{cc.get('outstanding')} outstanding cross-source disagreements")

    rels = _load(root, "relations.json")
    if rels is not None:
        known = set(slugs)
        for r in rels["relations"]:
            if r["from"] not in known or r["to"] not in known:
                errs.append(f"relation {r['from']}->{r['to']}: unknown endpoint")
            if len(r.get("source_quote", "").strip()) < 20:
                errs.append(f"relation {r['from']}->{r['to']}: no real source quote")

    for t in techs:
        if t.get("notes"):
            print(f"  note [{t['slug']}]: {'; '.join(t['notes'])}", file=sys.stderr)

    for t in techs:
        leftover = re.findall(r"\\[A-Za-z]+", t.get("definition_verbatim", ""))
        if leftover:
            errs.append(f"{t['slug']}: unresolved LaTeX {sorted(set(leftover))[:3]}")

    return errs


# The denylist scan covers every surface a reader can reach: docs/, data/,
# notebooks/, scripts/, and top-level metadata.
#
# Two exemptions, both necessary rather than convenient:
#   - this file defines the denylist
#   - tests/ holds fixtures that must contain the strings being detected,
#     and no test file is ever rendered to a reader
# scripts/ is deliberately NOT exempt: it ships in the repo and once
# carried manuscript filenames that identified the venue.
EXEMPT_FILES = {("scripts", "validate.py")}
EXEMPT_DIRS = {"tests"}


def _publishable(root):
    """Files that will be pushed. ref/ and specs/ are git-ignored."""
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if rel.parts in EXEMPT_FILES:
            continue
        parts = set(rel.parts)
        if parts & EXEMPT_DIRS:
            continue
        if parts & {"ref", "specs", ".git", "__pycache__", "node_modules"}:
            continue
        if p.suffix in {".html", ".md", ".json", ".cff", ".css", ".js",
                        ".txt", ".py", ".yml", ".yaml", ".sh"}:
            out.append(p)
    return out


def validate_site(root=pathlib.Path(".")):
    errs = []
    docs = root / "docs"

    src = root / "data"
    dst = docs / "data"
    if dst.exists():
        for f in src.glob("*.json"):
            mirror = dst / f.name
            if not mirror.exists():
                errs.append(f"docs/data is missing {f.name}")
            elif mirror.read_bytes() != f.read_bytes():
                errs.append(f"docs/data/{f.name} differs from data/{f.name}")

    for p in _publishable(root):
        text = p.read_text(errors="ignore")
        low = text.lower()
        for pat in VENUE_PATTERNS:
            m = re.search(pat, low)
            if m:
                errs.append(
                    f"{p.relative_to(root)}: venue/status reference {m.group(0)!r}"
                )
        if docs.exists() and docs in p.parents:
            for blk in re.findall(
                r'class="[^"]*reg-claim[^"]*"[^>]*>(.*?)</', text, re.S
            ):
                m = re.search(FORBIDDEN_MODALS, blk, re.I)
                if m:
                    errs.append(
                        f"{p.relative_to(root)}: regulatory claim uses "
                        f"{m.group(0)!r}; use the paper's modal verbs"
                    )

    if docs.exists():
        for bad in list(docs.rglob("*.tex")) + list(docs.rglob("*.pdf")):
            errs.append(f"{bad.relative_to(root)}: manuscript source inside docs/")

        for p in docs.rglob("*.html"):
            for href in re.findall(r'href="(/[^"#?]*)"', p.read_text(errors="ignore")):
                target = docs / href.lstrip("/")
                if not (target.exists() or (target / "index.html").exists()):
                    errs.append(f"{p.relative_to(root)}: dead link {href}")

    return errs


def validate(root=pathlib.Path("."), stage="all"):
    if stage == "data":
        return validate_data(root)
    if stage == "site":
        return validate_site(root)
    return validate_data(root) + validate_site(root)


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    problems = validate(pathlib.Path("."), stage)
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"{len(problems)} problem(s)" if problems else f"validate[{stage}]: clean")
    sys.exit(1 if problems else 0)
