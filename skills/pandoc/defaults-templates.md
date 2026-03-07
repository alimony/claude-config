# Pandoc: Defaults Files & Templates

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## Defaults Files

Defaults files let you store pandoc options in YAML. Use `--defaults` or `-d` to load them.

### Basic Usage

```bash
# Load a defaults file
pandoc -d mydefaults input.md -o output.html

# Extension .yaml is added automatically if not present
pandoc -d mydefaults   # looks for mydefaults.yaml

# Searched in: current dir, then defaults/ in data directory
```

### Example Defaults File

```yaml
# mydefaults.yaml
from: markdown+emoji
to: html5
standalone: true
output-file: output.html

# Reader options
shift-heading-level-by: 0
tab-stop: 4
preserve-tabs: false

# Writer options
wrap: auto
columns: 72
toc: true
toc-depth: 3
number-sections: true
highlight-style: tango

# Variables (same as -V)
variables:
  fontsize: 12pt
  geometry: margin=1in
  colorlinks: true
  lang: en-US

# Metadata (same as -M)
metadata:
  title: My Document
  author:
    - Jane Doe
    - John Smith
  date: 2024-01-15

# Include files
include-in-header:
  - header.html
include-before-body:
  - before.html
include-after-body:
  - after.html

# Filters
filters:
  - type: lua
    path: my-filter.lua
  - type: citeproc

# Template
template: custom.html

# CSS
css:
  - style.css

# Citation
bibliography: refs.bib
csl: apa.csl
cite-method: citeproc

# PDF engine
pdf-engine: xelatex
pdf-engine-opts:
  - "-shell-escape"
```

### Field Mapping to CLI Options

| Defaults Field | CLI Equivalent |
|----------------|----------------|
| `from` | `--from` / `-f` |
| `to` | `--to` / `-t` |
| `output-file` | `--output` / `-o` |
| `standalone` | `--standalone` / `-s` |
| `template` | `--template` |
| `variables` | `--variable` / `-V` |
| `metadata` | `--metadata` / `-M` |
| `metadata-files` | `--metadata-file` |
| `toc` | `--toc` |
| `toc-depth` | `--toc-depth` |
| `number-sections` | `--number-sections` / `-N` |
| `wrap` | `--wrap` |
| `columns` | `--columns` |
| `highlight-style` | `--syntax-highlighting` |
| `filters` | `--filter` / `--lua-filter` / `--citeproc` |
| `css` | `--css` |
| `bibliography` | `--bibliography` |
| `csl` | `--csl` |
| `cite-method` | `--citeproc` / `--natbib` / `--biblatex` |
| `pdf-engine` | `--pdf-engine` |
| `pdf-engine-opts` | `--pdf-engine-opt` |
| `include-in-header` | `-H` / `--include-in-header` |
| `include-before-body` | `-B` / `--include-before-body` |
| `include-after-body` | `-A` / `--include-after-body` |
| `resource-path` | `--resource-path` |
| `input-files` | Positional arguments |
| `file-scope` | `--file-scope` |
| `verbosity` | `--verbose` / `--quiet` |
| `fail-if-warnings` | `--fail-if-warnings` |
| `sandbox` | `--sandbox` |
| `extract-media` | `--extract-media` |

### Input Files in Defaults

```yaml
input-files:
  - chapter1.md
  - chapter2.md
  - chapter3.md
```

### Multiple Defaults Files

```bash
# Later defaults override earlier ones
pandoc -d base-settings -d html-settings input.md

# CLI flags override all defaults
pandoc -d mydefaults --toc-depth=2 input.md  # overrides toc-depth from defaults
```

### Cite Method

```yaml
# Use citeproc (default citation processor)
cite-method: citeproc

# Use natbib (LaTeX only, requires bibtex)
cite-method: natbib

# Use biblatex (LaTeX only, requires biber)
cite-method: biblatex
```

## Templates

Templates control the structure of standalone output documents. Pandoc fills template variables with document content and metadata.

### Using Templates

```bash
# Use default template for output format
pandoc -s input.md -o output.html

# Print default template (inspect/customize)
pandoc -D html > my-template.html
pandoc -D latex > my-template.tex

# Use custom template
pandoc -s --template=my-template.html input.md -o output.html
```

Templates are searched in: specified path → `templates/` in data directory.

### Template Syntax

#### Delimiters

Variables are enclosed in `$...$` or `${...}`:

```
$title$
${title}
$author.name$
```

#### Comments

```
$-- This is a comment and won't appear in output
```

#### Interpolated Variables

```
<title>$title$</title>
<meta name="author" content="$author$">
```

**Dot notation for nested fields:**

```
$author.name$
$author.affiliation$
```

#### Conditionals

```
$if(title)$
<h1>$title$</h1>
$endif$

$if(subtitle)$
<h2>$subtitle$</h2>
$else$
<h2>Untitled</h2>
$endif$

$-- Chained conditionals
$if(format)$
Format: $format$
$elseif(type)$
Type: $type$
$else$
Unknown
$endif$
```

#### For Loops

```
$for(author)$
<li>$author$</li>
$endfor$

$-- With separator
$for(author)$$author$$sep$, $endfor$

$-- Nested fields in loop
$for(author)$
  Name: $author.name$, Email: $author.email$
$endfor$
```

#### Partials (Include Other Templates)

```
$-- Include another template file
${ header.html() }

$-- Include with variable as content
${ styles() }
```

#### Nesting

Templates can reference other templates. Partials are searched relative to the main template, then in `templates/` in the data directory.

#### Breakable Spaces

Use `~` for a non-breaking space in templates:

```
$if(date)$Date:~$date$$endif$
```

#### Pipes (Transformations)

Apply transformations to variables:

```
$title/uppercase$          → UPPER CASE
$title/lowercase$          → lower case
$body/chomp$               → Remove trailing newlines
$title/nowrap$             → Prevent wrapping
$date/alpha$               → Alphabetic representation
$items/pairs$              → Key-value pairs from object
$items/first$              → First element
$items/last$               → Last element
$items/rest$               → All but first
$items/allbutlast$         → All but last
$items/length$             → Number of elements
$items/reverse$            → Reverse order
```

**Chaining pipes:**

```
$title/uppercase/nowrap$
```

## Template Variables

### Variables Set Automatically

| Variable | Content |
|----------|---------|
| `body` | Document body |
| `title` | From metadata |
| `author` | From metadata (may be list) |
| `date` | From metadata |
| `lang` | Document language (BCP 47) |
| `dir` | Text direction (ltr/rtl) |
| `toc` | Table of contents (if `--toc`) |
| `table-of-contents` | Same as `toc` |
| `lof` | List of figures (if `--lof`) |
| `lot` | List of tables (if `--lot`) |
| `header-includes` | Content from `--include-in-header` |
| `include-before` | Content from `--include-before-body` |
| `include-after` | Content from `--include-after-body` |
| `sourcefile` | Source filename(s) |
| `outputfile` | Output filename |
| `highlighting-css` | CSS for syntax highlighting |
| `math` | Math rendering code (MathJax/KaTeX script tag) |

### Metadata Variables

Set via YAML frontmatter, `-M`, or `--metadata-file`:

```yaml
---
title: My Document
subtitle: A Subtitle
author:
  - First Author
  - Second Author
date: January 2024
abstract: |
  This is the abstract.
keywords:
  - pandoc
  - markdown
thanks: Funded by grant XYZ
---
```

### Language Variables

```yaml
---
lang: en-US            # BCP 47 language tag
dir: ltr               # Text direction: ltr or rtl
---
```

### Variables for HTML

| Variable | Effect |
|----------|--------|
| `css` | CSS file links |
| `document-css` | Include pandoc's default CSS (true/false) |
| `mainfont` | Sets body font via CSS |
| `fontsize` | Body font size |
| `fontcolor` | Body text color |
| `linkcolor` | Link color |
| `backgroundcolor` | Background color |
| `linestretch` | Line height |
| `maxwidth` | Max content width |

### Variables for HTML Slides

| Variable | Effect |
|----------|--------|
| `revealjs-url` | Base URL for reveal.js files |
| `s5-url` | Base URL for S5 files |
| `slidy-url` | Base URL for Slidy files |
| `slideous-url` | Base URL for Slideous files |
| `theme` | Slide theme |
| `transition` | Slide transition |

### Variables for Beamer

| Variable | Effect |
|----------|--------|
| `theme` | Beamer theme (e.g., Madrid, Warsaw) |
| `colortheme` | Color theme |
| `fonttheme` | Font theme |
| `innertheme` | Inner theme |
| `outertheme` | Outer theme |
| `aspectratio` | Slide aspect ratio (169, 43, etc.) |
| `institute` | Author institute |
| `titlegraphic` | Title slide graphic |
| `logo` | Slide logo |
| `navigation` | Navigation symbols |
| `section-titles` | Show section title slides |

### Variables for LaTeX

#### Layout

| Variable | Effect |
|----------|--------|
| `geometry` | Page geometry (e.g., `margin=1in`) |
| `papersize` | Paper size (letter, a4, etc.) |
| `classoption` | Document class options |
| `documentclass` | Document class (article, report, book, memoir) |
| `beamerarticle` | Use beamer article mode |

#### Fonts

| Variable | Effect |
|----------|--------|
| `fontfamily` | LaTeX font package |
| `fontfamilyoptions` | Options for font package |
| `mainfont` | Main font (xelatex/lualatex) |
| `sansfont` | Sans-serif font |
| `monofont` | Monospace font |
| `mathfont` | Math font |
| `fontsize` | Font size (10pt, 11pt, 12pt) |
| `linestretch` | Line spacing multiplier |

#### Links

| Variable | Effect |
|----------|--------|
| `colorlinks` | Color links (true/false) |
| `linkcolor` | Internal link color |
| `citecolor` | Citation link color |
| `urlcolor` | URL link color |
| `toccolor` | TOC link color |

#### Front Matter

| Variable | Effect |
|----------|--------|
| `lof` | Include list of figures |
| `lot` | Include list of tables |
| `thanks` | Acknowledgments (footnote on title) |
| `toc` | Include table of contents |
| `toc-depth` | TOC depth |

### Variables for PowerPoint

| Variable | Effect |
|----------|--------|
| `monofont` | Font for code blocks |

### Variables for Typst

| Variable | Effect |
|----------|--------|
| `fontsize` | Font size |
| `mainfont` | Main font |
| `sansfont` | Sans font |
| `monofont` | Mono font |
| `mathfont` | Math font |
| `margin` | Page margin (object with top/bottom/left/right) |
| `papersize` | Paper size |
| `cols` | Number of columns |
| `section-numbering` | Section numbering format |

### Variables for Context

| Variable | Effect |
|----------|--------|
| `fontsize` | Body font size |
| `headertext`, `footertext` | Headers and footers |
| `indenting` | Paragraph indentation |
| `interlinespace` | Line spacing |
| `layout` | Page layout |
| `margin-left`, `margin-right` | Margins |
| `pagenumbering` | Page numbering style |

### Variables for Man Pages

| Variable | Effect |
|----------|--------|
| `section` | Man page section (1-9) |
| `header` | Header text |
| `footer` | Footer text |
| `adjusting` | Text adjustment (l, r, c, b) |
| `hyphenate` | Allow hyphenation (true/false) |

## Common Patterns

### Project Defaults File

Create a `pandoc.yaml` in your project root:

```yaml
# pandoc.yaml — project default settings
from: markdown+emoji+smart
standalone: true
toc: true
number-sections: true
highlight-style: tango
bibliography: references.bib
csl: apa.csl
cite-method: citeproc
metadata:
  link-citations: true
variables:
  colorlinks: true
```

```bash
pandoc -d pandoc paper.md -o paper.pdf
```

### Format-Specific Overrides

```yaml
# html-defaults.yaml
from: markdown
to: html5
standalone: true
embed-resources: true
css:
  - style.css
variables:
  document-css: true
  maxwidth: 40em
```

```yaml
# pdf-defaults.yaml
from: markdown
to: pdf
pdf-engine: xelatex
variables:
  geometry: margin=1in
  fontsize: 12pt
  mainfont: "Linux Libertine O"
  monofont: "Fira Code"
```

```bash
pandoc -d html-defaults paper.md -o paper.html
pandoc -d pdf-defaults paper.md -o paper.pdf
```
