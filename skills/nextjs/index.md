# Next.js Skills

Based on Next.js documentation (App Router + Pages Router).
Generated from https://nextjs.org/docs on 2026-03-18.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [fundamentals](./fundamentals.md) | Installation, project structure, layouts/pages, server/client components intro, error handling, CSS basics, deploying, upgrading, glossary | 549 |
| [routing](./routing.md) | File conventions (page, layout, template, loading, error, not-found, default), dynamic routes, route groups, parallel routes, intercepting routes, linking/navigation, redirecting, prefetching | 513 |
| [rendering](./rendering.md) | Server vs Client Components, `'use client'`/`'use server'`/`'use cache'` directives, composition patterns, cache components, partial prerendering | 423 |
| [data-fetching-caching](./data-fetching-caching.md) | Data fetching in Server Components, Server Actions, forms, four-layer caching architecture, revalidation, ISR, `use cache`, `cacheTag`/`cacheLife`, `connection()` | 609 |
| [styling](./styling.md) | CSS Modules, global CSS, Tailwind CSS (v3/v4), Sass, CSS-in-JS (styled-components, styled-jsx), `next/font` (Google/local fonts, variable fonts, Tailwind integration) | 433 |
| [metadata-seo](./metadata-seo.md) | Static/dynamic metadata, `generateMetadata`, OG images (`ImageResponse`), sitemaps, robots.txt, manifest, app icons, JSON-LD, viewport | 601 |
| [images-media](./images-media.md) | Image component (all props, fill mode, responsive patterns, art direction), image configuration, Script component (strategies, events), videos | 393 |
| [route-handlers](./route-handlers.md) | Route handlers (`route.ts`), proxy (`proxy.ts`), NextRequest/NextResponse, Edge Runtime, route segment config, CORS, streaming, webhooks | 542 |
| [hooks-functions](./hooks-functions.md) | Client hooks (useRouter, usePathname, useSearchParams, useParams, useLinkStatus), server functions (cookies, headers, redirect, notFound, forbidden, unauthorized, after, draftMode), Link/Form components, generateStaticParams | 566 |
| [configuration](./configuration.md) | next.config.js/ts (all key options), environment variables, TypeScript, ESLint, CLI commands, redirects, rewrites, headers, images, output, Turbopack, webpack | 645 |
| [deployment](./deployment.md) | Vercel/self-hosting/Docker/static deployment, standalone output, static exports, SPA mode, production checklist, CI caching, memory optimization, PWA | 609 |
| [testing](./testing.md) | Jest, Vitest, Playwright, Cypress (E2E + component), VS Code/Chrome debugging, testing pyramid for Next.js | 436 |
| [security-auth](./security-auth.md) | Authentication (Server Actions, sessions, JWT), authorization (DAL pattern, middleware), auth interrupts (forbidden/unauthorized), CSP with nonces, data security, taint API | 523 |
| [advanced-patterns](./advanced-patterns.md) | Internationalization, multi-zones, instrumentation, OpenTelemetry, lazy loading, MDX, draft mode, analytics, package bundling, third-party libraries, AI agents/MCP, custom server, SWC compiler, Fast Refresh | 645 |
| [pages-router](./pages-router.md) | Pages Router: file-system routing, special files (_app/_document/404/500), getStaticProps/getStaticPaths/getServerSideProps, SSG/SSR/CSR, API routes, layout patterns, migration to App Router | 573 |

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/nextjs/routing.md
    @~/.claude/skills/nextjs/data-fetching-caching.md

Or reference this index to see all available skills:

    @~/.claude/skills/nextjs/index.md

## Coverage

- Total documentation pages read: ~230
- Skill files created: 15
- Total lines: 8,060
- Pages failed: 0
