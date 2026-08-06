import pytest
from scripts.latexlib import (
    parse_newcommands, parse_acronyms, expand, normalize_name,
    split_set, strip_footnote_markers, unknown_commands,
)


def test_parse_newcommands_handles_nested_braces():
    tex = r"\newcommand{\task}{Task Specialization\xspace}" "\n" \
          r"\newcommand{\taskAbbr}{\hyperlink{dim:task}{Task Spec.\xspace}}"
    defs = parse_newcommands(tex)
    assert defs["task"] == r"Task Specialization\xspace"
    assert defs["taskAbbr"] == r"\hyperlink{dim:task}{Task Spec.\xspace}"


def test_expand_resolves_nested_macros_to_fixed_point():
    defs = {
        "taskAbbr": r"\hyperlink{dim:task}{Task Spec.\xspace}",
        "compEffAbbr": r"\hyperlink{dim:compEff}{Comp. Eff.\xspace}",
        "taskCompEffAbbr": r"{\taskAbbr, {\compEffAbbr}}",
    }
    assert expand(r"\taskCompEffAbbr", defs, {}) == "{Task Spec., {Comp. Eff.}}"


def test_expand_resolves_gls():
    assert expand(r"\gls{peft}", {}, {"peft": {"short": "PEFT"}}) == "PEFT"


def test_expand_leaves_unknown_commands_intact_for_reporting():
    assert r"\mysteryCmd" in expand(r"\mysteryCmd", {}, {})


def test_unknown_commands_reports_survivors():
    assert unknown_commands(r"\mysteryCmd and \another", {"another"}) == ["mysteryCmd"]


def test_split_set_handles_braced_sets_and_singletons():
    assert split_set("{Sched. Perm., Ad-hoc Perm.}") == ["Ad-hoc Perm.", "Sched. Perm."]
    assert split_set("Whole") == ["Whole"]


def test_split_set_handles_ESCAPED_braces():
    # Every D6 cell expands to this form. Stripping only {} leaves stray
    # backslashes and all 49 rows fail vocabulary lookup.
    assert split_set(r"\{DL, FM, LLM, MLLM\}") == ["DL", "FM", "LLM", "MLLM"]


def test_strip_footnote_markers_records_them():
    name, marks = strip_footnote_markers(r"DA$^\S$")
    assert name == "DA"
    assert marks == [r"\S"]


def test_normalize_name_strips_xspace_and_normalizes_slash_spacing():
    # These two exact strings caused false "alias" mismatches in the prototype.
    assert normalize_name(r"Long-Context Ext.\xspace") == "long-context ext."
    assert normalize_name(r"SSL / CPT$^\dagger$") == "ssl/cpt"


def test_parse_acronyms():
    gls = parse_acronyms(r"\newacronym{dl}{DL}{Deep Learning}")
    assert gls["dl"] == {"short": "DL", "long": "Deep Learning"}
