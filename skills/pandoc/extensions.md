# Pandoc: Extensions Reference

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## How Extensions Work

Extensions modify the behavior of input and output formats. Enable/disable with `+`/`-` syntax:

```bash
# Enable an extension
pandoc -f markdown+emoji input.md -o output.html

# Disable an extension
pandoc -f markdown-smart input.md -o output.html

# Multiple extensions
pandoc -f markdown+emoji+hard_line_breaks-smart input.md -o output.html

# Extensions on output format too
pandoc -f markdown -t html-smart input.md -o output.html
```

### Checking Available Extensions

```bash
# List all extensions with their defaults for a format
pandoc --list-extensions=markdown

# Output: + means enabled by default, - means disabled
# +smart
# +emoji       ← non-default (disabled)
# -hard_line_breaks  ← non-default (disabled)
```

## Typography

### Extension: `smart` (default: on for `markdown`)

Converts ASCII punctuation to typographic equivalents:

| Input | Output | Character |
|-------|--------|-----------|
| `"quotes"` | "quotes" | Curly double quotes |
| `'quotes'` | 'quotes' | Curly single quotes |
| `---` | — | Em-dash |
| `--` | – | En-dash |
| `...` | … | Ellipsis |

**Disable for code-heavy documents:**

```bash
pandoc -f markdown-smart input.md -o output.html
```

**Note:** `smart` is available for many formats, not just Markdown. E.g., `pandoc -f html+smart` will process smart typography when reading HTML.

## Headings and Sections

### Extension: `auto_identifiers` (default: on for `markdown`)

Automatically generates identifiers for headings:

```markdown
# My Heading
```

→ `<h1 id="my-heading">My Heading</h1>`

**Algorithm:**
1. Remove formatting, links, footnotes
2. Remove punctuation (except `-`, `_`, `.`)
3. Replace spaces with hyphens
4. Convert to lowercase
5. Prefix with `section-` if starts with a number
6. If duplicate, append `-1`, `-2`, etc.

### Extension: `ascii_identifiers`

Removes non-ASCII characters from identifiers (instead of keeping them).

### Extension: `gfm_auto_identifiers`

Uses GitHub's algorithm for generating heading IDs:
- Lowercases
- Removes punctuation except `-` and space
- Replaces spaces with `-`
- Different from pandoc's default in edge cases

**Use when targeting GitHub compatibility:**

```bash
pandoc -f markdown+gfm_auto_identifiers input.md -o output.html
```

## Math Input

Math extensions control how mathematical notation is parsed. The primary extension is `tex_math_dollars` (default: on), covered in `markdown-inline.md`.

Additional math input extensions:

| Extension | Syntax | Default |
|-----------|--------|---------|
| `tex_math_dollars` | `$...$` / `$$...$$` | On |
| `tex_math_gfm` | GFM-compatible `$` rules | Off |
| `tex_math_single_backslash` | `\(...\)` / `\[...\]` | Off |
| `tex_math_double_backslash` | `\\(...\\)` / `\\[...\\]` | Off |

## Raw HTML/TeX

### Extension: `raw_html` (default: on for HTML-capable formats)

Pass raw HTML through to output. Without this, HTML tags are removed.

### Extension: `raw_tex` (default: on for LaTeX-capable formats)

Pass raw LaTeX commands through to output.

### Extension: `raw_attribute` (default: on)

Generic syntax for embedding raw content for any format:

````markdown
```{=html}
<video src="video.mp4" controls></video>
```

```{=latex}
\newpage
```

Inline: `<br>`{=html}
````

### Extension: `markdown_in_html_blocks` (default: on)

Parse Markdown inside HTML block elements:

```html
<div class="note">
**This is bold** because Markdown is parsed here.
</div>
```

### Extension: `native_divs` / `native_spans` (default: on)

Convert HTML `<div>` and `<span>` tags to pandoc Div/Span elements, preserving their attributes.

## Literate Haskell

### Extension: `literate_haskell`

Enables literate Haskell conventions:

```markdown
This is a description.

> square :: Int -> Int
> square x = x * x

This is more description.
```

Lines beginning with `>` followed by a space are treated as Haskell code. Use with `.lhs` files or enable explicitly:

```bash
pandoc -f markdown+literate_haskell input.lhs -o output.html
```

## Other Extensions

### `empty_paragraphs`

Preserve empty paragraphs from input (normally pandoc removes them).

### `native_numbering`

Use the output format's native numbering for figures and tables (e.g., OpenDocument, DOCX).

### `xrefs_name` / `xrefs_number`

Cross-reference styles for OpenDocument output:
- `xrefs_name`: Reference by name ("Section 3.2")
- `xrefs_number`: Reference by number ("3.2")

### `styles` (docx reader)

Preserve Word custom styles as `custom-style` attributes. See `output-formats.md` for details.

### `amuse`

Support for the Amuse wiki markup format.

### `raw_markdown`

For ipynb (Jupyter) format: treat Markdown cells as raw Markdown instead of parsing them.

### `tagging` (context writer)

Produce ConTeXt markup optimized for PDF tagging/accessibility:

```bash
pandoc -t context+tagging input.md -o output.pdf
```

### Org-mode Extensions

| Extension | Purpose |
|-----------|---------|
| `org-citations` | Org citation syntax |
| `org-fancy-lists` | Org-style list markers (letters, roman) |
| `smart_quotes-org` | Smart quotes in org mode |
| `special_strings-org` | Special strings (LaTeX-like) in org |

### `typst-citations`

Use Typst's native citation syntax instead of pandoc's.

### `docx-citations`

Parse citations from Word (DOCX) documents.

### `element_citations`

For JATS XML output: use `<element-citation>` instead of `<mixed-citation>`.

### `ntb`

For Notebook (ntb) format support.

## Extension Defaults by Format

### `markdown` (Pandoc's Markdown)

**Enabled by default** (partial list of most important):
- `smart`, `auto_identifiers`, `header_attributes`
- `fenced_code_blocks`, `backtick_code_blocks`, `fenced_code_attributes`
- `line_blocks`, `fancy_lists`, `startnum`, `task_lists`
- `definition_lists`, `example_lists`
- `table_captions`, `simple_tables`, `multiline_tables`, `grid_tables`, `pipe_tables`
- `pandoc_title_block`, `yaml_metadata_block`
- `all_symbols_escapable`, `intraword_underscores`
- `strikeout`, `superscript`, `subscript`
- `tex_math_dollars`, `raw_html`, `raw_tex`, `raw_attribute`
- `latex_macros`, `shortcut_reference_links`
- `implicit_figures`, `link_attributes`
- `fenced_divs`, `bracketed_spans`
- `footnotes`, `inline_notes`, `citations`
- `escaped_line_breaks`, `blank_before_header`, `blank_before_blockquote`
- `space_in_atx_header`, `implicit_header_references`

**Disabled by default** (opt-in):
- `emoji`, `hard_line_breaks`, `mark`, `alerts`
- `autolink_bare_uris`, `wikilinks_title_after_pipe`
- `lists_without_preceding_blankline`, `four_space_rule`
- `east_asian_line_breaks`, `ignore_line_breaks`
- `mmd_title_block`, `abbreviations`, `attributes`
- `short_subsuperscripts`, `sourcepos`, `gutenberg`
- `tex_math_gfm`, `tex_math_single_backslash`

### `gfm` (GitHub Flavored Markdown)

Enabled: `pipe_tables`, `raw_html`, `fenced_code_blocks`, `auto_identifiers` (gfm style), `strikeout`, `task_lists`, `emoji`, `autolink_bare_uris`, `tex_math_gfm`

### `commonmark`

Minimal extensions. Enable extras with `commonmark_x`.

### `commonmark_x` (CommonMark + Extensions)

Adds to CommonMark: `smart`, `strikeout`, `pipe_tables`, `raw_html`, `fenced_code_blocks`, `fenced_code_attributes`, `backtick_code_blocks`, `footnotes`, `task_lists`, `attributes`, `auto_identifiers`, `yaml_metadata_block`

## Quick Reference: Common Extension Toggles

| Goal | Extension | Command |
|------|-----------|---------|
| Disable smart quotes | `-smart` | `pandoc -f markdown-smart` |
| Enable emoji | `+emoji` | `pandoc -f markdown+emoji` |
| GitHub alerts | `+alerts` | `pandoc -f markdown+alerts` |
| Hard line breaks | `+hard_line_breaks` | `pandoc -f markdown+hard_line_breaks` |
| Wiki links | `+wikilinks_title_after_pipe` | `pandoc -f markdown+wikilinks_title_after_pipe` |
| Highlighted text | `+mark` | `pandoc -f markdown+mark` |
| Bare URL auto-linking | `+autolink_bare_uris` | `pandoc -f markdown+autolink_bare_uris` |
| GFM-style heading IDs | `+gfm_auto_identifiers` | `pandoc -f markdown+gfm_auto_identifiers` |
| Preserve DOCX styles | `+styles` | `pandoc -f docx+styles` |
| PDF accessibility | `+tagging` | `pandoc -t context+tagging` |
| No footnotes | `-footnotes` | `pandoc -f markdown-footnotes` |
| No tables | `-pipe_tables-grid_tables-simple_tables-multiline_tables` | Disable all table types |
