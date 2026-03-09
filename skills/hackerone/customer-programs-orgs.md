# HackerOne API: Programs, Organizations & Assets

Based on HackerOne API v1 documentation.

## Programs

### List Your Programs
```
GET /v1/programs
```

### Get Program Details
```
GET /v1/programs/{program_id}
```

Returns program info including handle, policy, members, groups, and structured scopes.

### Program Balance
```
GET /v1/programs/{program_id}/balance
```

Check available funds for bounty payments.

### Billing Transactions
```
GET /v1/programs/{program_id}/payment_transactions
```

Filter by month/year. **Not available for sandbox programs.**

### Program Members
```
GET /v1/programs/{program_id}/members
```

### Audit Log
```
GET /v1/programs/{program_id}/audit_log
```

## Policy Management

### Update Policy
```
PUT /v1/programs/{program_id}/policy
```

Updates the program's disclosure policy content. Auto-notifies subscribers of changes.

### Upload Policy Attachment
```
POST /v1/programs/{program_id}/policy
```

Upload APKs, files, or other resources for hackers. Uses `multipart/form-data`.

## Hacker Management

### Allowed Reporters
```
GET /v1/programs/{program_id}/allowed_reporters
```

For private programs — list hackers with access, including history and activity.

### Reporters
```
GET /v1/programs/{program_id}/reporters
```

### Hacker Invitations
```
GET /v1/programs/{program_id}/hacker_invitations
POST /v1/programs/{program_id}/hacker_invitations
```

Invite hackers to private programs.

### Message Hackers
```
POST /v1/programs/{program_id}/messages
```

### Thanks / Acknowledgments
```
GET /v1/programs/{program_id}/thanks
```

## Structured Scopes

Define what assets are in scope for the program.

```
GET    /v1/programs/{program_id}/structured_scopes
POST   /v1/programs/{program_id}/structured_scopes
PUT    /v1/programs/{program_id}/structured_scopes/{scope_id}
DELETE /v1/programs/{program_id}/structured_scopes/{scope_id}
```

Scope attributes: `asset_identifier`, `asset_type`, `eligible_for_bounty`, `eligible_for_submission`, `max_severity`, `confidentiality_requirement`, `integrity_requirement`, `availability_requirement`, `instruction`.

## Weaknesses & CVEs

### Program Weaknesses
```
GET /v1/programs/{program_id}/weaknesses
```

CWE-mapped vulnerability types the program accepts.

### CVE Requests
```
GET  /v1/programs/{program_id}/cve_requests
POST /v1/programs/{program_id}/cve_requests
```

## Integrations & Triage

### Integrations
```
GET /v1/programs/{program_id}/integrations
```

### Triage Reviews
```
GET /v1/programs/{program_id}/triage_reviews
```

### Notify External Platform
```
POST /v1/programs/{program_id}/notify_external_platform
```

### Swag Management
```
GET /v1/programs/{program_id}/swag
PUT /v1/programs/{program_id}/swag
```

---

## Organizations

### Get Your Organizations
```
GET /v1/organizations
```

Or use `/v1/me/organizations` to get current user's org ID.

### Audit Log
```
GET /v1/organizations/{org_id}/audit_log
```

Supports filters and pagination.

### Get All Programs
```
GET /v1/organizations/{org_id}/programs
```

### Get All Inboxes
```
GET /v1/organizations/{org_id}/inboxes
```

### Eligibility Settings
```
GET /v1/organizations/{org_id}/eligibility_settings
PUT /v1/organizations/{org_id}/eligibility_settings
```

## Organization Members

### List Members
```
GET /v1/organizations/{org_id}/members
```

Returns all members with group access levels.

### Remove Member
```
DELETE /v1/organizations/{org_id}/members/{username}
```

### Update Member
```
PUT /v1/organizations/{org_id}/members/{username}
```

Update permissions and group assignments.

### Invitations
```
GET  /v1/organizations/{org_id}/invitations
POST /v1/organizations/{org_id}/invitations
```

Invite new members. Email validated against eligibility settings.

## Organization Groups

```
GET  /v1/organizations/{org_id}/groups
POST /v1/organizations/{org_id}/groups
PUT  /v1/organizations/{org_id}/groups/{group_id}
```

Groups have members, programs, and permissions (`reward_management`, `program_management`, `user_management`, `report_management`).

---

## Assets

### CRUD
```
GET    /v1/assets
POST   /v1/assets
PUT    /v1/assets/{asset_id}
DELETE /v1/assets/{asset_id}
```

### Get Organization ID

Required for asset operations:
```bash
curl "https://api.hackerone.com/v1/me/organizations" -u "$API_ID:$API_TOKEN"
```

### Bulk Import via CSV
```
POST /v1/assets/import
```

CSV columns: `identifier`, `asset_type`, `technologies`, `confidentiality_requirement`, `integrity_requirement`, `availability_requirement`, `description`, `reference`.

**Supported asset types:**
`Domain`, `Url`, `Cidr`, `Hardware`, `SourceCode`, `IosAppStore`, `IosTestflight`, `IosIpa`, `AndroidPlayStore`, `AndroidApk`, `WindowsMicrosoftStore`, `Executable`, `OtherAsset`

### Screenshots
```
POST /v1/assets/{asset_id}/screenshots
```

### Tags
```
GET  /v1/assets/tag_categories
POST /v1/assets/tag_categories
GET  /v1/assets/tags
POST /v1/assets/tags
```

### Ports
```
GET    /v1/assets/{asset_id}/ports
POST   /v1/assets/{asset_id}/ports
DELETE /v1/assets/{asset_id}/ports/{port_id}
```

### Reachability
```
GET  /v1/assets/{asset_id}/reachability
POST /v1/assets/{asset_id}/check_reachability
```

### Scanner Configuration
```
GET /v1/assets/{asset_id}/scanner_configuration
PUT /v1/assets/{asset_id}/scanner_configuration
```

### Asset Scopes
```
POST   /v1/assets/{asset_id}/scopes
PUT    /v1/assets/{asset_id}/scopes/{scope_id}
DELETE /v1/assets/{asset_id}/scopes/{scope_id}
```

---

## Automations

### CRUD
```
GET  /v1/automations
POST /v1/automations
PUT  /v1/automations/{automation_id}
```

### Runs & Logs
```
GET /v1/automations/{automation_id}/runs
GET /v1/automations/{automation_id}/runs/{run_id}/logs
```

### Trigger Automation
```
POST /v1/automations/{automation_id}/trigger
```

---

## Users

### Get Current User
```
GET /v1/user
```

### Get User by ID
```
GET /v1/users/{user_id}
```

Verify hacker participation in private programs using this endpoint.
