"""Locate the manuscript source files.

Files are discovered by role, not by hardcoded filename. Two reasons: the
filenames encode the submission venue, which must not appear anywhere in the
published repository, and discovery survives the authors renaming or
restructuring their LaTeX.

The manuscript itself lives in ref/, which is git-ignored and never pushed.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = ROOT / "ref" / "latex"


def _find(*needles, required=True):
    """First .tex whose name contains all needles, else None."""
    if REF.exists():
        for p in sorted(REF.glob("*.tex")):
            name = p.name.lower()
            if all(n in name for n in needles):
                return p
    if required:
        raise SystemExit(
            f"manuscript source not found for {needles!r} under {REF}. "
            "The manuscript is not distributed with this repository; "
            "extraction requires it locally."
        )
    return None


def config():
    """Macro and glossary definitions."""
    return _find("config")


def centerpiece():
    """The six-dimensional profile table."""
    return _find("centerpiece")


def main_text():
    """Main article: dimension category tables."""
    return _find("main")


def supplement():
    """Supplement: appendices, definitions, tensions."""
    return _find("supplement")
