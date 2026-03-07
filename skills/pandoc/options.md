# Pandoc: CLI Options Reference

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## General Options

| Option | Short | Description |
|--------|-------|-------------|
| `--from=FORMAT` | `-f` | Input format (with optional extensions: `markdown+emoji`) |
| `--to=FORMAT` | `-t` | Output format (with optional extensions) |
| `--output=FILE` | `-o` | Output file (default: stdout) |
| `--data-dir=DIR` | | User data directory for templates, filters, etc. |
| `--defaults=FILE` | `-d` | Read options from a YAML defaults file |
| `--bash-completion` | | Generate bash completion script |
| `--verbose` | | Verbose diagnostic output |
| `--quiet` | | Suppress warnings |
| `--fail-if-warnings` | | Exit with error on any warning |
| `--log=FILE` | | Write JSON log to file |
| `--list-input-formats` | | List supported input formats |
| `--list-output-formats` | | List supported output formats |
| `--list-extensions[=FMT]` | | List extensions (optionally for a format) |
| `--list-highlight-languages` | | List supported highlight languages |
| `--list-highlight-styles` | | List available highlight styles |
| `--version` | `-v` | Print version |
| `--help` | `-h` | Print help |

## Reader Options

| Option | Description |
|--------|-------------|
| `--shift-heading-level-by=N` | Shift heading levels by N (e.g., -1 makes h2→h1) |
| `--indented-code-classes=CLASSES` | Classes to apply to indented code blocks |
| `--default-image-extension=EXT` | Extension for images with no extension (e.g., `.png`) |
| `--file-scope` | Parse each file independently (separate footnote numbering) |
| `--filter=PROGRAM` | Run an external filter (JSON stdin→stdout) |
| `--lua-filter=SCRIPT` | Run a Lua filter (faster than external filters) |
| `-M KEY[:VAL]`, `--metadata=KEY[:VAL]` | Set metadata value (affects template AND document metadata) |
| `--metadata-file=FILE` | Read metadata from YAML file |
| `--preserve-tabs` | Keep tabs instead of converting to spaces |
| `--tab-stop=N` | Tab stop width (default: 4) |
| `--track-changes=accept\|reject\|all` | How to handle Word tracked changes |
| `--extract-media=DIR` | Extract media files to directory |
| `--abbreviations=FILE` | Custom abbreviations file for smart punctuation |
| `--trace` | Print AST after each pass (debugging) |
| `--sandbox` | Disable file system access during conversion |

### Filters

Filters transform the AST between reading and writing:

```bash
# External filter (any language, receives JSON on stdin)
pandoc --filter ./my-filter.py input.md -o output.html

# Lua filter (built-in, faster, no external process)
pandoc --lua-filter=my-filter.lua input.md -o output.html

# Multiple filters (executed in order)
pandoc -L filter1.lua -L filter2.lua input.md -o output.html

# Citeproc (built-in citation processing filter)
pandoc --citeproc input.md -o output.html
```

**Filter search path:** Current directory, then `filters/` in data directory.

### Metadata vs Variables

```bash
# Metadata: affects BOTH template rendering AND document content
pandoc -M title="My Doc" input.md -o output.html

# Variable: affects ONLY template rendering (not document content)
pandoc -V fontsize=12pt input.md -o output.pdf
```

**Key difference:** Metadata set with `-M` is accessible to filters and citeproc. Variables set with `-V` are not.

## General Writer Options

| Option | Short | Description |
|--------|-------|-------------|
| `--standalone` | `-s` | Produce complete document with template |
| `--template=FILE` | | Use custom template |
| `-V KEY=VAL`, `--variable=KEY=VAL` | | Set template variable |
| `--variable-json=KEY=JSON` | | Set template variable as JSON value |
| `--print-default-template=FMT` | `-D FMT` | Print default template for format |
| `--print-default-data-file=FILE` | | Print a default data file |
| `--eol=crlf\|lf\|native` | | Line ending style |
| `--dpi=N` | | DPI for image size calculation (default: 72) |
| `--wrap=auto\|none\|preserve` | | Text wrapping mode |
| `--columns=N` | | Column width for wrapping (default: 72) |
| `--toc` | | Include table of contents |
| `--toc-depth=N` | | TOC depth (default: 3) |
| `--lof` | | Include list of figures |
| `--lot` | | Include list of tables |
| `--strip-comments` | | Strip HTML comments |
| `--no-highlight` | | Disable syntax highlighting (deprecated: use `--syntax-highlighting=none`) |
| `--highlight-style=STYLE` | | Highlighting style (deprecated: use `--syntax-highlighting=STYLE`) |
| `--syntax-highlighting=STYLE` | | Syntax highlighting: `default`, `none`, `idiomatic`, style name, or `.theme` file |
| `--print-highlight-style=STYLE` | | Output highlight theme as JSON |
| `--syntax-definition=FILE` | | Custom KDE-style syntax definition |
| `--include-in-header=FILE` | `-H` | Include content in header |
| `--include-before-body=FILE` | `-B` | Include content before body |
| `--include-after-body=FILE` | `-A` | Include content after body |
| `--resource-path=PATHS` | | Colon-separated paths to search for resources |
| `--request-header=NAME:VAL` | | Custom HTTP request header |
| `--no-check-certificate` | | Skip HTTPS certificate verification |

### Wrapping Behavior

```bash
# Auto-wrap at column width (default)
pandoc --wrap=auto input.md -o output.md

# No wrapping (one paragraph per line)
pandoc --wrap=none input.md -o output.md

# Preserve original line breaks
pandoc --wrap=preserve input.md -o output.md
```

## Options Affecting Specific Writers

### HTML Options

| Option | Description |
|--------|-------------|
| `--embed-resources` | Embed images, CSS, JS in the HTML file |
| `--self-contained` | Deprecated alias for `--embed-resources --standalone` |
| `--html-q-tags` | Use `<q>` tags for quotes in HTML |
| `--ascii` | Use ASCII characters only (entities for non-ASCII) |
| `--email-obfuscation=none\|javascript\|references` | Email address obfuscation method |
| `--id-prefix=STRING` | Prefix for HTML element IDs |
| `--title-prefix=STRING` | Prefix for HTML title |
| `-c URL`, `--css=URL` | Link to CSS stylesheet |
| `--section-divs` | Wrap sections in `<section>` divs |

### Markdown Options

| Option | Description |
|--------|-------------|
| `--reference-links` | Use reference-style links |
| `--reference-location=block\|section\|document` | Where to place reference links |
| `--markdown-headings=atx\|setext` | Heading style |
| `--list-tables` | Use list-based table syntax |
| `--ascii` | Use ASCII escapes for non-ASCII |

### LaTeX/PDF Options

| Option | Description |
|--------|-------------|
| `--top-level-division=default\|section\|chapter\|part` | Top-level heading division |
| `-N`, `--number-sections` | Number section headings |
| `--number-offset=N[,N,...]` | Starting number for sections |
| `--listings` | Use `listings` package for code |
| `--pdf-engine=ENGINE` | PDF engine (pdflatex, xelatex, lualatex, typst, etc.) |
| `--pdf-engine-opt=OPT` | Pass option to PDF engine (can repeat) |

### Slide Show Options

| Option | Description |
|--------|-------------|
| `-i`, `--incremental` | Make lists display incrementally |
| `--slide-level=N` | Heading level for slide boundaries |

### EPUB Options

| Option | Description |
|--------|-------------|
| `--epub-cover-image=FILE` | EPUB cover image |
| `--epub-title-page=true\|false` | Generate title page |
| `--epub-metadata=FILE` | Dublin Core metadata XML file |
| `--epub-embed-font=FILE` | Embed font in EPUB |
| `--epub-chapter-level=N` | Split EPUB at heading level |
| `--epub-subdirectory=DIR` | Subdirectory for EPUB content |
| `--ipynb-output=all\|none\|best` | Jupyter notebook output handling |

### DOCX/ODT Options

| Option | Description |
|--------|-------------|
| `--reference-doc=FILE` | Template document for styles |

### Chunked HTML Options

| Option | Description |
|--------|-------------|
| `--split-level=N` | Heading level to split at |
| `--chunk-template=TEMPLATE` | Template for chunk filenames |

## Citation Rendering

| Option | Short | Description |
|--------|-------|-------------|
| `--citeproc` | `-C` | Process citations using citeproc |
| `--bibliography=FILE` | | Bibliography file (can repeat) |
| `--csl=FILE` | | Citation Style Language file |
| `--citation-abbreviations=FILE` | | Journal abbreviations JSON |
| `--natbib` | | Use natbib for LaTeX citations |
| `--biblatex` | | Use biblatex for LaTeX citations |

## Math Rendering in HTML

| Option | Description |
|--------|-------------|
| `--mathjax[=URL]` | Use MathJax (default math rendering for HTML) |
| `--mathml` | Use MathML |
| `--webtex[=URL]` | Use web service for math images |
| `--katex[=URL]` | Use KaTeX |
| `--gladtex` | Use GladTeX (produces EHT files) |

```bash
# Default MathJax
pandoc -s --mathjax input.md -o output.html

# KaTeX (faster rendering)
pandoc -s --katex input.md -o output.html

# MathML (no external JS needed)
pandoc -s --mathml input.md -o output.html
```

## Options for Wrapper Scripts

| Option | Description |
|--------|-------------|
| `--dump-args` | Print arguments and input files, then exit |
| `--ignore-args` | Ignore command-line arguments (read stdin) |

## Common Option Combinations

### Academic Paper (LaTeX/PDF)

```bash
pandoc -s \
  --citeproc --bibliography=refs.bib --csl=apa.csl \
  --number-sections \
  --toc --toc-depth=3 \
  -V geometry:margin=1in \
  -V fontsize=12pt \
  --pdf-engine=xelatex \
  paper.md -o paper.pdf
```

### Self-Contained HTML Report

```bash
pandoc -s \
  --embed-resources \
  --toc \
  --css=style.css \
  --mathjax \
  --syntax-highlighting=tango \
  report.md -o report.html
```

### Word Document with Custom Template

```bash
pandoc -s \
  --reference-doc=template.docx \
  --citeproc --bibliography=refs.bib \
  report.md -o report.docx
```

### EPUB Book

```bash
pandoc -s \
  --epub-cover-image=cover.jpg \
  --css=epub.css \
  --toc --toc-depth=2 \
  -M title="My Book" \
  -M author="Author Name" \
  ch1.md ch2.md ch3.md -o book.epub
```

### Markdown Cleanup/Normalization

```bash
pandoc -f markdown -t markdown \
  --wrap=none \
  --reference-links \
  --reference-location=block \
  input.md -o cleaned.md
```

## Precedence Rules

When options are specified in multiple places, the priority is (highest first):

1. **Command-line flags** — always win
2. **Defaults file** specified later (on command line)
3. **Defaults file** specified earlier
4. **YAML metadata** in document
5. **Pandoc defaults** (built-in)

Within defaults files, later keys override earlier keys. On the command line, later flags override earlier ones for single-value options, but accumulate for list options (`--bibliography`, `--css`, etc.).
