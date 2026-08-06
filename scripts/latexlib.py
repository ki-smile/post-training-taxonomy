"""LaTeX macro resolution for manuscript extraction.

Pure functions, no I/O. Every other extractor reads the manuscript through
this module, so these four parsing hazards are handled once here rather than
rediscovered in each script:

  1. macros nest and must be expanded to a fixed point
  2. technique names contain literal ``\\&``
  3. rows are delimited by ``\\tech{`` anchors, not by ``\\\\``
  4. dimension sets arrive with ESCAPED braces: ``\\{DL, FM\\}``
"""

import re

_XSPACE = r"\xspace"


def parse_newcommands(tex):
    """Map macro name -> body, brace-balanced so nested braces survive."""
    defs = {}
    for m in re.finditer(r"\\newcommand\{\\([A-Za-z]+)\}\s*\{", tex):
        i = m.end() - 1
        depth = 0
        for j in range(i, len(tex)):
            if tex[j] == "{":
                depth += 1
            elif tex[j] == "}":
                depth -= 1
                if depth == 0:
                    defs[m.group(1)] = tex[i + 1:j]
                    break
    return defs


def parse_acronyms(tex):
    """Map glossary key -> {short, long} from ``\\newacronym`` entries."""
    return {
        m.group(1): {"short": m.group(2), "long": m.group(3)}
        for m in re.finditer(
            r"\\newacronym\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}", tex
        )
    }


def expand(s, defs, gls, max_passes=50):
    """Expand macros to a fixed point. Unknown commands are left intact so
    ``unknown_commands`` can report them rather than losing them silently."""
    for _ in range(max_passes):
        prev = s
        s = re.sub(r"\\hyperlink\{[^}]*\}\{([^}]*)\}", r"\1", s)
        s = re.sub(r"\\pdftooltip\{([^}]*)\}\{[^}]*\}", r"\1", s)
        s = re.sub(
            r"\\(?:gls|glspl|Gls|Glspl|glsentrylong|glsentryshort)\{([^}]*)\}",
            lambda m: gls.get(m.group(1), {}).get("short", m.group(1)),
            s,
        )
        s = re.sub(
            r"\\([A-Za-z]+)(?![A-Za-z])",
            lambda m: defs.get(m.group(1), m.group(0)),
            s,
        )
        if s == prev:
            break
    return s.replace(_XSPACE, "")


def unknown_commands(s, known):
    """Commands still present after expansion. Reported, never dropped."""
    return sorted({m for m in re.findall(r"\\([A-Za-z]+)", s) if m not in known})


def strip_footnote_markers(s):
    """Split ``DA$^\\S$`` into ('DA', ['\\S']). Markers carry meaning and are
    recorded on the record rather than discarded."""
    marks = re.findall(r"\$\^\\?([A-Za-z]+|\*)\$", s)
    stripped = re.sub(r"\$\^[^$]*\$", "", s).strip()
    return stripped, [m if m == "*" else "\\" + m for m in marks]


def normalize_name(s):
    """Canonical form for matching a technique name across sources."""
    s, _ = strip_footnote_markers(s)
    s = s.replace(_XSPACE, "")
    s = re.sub(r"\\[A-Za-z]+", "", s)
    s = re.sub(r"[{}$^\\]", "", s)
    s = re.sub(r"\s*/\s*", "/", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def split_set(s):
    """``'{a, b}'`` -> ``['a','b']`` (sorted); ``'a'`` -> ``['a']``.

    Set-valued cells are the normal case, not the exception. Backslashes are
    stripped alongside braces because D6 cells arrive as ``\\{DL, FM\\}`` with
    escaped braces -- stripping only ``{}`` leaves members like ``\\ DL`` that
    then fail vocabulary lookup for every row.
    """
    s = s.replace(_XSPACE, "")
    s = re.sub(r"\\[A-Za-z]+", "", s)   # named commands
    s = re.sub(r"[{}\\]", " ", s)       # braces AND backslashes
    return sorted({p.strip() for p in s.split(",") if p.strip()})


def kebab(label):
    """'Parametric Update' -> 'parametric-update'. The category slug rule."""
    s = re.sub(r"[^A-Za-z0-9]+", "-", label.strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-")
