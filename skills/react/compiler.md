# React: React Compiler
Based on React 19 documentation.

## What It Does

React Compiler is a build-time tool that automatically memoizes React components and hooks. It eliminates the need for manual `useMemo`, `useCallback`, and `React.memo`.

**Before** (manual memoization):
```jsx
const ExpensiveComponent = memo(function ExpensiveComponent({ data, onClick }) {
  const processedData = useMemo(() => expensiveProcessing(data), [data]);
  const handleClick = useCallback((item) => onClick(item.id), [onClick]);
  return <List data={processedData} onClick={handleClick} />;
});
```

**After** (compiler handles it):
```jsx
function ExpensiveComponent({ data, onClick }) {
  const processedData = expensiveProcessing(data);
  const handleClick = (item) => onClick(item.id);
  return <List data={processedData} onClick={handleClick} />;
}
```

The compiler:
- Skips cascading re-renders by determining which JSX can be reused
- Memoizes expensive computations inside components and hooks
- Only optimizes React components and hooks, not arbitrary functions
- Depends on code following the Rules of React

## Installation

```bash
npm install -D babel-plugin-react-compiler@latest
```

The plugin **must run first** in the Babel plugin pipeline.

### Babel

```js
// babel.config.js
module.exports = {
  plugins: [
    'babel-plugin-react-compiler', // must be first
    // ... other plugins
  ],
};
```

### Vite

```js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: ['babel-plugin-react-compiler'],
      },
    }),
  ],
});
```

### React Router (Vite)

```bash
npm install -D vite-plugin-babel
```

```js
import { defineConfig } from "vite";
import babel from "vite-plugin-babel";
import { reactRouter } from "@react-router/dev/vite";

export default defineConfig({
  plugins: [
    reactRouter(),
    babel({
      filter: /\.[jt]sx?$/,
      babelConfig: {
        presets: ["@babel/preset-typescript"],
        plugins: [["babel-plugin-react-compiler", { /* options */ }]],
      },
    }),
  ],
});
```

### Next.js

Use the built-in support. See [Next.js docs](https://nextjs.org/docs/app/api-reference/next-config-js/reactCompiler).

### React 17 / 18

Install the runtime polyfill as a **production dependency** (not devDependencies):

```bash
npm install react-compiler-runtime@latest
```

Then set the `target` option:

```js
['babel-plugin-react-compiler', { target: '18' }]
```

### ESLint

```bash
npm install -D eslint-plugin-react-hooks@latest
```

Use the `recommended-latest` preset from `eslint-plugin-react-hooks`.

## Configuration

All options are passed as the second element of the Babel plugin tuple:

```js
['babel-plugin-react-compiler', { /* options here */ }]
```

### `compilationMode`

Controls which functions get compiled. Default: `'infer'`.

| Mode | Behavior |
|------|----------|
| `'infer'` | Auto-detects components (PascalCase) and hooks (`use` prefix). Default. |
| `'annotation'` | Only compiles functions with `"use memo"` directive. Best for incremental adoption. |
| `'all'` | Compiles all top-level functions. Not recommended -- may hurt performance. |
| `'syntax'` | Flow-only. Compiles functions using Flow component/hook syntax. |

```js
{ compilationMode: 'annotation' }
```

### `target`

Which React version to target. Default: `'19'`. Use string values.

| Value | Runtime needed |
|-------|---------------|
| `'19'` | None (uses `react/compiler-runtime`) |
| `'18'` | `react-compiler-runtime` package |
| `'17'` | `react-compiler-runtime` package |

```js
{ target: '18' }
```

### `panicThreshold`

How to handle compilation errors. Default: `'none'`.

| Value | Behavior |
|-------|----------|
| `'none'` | Skip problematic components, continue build. Use in production. |
| `'critical_errors'` | Fail on critical errors only. Useful in development. |
| `'all_errors'` | Fail on any compiler diagnostic. Strictest. |

```js
// Different thresholds per environment
{
  panicThreshold: process.env.NODE_ENV === 'development' ? 'critical_errors' : 'none'
}
```

### `logger`

Custom logging for compilation events. Default: `null`.

```js
{
  logger: {
    logEvent(filename, event) {
      switch (event.kind) {
        case 'CompileSuccess':
          console.log(`Compiled: ${filename}`);
          break;
        case 'CompileError':
          console.error(`Skipped: ${filename}`, event.detail.reason);
          if (event.detail.loc) {
            const { line, column } = event.detail.loc.start;
            console.error(`  at line ${line}, column ${column}`);
          }
          break;
      }
    }
  }
}
```

Event kinds: `CompileSuccess`, `CompileError`, `CompileDiagnostic`, `CompileSkip`, `PipelineError`, `Timing`.

### `gating`

Runtime feature flags for A/B testing compiled vs. uncompiled code. Default: `null`.

```js
{
  gating: {
    source: './src/utils/feature-flags',
    importSpecifierName: 'shouldUseCompiler',
  }
}
```

The gating module must export a named function returning a boolean:

```js
// src/utils/feature-flags.js
export function shouldUseCompiler() {
  return getFeatureFlag('react-compiler-enabled');
}
```

The compiler wraps each optimized function in a conditional: if the gate returns `true`, the optimized version runs; otherwise the original. Both versions are in the bundle, increasing bundle size.

## Directives

### `"use memo"` -- Opt In

Forces a function to be compiled. Placed at the start of a function body.

```jsx
function TodoList({ todos }) {
  "use memo";
  const sorted = todos.slice().sort();
  return <ul>{sorted.map(t => <TodoItem key={t.id} todo={t} />)}</ul>;
}
```

Works on hooks too:

```js
function useSortedData(data) {
  "use memo";
  return data.slice().sort();
}
```

In `compilationMode: 'annotation'`, this is the only way functions get compiled.
In `compilationMode: 'infer'`, this forces compilation even for non-standard names.

### `"use no memo"` -- Opt Out

Prevents a function from being compiled. Takes precedence over all compilation modes.

```jsx
function ProblematicComponent({ data }) {
  "use no memo"; // TODO: Fix Rules of React violation (JIRA-123)
  // ...
}
```

### Module-Level Directives

Apply to all functions in a file. Function-level directives override module-level:

```jsx
"use memo";

function A() { /* compiled */ }
function B() { /* compiled */ }
function C() {
  "use no memo"; // overrides module directive
  /* not compiled */
}
```

### Directive Rules

- Must be at the very start of the function body (comments OK before it)
- Use double or single quotes, **not backticks**
- Case-sensitive, exact match required
- `"use no forget"` is an alias for `"use no memo"`

## Incremental Adoption

Three strategies, from coarsest to finest grained.

### 1. Directory-Based (Babel Overrides)

```js
// babel.config.js
module.exports = {
  plugins: [],
  overrides: [
    {
      test: './src/modern/**/*.{js,jsx,ts,tsx}',
      plugins: ['babel-plugin-react-compiler'],
    },
  ],
};
```

Expand coverage over time:

```js
overrides: [
  {
    test: [
      './src/modern/**/*.{js,jsx,ts,tsx}',
      './src/features/**/*.{js,jsx,ts,tsx}',
    ],
    plugins: ['babel-plugin-react-compiler'],
  },
]
```

### 2. Annotation Mode (Per-Component)

Enable the compiler everywhere but only compile opted-in functions:

```js
['babel-plugin-react-compiler', { compilationMode: 'annotation' }]
```

Then add `"use memo"` to components one by one, starting with leaf components.

### 3. Runtime Gating (A/B Testing)

Use the `gating` option to ship both versions and toggle at runtime via feature flags. Useful for measuring performance impact before committing.

## Debugging

### Compiler Errors vs. Runtime Issues

- **Compiler errors** (build-time): Rare. The compiler skips code it cannot handle.
- **Runtime issues**: Code behaves differently when compiled. Usually caused by Rules of React violations.

### Debugging Workflow

1. Add `"use no memo"` to the suspect component
2. If the issue disappears, it is a Rules of React violation
3. Also try removing manual memoization (`useMemo`, `useCallback`, `memo`) to verify the app works without any memoization
4. Fix the violation, remove `"use no memo"`, verify the component shows a sparkle badge in React DevTools

### Common Breaking Patterns

- **Effects depending on referential equality**: Objects/arrays that must maintain the same reference across renders
- **Unstable dependency arrays**: Causing effects to over-fire or infinite loops
- **Conditional logic based on reference checks**: Code that uses `===` on objects for caching decisions

### React DevTools

Compiled components show a sparkle badge in React DevTools. Use this to verify compilation is applied.

### Reporting Bugs

1. Verify it is not a Rules of React violation (check with `eslint-plugin-react-hooks`)
2. Create a minimal reproduction
3. Test without the compiler to confirm it is the cause
4. File at [github.com/facebook/react](https://github.com/facebook/react/issues)

## Compiling Libraries

Library authors can pre-compile before publishing so all consumers benefit.

### Setup

```js
// babel.config.js
module.exports = {
  plugins: ['babel-plugin-react-compiler'],
};
```

### Supporting React 17/18

Add `react-compiler-runtime` as a **production dependency** and set the minimum supported target:

```json
{
  "dependencies": {
    "react-compiler-runtime": "^1.0.0"
  },
  "peerDependencies": {
    "react": "^17.0.0 || ^18.0.0 || ^19.0.0"
  }
}
```

```js
['babel-plugin-react-compiler', { target: '17' }]
```

### Testing

Run the full test suite against both compiled and uncompiled output. Create a separate Babel config without the compiler for comparison.

## Best Practices

- **Follow Rules of React.** The compiler depends on them. Fix ESLint violations first.
- **Start with `panicThreshold: 'none'`** in production so compilation failures are silent skips, not build failures.
- **Use `eslint-plugin-react-hooks`** with the latest recommended config before adopting the compiler.
- **Remove manual memoization gradually.** The compiler handles it, but verify behavior first.
- **Use `"use no memo"` as a temporary escape hatch**, not a permanent solution. Always add a comment explaining why and a tracking issue.
- **Adopt incrementally.** Start with a small directory or annotation mode, expand as confidence grows.
- **Use the logger** during adoption to understand what is and is not being compiled.
- **Place `babel-plugin-react-compiler` first** in the plugin list. It needs unmodified source.

## Common Pitfalls

| Pitfall | Why it breaks | Fix |
|---------|--------------|-----|
| Mutating props or state directly | Violates Rules of React; compiler assumes immutability | Always create new objects/arrays |
| Side effects during render | Compiler may reorder or skip code | Move side effects to `useEffect` |
| Reading `ref.current` during render | Refs are mutable escape hatches the compiler cannot track | Read refs in effects or event handlers |
| Dynamic hook calls (conditionals/loops) | Violates Rules of Hooks | Call hooks at the top level unconditionally |
| Relying on referential equality for correctness | Compiler changes when new objects are created | Use value comparisons or stable references via `useRef` |
| `"use no memo"` placed after code | Directive is ignored if not at function start | Move to first line of function body |
| Using backticks for directives | Not recognized as directives | Use single or double quotes |
