"""Shared HTML fragments used by more than one page."""

from scripts.layout import esc

DIM_KEYS = ["d1", "d2", "d3", "d4", "d5", "d6"]


def strip(dims, technique, *, compact=False, outside=(), up="../../"):
    """The profile strip -- the site's signature element."""
    cells = []
    for i, d in enumerate(DIM_KEYS, start=1):
        labels = []
        for slug in technique[d]:
            cat = next(
                (c for c in dims[d]["categories"] if c["slug"] == slug), None
            )
            label = cat["abbr"] if cat else slug
            labels.append(
                f'<span><a class="chip" data-dim="{d}" '
                f'href="{up}dimensions/{d}/#{esc(slug)}">{esc(label)}</a></span>'
            )
        cls = " profile-cell--outside" if d in outside else ""
        cells.append(
            f'<div class="profile-cell{cls}">'
            f'<span class="profile-cell__dim">{d.upper()}</span>'
            f'<span class="profile-cell__values">{"".join(labels)}</span>'
            f"</div>"
        )
    extra = " profile-strip--compact" if compact else ""
    return (
        f'<div class="profile-strip{extra}" role="group" '
        f'aria-label="Six-dimensional profile">{"".join(cells)}</div>'
    )


def chip_list(dims, key, slugs, up="../../"):
    out = []
    for slug in slugs:
        cat = next((c for c in dims[key]["categories"] if c["slug"] == slug), None)
        label = cat["abbr"] if cat else slug
        out.append(
            f'<a class="chip" data-dim="{key}" '
            f'href="{up}dimensions/{key}/#{esc(slug)}">{esc(label)}</a>'
        )
    return " ".join(out)


def technique_link(t, up="../../"):
    return f'<a href="{up}techniques/{t["slug"]}/">{esc(t["name"])}</a>'


def dim_label(dims, key):
    return f'{key.upper()} {dims[key]["name"]}'


def separator_prose(sep, name_a, name_b, dims):
    """Describe a pair using three-state semantics.

    Only disjoint dimensions separate a pair. Where none do, say so -- calling
    containment "separation" would misdescribe the relationship.
    """
    def names(keys):
        return ", ".join(dim_label(dims, k) for k in keys)

    parts = []
    if sep["identical"]:
        parts.append(
            f"<strong>{esc(name_a)}</strong> and <strong>{esc(name_b)}</strong> "
            f"are identical on {esc(names(sep['identical']))}."
        )
    else:
        parts.append(
            f"<strong>{esc(name_a)}</strong> and <strong>{esc(name_b)}</strong> "
            f"share no dimension exactly."
        )
    if sep["disjoint"]:
        parts.append(f"They are separated by {esc(names(sep['disjoint']))}.")
    else:
        parts.append(
            "No dimension separates them outright — one strictly extends the other."
        )
    if sep["overlapping"]:
        parts.append(f"They partially overlap on {esc(names(sep['overlapping']))}.")
    return " ".join(parts)
