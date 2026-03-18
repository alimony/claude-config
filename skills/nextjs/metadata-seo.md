# Next.js: Metadata & SEO
Based on Next.js documentation (App Router).

## Static Metadata

Export a `metadata` object from `layout.tsx` or `page.tsx` (Server Components only).

```tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'My Site',
  description: 'Site description',
}
```

You cannot export both `metadata` and `generateMetadata` from the same segment. File-based metadata (e.g. `opengraph-image.tsx`) takes priority over both.

### metadataBase

Set a base URL prefix for all URL-based metadata fields. Typically set in root `app/layout.tsx`.

```tsx
export const metadata: Metadata = {
  metadataBase: new URL('https://acme.com'),
  alternates: { canonical: '/' },       // -> https://acme.com
  openGraph: { images: '/og.png' },     // -> https://acme.com/og.png
}
```

Relative paths compose with `metadataBase`; absolute URLs bypass it.

### Title Object

```tsx
// Root layout — template + fallback
export const metadata: Metadata = {
  title: {
    template: '%s | Acme',   // applied to child segments
    default: 'Acme',         // required when using template
  },
}

// Child page
export const metadata: Metadata = {
  title: 'About',            // -> "About | Acme"
}

// Escape template with absolute
export const metadata: Metadata = {
  title: { absolute: 'Custom Title' },  // ignores parent template
}
```

`title.template` applies to **child** segments only, not the segment where it is defined. It has no effect in `page.tsx` (terminal segment).

## Dynamic Metadata — generateMetadata

```tsx
import type { Metadata, ResolvingMetadata } from 'next'

type Props = {
  params: Promise<{ slug: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export async function generateMetadata(
  { params, searchParams }: Props,
  parent: ResolvingMetadata
): Promise<Metadata> {
  const { slug } = await params
  const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json())

  // Extend parent metadata instead of replacing
  const previousImages = (await parent).openGraph?.images || []

  return {
    title: post.title,
    openGraph: {
      images: ['/post-og.jpg', ...previousImages],
    },
  }
}
```

- `params` and `searchParams` are promises (v16+). `searchParams` is only available in `page.tsx`.
- `fetch` inside `generateMetadata` is auto-memoized. Use `React.cache()` when `fetch` is unavailable.
- `redirect()` and `notFound()` work inside `generateMetadata`.

### Streaming Metadata

Dynamic metadata streams separately from UI, so `generateMetadata` does not block rendering. Streaming is **disabled for HTML-limited bots** (Twitterbot, facebookexternalhit, etc.) detected via User-Agent.

Disable streaming entirely:
```ts
// next.config.ts
const config = { htmlLimitedBots: /.*/ }
```

### Memoizing Data Requests

Use `React.cache()` to share data between `generateMetadata` and the page component:

```ts
import { cache } from 'react'
export const getPost = cache(async (slug: string) => {
  return db.query.posts.findFirst({ where: eq(posts.slug, slug) })
})
```

## Metadata Fields Reference

### Core Fields

```tsx
export const metadata: Metadata = {
  title: 'Next.js',
  description: 'The React Framework',
  generator: 'Next.js',
  applicationName: 'My App',
  referrer: 'origin-when-cross-origin',
  keywords: ['Next.js', 'React'],
  authors: [{ name: 'Alice' }, { name: 'Bob', url: 'https://bob.dev' }],
  creator: 'Alice',
  publisher: 'Acme Inc',
  formatDetection: { email: false, address: false, telephone: false },
  category: 'technology',
}
```

### Open Graph

```tsx
export const metadata: Metadata = {
  openGraph: {
    title: 'My Site',
    description: 'Description',
    url: 'https://example.com',
    siteName: 'My Site',
    locale: 'en_US',
    type: 'website',  // or 'article'
    images: [
      { url: 'https://example.com/og.png', width: 1200, height: 630, alt: 'OG image' },
    ],
    // Article-specific:
    // publishedTime: '2024-01-01T00:00:00Z',
    // authors: ['Alice'],
  },
}
```

### Twitter

```tsx
export const metadata: Metadata = {
  twitter: {
    card: 'summary_large_image',
    title: 'My Site',
    description: 'Description',
    creator: '@handle',
    images: ['https://example.com/og.png'],
  },
}
```

### Robots (per-page)

```tsx
export const metadata: Metadata = {
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}
```

### Icons

```tsx
export const metadata: Metadata = {
  icons: {
    icon: '/icon.png',
    shortcut: '/shortcut-icon.png',
    apple: '/apple-icon.png',
    // Multiple sizes:
    // icon: [
    //   { url: '/icon.png' },
    //   { url: '/icon-dark.png', media: '(prefers-color-scheme: dark)' },
    // ],
  },
}
```

### Alternates & Canonical

```tsx
export const metadata: Metadata = {
  alternates: {
    canonical: 'https://example.com',
    languages: { 'en-US': '/en-US', 'de-DE': '/de-DE' },
    media: { 'only screen and (max-width: 600px)': '/mobile' },
    types: { 'application/rss+xml': '/rss' },
  },
}
```

### Verification

```tsx
export const metadata: Metadata = {
  verification: {
    google: 'google-verification-code',
    yandex: 'yandex-verification-code',
    yahoo: 'yahoo-verification-code',
  },
}
```

### Other / Custom

```tsx
export const metadata: Metadata = {
  manifest: '/manifest.json',
  other: { custom: 'meta-value' },
}
```

## Viewport — generateViewport

Viewport is separate from metadata (since Next.js 14). `themeColor` and `colorScheme` belong here, not in `metadata`.

```tsx
import type { Viewport } from 'next'

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
  colorScheme: 'dark light',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}
```

Dynamic variant:
```tsx
export async function generateViewport(): Promise<Viewport> {
  return { themeColor: 'black' }
}
```

Viewport cannot be streamed -- it blocks until resolved because it affects initial page rendering.

## Metadata Merging & Inheritance

Metadata is evaluated root-down: `app/layout.tsx` -> nested layouts -> `page.tsx`.

- **Shallow merge**: duplicate top-level keys are replaced by the closest segment.
- **Nested objects are fully replaced**, not deep-merged. If a child defines `openGraph: { title }`, the parent's `openGraph.description` is lost.
- **Fields not redefined** in child segments are inherited from the parent.

To share nested fields across segments, extract to a shared variable:

```tsx
// app/shared-metadata.ts
export const sharedOG = { images: ['https://example.com/og.png'] }

// app/page.tsx
import { sharedOG } from './shared-metadata'
export const metadata = { openGraph: { ...sharedOG, title: 'Home' } }

// app/about/page.tsx
import { sharedOG } from '../shared-metadata'
export const metadata = { openGraph: { ...sharedOG, title: 'About' } }
```

## File Conventions — Overview

| File | Location | Purpose |
|------|----------|---------|
| `favicon.ico` | `app/` only | Browser tab icon |
| `icon.(ico\|jpg\|png\|svg)` | `app/**/*` | General icon |
| `apple-icon.(jpg\|png)` | `app/**/*` | Apple touch icon |
| `opengraph-image.(jpg\|png\|gif)` | `app/**/*` | OG image |
| `twitter-image.(jpg\|png\|gif)` | `app/**/*` | Twitter card image |
| `opengraph-image.alt.txt` | alongside image | Alt text |
| `sitemap.xml` or `sitemap.ts` | `app/` | Sitemap |
| `robots.txt` or `robots.ts` | `app/` | Robots directives |
| `manifest.json` or `manifest.ts` | `app/` | Web app manifest |

All file conventions also accept `.js`/`.ts`/`.tsx` for dynamic generation. Number suffixes for multiple icons: `icon1.png`, `icon2.png`.

## OG Images — Dynamic Generation

### File-based (opengraph-image.tsx)

```tsx
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og'

export const alt = 'Blog post'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await fetch(`https://api.example.com/posts/${slug}`).then(r => r.json())

  return new ImageResponse(
    (
      <div style={{
        fontSize: 48, background: 'white', width: '100%', height: '100%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {post.title}
      </div>
    ),
    { ...size }
  )
}
```

Config exports: `alt` (string), `size` ({ width, height }), `contentType` (MIME type).

### ImageResponse API

```tsx
import { ImageResponse } from 'next/og'

new ImageResponse(element, {
  width: 1200,              // default 1200
  height: 630,              // default 630
  emoji: 'twemoji',         // 'twemoji' | 'blobmoji' | 'noto' | 'openmoji'
  fonts: [{
    name: 'Inter',
    data: fontBuffer,        // ArrayBuffer — ttf/otf/woff
    weight: 400,
    style: 'normal',
  }],
  debug: false,
  status: 200,
  headers: {},
})
```

- Uses Satori + Resvg. Only **flexbox** layout and a subset of CSS. No `display: grid`.
- Max bundle size: 500KB. Font formats: ttf, otf, woff (ttf/otf preferred).

### Custom Fonts

```tsx
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'

const fontData = await readFile(join(process.cwd(), 'assets/Inter-SemiBold.ttf'))

return new ImageResponse(<div style={{ fontFamily: 'Inter' }}>Hello</div>, {
  fonts: [{ name: 'Inter', data: fontData, style: 'normal', weight: 600 }],
})
```

### generateImageMetadata — Multiple Images

Generate multiple OG images or icons from a single file:

```tsx
// app/icon.tsx
import { ImageResponse } from 'next/og'

export function generateImageMetadata() {
  return [
    { contentType: 'image/png', size: { width: 48, height: 48 }, id: 'small' },
    { contentType: 'image/png', size: { width: 72, height: 72 }, id: 'medium' },
  ]
}

export default async function Icon({ id }: { id: Promise<string | number> }) {
  const iconId = await id
  return new ImageResponse(
    <div style={{
      width: '100%', height: '100%', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      fontSize: 88, background: '#000', color: '#fafafa',
    }}>
      Icon {iconId}
    </div>
  )
}
```

## Generated Icons (favicon, icon, apple-icon)

```tsx
// app/icon.tsx
import { ImageResponse } from 'next/og'

export const size = { width: 32, height: 32 }
export const contentType = 'image/png'

export default function Icon() {
  return new ImageResponse(
    <div style={{
      fontSize: 24, background: 'black', width: '100%', height: '100%',
      display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
    }}>
      A
    </div>,
    { ...size }
  )
}
```

`favicon` can only be in `app/` root. Use `icon` for deeper segments. Cannot generate `favicon` programmatically -- use `icon` instead.

## Sitemap

### Static

Place `app/sitemap.xml` directly.

### Generated

```tsx
// app/sitemap.ts
import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: 'https://acme.com', lastModified: new Date(), changeFrequency: 'yearly', priority: 1 },
    { url: 'https://acme.com/about', lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
  ]
}
```

### With Localization

```tsx
export default function sitemap(): MetadataRoute.Sitemap {
  return [{
    url: 'https://acme.com',
    lastModified: new Date(),
    alternates: {
      languages: { es: 'https://acme.com/es', de: 'https://acme.com/de' },
    },
  }]
}
```

### With Images/Videos

```tsx
return [{
  url: 'https://example.com',
  images: ['https://example.com/image.jpg'],
  videos: [{ title: 'Demo', thumbnail_loc: 'https://example.com/thumb.jpg', description: '...' }],
}]
```

### Multiple Sitemaps (generateSitemaps)

For large sites (Google's limit: 50,000 URLs per sitemap):

```tsx
// app/product/sitemap.ts
export async function generateSitemaps() {
  return [{ id: 0 }, { id: 1 }, { id: 2 }]
}

export default async function sitemap(props: { id: Promise<string> }): Promise<MetadataRoute.Sitemap> {
  const id = await props.id
  const start = Number(id) * 50000
  const products = await getProducts(start, start + 50000)
  return products.map(p => ({ url: `https://acme.com/product/${p.id}`, lastModified: p.date }))
}
// Produces: /product/sitemap/0.xml, /product/sitemap/1.xml, etc.
```

## Robots

### Static

Place `app/robots.txt` directly.

### Generated

```tsx
// app/robots.ts
import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow: '/private/' },
      { userAgent: ['Applebot', 'Bingbot'], disallow: ['/'] },
    ],
    sitemap: 'https://acme.com/sitemap.xml',
    // host: 'https://acme.com',
  }
}
```

## Manifest

### Static

Place `app/manifest.json` or `app/manifest.webmanifest`.

### Generated

```tsx
// app/manifest.ts
import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'My App',
    short_name: 'App',
    description: 'Description',
    start_url: '/',
    display: 'standalone',
    background_color: '#fff',
    theme_color: '#fff',
    icons: [{ src: '/favicon.ico', sizes: 'any', type: 'image/x-icon' }],
  }
}
```

## JSON-LD Structured Data

Render as a `<script>` tag in Server Components. Sanitize `<` to prevent XSS.

```tsx
// app/products/[id]/page.tsx
export default async function Page({ params }) {
  const { id } = await params
  const product = await getProduct(id)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    image: product.image,
    description: product.description,
  }

  return (
    <section>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c'),
        }}
      />
      {/* page content */}
    </section>
  )
}
```

Type with `schema-dts`:
```tsx
import { Product, WithContext } from 'schema-dts'

const jsonLd: WithContext<Product> = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: 'Sticker',
  image: 'https://example.com/sticker.png',
  description: 'A sticker.',
}
```

Validate with [Rich Results Test](https://search.google.com/test/rich-results) or [Schema Markup Validator](https://validator.schema.org/).

## Default Head Tags

Always added automatically, even without any metadata exports:

```html
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

## Key Rules

1. `metadata` and `generateMetadata` are **Server Components only**.
2. You cannot export both `metadata` object and `generateMetadata` from the same segment.
3. File-based metadata (images, sitemap, robots) overrides config-based metadata.
4. Metadata files (`sitemap.ts`, `opengraph-image.tsx`, `icon.tsx`, `robots.ts`) are special Route Handlers, cached by default.
5. Generated images are statically optimized at build time unless they use Dynamic APIs.
6. Metadata merges **shallowly** -- nested objects like `openGraph` are fully replaced, not deep-merged.
7. `themeColor` and `colorScheme` belong in `viewport` export, not `metadata` (deprecated in metadata since v14).
