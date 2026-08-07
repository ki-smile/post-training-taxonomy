#!/usr/bin/env python3
"""Build data/references.json from the manuscript bibliography.

Two sources, each doing what it is good at:

  The .bib file supplies the metadata -- author, title, year, venue, DOI -- and
  is keyed by exactly the identifiers used in the prose, so nothing is guessed.

  The rendered PDF supplies the NUMBERS. The paper numbers its bibliography
  alphabetically over the works it actually cites, and using the same numbers
  means a reader can check [90] on the site against [90] in the paper. Numbering
  independently would produce a second, conflicting scheme.

Every cite key must resolve to a .bib entry; an unresolved key fails the build
rather than rendering as a dangling marker. Numbers are optional -- a key with
no locatable PDF entry still renders its full reference, just without a number.
"""

import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from scripts import sources  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAX = ROOT / "data/taxonomy.json"
OUT = ROOT / "data/references.json"


def fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def strip_braces(s):
    """BibTeX brace-protection: {Large} {Language} {Models} -> Large Language Models."""
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_bib(text):
    """Minimal BibTeX reader: key -> {field: value}. Brace-balanced values."""
    out = {}
    for m in re.finditer(r"@(\w+)\s*(\{)\s*([^,\s]+)\s*,", text):
        kind, key = m.group(1).lower(), m.group(3)
        # Balance from the ENTRY's opening brace. Starting from the comma
        # after the key would terminate at the first field's closing brace
        # and yield an empty entry.
        open_at = m.start(2)
        depth, body = 0, None
        for j in range(open_at, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    body = text[open_at + 1:j]
                    break
        if body is None:
            continue
        fields = {"__type__": kind}
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            name = fm.group(1).lower()
            rest = body[fm.end():].lstrip()
            if rest.startswith("{"):
                d = 0
                for k, ch in enumerate(rest):
                    if ch == "{":
                        d += 1
                    elif ch == "}":
                        d -= 1
                        if d == 0:
                            fields[name] = rest[1:k]
                            break
            elif rest.startswith('"'):
                end = rest.find('"', 1)
                fields[name] = rest[1:end]
            else:
                fields[name] = rest.split(",")[0].strip()
        out[key] = fields
    return out


def authors_of(entry):
    raw = strip_braces(entry.get("author") or entry.get("editor") or "")
    if not raw:
        return []
    people = []
    for part in re.split(r"\s+and\s+", raw):
        part = part.strip()
        if not part:
            continue
        if "," in part:                       # "Surname, Given"
            surname, given = part.split(",", 1)
            people.append(f"{given.strip()} {surname.strip()}".strip())
        else:
            people.append(part)
    return people


def format_authors(people):
    if not people:
        return ""
    if len(people) == 1:
        return people[0]
    if len(people) <= 6:
        return ", ".join(people[:-1]) + ", and " + people[-1]
    return people[0] + " et al."


def venue_of(e):
    for f in ("journal", "booktitle", "publisher", "school", "institution",
              "howpublished", "series"):
        if e.get(f):
            return strip_braces(e[f])
    if e.get("__type__") == "misc" and e.get("archiveprefix"):
        return strip_braces(e["archiveprefix"])
    return ""


def url_of(e):
    if e.get("doi"):
        doi = strip_braces(e["doi"]).replace("https://doi.org/", "")
        return f"https://doi.org/{doi}"
    if e.get("url"):
        return strip_braces(e["url"])
    if e.get("eprint"):
        return f"https://arxiv.org/abs/{strip_braces(e['eprint'])}"
    return ""


def pdf_numbers():
    """Map a (surname, year, title-word-set) signature to the paper's number."""
    pdf = ROOT / "ref" / "arXiv_clean.pdf"
    alt = sorted((ROOT / "ref").glob("*.pdf"))
    path = pdf if pdf.exists() else (alt[0] if alt else None)
    if path is None:
        return []
    import subprocess
    txt = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                         capture_output=True, text=True).stdout
    if "\nReferences" not in txt:
        return []
    body = txt[txt.index("\nReferences"):]
    out = []
    for chunk in re.split(r"\n\s*(?=\[\d+\]\s)", body):
        m = re.match(r"\s*\[(\d+)\]\s*(.*)", chunk, re.S)
        if not m:
            continue
        n = int(m.group(1))
        flat = re.sub(r"\s+", " ", m.group(2)).strip()
        out.append((n, flat, fold(flat)))
    return out


def main():
    bib_files = sorted((ROOT / "ref").glob("**/*.bib"))
    if not bib_files:
        raise SystemExit(
            "no .bib found under ref/ — the bibliography is not distributed "
            "with this repository; extraction requires it locally"
        )
    entries = {}
    for f in bib_files:
        entries.update(parse_bib(f.read_text(errors="ignore")))

    tax = json.loads(TAX.read_text())
    keys = []
    for t in tax["techniques"]:
        for field in ("definition_verbatim", "classification_tension"):
            for grp in re.findall(r'data-cite="([^"]+)"', t.get(field) or ""):
                keys += [k.strip() for k in grp.split(",")]
    keys = sorted(set(k for k in keys if k))

    missing = [k for k in keys if k not in entries]
    if missing:
        raise SystemExit(
            f"{len(missing)} cite key(s) absent from the bibliography: {missing[:8]}"
        )

    numbered = pdf_numbers()
    refs, unnumbered = {}, []
    for k in keys:
        e = entries[k]
        people = authors_of(e)
        title = strip_braces(e.get("title", ""))
        year = strip_braces(e.get("year", "")) or "n.d."

        n = None
        if numbered:
            surname = fold(people[0].split()[-1]) if people else ""
            words = {w for w in re.findall(r"[a-z0-9]+", fold(title)) if len(w) > 3}
            best, score = None, 0
            for num, _flat, ffold in numbered:
                s = sum(1 for w in words if w in ffold)
                if surname and surname in ffold:
                    s += 2
                if year.isdigit() and year in ffold:
                    s += 1
                if s > score:
                    best, score = num, s
            # demand real title evidence, not just a surname collision
            if best is not None and score >= max(4, len(words) * 0.30 + 2):
                n = best
        if n is None:
            unnumbered.append(k)

        refs[k] = {
            "number": n,
            "authors": format_authors(people),
            "title": title,
            "year": year,
            "venue": venue_of(e),
            "url": url_of(e),
        }

    OUT.write_text(json.dumps(
        {"note": ("Bibliography for works cited in the technique definitions. "
                  "Numbers match the paper's own bibliography so a citation can "
                  "be checked against the PDF."),
         "references": refs}, indent=2, ensure_ascii=False) + "\n")

    named = sum(1 for r in refs.values() if r["number"])
    print(f"wrote {OUT.relative_to(ROOT)}  {len(refs)} references, "
          f"{named} numbered as in the paper")
    if unnumbered:
        print(f"  no paper number for: {', '.join(unnumbered[:6])}"
              + (" …" if len(unnumbered) > 6 else ""))


if __name__ == "__main__":
    main()
