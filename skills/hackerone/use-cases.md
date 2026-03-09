# HackerOne API: Use Cases & Integration Patterns

Based on HackerOne API v1 documentation.

## 1. Import Known Vulnerabilities

Import vulnerabilities discovered outside HackerOne (internal tests, automated scanners).

```bash
curl -X POST "https://api.hackerone.com/v1/reports" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "report",
      "attributes": {
        "team_handle": "myprogram",
        "title": "SQL Injection in search endpoint",
        "vulnerability_information": "Found by internal DAST scanner...",
        "impact": "Database access",
        "source": "internal_scanner"
      }
    }
  }'
```

The `source` attribute tracks origin — useful for analytics and duplicate detection.

## 2. Query & Filter Reports

### Basic filtering
```bash
curl "https://api.hackerone.com/v1/reports?filter[program][]=myprogram" \
  -u "$API_ID:$API_TOKEN"
```

### Multiple states
```bash
curl "https://api.hackerone.com/v1/reports?filter[state][]=triaged&filter[state][]=retesting" \
  -u "$API_ID:$API_TOKEN"
```

### Custom field filtering
```bash
curl "https://api.hackerone.com/v1/reports?filter[custom_fields][CF_123]=urgent" \
  -u "$API_ID:$API_TOKEN"
```

### Combine filters
```bash
curl "https://api.hackerone.com/v1/reports?filter[program][]=myprogram&filter[state][]=triaged&filter[severity][]=critical" \
  -u "$API_ID:$API_TOKEN"
```

## 3. Bounty Management

### Award bounty on a report
```bash
curl -X POST "https://api.hackerone.com/v1/reports/12345/bounties" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"type": "bounty", "attributes": {"amount": 500, "currency": "USD"}}}'
```

### Award external bounty (discovered outside HackerOne)
Use the program bounty endpoint with additional fields: amount, currency, severity rating, and reference IDs.

## 4. Program Management

### Find your program info
```bash
# List your programs
curl "https://api.hackerone.com/v1/programs" -u "$API_ID:$API_TOKEN"

# Get specific program with members and groups
curl "https://api.hackerone.com/v1/programs/12345" -u "$API_ID:$API_TOKEN"
```

### Check program balance
```bash
curl "https://api.hackerone.com/v1/programs/12345/balance" -u "$API_ID:$API_TOKEN"
```

### Get billing transactions
```bash
# Filter by month/year (not available for sandbox programs)
curl "https://api.hackerone.com/v1/programs/12345/payment_transactions?month=3&year=2024" \
  -u "$API_ID:$API_TOKEN"
```

### Check hacker participation in private programs
```bash
# Query allowed reporters
curl "https://api.hackerone.com/v1/programs/12345/allowed_reporters" -u "$API_ID:$API_TOKEN"

# Check specific reporter activity types:
# activity-program-hacker-joined, activity-program-hacker-left, activity-invitation-received
```

### Update program policy
```bash
curl -X PUT "https://api.hackerone.com/v1/programs/12345/policy" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"type": "program", "attributes": {"policy": "New policy content..."}}}'
```

Auto-notifies subscribers of policy changes.

## 5. Asset Management

### Step 1: Get organization ID
```bash
curl "https://api.hackerone.com/v1/me/organizations" -u "$API_ID:$API_TOKEN"
```

### Step 2: Import assets via CSV
```bash
curl -X POST "https://api.hackerone.com/v1/assets/import" \
  -u "$API_ID:$API_TOKEN" \
  -F "file=@assets.csv"
```

CSV columns: `identifier`, `asset_type`, `technologies`, `confidentiality_requirement`, `integrity_requirement`, `availability_requirement`, `description`, `reference`

**Asset types:** `Domain`, `Url`, `Cidr`, `Hardware`, `SourceCode`, `IosAppStore`, `IosTestflight`, `IosIpa`, `AndroidPlayStore`, `AndroidApk`, `WindowsMicrosoftStore`, `Executable`, `OtherAsset`

### Step 3: Attach screenshots
```bash
curl -X POST "https://api.hackerone.com/v1/assets/67890/screenshots" \
  -u "$API_ID:$API_TOKEN" \
  -F "file=@screenshot.png"
```

## 6. Organization Management

### Invite members
```bash
curl -X POST "https://api.hackerone.com/v1/organizations/123/invitations" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"type": "invitation", "attributes": {"email": "user@company.com"}}}'
```

Email validated against eligibility settings.

### Manage groups
```bash
# Create group with members, programs, and permissions
curl -X POST "https://api.hackerone.com/v1/organizations/123/groups" \
  -u "$API_ID:$API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "group",
      "attributes": {
        "name": "Triage Team",
        "permissions": ["report_management"]
      }
    }
  }'
```

## 7. Automatic Inbox Assignment

Route incoming reports to custom inboxes based on attributes.

### Prerequisites
- Report permission on the program
- Read-only permission on custom inboxes

### Workflow

```
1. Get org ID        → GET /v1/me/organizations
2. Get inbox IDs     → GET /v1/organizations/{org_id}/inboxes
3. Map attributes    → Build report-attribute-to-inbox mapping
4. Set webhook       → Trigger on "report_created" event
5. On webhook fire   → GET /v1/reports/{id} to fetch report details
6. Assign inbox      → PUT /v1/reports/{id}/inboxes
```

**Key constraint:** Reports cannot be assigned to default inboxes — only custom inboxes.

## 8. Program Analytics

### Submissions by time period
```bash
curl "https://api.hackerone.com/v1/analytics?key=submissions&interval=quarter&start_at=2024-01-01&end_at=2024-12-31&team_id=12345" \
  -u "$API_ID:$API_TOKEN"
```

### Bounties awarded
```bash
curl "https://api.hackerone.com/v1/analytics?key=bounty_awarded&interval=month&start_at=2024-01-01&end_at=2024-12-31&organization_id=67890" \
  -u "$API_ID:$API_TOKEN"
```

### SLA metrics
Single-value queries returning:
- `missed_first_response_target`
- `average_first_response_time` / `median_first_response_time`
- Equivalent metrics for triage, bounty, and resolution stages

Times are returned in **seconds**. Averages return `null` when denominator is zero.

## 9. Incremental Data Sync

Efficiently sync changes without re-fetching everything:

```bash
# First sync: get all activities
curl "https://api.hackerone.com/v1/incremental/activities?handle=myprogram&sort=updated_at&order=asc" \
  -u "$API_ID:$API_TOKEN"

# Save meta.max_updated_at from response

# Subsequent syncs: only get changes
curl "https://api.hackerone.com/v1/incremental/activities?handle=myprogram&updated_at_after=2024-03-15T10:30:00.000Z&sort=updated_at&order=asc" \
  -u "$API_ID:$API_TOKEN"
```

## Common Integration Patterns

### External tracker sync
1. Set webhook for state change events
2. On webhook → create/update ticket in Jira/Linear/etc.
3. Use `reference` field to link back: `PUT /v1/reports/{id}/reference`

### Dashboard building
1. Use analytics API for aggregate metrics
2. Use reports API with filters for drill-down
3. Use incremental activities for real-time updates

### Automated triage
1. Webhook on `report_created`
2. Fetch report details
3. Apply rules (severity, scope, custom fields)
4. Auto-assign to inbox/user/group
5. Add comment with initial assessment
