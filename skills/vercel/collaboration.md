# Vercel: Collaboration & Developer Tools
Based on Vercel documentation.

## Comments

### Overview

Comments allow team members and invited participants to give direct feedback on preview deployments (and other environments) through the Vercel Toolbar. Enabled by default on all preview deployments, free on all plans. All users must have a Vercel account.

- Comments attach to any part of the UI, creating threaded discussions
- PR owners get email notifications on new comments; thread participants get notified on activity
- On Pro/Enterprise plans, external users can be invited to view and comment
- Slack integration mirrors comment threads as Slack threads (bidirectional sync)

### Creating Comments

| Action | How |
|--------|-----|
| Enter comment mode | Press `c` or select **Comment** in toolbar menu |
| Place comment | Click on page or highlight text |
| Mention users | Type `@username` in comment |
| Add emoji | Type `:emoji_name:` |
| Add reaction | Click emoji icon next to commenter name |
| Attach screenshot | Click `+` to upload, camera icon to capture page, or click-drag to screenshot region (browser extension required for latter two) |
| Copy comment link | Click ellipsis next to commenter name, select **Copy Link** |

### Markdown in Comments

Supported: **bold** (`*text*`, Cmd+B), *italic* (`_text_`, Cmd+I), ~~strikethrough~~ (`~text~`, Cmd+Shift+X), `code` (Cmd+E), bulleted lists (`-`), numbered lists (`1.`), links (`[text](url)`), quotes (`>`).

### Comment Threads and Inbox

- Every new comment starts a thread visible in the **Inbox** (toolbar menu)
- Filter threads by: page (current or all), status (resolved/unresolved)
- Navigate threads with up/down arrows in inbox
- Drag inbox to left or right side of screen
- Resolve threads via the **Resolve** checkbox

### Notifications

Triggered by: new thread creation, replies in subscribed threads, thread resolution.

| Channel | Details |
|---------|---------|
| Dashboard | Filter by author, status, project, page, branch. Use `*` wildcard for URL search |
| Email | Sent to Vercel account email; batched for rapid activity |
| Slack | Requires Vercel Slack integration; bidirectional thread sync |

Per-deployment notification preferences (in toolbar Preferences): **All**, **Replies and Mentions**, or **Never**. Per-thread: **Follow** or **Unfollow** via thread ellipsis menu.

### Session Info for Debugging

Hover over a comment timestamp to see commenter's browser, window dimensions, device pixel ratio, and deployment URL. Click the screen icon to copy full session JSON.

### Enabling/Disabling Comments

Comments are a toolbar feature -- controlling the toolbar controls comments.

| Level | How |
|-------|-----|
| Team | Settings > General > Vercel Toolbar > On/Off per environment |
| Project | Project Settings > General > Vercel Toolbar > Default/On/Off per environment |
| Session | Toolbar menu > **Disable for Session** |
| Branch | Set `VERCEL_PREVIEW_FEEDBACK_ENABLED=1` or `0` as env var |
| Automation | Send `x-vercel-skip-toolbar` header to disable for e2e tests |

## Vercel Toolbar

### Overview

The toolbar assists iteration and development. It appears on all preview deployments by default. Starts in a sleeping state -- click to activate, or use the browser extension's **Always Activate** preference.

### Toolbar Menu Features

Open with keyboard shortcut or click the menu icon.

| Feature | Description |
|---------|-------------|
| Comments | Leave/view feedback |
| Inbox | View all open comment threads |
| Layout Shifts | Detect CLS-causing elements |
| Interaction Timing | Measure INP per interaction |
| Accessibility Audit | WCAG 2.0 A/AA automated checks |
| Open Graph | Preview link/share card metadata |
| Draft Mode | Toggle unpublished CMS content |
| Edit Mode | Edit CMS content in context |
| Feature Flags | Read/override flag values |
| Branch switching | Switch between preview branches |
| Share | Copy deployment URL with query params |
| Search | Search toolbar and dashboard pages |

### Toolbar Preferences

Configurable per user: notifications, theme, layout shift detection, accessibility audit, interaction timing, keyboard shortcuts, Always Activate, Start Hidden.

Custom keyboard shortcuts can be set for any tool via Preferences > Keyboard Shortcuts.

### Browser Extension

Available for Chrome, Firefox, Opera, Edge. Adds:

- Faster toolbar with fewer network requests
- Screenshot capture (click-drag to select area)
- **Always Activate** and **Start Hidden** preferences
- Click extension icon to show/hide toolbar

Install: [Chrome Web Store](https://chromewebstore.google.com/detail/vercel/lahhiofdgnbcgmemekkmjnpifojdaelb) | [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/vercel)

### Toolbar in Production and Localhost

The toolbar works in production and local dev -- not just previews. All features (comments, flags, draft mode, edit mode) are available. Enable via project settings or the browser extension.

### Content Security Policy

If you have a CSP, add these directives:

```
script-src https://vercel.live
connect-src https://vercel.live wss://ws-us3.pusher.com
img-src https://vercel.live https://vercel.com data: blob:
frame-src https://vercel.live
style-src https://vercel.live 'unsafe-inline'
font-src https://vercel.live https://assets.vercel.com
```

### Disabling for Specific Contexts

| Context | Method |
|---------|--------|
| E2E tests | `x-vercel-skip-toolbar` request header |
| Specific branch | `VERCEL_PREVIEW_FEEDBACK_ENABLED=0` env var |
| Current session | Toolbar menu > Disable for Session, or drag toolbar to X |
| Custom alias domains | Must opt in via project settings on dashboard |

## Performance Tools

### Layout Shift Tool

Detects elements causing Cumulative Layout Shift (CLS). Common causes: size changes, font loading, unsized media, dynamic content injection, layout-affecting animations.

- Access via toolbar menu > **Layout Shifts**; badge shows shift count
- Each shift shows impact, responsible element, and description
- **Replay shifts**: double-click a shift or use Replay button; select multiple to replay together
- **Exclude elements**: add `data-allow-shifts` attribute to an element (applies to descendants too)
- Disable: Preferences > Layout Shift Detection toggle

### Interaction Timing Tool

Measures per-interaction latency for Interaction to Next Paint (INP) Core Web Vital.

- Access via toolbar menu > **Interaction Timing**; badge shows current INP
- Hover over interaction timeline to see breakdown: input delay, processing, rendering
- Toast notifications appear for interactions > 200ms
- Preferences: **On** (with toasts), **On (Silent)** (no toasts, still tracks), **Off**

### Accessibility Audit Tool

Automated WCAG 2.0 Level A and AA checks using [deque axe](https://github.com/dequelabs/axe-core) rules. Runs in background on all toolbar-enabled environments.

- Access via toolbar menu > **Accessibility Audit**; badge shows issue count
- Filter by severity: Critical, Serious, Moderate, Minor
- Each issue includes explanation and link to relevant WCAG guideline
- Hover over failing element markup to highlight on page; click to log to devtools
- **Recording mode**: click **Start Recording** to capture issues during interaction (hover, focus states); persists across navigation within session
- Disable: Preferences > Accessibility Audit toggle

## Draft Mode

### Overview

View unpublished headless CMS content rendered with full site styling. Supported by Next.js and SvelteKit (any framework using Build Output API with `bypassToken`).

### How It Works

1. ISR routes have a `bypassToken` (cryptographically-secure, set at build time)
2. When visiting an ISR route, the page checks for a `__prerender_bypass` cookie
3. If the cookie matches the `bypassToken`, the page renders in Draft Mode (bypasses ISR cache)
4. Only team members can view draft content

### Next.js (App Router)

```tsx
// app/page.tsx
import { draftMode } from 'next/headers';

async function getContent() {
  const { isEnabled } = await draftMode();
  const url = isEnabled
    ? 'https://draft.example.com'
    : 'https://production.example.com';
  const res = await fetch(url, { next: { revalidate: 120 } });
  return res.json();
}

export default async function Page() {
  const { title, desc } = await getContent();
  return (
    <main>
      <h1>{title}</h1>
      <p>{desc}</p>
    </main>
  );
}
```

### SvelteKit

```ts
// blog/[slug]/+page.server.ts
import { BYPASS_TOKEN } from '$env/static/private';

export const config = {
  isr: {
    bypassToken: BYPASS_TOKEN,
    expiration: 60,
  },
};
```

### Sharing Drafts

Append `?__vercel_draft=1` to the URL. Only Vercel team members can view draft content, even with the query parameter.

### Activating

Toggle Draft Mode in the Vercel Toolbar menu. The toolbar turns purple when Draft Mode is active.

## Edit Mode

### Overview

Edit Mode allows content authors to edit CMS content directly within the website's context, seeing changes in the actual layout and design. Elements matched to CMS fields become **Content Links** -- highlighted in blue on hover, linking directly to the CMS editing interface.

### Accessing

1. Log into the Vercel Toolbar
2. Navigate to a page with editable content
3. Select **Edit Mode** in toolbar menu
4. Hover over elements to see Content Link indicators; click to open CMS editor

No additional code changes required on the page.

### Supported CMS Platforms

Contentful, Sanity, Builder.io, TinaCMS, DatoCMS, Payload, Uniform, Strapi.

## Feature Flags

### Overview

Vercel provides a complete feature flags platform. Use Vercel as your provider or connect a Marketplace provider. Unified dashboard shows all flags regardless of provider.

### Key Capabilities

- Gradual rollout to specific users, teams, or environments
- Production testing before full launch
- A/B testing with conversion and performance measurement
- Local flag overrides via Flags Explorer in toolbar (no code changes)
- Decouple deployment from feature release

### Flags Explorer

The toolbar includes a Flags Explorer for reading and overriding flag values on any environment. Override flags locally without code changes -- useful for development and QA.

### Observability

Track flag evaluations in Runtime Logs and analyze impact in Web Analytics.

```js
// Manual reporting (automatic with Flags SDK)
reportValue(flagKey, flagValue);
```

How it works:
1. Code evaluates a flag and calls `reportValue(flagKey, flagValue)`
2. Vercel captures evaluations and associates them with the request
3. View data in Runtime Logs or Web Analytics dashboards

With the Flags SDK, reporting is automatic -- no manual instrumentation needed.

### Insights From Flag Tracking

- Feature performance in production
- User segment targeting accuracy
- Correlation between flags and application metrics
- Issues tied to specific flag configurations

## Quick Reference: Toolbar Keyboard Shortcuts

| Action | Default |
|--------|---------|
| Open toolbar menu | Configurable (browser extension required to change) |
| Show/hide toolbar | Configurable (browser extension required to change) |
| Enter comment mode | `c` |
| Custom tool shortcuts | Set via Preferences > Keyboard Shortcuts |
