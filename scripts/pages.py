"""Page renderers. Each yields (relative_path, title, body_html, layout_kwargs)."""

from scripts.layout import (
    ARXIV_ID, ARXIV_URL, AUDIO_FILE, AUDIO_LENGTH, AUDIO_TITLE, DISCLAIMER,
    REPO_URL, SMAILE_NAME, SMAILE_URL, VIDEO_CHANNEL, VIDEO_ID, VIDEO_TITLE,
    VIDEO_URL, esc,
)
from scripts.render import (
    DIM_KEYS, chip_list, dim_label, separator_prose, strip, technique_link,
)

EDITORIAL_LABEL = (
    '<p class="provenance">In brief — site editorial, not from the paper</p>'
)


# ---------------------------------------------------------------- techniques

def technique_pages(d):
    tax, dims = d["taxonomy"], d["dimensions"]
    derived = d["derived"] or {}
    rels = (d["relations"] or {}).get("relations", [])
    by_slug = {t["slug"]: t for t in tax["techniques"]}

    for t in tax["techniques"]:
        up = "../../"
        ref = (
            '<p class="callout callout--warn"><strong>Reference baseline.</strong> '
            "Training is included to contrast the properties of post-training "
            "techniques. It is not itself a post-training technique.</p>"
            if t["is_reference_row"] else ""
        )

        related = [
            r for r in rels if r["from"] == t["slug"] or r["to"] == t["slug"]
        ]
        rel_html = ""
        if related:
            items = []
            for r in related:
                other = r["to"] if r["from"] == t["slug"] else r["from"]
                if other not in by_slug:
                    continue
                items.append(
                    f"<li><span class=\"eyebrow\">{esc(r['type'])}</span> "
                    f"{technique_link(by_slug[other], up)} — {esc(r['label'])}"
                    f"<br><q style=\"color:var(--text-muted);font-size:var(--step--1)\">"
                    f"{esc(r['source_quote'])}</q> "
                    f"<span class=\"provenance\">{esc(r['source_ref'])}</span></li>"
                )
            if items:
                rel_html = (
                    f'<section class="stack"><h2>Related techniques</h2>'
                    f'<ul class="stack">{"".join(items)}</ul></section>'
                )

        near = (derived.get("nearest") or {}).get(t["slug"], [])
        near_html = ""
        if near:
            links = ", ".join(
                f'{technique_link(by_slug[n["slug"]], up)} '
                f'<span style="color:var(--text-muted)">({n["distance"]:.2f})</span>'
                for n in near if n["slug"] in by_slug
            )
            near_html = (
                f'<section class="stack"><h2>Nearest profiles</h2>'
                f'<p class="computed">{links}</p>'
                f'<p class="provenance">Computed from the taxonomy data '
                f'(Gower distance over all six dimensions)</p></section>'
            )

        notes = ""
        if t.get("footnotes"):
            notes = (
                '<section class="stack"><h2>Notes from the table</h2>'
                + "".join(
                    f'<p class="callout">{esc(f["text"])}</p>'
                    for f in t["footnotes"]
                )
                + "</section>"
            )

        tension = ""
        if t.get("classification_tension"):
            tension = (
                f'<section class="stack"><h2>Classification tensions</h2>'
                f'<div class="verbatim">{t["classification_tension"]}</div>'
                f'<p class="provenance">Appendix C</p></section>'
            )

        definition = ""
        if t.get("definition_verbatim"):
            definition = (
                f'<section class="stack"><h2>Definition</h2>'
                f'<div class="verbatim">{t["definition_verbatim"]}</div>'
                f'<p class="provenance">Verbatim from the paper — '
                f'{esc(t.get("source_ref", ""))}</p></section>'
            )

        others = [x for x in tax["techniques"] if x["slug"] != t["slug"]][:1]
        compare = (
            f'<a class="btn" href="{up}compare/?t={t["slug"]},{others[0]["slug"]}">'
            f"Compare with another technique</a>" if others else ""
        )

        body = f"""
<div class="wrap section stack">
  <p class="eyebrow">{esc(t["family"])}</p>
  <h1>{esc(t["name"])}</h1>
  {ref}
  {strip(dims, t, up=up)}
  <div class="editorial stack">
    {EDITORIAL_LABEL}
    <p>{esc(t["summary_editorial"])}</p>
  </div>
  {definition}
  {notes}
  {tension}
  {rel_html}
  {near_html}
  <section class="stack">
    <h2>Cite this row</h2>
    <pre>{esc(t["name"])} — six-dimensional profile
{chr(10).join(f'{k.upper()}: {", ".join(t[k])}' for k in DIM_KEYS)}
Source: {ARXIV_ID}</pre>
    {compare}
    <a class="btn" href="{up}explorer/?q={esc(t["slug"])}">Find in the explorer</a>
  </section>
</div>
"""
        yield (
            f"techniques/{t['slug']}/index.html",
            t["name"],
            body,
            {"depth": 2, "description": t["summary_editorial"]},
        )


# ---------------------------------------------------------------- dimensions

def dimension_pages(d):
    tax, dims = d["taxonomy"], d["dimensions"]
    for key in DIM_KEYS:
        dim = dims[key]
        up = "../../"
        groups = {}
        for c in dim["categories"]:
            groups.setdefault(c.get("meta_group") or "", []).append(c)

        blocks = []
        for group, cats in groups.items():
            rows = []
            for c in cats:
                users = [
                    technique_link(t, up)
                    for t in tax["techniques"]
                    if c["slug"] in t[key]
                ]
                rows.append(f"""
<tr id="{esc(c['slug'])}">
  <td><span class="chip" data-dim="{key}">{esc(c['abbr'])}</span><br>
      <strong>{esc(c['label'])}</strong></td>
  <td>{c.get('definition') or '<em>No definition in the appendix.</em>'}</td>
  <td>{', '.join(users) if users else '<em>none</em>'}
      <br><span class="provenance">{len(users)} technique(s)</span></td>
</tr>""")
            heading = f"<h2>{esc(group)}</h2>" if group else ""
            blocks.append(f"""
<section class="stack">{heading}
  <div class="table-scroll"><table>
    <thead><tr><th>Category</th><th>Definition</th><th>Techniques</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>
</section>""")

        others = " ".join(
            f'<a class="chip" data-dim="{k}" href="{up}dimensions/{k}/">'
            f"{k.upper()}</a>"
            for k in DIM_KEYS if k != key
        )

        body = f"""
<div class="wrap section stack">
  <p class="eyebrow">Dimension {key.upper()}</p>
  <h1>{esc(dim['name'])}</h1>
  <p style="font-size:var(--step-1);color:var(--text-muted)">
    {esc(dim['question'])}</p>
  <p>{len(dim['categories'])} categories. Other dimensions: {others}</p>
  {''.join(blocks)}
  <p class="provenance">Category definitions verbatim from the paper's appendix</p>
</div>
"""
        yield (
            f"dimensions/{key}/index.html",
            f"{key.upper()} — {dim['name']}",
            body,
            {"depth": 2, "description": dim["question"]},
        )


def all_pages(d):
    yield home_page(d)
    yield explorer_page(d)
    yield concepts_page(d)
    yield ambiguity_page(d)
    yield governance_page(d)
    yield compare_page(d)
    yield disambiguate_page(d)
    yield wizard_page(d)
    yield map_page(d)
    yield glossary_page(d)
    yield data_page(d)
    yield notfound_page(d)
    yield from technique_pages(d)
    yield from dimension_pages(d)


# ---------------------------------------------------------------------- home

def home_page(d):
    tax, derived = d["taxonomy"], d["derived"]
    n = tax["meta"]["n_techniques"]
    body = f"""
<section class="section wrap">
  <div class="stack" style="max-width:52rem">
    <p class="eyebrow"><a href="{SMAILE_URL}" style="color:inherit">{SMAILE_NAME}</a></p>
    <div id="hero-resolve" class="stack">
      <p style="font-size:var(--step-2);font-family:var(--font-display);
                color:var(--text-muted)" id="hero-phrase">
        &ldquo;The model was fine-tuned.&rdquo;</p>
      <p style="color:var(--text-muted)">&darr; what does that actually mean?</p>
      {strip(d["dimensions"],
             next(t for t in tax["techniques"] if t["slug"] == "peft"),
             up="")}
    </div>
    <h1>{n} techniques. Six dimensions. One coordinate each.</h1>
    <p style="font-size:var(--step-1)">
      A six-dimensional taxonomy of post-training adaptation, built so a model
      change can be named precisely enough to document, compare, and audit.</p>
    <p>
      <a class="btn btn--solid" href="explorer/">Explore the taxonomy</a>
      <a class="btn" href="wizard/">Classify a change</a>
      <a class="btn" href="concepts/">Start with the concepts</a>
    </p>
  </div>
</section>

<section class="section section--surface wrap stack">
  <h2>Three problems this solves</h2>
  <div class="grid grid--3">
    <div class="card stack">
      <p class="eyebrow">Terminological ambiguity</p>
      <p>The same word means different things. &ldquo;Fine-tuning&rdquo; covers
         three different scopes with three different validation burdens.</p>
      <a href="disambiguate/">Disambiguate a term &rarr;</a>
    </div>
    <div class="card stack">
      <p class="eyebrow">Single-axis taxonomies</p>
      <p>Is PEFT a fine-tuning method or an efficiency method? It is both, which
         is why one axis cannot hold it.</p>
      <a href="explorer/">Filter on all six axes &rarr;</a>
    </div>
    <div class="card stack">
      <p class="eyebrow">Model-type conflation</p>
      <p>Prompt engineering is meaningless for a random forest. Which techniques
         are even available depends on what you are adapting.</p>
      <a href="map/">See the model-tier ladder &rarr;</a>
    </div>
  </div>
</section>

<section class="section wrap stack">
  <h2>Training, or post-training?</h2>
  <p>Training and retraining are <em>mechanistically identical</em> — the same
     gradient updates, the same permanence, the same scope. What separates them
     is why you did it and what data you used.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Pair</th><th>Identical on</th><th>Separated by</th></tr></thead>
    <tbody>
      <tr><td>Training vs Retraining</td><td>D1, D4, D5, D6</td>
          <td><strong>D2</strong> build vs repair · <strong>D3</strong> data regime</td></tr>
      <tr><td>Retraining vs Full FT</td><td>D1, D4, D5</td>
          <td><strong>D2</strong> drift vs new task</td></tr>
      <tr><td>Partial FT vs PEFT</td><td>D1, D3, D4, D6</td>
          <td><em>nothing outright</em> — PEFT strictly extends it</td></tr>
    </tbody>
  </table></div>
  <p><a class="btn" href="concepts/">What counts as post-training adaptation?</a></p>
</section>

<section class="section section--surface wrap stack">
  <h2>Why precision matters</h2>
  <div class="grid grid--2">
    <div class="card stack">
      <p class="eyebrow">Before</p>
      <p><q>Update v2.1: the model was fine-tuned on recent hospital data to
        improve performance and incorporate new clinical guidelines.</q></p>
      <p style="color:var(--text-muted)">Does not say whether base weights
        changed, whether the change is permanent, or whether the guidelines were
        learned or retrieved.</p>
    </div>
    <div class="card stack">
      <p class="eyebrow">After</p>
      <p>Two layers, named separately — a parameter update to an adapter, and a
         retrieval corpus update. Each with its own six-dimensional profile.</p>
      <a href="ambiguity/">See the full worked example &rarr;</a>
    </div>
  </div>
</section>

<section class="section wrap stack">
  <h2>Overviews</h2>
  <div class="grid grid--2">
    <div class="stack">
      <p class="eyebrow">Video overview</p>
      <button class="video-facade" type="button"
              data-video="{VIDEO_ID}" data-title="{esc(VIDEO_TITLE)}"
              aria-label="Play: {esc(VIDEO_TITLE)}">
        <img src="media/video-poster.jpg" alt="" width="1280" height="720">
        <span class="video-facade__play" aria-hidden="true">&#9654;</span>
      </button>
      <p><strong>{esc(VIDEO_TITLE)}</strong><br>
        <span class="provenance">{esc(VIDEO_CHANNEL)}</span></p>
      <p class="provenance">Nothing loads from YouTube until you press play.
        <a href="{VIDEO_URL}">Watch on YouTube instead</a></p>
    </div>
    <div class="stack">
      <p class="eyebrow">Audio overview</p>
      <div class="card stack">
        <p><strong>{esc(AUDIO_TITLE)}</strong><br>
          <span class="provenance">{esc(VIDEO_CHANNEL)} · {esc(AUDIO_LENGTH)}</span></p>
        <audio controls preload="none" style="width:100%">
          <source src="media/{AUDIO_FILE}" type="audio/mpeg">
          Your browser cannot play audio inline —
          <a href="media/{AUDIO_FILE}">download the file</a> instead.
        </audio>
        <p class="provenance">
          <a href="media/{AUDIO_FILE}" download>Download (19 MB)</a>
          · nothing downloads until you press play</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--surface wrap stack">
  <h2>Cite</h2>
  <p>The preprint is <a href="{ARXIV_URL}">{ARXIV_ID}</a>
     <em>(placeholder until posted)</em>.</p>
  <pre>@misc{{afdideh2026taxonomy,
  title  = {{A Six-Dimensional Taxonomy of Post-Training Adaptation
            Techniques with Applications in AI Governance}},
  author = {{Afdideh, Fardin and Seoane, Fernando and Abtahi, Farhad}},
  year   = {{2026}},
  eprint = {{XXXX.XXXXX}},
  archivePrefix = {{arXiv}}
}}</pre>
  <p><a class="btn" href="data/">Download the taxonomy data</a></p>
</section>
"""
    return ("index.html", "A six-dimensional taxonomy of post-training adaptation",
            body, {"depth": 0, "scripts": ("video.js",),
                   "description": f"{n} post-training adaptation techniques, "
                                  "each with a six-dimensional profile."})


# ------------------------------------------------------------------ explorer

def explorer_page(d):
    tax, dims = d["taxonomy"], d["dimensions"]
    up = "../"
    facets = []
    for k in DIM_KEYS:
        opts = "".join(
            f'<label class="facet__opt"><input type="checkbox" data-facet="{k}" '
            f'value="{esc(c["slug"])}"> <span class="chip" data-dim="{k}">'
            f'{esc(c["abbr"])}</span></label>'
            for c in dims[k]["categories"]
        )
        facets.append(
            f'<details class="facet" data-facet-group="{k}"><summary>'
            f'<strong>{k.upper()}</strong> {esc(dims[k]["name"])}</summary>'
            f'<div class="facet__opts">{opts}</div></details>'
        )
    fams = sorted({t["family"] for t in tax["techniques"]})
    fam_opts = "".join(
        f'<label class="facet__opt"><input type="checkbox" data-facet="family" '
        f'value="{esc(f)}"> {esc(f)}</label>' for f in fams
    )
    facets.append(
        '<details class="facet" data-facet-group="family"><summary>'
        '<strong>Family</strong> navigational grouping</summary>'
        f'<div class="facet__opts">{fam_opts}</div></details>'
    )

    rows = []
    for t in tax["techniques"]:
        cells = "".join(
            f"<td>{chip_list(dims, k, t[k], up)}</td>" for k in DIM_KEYS
        )
        rows.append(
            f'<tr data-technique="{esc(t["slug"])}">'
            f'<td class="tech-cell"><a href="{up}techniques/{t["slug"]}/">'
            f'<strong>{esc(t["name"])}</strong></a>'
            f'<span class="tech-cell__family">{esc(t["family"])}</span></td>'
            f"{cells}</tr>"
        )
    heads = "".join(
        f'<th>{k.upper()}<br><span style="font-weight:400;text-transform:none">'
        f'{esc(dims[k]["name"])}</span></th>' for k in DIM_KEYS
    )

    body = f"""
<div class="wrap section stack">
  <h1>Taxonomy explorer</h1>
  <p>All {len(tax["techniques"])} rows, filterable on every dimension at once.
     Selecting several values inside one dimension widens the result; selecting
     across dimensions narrows it.</p>
  <div class="explorer">
    <aside class="explorer__facets stack">
      <p class="eyebrow">Filter</p>
      {''.join(facets)}
    </aside>
    <div class="explorer__results stack">
      <div class="explorer__bar">
        <label class="visually-hidden" for="q">Search techniques</label>
        <input id="q" type="search" placeholder="Search techniques…">
        <button class="btn" id="reset" type="button">Reset</button>
      </div>
      <p aria-live="polite" id="count" class="provenance">
        {len(tax["techniques"])} of {len(tax["techniques"])} techniques</p>
      <div class="table-scroll"><table id="results">
        <thead><tr><th>Technique</th>{heads}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
    </div>
  </div>
</div>
"""
    return ("explorer/index.html", "Explorer", body,
            {"depth": 1, "current": "/explorer/", "scripts": ("explorer.js",),
             "description": "Filter 49 adaptation techniques on all six dimensions."})


# ------------------------------------------------------------------ concepts

def concepts_page(d):
    tax, dims, derived = d["taxonomy"], d["dimensions"], d["derived"]
    by = {t["slug"]: t for t in tax["techniques"]}
    seps = derived["separators"]

    rows = []
    PAIRS = [("training", "retraining"), ("retraining", "fullft"),
             ("fullft", "partft"), ("partft", "peft"),
             ("retraining", "cl"), ("fsl", "icl")]
    for a, b in PAIRS:
        s = seps.get(f"{a}|{b}")
        if not s:
            continue
        def fmt(keys):
            return ", ".join(k.upper() for k in keys) or "—"
        rows.append(
            f"<tr><td>{esc(by[a]['name'])} vs {esc(by[b]['name'])}</td>"
            f"<td>{fmt(s['identical'])}</td>"
            f"<td>{fmt(s['overlapping'])}</td>"
            f"<td><strong>{fmt(s['disjoint'])}</strong></td></tr>"
        )

    body = f"""
<div class="wrap section stack">
  <h1>Training, or post-training?</h1>
  <p style="font-size:var(--step-1)">&ldquo;Post-training&rdquo; is an
     operational context, not a technique class. It marks the point after which
     a model already exists and may carry obligations.</p>

  <section class="stack">
    <h2>The lifecycle</h2>
    <pre>  Training  →  Deployment  →  Drift  →  Post-training adaptation  →  Redeployment
                                                    ↑
                              48 techniques live here</pre>
  </section>

  <section class="stack">
    <h2>Five things that all look like &ldquo;updating the weights&rdquo;</h2>
    <p>Each pair below shares most of its profile. The column that matters is
       the last one: only a dimension where the two share <em>no</em> value
       actually separates them.</p>
    <div class="table-scroll"><table>
      <thead><tr><th>Pair</th><th>Identical on</th><th>Overlapping</th>
        <th>Separated by</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table></div>
    <p class="provenance">Computed from the taxonomy data</p>
    <p class="callout">Partial FT and PEFT have <strong>no</strong> separating
      dimension: PEFT strictly extends Partial FT rather than differing from it.
      A two-state comparison would report them as &ldquo;separated&rdquo;, which
      would be wrong.</p>
  </section>

  <section class="stack">
    <h2>What drift means</h2>
    <div class="grid grid--2">
      <div class="card"><p class="eyebrow">Covariate shift</p>
        <p>The inputs change; the input–output relationship holds.</p></div>
      <div class="card"><p class="eyebrow">Concept drift</p>
        <p>The input–output mapping itself changes, invalidating learned
           behaviour.</p></div>
      <div class="card"><p class="eyebrow">Prompt drift</p>
        <p>How people interact with the model evolves.</p></div>
      <div class="card"><p class="eyebrow">Alignment drift</p>
        <p>Static behaviour diverges from shifting safety or cultural
           standards.</p></div>
    </div>
    <p class="reg-claim">Monitoring for drift may be treated as a safety and
      reliability control, not only as a technical optimisation.</p>
  </section>

  <section class="stack">
    <h2>What is in scope — and what is not</h2>
    <div class="grid grid--3">
      <div class="card stack"><p class="eyebrow">Core</p>
        <p>Methods applied after training that modify parameters, inference
           context, or outputs — fine-tuning, PEFT, alignment, RAG, knowledge
           editing.</p></div>
      <div class="card stack"><p class="eyebrow">Boundary extension</p>
        <p>Training-time data-pipeline strategies applied to an existing model
           as an adaptation mechanism — augmentation, curriculum learning,
           active learning. Marked pipeline-mediated so their status stays
           visible.</p></div>
      <div class="card stack"><p class="eyebrow">Excluded</p>
        <p>Deployment-layer controls: output guardrails, content moderation,
           watermarking, post-processing, human-in-the-loop review. Also
           foundational learning paradigms and low-level optimisations.</p></div>
    </div>
    <p class="callout callout--warn"><strong>Why the exclusions matter.</strong>
      Deployment-layer controls are excluded because they do not modify the
      model's parameters, inference context, or adaptation pipeline as this
      taxonomy defines them. That is a scope boundary, not a claim of
      regulatory irrelevance.</p>
  </section>

  <section class="stack">
    <h2>Two names, one scope</h2>
    <p><strong>Model adaptation</strong> is the academic umbrella, used when
       discussing technical properties. <strong>Post-training techniques</strong>
       is the industry and regulatory framing, used when the point is that the
       model already exists and may carry obligations. Same
       {tax["meta"]["n_techniques"]} techniques either way.</p>
    <p><a class="btn" href="../explorer/">Browse them all</a>
       <a class="btn" href="../ambiguity/">Why precision matters</a></p>
  </section>
</div>
"""
    return ("concepts/index.html", "Training vs post-training adaptation", body,
            {"depth": 1, "current": "/concepts/",
             "description": "What counts as post-training adaptation, and what does not."})


# ----------------------------------------------------------------- ambiguity

def ambiguity_page(d):
    tax, derived = d["taxonomy"], d["derived"]
    by = {t["slug"]: t for t in tax["techniques"]}
    bs = derived["compute_blind_spot"]
    up = "../"

    def links(slugs):
        return ", ".join(
            f'<a href="{up}techniques/{s}/">{esc(by[s]["name"])}</a>'
            for s in slugs if s in by
        )

    amb = (d["ambiguities"] or {}).get("entries", [])
    amb_html = "".join(
        f"""<div class="card stack">
      <p class="eyebrow">{esc(a["source"])}</p>
      <h3>{esc(a["display"])}</h3>
      <p>{esc(a["fails_to_specify"])}</p>
      <p><strong>The question that resolves it:</strong> {esc(a["question"])}</p>
      <p>{links(a["slugs"])}</p>
    </div>""" for a in amb
    )

    body = f"""
<div class="wrap section stack">
  <h1>Why imprecision has consequences</h1>
  <p style="font-size:var(--step-1)">Vague language about model change is not
     only untidy. It can leave an auditor unable to tell what happened.</p>
  <p class="callout callout--warn reg-claim">{esc(DISCLAIMER)}</p>

  <section class="stack">
    <h2>The gaps the paper identifies</h2>
    <div class="table-scroll"><table>
      <thead><tr><th>Framework</th><th>The gap</th></tr></thead>
      <tbody>
        <tr><td>EU AI Act</td><td class="reg-claim">Treats substantial
          modification as potentially triggering reclassification, yet offers no
          technical definition of what fine-tuning is as distinct from other
          modifications.</td></tr>
        <tr><td>EU AI Act — GPAI</td><td class="reg-claim">A compute-based
          threshold may fail to capture low-compute techniques that
          substantially alter behaviour.</td></tr>
        <tr><td>FDA PCCP</td><td class="reg-claim">Audits of submissions reveal
          a persistent lack of transparency and omission of technical detail
          needed to evaluate model change.</td></tr>
        <tr><td>EU MDR / IVDR</td><td class="reg-claim">A statement that a model
          &ldquo;was updated&rdquo; may be insufficient where documentation calls
          for mechanism, persistence, and scope.</td></tr>
      </tbody>
    </table></div>
  </section>

  <section class="stack">
    <h2>The compute-threshold blind spot</h2>
    <p><strong>{bs["total"]} of {len(tax["techniques"])}</strong> techniques
       operate wholly or partly outside gradient-compute thresholds.
       <strong>{len(bs["exclusive"])} are exclusively non-gradient</strong> and
       <strong>{len(bs["dual"])} are dual-mechanism</strong>, gradient-based in
       some implementations and not others.</p>
    <div class="grid grid--2">
      <div class="card stack"><p class="eyebrow">Exclusively non-gradient</p>
        <p>{links(bs["exclusive"])}</p></div>
      <div class="card stack"><p class="eyebrow">Dual-mechanism</p>
        <p>{links(bs["dual"])}</p></div>
    </div>
    <p class="provenance">Derived from D1 mechanism groups II and III</p>
    <p><a class="btn" href="{up}explorer/">Reproduce this filter</a></p>
  </section>

  <section class="stack">
    <h2>Four phrases that hide the change</h2>
    <div class="grid grid--2">{amb_html}</div>
    <p><a class="btn" href="{up}disambiguate/">Work through a term</a></p>
  </section>

  <section class="stack">
    <h2>The same change, described two ways</h2>
    <div class="grid grid--2">
      <div class="card stack">
        <p class="eyebrow">Before — standard prose</p>
        <p><q>Update v2.1: the model was fine-tuned on recent hospital data to
          improve performance and incorporate new clinical guidelines.</q></p>
        <p style="color:var(--text-muted)">An auditor cannot tell whether base
          weights changed (D5), whether the change is transient or permanent
          (D4), or whether the guidelines were learned parametrically or
          retrieved at inference (D1).</p>
      </div>
      <div class="card stack">
        <p class="eyebrow">After — two named layers</p>
        <p><strong>Layer 1 — parameter update.</strong> PEFT applied to the base
          model, for drift remediation, on small labelled data, ad-hoc
          permanent, modular scope, LLM.</p>
        <p><strong>Layer 2 — inference update.</strong> Retrieval corpus updated
          with new guidelines: context injection, knowledge update, external
          corpus, version-persistent, input/output space, LLM.</p>
        <p style="color:var(--text-muted)">The base weights are recorded as
          intended to remain frozen, and the adapter and retrieval artifacts are
          identified as the modified components.</p>
      </div>
    </div>
    <p><a class="btn btn--solid" href="{up}wizard/">Describe your own change</a></p>
  </section>

  <section class="stack">
    <h2>Mathematically similar, documented differently</h2>
    <p class="reg-claim">Task arithmetic and task-vector-negation unlearning both
       produce lineage-opaque derived artifacts. Naming both by their mechanism
       can support consistent documentation of operations that are
       mathematically alike.</p>
  </section>

  <section class="stack">
    <h2>No single dimension decides</h2>
    <p class="reg-claim">Regulatory consequence depends on intended use, risk
      class, and the applicable pathway in addition to the six-dimensional
      profile. The same retrieval architecture may carry different consequences
      in customer support and in clinical decision support. The taxonomy names
      the intervention; it does not classify it legally.</p>
  </section>
</div>
"""
    return ("ambiguity/index.html", "Why precision matters", body,
            {"depth": 1, "current": "/ambiguity/",
             "description": "The regulatory consequences of imprecise language about model change."})


# ---------------------------------------------------------------- governance

def governance_page(d):
    dims = d["dimensions"]
    up = "../"
    dim_rows = "".join(
        f'<tr><td><strong>{k.upper()}</strong> {esc(dims[k]["name"])}</td>'
        f'<td>{esc(dims[k]["question"])}</td></tr>' for k in DIM_KEYS
    )
    body = f"""
<div class="wrap section stack">
  <h1>Mapping to governance frameworks</h1>
  <p class="callout callout--warn reg-claim">{esc(DISCLAIMER)}</p>

  <section class="stack">
    <h2>What each dimension can document</h2>
    <div class="table-scroll"><table>
      <thead><tr><th>Dimension</th><th>Question it answers</th></tr></thead>
      <tbody>{dim_rows}</tbody>
    </table></div>
  </section>

  <section class="stack">
    <h2>Four frameworks</h2>
    <div class="grid grid--2">
      <div class="card stack"><h3>NIST AI RMF</h3>
        <p class="reg-claim">Its lifecycle stages and core functions may be
          mapped to adaptation goals: the operate-and-monitor stage invokes
          drift remediation and continual adaptation, which can be separated by
          persistence (D4) and structural scope (D5). Data-stage obligations
          connect to D3.</p></div>
      <div class="card stack"><h3>EU AI Act</h3>
        <p class="reg-claim">Risk-based requirements and post-market obligations
          may be informed by goal, persistence, and scope. A compute threshold
          can identify large fine-tuning events but may not capture low-compute
          interventions that materially alter behaviour. Derived artifacts with
          fused composition may heighten the need for provenance
          documentation.</p></div>
      <div class="card stack"><h3>EU MDR / IVDR</h3>
        <p class="reg-claim">Post-market surveillance obligations may draw on
          D1, D4, and D5 for technical documentation, and on D2 and D3 for
          benefit-risk and clinical evaluation. A change driven by drift
          remediation can be distinguished from one driven by task
          specialisation even where mechanism and persistence are
          identical.</p></div>
      <div class="card stack"><h3>FDA PCCP</h3>
        <p class="reg-claim">Modification description may map to D1, D4, D5 and
          D6; the modification protocol to D3 plus separately stated validation
          criteria; impact assessment to D2 and D4 alongside intended-purpose
          analysis conducted outside this framework.</p></div>
    </div>
  </section>

  <section class="stack">
    <h2>Start from a technique</h2>
    <p>Every technique page carries its full profile, so the documentation
       dimensions above can be read off directly.</p>
    <p><a class="btn" href="{up}explorer/">Find a technique</a>
       <a class="btn" href="{up}wizard/">Describe a change</a>
       <a class="btn" href="{up}ambiguity/">Why this matters</a></p>
  </section>
</div>
"""
    return ("governance/index.html", "Governance mapping", body,
            {"depth": 1, "current": "/governance/",
             "description": "How the six dimensions map to AI governance documentation."})


# ------------------------------------------------------------------- compare

def compare_page(d):
    tax = d["taxonomy"]
    opts = "".join(
        f'<option value="{esc(t["slug"])}">{esc(t["name"])}</option>'
        for t in tax["techniques"]
    )
    body = f"""
<div class="wrap section stack">
  <h1>Compare techniques</h1>
  <p>Pick two to four. Dimensions where they share no value are what actually
     separates them; dimensions that merely overlap are reported separately.</p>
  <div class="grid grid--2">
    <label>First <select id="sel-a">{opts}</select></label>
    <label>Second <select id="sel-b">{opts}</select></label>
  </div>
  <div id="compare-out" class="stack"></div>
</div>
"""
    return ("compare/index.html", "Compare", body,
            {"depth": 1, "current": "/compare/", "scripts": ("compare.js",),
             "description": "Compare six-dimensional profiles side by side."})


# --------------------------------------------------------------- disambiguate

def disambiguate_page(d):
    tax = d["taxonomy"]
    by = {t["slug"]: t for t in tax["techniques"]}
    up = "../"
    entries = (d["ambiguities"] or {}).get("entries", [])
    cards = []
    for a in entries:
        opts = "".join(
            f'<li><a href="{up}techniques/{s}/"><strong>{esc(by[s]["name"])}</strong></a>'
            f' — {esc(by[s]["summary_editorial"])}</li>'
            for s in a["slugs"] if s in by
        )
        cards.append(f"""
<section class="card stack" id="{esc(a['term'].replace(' ', '-'))}">
  <p class="eyebrow">{esc(a['source'])}</p>
  <h2>{esc(a['display'])}</h2>
  <p>{esc(a['fails_to_specify'])}</p>
  <p class="callout"><strong>Ask:</strong> {esc(a['question'])}</p>
  <ul class="stack">{opts}</ul>
  <p><a href="{up}compare/?t={','.join(a['slugs'][:2])}">Compare these profiles &rarr;</a></p>
</section>""")
    body = f"""
<div class="wrap section stack">
  <h1>One word, several meanings</h1>
  <p style="font-size:var(--step-1)">These are the terms the paper singles out
     as genuinely ambiguous. Each collapses techniques with different profiles.</p>
  {''.join(cards)}
</div>
"""
    return ("disambiguate/index.html", "Terminology", body,
            {"depth": 1, "current": "/disambiguate/",
             "description": "Ambiguous adaptation terms and the questions that resolve them."})


# -------------------------------------------------------------------- wizard

def wizard_page(d):
    dims = d["dimensions"]
    def opts(key):
        return "".join(
            f'<label class="opt"><input type="radio" name="{key}" '
            f'value="{esc(c["slug"])}"> <span>{esc(c["label"])}</span></label>'
            for c in dims[key]["categories"]
        )
    body = f"""
<div class="wrap section stack">
  <h1>Describe a change</h1>
  <p style="font-size:var(--step-1)">Answer in the order the paper suggests:
     what model, then why, then what data you had.</p>

  <p class="callout callout--warn reg-claim">{esc(DISCLAIMER)}</p>

  <section class="stack">
    <h2>1 · What model type?</h2>
    <p class="provenance">The only step that removes candidates</p>
    <div class="optgrid">{opts("d6")}</div>
  </section>

  <section class="stack">
    <h2>2 · What was the goal?</h2>
    <p class="provenance">Ranks candidates — never eliminates them</p>
    <div class="optgrid">{opts("d2")}</div>
  </section>

  <section class="stack">
    <h2>3 · What data did you have?</h2>
    <p class="provenance">Ranks candidates — never eliminates them</p>
    <div class="optgrid">{opts("d3")}</div>
  </section>

  <p class="callout"><strong>None of these?</strong> If your change is an output
     guardrail, a moderation filter, a watermark, or post-processing, it sits
     outside this taxonomy by design.
     <a href="../concepts/#scope">See what is in scope</a>.</p>

  <section class="stack">
    <h2>Candidates</h2>
    <p id="wizard-count" aria-live="polite" class="provenance">Choose a model type to begin.</p>
    <div id="wizard-results" class="stack"></div>
  </section>

  <section class="stack" id="wizard-output" hidden>
    <h2>Your profile</h2>
    <div id="wizard-profile"></div>
    <h3>For a change log</h3>
    <pre id="wizard-prose"></pre>
    <h3>As JSON</h3>
    <pre id="wizard-json"></pre>
  </section>
</div>
"""
    return ("wizard/index.html", "Classify a change", body,
            {"depth": 1, "current": "/wizard/", "scripts": ("wizard.js",),
             "description": "Name a model change with a six-dimensional profile."})


# ----------------------------------------------------------------------- map

def map_page(d):
    tax, derived, dims = d["taxonomy"], d["derived"], d["dimensions"]
    rels = (d["relations"] or {}).get("relations", [])
    up = "../"
    tiers = [c["slug"] for c in dims["d6"]["categories"]]
    order = ["ml", "dl", "fm", "llm", "mllm"]
    tiers = [t for t in order if t in tiers]

    superseded = {r["from"] for r in rels if r["type"] == "supersession"}

    rungs, seen = [], set()
    for tier in tiers:
        here = [t for t in tax["techniques"] if tier in t["d6"]]
        new = [t for t in here if t["slug"] not in seen]
        gone = [t for t in here if t["slug"] in superseded and tier in ("llm", "mllm")]
        seen |= {t["slug"] for t in here}
        label = next(c["label"] for c in dims["d6"]["categories"] if c["slug"] == tier)
        rungs.append(f"""
<div class="card stack" data-tier="{esc(tier.upper())}">
  <p class="eyebrow">{esc(tier.upper())} · {esc(label)}</p>
  <p><strong>{len(here)}</strong> techniques available</p>
  <p><span class="provenance">New at this tier ({len(new)})</span><br>
    {', '.join(f'<a href="{up}techniques/{t["slug"]}/">{esc(t["name"])}</a>' for t in new) or '<em>none</em>'}</p>
  {'<p><span class="provenance">Superseded here</span><br>' +
   ', '.join(f'<a href="{up}techniques/{t["slug"]}/">{esc(t["name"])}</a>' for t in gone) + '</p>'
   if gone else ''}
</div>""")

    sil = derived["silhouette"]
    body = f"""
<div class="wrap section stack">
  <h1>How the taxonomy is shaped</h1>

  <section class="stack">
    <h2>The model-tier ladder</h2>
    <p>Moving down the hierarchy adds techniques without removing them — except
       where a technique is superseded by a more general alternative. Supersession
       is not binary: a superseded technique often remains technically available.</p>
    <div class="grid grid--2">{''.join(rungs)}</div>
    <p class="provenance">Computed from D6 membership and curated supersession relations</p>
  </section>

  <section class="stack">
    <h2>Do the families hold together?</h2>
    <p>Not really — and the paper says so. Measuring how well the nine
       navigational families separate in profile space gives a silhouette of
       <strong>{sil["raw_gower_all"]:+.4f}</strong> across all rows, or
       <strong>{sil["raw_gower_post_training_only"]:+.4f}</strong> over the
       post-training techniques alone. Both are near zero; anything below about
       0.2 indicates no meaningful clustering.</p>
    <p class="callout">This is the expected result. The families are
       <strong>navigational groupings to aid discovery</strong>, not validated
       statistical clusters. Techniques share one anchor dimension while
       differing on others, which is exactly why a single axis cannot hold
       them.</p>
    <p class="provenance">Computed from the taxonomy data</p>
  </section>

  <section class="stack">
    <h2>Similarity projection</h2>
    <div class="placeholder">
      <p class="eyebrow">Coordinates not yet exported</p>
      <p>The analysis reproduces the published silhouette scores exactly, so
         the projection is settled — but its coordinates live only inside the
         notebook. An interactive version goes here once they are exported.</p>
    </div>
    <p>Pairwise distances are independent of the projection and are shown on
       every technique page under <em>nearest profiles</em>.</p>
  </section>
</div>
"""
    return ("map/index.html", "Structure", body,
            {"depth": 1, "current": "/map/",
             "description": "Model-tier inheritance and how coherent the families are."})


# ---------------------------------------------------------------- glossary

def glossary_page(d):
    gls = (d["glossary"] or {}).get("entries", [])
    rows = "".join(
        f'<tr class="glossary-entry" data-term="{esc((e["short"] + " " + e["long"]).lower())}">'
        f'<td><strong>{esc(e["short"])}</strong></td><td>{esc(e["long"])}</td></tr>'
        for e in gls
    )
    body = f"""
<div class="wrap section stack">
  <h1>Glossary</h1>
  <p>{len(gls)} abbreviations used across the taxonomy.</p>
  <label class="visually-hidden" for="gq">Filter</label>
  <input id="gq" type="search" placeholder="Filter…" style="padding:var(--sp-2);
    border:1px solid var(--border);border-radius:var(--radius);
    background:var(--bg);color:var(--text);width:min(100%,24rem)">
  <p class="provenance" id="gcount" aria-live="polite">{len(gls)} entries</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Abbreviation</th><th>Expansion</th></tr></thead>
    <tbody id="gbody">{rows}</tbody>
  </table></div>
</div>
"""
    return ("glossary/index.html", "Glossary", body,
            {"depth": 1, "current": "/glossary/", "scripts": ("glossary.js",),
             "description": "Abbreviations used across the taxonomy."})


# -------------------------------------------------------------------- data

def data_page(d):
    tax = d["taxonomy"]
    disc = (d["discrepancies"] or {}).get("entries", [])
    disc_html = "".join(
        f'<li><strong>{esc(e["slug"])}</strong> / {esc(e["dimension"]).upper()} — '
        f'resolved in favour of the manuscript. {esc(e["reason"])}</li>'
        for e in disc
    )
    body = f"""
<div class="wrap section stack">
  <h1>Download the data</h1>
  <p>The taxonomy is published as data, not only as a website. Every profile is
     machine-extracted from the manuscript and cross-checked against the
     authors' analysis notebook.</p>

  <div class="grid grid--2">
    <div class="card stack"><h3>taxonomy.json</h3>
      <p>{len(tax["techniques"])} records with full six-dimensional profiles,
         definitions, and provenance.</p>
      <a class="btn" href="../data/taxonomy.json" download>Download JSON</a></div>
    <div class="card stack"><h3>taxonomy.csv</h3>
      <p>The same table flattened for spreadsheets; set-valued cells joined
         with <code>|</code>.</p>
      <a class="btn" href="../data/taxonomy.csv" download>Download CSV</a></div>
    <div class="card stack"><h3>dimensions.json</h3>
      <p>All six vocabularies with definitions and meta-groups.</p>
      <a class="btn" href="../data/dimensions.json" download>Download</a></div>
    <div class="card stack"><h3>derived.json</h3>
      <p>Gower distances, nearest profiles, separators, silhouette.</p>
      <a class="btn" href="../data/derived.json" download>Download</a></div>
  </div>

  <section class="stack">
    <h2>How it was verified</h2>
    <ul>
      <li>All <strong>{tax["meta"]["crosscheck"]["cells_compared"]}</strong>
        profile cells compared between the manuscript table and the authors'
        notebook; <strong>{tax["meta"]["crosscheck"]["cells_identical"]}</strong>
        agree.</li>
      <li>Every dimension value is checked against its published vocabulary.</li>
      <li>Nothing is re-typed by hand.</li>
    </ul>
    {'<p><strong>Adjudicated differences</strong></p><ul>' + disc_html + '</ul>' if disc_html else ''}
  </section>

  <section class="stack">
    <h2>Using the identifiers</h2>
    <p>The <code>slug</code> is the stable identifier — use it for
       cross-references and URLs. Row numbers appear in the paper but depend on
       how the document is built, so they are display metadata only.</p>
    <p>Every dimension value is an <strong>array</strong>, including
       single-valued ones. Set-valued cells are the normal case.</p>
  </section>

  <section class="stack">
    <h2>Citing the dataset</h2>
    <pre>Afdideh, F., Seoane, F., &amp; Abtahi, F. (2026).
A Six-Dimensional Taxonomy of Post-Training Adaptation Techniques
with Applications in AI Governance. {ARXIV_ID}</pre>
    <p>Data and extracted prose are CC BY 4.0; code is MIT.</p>
  </section>
</div>
"""
    return ("data/index.html", "Data", body,
            {"depth": 1, "current": "/data/",
             "description": "Download the taxonomy as JSON and CSV."})


# --------------------------------------------------------------------- 404

def notfound_page(d):
    body = """
<div class="wrap section stack">
  <h1>No such page</h1>
  <p>That address does not exist here.</p>
  <p><a class="btn" href="/">Home</a>
     <a class="btn" href="/explorer/">Explorer</a>
     <a class="btn" href="/glossary/">Glossary</a></p>
</div>
"""
    return ("404.html", "Not found", body, {"depth": 0})
