"""Single source of truth for the taxonomy version.

The version describes the *dataset*, not the website. A wording change on a
page does not move it; a changed profile value does, because anyone who
pinned to a version and joined against it would silently get different data.

See CHANGELOG.md for what counts as which kind of change.
"""

VERSION = "1.0.0"
RELEASED = "2026-08-06"
