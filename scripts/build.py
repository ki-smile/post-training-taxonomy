#!/usr/bin/env python3
"""Generate the site into docs/.

Runs validate_data first and aborts on failure. Runs validate_site only with
--strict, because link integrity cannot pass until every page exists.
"""

import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts import pages  # noqa: E402
from scripts.layout import page  # noqa: E402
from scripts.validate import validate_data, validate_site  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"


def load():
    d = {}
    for name in ("taxonomy", "dimensions", "derived", "relations",
                 "glossary", "discrepancies", "ambiguities"):
        p = DATA / f"{name}.json"
        d[name] = json.loads(p.read_text()) if p.exists() else None
    return d


def write(rel, html):
    target = DOCS / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


def main():
    strict = "--strict" in sys.argv

    problems = validate_data(ROOT)
    if problems:
        for p in problems:
            print(f"FAIL {p}", file=sys.stderr)
        raise SystemExit("validate_data failed; nothing was rendered")

    d = load()
    built = 0

    for rel, title, body, kw in pages.all_pages(d):
        write(rel, page(title, body, **kw))
        built += 1

    # docs/data must mirror data/ byte-for-byte; Pages cannot read ../data.
    out = DOCS / "data"
    out.mkdir(parents=True, exist_ok=True)
    for f in DATA.glob("*.json"):
        shutil.copy2(f, out / f.name)
    for f in DATA.glob("*.csv"):
        shutil.copy2(f, out / f.name)
    for f in DATA.glob("*.md"):
        shutil.copy2(f, out / f.name)

    print(f"built {built} pages into {DOCS.relative_to(ROOT)}/")

    if strict:
        problems = validate_site(ROOT)
        for p in problems:
            print(f"FAIL {p}", file=sys.stderr)
        if problems:
            raise SystemExit(f"validate_site: {len(problems)} problem(s)")
        print("validate_site: clean")


if __name__ == "__main__":
    main()
