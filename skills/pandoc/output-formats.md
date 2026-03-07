# Pandoc: Output Formats & Special Features

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## EPUB Creation

### Basic Usage

```bash
pandoc input.md -o book.epub
pandoc --epub-cover-image=cover.jpg input.md -o book.epub
```

### EPUB Metadata

Specify via YAML metadata block or `--epub-metadata` (Dublin Core XML):

```yaml
---
title:
- type: main
  text: My Book
- type: subtitle
  text: An Investigation
creator:
- role: author
  text: John Smith
- role: editor
  text: Sarah Jones
identifier:
- scheme: DOI
  text: doi:10.234234.234/33
publisher: My Press
rights: "\u00A9 2007 John Smith, CC BY-NC"
date: 2024-01-15
lang: en-US
subject:
- text: Science
  authority: BISAC
cover-image: cover.jpg
css: epub-style.css
page-progression-direction: ltr
---
```

**Key metadata fields:**

| Field | Format |
|-------|--------|
| `identifier` | String or `{scheme, text}`. Schemes: ISBN-10, ISBN-13, DOI, URN, etc. |
| `title` | String or `{type, text}`. Types: main, subtitle, short, collection, edition |
| `creator` | String or `{role, file-as, text}`. Roles: author, editor, etc. (MARC relators) |
| `contributor` | Same format as creator |
| `date` | YYYY-MM-DD (only year required) |
| `lang` | BCP 47 language tag |
| `cover-image` | Path to cover image file |
| `css` | Path to CSS stylesheet (replaces `stylesheet`) |
| `belongs-to-collection` | Collection/series name |
| `group-position` | Position within collection |

### Accessibility Metadata

```yaml
---
accessModes: ["textual"]
accessModeSufficient: ["textual"]
accessibilityHazards: ["none"]
accessibilityFeatures:
  - alternativeText
  - readingOrder
  - structuralNavigation
  - tableOfContents
---
```

### The epub:type Attribute

Mark chapters with EPUB3 semantic types:

```markdown
# My Prologue {epub:type=prologue}
```

| epub:type | Body wrapper |
|-----------|-------------|
| prologue, abstract, acknowledgments, copyright-page, dedication, foreword, preface, titlepage | frontmatter |
| appendix, colophon, bibliography, index | backmatter |
| (anything else) | bodymatter |

### Linked Media

By default, pandoc downloads and embeds all media. For external links:

```html
<audio controls="1">
  <source src="https://example.com/music.mp3"
          data-external="1" type="audio/mpeg">
</audio>
```

For images in Markdown: `![img](url){external=1}`

### EPUB Styling

```bash
# Use custom CSS
pandoc --css=my-styles.css input.md -o book.epub

# View default EPUB CSS
pandoc --print-default-data-file epub.css
```

Set `document-css: true` for pandoc's more opinionated default styling.

### iBooks-Specific Metadata

```yaml
---
ibooks:
  version: 1.3.4
  specified-fonts: true
  ipad-orientation-lock: portrait-only
  binding: true
  scroll-axis: vertical
---
```

## Chunked HTML

Split a document into multiple linked HTML pages:

```bash
# Produce a zip archive
pandoc -t chunkedhtml input.md -o output.zip

# Unpack into a directory (directory must not exist)
pandoc -t chunkedhtml input.md -o output-dir

# Control split depth
pandoc -t chunkedhtml --split-level=2 input.md -o output.zip
```

**Features:**
- Internal links automatically adjusted
- Images under working directory incorporated
- Navigation links added
- `sitemap.json` included with hierarchical structure
- TOC on top page by default (set `toc` variable for all pages)
- Customize navigation via template

## Jupyter Notebooks

### Creating Notebooks

```bash
pandoc input.md -o notebook.ipynb
```

Pandoc infers notebook structure:
- Code blocks with class `code` become code cells
- Other content becomes Markdown cells
- Images in Markdown cells become attachments

```yaml
---
title: My Notebook
jupyter:
  nbformat: 4
  nbformat_minor: 5
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---
```

### Reading Notebooks

```bash
pandoc notebook.ipynb -o output.md

# Control how cell outputs are handled
pandoc --ipynb-output=all notebook.ipynb -o output.md    # all outputs
pandoc --ipynb-output=none notebook.ipynb -o output.md   # no outputs
pandoc --ipynb-output=best notebook.ipynb -o output.md   # best format (default)
```

## Vimdoc

Create Vim help files:

```bash
pandoc -t vimdoc input.md -o plugin-name.txt
```

## Syntax Highlighting

### Built-in Highlighting

Pandoc uses the [skylighting](https://github.com/jgm/skylighting) library. Supported in: HTML, EPUB, Docx, Ms, Man, Typst, LaTeX/PDF.

```bash
# List supported languages
pandoc --list-highlight-languages

# List available styles
pandoc --list-highlight-styles
```

### Choosing a Style

```bash
# Use a built-in style
pandoc --highlight-style=tango input.md -o output.html

# Disable highlighting
pandoc --highlight-style=none input.md -o output.html

# Use format-native highlighting
pandoc --highlight-style=idiomatic input.md -o output.html
```

Built-in styles: `pygments` (default), `tango`, `espresso`, `zenburn`, `kate`, `monochrome`, `breezedark`, `haddock`.

### Custom Themes

```bash
# Export a theme as JSON for customization
pandoc -o my.theme --print-highlight-style pygments

# Edit my.theme, then use it
pandoc --highlight-style=my.theme input.md -o output.html
```

**Gotcha:** Theme JSON files must be UTF-8 without BOM.

### Custom Syntax Definitions

```bash
# Load a KDE-style XML syntax definition
pandoc --syntax-definition=my-language.xml input.md -o output.html
```

Find definitions at [KDE's syntax-highlighting repo](https://github.com/KDE/syntax-highlighting/tree/master/data/syntax).

### Idiomatic Highlighting

`--highlight-style=idiomatic` uses the output format's native highlighter:

| Format | Effect |
|--------|--------|
| reveal.js | Uses reveal.js highlight plugin (set `highlightjs-theme` variable) |
| Typst | Uses Typst built-in highlighting (also the default) |
| LaTeX | Uses `listings` package (note: doesn't support multi-byte encoding natively) |
| Others | Same as `default` |

## Custom Styles (Docx, ODT, ICML)

### Output: Applying Custom Styles

Use `custom-style` attribute on divs and spans:

```markdown
[Get out]{custom-style="Emphatically"}, he said.

::: {custom-style="Poetry"}
| A Bird came down the Walk---
| He did not know I saw---
:::
```

- Styles inherit from Normal (docx) or Default Paragraph Style (odt)
- If style exists in reference doc, pandoc uses it as-is
- Use with pandoc filters for advanced style mapping

### Input: Preserving Styles from Docx

```bash
# Default: styles converted to pandoc elements
pandoc input.docx -f docx -t markdown

# With +styles: preserves custom-style attributes
pandoc input.docx -f docx+styles -t markdown
```

With `+styles`, output preserves `custom-style` divs and spans:

```markdown
::: {custom-style="First Paragraph"}
This is some text.
:::

::: {custom-style="Body Text"}
This is text with an [emphasized]{custom-style="Emphatic"} text style.
:::
```

This enables round-tripping: read docx → modify → write docx while preserving styles.

## Accessible PDFs and PDF Standards

### Overview

PDF is not accessible by default. Tagged PDFs add semantic information. PDF/A and PDF/UA define standards for archiving and accessibility.

**Note:** Standard compliance depends on many factors (e.g., colorspace of embedded images). External tools are needed to verify compliance.

### LaTeX (LuaLaTeX)

```bash
# PDF/UA-2
pandoc -V pdfstandard=ua-2 --pdf-engine=lualatex doc.md -o doc.pdf

# Multiple standards
pandoc --pdf-engine=lualatex doc.md -o doc.pdf
```

```yaml
---
pdfstandard:
  - ua-2
  - a-4f
---
```

Requires LuaLaTeX in TeX Live 2025+ with LaTeX kernel 2025-06-01 or newer. PDF version is inferred automatically.

### ConTeXt

ConTeXt always produces tagged PDFs. Enable the `tagging` extension for optimized tagging:

```bash
pandoc -t context+tagging doc.md -o doc.pdf
```

### WeasyPrint

Experimental support since version 57:

```bash
pandoc --pdf-engine=weasyprint --pdf-engine-opt=--pdf-variant=pdf/ua-1 doc.md -o doc.pdf
```

### Prince XML

```bash
pandoc --pdf-engine=prince --pdf-engine-opt=--tagged-pdf doc.md -o doc.pdf
```

### Typst

Typst 0.12+ supports PDF/A-2b:

```bash
pandoc --pdf-engine=typst --pdf-engine-opt=--pdf-standard=a-2b doc.md -o doc.pdf
```

### Word Processors

Pandoc can produce `.docx`/`.odt` that word processors can convert to accessible PDFs:

```bash
pandoc doc.md -o doc.docx
# Then use Word/LibreOffice to export as tagged PDF
```

## PDF Engine Comparison

| Engine | Via | Best For | Accessibility |
|--------|-----|----------|---------------|
| pdflatex | LaTeX | Standard academic docs | Tagged (LuaLaTeX only) |
| xelatex | LaTeX | Unicode/custom fonts | Tagged (LuaLaTeX only) |
| lualatex | LaTeX | Full Unicode + tagging | PDF/A, PDF/UA |
| context | ConTeXt | Advanced typography | Always tagged |
| typst | Typst | Modern, fast | PDF/A-2b |
| weasyprint | HTML→PDF | CSS-styled docs | Experimental |
| prince | HTML→PDF | High-quality CSS→PDF | Yes (commercial) |
| wkhtmltopdf | HTML→PDF | Quick HTML rendering | No |
