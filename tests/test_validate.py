import json
import pathlib
import shutil

from scripts.validate import validate_data, validate_site

IGNORE = shutil.ignore_patterns(".git", "__pycache__", "ref", "node_modules")


def _copy(tmp_path):
    root = tmp_path / "r"
    shutil.copytree(".", root, ignore=IGNORE)
    return root


def test_clean_repo_passes_data_stage():
    # Site stage is not asserted here: pages that technique pages link to do
    # not exist until the later tasks, so link integrity cannot pass yet.
    assert validate_data(pathlib.Path(".")) == []


def test_unknown_dimension_value_fails(tmp_path):
    root = _copy(tmp_path)
    p = root / "data/taxonomy.json"
    t = json.loads(p.read_text())
    t["techniques"][0]["d1"] = ["not-a-real-category"]
    p.write_text(json.dumps(t))
    assert any("not-a-real-category" in m for m in validate_data(root))


def test_reduced_comparison_count_fails(tmp_path):
    root = _copy(tmp_path)
    p = root / "data/taxonomy.json"
    t = json.loads(p.read_text())
    t["meta"]["crosscheck"]["cells_compared"] = 282
    p.write_text(json.dumps(t))
    assert any("294" in m for m in validate_data(root))


def test_wrong_family_sizes_fail(tmp_path):
    root = _copy(tmp_path)
    p = root / "data/taxonomy.json"
    t = json.loads(p.read_text())
    for x in t["techniques"]:
        if x["slug"] == "peft":
            x["family"] = "Inference-Time Adaptation"
    p.write_text(json.dumps(t))
    assert any("family sizes" in m for m in validate_data(root))


def test_empty_dimension_fails(tmp_path):
    root = _copy(tmp_path)
    p = root / "data/taxonomy.json"
    t = json.loads(p.read_text())
    t["techniques"][0]["d3"] = []
    p.write_text(json.dumps(t))
    assert any("non-empty list" in m for m in validate_data(root))


def test_relation_without_a_real_quote_fails(tmp_path):
    root = _copy(tmp_path)
    p = root / "data/relations.json"
    r = json.loads(p.read_text())
    r["relations"][0]["source_quote"] = "tbd"
    p.write_text(json.dumps(r))
    assert any("source quote" in m for m in validate_data(root))


def test_venue_name_in_docs_fails(tmp_path):
    root = _copy(tmp_path)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs/index.html").write_text("<p>Submitted to a journal</p>")
    assert any("venue/status" in m for m in validate_site(root))


def test_forbidden_modal_verb_in_governance_fails(tmp_path):
    root = _copy(tmp_path)
    d = root / "docs/governance"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(
        '<p class="reg-claim">This triggers re-certification.</p>'
    )
    assert any("triggers" in m for m in validate_site(root))


def test_permitted_modal_verb_passes(tmp_path):
    root = _copy(tmp_path)
    d = root / "docs/governance"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(
        '<p class="reg-claim">This may require documentation.</p>'
    )
    assert not any("reg-claim" in m or "modal" in m for m in validate_site(root))


def test_data_copy_drift_fails(tmp_path):
    root = _copy(tmp_path)
    d = root / "docs/data"
    d.mkdir(parents=True, exist_ok=True)
    (d / "taxonomy.json").write_text('{"techniques": []}')
    assert any("docs/data/taxonomy.json differs" in m for m in validate_site(root))


def test_manuscript_source_inside_docs_fails(tmp_path):
    root = _copy(tmp_path)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs/leak.tex").write_text("\\documentclass{article}")
    assert any("manuscript source inside docs" in m for m in validate_site(root))


def test_scripts_are_not_exempt_from_the_venue_scan(tmp_path):
    """scripts/ ships in the repo and once carried venue-identifying filenames."""
    root = _copy(tmp_path)
    (root / "scripts/leak.py").write_text('URL = "submitted to a journal"')
    assert any("leak.py" in m for m in validate_site(root))


def test_venue_scan_covers_python_sources(tmp_path):
    root = _copy(tmp_path)
    (root / "notebooks/leak.md").write_text("Prepared for ACM review.")
    assert any("leak.md" in m for m in validate_site(root))


def test_stale_version_stamp_fails(tmp_path):
    """A forgotten rebuild ships data labelled with the wrong version, which
    is worse than no version, because consumers pin to it."""
    root = _copy(tmp_path)
    p = root / "data/taxonomy.json"
    t = json.loads(p.read_text())
    t["meta"]["version"] = "0.9.0"
    p.write_text(json.dumps(t))
    assert any("rerun the pipeline" in m for m in validate_data(root))
