import json
import pathlib
import re


def _tax():
    return json.loads(pathlib.Path("data/taxonomy.json").read_text())


def _dims():
    return json.loads(pathlib.Path("data/dimensions.json").read_text())


def test_extractor_runs():
    assert pathlib.Path('data/taxonomy.json').exists()

def test_every_technique_has_a_definition_or_an_explicit_note():
    for x in _tax()["techniques"]:
        assert x["definition_verbatim"] or x["notes"], f"{x['slug']} has neither"


def test_missing_definitions_are_empty_string_never_none():
    for x in _tax()["techniques"]:
        assert isinstance(x["definition_verbatim"], str)


def test_most_techniques_have_a_definition():
    have = [x for x in _tax()["techniques"] if x["definition_verbatim"]]
    # Training is a reference baseline with no Appendix C entry; the rest
    # should all be covered.
    assert len(have) >= 45


def test_definitions_contain_no_unresolved_latex():
    for x in _tax()["techniques"]:
        d = x["definition_verbatim"]
        assert "\\gls" not in d and "\\xspace" not in d, x["slug"]
        assert not re.search(r"\\[A-Za-z]+\{", d), x["slug"]


def test_inline_dimension_values_become_chip_markup():
    peft = next(x for x in _tax()["techniques"] if x["slug"] == "peft")
    assert 'data-dim="d5"' in peft["definition_verbatim"]
    assert 'data-slug="modular"' in peft["definition_verbatim"]


def test_chip_slugs_are_all_in_the_vocabulary():
    vocab = {
        k: {c["slug"] for c in v["categories"]} for k, v in _dims().items()
    }
    for x in _tax()["techniques"]:
        for dim, slug in re.findall(
            r'data-dim="(d\d)" data-slug="([a-z0-9-]+)"', x["definition_verbatim"]
        ):
            assert slug in vocab[dim], (x["slug"], dim, slug)


def test_citations_are_preserved_as_markup_not_dropped():
    peft = next(x for x in _tax()["techniques"] if x["slug"] == "peft")
    assert 'class="cite"' in peft["definition_verbatim"]


def test_glossary_terms_are_expanded():
    peft = next(x for x in _tax()["techniques"] if x["slug"] == "peft")
    assert "PEFT" in peft["definition_verbatim"]


def test_html_special_characters_are_escaped():
    for x in _tax()["techniques"]:
        d = x["definition_verbatim"]
        # Only our own generated tags may appear.
        for tag in re.findall(r"<(/?)([a-z]+)", d):
            assert tag[1] in {"span", "sup"}, (x["slug"], tag)


def test_source_ref_records_the_appendix_subsection():
    for x in _tax()["techniques"]:
        if x["definition_verbatim"]:
            assert x["source_ref"], x["slug"]


def test_every_dimension_category_has_a_definition():
    dims = _dims()
    for k in ("d1", "d2", "d3", "d4", "d5"):
        missing = [c["slug"] for c in dims[k]["categories"] if not c.get("definition")]
        assert not missing, (k, missing)
