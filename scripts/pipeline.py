#!/usr/bin/env python3
"""Run the extraction stages in dependency order.

Order matters and is not incidental:

    dimensions -> glossary -> taxonomy -> prose -> derived

`taxonomy` regenerates data/taxonomy.json from the manuscript, which discards
anything merged into it afterwards. `prose` then merges definitions back in.
Running `taxonomy` alone after `prose` silently drops every definition, so
this module is the only supported entry point for a full regeneration.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

STAGES = [
    "extract_dimensions",
    "extract_glossary",
    "extract_taxonomy",
    "extract_prose",
    "extract_bibliography",
    "compute_derived",
]


def run(stages=None, quiet=False):
    for stage in stages or STAGES:
        script = ROOT / "scripts" / f"{stage}.py"
        if not script.exists():
            continue  # stage not implemented yet
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=quiet,
            text=True,
        )
        if result.returncode != 0:
            if quiet and result.stderr:
                print(result.stderr, file=sys.stderr)
            raise SystemExit(f"pipeline failed at {stage}")


if __name__ == "__main__":
    run()
