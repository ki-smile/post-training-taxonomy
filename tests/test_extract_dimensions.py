import json
import pathlib
import subprocess
import sys

DIMS = pathlib.Path("data/dimensions.json")


def _dims():
    return json.loads(DIMS.read_text())


def test_dimensions_extracted_with_expected_counts():
    subprocess.run([sys.executable, "scripts/extract_dimensions.py"], check=True)
    counts = {k: len(v["categories"]) for k, v in _dims().items()}
    assert counts == {"d1": 9, "d2": 19, "d3": 21, "d4": 8, "d5": 10, "d6": 5}


def test_every_category_has_slug_label_and_abbr():
    for d in _dims().values():
        for c in d["categories"]:
            assert c["slug"] and c["label"] and c["abbr"]
            assert "anchor" in c
            assert c["slug"] == c["slug"].lower()
            assert " " not in c["slug"]


def test_category_slug_is_kebab_of_the_LABEL_not_the_anchor():
    # NORMATIVE: slug = kebab-case of the long label. The manuscript anchor is
    # kept separately in `anchor`, because \tax{n}{key} in prose keys on the
    # anchor and chip rendering must map anchor -> slug.
    dims = _dims()
    d2 = {c["slug"]: c for c in dims["d2"]["categories"]}
    assert "task-specialization" in d2
    assert d2["task-specialization"]["anchor"] == "task"
    d1 = {c["slug"]: c for c in dims["d1"]["categories"]}
    assert "parametric-update" in d1
    assert d1["parametric-update"]["anchor"] == "paramUpd"


def test_d6_categories_come_from_tier_acronyms_and_have_no_anchor():
    # Model tiers carry NO dim: anchors in the manuscript -- all 67 belong to
    # D1-D5 -- so D6 is built from the glossary instead.
    d6 = {c["slug"]: c for c in _dims()["d6"]["categories"]}
    assert set(d6) == {"ml", "dl", "fm", "llm", "mllm"}
    assert d6["llm"]["label"] == "Large Language Model"
    assert d6["llm"]["anchor"] is None


def test_every_dimension_has_name_and_question():
    for key, d in _dims().items():
        assert d["name"] and d["question"]
    assert _dims()["d1"]["name"] == "Mechanism"
    assert _dims()["d6"]["question"] == "What model is being adapted?"


def test_d1_categories_carry_their_meta_group():
    groups = {c["meta_group"] for c in _dims()["d1"]["categories"]}
    # Table 3 organises D1 into four groups, I-IV.
    assert len([g for g in groups if g]) >= 1
    assert len(groups) <= 5


def test_anchors_are_unique_within_a_dimension():
    for d in _dims().values():
        anchors = [c["anchor"] for c in d["categories"] if c["anchor"]]
        assert len(anchors) == len(set(anchors))
