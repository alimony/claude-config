# Sentry Skills

Based on Sentry documentation.
Generated from https://docs.sentry.io on 2026-03-09.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [fundamentals](./fundamentals.md) | Core concepts, key terms, events/issues/traces, search syntax, data flow, onboarding checklist | 325 |
| [python-sdk](./python-sdk.md) | Python SDK setup, Django, Celery, FastAPI, Flask, configuration, capturing events, crons, profiling, logging | 774 |
| [javascript-sdk](./javascript-sdk.md) | JS SDK setup, React, Next.js, Node.js, source maps, session replay, ErrorBoundary, browser tracing | 820 |
| [configuration](./configuration.md) | SDK options, sampling, filtering, environments, releases, draining, dynamic sampling, quotas | 366 |
| [enriching-events](./enriching-events.md) | Tags, breadcrumbs, context, scopes, user identification, event processors, attachments, fingerprinting | 496 |
| [tracing-performance](./tracing-performance.md) | Spans, custom instrumentation, automatic instrumentation, trace propagation, OpenTelemetry, profiling | 450 |
| [issues-alerts](./issues-alerts.md) | Issue triage, priority, grouping, ownership rules, alerts, dashboards, AI features | 291 |
| [crons-releases](./crons-releases.md) | Cron monitoring, uptime checks, release tracking, deploy markers, release health, user feedback | 351 |
| [cli](./cli.md) | CLI installation, auth, release management, source maps, debug files, sending events, cron wrapping | 448 |
| [data-management](./data-management.md) | PII scrubbing, sensitive data, data retention, security, quotas, rate limiting | 357 |
| [integrations](./integrations.md) | GitHub, GitLab, Slack, PagerDuty, Jira, Linear, Vercel, SSO, teams, permissions | 255 |
| [ai-monitoring](./ai-monitoring.md) | AI agent monitoring, MCP server, agent skills, LLM call tracking, token costs, privacy | 417 |

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/sentry/python-sdk.md
    @~/.claude/skills/sentry/javascript-sdk.md

Or reference this index to see all available skills:

    @~/.claude/skills/sentry/index.md

## Coverage

- Total documentation pages read: ~150
- Skill files created: 12
- Total lines: 5,320
- Pages failed: 0
