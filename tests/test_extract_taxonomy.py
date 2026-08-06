import collections
import json
import pathlib

TAX = pathlib.Path("data/taxonomy.json")


def _tax():
    return json.loads(TAX.read_text())


def test_runs_and_emits_49_records():
    t = _tax()
    assert len(t["techniques"]) == 49
    assert sum(1 for x in t["techniques"] if x["is_reference_row"]) == 1


def test_family_sizes_match_the_manuscript():
    fams = collections.Counter(
        x["family"] for x in _tax()["techniques"] if not x["is_reference_row"]
    )
    assert sorted(fams.values()) == [3, 4, 4, 5, 5, 5, 6, 8, 8]


def test_all_dimension_values_are_arrays_even_singletons():
    for x in _tax()["techniques"]:
        for d in ("d1", "d2", "d3", "d4", "d5", "d6"):
            assert isinstance(x[d], list) and len(x[d]) >= 1


def test_cross_check_compares_all_294_cells_with_zero_outstanding():
    meta = _tax()["meta"]["crosscheck"]
    assert meta["cells_compared"] == 294  # 49 x 6; a smaller denominator is the bug
    assert meta["cells_identical"] == 294
    assert meta["outstanding"] == 0


def test_fsl_uses_the_manuscript_value_not_the_stale_notebook_one():
    fsl = next(x for x in _tax()["techniques"] if x["slug"] == "fsl")
    assert sorted(fsl["d3"]) == ["few-demonstrations", "small-labeled"]


def test_peft_profile_matches_the_manuscript():
    p = next(x for x in _tax()["techniques"] if x["slug"] == "peft")
    assert p["d1"] == ["parametric-update"]
    assert sorted(p["d2"]) == ["computational-efficiency", "task-specialization"]
    assert sorted(p["d5"]) == ["modular", "partial"]
    assert sorted(p["d6"]) == ["dl", "fm", "llm", "mllm"]


def test_slugs_are_unique_and_url_safe():
    slugs = [x["slug"] for x in _tax()["techniques"]]
    assert len(slugs) == len(set(slugs))
    assert all(s.replace("-", "").isalnum() and s.islower() for s in slugs)


def test_slug_is_lowercased_tech_key():
    slugs = {x["slug"] for x in _tax()["techniques"]}
    for expected in ("peft", "fullft", "advrstrn", "munlrn", "ttcompute", "ssl"):
        assert expected in slugs


def test_footnote_markers_recorded_not_discarded():
    da = next(x for x in _tax()["techniques"] if x["slug"] == "da")
    assert da["footnote_markers"]  # DA carries the section-symbol marker


def test_every_dimension_value_exists_in_the_vocabulary():
    dims = json.loads(pathlib.Path("data/dimensions.json").read_text())
    vocab = {k: {c["slug"] for c in v["categories"]} for k, v in dims.items()}
    for x in _tax()["techniques"]:
        for d in ("d1", "d2", "d3", "d4", "d5", "d6"):
            assert set(x[d]) <= vocab[d], (x["slug"], d, x[d])


def test_discrepancies_file_records_the_resolved_fsl_case():
    d = json.loads(pathlib.Path("data/discrepancies.json").read_text())
    assert any(
        e["slug"] == "fsl" and e["status"] == "resolved" for e in d["entries"]
    )


def test_csv_is_written_with_pipe_joined_sets():
    rows = pathlib.Path("data/taxonomy.csv").read_text().splitlines()
    assert len(rows) == 50  # header + 49
    assert "slug" in rows[0]
    assert any("|" in r for r in rows[1:])
