"""Versions. Two of them, because two things change independently.

TAXONOMY_VERSION describes the *dataset* — the 49 profiles, the vocabularies,
the definitions. People cite it and join against it, so it moves only when the
data does. See CHANGELOG.md for what counts as which kind of change.

The site changes far more often: typography, layout, a new page, a bug fix.
None of that says anything about the taxonomy, so it must not move the
taxonomy version. The site is identified by its build date and commit
instead, which is what a reader needs to know ("am I looking at a current
page?") without implying the data beneath it changed.
"""

import datetime
import pathlib
import subprocess

# ---- the dataset ----
TAXONOMY_VERSION = "1.0.0"
TAXONOMY_RELEASED = "2026-08-06"

# Backwards-compatible aliases: the data schema already ships these names.
VERSION = TAXONOMY_VERSION
RELEASED = TAXONOMY_RELEASED

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def site_commit():
    """Short commit of the build, or None outside a git checkout."""
    try:
        out = subprocess.run(
            ["git", "-C", str(_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def site_built():
    """Build date. Uses the commit date where available so a rebuild of an
    unchanged tree does not appear to be a new version of the site."""
    try:
        out = subprocess.run(
            ["git", "-C", str(_ROOT), "log", "-1", "--format=%cs"],
            capture_output=True, text=True, timeout=5,
        )
        if out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return datetime.date.today().isoformat()
