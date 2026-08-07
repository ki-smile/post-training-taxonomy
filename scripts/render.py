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


def cite_label(ref):
    """Short form used in the hover title: Author (Year), Title."""
    bits = []
    if ref.get("authors"):
        bits.append(ref["authors"])
    if ref.get("year"):
        bits.append(f"({ref['year']})")
    line = " ".join(bits)
    return f"{line}. {ref['title']}" if line else ref["title"]


def resolve_citations(html_text, refs):
    """Turn <sup data-cite="key,key">[ref]</sup> into numbered, linked markers.

    The number is the paper's own, so a citation on the page can be checked
    against the same number in the PDF. The full reference is carried in the
    title attribute for hover, and repeated in full at the foot of the page --
    hover alone is invisible on touch devices and cannot be copied.
    """
    import re

    def one(m):
        keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
        known = [k for k in keys if k in refs]
        if not known:
            return ""
        known.sort(key=lambda k: refs[k].get("number") or 9999)
        parts = []
        for k in known:
            ref = refs[k]
            n = ref.get("number")
            label = esc(cite_label(ref))
            shown = str(n) if n else "ref"
            parts.append(
                f'<a href="#ref-{esc(k)}" class="cite__n" title="{label}">{shown}</a>'
            )
        return f'<sup class="cite">[{", ".join(parts)}]</sup>'

    return re.sub(r'<sup class="cite" data-cite="([^"]+)">\[ref\]</sup>', one, html_text)


def cited_keys(*html_texts):
    import re
    keys = []
    for t in html_texts:
        for grp in re.findall(r'data-cite="([^"]+)"', t or ""):
            keys += [k.strip() for k in grp.split(",") if k.strip()]
    return keys


def reference_list(keys, refs):
    """Full entries for the works this page cites, in the paper's order."""
    seen, ordered = set(), []
    for k in keys:
        if k in refs and k not in seen:
            seen.add(k)
            ordered.append(k)
    if not ordered:
        return ""
    ordered.sort(key=lambda k: refs[k].get("number") or 9999)
    items = []
    for k in ordered:
        r = refs[k]
        n = r.get("number")
        marker = f"[{n}]" if n else "—"
        title = esc(r["title"])
        if r.get("url"):
            title = f'<a href="{esc(r["url"])}">{title}</a>'
        tail = " ".join(x for x in (esc(r.get("venue") or ""),) if x)
        items.append(
            f'<li id="ref-{esc(k)}"><span class="ref__n">{marker}</span> '
            f'<span class="ref__body">{esc(r.get("authors") or "")} '
            f'{esc(r.get("year") or "")}. {title}.'
            + (f" <span class=\"ref__venue\">{tail}</span>" if tail else "")
            + "</span></li>"
        )
    return (
        '<section class="stack"><h2>References</h2>'
        f'<ol class="reflist">{"".join(items)}</ol>'
        '<p class="provenance">Numbered as in the paper</p></section>'
    )
