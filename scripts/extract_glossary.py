#!/usr/bin/env python3
"""Extract the acronym glossary from the manuscript.

The manuscript defines every acronym once via \\newacronym{key}{short}{long},
so the glossary needs no scraping and no inference.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts import sources  # noqa: E402

from scripts.latexlib import parse_acronyms  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/glossary.json"


def main():
    gls = parse_acronyms(sources.config().read_text())
    entries = [
        {"key": k, "short": v["short"], "long": v["long"]}
        for k, v in gls.items()
    ]
    entries.sort(key=lambda e: e["short"].lower())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"entries": entries}, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"wrote {OUT.relative_to(ROOT)}  {len(entries)} entries")


if __name__ == "__main__":
    main()
