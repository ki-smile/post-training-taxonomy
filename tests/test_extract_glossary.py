import json
import pathlib


def _gls():
    return json.loads(pathlib.Path("data/glossary.json").read_text())


def _tax():
    return json.loads(pathlib.Path("data/taxonomy.json").read_text())


def test_glossary_has_171_entries():
    assert len(_gls()["entries"]) == 171


def test_known_acronyms_resolve():
    g = {e["key"]: e for e in _gls()["entries"]}
    assert g["llm"]["long"] == "Large Language Model"
    assert g["peft"]["short"] == "PEFT"


def test_entries_are_sorted_and_complete():
    entries = _gls()["entries"]
    assert entries == sorted(entries, key=lambda e: e["short"].lower())
    for e in entries:
        assert e["key"] and e["short"] and e["long"]


def test_footnote_text_attached_to_flagged_techniques():
    ssl = next(x for x in _tax()["techniques"] if x["slug"] == "ssl")
    assert any("adaptation role" in f["text"] for f in ssl["footnotes"])


def test_section_marker_techniques_get_the_classification_tensions_note():
    flagged = [x for x in _tax()["techniques"] if "\\S" in x["footnote_markers"]]
    assert len(flagged) == 7  # the paper flags exactly seven
    for x in flagged:
        assert any("tension" in f["text"].lower() for f in x["footnotes"])


def test_centerpiece_note_is_recorded_in_meta():
    note = _tax()["meta"]["centerpiece_note"]
    assert "explain" in note.lower()


def test_fsl_footnote_points_at_icl():
    fsl = next(x for x in _tax()["techniques"] if x["slug"] == "fsl")
    assert any("ICL" in f["text"] for f in fsl["footnotes"])
