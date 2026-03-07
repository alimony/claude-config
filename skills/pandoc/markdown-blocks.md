# Pandoc: Markdown Block Elements

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## Philosophy

Pandoc's Markdown is an extended variant of John Gruber's original Markdown. It aims for unambiguous, expressive document markup. Extensions can be toggled with `+ext`/`-ext` syntax.

**Key difference from other Markdown flavors:** Pandoc Markdown has MANY extensions enabled by default (footnotes, tables, definition lists, metadata blocks, etc.). If targeting GFM or CommonMark specifically, use `-f gfm` or `-f commonmark_x`.

## Paragraphs

A paragraph is one or more lines of text followed by a blank line.

```markdown
This is a paragraph.

This is another paragraph.
```

**Newlines within a paragraph** are treated as spaces (soft wrap). To force a line break:

### Extension: `escaped_line_breaks` (default: on)

A backslash followed by a newline creates a hard line break:

```markdown
This is line one.\
This is line two.
```

Produces `<br>` in HTML. (In standard Markdown, two trailing spaces also work.)

## Headings

### ATX-Style Headings (Preferred)

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
```

### Setext-Style Headings

```markdown
Heading 1
=========

Heading 2
---------
```

Only levels 1 and 2 are available with setext style.

### Extension: `blank_before_header` (default: on)

Requires a blank line before a heading:

```markdown
Some text.

# This works

Some text.
# This does NOT work (no blank line before)
```

### Extension: `space_in_atx_header` (default: on)

Requires a space after the `#` characters:

```markdown
# This is a heading     ← correct
#This is NOT a heading  ← treated as paragraph
```

### Heading Identifiers

Pandoc auto-generates identifiers from heading text:

```markdown
# My Great Heading
```

Produces `<h1 id="my-great-heading">`. Rules:
- Lowercase
- Spaces → hyphens
- Remove punctuation (except hyphens, underscores, periods)
- Prefix with `section-` if starts with number

### Extension: `header_attributes` (default: on)

Override identifiers and add classes/attributes:

```markdown
# My Heading {#custom-id .unnumbered}

## Another Heading {#sec:intro .highlight data-x="5"}

### No Number {-}    ← shorthand for .unnumbered
```

### Extension: `implicit_header_references` (default: on)

Reference headings as link targets by their text:

```markdown
# Introduction

...later in the document...

See the [Introduction] for details.
See the [introduction][Introduction] for details.
```

### Extension: `auto_identifiers` (default: on for markdown)

Auto-generates heading IDs. Without this, headings have no ID attribute.

### Extension: `gfm_auto_identifiers`

Uses GitHub's ID generation algorithm instead of pandoc's.

## Block Quotations

```markdown
> This is a block quote.
>
> It can span multiple paragraphs.
>
> > And they can be nested.
```

**Lazy continuation** — you don't need `>` on every line:

```markdown
> This is a block quote
that continues on the next line
without a > character.
```

### Extension: `blank_before_blockquote` (default: on)

Requires a blank line before a block quote:

```markdown
Some text.

> This is a quote.
```

## Code Blocks

### Indented Code Blocks

Indent by 4 spaces (or 1 tab):

```markdown
    def hello():
        print("Hello")
```

### Fenced Code Blocks

#### Extension: `fenced_code_blocks` (default: on)

Use tildes or backticks:

````markdown
```python
def hello():
    print("Hello")
```

~~~ruby
puts "Hello"
~~~
````

#### Extension: `backtick_code_blocks` (default: on)

Enables backtick fences (`` ``` ``). Without this, only tilde fences (`~~~`) work.

#### Extension: `fenced_code_attributes` (default: on)

Add attributes to fenced code blocks:

````markdown
```{#mycode .python .numberLines startFrom="10"}
def hello():
    print("Hello")
```
````

Shorthand — just the language name:

````markdown
```python
code here
```
````

## Line Blocks

### Extension: `line_blocks` (default: on)

Preserve line breaks and leading spaces (useful for poetry, addresses):

```markdown
| The limerick packs laughs anatomical
| In space that is quite economical.
|    But the good ones I've seen
|    So seldom are clean
| And the clean ones so seldom are comical.
```

Each line begins with `|` followed by a space.

## Lists

### Bullet Lists

```markdown
- Item one
- Item two
- Item three
```

Can use `*`, `+`, or `-` as markers. Changing the marker starts a new list.

### Ordered Lists

```markdown
1. First
2. Second
3. Third
```

#### Extension: `fancy_lists` (default: on)

Allows different numbering styles:

```markdown
i. Roman lowercase
ii. More roman
iii. And more

A) Letter uppercase
B) More letters

(1) Parenthesized numbers
(2) More numbers

#. Auto-numbered
#. And another
```

#### Extension: `startnum` (default: on)

List numbering starts from the first number used:

```markdown
5. This starts at five
6. This is six
7. This is seven
```

#### Extension: `task_lists` (default: on)

```markdown
- [ ] Unchecked
- [x] Checked
- [ ] Another unchecked
```

### Block Content in List Items

List items can contain multiple paragraphs, code blocks, etc. — indent continuation by 4 spaces:

```markdown
- First item.

    Second paragraph of first item.

        Code block in list item.

- Second item.
```

**The four-space rule:** Continuation content must be indented to align with the first non-space content of the list item.

### Definition Lists

#### Extension: `definition_lists` (default: on)

```markdown
Term 1
:   Definition 1a

:   Definition 1b

Term 2
:   Definition 2
```

Each term must fit on one line. Definitions start with `:` (or `~`) followed by a space and the definition text. Multiple definitions per term are allowed.

**Compact definition lists** (no blank line between items):

```markdown
Term 1
:   Definition 1

Term 2
:   Definition 2
```

### Example Lists

#### Extension: `example_lists` (default: on)

Numbered examples that continue across the document:

```markdown
(@) First example.
(@) Second example.

Explanation text...

(@) Third example (numbered 3).
```

Labeled examples for cross-referencing:

```markdown
(@good) This is a good example.
(@bad) This is a bad example.

As (@good) illustrates, ...
```

### Ending a List

To end a list and start a non-list paragraph that looks like a list:

```markdown
-   item one
-   item two

<!-- end list -->

1.  Not a list continuation, but starts with a number.
```

Or use an indented code block that isn't part of the list by inserting a blank HTML comment.

## Horizontal Rules

Three or more `*`, `-`, or `_` on a line:

```markdown
***
---
___

* * * * *
- - - - -
```

## Tables

### Extension: `simple_tables` (default: on)

```markdown
  Right     Left     Center     Default
-------     ------ ----------   -------
     12     12        12            12
    123     123       123          123
      1     1          1             1

Table: A simple table with caption.
```

Column alignment is determined by the header text position relative to the dashed line.

### Extension: `multiline_tables` (default: on)

Allow multi-line cell content:

```markdown
-------------------------------------------------------------
 Centered   Default           Right Left
  Header    Aligned         Aligned Aligned
----------- ------- --------------- -------------------------
   First    row                12.0 Example of a row that
                                    spans multiple lines.

  Second    row                 5.0 Here's another one. Note
                                    the blank line between
                                    rows.
-------------------------------------------------------------

Table: Here's the caption. It, too, may span
multiple lines.
```

Must end with a row of dashes, then a blank line.

### Extension: `grid_tables` (default: on)

Most flexible table format:

```markdown
+---------------+---------------+--------------------+
| Fruit         | Price         | Advantages         |
+===============+===============+====================+
| Bananas       | $1.34         | - built-in wrapper |
|               |               | - bright color     |
+---------------+---------------+--------------------+
| Oranges       | $2.10         | - cures scurvy     |
|               |               | - tasty            |
+---------------+---------------+--------------------+

: Grid table with caption.
```

- `=` row separates header from body
- Cells can contain block elements (lists, code blocks, multiple paragraphs)
- Alignment determined by `:` in the separator row

```markdown
+-------+-------+
| Right | Left  |
+------:+:------+
| 12    | 12    |
+-------+-------+
```

### Extension: `pipe_tables` (default: on)

GitHub-style tables:

```markdown
| Right | Left | Default | Center |
|------:|:-----|---------|:------:|
|   12  |  12  |    12   |   12   |
|  123  |  123 |   123   |  123   |
|    1  |  1   |     1   |    1   |

: Pipe table caption
```

**Limitations:**
- Cells cannot contain block elements (no multi-line, no lists)
- Cell contents are always parsed as inlines
- `|` in cells must be escaped: `\|`

### Extension: `table_captions` (default: on)

Add captions with `:` prefix:

```markdown
: This is the table caption.
```

Caption can go before or after the table.

### Extension: `table_attributes`

Add attributes to tables:

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

: Caption {#tbl:my-table .striped}
```

### Choosing a Table Format

| Feature | Simple | Multiline | Grid | Pipe |
|---------|--------|-----------|------|------|
| Multi-line cells | No | Yes | Yes | No |
| Block content in cells | No | No | Yes | No |
| Column alignment | Yes | Yes | Yes | Yes |
| Headerless | Yes | Yes | Yes | No |
| Easy to type | Yes | Medium | No | Yes |
| Widely supported | No | No | No | Yes (GFM) |

**Recommendation:** Use **pipe tables** for simple tables (widely compatible). Use **grid tables** when cells need block content.

## Metadata Blocks

### Extension: `pandoc_title_block` (default: on)

```markdown
% Title
% Author1; Author2
% Date

Document content...
```

Lines can be omitted but `%` must be present:

```markdown
%
% Author
%
```

### Extension: `yaml_metadata_block` (default: on)

More powerful — supports arbitrary metadata:

```yaml
---
title: My Document
author:
  - Jane Doe
  - John Smith
date: 2024-01-15
abstract: |
  This is the abstract.
  It can span multiple lines.
keywords: [pandoc, markdown, conversion]
bibliography: refs.bib
lang: en-US
---
```

**Rules:**
- Must start with `---` on the first line of the document (or after a blank line)
- Must end with `---` or `...`
- Multiple YAML blocks are merged (later values override)
- Fields become template variables and are accessible to filters

**Common metadata fields:**

| Field | Purpose |
|-------|---------|
| `title` | Document title |
| `author` | Author(s) — string or list |
| `date` | Date |
| `abstract` | Abstract text |
| `keywords` | Keywords list |
| `lang` | Language (BCP 47) |
| `dir` | Text direction (ltr/rtl) |
| `bibliography` | Bibliography file(s) |
| `csl` | Citation style file |
| `link-citations` | Hyperlink citations (true/false) |
| `nocite` | Uncited bibliography entries |
| `header-includes` | Raw content for document header |
