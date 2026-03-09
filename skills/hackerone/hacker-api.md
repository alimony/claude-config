# HackerOne API: Hacker Endpoints

Based on HackerOne API v1 documentation.

All hacker endpoints are prefixed with `/v1/hackers/`. Authentication uses the hacker's personal API token (generated from Settings).

## Hacktivity (Public Reports)

### Search Public Reports
```
GET /v1/hackers/hacktivity
```

Uses Apache Lucene query syntax for filtering.

| Parameter | Type | Description |
|-----------|------|-------------|
| `queryString` | string (required) | Lucene filter expression |
| `page[number]` | integer | Default: 1 |
| `page[size]` | integer | 1-100, default: 25 |

**Supported query fields:**
`severity_rating`, `asset_type`, `substate`, `cwe`, `cve_ids`, `reporter`, `team`, `total_awarded_amount`, `disclosed_at`, `has_collaboration`, `disclosed`

```bash
# Find critical XSS reports
curl "https://api.hackerone.com/v1/hackers/hacktivity?queryString=severity_rating:critical+AND+cwe:CWE-79" \
  -u "$USERNAME:$API_TOKEN"
```

Response includes: title, severity, CVE IDs, awards, disclosure status, and relationships to reporter and program.

---

## Reports

### List Your Reports
```
GET /v1/hackers/me/reports
```

Paginated list of the authenticated hacker's vulnerability reports.

### Get Single Report
```
GET /v1/hackers/reports/{id}
```

Full report details including activities, attachments, severity, bounties, weakness, and remediation guidance.

**Note:** `vulnerability_information` is only included if the hacker owns the report.

### Create Report
```
POST /v1/hackers/reports
```

Submit a vulnerability to a program.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `team_handle` | string | Yes | Target program |
| `title` | string | Yes | Report title |
| `vulnerability_information` | string | Yes | Detailed description with repro steps |
| `impact` | string | Yes | Security impact |
| `severity_rating` | string | No | `none`, `low`, `medium`, `high`, `critical` |
| `weakness_id` | integer | No | CWE reference ID |
| `structured_scope_id` | integer | No | Target asset scope |

```bash
curl -X POST "https://api.hackerone.com/v1/hackers/reports" \
  -u "$USERNAME:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "report",
      "attributes": {
        "team_handle": "security_program",
        "title": "SSRF in webhook handler",
        "vulnerability_information": "## Steps\n1. Navigate to...",
        "impact": "Internal network scanning possible",
        "severity_rating": "high"
      }
    }
  }'
```

---

## Report Intents (AI-Assisted Drafts)

Draft reports with AI analysis before formal submission.

### List Report Intents
```
GET /v1/hackers/report_intents
```

### Create Report Intent
```
POST /v1/hackers/report_intents
```

| Field | Required | Description |
|-------|----------|-------------|
| `team_handle` | Yes | Target program |
| `description` | Yes | Vulnerability details for AI analysis |

### Get / Update / Delete
```
GET    /v1/hackers/report_intents/{id}
PATCH  /v1/hackers/report_intents/{id}
DELETE /v1/hackers/report_intents/{id}
```

### Submit (Convert to Report)
```
POST /v1/hackers/report_intents/{id}/submit
```

Converts the draft into a formal vulnerability report.

### Report Intent States
- `pending` — being analyzed
- `ready_to_submit` — analysis complete
- `submitted` — converted to report

### AI Job Types
`assistant_response`, `revise_intent`, `analyze_asset_type`, `analyze_vulnerability_presence`, `analyze_bug_type`, `determine_asset`, `analyze_cif`, `analyze_bug_class_completeness`, `assistant_summary`

### Attachment Management
```
GET    /v1/hackers/report_intents/{id}/attachments
POST   /v1/hackers/report_intents/{id}/attachments      # multipart/form-data with files[]
DELETE /v1/hackers/report_intents/{id}/attachments/{attachment_id}
```

Attachment URLs expire after 60 minutes.

---

## Programs

### List Available Programs
```
GET /v1/hackers/programs
```

Returns bug bounty programs with: handle, name, currency, policy, submission state, bounty offerings, and scope status.

### Get Program Details
```
GET /v1/hackers/programs/{handle}
```

Note: uses `handle` (string), not numeric ID.

### Get Structured Scopes
```
GET /v1/hackers/programs/{handle}/structured_scopes
```

Asset definitions with type, identifier, bounty eligibility, severity caps, and CIA requirements.

| Filter | Description |
|--------|-------------|
| `filter[id__gt]` | ID greater than (for large datasets > 10,000) |
| `filter[created_at__gt]` | Created after ISO 8601 timestamp |
| `filter[updated_at__gt]` | Updated after ISO 8601 timestamp |

### Get Weaknesses
```
GET /v1/hackers/programs/{handle}/weaknesses
```

CWE-mapped vulnerability types with descriptions and external identifiers.

---

## Payments

### Get Balance
```
GET /v1/hackers/payments/balance
```

Returns `{"balance": "1234.56"}`.

### Get Earnings
```
GET /v1/hackers/payments/earnings
```

Paginated earnings history. Each earning has: `amount`, `created_at`, and type (`earning-bounty-earned`, `earning-retest-completed`, `earning-pentest-completed`). Relationships to program and report.

### Get Payouts
```
GET /v1/hackers/payments/payouts
```

Payout transactions with: `amount`, `paid_out_at`, `reference`, `payout_provider` (e.g., PayPal), `status`.

---

## Hacker Endpoint Quick Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| Search hacktivity | GET | `/v1/hackers/hacktivity` |
| My reports | GET | `/v1/hackers/me/reports` |
| Get report | GET | `/v1/hackers/reports/{id}` |
| Submit report | POST | `/v1/hackers/reports` |
| List programs | GET | `/v1/hackers/programs` |
| Program details | GET | `/v1/hackers/programs/{handle}` |
| Program scopes | GET | `/v1/hackers/programs/{handle}/structured_scopes` |
| Program weaknesses | GET | `/v1/hackers/programs/{handle}/weaknesses` |
| Report intents | GET/POST | `/v1/hackers/report_intents` |
| Submit intent | POST | `/v1/hackers/report_intents/{id}/submit` |
| Balance | GET | `/v1/hackers/payments/balance` |
| Earnings | GET | `/v1/hackers/payments/earnings` |
| Payouts | GET | `/v1/hackers/payments/payouts` |

## Code Examples Available

The HackerOne docs provide example code in: Shell/curl, Python, Ruby, Java, JavaScript, and Go.
