# Pandoc: Advanced Features

Based on Pandoc documentation (pandoc.org/MANUAL.html).

## Custom Readers and Writers

Pandoc can be extended with custom readers and writers written in **Lua**. Pandoc includes a Lua interpreter — no separate installation needed.

### Using Custom Readers/Writers

```bash
# Custom writer
pandoc -t data/sample.lua input.md

# Custom reader
pandoc -f my_markup.lua -t latex -s

# Scripts are also searched in the custom/ subdirectory of --data-dir
```

### Writing a Custom Reader

A custom reader defines a `Reader` function that takes a string and returns a Pandoc AST:

```lua
-- my-reader.lua
function Reader(input, opts)
  -- Use lpeg for parsing (available by default)
  local lpeg = require("lpeg")

  -- Build a Pandoc document
  return pandoc.Pandoc({
    pandoc.Para({pandoc.Str("Hello from custom reader")})
  })
end
```

- Use `pandoc.*` functions to create AST elements
- The [lpeg](http://www.inf.puc-rio.br/~roberto/lpeg/) parsing library is available
- Optional second parameter `opts` gives access to reader options (e.g., tab stop)
- See a sample: `pandoc --print-default-data-file creole.lua`

### Writing a Custom Writer

A custom writer defines functions for rendering each AST element:

```lua
-- my-writer.lua
function Writer(doc, opts)
  local result = {}
  for _, block in ipairs(doc.blocks) do
    table.insert(result, render_block(block))
  end
  return table.concat(result, "\n")
end
```

- See [djot-writer.lua](https://github.com/jgm/djot.lua/blob/main/djot-writer.lua) for a full example
- **No default template** — use `--template` manually or add `default.NAME_OF_WRITER.lua` to the `templates/` subdirectory of your data directory

### Custom Writers vs Lua Filters

| Feature | Custom Writer | Lua Filter |
|---------|--------------|------------|
| Purpose | Define a new output format | Transform the AST |
| When | Replaces the writer entirely | Runs between reader and writer |
| Scope | Full document rendering | Element-by-element transformation |
| Usage | `-t mywriter.lua` | `--lua-filter=myfilter.lua` |

Use **filters** to modify the AST before an existing writer processes it. Use **custom writers** when you need a completely new output format.

## Running Pandoc as a Lua Interpreter

```bash
# Direct invocation
pandoc lua script.lua

# Or symlink/rename pandoc to pandoc-lua
pandoc-lua script.lua
```

Behaves like the standalone Lua 5.4 interpreter with extras:

**Available globally:**
- All `pandoc.*` packages
- `re` and `lpeg` libraries
- `PANDOC_VERSION`, `PANDOC_STATE`, `PANDOC_API_VERSION`

**Use cases:**
- Scripting document processing pipelines
- Testing Lua filters interactively
- Using pandoc's AST manipulation from standalone scripts

## Running Pandoc as a Web Server

```bash
# Start the server
pandoc server

# Or symlink/rename pandoc to pandoc-server
pandoc-server

# CGI mode
pandoc-server.cgi
```

Exposes a JSON API for document conversion. See the [pandoc-server documentation](https://github.com/jgm/pandoc/blob/master/doc/pandoc-server.md) for full API details.

**Security:** pandoc-server uses Haskell's type system to guarantee no I/O during conversions — maximally secure by design.

## Reproducible Builds

Some formats (EPUB, docx, ODT) include timestamps, causing different output on successive builds from the same source.

### Using SOURCE_DATE_EPOCH

```bash
# Set a fixed timestamp (Unix epoch seconds)
SOURCE_DATE_EPOCH=1704067200 pandoc input.md -o output.epub

# Use git commit timestamp for reproducibility
SOURCE_DATE_EPOCH=$(git log -1 --format=%ct) pandoc input.md -o output.epub
```

### LaTeX PDF Reproducibility

For reproducible LaTeX PDFs, either:
- Set `pdf-trailer-id` in metadata (explicit ID)
- Leave it undefined — pandoc creates one from a hash of `SOURCE_DATE_EPOCH` + document contents

### EPUB Reproducibility

Set `identifier` explicitly in metadata:

```yaml
---
identifier:
- scheme: DOI
  text: doi:10.1234/my-book
---
```

## Security

### Threat Model

| Threat | Risk | Mitigation |
|--------|------|------------|
| **Malicious filters/writers** | Can do anything on filesystem | Audit filters carefully |
| **Include directives** | LaTeX, Org, RST, Typst can read files | Use `--sandbox` |
| **Embedded images** | RTF, FB2, HTML+self-contained, EPUB, Docx, ODT embed files | Use `--sandbox` |
| **iframe fetching** | HTML reader fetches iframe src content | Use `-f html+raw_html` or `--sandbox` |
| **Pathological input** | Parser DoS on crafted input | Use timeout, heap limits |
| **Raw HTML passthrough** | XSS if `raw_html` enabled | Sanitize output HTML |

### Sandbox Mode

```bash
# Prevent all file system access during conversion
pandoc --sandbox input.md -o output.html
```

`--sandbox` prevents:
- Reading files via include directives
- Embedding local images
- Fetching iframe contents

**Trade-off:** Also prevents including images in self-contained formats.

### For Haskell Library Users

Run pandoc operations in the `PandocPure` monad for complete filesystem isolation. See [Using the Pandoc API](https://pandoc.org/using-the-pandoc-api.html).

### Performance/DoS Protection

```bash
# Limit heap size to 512MB
pandoc +RTS -M512M -RTS input.md -o output.html
```

**Tip:** The `commonmark` parser (including `commonmark_x` and `gfm`) is much less vulnerable to pathological performance than the `markdown` parser. **Use `commonmark` or `gfm` for untrusted input.**

### HTML Output Safety

Pandoc-generated HTML is **not guaranteed safe**:
- With `raw_html` enabled, users can inject arbitrary HTML
- Even without `raw_html`, dangerous content can appear in URLs/attributes
- **Always run output through an HTML sanitizer** when processing untrusted input

## Security Checklist

1. **Audit all filters and custom writers** before use
2. **Use `--sandbox`** when processing untrusted input
3. **Use `commonmark`/`gfm` reader** instead of `markdown` for untrusted input
4. **Set heap limits** (`+RTS -M512M -RTS`) for server deployments
5. **Sanitize HTML output** before serving to browsers
6. **Don't use `--self-contained`** with untrusted input (embeds local files)
7. **Set timeouts** for pandoc operations in server/API contexts
