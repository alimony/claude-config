# Pandoc: Fundamentals

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## What Is Pandoc?

Pandoc is a universal document converter. It reads markup in one format and writes it in another. The architecture is:

```
Input Format → Reader → AST (Abstract Syntax Tree) → Writer → Output Format
```

**Key insight:** Conversions go through an intermediate AST representation. This means:
- Any input format can be converted to any output format
- Conversions are *lossy* when formats differ in expressiveness (e.g., a complex LaTeX doc → Markdown may lose information)
- Filters and Lua scripts can transform the AST between reading and writing

## Synopsis

```bash
pandoc [OPTIONS] [INPUT-FILE]...
```

- **No input file:** reads from stdin
- **No `-o` flag:** writes to stdout
- **Multiple input files:** concatenated (with blank line between) before parsing
- **Output format guessed** from `-o` extension, or defaults to HTML
- **Input format guessed** from file extension, or defaults to Markdown

## Specifying Formats

```bash
# Explicit input/output formats
pandoc -f markdown -t html input.md

# Short form
pandoc -f markdown -t latex input.md -o output.tex

# With extensions
pandoc -f markdown+emoji+hard_line_breaks -t html input.md
pandoc -f markdown-smart -t html input.md
```

### Format Extension Syntax

```
format+extension1-extension2+extension3
```

- `+ext` enables an extension
- `-ext` disables an extension
- Multiple extensions can be chained

### List Available Formats and Extensions

```bash
pandoc --list-input-formats
pandoc --list-output-formats
pandoc --list-extensions            # all extensions
pandoc --list-extensions=markdown   # extensions for a specific format
```

### Common Input Formats

| Format | Name | Notes |
|--------|------|-------|
| Pandoc Markdown | `markdown` | Default, most extensions enabled |
| CommonMark | `commonmark` | Strict CommonMark |
| CommonMark + extensions | `commonmark_x` | CommonMark with common extensions |
| GitHub Flavored Markdown | `gfm` | GFM spec |
| HTML | `html` | |
| LaTeX | `latex` | |
| DOCX | `docx` | Microsoft Word |
| EPUB | `epub` | |
| Org Mode | `org` | Emacs Org |
| reStructuredText | `rst` | |
| Jupyter Notebook | `ipynb` | |
| BibLaTeX/BibTeX | `biblatex`/`bibtex` | Bibliography formats |
| CSV | `csv` | Tables |
| Typst | `typst` | |

### Common Output Formats

| Format | Name | File Extension |
|--------|------|---------------|
| HTML | `html` / `html5` | `.html` |
| PDF | (via engine) | `.pdf` |
| LaTeX | `latex` | `.tex` |
| DOCX | `docx` | `.docx` |
| EPUB | `epub` / `epub3` | `.epub` |
| Markdown | `markdown` | `.md` |
| Plain text | `plain` | `.txt` |
| reveal.js | `revealjs` | `.html` |
| Beamer | `beamer` | `.pdf` / `.tex` |
| PowerPoint | `pptx` | `.pptx` |
| Typst | `typst` | `.typ` |
| Chunked HTML | `chunkedhtml` | `.zip` |

## Common Conversion Patterns

```bash
# Markdown → HTML
pandoc input.md -o output.html

# Markdown → standalone HTML (with <head>, <body>)
pandoc -s input.md -o output.html

# Markdown → PDF (via LaTeX)
pandoc input.md -o output.pdf

# Markdown → Word
pandoc input.md -o output.docx

# Markdown → EPUB
pandoc input.md -o output.epub

# Word → Markdown
pandoc input.docx -o output.md

# HTML → Markdown
pandoc -f html https://example.com -o output.md

# Multiple inputs → single output
pandoc ch1.md ch2.md ch3.md -o book.pdf

# Stdin → stdout
echo "**bold**" | pandoc -f markdown -t html

# With table of contents
pandoc -s --toc input.md -o output.html

# With custom CSS
pandoc -s --css=style.css input.md -o output.html

# Self-contained HTML (all resources embedded)
pandoc -s --embed-resources --standalone input.md -o output.html
```

## Fragment vs Standalone (`-s`)

By default, pandoc produces a **document fragment** — just the body content.

```bash
# Fragment (no <html>, <head>, <body> wrapper)
pandoc input.md -o output.html
# Output: <p>Hello <strong>world</strong></p>

# Standalone (complete document with template)
pandoc -s input.md -o output.html
# Output: <!DOCTYPE html><html>...<body><p>Hello...</p></body></html>
```

**When you need `-s`:**
- HTML files you'll open in a browser
- LaTeX files you'll compile
- Any format where a wrapper is expected

**When you don't need `-s`:**
- HTML fragments for embedding in another page
- Piping output to another tool
- DOCX, EPUB, PPTX (always standalone — `-s` is implied)

## Creating a PDF

Pandoc can produce PDFs via several intermediate formats and engines:

### Via LaTeX (Default)

```bash
# Default (pdflatex)
pandoc input.md -o output.pdf

# With XeLaTeX (better Unicode/font support)
pandoc --pdf-engine=xelatex input.md -o output.pdf

# With LuaLaTeX (full Unicode + PDF tagging)
pandoc --pdf-engine=lualatex input.md -o output.pdf

# With TinyTeX (lightweight LaTeX distribution)
pandoc --pdf-engine=tectonic input.md -o output.pdf
```

### Via HTML

```bash
# WeasyPrint (CSS-styled PDFs)
pandoc --pdf-engine=weasyprint input.md -o output.pdf

# wkhtmltopdf
pandoc --pdf-engine=wkhtmltopdf input.md -o output.pdf

# Prince (commercial, high quality)
pandoc --pdf-engine=prince input.md -o output.pdf

# Pagedjs-cli
pandoc --pdf-engine=pagedjs-cli input.md -o output.pdf
```

### Via Typst

```bash
pandoc --pdf-engine=typst input.md -o output.pdf
```

### Via ConTeXt

```bash
pandoc -t context input.md -o output.pdf
```

### Via groff (ms/man)

```bash
pandoc -t ms input.md --pdf-engine=pdfroff -o output.pdf
```

### Choosing a PDF Engine

| Engine | Via | Best For |
|--------|-----|----------|
| **pdflatex** | LaTeX | Standard academic documents |
| **xelatex** | LaTeX | Unicode text, custom fonts |
| **lualatex** | LaTeX | Full Unicode, PDF accessibility |
| **typst** | Typst | Modern, fast, simpler syntax |
| **weasyprint** | HTML | CSS-styled documents |
| **wkhtmltopdf** | HTML | Quick HTML→PDF |
| **prince** | HTML | High-quality CSS→PDF (commercial) |
| **context** | ConTeXt | Advanced typography |

**Common issue:** "LaTeX Error: File not found" — install the required LaTeX packages. For a minimal installation, use [TinyTeX](https://yihui.org/tinytex/).

## Character Encoding

- **Input must be UTF-8.** Pandoc assumes UTF-8 for all input.
- **Convert non-UTF-8 input first:**

```bash
iconv -t utf-8 input.latin1.txt | pandoc -o output.html
```

- Pandoc strips the UTF-8 BOM (byte order mark) if present.

## Reading from the Web

```bash
# Fetch and convert a URL
pandoc -f html https://example.com/page.html -o output.md

# With custom headers
pandoc --request-header='User-Agent: MyApp' -f html https://example.com -o output.md
```

## Exit Codes

| Code | Name | Meaning |
|------|------|---------|
| 0 | Success | No errors |
| 1 | PandocIOError | I/O error |
| 3 | PandocFailOnWarningError | `--fail-if-warnings` triggered |
| 4 | PandocAppError | Application error |
| 5 | PandocTemplateError | Template error |
| 6 | PandocOptionError | Invalid option |
| 21 | PandocUnknownReaderError | Unknown input format |
| 22 | PandocUnknownWriterError | Unknown output format |
| 23 | PandocUnsupportedExtensionError | Unsupported extension |
| 24 | PandocCiteprocError | Citeproc error |
| 25 | PandocBibliographyError | Bibliography error |
| 31 | PandocEpubSubdirectoryError | EPUB subdirectory error |
| 43 | PandocPDFError | PDF creation error |
| 44 | PandocXMLError | XML parsing error |
| 47 | PandocPDFProgramNotFoundError | PDF engine not found |
| 61 | PandocHttpError | HTTP request error |
| 62 | PandocShouldNeverHappenError | Internal error |
| 63 | PandocSomeError | Generic error |
| 64 | PandocParseError | Parse error |
| 65 | PandocParsecError | Parsec error |
| 66 | PandocMakePDFError | PDF engine error |
| 67 | PandocSyntaxMapError | Syntax highlighting map error |
| 83 | PandocFilterError | Filter error |
| 84 | PandocLuaError | Lua filter error |
| 89 | PandocNoScriptingEngine | No Lua engine available |
| 91 | PandocMacroLoop | Infinite macro loop |
| 92 | PandocUTF8DecodingError | UTF-8 decoding error |
| 93 | PandocIpynbDecodingError | Notebook decoding error |
| 94 | PandocUnsupportedCharsetError | Unsupported charset |
| 97 | PandocCouldNotFindDataFileError | Data file not found |
| 98 | PandocCouldNotFindMetadataFileError | Metadata file not found |
| 99 | PandocResourceNotFound | Resource not found |

### Scripting with Exit Codes

```bash
pandoc input.md -o output.pdf 2>/dev/null
case $? in
  0) echo "Success" ;;
  43) echo "PDF creation failed — check LaTeX installation" ;;
  47) echo "PDF engine not found — install pdflatex or use --pdf-engine" ;;
  *) echo "Error: exit code $?" ;;
esac
```

## Key Flags Quick Reference

| Flag | Short | Purpose |
|------|-------|---------|
| `--from=FORMAT` | `-f` | Input format |
| `--to=FORMAT` | `-t` | Output format |
| `--output=FILE` | `-o` | Output file |
| `--standalone` | `-s` | Produce complete document (not fragment) |
| `--template=FILE` | | Custom template |
| `--variable=KEY:VAL` | `-V` | Set template variable |
| `--metadata=KEY:VAL` | `-M` | Set metadata |
| `--toc` | | Include table of contents |
| `--number-sections` | `-N` | Number section headings |
| `--css=URL` | `-c` | Link CSS stylesheet |
| `--embed-resources` | | Embed all resources in output |
| `--pdf-engine=ENGINE` | | PDF engine to use |
| `--filter=SCRIPT` | `-F` | Run a filter |
| `--lua-filter=SCRIPT` | `-L` | Run a Lua filter |
| `--citeproc` | `-C` | Process citations |
| `--bibliography=FILE` | | Bibliography file |
| `--defaults=FILE` | `-d` | Read options from defaults file |
| `--verbose` | | Verbose output |
| `--quiet` | | Suppress warnings |
| `--sandbox` | | Disable file I/O in conversions |
| `--version` | `-v` | Show version |
| `--help` | `-h` | Show help |

## Common Pitfalls

1. **Fragment vs standalone:** Forgetting `-s` for HTML/LaTeX produces headless documents
2. **Format guessing:** Without `-f`, pandoc guesses from file extension — may guess wrong for stdin
3. **Missing LaTeX packages:** PDF creation fails if LaTeX packages aren't installed — use `--pdf-engine=typst` or `--pdf-engine=weasyprint` as alternatives
4. **Non-UTF-8 input:** Pandoc requires UTF-8 — convert with `iconv` first
5. **File concatenation:** Multiple input files are concatenated with blank lines — may cause unexpected heading level issues
6. **Extension defaults differ by format:** `markdown` has many extensions on by default; `commonmark` has few — check with `--list-extensions=FORMAT`
