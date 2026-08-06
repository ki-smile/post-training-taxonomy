import json
import pathlib
import re
import subprocess
import sys

import pytest

DOCS = pathlib.Path("docs")


@pytest.fixture(scope="module", autouse=True)
def site():
    subprocess.run([sys.executable, "scripts/build.py"], check=True)


def test_generates_49_technique_pages_and_6_dimension_pages():
    assert len(list(DOCS.glob("techniques/*/index.html"))) == 49
    assert len(list(DOCS.glob("dimensions/d*/index.html"))) == 6


def test_every_named_page_exists():
    for name in ("index.html", "404.html", "explorer/index.html",
                 "concepts/index.html", "ambiguity/index.html",
                 "governance/index.html", "compare/index.html",
                 "disambiguate/index.html", "wizard/index.html",
                 "map/index.html", "glossary/index.html", "data/index.html"):
        assert (DOCS / name).exists(), name


def test_no_unrendered_template_tokens_remain():
    for p in DOCS.rglob("*.html"):
        text = p.read_text()
        assert "${" not in text, p
        assert "{{" not in text or "bibtex" in text.lower(), p


def test_technique_page_contains_profile_strip_and_citation():
    h = (DOCS / "techniques/peft/index.html").read_text()
    assert 'class="profile-strip"' in h
    assert "arXiv:" in h


def test_editorial_summary_is_explicitly_labelled():
    h = (DOCS / "techniques/peft/index.html").read_text()
    assert "site editorial" in h.lower()


def test_reference_row_is_marked_distinct():
    h = (DOCS / "techniques/training/index.html").read_text()
    assert "reference baseline" in h.lower()


def test_docs_data_is_byte_identical_to_data():
    for src in pathlib.Path("data").glob("*.json"):
        assert (DOCS / "data" / src.name).read_bytes() == src.read_bytes()


def test_explorer_has_all_49_rows_without_js():
    h = (DOCS / "explorer/index.html").read_text()
    assert h.count('data-technique="') == 49


def test_explorer_has_six_dimension_facets_plus_family():
    h = (DOCS / "explorer/index.html").read_text()
    for d in ("d1", "d2", "d3", "d4", "d5", "d6", "family"):
        assert f'data-facet="{d}"' in h


def test_result_count_is_a_live_region():
    assert 'aria-live="polite"' in (DOCS / "explorer/index.html").read_text()


def test_concepts_states_the_exclusion_caveat():
    h = (DOCS / "concepts/index.html").read_text().lower()
    assert "scope boundary, not a claim of" in h
    assert "regulatory irrelevance" in h


def test_separator_matrix_is_static_not_js_generated():
    h = (DOCS / "concepts/index.html").read_text()
    assert "Training" in h and "Retraining" in h
    assert "strictly extends" in h


def test_blind_spot_counts_are_computed_and_correct():
    h = (DOCS / "ambiguity/index.html").read_text()
    assert "<strong>14 of 49</strong>" in h   # not a bare "14"
    assert "exclusively non-gradient" in h
    assert "dual-mechanism" in h


def test_governance_uses_only_permitted_modal_verbs():
    h = (DOCS / "governance/index.html").read_text()
    for blk in re.findall(r'class="[^"]*reg-claim[^"]*"[^>]*>(.*?)</', h, re.S):
        assert not re.search(r"\b(triggers|constitutes|requires|must)\b", blk, re.I)


def test_every_page_carries_the_disclaimer():
    for name in ("concepts", "ambiguity", "governance"):
        h = (DOCS / name / "index.html").read_text().lower()
        assert "not legal advice" in h


def test_ladder_has_five_tiers_and_shows_supersession():
    h = (DOCS / "map/index.html").read_text()
    for tier in ("ML", "DL", "FM", "LLM", "MLLM"):
        assert f'data-tier="{tier}"' in h
    assert "supersed" in h.lower()


def test_scatter_absent_while_umap_is_null():
    d = json.loads(pathlib.Path("data/derived.json").read_text())
    h = (DOCS / "map/index.html").read_text().lower()
    if d["umap"] is None:
        assert "not yet exported" in h


def test_map_states_the_near_zero_silhouette_finding():
    h = (DOCS / "map/index.html").read_text().lower()
    assert "silhouette" in h and "navigational" in h


def test_glossary_page_lists_all_171_entries():
    h = (DOCS / "glossary/index.html").read_text()
    assert h.count('class="glossary-entry"') == 171


def test_data_page_offers_csv_and_json():
    h = (DOCS / "data/index.html").read_text()
    assert "taxonomy.csv" in h and "taxonomy.json" in h


def test_hero_renders_a_resolved_profile_without_js():
    h = (DOCS / "index.html").read_text()
    assert 'class="profile-strip"' in h
    assert "fine-tuned" in h.lower()


def test_media_sections_are_present():
    h = (DOCS / "index.html").read_text().lower()
    assert "video overview" in h and "audio overview" in h


def test_video_is_a_click_to_load_facade_not_an_eager_embed():
    """The page must make no third-party request until a reader presses play."""
    h = (DOCS / "index.html").read_text()
    assert "<iframe" not in h, "iframe in static HTML would load on page view"
    assert 'class="video-facade"' in h
    assert 'src="media/video-poster.jpg"' in h  # poster served locally
    assert "youtube.com" not in h and "ytimg.com" not in h


def test_audio_player_present_and_does_not_preload():
    """Without preload="none" every visitor downloads ~19 MB unasked."""
    h = (DOCS / "index.html").read_text()
    assert "<audio" in h and 'preload="none"' in h
    src = re.search(r'<source src="(media/[^"]+\.mp3)"', h)
    assert src, "no mp3 source on the home page"
    assert (DOCS / src.group(1)).exists(), "audio file missing from docs/media"


def test_audio_has_a_download_fallback():
    h = (DOCS / "index.html").read_text()
    assert "download" in h.lower()


def test_video_facade_script_is_actually_attached():
    """The facade is inert without its module; a missing tag fails silently."""
    h = (DOCS / "index.html").read_text()
    assert re.search(r'src="js/video\.js(\?v=[0-9a-f]+)?"', h)
    assert (DOCS / "js/video.js").exists()


def test_video_poster_is_committed_locally():
    poster = DOCS / "media/video-poster.jpg"
    assert poster.exists() and poster.stat().st_size > 5000


def test_arxiv_placeholder_and_bibtex_present():
    h = (DOCS / "index.html").read_text()
    assert "arXiv:XXXX.XXXXX" in h and "@misc" in h


def test_no_venue_name_anywhere_in_docs():
    for p in DOCS.rglob("*.html"):
        low = p.read_text().lower()
        for bad in ("submitted to", "under review", "in revision"):
            assert bad not in low, (p, bad)


def test_every_page_has_a_skip_link_and_main_landmark():
    for p in DOCS.rglob("*.html"):
        h = p.read_text()
        assert 'href="#main"' in h and 'id="main"' in h, p


def test_scatter_renders_when_coordinates_exist():
    import json
    d = json.loads(pathlib.Path("data/derived.json").read_text())
    h = (DOCS / "map/index.html").read_text()
    if d["umap"]:
        assert "<svg viewBox" in h
        assert h.count("<circle") == len(d["umap"]["points"])
        assert "Coordinates as a table" in h
    else:
        assert "not yet exported" in h.lower()


def test_recomputed_projection_is_labelled_as_such():
    """A recomputed embedding must never be captioned as the paper's."""
    import json
    d = json.loads(pathlib.Path("data/derived.json").read_text())
    if not d["umap"]:
        return
    h = (DOCS / "map/index.html").read_text()
    if d["umap"].get("source") == "recomputed":
        assert "Recomputed, not the projection printed in the paper" in h
        assert "authors' own analysis run" not in h
    else:
        assert "authors' own analysis run" in h


def test_assets_are_content_versioned():
    """Without a cache-busting hash, returning visitors keep stale CSS and JS
    after a deploy -- a shipped redesign can appear not to have shipped."""
    h = (DOCS / "index.html").read_text()
    for asset in ("css/style.css", "css/tokens.css", "js/theme.js"):
        assert re.search(rf'{re.escape(asset)}\?v=[0-9a-f]{{8}}', h), asset


def test_fonts_are_actually_self_hosted():
    """src: local() alone silently falls back for anyone without the font."""
    css = (DOCS / "css/style.css").read_text()
    rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)   # ignore commentary
    assert "src: local(" not in rules, "a local()-only src silently falls back"
    for f in ("DMSans-var-latin.woff2", "DMMono-400-latin.woff2",
              "DMMono-500-latin.woff2"):
        assert f in css, f
        p = DOCS / "fonts" / f
        assert p.exists() and p.read_bytes()[:4] == b"wOF2", f


def test_profile_strip_renders_the_same_from_python_and_js():
    """The strip is the site's signature element; it must not differ by which
    code path drew it."""
    py = (pathlib.Path("scripts/render.py")).read_text()
    js = (DOCS / "js/store.js").read_text()
    for marker in ('class="chip"', "data-dim=", "profile-cell__dim",
                   "profile-cell__values", "dimensions/"):
        assert marker in py, f"python renderer missing {marker}"
        assert marker in js, f"js renderer missing {marker}"


def test_hero_is_interactive_and_has_a_static_fallback():
    h = (DOCS / "index.html").read_text()
    assert h.count('class="hero__tab"') == 3
    assert 'class="profile-strip"' in h      # rendered without JS too
    assert re.search(r'src="js/hero\.js(\?v=[0-9a-f]+)?"', h)
