# Next.js: Images & Media
Based on Next.js documentation (App Router).

## Image Component (`next/image`)

Extends `<img>` with automatic optimization: format conversion (WebP/AVIF), responsive sizing, lazy loading, and layout shift prevention.

```jsx
import Image from 'next/image'

// Local image (static import — width/height/blurDataURL auto-detected)
import profilePic from './profile.png'
<Image src={profilePic} alt="Profile" placeholder="blur" />

// Local image (public dir — must specify width/height)
<Image src="/profile.png" alt="Profile" width={500} height={500} />

// Remote image (must specify width/height, configure remotePatterns)
<Image src="https://cdn.example.com/photo.jpg" alt="Photo" width={800} height={600} />
```

### Required Props

| Prop | Type | Notes |
|------|------|-------|
| `src` | `string \| StaticImport` | Path, URL, or static import |
| `alt` | `string` | Required. Use `alt=""` for decorative images |
| `width` | `number` | Intrinsic px. Not needed for static imports or `fill` |
| `height` | `number` | Intrinsic px. Not needed for static imports or `fill` |

`width`/`height` set aspect ratio for space reservation, not rendered size (CSS controls that).

### Key Optional Props

| Prop | Type | Default | Notes |
|------|------|---------|-------|
| `fill` | `boolean` | `false` | Image fills parent. Parent needs `position: relative/fixed/absolute`. Omit `width`/`height`. |
| `sizes` | `string` | — | Media query string for responsive `srcset`. Use with `fill` or responsive CSS. |
| `quality` | `number` | `75` | 1-100. Must match a value in `qualities` config. |
| `loading` | `string` | `"lazy"` | `"lazy"` or `"eager"`. |
| `preload` | `boolean` | `false` | Inserts `<link>` preload in `<head>`. Use for LCP/hero images. |
| `placeholder` | `string` | `"empty"` | `"empty"`, `"blur"`, or `"data:image/..."`. |
| `blurDataURL` | `string` | — | Auto-generated for static imports. Provide manually for remote images. Keep tiny (10px or less). |
| `loader` | `function` | — | `({ src, width, quality }) => url`. Requires `'use client'`. |
| `unoptimized` | `boolean` | `false` | Serve as-is. Auto-true when `src` ends in `.svg`. |
| `style` | `object` | — | Inline CSS. Set `height: 'auto'` when overriding `width`. |
| `onLoad` | `function` | — | Fires after load. Requires `'use client'`. |
| `onError` | `function` | — | Fires on load failure. Requires `'use client'`. |
| `overrideSrc` | `string` | — | Override the `src` attr on rendered `<img>` (SEO migration). |
| `decoding` | `string` | `"async"` | `"async"`, `"sync"`, or `"auto"`. |

`priority` is deprecated in Next.js 16 — use `preload` or `loading="eager"` instead.

### `fill` Mode

Makes image fill its parent container. Always pair with `sizes` to avoid downloading oversized images.

```jsx
<div style={{ position: 'relative', width: '100%', height: '400px' }}>
  <Image
    src="/hero.jpg"
    alt="Hero"
    fill
    sizes="100vw"
    style={{ objectFit: 'cover' }}
  />
</div>
```

Parent **must** have `position: relative`, `fixed`, or `absolute`. Use `objectFit` (`"cover"`, `"contain"`) to control cropping.

### `sizes` Prop

Tells the browser how wide the image will be at different viewports. Without it, browser assumes `100vw` and may download oversized images.

```jsx
<Image
  fill
  src="/photo.jpg"
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
/>
```

- Without `sizes`: generates limited `srcset` (1x, 2x) — for fixed-size images.
- With `sizes`: generates full `srcset` (640w, 750w, ...) — for responsive layouts.

### Responsive Patterns

**Static import (responsive full-width):**
```jsx
import mountains from '../public/mountains.jpg'

<Image
  src={mountains}
  alt="Mountains"
  sizes="100vw"
  style={{ width: '100%', height: 'auto' }}
/>
```

**Remote image (responsive):**
```jsx
<Image
  src={photoUrl}
  alt="Photo"
  width={500}
  height={300}
  sizes="100vw"
  style={{ width: '100%', height: 'auto' }}
/>
```

### Art Direction with `getImageProps`

Use `getImageProps()` for `<picture>` element patterns (different images per viewport):

```jsx
import { getImageProps } from 'next/image'

export default function Home() {
  const common = { alt: 'Hero', sizes: '100vw' }
  const { props: { srcSet: desktop } } = getImageProps({
    ...common, width: 1440, height: 875, src: '/desktop.jpg',
  })
  const { props: { srcSet: mobile, ...rest } } = getImageProps({
    ...common, width: 750, height: 1334, src: '/mobile.jpg',
  })

  return (
    <picture>
      <source media="(min-width: 1000px)" srcSet={desktop} />
      <source media="(min-width: 500px)" srcSet={mobile} />
      <img {...rest} style={{ width: '100%', height: 'auto' }} />
    </picture>
  )
}
```

`getImageProps` returns props for the underlying `<img>`, useful for canvas, CSS background-image (`image-set()`), or `<picture>`.

### Theme Detection (Light/Dark)

Use CSS media queries to show/hide the correct image:

```css
.imgDark { display: none; }
@media (prefers-color-scheme: dark) {
  .imgLight { display: none; }
  .imgDark { display: unset; }
}
```

```jsx
<Image src="/light.png" className={styles.imgLight} {...rest} />
<Image src="/dark.png" className={styles.imgDark} {...rest} />
```

Do not use `preload` or `loading="eager"` — both images would load. Use `fetchPriority="high"` if needed.

## Image Configuration (`next.config.js`)

### `remotePatterns` (required for remote images)

```js
module.exports = {
  images: {
    remotePatterns: [
      // URL shorthand (Next.js 15.3+)
      new URL('https://cdn.example.com/assets/**'),
      // Object form
      {
        protocol: 'https',
        hostname: '**.example.com',   // ** = any subdomain
        port: '',
        pathname: '/images/**',       // ** = any path segments
        search: '',                   // empty = block query strings
      },
    ],
  },
}
```

Wildcards: `*` matches one segment/subdomain, `**` matches many. Omitting fields implies `**` (not recommended).

### `localPatterns`

Restrict which local paths can be optimized:

```js
images: {
  localPatterns: [{ pathname: '/assets/images/**', search: '' }],
}
```

### Key Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `deviceSizes` | `[640,750,828,1080,1200,1920,2048,3840]` | Breakpoints for responsive `srcset` |
| `imageSizes` | `[32,48,64,96,128,256,384]` | Sizes for images with `sizes` prop (smaller than viewport) |
| `qualities` | `[75]` | Allowed quality values. Required in Next.js 16. |
| `formats` | `['image/webp']` | Output formats. Add `'image/avif'` for AVIF (slower encode, 20% smaller). |
| `minimumCacheTTL` | `14400` (4h) | Cache TTL in seconds for optimized images |
| `unoptimized` | `false` | Disable optimization globally |
| `loader` / `loaderFile` | — | Custom optimization service. Set `loader: 'custom'` + path to loader file. |
| `dangerouslyAllowSVG` | `false` | Enable SVG optimization. Pair with `contentSecurityPolicy`. |
| `contentDispositionType` | `'attachment'` | `'attachment'` or `'inline'` for optimized images |
| `contentSecurityPolicy` | — | CSP header for images. Essential with SVG. |

### Custom Loader

```js
// next.config.js
module.exports = {
  images: { loader: 'custom', loaderFile: './lib/image-loader.js' },
}

// lib/image-loader.js
'use client'
export default function myLoader({ src, width, quality }) {
  return `https://cdn.example.com/${src}?w=${width}&q=${quality || 75}`
}
```

Per-instance alternative: pass `loader` prop directly to `<Image>`.

## Script Component (`next/script`)

Optimizes third-party script loading with configurable strategies.

```jsx
import Script from 'next/script'
```

### Loading Strategies

| Strategy | When | Use For |
|----------|------|---------|
| `beforeInteractive` | Before hydration. Must be in root layout. | Bot detectors, cookie consent |
| `afterInteractive` | **(default)** After some hydration | Tag managers, analytics |
| `lazyOnload` | During browser idle time | Chat widgets, social embeds |
| `worker` | Web worker (experimental, Pages Router only) | Non-critical third-party scripts |

### Usage Patterns

**All routes** — place in root layout:
```jsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
      <Script src="https://analytics.example.com/script.js" />
    </html>
  )
}
```

**Specific routes** — place in layout or page:
```jsx
// app/dashboard/layout.tsx
export default function DashboardLayout({ children }) {
  return (
    <>
      <section>{children}</section>
      <Script src="https://example.com/dashboard-analytics.js" />
    </>
  )
}
```

Scripts load only once even across navigations within the same layout.

**`beforeInteractive`** must be in root layout (`app/layout.tsx`). Always injected into `<head>`.

### Event Handlers

Require `'use client'`. Cannot use `onLoad`/`onError` with `beforeInteractive`.

```jsx
'use client'
import Script from 'next/script'

<Script
  src="https://maps.googleapis.com/maps/api/js"
  onLoad={() => console.log('Loaded')}
  onReady={() => {
    // Runs after load AND on every re-mount (navigation)
    new google.maps.Map(ref.current, { center, zoom: 8 })
  }}
  onError={(e) => console.error('Failed', e)}
/>
```

- `onLoad`: fires once after script loads. Not with `beforeInteractive`.
- `onReady`: fires after load + every component mount. Good for re-initialization.
- `onError`: fires on load failure. Not with `beforeInteractive`.

### Inline Scripts

Must have an `id` prop:

```jsx
<Script id="show-banner">
  {`document.getElementById('banner').classList.remove('hidden')`}
</Script>

// or
<Script id="show-banner" dangerouslySetInnerHTML={{
  __html: `document.getElementById('banner').classList.remove('hidden')`,
}} />
```

### Forwarded Attributes

Additional DOM attributes (`nonce`, `data-*`, etc.) pass through to the rendered `<script>`:

```jsx
<Script src="..." id="my-script" nonce="XUENAJFW" data-test="script" />
```

## Videos

No built-in `<Video>` component. Use HTML `<video>` or `<iframe>`.

### Self-Hosted Video (`<video>`)

```jsx
export function Video() {
  return (
    <video width="320" height="240" controls preload="none">
      <source src="/video.mp4" type="video/mp4" />
      <track src="/captions.vtt" kind="subtitles" srcLang="en" label="English" />
      Your browser does not support the video tag.
    </video>
  )
}
```

Key attributes: `controls`, `preload="none"`, `autoPlay` (pair with `muted` + `playsInline` for iOS), `loop`.

### Embedded Video (`<iframe>`)

```jsx
<iframe
  src="https://www.youtube.com/embed/VIDEO_ID"
  allowFullScreen
  loading="lazy"
  title="Video description"
/>
```

### Streaming with Suspense

Fetch video URL server-side and stream with Suspense:

```jsx
import { Suspense } from 'react'

async function VideoComponent() {
  const src = await getVideoSrc()
  return <iframe src={src} allowFullScreen />
}

export default function Page() {
  return (
    <Suspense fallback={<VideoSkeleton />}>
      <VideoComponent />
    </Suspense>
  )
}
```

### Video Best Practices

- Include `<track>` for subtitles/captions (accessibility).
- Use `preload="none"` to avoid unnecessary data transfer.
- For autoplay: always add `muted` and `playsInline` (iOS requirement).
- Make embeds responsive with CSS.
- Consider `next-video` (open source) for a `<Video>` component with hosting integration.

## Common Pitfalls

1. **Missing `remotePatterns`**: Remote images fail with 400 unless the hostname is configured. Be specific with `protocol`, `hostname`, `pathname`, and `search`.
2. **Layout shift (CLS)**: Always provide `width`/`height` or use `fill`. These set the aspect ratio for space reservation.
3. **Oversized downloads**: Use `sizes` prop with `fill` or responsive images. Without it, browser assumes `100vw`.
4. **Missing `qualities` config**: Next.js 16 requires explicit `qualities` array. Default is `[75]`. Add more values if you use different `quality` props.
5. **SVG handling**: SVGs auto-set `unoptimized`. For SVG optimization, enable `dangerouslyAllowSVG` with `contentSecurityPolicy`.
6. **`style` width without height**: When setting `width` via `style`, always add `height: 'auto'` to preserve aspect ratio.
7. **Function props in Server Components**: `onLoad`, `onError`, `loader` require `'use client'`.
8. **Theme images loading both**: Don't use `preload`/`loading="eager"` on theme-switched images — both will download.
9. **Script `beforeInteractive` placement**: Must be in root layout only. Placing elsewhere has no effect.
10. **Inline scripts without `id`**: Next.js cannot track/deduplicate inline scripts without an `id` prop.
