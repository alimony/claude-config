# Pandoc: Citations & Bibliography

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## Quick Start

```bash
# Basic citation processing
pandoc --citeproc input.md -o output.html

# With explicit bibliography and style
pandoc --citeproc --bibliography=refs.bib --csl=ieee.csl input.md -o output.pdf
```

You need three things:
1. A document with citation syntax (`[@key]`)
2. A bibliography source (`.bib` file or inline YAML)
3. Optionally, a CSL style file (defaults to Chicago author-date)

## Citation Syntax

### Basic Citations

```markdown
Blah blah [@doe2020].                 → (Doe 2020)
Blah blah [@doe2020, p. 33].         → (Doe 2020, 33)
Blah blah [@doe2020; @smith2019].    → (Doe 2020; Smith 2019)
```

### In-Text (Author Visible)

```markdown
@doe2020 says blah.                   → Doe (2020) says blah.
@doe2020 [p. 33] says blah.          → Doe (2020, 33) says blah.
```

### Suppress Author

```markdown
Doe says blah [-@doe2020].           → Doe says blah (2020).
```

### Prefixes and Suffixes

```markdown
[see @doe2020, pp. 33-35; also @smith2019, chap. 1]
→ (see Doe 2020, 33–35; also Smith 2019, chap. 1)
```

### Multiple Citations

```markdown
[@doe2020; @smith2019; @jones2018]
→ (Doe 2020; Jones 2018; Smith 2019)
```

## Bibliography Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| BibLaTeX | `.bib` | Default interpretation for `.bib` |
| BibTeX | `.bibtex` | Use `.bibtex` to force BibTeX interpretation |
| CSL JSON | `.json` | Native citeproc format |
| CSL YAML | `.yaml` | Human-readable alternative |
| RIS | `.ris` | Common export format |

**Note:** `.bib` files are interpreted as BibLaTeX by default. Use `.bibtex` extension to force BibTeX.

## Specifying Bibliography Data

### Via YAML Metadata

```yaml
---
title: My Paper
bibliography: refs.bib
---
```

### Via Command Line

```bash
pandoc --citeproc --bibliography=refs.bib input.md -o output.pdf

# Multiple bibliography files
pandoc --citeproc --bibliography=main.bib --bibliography=extra.bib input.md -o output.pdf
```

### Multiple Bibliographies in YAML

```yaml
---
bibliography:
  - primary.bib
  - secondary.bib
---
```

### Inline References (No External File)

```yaml
---
references:
- type: article-journal
  id: WatsonCrick1953
  author:
  - family: Watson
    given: J. D.
  - family: Crick
    given: F. H. C.
  issued:
    date-parts:
    - - 1953
      - 4
      - 25
  title: 'Molecular structure of nucleic acids: a structure for
    deoxyribose nucleic acid'
  container-title: Nature
  volume: 171
  issue: 4356
  page: 737-738
  DOI: 10.1038/171737a0
---
```

If both external bibliography and inline references are provided, both are used. Inline references take precedence on conflicting IDs.

### Converting Between Bibliography Formats

```bash
# BibLaTeX → CSL JSON
pandoc chem.bib -s -f biblatex -t csljson -o chem.json

# BibLaTeX → YAML with inline references
pandoc chem.bib -s -f biblatex -t markdown -o chem.yaml

# CSL YAML → BibLaTeX
pandoc chem.yaml -s -f markdown -t biblatex -o chem.bib

# Render a formatted bibliography directly
pandoc chem.bib -s --citeproc -o chem.html
pandoc chem.bib -s --citeproc -o chem.pdf
```

## Citation Styles (CSL)

```bash
# Use a specific CSL style
pandoc --citeproc --csl=ieee.csl input.md -o output.pdf
```

Or in YAML metadata:

```yaml
---
csl: chicago-fullnote-bibliography.csl
# Alternative key name:
# citation-style: chicago-fullnote-bibliography.csl
---
```

- **Default style:** Chicago Manual of Style author-date
- **Override default:** Copy a CSL file to `default.csl` in your user data directory
- **Find styles:** [Zotero Style Repository](https://www.zotero.org/styles)
- **CSL spec:** [Citation Style Language](https://docs.citationstyles.org/en/stable/specification.html)

### Journal Abbreviations

```bash
pandoc --citeproc --citation-abbreviations=abbrevs.json input.md -o output.pdf
```

Format of `abbrevs.json`:

```json
{
  "default": {
    "container-title": {
      "Lloyd's Law Reports": "Lloyd's Rep",
      "Estates Gazette": "EG"
    }
  }
}
```

## Citations in Note Styles

When using footnote-based citation styles, **don't insert footnotes manually** — pandoc creates them automatically:

```markdown
Blah blah [@foo, p. 33].
```

With a note style, this produces a footnote automatically. Pandoc handles spacing and punctuation placement.

**Citations inside regular footnotes:**

```markdown
[^1]: Some studies [@foo; @bar, p. 33] show results.
For a survey, see @baz [chap. 1].
```

- Normal citations in footnotes: rendered in parentheses
- In-text citations in footnotes: rendered without parentheses

## Placement of the Bibliography

**Default:** End of the document.

**Custom placement** — use a div with id `refs`:

```markdown
# References

::: {#refs}
:::

# Appendix

Content after bibliography...
```

**Suppress bibliography entirely:**

```yaml
---
suppress-bibliography: true
---
```

**Section heading for bibliography:**

```yaml
---
reference-section-title: "Works Cited"
---
```

Or place the heading manually:

```markdown
Last paragraph of the document...

# References
```

The bibliography inserts after this heading. The `unnumbered` class is added automatically.

**Bibliography in a template variable:**

```yaml
---
refs: |
  ::: {#refs}
  :::
---
```

Then use `$refs$` in your template.

## Including Uncited Items

**Specific items:**

```yaml
---
nocite: |
  @item1, @item2
---
```

**All items in the bibliography:**

```yaml
---
nocite: |
  @*
---
```

## Other Relevant Metadata Fields

| Field | Effect | Default |
|-------|--------|---------|
| `link-citations` | Hyperlink citations to bibliography entries | `false` |
| `link-bibliography` | Hyperlink DOIs/URLs in bibliography | `true` |
| `lang` | Localization (labels, quotes, sorting) | System locale |
| `notes-after-punctuation` | Move footnote refs after punctuation | `true` for note styles |
| `suppress-bibliography` | Don't generate bibliography | `false` |
| `reference-section-title` | Heading text for bibliography section | None |

### Language/Sorting Examples

```yaml
---
lang: en-US                    # American English
lang: zh-u-co-pinyin           # Chinese with Pinyin collation
lang: es-u-co-trad             # Spanish traditional collation
lang: fr-u-kb                  # French backwards accent sorting
lang: en-US-u-kf-upper         # Uppercase sorts before lowercase
---
```

## LaTeX-Native Citation Rendering

For LaTeX output, you can use natbib or biblatex instead of citeproc:

```bash
# natbib (requires BibTeX .bib file)
pandoc --natbib --bibliography=refs.bib input.md -o output.tex

# biblatex (requires BibLaTeX .bib file)
pandoc --biblatex --bibliography=refs.bib input.md -o output.tex
```

These produce LaTeX citation commands (`\cite`, `\citep`, `\textcite`, etc.) instead of rendered text. Run BibTeX/Biber separately to resolve citations.

## Capitalization Rules

### BibTeX/BibLaTeX Files

- English titles: **title case**
- Non-English titles: **sentence case** (set `langid` field)
- Protect proper names with braces: `title = {My Dinner with {Andre}}`
- Protect lowercase/camelCase: `title = {Dispersion on the {nm} Scale}`

### CSL Files (JSON/YAML)

- All titles: **sentence case**
- Use `language` field for non-English titles
- Protect words: `the <span class="nocase">nm</span> scale`

## Complete Working Example

```yaml
---
title: My Research Paper
author: Jane Doe
date: 2024-01-15
bibliography: references.bib
csl: apa.csl
link-citations: true
nocite: |
  @background-reading
---

# Introduction

The field has advanced significantly [@smith2020; @jones2021].
As @doe2019 [p. 42] noted, "this is important."

# Methods

We followed the protocol [-@standard2018].

# References

::: {#refs}
:::
```

```bash
pandoc --citeproc paper.md -o paper.pdf
```

## Common Pitfalls

- **`.bib` vs `.bibtex`:** Pandoc treats `.bib` as BibLaTeX. If your file is BibTeX, rename to `.bibtex`
- **Missing `--citeproc`:** Without this flag, citation syntax is left unprocessed
- **Title capitalization:** BibTeX titles must be in title case with proper names braced; CSL titles must be in sentence case
- **Note style + manual footnotes:** Don't add footnotes manually with note citation styles — pandoc creates them
- **Bibliography placement:** Without a `{#refs}` div, the bibliography goes at the very end of the document
