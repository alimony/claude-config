# Pandoc: Markdown Inline Elements & Non-Default Extensions

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## Backslash Escapes

### Extension: `all_symbols_escapable` (default: on)

Any punctuation or symbol character can be escaped with a backslash:

```markdown
\*not emphasis\*
\# not a heading
\[not a link\]
\| not a table pipe
```

A backslash followed by a newline creates a hard line break (see `escaped_line_breaks`).

## Emphasis

```markdown
*italic* or _italic_
**bold** or __bold__
***bold italic*** or ___bold italic___
```

### Extension: `intraword_underscores` (default: on)

Underscores in words are treated literally (not emphasis):

```markdown
my_variable_name     ← no emphasis
my*variable*name     ← "variable" is italic
```

**Tip:** Use `*` for emphasis to avoid ambiguity with underscores in identifiers.

## Strikeout

### Extension: `strikeout` (default: on)

```markdown
This is ~~deleted text~~.
```

## Superscripts and Subscripts

### Extension: `superscript`, `subscript` (default: on)

```markdown
H~2~O is water.
2^10^ is 1024.
```

Spaces must be escaped if present:

```markdown
H~2\ O~ needs the escaped space.
```

### Extension: `short_subsuperscripts` (non-default)

Shorter syntax for single-character sub/superscripts:

```markdown
H~2O     ← H₂O (only single char after ~)
x^2 + 1  ← x² + 1 (only single char after ^)
```

## Verbatim (Inline Code)

```markdown
Use `printf()` to print.
Use `` `backtick` `` inside code.      ← double backticks to include literal backtick
Use ```code with `` inside```.          ← triple backticks for double backticks
```

### Extension: `inline_code_attributes` (default: on)

```markdown
`code`{.python}
`code`{#mycode .haskell .numberLines}
```

## Underline

```markdown
[This text is underlined]{.underline}
```

## Small Caps

```markdown
[Small caps text]{.smallcaps}
```

## Highlighting (Mark)

### Extension: `mark` (non-default)

```markdown
This is ==highlighted text==.
```

Enable with: `pandoc -f markdown+mark`

## Math

### Extension: `tex_math_dollars` (default: on)

```markdown
Inline math: $E = mc^2$

Display math:
$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$
```

**Rules:**
- Inline: `$...$` — no space after opening `$` or before closing `$`
- Display: `$$...$$` — can span multiple lines
- Backslash-escaped `\$` produces a literal dollar sign

**Rendering in HTML** — choose one:

```bash
pandoc --mathjax input.md -o output.html     # MathJax (default)
pandoc --katex input.md -o output.html       # KaTeX (faster)
pandoc --mathml input.md -o output.html      # MathML (no JS)
pandoc --webtex input.md -o output.html      # Server-rendered images
```

### Non-Default Math Extensions

| Extension | Syntax | Enable |
|-----------|--------|--------|
| `tex_math_gfm` | `$`/`$$` with GFM rules | `+tex_math_gfm` |
| `tex_math_single_backslash` | `\(...\)` / `\[...\]` | `+tex_math_single_backslash` |
| `tex_math_double_backslash` | `\\(...\\)` / `\\[...\\]` | `+tex_math_double_backslash` |

## Raw HTML/LaTeX

### Extension: `raw_html` (default: on for HTML-like formats)

```markdown
<div class="special">
This is raw HTML.
</div>

<span style="color: red;">Red text</span>
```

### Extension: `markdown_in_html_blocks` (default: on)

Markdown is processed inside HTML block-level elements:

```html
<div class="note">
*This will be* **parsed as Markdown**.
</div>
```

### Extension: `native_divs` (default: on)

HTML `<div>` tags become pandoc Div elements (preserving classes/attributes):

```markdown
<div class="warning">
This is a warning.
</div>
```

### Extension: `native_spans` (default: on)

HTML `<span>` tags become pandoc Span elements.

### Extension: `raw_tex` (default: on for LaTeX)

```markdown
\textbf{This is LaTeX bold} and $\alpha + \beta$.
```

### Extension: `raw_attribute` (default: on)

Generic syntax for any raw format:

````markdown
```{=html}
<video src="video.mp4" controls></video>
```

`<br>`{=html}

```{=latex}
\newpage
```
````

## LaTeX Macros

### Extension: `latex_macros` (default: on)

Define and use LaTeX macros in Markdown:

```markdown
\newcommand{\tuple}[1]{\langle #1 \rangle}

The $\tuple{a, b, c}$ is ordered.
```

- Macros are applied to all LaTeX math AND in raw LaTeX
- For HTML output, macros expand to their definition
- For LaTeX output, macro definitions are passed through to LaTeX

## Links

### Automatic Links

```markdown
<https://example.com>
<user@example.com>
```

### Extension: `autolink_bare_uris` (non-default)

```markdown
Visit https://example.com for more.
```

Enable with: `pandoc -f markdown+autolink_bare_uris`

### Inline Links

```markdown
[Link text](https://example.com "Optional title")
[Link text](https://example.com)
```

### Reference Links

```markdown
[Link text][ref-id]
[Link text][]          ← uses link text as ID

[ref-id]: https://example.com "Optional title"
```

### Extension: `shortcut_reference_links` (default: on)

Omit the second bracket pair:

```markdown
See the [Pandoc manual] for details.

[Pandoc manual]: https://pandoc.org/MANUAL.html
```

### Internal Links

Link to heading IDs:

```markdown
See the [Introduction](#introduction).

# Introduction {#introduction}
```

With `implicit_header_references`, just use the heading text:

```markdown
See the [Introduction].
```

## Images

```markdown
![Alt text](image.png "Optional title")
![Alt text](image.png){width=50%}
```

### Extension: `implicit_figures` (default: on)

An image alone in a paragraph becomes a figure with caption:

```markdown
![This becomes the figure caption.](image.png)
```

To prevent this (keep as inline image), add a non-breaking space after:

```markdown
![Not a figure](image.png)\
```

### Extension: `link_attributes` (default: on)

Add attributes to images (and links):

```markdown
![Caption](image.png){width=50% height=300px}
![Caption](image.png){width="3in"}
![Caption](image.png){.bordered #fig:example}
```

**Common image attributes:**

| Attribute | Effect |
|-----------|--------|
| `width` | Image width (px, %, in, cm) |
| `height` | Image height |
| `.class` | CSS class |
| `#id` | Element ID |

## Divs and Spans

### Extension: `fenced_divs` (default: on)

Block-level containers with classes and attributes:

```markdown
::: {.warning}
This is a warning box.
:::

::: {#special .note data-count="5"}
Content with multiple attributes.
:::

:::: {.columns}
::: {.column width="50%"}
Left column
:::
::: {.column width="50%"}
Right column
:::
::::
```

**Nesting:** Use more colons for outer fences.

### Extension: `bracketed_spans` (default: on)

Inline containers:

```markdown
[This text]{.highlight}
[Important]{.red #imp data-x="5"}
[Small caps]{.smallcaps}
[Underlined]{.underline}
```

## Footnotes

### Extension: `footnotes` (default: on)

```markdown
Here is a footnote reference.[^1]

[^1]: Here is the footnote content.

    It can contain multiple paragraphs (indent continuation).

    And even code blocks.
```

**Footnote identifiers** can be any string (not just numbers):

```markdown
See this point.[^longnote]

[^longnote]: This is a longer footnote with multiple paragraphs.

    Second paragraph of the footnote.
```

### Extension: `inline_notes` (default: on)

```markdown
Here is an inline note.^[This is the note content.]
```

## Citation Syntax

### Extension: `citations` (default: on)

```markdown
[@smith2020]                       → (Smith 2020)
[@smith2020, p. 33]                → (Smith 2020, 33)
[@smith2020; @jones2021]           → (Smith 2020; Jones 2021)
@smith2020                         → Smith (2020)
@smith2020 [p. 33]                 → Smith (2020, 33)
[-@smith2020]                      → (2020)
[see @smith2020, pp. 33-35]        → (see Smith 2020, 33–35)
```

Requires `--citeproc` flag to process. See `citations.md` for full details.

## Non-Default Extensions

These extensions are OFF by default. Enable with `+extension_name`.

### `alerts`

GitHub-style alert/admonition blocks:

```markdown
> [!NOTE]
> This is a note.

> [!WARNING]
> This is a warning.

> [!TIP]
> This is a tip.
```

Enable: `pandoc -f markdown+alerts`

### `emoji`

Emoji shortcodes:

```markdown
I :heart: pandoc! :tada:
```

Enable: `pandoc -f markdown+emoji`

### `hard_line_breaks`

Every newline in the source becomes a `<br>`:

```markdown
Line one
Line two (this would be a new line, not same paragraph)
```

Enable: `pandoc -f markdown+hard_line_breaks`

### `wikilinks_title_after_pipe`

Wiki-style links:

```markdown
[[Page Name|Display Text]]
```

Enable: `pandoc -f markdown+wikilinks_title_after_pipe`

There's also `wikilinks_title_before_pipe`:

```markdown
[[Display Text|Page Name]]
```

### `mark`

Highlighted text:

```markdown
==highlighted==
```

Enable: `pandoc -f markdown+mark`

### `attributes`

Generic attribute syntax for more elements:

```markdown
{.class #id key=value}
```

Enable: `pandoc -f markdown+attributes`

### `old_dashes`

GNU-style dash interpretation:

```markdown
--   → en-dash
---  → em-dash
```

(Default pandoc: `--` = en-dash, `---` = em-dash, same result.)

### `lists_without_preceding_blankline`

Lists don't require a blank line before them:

```markdown
Some text.
- Item one
- Item two
```

### `four_space_rule`

Use a strict 4-space rule for list continuation (like original Markdown).

### `east_asian_line_breaks` / `ignore_line_breaks`

- `east_asian_line_breaks`: Ignore newlines between East Asian characters
- `ignore_line_breaks`: Ignore all newlines (treat as spaces)

### `rebase_relative_paths`

Resolve relative paths in links/images relative to the source file location (useful with multiple input files).

### `mmd_title_block`

MultiMarkdown-style title block:

```markdown
Title:    My Document
Author:   Jane Doe
Date:     January 2024
```

### `abbreviations`

Abbreviation definitions:

```markdown
*[HTML]: Hyper Text Markup Language
*[W3C]: World Wide Web Consortium

The HTML specification is maintained by the W3C.
```

### `sourcepos`

Add data-pos attributes to elements with source file positions (useful for editors).

### `gutenberg`

Formats for Project Gutenberg texts (special whitespace handling).

## Markdown Variants

Pandoc supports several predefined Markdown variants:

| Variant | Description |
|---------|-------------|
| `markdown` | Pandoc's extended Markdown (default) |
| `markdown_strict` | Original Markdown (Gruber) |
| `markdown_phpextra` | PHP Markdown Extra |
| `markdown_mmd` | MultiMarkdown |
| `commonmark` | CommonMark spec |
| `commonmark_x` | CommonMark with common extensions |
| `gfm` | GitHub Flavored Markdown |

```bash
# GitHub Flavored Markdown
pandoc -f gfm input.md -o output.html

# CommonMark with extensions
pandoc -f commonmark_x input.md -o output.html

# Strict original Markdown
pandoc -f markdown_strict input.md -o output.html
```

**Choosing a variant:**
- **`markdown`** — Maximum features, pandoc-specific extensions
- **`gfm`** — GitHub compatibility (tables, task lists, auto-links)
- **`commonmark_x`** — Strict spec with common extras (footnotes, tables, etc.)
- **`commonmark`** — Strictest CommonMark (few extensions)
