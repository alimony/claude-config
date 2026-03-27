# Wrangler: Builds & Bundling
Based on Wrangler documentation from developers.cloudflare.com.

## How Wrangler Bundles Code

Wrangler uses **esbuild** under the hood. When you run `wrangler dev` or `wrangler deploy`, it:

1. Resolves your `main` entrypoint
2. Bundles all imports (including npm dependencies from `package.json`)
3. Handles non-JS assets (`.txt`, `.html`, `.wasm`, etc.) as typed modules
4. Uploads the result

Preview the bundle output without deploying:

```sh
npx wrangler deploy --dry-run --outdir dist
```

## Default Module Handling

These file types are automatically handled (not inlined into JS):

| Extension       | Imported As            |
|-----------------|------------------------|
| `.txt`          | `string`               |
| `.html`         | `string`               |
| `.sql`          | `string`               |
| `.bin`          | `ArrayBuffer`          |
| `.wasm`         | `WebAssembly.Module`   |

Note: `WebAssembly.instantiateStreaming()` is **not supported** in Workers.

## Key Configuration Fields

All fields go in `wrangler.toml` (or `wrangler.jsonc`).

### Entrypoint

```toml
main = "./src/index.ts"
```

### Minification

```toml
minify = true
```

### Keep Function Names

Defaults to `true`. Controls esbuild's `keepNames` option (useful for stack traces):

```toml
keep_names = true
```

### Disable Bundling Entirely

```toml
no_bundle = true
```

When `no_bundle = true`:
- Wrangler skips all internal build steps
- No minification, no polyfill injection
- Your code must be plain JS with no unresolved dependencies
- `find_additional_modules` defaults to `true` automatically

CLI equivalent: `npx wrangler deploy --no-bundle`

## Custom Builds

Use `[build]` when you need your own build step (Webpack, Rollup, custom scripts, etc.) to run **before** Wrangler processes the output.

### Configuration

```toml
[build]
command = "npm run build"
cwd = "build_cwd"
watch_dir = "build_watch_dir"
```

Equivalent JSON (`wrangler.jsonc`):

```jsonc
{
  "build": {
    "command": "npm run build",
    "cwd": "build_cwd",
    "watch_dir": "build_watch_dir"
  }
}
```

### Fields

| Field       | Type                 | Default | Description                                      |
|-------------|----------------------|---------|--------------------------------------------------|
| `command`   | `string`             | --      | Shell command to build your Worker                |
| `cwd`       | `string`             | `.`     | Working directory for the command                 |
| `watch_dir` | `string \| string[]` | `.`     | Directories watched for changes during `wrangler dev` |

### Shell Behavior

- **Linux/macOS**: command runs in `sh`
- **Windows**: command runs in `cmd`
- `&&` and `||` operators work on both platforms

### Watch Mode

During `wrangler dev`, Wrangler monitors `watch_dir` for file changes and re-runs the build command automatically. Watch multiple directories:

```toml
[build]
command = "npm run build"
watch_dir = ["src", "shared"]
```

### Common Patterns

**TypeScript with a custom tsconfig:**

```toml
[build]
command = "tsc --project tsconfig.worker.json && node scripts/post-build.js"
watch_dir = "src"
```

**Webpack or Rollup:**

```toml
main = "./dist/index.js"

[build]
command = "npx webpack --config webpack.worker.config.js"
watch_dir = "src"
```

**Multi-step build with pre/post processing:**

```toml
[build]
command = "node scripts/generate-routes.js && npx esbuild src/index.ts --bundle --outfile=dist/worker.js"
cwd = "."
watch_dir = ["src", "scripts"]
```

The `main` entrypoint should point to whatever your custom build produces.

## Module Rules

Define how non-standard file types are imported. Five module types are available:

- `ESModule` -- ES module format
- `CommonJS` -- CommonJS format
- `CompiledWasm` -- pre-compiled WebAssembly
- `Text` -- imported as string
- `Data` -- imported as ArrayBuffer

### Basic Rule

```toml
[[rules]]
type = "Text"
globs = ["**/*.md"]
```

### Multiple Rules with Fallthrough

When `fallthrough = true`, a file can match multiple rules (processed in order):

```toml
[[rules]]
type = "Text"
globs = ["**/*.md"]
fallthrough = true

[[rules]]
type = "Text"
globs = ["**/*.csv"]
```

### Treating JS as ESModule

If your `.js` files are ES modules but Wrangler treats them as CommonJS:

```toml
[[rules]]
type = "ESModule"
globs = ["**/*.js"]
```

## Additional Modules (Dynamic Imports)

For lazy-loaded or dynamically imported files that esbuild cannot statically resolve:

```toml
find_additional_modules = true
base_dir = "./src"

[[rules]]
type = "ESModule"
globs = ["./lang/**/*.mjs"]
```

This traverses the file tree below `base_dir` and includes matching files as unbundled external modules. Useful for:

- Large dynamically imported files you want loaded on demand
- Variable-based dynamic imports: `await import(\`./lang/${language}.mjs\`)`
- Partial bundling -- only some source files match the rules

### Related Options

```toml
# Directory for evaluating module rules (defaults to directory of main)
base_dir = "./src"

# Preserve original file names instead of prepending content hashes
preserve_file_names = true
```

Without `preserve_file_names`, files get hashed names like `34de60b44167af5c-favicon.ico`.

## Conditional Exports (package.json)

Wrangler respects the `exports` field in `package.json` and specifically looks for the **`workerd`** condition key. This lets npm packages ship Workers-specific code:

```json
{
  "exports": {
    ".": {
      "workerd": "./src/worker-entry.js",
      "default": "./src/index.js"
    }
  }
}
```

## Decision Guide: Default Bundling vs Custom Builds

**Use default esbuild bundling when:**
- Standard TypeScript/JavaScript project
- npm dependencies resolve cleanly
- No special compilation steps needed

**Use custom builds when:**
- You need Webpack, Rollup, or another bundler
- Pre-processing steps (code generation, route manifests)
- Complex TypeScript configurations
- Monorepo setups where you need to build shared packages first

**Use `no_bundle` when:**
- Your code is already fully bundled by an external tool
- You want complete control over the output
- Pre-built WASM or vendored dependencies

## Common Pitfalls

1. **esbuild is pre-1.0** -- Wrangler minor version updates can include breaking bundling changes. Pin your Wrangler version in CI.

2. **Custom build + missing `main`** -- When using `[build]`, ensure `main` points to the file your build command **produces**, not your source file.

3. **`no_bundle` requires self-contained code** -- No npm imports, no TypeScript, no JSX. Everything must be resolved before Wrangler sees it.

4. **`watch_dir` defaults to `.`** -- In large repos this can be noisy. Always set it explicitly to your source directory.

5. **Module rules are ordered** -- Rules are matched top-to-bottom. Use `fallthrough = true` if you need a file to match multiple rules.

6. **`find_additional_modules` + `no_bundle`** -- When `no_bundle` is `true`, `find_additional_modules` automatically becomes `true`. If you set explicit rules, they apply to the unbundled traversal.

7. **WASM imports** -- Use `import wasm from "./module.wasm"` (not `instantiateStreaming`). The runtime does not support streaming instantiation.

8. **Not applicable with Vite plugin** -- `[build]`, `no_bundle`, `find_additional_modules`, `base_dir`, and `minify` are ignored when using the Cloudflare Vite plugin. Use Vite's own config instead.
