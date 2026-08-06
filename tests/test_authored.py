import json
import pathlib

VALID_TYPES = {"umbrella", "sub-technique", "bridge", "supersession", "hybrid"}


def _tax():
    return json.loads(pathlib.Path("data/taxonomy.json").read_text())


def _slugs():
    return {x["slug"] for x in _tax()["techniques"]}


def test_every_relation_is_typed_endpoint_valid_and_quoted():
    rels = json.loads(pathlib.Path("data/relations.json").read_text())["relations"]
    slugs = _slugs()
    assert len(rels) >= 6
    for r in rels:
        assert r["type"] in VALID_TYPES, r
        assert r["from"] in slugs and r["to"] in slugs, r
        assert len(r["source_quote"].strip()) > 20, r  # a real quote, not a stub
        assert r["source_ref"], r
        assert r["quote_in"] in slugs, r


def test_supersessions_needed_by_the_ladder_are_present():
    rels = json.loads(pathlib.Path("data/relations.json").read_text())["relations"]
    sup = {(r["from"], r["to"]) for r in rels if r["type"] == "supersession"}
    assert ("da", "ssl") in sup or ("da", "peft") in sup
    assert ("metalrn", "icl") in sup


def test_relation_quotes_appear_in_the_extracted_prose():
    """A relation without a locatable source line is not a relation.

    Checked against the rendered definitions rather than raw LaTeX, because
    the source is full of \\gls{} macros that expand at render time.
    """
    import re
    import html as _html
    defs = {
        x["slug"]: " ".join(
            _html.unescape(re.sub(r"<[^>]+>", "", x["definition_verbatim"])).split()
        )
        for x in _tax()["techniques"]
    }
    rels = json.loads(pathlib.Path("data/relations.json").read_text())["relations"]
    for r in rels:
        host = defs.get(r["quote_in"], "")
        probe = " ".join(r["source_quote"].split())
        assert probe in host, (
            f"{r['from']}->{r['to']}: quote not found in {r['quote_in']}"
        )


def test_every_technique_has_a_one_sentence_editorial_summary():
    import re
    for x in _tax()["techniques"]:
        s = x["summary_editorial"]
        assert s and s.endswith("."), x["slug"]
        assert len(s) <= 220, f"{x['slug']} summary too long: {len(s)}"
        # The constraint is ONE sentence. An earlier version of this test
        # only checked the terminal period, so eight two-sentence summaries
        # passed unnoticed until an external reviewer counted them.
        sentences = [p for p in re.split(r"(?<=[.!?])\s+", s.strip()) if p]
        assert len(sentences) == 1, (
            f"{x['slug']}: {len(sentences)} sentences, expected 1"
        )


def test_summaries_do_not_copy_the_verbatim_definition():
    for x in _tax()["techniques"]:
        if x["definition_verbatim"]:
            assert x["summary_editorial"] not in x["definition_verbatim"], x["slug"]


def test_summaries_cover_every_slug_exactly():
    summaries = json.loads(pathlib.Path("data/summaries.json").read_text())["summaries"]
    assert set(summaries) == _slugs()
