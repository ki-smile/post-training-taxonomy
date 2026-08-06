"""Run the extraction pipeline once per session.

Individual test modules must not invoke extractors themselves: the stages
share data/taxonomy.json, and running a later stage out of order discards
what an earlier one merged in. A single ordered run removes the ordering
dependency between test modules entirely.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts import pipeline  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def built():
    pipeline.run(quiet=True)
