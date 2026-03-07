# Pandoc: Slide Presentations

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## Supported Slide Formats

| Format | Output flag | Type |
|--------|-----------|------|
| reveal.js | `-t revealjs` | HTML + JS |
| Beamer | `-t beamer` | LaTeX → PDF |
| PowerPoint | `-o file.pptx` | OOXML |
| Slidy | `-t slidy` | HTML + JS |
| Slideous | `-t slideous` | HTML + JS |
| DZSlides | `-t dzslides` | HTML (self-contained) |
| S5 | `-t s5` | HTML + JS |

## Quick Start

```bash
# HTML slides (reveal.js)
pandoc -t revealjs -s slides.md -o slides.html

# PDF slides (Beamer/LaTeX)
pandoc -t beamer slides.md -o slides.pdf

# PowerPoint
pandoc slides.md -o slides.pptx

# Self-contained HTML (no external dependencies)
pandoc -t revealjs -s --self-contained slides.md -o slides.html
```

## Slide Structure

### How Headings Map to Slides

The **slide level** determines which heading level creates new slides. By default, it's the highest heading level that is followed immediately by content (not another heading).

```markdown
% My Presentation        ← Title slide (from metadata)
% Author Name
% Date

# Section Title           ← Title slide (above slide level)

## Slide One              ← New slide (at slide level = 2)
- Content here

## Slide Two              ← New slide
More content

---                       ← Horizontal rule always starts new slide
Content on its own slide
```

**Override with `--slide-level`:**

```bash
# All h1 headings = slides
pandoc -t revealjs --slide-level=1 -s slides.md -o slides.html

# Flat layout (only horizontal rules create slides)
pandoc -t revealjs --slide-level=0 -s slides.md -o slides.html
```

**Rules:**
- Horizontal rule (`---`) always starts a new slide
- Heading at slide level starts a new slide
- Headings *below* slide level create sub-headings within a slide (in Beamer: "blocks")
- Headings *above* slide level create section title slides

**reveal.js note:** With slide level 2, you get a 2D layout (h1 = horizontal, h2 = vertical). Use `--slide-level=0` for a flat 1D layout.

### PowerPoint Layout Choice

The pptx writer automatically selects layouts based on content:

| Layout | When Used |
|--------|-----------|
| **Title Slide** | Initial slide from metadata (title, author, date) |
| **Section Header** | Headings above slide level |
| **Two Content** | Slides with `::: columns` containing 2+ columns |
| **Comparison** | Two-column slides where a column has text + non-text |
| **Content with Caption** | Non-column slides with text followed by image/table |
| **Blank** | Slides with only blank content or speaker notes |
| **Title and Content** | Everything else |

Layouts come from the reference doc (`--reference-doc`).

## Incremental Lists

```bash
# All lists display incrementally
pandoc -t revealjs -s -i slides.md -o slides.html
```

**Per-list override using fenced divs:**

```markdown
::: incremental
- Item 1
- Item 2
- Item 3
:::

::: nonincremental
- All at once
- Regardless of -i flag
:::
```

**Legacy method:** Lists inside blockquotes toggle the default behavior.

## Pauses

Insert a pause within a slide with three dots separated by spaces:

```markdown
# My Slide

Content before the pause

. . .

Content after the pause
```

**Note:** Pauses are not yet supported in PowerPoint output.

## Speaker Notes

```markdown
## My Slide

Visible content here.

::: notes
These are speaker notes.

- They can contain Markdown
- Press `s` in reveal.js to see them
:::
```

**PowerPoint title slide notes** — use the `notes` metadata field:

```yaml
---
title: My Presentation
author: Jane Doe
notes: |
  Welcome everyone.
  Remember to introduce yourself.
---
```

## Columns

```markdown
:::::::::::::: {.columns}
::: {.column width="40%"}
Left column content
:::
::: {.column width="60%"}
Right column content
:::
::::::::::::::
```

**Note:** Column widths don't currently work for PowerPoint.

### Beamer Column Attributes

```markdown
:::::::::::::: {.columns align=center totalwidth=8em}
::: {.column width="40%" align=center}
Left content
:::
::: {.column width="60%" align=bottom}
Right content
:::
::::::::::::::
```

- `align`: `top`, `top-baseline`, `center`, `bottom` (default: `top`)
- `totalwidth`: limits total column width
- `.onlytextwidth` class: sets `totalwidth` to `\textwidth`

## Styling

### reveal.js

```bash
# Use a built-in theme
pandoc -t revealjs -s -V theme=moon slides.md -o slides.html

# Custom CSS
pandoc -t revealjs -s --css=custom.css slides.md -o slides.html
```

All reveal.js configuration options can be set via `-V` variables.

### Beamer

```bash
# Theme
pandoc -t beamer -V theme:Warsaw slides.md -o slides.pdf

# Full theme customization
pandoc -t beamer \
  -V theme:Madrid \
  -V colortheme:seahorse \
  -V fonttheme:structurebold \
  slides.md -o slides.pdf
```

### PowerPoint

Use `--reference-doc` to apply a custom template:

```bash
pandoc --reference-doc=my-template.pptx slides.md -o slides.pptx
```

## Beamer Frame Attributes

Add LaTeX frame options via heading classes:

```markdown
# Code Slide {.fragile}

# Bibliography {.allowframebreaks}

# Important {.standout}
```

Available frame attributes: `allowdisplaybreaks`, `allowframebreaks`, `b`, `c`, `s`, `t`, `environment`, `label`, `plain`, `shrink`, `standout`, `noframenumbering`, `squeeze`.

Custom frame options:

```markdown
# Heading {frameoptions="squeeze,shrink,customoption=foobar"}
```

### Beamer Blocks

Headings below slide level become blocks. Special classes:

```markdown
## Slide Title

### Regular Block
Content in a `block` environment.

### Example {.example}
Content in an `exampleblock` environment.

### Warning {.alert}
Content in an `alertblock` environment.
```

## Background Images

### On All Slides

```yaml
---
background-image: /path/to/image.png
---
```

- **Beamer/reveal.js:** Uses `background-image` metadata
- **PowerPoint:** Set backgrounds in reference doc layouts

### On Individual Slides (reveal.js, pptx)

```markdown
## {background-image="/path/to/image.jpg"}

Slide content with custom background.
```

Additional reveal.js background options: `background-size`, `background-repeat`, `background-color`, `transition`, `transition-speed`.

### On the Title Slide (reveal.js)

```yaml
---
title: My Slide Show
parallaxBackgroundImage: /path/to/bg.png
title-slide-attributes:
  data-background-image: /path/to/title_image.png
  data-background-size: contain
---
```

### Parallax Background (reveal.js)

```yaml
---
parallaxBackgroundImage: /path/to/image.png
parallaxBackgroundSize: 2100px 900px
parallaxBackgroundHorizontal: 200
parallaxBackgroundVertical: 50
---
```

## Format Comparison

| Feature | reveal.js | Beamer | PowerPoint | Slidy |
|---------|-----------|--------|------------|-------|
| Incremental lists | Yes | Yes | Yes | Yes |
| Pauses | Yes | Yes | No | Yes |
| Speaker notes | Yes | Yes | Yes | No |
| Columns | Yes | Yes | Yes | Yes |
| Background images | Yes | Yes | Yes (ref doc) | No |
| Custom themes | CSS/config | LaTeX themes | Reference doc | CSS |
| Self-contained | `--self-contained` | PDF is self-contained | Always | `--self-contained` |
| 2D navigation | Yes (slide-level=2) | No | No | No |

## Common Patterns

### Minimal reveal.js Presentation

```bash
pandoc -t revealjs -s \
  -V theme=black \
  -V transition=slide \
  -V slideNumber=true \
  slides.md -o slides.html
```

### Academic Beamer Presentation

```bash
pandoc -t beamer \
  -V theme:Madrid \
  -V colortheme:default \
  --toc \
  --slide-level=2 \
  slides.md -o slides.pdf
```

### Converting reveal.js to PDF

Print the reveal.js slides from the browser (append `?print-pdf` to URL), or:

```bash
# Direct PDF via Beamer
pandoc -t beamer slides.md -o slides.pdf
```
