# Next.js: Styling
Based on Next.js documentation (App Router).

## CSS Modules

CSS Modules scope styles locally by generating unique class names. Use `.module.css` extension.

```css
/* app/blog/blog.module.css */
.blog {
  padding: 24px;
}
```

```tsx
// app/blog/page.tsx
import styles from './blog.module.css'

export default function Page() {
  return <main className={styles.blog}></main>
}
```

- Files must use `.module.css` (or `.module.scss` with Sass)
- Can be imported in any component inside `app/`
- Class names accessed as properties on the imported `styles` object
- No naming collisions across files

## Global CSS

Import global styles in any layout, page, or component. For app-wide styles, import in the root layout.

```css
/* app/global.css */
body {
  padding: 20px 20px 60px;
  max-width: 680px;
  margin: 0 auto;
}
```

```tsx
// app/layout.tsx
import './global.css'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

**Caveat:** Next.js uses React's built-in stylesheet support with Suspense. Stylesheets are not removed when navigating between routes, which can cause conflicts. Use global CSS only for truly global styles (resets, base styles). Prefer CSS Modules or Tailwind for component styling.

### External Stylesheets

Import third-party CSS anywhere in `app/`:

```tsx
import 'bootstrap/dist/css/bootstrap.css'
```

In React 19, `<link rel="stylesheet" href="..." />` can also be used directly.

## CSS Ordering and Merging

In production, Next.js automatically chunks and merges stylesheets. Order depends on **import order** in your code.

```tsx
// base-button.module.css loads first because BaseButton is imported first
import { BaseButton } from './base-button'
import styles from './page.module.css'
```

**Recommendations for predictable ordering:**
- Contain CSS imports to a single JS/TS entry file when possible
- Import global styles in root layout
- Use consistent naming (`<name>.module.css`)
- Extract shared styles into shared components
- Disable auto-sort-imports linters (e.g., ESLint `sort-imports`)
- Use `cssChunking` in `next.config.js` to control chunking behavior

## Tailwind CSS

### Tailwind v4 (default)

```bash
npm install -D tailwindcss @tailwindcss/postcss
```

```js
// postcss.config.mjs
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

```css
/* app/globals.css */
@import 'tailwindcss';
```

Import in root layout:

```tsx
// app/layout.tsx
import './globals.css'
```

### Tailwind v3 (broader browser support)

```bash
npm install -D tailwindcss@^3 postcss autoprefixer
npx tailwindcss init -p
```

```js
// tailwind.config.js
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: { extend: {} },
  plugins: [],
}
```

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Tailwind CSS works with Turbopack (since Next.js 13.1).

## Sass

Built-in support after installing the package. Works with `.scss`, `.sass`, `.module.scss`, and `.module.sass`.

```bash
npm install --save-dev sass
```

### Configuration

```ts
// next.config.ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  sassOptions: {
    additionalData: `$var: red;`,  // prepended to every Sass file
  },
}
export default nextConfig
```

Use `implementation: 'sass-embedded'` for the embedded Sass compiler:

```ts
sassOptions: {
  implementation: 'sass-embedded',
}
```

### Exporting Sass Variables to JS

```scss
/* app/variables.module.scss */
$primary-color: #64ff00;

:export {
  primaryColor: $primary-color;
}
```

```tsx
import variables from './variables.module.scss'

export default function Page() {
  return <h1 style={{ color: variables.primaryColor }}>Hello!</h1>
}
```

## CSS-in-JS

CSS-in-JS libraries **only work in Client Components** (`'use client'`). They cannot be used directly in Server Components.

### Supported Libraries

ant-design, chakra-ui, @fluentui/react-components, kuma-ui, @mui/material, @mui/joy, pandacss, styled-jsx, styled-components, stylex, tamagui, tss-react, vanilla-extract.

**Working on support:** emotion.

### Setup Pattern (3 steps)

1. Create a **style registry** to collect CSS rules during render
2. Use `useServerInsertedHTML` hook to inject rules before content
3. Wrap your app with the registry Client Component

### styled-components

Enable in config:

```js
// next.config.js
module.exports = {
  compiler: {
    styledComponents: true,
  },
}
```

Create registry:

```tsx
// lib/registry.tsx
'use client'

import React, { useState } from 'react'
import { useServerInsertedHTML } from 'next/navigation'
import { ServerStyleSheet, StyleSheetManager } from 'styled-components'

export default function StyledComponentsRegistry({
  children,
}: {
  children: React.ReactNode
}) {
  const [styledComponentsStyleSheet] = useState(() => new ServerStyleSheet())

  useServerInsertedHTML(() => {
    const styles = styledComponentsStyleSheet.getStyleElement()
    styledComponentsStyleSheet.instance.clearTag()
    return <>{styles}</>
  })

  if (typeof window !== 'undefined') return <>{children}</>

  return (
    <StyleSheetManager sheet={styledComponentsStyleSheet.instance}>
      {children}
    </StyleSheetManager>
  )
}
```

Wrap in root layout:

```tsx
// app/layout.tsx
import StyledComponentsRegistry from './lib/registry'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <StyledComponentsRegistry>{children}</StyledComponentsRegistry>
      </body>
    </html>
  )
}
```

### styled-jsx

Same pattern -- create registry with `StyleRegistry` and `createStyleRegistry` from `styled-jsx`, wrap in root layout. Requires `styled-jsx` v5.1.0+.

## Fonts (`next/font`)

Automatically optimizes fonts, self-hosts them, and eliminates external network requests. No layout shift (CLS).

### Google Fonts

Fonts are downloaded at build time and served from your domain. No browser requests to Google.

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.className}>
      <body>{children}</body>
    </html>
  )
}
```

Variable fonts don't need `weight`. Non-variable fonts require it:

```tsx
const roboto = Roboto({
  weight: ['400', '700'],
  style: ['normal', 'italic'],
  subsets: ['latin'],
  display: 'swap',
})
```

Multi-word font names use underscores: `Roboto_Mono`.

### Local Fonts

```tsx
import localFont from 'next/font/local'

const myFont = localFont({
  src: './my-font.woff2',
  display: 'swap',
})
```

Multiple files for one family:

```ts
const roboto = localFont({
  src: [
    { path: './Roboto-Regular.woff2', weight: '400', style: 'normal' },
    { path: './Roboto-Italic.woff2', weight: '400', style: 'italic' },
    { path: './Roboto-Bold.woff2', weight: '700', style: 'normal' },
  ],
})
```

Font files can live in `public/` or colocated in `app/`.

### Font API Options

| Option | google | local | Description |
|--------|--------|-------|-------------|
| `src` | - | required | Path string or array of `{path, weight?, style?}` |
| `weight` | required* | required* | Single string, range (`'100 900'`), or array. *Not needed for variable fonts |
| `style` | optional | optional | `'normal'`, `'italic'`, or array |
| `subsets` | optional | - | Array of subset names (e.g., `['latin']`). Triggers preload link |
| `axes` | optional | - | Extra variable font axes (e.g., `['slnt']`) |
| `display` | optional | optional | `'swap'` (default), `'auto'`, `'block'`, `'fallback'`, `'optional'` |
| `preload` | optional | optional | Boolean, default `true` |
| `fallback` | optional | optional | Array of fallback font names |
| `adjustFontFallback` | optional | optional | Google: boolean (default `true`). Local: `'Arial'` (default), `'Times New Roman'`, or `false` |
| `variable` | optional | optional | CSS variable name string (e.g., `'--font-inter'`) |
| `declarations` | - | optional | Array of `{prop, value}` for extra `@font-face` descriptors |

### Applying Fonts

Three methods:
- **`className`**: `<p className={inter.className}>` -- most common
- **`style`**: `<p style={inter.style}>` -- inline style object
- **CSS variable**: Set `variable: '--font-inter'`, apply `.variable` class to parent, use `var(--font-inter)` in CSS

### Multiple Fonts

Centralize in a definitions file:

```ts
// app/fonts.ts
import { Inter, Roboto_Mono } from 'next/font/google'

export const inter = Inter({ subsets: ['latin'], display: 'swap' })
export const roboto_mono = Roboto_Mono({ subsets: ['latin'], display: 'swap' })
```

Import where needed. Each font function call is one instance -- define once, import many times.

### Fonts with Tailwind CSS

Use `variable` option to create CSS variables, then wire into Tailwind theme:

```tsx
// app/layout.tsx
const inter = Inter({ subsets: ['latin'], display: 'swap', variable: '--font-inter' })
const roboto_mono = Roboto_Mono({ subsets: ['latin'], display: 'swap', variable: '--font-roboto-mono' })

// Apply variables to <html>
<html className={`${inter.variable} ${roboto_mono.variable} antialiased`}>
```

Tailwind v4:
```css
/* global.css */
@import 'tailwindcss';

@theme inline {
  --font-sans: var(--font-inter);
  --font-mono: var(--font-roboto-mono);
}
```

Tailwind v3:
```js
// tailwind.config.js
theme: {
  extend: {
    fontFamily: {
      sans: ['var(--font-inter)'],
      mono: ['var(--font-roboto-mono)'],
    },
  },
},
```

Then use `font-sans` / `font-mono` utility classes.

### Preloading Behavior

Fonts are preloaded based on where the font function is called:
- **Page file** -- preloaded on that route only
- **Layout file** -- preloaded on all routes wrapped by that layout
- **Root layout** -- preloaded on all routes

## Best Practices

1. **Prefer Tailwind CSS** for most styling -- utility classes cover common patterns
2. **Use CSS Modules** when Tailwind isn't sufficient for component-specific styles
3. **Avoid CSS-in-JS in Server Components** -- it only works in Client Components
4. **Use variable fonts** -- better performance and flexibility than static weights
5. **Define fonts once** in a shared file, import everywhere
6. **Always set `display: 'swap'`** for web fonts to avoid invisible text during load
7. **Specify `subsets`** for Google Fonts to reduce file size and enable preloading
8. **Check production build** for CSS order -- dev mode ordering may differ
9. **Minimize font count** -- each font is an additional download
10. **Use `adjustFontFallback`** (enabled by default) to reduce CLS with size-adjusted fallbacks
