# Sentry: CLI
Based on Sentry documentation (docs.sentry.io).

## Installation

**curl (macOS/Linux):**
```bash
curl -sL https://sentry.io/get-cli/ | sh
# Pin a specific version:
curl -sL https://sentry.io/get-cli/ | SENTRY_CLI_VERSION="3.3.0" sh
```

**npm:**
```bash
npm install @sentry/cli
# Global:
sudo npm install -g @sentry/cli --unsafe-perm
# Access locally:
./node_modules/.bin/sentry-cli --help
```

**Homebrew (macOS):**
```bash
brew install getsentry/tools/sentry-cli
```

**Docker:**
```bash
docker pull getsentry/sentry-cli
docker run --rm -v $(pwd):/work getsentry/sentry-cli --help
```

**Scoop (Windows):**
```bash
scoop install sentry-cli
```

Update/uninstall: `sentry-cli update` / `sentry-cli uninstall`.

## Authentication

**Interactive login:**
```bash
sentry-cli login
# Self-hosted:
sentry-cli --url https://myserver.invalid/ login
```

**Auth token via environment variable (preferred in CI):**
```bash
export SENTRY_AUTH_TOKEN=sntrys_YOUR_TOKEN_HERE
```

**Auth token via config file (`~/.sentryclirc`):**
```ini
[auth]
token=sntrys_YOUR_TOKEN_HERE
```

The CLI searches upward from the current directory for `.sentryclirc` and always loads `~/.sentryclirc` as a fallback. Priority: CLI flags > env vars > config file.

**Verify configuration:**
```bash
sentry-cli info
```

## Configuration

### Config File (`.sentryclirc`, INI format)

```ini
[auth]
token=sntrys_YOUR_TOKEN_HERE

[defaults]
url=https://sentry.io/
org=my-org
project=my-project
```

### Key Environment Variables

| Variable | Purpose |
|---|---|
| `SENTRY_AUTH_TOKEN` | Auth token for API access |
| `SENTRY_DSN` | DSN for send-event and cron monitors |
| `SENTRY_URL` | Sentry server URL (default: `https://sentry.io/`) |
| `SENTRY_ORG` | Organization slug |
| `SENTRY_PROJECT` | Project slug |
| `SENTRY_LOG_LEVEL` | Logging: trace, debug, info, warn (default), error |
| `SENTRY_NO_PROGRESS_BAR` | Set `1` to suppress progress bars (CI) |
| `SENTRY_VCS_REMOTE` | Git remote name (default: `origin`) |

### Proxy

```ini
[http]
proxy_url=http://proxy.example.com:8080
proxy_username=user
proxy_password=pass
```

Or use the standard `http_proxy` / `https_proxy` env vars.

## Release Management

Releases are global per organization. Use unique names if multiple projects share version schemes.

### Creating and Finalizing

```bash
# Propose version from git (short SHA):
VERSION=$(sentry-cli releases propose-version)

# Create a release:
sentry-cli releases new "$VERSION"

# Create and finalize immediately:
sentry-cli releases new "$VERSION" --finalize

# Finalize later:
sentry-cli releases finalize "$VERSION"
```

Finalizing sets a timestamp used for sorting and determining "next release" for issue resolution.

### Associating Commits

```bash
# Auto-detect from repo integration:
sentry-cli releases set-commits "$VERSION" --auto

# From local git history (no repo integration needed):
sentry-cli releases set-commits "$VERSION" --local

# Manual commit or range:
sentry-cli releases set-commits "$VERSION" --commit "owner/repo@abc123"
sentry-cli releases set-commits "$VERSION" --commit "owner/repo@prev..current"
```

Use `--ignore-missing` when commits may have been rebased or squashed.

### Deploy Markers

```bash
# Register a deploy:
sentry-cli deploys new --release "$VERSION" -e production

# With duration (seconds):
sentry-cli deploys new --release "$VERSION" -e staging -t 120

# List deploys:
sentry-cli deploys list --release "$VERSION"
```

### CI/CD Workflow (typical)

```bash
VERSION=$(sentry-cli releases propose-version)
sentry-cli releases new "$VERSION"
sentry-cli releases set-commits "$VERSION" --auto

# ... build and upload source maps ...
sentry-cli sourcemaps inject ./dist
sentry-cli sourcemaps upload ./dist

sentry-cli releases finalize "$VERSION"
sentry-cli deploys new --release "$VERSION" -e production
```

## Source Maps

### Automated Setup (Recommended)

```bash
npx @sentry/wizard@latest -i sourcemaps
```

The wizard configures login, project selection, build tool plugin, and CI pipeline.

### Uploading via CLI

Requires sentry-cli >= 2.17.0 and Sentry JS SDK >= 7.47.0.

**Step 1 — Inject debug IDs into built files:**
```bash
sentry-cli sourcemaps inject /path/to/build/output
```

This adds `//# debugId=<id>` comments to minified JS files and `"debug_id"` fields to `.map` files.

**Step 2 — Upload the artifact bundle:**
```bash
sentry-cli sourcemaps upload /path/to/build/output
```

**Optional flags:**
```bash
# Associate with a release:
sentry-cli sourcemaps upload --release=1.0.0 ./dist

# Associate with release + distribution:
sentry-cli sourcemaps upload --release=1.0.0 --dist=android ./dist
```

When using `--release` / `--dist`, the SDK must be configured to match:
```javascript
Sentry.init({ release: "1.0.0", dist: "android" });
```

### Webpack Plugin

```bash
npm install @sentry/webpack-plugin --save-dev
```

```javascript
const { sentryWebpackPlugin } = require("@sentry/webpack-plugin");

module.exports = {
  devtool: "hidden-source-map",
  plugins: [
    sentryWebpackPlugin({
      org: "my-org",
      project: "my-project",
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        filesToDeleteAfterUpload: ["./**/*.map"],
      },
    }),
  ],
};
```

Auth can also be set via `SENTRY_AUTH_TOKEN` env var or a `.env.sentry-build-plugin` file.
The plugin does not upload in watch/development mode.

### Vite Plugin

```bash
npm install @sentry/vite-plugin --save-dev
```

```javascript
import { defineConfig } from "vite";
import { sentryVitePlugin } from "@sentry/vite-plugin";

export default defineConfig({
  build: { sourcemap: "hidden" },
  plugins: [
    // Place Sentry plugin AFTER all other plugins
    sentryVitePlugin({
      org: "my-org",
      project: "my-project",
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        filesToDeleteAfterUpload: ["./**/*.map"],
      },
    }),
  ],
});
```

### Troubleshooting Source Maps

- **Missing debug IDs:** Run the wizard (`npx @sentry/wizard@latest -i sourcemaps`) and ensure you test with a production build.
- **Maps not applying:** Artifacts must be uploaded before errors are captured.
- **Development builds:** Source maps are only generated and uploaded during production builds.
- Use `"hidden-source-map"` (webpack) or `sourcemap: "hidden"` (Vite) to upload maps without exposing them publicly.
- Delete `.map` files after upload with `filesToDeleteAfterUpload` in plugin config.

## Debug Information Files

Used for native crash symbolication (iOS dSYMs, Android ProGuard, native libraries).

### Validate a File

```bash
sentry-cli debug-files check mylibrary.so.debug
```

### Upload Debug Files

```bash
sentry-cli debug-files upload -o my-org -p my-project /path/to/files

# Wait for server-side processing:
sentry-cli debug-files upload --wait /path/to/files

# Include source code in the bundle:
sentry-cli debug-files upload --include-sources /path/to/files
```

The command recursively scans directories and skips already-uploaded files.

### Apple BCSymbolMaps

```bash
sentry-cli debug-files upload --symbol-maps /path/to/BCSymbolMaps /path/to/dSYMs
```

### ProGuard Mappings

```bash
sentry-cli upload-proguard app/build/outputs/mapping/release/mapping.txt

# With explicit UUID (must match AndroidManifest.xml meta-data):
sentry-cli upload-proguard --uuid <UUID> /path/to/mapping.txt
```

### JVM Source Bundles

```bash
sentry-cli debug-files bundle-jvm --output ./out --debug-id <UUID> /path/to/sources
sentry-cli debug-files upload --type jvm ./out
```

### Native Source Bundles

```bash
# Create bundles from debug info:
sentry-cli debug-files bundle-sources /path/to/debug/files
# Upload them:
sentry-cli debug-files upload --type sourcebundle /path/to/bundles
```

## Sending Events

Test your Sentry setup from the command line. Requires `SENTRY_DSN` to be set.

```bash
export SENTRY_DSN='https://examplePublicKey@o0.ingest.sentry.io/0'

# Simple message:
sentry-cli send-event -m "Something broke"

# Multi-line:
sentry-cli send-event -m "Line 1" -m "Line 2"

# With tags and extra data:
sentry-cli send-event -m "Deploy failed" -t environment:staging -e user:admin

# Attach a logfile as breadcrumbs (last 100 entries):
sentry-cli send-event -m "Task failed" --logfile error.log

# With a specific release:
sentry-cli send-event -m "Error" --release 1.0.0

# Send a stored JSON event:
sentry-cli send-event ./events/event.json
```

**Bash hook** for automatic error reporting in shell scripts:
```bash
#!/bin/bash
export SENTRY_DSN='https://examplePublicKey@o0.ingest.sentry.io/0'
eval "$(sentry-cli bash-hook)"
# Any failing command will now send an event to Sentry
```

## Cron Monitoring

Wrap scheduled jobs so Sentry tracks missed, late, and failed runs. Requires sentry-cli >= 2.16.1 and `SENTRY_DSN`.

```bash
# Basic usage — wraps a command and reports status:
sentry-cli monitors run my-monitor-slug -- /path/to/job.sh

# With schedule (auto-creates the monitor):
sentry-cli monitors run --schedule "0 * * * *" my-monitor-slug -- my-command

# With environment:
sentry-cli monitors run -e production my-monitor-slug -- node cleanup.js

# With check-in margin and max runtime (minutes):
sentry-cli monitors run \
  --check-in-margin 5 \
  --max-runtime 30 \
  --timezone "America/New_York" \
  my-monitor-slug -- ./run-etl.sh
```

**Crontab example:**
```cron
* * * * * SENTRY_DSN=https://key@o0.ingest.sentry.io/0 sentry-cli monitors run my-slug -- /usr/local/bin/my-job
```

## Logs

View and stream logs from Sentry projects.

```bash
# List recent logs:
sentry-cli logs list --project=my-project --org=my-org

# Stream logs in real time:
sentry-cli logs list --project=my-project --org=my-org --live
```

Output includes timestamp, log level, message, and trace ID (when available).

## Common CI/CD Patterns

### GitHub Actions

```yaml
env:
  SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
  SENTRY_ORG: my-org
  SENTRY_PROJECT: my-project

steps:
  - run: npm install @sentry/cli
  - run: |
      VERSION=$(npx sentry-cli releases propose-version)
      npx sentry-cli releases new "$VERSION"
      npx sentry-cli releases set-commits "$VERSION" --auto
  - run: npm run build
  - run: |
      npx sentry-cli sourcemaps inject ./dist
      npx sentry-cli sourcemaps upload ./dist
  - run: |
      npx sentry-cli releases finalize "$VERSION"
      npx sentry-cli deploys new --release "$VERSION" -e production
```

### Docker Build

```dockerfile
FROM node:20 AS build
RUN npm install @sentry/cli
RUN npx sentry-cli sourcemaps inject ./dist
RUN npx sentry-cli sourcemaps upload ./dist
```

Or use the official image:
```bash
docker run --rm \
  -e SENTRY_AUTH_TOKEN \
  -e SENTRY_ORG=my-org \
  -e SENTRY_PROJECT=my-project \
  -v $(pwd)/dist:/work \
  getsentry/sentry-cli sourcemaps upload /work
```

### Suppress Failures in CI

Set `SENTRY_ALLOW_FAILURE=1` to prevent sentry-cli errors from breaking your pipeline. Useful for non-critical upload steps.
