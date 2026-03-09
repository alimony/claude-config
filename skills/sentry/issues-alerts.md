# Sentry: Issues, Alerts & Dashboards
Based on Sentry documentation (docs.sentry.io).

## Issues

An **issue** is a single bug or problem grouped from similar events. Sentry automatically groups events using fingerprints — events with the same fingerprint become one issue. Quota is consumed by events, not issues.

### Issue Types

- **Error Issues** — grouped error events (exceptions, crashes)
- **Performance Issues** — grouped poorly-performing transactions (N+1 queries, slow DB, render blocking, etc.)

### Issue Details Page

The central debugging hub. Key sections:

- **Header** — error message, event/user counts, assign/resolve/archive actions
- **Stack Trace** — most important element for grouping; shows the error line and call chain
- **Breadcrumbs** — timeline of events leading to the error (HTTP requests, logs, DOM events)
- **Suspect Commits** — commits likely responsible, with author suggestions
- **Trace Preview** — abbreviated distributed trace with cross-linked issues
- **Session Replay** — recording of the user session (frontend and backend with distributed tracing)
- **Tags** — searchable key/value pairs (browser, OS, release, custom tags)
- **Contexts** — auto-generated or manually set debugging metadata

Event navigation defaults to the "Recommended" event (selected by recency within 7 days, relevance, and debugging content availability).

## Issue Priority

Three levels, determined automatically by log level and actionability:

| Priority | Typical Events | Action |
|----------|---------------|--------|
| **High** | `ERROR`, `FATAL` | Requires immediate attention |
| **Medium** | `WARNING` | Attention in the near term |
| **Low** | `DEBUG`, `INFO` | No urgent action needed |

**Enhanced priority** (Business/Trial plans, Python and JavaScript): also considers error message content, whether the error was handled, and historical actions on similar issues.

**Automatic escalation**: event volume spikes raise priority automatically. Once manually changed, priority is no longer auto-adjusted.

## Issue States & Triage

Six mutually exclusive states:

| State | Search Syntax | Description |
|-------|--------------|-------------|
| **New** | `is:new` | Created in the last 7 days |
| **Ongoing** | `is:ongoing` | Older than 7 days or manually marked reviewed |
| **Escalating** | `is:escalating` | Exceeded forecasted event volume |
| **Regressed** | `is:regressed` | A resolved issue that recurred |
| **Archived** | `is:archived` | Removed from active triage |
| **Resolved** | `is:resolved` | Marked as fixed |

**Triage tabs**: All Unresolved, For Review (new/regressed/unreviewed), Regressed, Archived, Escalating.

**Sort options**: Last Seen, First Seen, Trends, Events (volume), Users (affected count).

### Archive Options

Archiving pauses alerts and removes the issue from the stream:

- Until escalating (default) — resurfaces if volume spikes
- Forever — events still recorded but never escalate
- For a specific time period
- Until N occurrences
- Until affecting N users

### Resolution

- Manual: mark as Resolved (optionally tied to a release)
- Commit-based: include the issue ID in a commit message
- **Delete and Discard Forever** (Error Issues only): prevents future event recording

## Issue Grouping & Fingerprints

Sentry assigns a fingerprint to each event. Events with the same fingerprint are grouped into one issue. The default fingerprint (`{{ default }}`) uses stack trace frames, exception types, and error messages.

### Why Similar Issues Stay Separate

Subtle differences (e.g., different function names at the top of a stack trace) produce different fingerprints even when errors look similar.

### Four Ways to Customize Grouping

1. **Merge Issues** — combines existing issues retroactively. Does not affect future grouping. Can be unmerged later via Issue Details > Merged Issues tab.

2. **Fingerprint Rules** (server-side) — match on error type or message patterns and assign a custom fingerprint. Example:

   ```
   # Group all ConnectTimeout errors together
   type:ConnectTimeout -> connect-timeout

   # Group by message pattern with wildcards
   message:"Failed to connect to *" -> connection-failure
   ```

3. **Stack Trace Rules** — control which frames are used for grouping. Sentry auto-filters framework/middleware code, but this is customizable. Example:

   ```
   # Mark frames from vendor code as not in-app
   family:javascript stack.abs_path:**/node_modules/** -app

   # Force specific paths to be treated as in-app
   stack.abs_path:**/my-app/src/** +app
   ```

4. **SDK-side Fingerprinting** — assign fingerprints in code before sending to Sentry:

   ```python
   # Python SDK example
   def before_send(event, hint):
       if "DatabaseError" in str(hint.get("exc_info", "")):
           event["fingerprint"] = ["database-error"]
       return event

   sentry_sdk.init(before_send=before_send)
   ```

   ```javascript
   // JavaScript SDK example
   Sentry.init({
     beforeSend(event) {
       if (event.exception?.values?.[0]?.type === "ChunkLoadError") {
         event.fingerprint = ["chunk-load-error"];
       }
       return event;
     },
   });
   ```

Custom rules only affect future events — existing issues remain unchanged.

## Ownership Rules

Automatically assign error issues to teams or individuals. Enables auto-assignment and targeted alert routing.

### Rule Syntax

Format: `type:pattern owners`

| Type | Matches | Example |
|------|---------|---------|
| `path:` | File paths in stack traces | `path:src/billing/*.py #billing-team` |
| `module:` | Module names in stack traces | `module:com.example.auth admin@example.com` |
| `url:` | Request URLs | `url:*/api/checkout/* #payments` |
| `tags.KEY:` | Event tag values | `tags.transaction:*/api/users/* #backend` |

Patterns support Unix-style globs (`*`, `?`). Multiple owners separated by spaces. Teams prefixed with `#`.

### Code Owners (Business/Enterprise)

Import GitHub/GitLab CODEOWNERS files. Requires Code Mappings to normalize file paths. Max 3MB. Does not support exclusion rules (lines without owners).

### Evaluation Order

1. Code Owners rules evaluated top-to-bottom
2. Ownership Rules evaluated top-to-bottom
3. **Last matching rule wins**
4. Leftmost owner assigned if multiple owners specified

Once manually assigned, auto-assignment is disabled for that issue.

## Alerts

### Alert Types

**Issue Alerts** — trigger per-event when issues match criteria. Each new event is evaluated against three components:

- **When** (triggers): new issue, issue frequency increasing, resolved/archived issues becoming unresolved
- **If** (filters): narrow by issue attributes (level, category, tags, assigned team)
- **Then** (actions): send notification, assign, create ticket

**Metric Alerts** — trigger when aggregate metrics cross thresholds. Two severity levels: Warning and Critical. Max 1,000 per organization. Available metrics:

| Category | Metrics |
|----------|---------|
| Errors | Error count, users affected |
| Sessions | Crash-free session rate, crash-free user rate |
| Performance | Throughput, transaction duration, Apdex, failure rate, LCP, FID, CLS |
| Custom | Custom metrics via SDK |

**Uptime Alerts** — trigger when HTTP checks fail to meet criteria. Max 100 per organization.

**User Feedback Alerts** — issue alert filtered by category "Feedback".

### Creating Alerts

1. Go to **Alerts > Create Alert Rule**
2. Choose type: Issues, Metric, or Uptime Monitor
3. Set conditions (When/If/Then for issue alerts; thresholds for metric alerts)

**Limits**: 100 issue alerts with "slow" conditions (change/percent-based), 500 with "fast" conditions (state changes).

**Duplication**: clone existing rules via Actions > Duplicate.

### Alert Management

- **Mute for me** — personal mute
- **Mute for everyone** — organization-wide mute
- Sentry auto-disables duplicate alerts and alerts without actions
- Re-enable by editing and re-saving

## Notifications

Four notification types:

| Type | Description | Default Channel |
|------|-------------|-----------------|
| **Workflow** | Issue state changes (resolved, regressed, assigned, commented) | Email to subscribed members |
| **Deploy** | Release deployed, sent to commit authors | Email |
| **Spend** | Quota consumption thresholds | Email, Slack, and others |
| **Weekly Reports** | Organization activity summary, sent Saturdays | Email |

### Subscription Management

Users auto-subscribe via: assignment, manual subscription, commenting, bookmarking, or resolution. Unsubscribe when unassigned, comment deleted, or bookmark removed.

Configure personal preferences at **User Settings > Notifications**. Spend notification thresholds at **Settings > Subscription > Manage Spend Notifications**.

## Dashboards

Dashboards provide a broad overview of application health across projects, built from widgets that visualize error and performance data.

### Built-In Dashboard

Every organization gets a default template dashboard shared across all users.

### Global Filters

Applied at the top of any dashboard, affecting all widgets:

- Projects, Environments, Date ranges, Releases
- Custom filters (add via the `+` button)
- Time series zoom syncs across all widgets

### Custom Dashboards

Create from scratch or from pre-built templates. Shared across the organization.

**Widget Builder**: configure data sources, queries, and visualizations.
**Widget Library**: pre-built widgets ready to add.

**Access control**: creators restrict editing to specific teams. Creators and org owners always retain edit access.

Each widget's ellipsis menu opens data in Discover or Issues for deeper investigation. The expanded Widget Viewer supports table pagination, sorting, column adjustment, independent chart zooming, and shareable URLs.

### Metrics Extraction (Early Adopter)

Collects metrics from custom tags and filters. Approximate metrics visible during creation; full metrics appear within ~15 minutes.

## Explore (Discover)

A powerful query engine for ad-hoc queries across all metadata, spanning multiple projects and environments. Use it to:

- Investigate error patterns and performance bottlenecks
- Query events by any tag, field, or attribute
- Build and save custom queries
- Correlate errors with releases, deployments, or user segments

Widgets can be opened directly in Discover from any dashboard for deeper analysis.

## Projects

A **project** represents a service or application. Create separate projects for different components (API server, frontend client, worker, etc.).

- Assign a team at creation — all team members get access
- Add additional teams via Project Teams settings
- Projects map to repos, components, or microservices aligned with team ownership
- Default views in Issues and Discover are project-scoped

**Projects vs. Environments**: projects organize services; environments (staging, production) help triage issues across release stages.

The Projects page shows: error/transaction snapshots (24h), crash-free session %, and deploy info.

## AI Features (Seer)

**Seer** is Sentry's AI debugging agent (add-on feature):

- **Autofix** — root cause analysis with suggested code fixes for errors and performance issues
- **Code Review** — analyzes GitHub PRs to identify bugs before merging
- **Issue Summary** — highlights what's wrong, potential causes, and connected trace insights
- **Query Assistant** — converts natural language into trace/span data queries
- **AI Summaries** — synthesizes User Feedback and Session Replay data for recurring patterns

### Configuration

- **Organization-wide toggle**: Settings > "Show Generative AI Features" (disables all AI)
- **Granular control**: Seer settings panel for selective feature activation
- **Advanced**: prevent code generation specifically, or restrict additional context in alerts

Sentry does not train AI models on your data by default. AI outputs are visible only to authorized account users.
