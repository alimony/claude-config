# HackerOne API: Customer Report Endpoints

Based on HackerOne API v1 documentation.

## Overview

Reports are the core resource — vulnerability submissions from hackers. The customer API provides full CRUD and lifecycle management for reports.

## List & Read

### Get All Reports
```
GET /v1/reports
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `filter[program][]` | string | Filter by program handle |
| `filter[state][]` | string | Filter by state (can specify multiple) |
| `filter[severity][]` | string | Filter by severity rating |
| `filter[custom_fields][CF_ID]` | string | Filter by custom field value |
| `page[number]` | integer | Page number (default: 1) |
| `page[size]` | integer | Page size (default: 25, max: 100) |

```bash
# Get triaged reports for a program
curl "https://api.hackerone.com/v1/reports?filter[program][]=myprogram&filter[state][]=triaged" \
  -u "$API_ID:$API_TOKEN"
```

### Get Single Report
```
GET /v1/reports/{report_id}
```

Returns full report with relationships (reporter, program, severity, bounties, activities, attachments, weakness, structured_scope, summaries).

## Create & Import

### Create Report
```
POST /v1/reports
```

Used to import known vulnerabilities discovered outside HackerOne (internal tests, automated scanners). The `source` attribute tracks origin for analytics and duplicate detection.

```bash
curl -X POST "https://api.hackerone.com/v1/reports" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "report",
      "attributes": {
        "team_handle": "myprogram",
        "title": "XSS in login page",
        "vulnerability_information": "Steps to reproduce...",
        "impact": "Account takeover possible",
        "severity_rating": "high",
        "source": "internal_scanner"
      }
    }
  }'
```

## State Management

### Change State
```
PUT /v1/reports/{report_id}/state
```

Report states: `new`, `pending-program-review`, `triaged`, `needs-more-info`, `resolved`, `not-applicable`, `informative`, `duplicate`, `spam`, `retesting`

```bash
curl -X PUT "https://api.hackerone.com/v1/reports/12345/state" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"type": "state-change", "attributes": {"state": "triaged"}}}'
```

## Bounty & Rewards

### Award Bounty
```
POST /v1/reports/{report_id}/bounties
```

For HackerOne-submitted vulnerabilities. Body includes `amount` and `currency`.

### Mark Ineligible for Bounty
```
POST /v1/reports/{report_id}/ineligible
```

### Bounty Suggestions
```
GET /v1/reports/{report_id}/bounty_suggestions
POST /v1/reports/{report_id}/bounty_suggestions
```

### Award Swag
```
POST /v1/reports/{report_id}/swag
```

## Comments & Communication

### Create Comment
```
POST /v1/reports/{report_id}/comments
```

### Add Participant
```
POST /v1/reports/{report_id}/participants
```

Adds external collaborators to a report.

## Attachments

### Upload Attachments
```
POST /v1/reports/{report_id}/attachments
```

Uses `multipart/form-data` with `files[]` parameter.

### Delete Attachment
```
DELETE /v1/reports/{report_id}/attachments/{attachment_id}
```

## Metadata Updates

### Update Title
```
PUT /v1/reports/{report_id}/title
```

### Update Severity
```
PUT /v1/reports/{report_id}/severity
```

### Update Weakness
```
PUT /v1/reports/{report_id}/weakness
```

### Update Structured Scope
```
PUT /v1/reports/{report_id}/scope
```

### Update Reference
```
PUT /v1/reports/{report_id}/reference
```

Sets external tracking reference (e.g., Jira ticket ID).

### Update CVEs
```
PUT /v1/reports/{report_id}/cves
```

### Update Custom Fields
```
PUT /v1/reports/{report_id}/custom_fields
```

### Update Tags
```
PUT /v1/reports/{report_id}/tags
```

## Assignment & Triage

### Update Assignee
```
PATCH /v1/reports/{report_id}/assignee
```

Assign to a specific user or group.

### Update Inboxes
```
PUT /v1/reports/{report_id}/inboxes
```

Move report to custom inboxes. **Note:** Cannot assign to default inboxes — only custom inboxes.

## Disclosure

### Update Disclosure
```
PUT /v1/reports/{report_id}/disclosure
```

Manage public disclosure requests and status.

## Retesting

### Request Retest
```
POST /v1/reports/{report_id}/retest
```

### Cancel Retest
```
DELETE /v1/reports/{report_id}/retest
```

## Other Operations

### Generate PDF
```
POST /v1/reports/{report_id}/generate_pdf
```

### Redact Report
```
POST /v1/reports/{report_id}/redact
```

### Escalate Report
```
POST /v1/reports/{report_id}/escalate
```

### Remove Escalation
```
DELETE /v1/reports/{report_id}/escalate
```

### Transfer Report
```
POST /v1/reports/{report_id}/transfer
```

Transfer a report to a different program.

### Add Summary
```
POST /v1/reports/{report_id}/summary
```

Summaries are visible before disclosure (categories: `researcher`, `team`, `triage`).

## Report Endpoint Quick Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| List reports | GET | `/v1/reports` |
| Get report | GET | `/v1/reports/{id}` |
| Create report | POST | `/v1/reports` |
| Change state | PUT | `/v1/reports/{id}/state` |
| Award bounty | POST | `/v1/reports/{id}/bounties` |
| Add comment | POST | `/v1/reports/{id}/comments` |
| Upload attachment | POST | `/v1/reports/{id}/attachments` |
| Update severity | PUT | `/v1/reports/{id}/severity` |
| Update assignee | PATCH | `/v1/reports/{id}/assignee` |
| Update inboxes | PUT | `/v1/reports/{id}/inboxes` |
| Request retest | POST | `/v1/reports/{id}/retest` |
| Generate PDF | POST | `/v1/reports/{id}/generate_pdf` |
| Transfer | POST | `/v1/reports/{id}/transfer` |
| Escalate | POST | `/v1/reports/{id}/escalate` |
| Manage disclosure | PUT | `/v1/reports/{id}/disclosure` |
| Update title | PUT | `/v1/reports/{id}/title` |
| Update reference | PUT | `/v1/reports/{id}/reference` |
| Update CVEs | PUT | `/v1/reports/{id}/cves` |
| Update weakness | PUT | `/v1/reports/{id}/weakness` |
| Update scope | PUT | `/v1/reports/{id}/scope` |
| Update custom fields | PUT | `/v1/reports/{id}/custom_fields` |
| Update tags | PUT | `/v1/reports/{id}/tags` |
| Add summary | POST | `/v1/reports/{id}/summary` |
| Add participant | POST | `/v1/reports/{id}/participants` |
| Mark ineligible | POST | `/v1/reports/{id}/ineligible` |
| Award swag | POST | `/v1/reports/{id}/swag` |
| Redact | POST | `/v1/reports/{id}/redact` |
