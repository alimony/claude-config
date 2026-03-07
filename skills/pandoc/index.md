# Pandoc Skills

Based on Pandoc documentation (pandoc.org/MANUAL.html).
Generated from https://pandoc.org/MANUAL.html on 2026-03-07.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [fundamentals](./fundamentals.md) | What Pandoc is, reader-AST-writer pipeline, format specification, PDF creation (all engines), character encoding, reading URLs, exit codes, common patterns | 336 |
| [options](./options.md) | All CLI options: general, reader, writer, format-specific (HTML/LaTeX/EPUB/slides/DOCX), citation rendering, math rendering, wrapper scripts, common combinations | 299 |
| [defaults-templates](./defaults-templates.md) | Defaults YAML files, template syntax (variables, conditionals, loops, partials, pipes), template variables for all output formats (HTML, LaTeX, Beamer, PowerPoint, Typst, ConTeXt, man pages) | 534 |
| [markdown-blocks](./markdown-blocks.md) | Block elements: paragraphs, headings (ATX/setext, identifiers, attributes), block quotes, code blocks (indented/fenced), line blocks, lists (bullet/ordered/definition/example/task), tables (simple/multiline/grid/pipe), metadata blocks (YAML/title) | 558 |
| [markdown-inline](./markdown-inline.md) | Inline elements: emphasis, strikeout, super/subscripts, verbatim, underline, small caps, math, raw HTML/LaTeX, links (inline/reference/internal), images, divs/spans, footnotes, citation syntax, non-default extensions (emoji, alerts, wikilinks, hard line breaks, mark), Markdown variants | 570 |
| [extensions](./extensions.md) | Extension mechanism (+ext/-ext), typography (smart), heading identifiers, math input modes, raw HTML/TeX, literate Haskell, format-specific extensions (org, typst, docx), extension defaults by format, quick reference | 287 |
| [citations](./citations.md) | Citation syntax, bibliography formats (BibTeX/BibLaTeX/CSL JSON/YAML/RIS), CSL styles, citation workflow, note styles, bibliography placement, uncited items, metadata fields, natbib/biblatex for LaTeX | 372 |
| [presentations](./presentations.md) | Slide shows: reveal.js, Beamer, PowerPoint, Slidy; slide structure, incremental lists, pauses, speaker notes, columns, styling, backgrounds, frame attributes, format comparison | 351 |
| [output-formats](./output-formats.md) | EPUBs (metadata, epub:type, linked media, styling), chunked HTML, Jupyter notebooks, Vimdoc, syntax highlighting (styles, custom themes, KDE definitions), custom styles (docx/odt), accessible PDFs (LaTeX/ConTeXt/WeasyPrint/Typst/Prince), PDF engine comparison | 378 |
| [advanced](./advanced.md) | Custom Lua readers/writers, Pandoc as Lua interpreter, web server mode, reproducible builds (SOURCE_DATE_EPOCH), security (sandbox, threats, DoS protection, HTML sanitization) | 198 |

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/pandoc/fundamentals.md
    @~/.claude/skills/pandoc/markdown-blocks.md

Or reference this index to see all available skills:

    @~/.claude/skills/pandoc/index.md

## Coverage

- Total documentation pages read: 1 (single-page manual, ~580KB)
- Skill files created: 10
- Total lines: 3,883
- Pages failed: 0
