# Sentry: Crons, Releases & Monitoring
Based on Sentry documentation (docs.sentry.io).

## Cron Monitoring

Cron Monitoring tracks scheduled, recurring jobs for uptime and performance. It alerts on missed runs, timeouts, and failures.

### Check-in Statuses

- **`in_progress`** -- Job has started executing
- **`ok`** -- Job completed successfully
- **`error`** -- Job failed

### Monitor Configuration

| Option | Description |
|--------|-------------|
| `schedule` | Crontab (`{"type": "crontab", "value": "0 * * * *"}`) or interval (`{"type": "interval", "value": "2", "unit": "hour"}`) |
| `checkin_margin` | Minutes after expected time before marking as missed |
| `max_runtime` | Minutes allowed before marking as timed out |
| `timezone` | IANA timezone identifier (e.g., `Europe/Vienna`) |
| `failure_issue_threshold` | Consecutive failures before creating an issue |
| `recovery_threshold` | Consecutive OK check-ins before resolving an issue |

**Rate limit:** 6 check-ins per minute per monitor environment.

---

## Python Crons

Requires `sentry-sdk >= 1.17.0`.

### Decorator (recommended)

```python
import sentry_sdk
from sentry_sdk.crons import monitor

# Async functions supported from SDK 1.44.1+
@monitor(monitor_slug='my-job')
def tell_the_world():
    print('My scheduled task...')
```

### Context Manager

```python
from sentry_sdk.crons import monitor

def tell_the_world():
    with monitor(monitor_slug='my-job'):
        print('My scheduled task...')
```

### Manual Check-ins

```python
from sentry_sdk.crons import capture_checkin
from sentry_sdk.crons.consts import MonitorStatus

check_in_id = capture_checkin(
    monitor_slug='my-job',
    status=MonitorStatus.IN_PROGRESS,
)

# ... execute task ...

capture_checkin(
    monitor_slug='my-job',
    check_in_id=check_in_id,
    status=MonitorStatus.OK,  # or MonitorStatus.ERROR
)
```

### Upserting Monitor Config (SDK 1.45.0+)

Pass `monitor_config` to the decorator or `capture_checkin` to create/update the monitor automatically:

```python
monitor_config = {
    "schedule": {"type": "crontab", "value": "0 0 * * *"},
    "timezone": "Europe/Vienna",
    "checkin_margin": 10,
    "max_runtime": 10,
    "failure_issue_threshold": 5,
    "recovery_threshold": 5,
}

@monitor(monitor_slug='my-job', monitor_config=monitor_config)
def tell_the_world():
    print('My scheduled task...')
```

### Celery Beat

Sentry auto-discovers Celery Beat tasks. See dedicated Celery Beat integration docs for setup.

---

## JavaScript/Node Crons

Requires `@sentry/node >= 7.51.1`.

### Automatic Instrumentation

**cron library** (SDK 7.92.0+):

```javascript
import { CronJob } from "cron";
const CronJobWithCheckIn = Sentry.cron.instrumentCron(CronJob, "my-cron-job");

const job = new CronJobWithCheckIn("* * * * *", () => {
  console.log("Running every minute");
});
```

**node-cron** (SDK 7.92.0+):

```javascript
import cron from "node-cron";
const cronWithCheckIn = Sentry.cron.instrumentNodeCron(cron);

cronWithCheckIn.schedule("* * * * *", () => {
  console.log("Running every minute");
}, { name: "my-cron-job" });
```

**node-schedule** (SDK 7.93.0+):

```javascript
import * as schedule from "node-schedule";
const scheduleWithCheckIn = Sentry.cron.instrumentNodeSchedule(schedule);

scheduleWithCheckIn.scheduleJob("my-cron-job", "* * * * *", () => {
  console.log("Running every minute");
});
```

### withMonitor() (SDK 7.76.0+)

Wraps a callback with automatic check-ins. Errors within the callback are associated with the current trace.

```javascript
Sentry.withMonitor("my-job", () => {
  // your scheduled task
});
```

With monitor config (upsert):

```javascript
Sentry.withMonitor("my-job", () => {
  // your scheduled task
}, {
  schedule: { type: "crontab", value: "* * * * *" },
  checkinMargin: 2,
  maxRuntime: 10,
  timezone: "America/Los_Angeles",
  failureIssueThreshold: 5,  // SDK 8.7.0+
  recoveryThreshold: 5,       // SDK 8.7.0+
});
```

### Manual Check-ins

```javascript
const checkInId = Sentry.captureCheckIn({
  monitorSlug: "my-job",
  status: "in_progress",
});

// ... execute task ...

Sentry.captureCheckIn({
  checkInId,
  monitorSlug: "my-job",
  status: "ok",  // or "error"
});
```

### Heartbeat (no in_progress)

For simpler monitoring that only detects missed or failed jobs, send a single `ok` or `error` check-in without an `in_progress` step.

---

## CLI Crons

Requires `sentry-cli >= 2.16.1`. Wraps any shell command with automatic check-ins.

### Setup

```bash
export SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

Or in `~/.sentryclirc`:

```ini
[auth]
dsn = https://examplePublicKey@o0.ingest.sentry.io/0
```

### Basic Usage

```bash
sentry-cli monitors run <monitor-slug> -- <command> <args>
sentry-cli monitors run my-job -- python path/to/script.py
```

### Flags

| Flag | Description |
|------|-------------|
| `--schedule` / `-s` | Crontab schedule (quoted), e.g., `"0 * * * *"` |
| `--check-in-margin` | Minutes before marking as missed |
| `--max-runtime` | Max runtime in minutes |
| `--timezone` | IANA timezone identifier |
| `-e` | Monitor environment, e.g., `-e dev` |

```bash
sentry-cli monitors run --schedule "*/5 * * * *" --timezone "Europe/Vienna" \
  -e production my-job -- ./run-task.sh
```

---

## Uptime Monitoring

HTTP-based uptime checks that continuously ping configured URLs from multiple geographic regions.

### How It Works

- Checks execute from **multiple regions in round-robin** to reduce false positives from localized network issues
- An issue is created only after **3 consecutive failures** (configurable via thresholds)
- **Automatic setup**: Sentry auto-configures monitoring for the most frequently encountered hostname in your error data

### Check Criteria

- Must return **2xx** status (custom verification rules available in early access)
- **3xx** responses are followed automatically
- **10-second timeout** threshold
- DNS resolution failures count as check failures

### Uptime Spans

Spans labeled `uptime.request` serve as root spans for uptime traces. They are complimentary (no quota impact) and exempt from sampling.

### Alerts

Create issue alerts selecting the "outage" category, then configure delivery channels (email, Slack, etc.).

---

## Releases

A release is a version of your code deployed to an environment. Sentry auto-creates a release entity the first time it sees an event with a release identifier, but you should notify Sentry before deploying for best results.

### What You Get

- Identify new issues and regressions introduced by a release
- Track crash-free session and user percentages
- See which commits contributed to each release
- Deploy markers showing when releases went live

### Resolving Issues via Releases

- **Current Release**: Resolves in current version; reopens if it recurs in a newer semver release
- **Next Release**: Resolves against the latest version where the issue was seen; updates automatically
- **Specific Commit**: Waits for a release containing that commit

---

## Release Health

Tracks how crashes and bugs impact user experience across releases. SDKs automatically manage session lifecycles.

### Session Types

- **User-mode / Application-mode**: Starts when app launches or returns from background (>30s). Represents user interactions with client applications.
- **Server-mode / Request-mode**: One session per HTTP request or RPC call. High volume.

### Health Statuses

| Status | Meaning |
|--------|---------|
| **Healthy** | Session ended normally, no errors |
| **Errored** | Normal shutdown but had handled errors during session |
| **Crashed** | Unhandled error or hard crash |
| **Abnormal** | SDK could not determine graceful termination (e.g., dead battery, forced kill) |

### Key Metrics

- **Crash-free sessions**: Percentage of sessions not ended by a crash
- **Crash-free users**: Percentage of users who did not experience a crash
- **Release adoption**: Session or user count in last 24 hours as percentage of all project releases

### Adoption Stages (mobile/desktop, calculated hourly)

- **Adopted**: 10%+ of sessions
- **Low Adoption**: Below 10%
- **Replaced**: Previously adopted, now below threshold

---

## User Feedback

Three collection methods for gathering feedback from users.

### User Feedback Widget

Always-visible UI that captures: description, screenshots, email, associated replay (up to 60s prior), page URL, and tags.

### Crash-Report Modal

Automatic modal triggered after an error. Captures: description, Sentry issue link, page URL, and tags.

### User Feedback API

Programmatic submission for custom UIs. See platform-specific SDK docs for setup.

### Triage

- Filter by project, environment, date range
- Search with fields like `url:*/payments/*`
- Resolve, assign, or mark as spam (individually or in bulk)
- AI-powered summaries identify common sentiments and patterns
- Spam detection via Google Cloud Platform language model
- Create/link external issues (GitHub, Jira) directly from feedback

---

## Stats

The Stats page (`Organization Settings > Stats`) shows event and attachment consumption across your organization over a configurable period (1 hour to 90 days).

### Event Categories

| Category | Description |
|----------|-------------|
| **Accepted** | Successfully processed and stored |
| **Filtered** | Excluded by inbound filters (browser extensions, localhost, legacy browsers, web crawlers, specific releases) |
| **Rate Limited** | Dropped due to quotas, spike protection, DSN limits, or disabled features |
| **Invalid** | Rejected for format issues, duplicates, or missing projects |
| **Client Discard** | Dropped by SDK (queue overflow, network failure, sample rate) |

### Tabs (Business/Enterprise plans)

- **Usage**: Event and attachment volume with category breakdowns
- **Issues**: New issues, regressions, triage activity by team
- **Health**: Crash-free sessions, transaction health, alert counts, release counts
