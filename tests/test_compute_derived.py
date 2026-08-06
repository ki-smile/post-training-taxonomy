import json
import pathlib


def _d():
    return json.loads(pathlib.Path("data/derived.json").read_text())


def test_gower_matrix_is_square_symmetric_zero_diagonal():
    g = _d()["gower"]
    assert len(g) == 49 and all(len(r) == 49 for r in g)
    for i in range(49):
        assert abs(g[i][i]) < 1e-12
        for j in range(49):
            assert abs(g[i][j] - g[j][i]) < 1e-12


def test_order_matches_the_taxonomy():
    tax = json.loads(pathlib.Path("data/taxonomy.json").read_text())
    assert _d()["order"] == [x["slug"] for x in tax["techniques"]]


def test_separator_three_states_for_partial_ft_vs_peft():
    # No disjoint dimension: PEFT strictly extends Partial FT. A two-state
    # comparison would wrongly report "separated by".
    s = _d()["separators"]["partft|peft"]
    assert set(s["identical"]) == {"d1", "d3", "d4", "d6"}
    assert set(s["overlapping"]) == {"d2", "d5"}
    assert s["disjoint"] == []


def test_separator_for_fsl_vs_icl_has_no_identical_dimension():
    s = _d()["separators"]["fsl|icl"]
    assert s["identical"] == []
    assert set(s["disjoint"]) == {"d1", "d4", "d5", "d6"}


def test_training_vs_retraining_matches_the_paper():
    s = _d()["separators"]["training|retraining"]
    assert set(s["identical"]) == {"d1", "d4", "d5", "d6"}
    assert set(s["disjoint"]) == {"d2", "d3"}


def test_nearest_excludes_self_and_returns_five():
    n = _d()["nearest"]["peft"]
    assert len(n) == 5 and all(x["slug"] != "peft" for x in n)
    assert n == sorted(n, key=lambda x: x["distance"])


def test_umap_payload_declares_its_provenance():
    """Whatever is shipped must say which run produced it.

    A recomputed embedding is a different figure from the paper's, so the
    distinction has to survive into the data, not just the page.
    """
    u = _d()["umap"]
    if u is None:
        return  # nothing exported yet
    assert u["source"] in {"authors", "recomputed"}
    assert len(u["points"]) == 49
    if u["source"] == "recomputed":
        # the published value must be carried alongside for comparison
        assert u["published_silhouette"] is not None
        assert u["silhouette"] != u["published_silhouette"]


def test_silhouette_reproduces_the_manuscript_value():
    # The manuscript reports +0.0173 for the raw Gower silhouette.
    assert abs(_d()["silhouette"]["raw_gower_all"] - 0.0173) < 5e-4


def test_blind_spot_counts_are_derived_not_asserted():
    b = _d()["compute_blind_spot"]
    assert b["total"] == 14
    assert len(b["exclusive"]) == 10
    assert len(b["dual"]) == 4
    assert "activation-steering" in b["exclusive"] or "actsteer" in b["exclusive"]


def test_umap_coordinates_are_consumed_when_exported(tmp_path, monkeypatch):
    """The scatter must light up from an export without further code changes."""
    import subprocess, sys, shutil
    root = tmp_path / "r"
    shutil.copytree(".", root, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "ref", "docs", "node_modules"))
    tax = json.loads((root / "data/taxonomy.json").read_text())
    names = [t["name"] for t in tax["techniques"]]
    (root / "data/umap_coords.json").write_text(json.dumps({
        "technique": names,
        "family": [t["family"] for t in tax["techniques"]],
        "x": [float(i) for i in range(len(names))],
        "y": [float(-i) for i in range(len(names))],
        "silhouette_umap": -0.0346,
        "versions": {"umap_learn": "0.5.x"},
    }))
    subprocess.run([sys.executable, "scripts/compute_derived.py"],
                   cwd=root, check=True, capture_output=True)
    d = json.loads((root / "data/derived.json").read_text())
    assert d["umap"] is not None
    assert len(d["umap"]["points"]) == 49
    assert d["umap"]["silhouette"] == -0.0346


def test_mismatched_coordinate_names_fail_loudly(tmp_path):
    """A silently dropped point would be worse than a failed build."""
    import subprocess, sys, shutil
    root = tmp_path / "r"
    shutil.copytree(".", root, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "ref", "docs", "node_modules"))
    (root / "data/umap_coords.json").write_text(json.dumps({
        "technique": ["Not A Real Technique"], "family": ["X"],
        "x": [0.0], "y": [0.0],
    }))
    r = subprocess.run([sys.executable, "scripts/compute_derived.py"],
                       cwd=root, capture_output=True, text=True)
    assert r.returncode != 0
    assert "missing" in (r.stderr + r.stdout).lower()
