# Sentry: Integrations & Organization
Based on Sentry documentation (docs.sentry.io).

## Integration Categories

Sentry integrations are first-class actors within the platform. Categories:

- **Source Code Management** — GitHub, GitLab, Azure DevOps, Bitbucket, Perforce
- **Notification & Incidents** — Slack, PagerDuty, Microsoft Teams, Discord, Opsgenie
- **Project Management / Issue Tracking** — Jira, Linear, Asana, ClickUp, Height
- **Deployment** — Vercel, GitHub Actions, Bitbucket Pipelines, Netlify, Heroku (legacy)
- **Data Forwarding** — Amazon SQS, Segment, Splunk, Grafana
- **Session Replay** — FullStory, OpenReplay, BetterBugs
- **Feature Flags** — LaunchDarkly, Split

All integrations are installed at the organization level. Required role: **owner, manager, or admin**.

---

## Source Code Management

### GitHub

**Setup:** Settings > Integrations > GitHub. Authorize the GitHub App and select repository access. Three variants exist: GitHub (github.com), GitHub Enterprise (self-hosted), and Seer GitHub App (AI PR generation).

**Permissions required on GitHub:**

| Permission | Level | Purpose |
|---|---|---|
| Contents | Read & Write | Source files, suspect commits, PR creation |
| Pull Requests | Read & Write | PR comments for issues, AI review |
| Issues | Read & Write | Create/update issues from Sentry |
| Commit Statuses | Read & Write | Status checks on commits |
| Webhooks | Read & Write | Real-time event subscriptions |
| Members (org) | Read-only | User identity mapping |

**Key features:**

- **Suspect commits** — Identifies recent changes to files in the error stack trace. Authors become suggested assignees.
- **Resolve via commit** — Include `Fixes MYAPP-317` in a commit or PR message. Issue auto-resolves when code reaches production (requires release association).
- **Stack trace linking** — Maps frames to source files. With commit tracking, links point to the exact commit; otherwise defaults to the primary branch. Configure via: project, repository, default branch, and optional stack trace / source code root paths.
- **PR comments** — On merged PRs: comments when a merge is suspected of causing issues (up to 5 linked issues). On open PRs: scans changes against recent unresolved issues (Python, JS/TS, PHP, Ruby).
- **Code Owners** — Import CODEOWNERS to auto-route issues and alerts (Business/Enterprise).
- **Issue sync** — Bidirectional sync of comments, assignees, and status between Sentry and GitHub. Requires user mapping (1:1 GitHub-to-Sentry).
- **AI code review** — Enable via org settings ("Show Generative AI Features" + "Enable AI Code Review").
- **Missing member detection** — Monthly alerts about GitHub contributors not in Sentry org.

**Issue creation:** Automatic via Issue Alert action "Create a new GitHub issue" or manual via the Linked Issues sidebar panel.

### GitLab

**Setup:** Settings > Integrations > GitLab > Add Installation. Create a Sentry application in GitLab, then provide the base URL, group path, application ID, and secret. Use a **dedicated service account** rather than a personal account.

**Key features:** Same core set as GitHub — suspect commits, stack trace linking, resolve via commit/PR (`Fixes SHORT-ID`), Code Owners (Business/Enterprise), and issue management.

**Limitations:**
- Repositories must be under group accounts, not personal accounts
- Subgroups require GitLab 11.6+
- Issues are searchable by name only (not number)
- The integration creator becomes the default reporter for created issues

**Stack trace linking setup:** Configure project, repository, branch, and optional Stack Trace Root / Source Code Root to map file paths correctly.

---

## Notification & Incidents

### Slack

**Setup:** Settings > Integrations > Slack > Add Workspace. Authenticate with your Slack workspace. For private channels, type `@sentry` in the channel to add the bot.

**Identity linking:** Run `/sentry link` in Slack for personal notifications. Run `/sentry link team` for team-level alerts.

**Alert configuration:**

- **Issue alerts** — Action: "Send a Slack notification". Specify workspace, channel, optional tags/notes. Quick actions in Slack: Resolve, Archive, Select Assignee.
- **Metric alerts** — Notifications include status charts and investigation links. Updates arrive as threaded replies; critical alerts also post to the main channel.

**Troubleshooting:** If rate-limited when saving alert rules, enter channel/user ID alongside the name. Find channel ID by clicking the channel name header; user ID via avatar > View full profile > "..." > Copy member ID.

### PagerDuty

**Setup:** Settings > Integrations > PagerDuty > Add Installation. Authenticate and select which PagerDuty services receive incidents.

**Alert routing:**

- **Issue alerts** — Action: "Send a PagerDuty notification". Choose account + service. Default severity: critical for fatal/error, warning for warnings, info for debug/info.
- **Metric alerts** — Same account/service selection. Default: critical for critical status, warning for warning status.

**Auto-resolution:** PagerDuty incidents auto-resolve when the Sentry metric alert resolves (only if no warning threshold exists). With warning thresholds, manual PagerDuty resolution may be needed.

### Discord

Install via Settings > Integrations > Discord. Configure alert rules to send notifications to specific Discord channels. Supports issue and metric alerts.

---

## Project Management

### Jira

**Setup (Cloud):** Settings > Integrations > Jira. Install from the Jira marketplace. Disable ad-blockers during setup. Select Sentry organizations to connect.

**Setup (Data Center):** Uses Application Links with RSA key pairs. Generate keys via OpenSSL, create an application link in Jira with OAuth URLs, configure incoming authentication.

**Features:**

- **Issue creation** — Manual from the Linked Issues sidebar (Team+). Automatic via Issue Alert action (Business+).
- **Issue sync** — Bidirectional sync of comments, assignees, and status (Team+). Resolving in Sentry updates Jira; closing in Jira updates Sentry.
- **Ignored fields** — Hide specific Jira fields from the creation form by entering comma-separated field IDs in configuration.

**Troubleshooting:**
- Custom required fields that can't be pre-populated: create tickets in Jira first, then link
- Failed issue creation: verify alert priority matches project configuration
- 4xx/5xx errors: ensure Jira instance is publicly accessible and Sentry IPs are whitelisted
- Assignee sync: users need "Assignable User" permission in the Jira project

### Linear

**Setup:** Settings > Integrations > Linear. Follow Linear's setup docs at linear.app/docs/sentry. Not available on self-hosted Sentry.

**Features:**

- **Automatic issue creation** — Create alert rules with action "Notify Integration" > "Linear"
- **Manual linking** — Use the Linked Issues sidebar to create or link Linear issues
- Maintained and supported by Linear directly

---

## Deployment

### Vercel

**Setup:** Visit vercel.com/integrations/sentry, click "Add Integration", select Vercel scope and projects, review permissions. This creates an internal integration for auth tokens — **do not delete it**.

**Auto-configured environment variables:**

| Variable | Purpose |
|---|---|
| `SENTRY_ORG` | Organization slug |
| `SENTRY_PROJECT` | Linked project name |
| `SENTRY_AUTH_TOKEN` | Auth token from internal integration |
| `NEXT_PUBLIC_SENTRY_DSN` | DSN for Next.js SDK |

**Source maps & releases:**
1. Instrument your code with a Sentry SDK
2. Install a source code integration (GitHub/GitLab) and add repositories
3. Add a Sentry bundler plugin (webpack, Vite, Esbuild, or Rollup)
4. Redeploy on Vercel to trigger the release

Next.js and SvelteKit projects have bundler plugins pre-configured.

**Vercel Marketplace integration** also sets `SENTRY_VERCEL_LOG_DRAIN_URL`, `SENTRY_OTLP_TRACES_URL`, and `SENTRY_PUBLIC_KEY` for log/trace forwarding.

### Other Deployment Integrations

- **GitHub Actions** — Use `getsentry/action-release` to create releases and upload source maps in CI
- **Bitbucket Pipelines** — Similar release/source-map workflow via Sentry CLI
- **Netlify** — Plugin-based integration for automatic release creation

All deployment integrations associate commits with releases, enabling suspect commits and deploy tracking.

---

## Authentication

### Single Sign-On (SSO)

**Trial/Team+ plans:** Google Business App (single domain), GitHub Organizations.

**Business/Enterprise plans:** SAML2 providers — Auth0, Azure AD, Okta, OneLogin, Rippling, Jumpcloud. SCIM provisioning for automated identity management.

**SAML endpoints** (replace `[org_slug]` with your org):
- ACS: `https://sentry.io/saml/acs/[org_slug]/`
- SLS: `https://sentry.io/saml/sls/[org_slug]/`
- Metadata: `https://sentry.io/saml/metadata/[org_slug]/`

Supports IdP-initiated SSO, SP-initiated SSO, and IdP-initiated Single Logout.

**Enforcement:** Once activated, all existing users must link their account. New SSO users get member-level access across all teams. Sessions persist for two weeks. Sentry monitors linked accounts and disables access if revocation is detected.

### Two-Factor Authentication (2FA)

Enable per-user or enforce org-wide. Supports authenticator apps (TOTP) and hardware security keys (U2F/WebAuthn). Recovery codes are provided at setup — store them securely.

---

## Organization: Membership & Roles

### Organization-Level Roles (all plans)

| Role | Capabilities |
|---|---|
| **Billing** | Manage payment and compliance only |
| **Member** | View data, act on issues, join teams |
| **Admin** | Edit integrations, manage projects (deprecated on Business/Enterprise) |
| **Manager** | Full team/project management, membership oversight |
| **Owner** | Complete control; can transfer/remove the organization |

### Team-Level Roles (Business/Enterprise)

| Role | Capabilities |
|---|---|
| **Team Contributor** | View issues, perform basic actions |
| **Team Admin** | Manage team membership and projects within their team |

When a user holds multiple roles across teams, the **union of permissions** applies.

### Member Management

- **Inviting:** Managers and Owners control invitations. Enable "Let Members Invite Others" to delegate.
- **Open Membership:** Teams allow open joining by default. Disable via the "Open Membership" toggle to require approval from Managers, Owners, or Team Admins.
- **Project access:** Granted through team membership. Assign projects to teams; members join teams to gain access.

---

## Integration Patterns

### Recommended Workflow Setup

1. **Connect source code** (GitHub/GitLab) — Enables suspect commits, stack trace links, and resolve-via-commit
2. **Configure notifications** (Slack/PagerDuty) — Route issue and metric alerts to the right channels
3. **Link project management** (Jira/Linear) — Create and track issues from Sentry
4. **Set up deployment tracking** (Vercel/GitHub Actions) — Associate releases with commits for full traceability

### Release Association

Many features depend on linking commits to releases:
- Suspect commits identify which code change caused an error
- Resolve-via-commit/PR auto-closes issues when fixes deploy
- Deploy tracking shows which release introduced or resolved issues

Configure via: SDK release option, CI/CD integration, or Sentry CLI (`sentry-cli releases`).

### Code Owners

Available on Business/Enterprise. Import a CODEOWNERS file (GitHub or GitLab) to:
- Auto-assign issues to the responsible team/person
- Route alerts based on file ownership
- Surface ownership in the issue detail sidebar

### Stack Trace Linking

For all SCM integrations, configure code mappings:
- **Stack Trace Root** — The prefix in your stack traces (e.g., `app/`)
- **Source Code Root** — The corresponding path in your repo (e.g., `src/app/`)
- **Default Branch** — Branch to link to when no commit context exists

### Alert Routing Best Practices

- Use **issue alerts** for new/regression events with Slack for team visibility
- Use **metric alerts** with PagerDuty for threshold-based on-call escalation
- Set severity mappings explicitly rather than relying on defaults
- Thread metric alert updates in Slack to reduce channel noise
- Link Slack/Sentry identities (`/sentry link`) so personal notifications work
