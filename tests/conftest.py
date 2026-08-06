"""Test fixtures.

Two modes, and the difference matters:

  With ref/ present (the authors' machine) the extraction pipeline runs first,
  so the tests check that extraction still reproduces the committed data.

  Without it (a fresh clone, or CI) the pipeline cannot run -- the manuscript
  is not distributed -- so the tests run against the committed data instead.
  That is the more important case to keep working: it is what anyone who
  forks the repository gets, and it verifies the artifact that actually ships.

Either way the tests never invoke extractors themselves; the stages share
data/taxonomy.json, and running a later stage out of order discards what an
earlier one merged in.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import pipeline  # noqa: E402

MANUSCRIPT = ROOT / "ref" / "latex"


def pytest_report_header(config):
    mode = "re-extracting from manuscript" if MANUSCRIPT.exists() else \
           "committed data (no manuscript present)"
    return f"taxonomy: testing against {mode}"


@pytest.fixture(scope="session", autouse=True)
def built():
    if MANUSCRIPT.exists():
        pipeline.run(quiet=True)
    else:
        # Nothing to rebuild from; assert the shipped data is actually here.
        missing = [
            n for n in ("taxonomy.json", "dimensions.json", "derived.json",
                        "relations.json", "glossary.json")
            if not (ROOT / "data" / n).exists()
        ]
        if missing:
            pytest.exit(f"data/ is incomplete and cannot be rebuilt: {missing}")
