# HackerOne API: Activities, Analytics, Credentials & More

Based on HackerOne API v1 documentation.

## Activities

Activities represent actions taken on reports (comments, state changes, bounty awards, etc.).

### Get Activity
```
GET /v1/activities/{id}
```

Returns a single activity with relationships (actor, attachments).

### Query Activities (Incremental)
```
GET /v1/incremental/activities
```

Best for syncing — fetches activities ordered by update date.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `handle` | string | Yes | Program handle |
| `report_id` | integer | No | Filter by report |
| `updated_at_after` | string | No | ISO 8601 cutoff |
| `sort` | string | No | `report_id`, `created_at`, or `updated_at` |
| `order` | string | No | `asc` or `desc` (default: `desc`) |
| `page[number]` | integer | No | Default: 1 |
| `page[size]` | integer | No | Default: 25, max: 100 |

Response includes `meta.max_updated_at` — save this for next sync call.

```bash
curl "https://api.hackerone.com/v1/incremental/activities?handle=myprogram&updated_at_after=2024-01-01T00:00:00Z&sort=updated_at&order=asc" \
  -u "$API_ID:$API_TOKEN"
```

### Activity Types (50+)

**Report state changes:**
`activity-bug-filed`, `activity-bug-triaged`, `activity-bug-resolved`, `activity-bug-reopened`, `activity-bug-inactive`, `activity-bug-duplicate`, `activity-bug-cloned`, `activity-bug-spam`, `activity-bug-new`, `activity-bug-needs-more-info`, `activity-bug-informative`, `activity-bug-not-applicable`, `activity-bug-retesting`

**Bounty & rewards:**
`activity-bounty-awarded`, `activity-bounty-suggested`, `activity-not-eligible-for-bounty`, `activity-swag-awarded`

**Comments:**
`activity-comment`, `activity-comments-closed`

**User management:**
`activity-user-assigned-to-bug`, `activity-group-assigned-to-bug`, `activity-nobody-assigned-to-bug`, `activity-user-banned-from-program`, `activity-external-user-invited`, `activity-external-user-joined`, `activity-external-user-removed`, `activity-external-user-invitation-cancelled`

**Program events:**
`activity-program-hacker-joined`, `activity-program-hacker-left`, `activity-program-inactive`

**Disclosure:**
`activity-agreed-on-going-public`, `activity-manually-disclosed`, `activity-report-became-public`, `activity-cancelled-disclosure-request`

**Retesting:**
`activity-bug-retesting`, `activity-report-retest-approved`, `activity-report-retest-rejected`, `activity-user-completed-retest`, `activity-user-left-retest`, `activity-retest-user-expired`

**Metadata updates:**
`activity-reference-id-added`, `activity-changed-scope`, `activity-report-severity-updated`, `activity-report-title-updated`, `activity-report-vulnerability-information-updated`, `activity-report-vulnerability-types-updated`, `activity-report-custom-field-value-updated`, `activity-report-prioritised`

**Other:**
`activity-mediation-requested`, `activity-hacker-requested-mediation`, `activity-triage-intake-completed`, `activity-invitation-received`

### Activity-Specific Fields

| Activity | Extra Fields |
|----------|-------------|
| `bounty-awarded` / `bounty-suggested` | `bounty_amount`, `bonus_amount` |
| `bug-cloned` / `bug-duplicate` | `original_report_id` |
| `external-user-invited` | `email` |
| `reference-id-added` | `reference`, `reference_url` |
| `changed-scope` | relationships: `old_scope`, `new_scope` |
| `custom-field-value-updated` | `old_value`, `new_value`, relationship: `custom_field_attribute` |
| `report-prioritised` | `high_priority`, `high_priority_reason` |
| `agreed-on-going-public` | `disclosed_at`, `allow_singular_disclosure_at` |
| `group-assigned-to-bug` | relationship: `group` |
| `external-user-removed` | relationship: `removed_user` |

### Base Activity Fields

All activities share:
- `id`, `type`, `report_id`, `message` (not Markdown), `internal` (boolean), `created_at`, `updated_at`
- Relationships: `actor` (user or program), `attachments`
- `internal: true` = visible only to program staff

---

## Analytics

### Get Analytics Data
```
GET /v1/analytics
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | string | Yes | Chart name (see below) |
| `interval` | string | Yes | `month`, `quarter`, or `year` |
| `start_at` | string | Yes | Start date (YYYY-MM-DD, inclusive) |
| `end_at` | string | Yes | End date (YYYY-MM-DD, exclusive) |
| `team_id` | string | No | Filter by program ID |
| `organization_id` | string | No | Filter by organization ID |

### Available Analytics Keys

**Submissions dashboard:**
Report counts by interval, optionally by severity.

**Rewards dashboard:**
`bounty_awarded` — total bounty amounts by time period.

**Response efficiency:**
SLA metrics including `missed_first_response_target`, `average_first_response_time`, `median_first_response_time`, and equivalent for triage, bounty, and resolution stages. Times in seconds; averages return `null` when denominator is zero.

**Other dashboards:**
Hacker engagement, statistics, mediations.

Response format:
```json
{
  "data": {
    "keys": ["date", "value"],
    "values": [["2024-01", 42], ["2024-02", 55]]
  }
}
```

---

## Credentials

Manage test credentials shared with hackers for specific scopes. Requires **Team Management** permission.

### List Credentials
```
GET /v1/credentials
```

| Parameter | Type | Required |
|-----------|------|----------|
| `program_id` | integer | Yes |
| `structured_scope_id` | integer | Yes |
| `state` | string | No (`revoked`, `available`, `claimed`) |

### Create Credential
```
POST /v1/credentials
```

```json
{
  "structured_scope_id": 123,
  "data": {
    "type": "credential",
    "attributes": {
      "credentials": "{\"username\": \"test\", \"password\": \"secret\"}",
      "assignee": "hacker_username"
    }
  },
  "batch_id": "optional-batch-id"
}
```

`credentials` is a JSON-encoded string containing the credential key-value pairs.

### Update Credential
```
PUT /v1/credentials/{id}
```

Set `recycle: true` to remove the current assignee.

### Assign Credential
```
PUT /v1/credentials/{id}/assign
```

Body: `{"username": "hacker_username"}`

### Revoke Credential
```
PUT /v1/credentials/{id}/revoke
```

Marks credential as revoked without deleting.

### Delete Credential
```
DELETE /v1/credentials/{id}/
```

### Credential Inquiries

Request information from hackers for a specific scope:

```
POST   /v1/programs/{id}/credential_inquiries
GET    /v1/programs/{id}/credential_inquiries
PUT    /v1/programs/{program_id}/credential_inquiries/{id}
DELETE /v1/programs/{program_id}/credential_inquiries/{id}
```

### Credential Inquiry Responses

```
GET    /v1/programs/{program_id}/credential_inquiries/{inquiry_id}/credential_inquiry_responses
DELETE /v1/programs/{program_id}/credential_inquiries/{inquiry_id}/credential_inquiry_responses/{id}
```

---

## Email

### Send Email
```
POST /v1/email
```

```json
{
  "data": {
    "type": "email-message",
    "attributes": {
      "email": "recipient@example.com",
      "subject": "Subject line",
      "markdown_content": "Email body in **markdown**"
    }
  }
}
```

**Constraint:** Recipient must share an organization with the API token holder, or the domain must be verified.

---

## HAI — AI Completions (Preview)

### Create Completion
```
POST /v1/hai/chat/completions
```

```json
{
  "data": {
    "type": "completion-request",
    "attributes": {
      "hai_play_id": 1,
      "messages": [{"role": "user", "content": "Analyze this..."}],
      "program_handles": ["myprogram"],
      "report_ids": [12345],
      "cve_ids": ["CVE-2024-1234"],
      "cwe_ids": ["CWE-79"]
    }
  }
}
```

### Get Completions
```
GET /v1/hai/get/completions
```

Retrieve previously generated AI completions.
