# Next.js: Testing & Debugging
Based on Next.js documentation (App Router).

## Overview

| Type | Tool | Purpose |
|------|------|---------|
| Unit / Snapshot | Jest | Component rendering, snapshots, mocking |
| Unit | Vitest | Faster alternative to Jest, Vite-based |
| E2E | Playwright | Cross-browser automation (Chromium, Firefox, WebKit) |
| E2E + Component | Cypress | Browser-based E2E and component testing |

**Key limitation:** `async` Server Components are not supported by Jest or Vitest. Use E2E tests for `async` components.

---

## Jest

### Install

```bash
npm install -D jest jest-environment-jsdom @testing-library/react \
  @testing-library/dom @testing-library/jest-dom ts-node @types/jest
```

### Configuration

`next/jest` auto-configures transform (SWC), mocks for CSS/images/`next/font`, `.env` loading, and `node_modules`/`.next` ignoring.

```ts
// jest.config.ts
import type { Config } from 'jest'
import nextJest from 'next/jest.js'

const createJestConfig = nextJest({
  dir: './',  // loads next.config.js and .env
})

const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
}

// Must export this way so next/jest can load async Next.js config
export default createJestConfig(config)
```

```ts
// jest.setup.ts
import '@testing-library/jest-dom'
```

### Path aliases

Match `tsconfig.json` paths in Jest config:

```ts
// tsconfig.json:  "paths": { "@/components/*": ["components/*"] }
// jest.config.ts:
moduleNameMapper: {
  '^@/components/(.*)$': '<rootDir>/components/$1',
}
```

### Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

### Writing tests

```tsx
// __tests__/page.test.tsx
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Page from '../app/page'

describe('Page', () => {
  it('renders a heading', () => {
    render(<Page />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
  })
})
```

### Snapshot testing

```tsx
// __tests__/snapshot.test.tsx
import { render } from '@testing-library/react'
import Page from '../app/page'

it('renders homepage unchanged', () => {
  const { container } = render(<Page />)
  expect(container).toMatchSnapshot()
})
```

---

## Vitest

### Install

```bash
# TypeScript
npm install -D vitest @vitejs/plugin-react jsdom \
  @testing-library/react @testing-library/dom vite-tsconfig-paths

# JavaScript (omit vite-tsconfig-paths)
npm install -D vitest @vitejs/plugin-react jsdom \
  @testing-library/react @testing-library/dom
```

### Configuration

```ts
// vitest.config.mts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: 'jsdom',
  },
})
```

### Scripts

```json
{
  "scripts": {
    "test": "vitest"
  }
}
```

`vitest` runs in watch mode by default.

### Writing tests

```tsx
// __tests__/page.test.tsx
import { expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'
import Page from '../app/page'

test('Page', () => {
  render(<Page />)
  expect(
    screen.getByRole('heading', { level: 1, name: 'Home' })
  ).toBeDefined()
})
```

### Vitest vs Jest for Next.js

- Vitest uses Vite for transforms; Jest uses SWC via `next/jest`.
- Vitest has native ESM support; Jest requires configuration for ESM.
- Vitest needs `vite-tsconfig-paths` for TS path aliases; Jest uses `moduleNameMapper`.
- Vitest runs in watch mode by default; Jest needs `--watch` flag.
- Both use `@testing-library/react` + `jsdom` identically.

---

## Playwright (E2E)

### Install

```bash
npm init playwright
# Guides you through setup, creates playwright.config.ts
```

### Configuration

```ts
// playwright.config.ts  (key options)
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:3000',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
})
```

The `webServer` option auto-starts the dev server before tests.

### Writing tests

```ts
// tests/example.spec.ts
import { test, expect } from '@playwright/test'

test('should navigate to the about page', async ({ page }) => {
  await page.goto('/')
  await page.click('text=About')
  await expect(page).toHaveURL('/about')
  await expect(page.locator('h1')).toContainText('About')
})
```

### Running

```bash
# Against dev server (webServer config handles startup)
npx playwright test

# Against production build (recommended for CI)
npm run build && npm run start
# then in another terminal:
npx playwright test

# CI: headless by default; install browser deps first:
npx playwright install-deps
```

---

## Cypress (E2E + Component)

### Install

```bash
npm install -D cypress
```

### Scripts

```json
{
  "scripts": {
    "cypress:open": "cypress open",
    "e2e": "start-server-and-test dev http://localhost:3000 \"cypress open --e2e\"",
    "e2e:headless": "start-server-and-test dev http://localhost:3000 \"cypress run --e2e\"",
    "component": "cypress open --component",
    "component:headless": "cypress run --component"
  }
}
```

`start-server-and-test` (separate package) starts the dev server then runs Cypress.

### E2E configuration

```ts
// cypress.config.ts
import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    setupNodeEvents(on, config) {},
  },
})
```

### E2E test

```ts
// cypress/e2e/app.cy.js
describe('Navigation', () => {
  it('should navigate to the about page', () => {
    cy.visit('/')
    cy.get('a[href*="about"]').click()
    cy.url().should('include', '/about')
    cy.get('h1').contains('About')
  })
})
```

### Component testing configuration

```ts
// cypress.config.ts
import { defineConfig } from 'cypress'

export default defineConfig({
  component: {
    devServer: {
      framework: 'next',
      bundler: 'webpack',
    },
  },
})
```

### Component test

```tsx
// cypress/component/about.cy.tsx
import Page from '../../app/page'

describe('<Page />', () => {
  it('should render and display expected content', () => {
    cy.mount(<Page />)
    cy.get('h1').contains('Home')
    cy.get('a[href="/about"]').should('be.visible')
  })
})
```

**Note:** Cypress component tests don't start a Next.js server, so `<Image />` and other server-dependent features may not work. Cypress does not support component testing for `async` Server Components.

---

## Debugging

### VS Code

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug server-side",
      "type": "node-terminal",
      "request": "launch",
      "command": "npm run dev -- --inspect"
    },
    {
      "name": "Next.js: debug client-side",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000"
    },
    {
      "name": "Next.js: debug full stack",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/node_modules/next/dist/bin/next",
      "runtimeArgs": ["--inspect"],
      "skipFiles": ["<node_internals>/**"],
      "serverReadyAction": {
        "action": "debugWithEdge",
        "killOnServerStop": true,
        "pattern": "- Local:.+(https?://.+)",
        "uriFormat": "%s",
        "webRoot": "${workspaceFolder}"
      }
    }
  ]
}
```

For Turborepo/monorepo, add `"cwd": "${workspaceFolder}/apps/web"` to server-side configs.

### Chrome DevTools (server-side)

```bash
npm run dev -- --inspect
# Debugger listening on ws://127.0.0.1:9229/...
```

1. Open `chrome://inspect` in Chrome.
2. Find your Next.js app under **Remote Target**.
3. Click **inspect** to open DevTools.
4. Source files are at `webpack://{app-name}/./`.

Use `--inspect=0.0.0.0` for remote access (e.g., Docker).

For `--inspect-brk` or `--inspect-wait`, use `NODE_OPTIONS`:
```bash
NODE_OPTIONS=--inspect-brk next dev
```

### Client-side debugging

- Open DevTools (`Ctrl+Shift+J` / `Cmd+Option+I`).
- Go to **Sources** tab.
- Use `debugger` statements or `Ctrl+P`/`Cmd+P` to find files.
- Source files are at `webpack://_N_E/./`.

### Firefox DevTools (server-side)

1. Open `about:debugging`.
2. Click **This Firefox** in the sidebar.
3. Find and **Inspect** your Next.js app under Remote Targets.

### Windows note

Disable Windows Defender during development -- it checks every file read, significantly slowing Fast Refresh.

---

## Best Practices

### Testing pyramid for Next.js

1. **Unit tests (many):** Pure functions, hooks, synchronous components. Use Jest or Vitest with React Testing Library.
2. **Component tests (moderate):** Interactive components with user events. Use Cypress component testing or RTL with Jest/Vitest.
3. **E2E tests (fewer but critical):** Full user flows, navigation, form submissions, `async` Server Components. Use Playwright or Cypress.

### What to test where

| What | Tool | Why |
|------|------|-----|
| Utility functions | Jest / Vitest | Pure logic, fast |
| Synchronous components | Jest / Vitest + RTL | Render output, props, events |
| `async` Server Components | Playwright / Cypress E2E | No unit test support yet |
| Navigation flows | Playwright / Cypress E2E | Requires real routing |
| API routes | Jest / Vitest (handler unit tests) or E2E | Depends on complexity |
| Forms and user interactions | RTL (simple) or E2E (complex) | RTL for logic, E2E for full flow |

### General guidance

- Run unit tests against `jsdom`; run E2E tests against a production build (`next build && next start`) for realistic behavior.
- Use `webServer` (Playwright) or `start-server-and-test` (Cypress) to automate server startup.
- Test files can live in `__tests__/` or colocated next to the components they test.
- For snapshot tests, review diffs carefully -- accept intentional changes, investigate unexpected ones.
- Install React Developer Tools browser extension for component inspection and performance debugging.
