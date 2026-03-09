# HackerOne API: Webhooks

Based on HackerOne API v1 documentation.

## Overview

Webhooks deliver real-time HTTP POST notifications when events occur on HackerOne. Use them to update external issue trackers, trigger notifications, backup data, or provision accounts.

## Webhook Events (40+)

### Report Events

| Event | Trigger |
|-------|---------|
| `report_created` | New report submitted |
| `report_triaged` | Report triaged |
| `report_resolved` | Report resolved |
| `report_reopened` | Report reopened |
| `report_needs_more_info` | More info requested |
| `report_bounty_awarded` | Bounty awarded |
| `report_bounty_suggested` | Bounty suggested |
| `report_swag_awarded` | Swag awarded |
| `report_not_eligible_for_bounty` | Marked ineligible |
| `report_closed_as_duplicate` | Closed as duplicate |
| `report_closed_as_spam` | Closed as spam |
| `report_closed_as_informative` | Closed as informative |
| `report_closed_as_not_applicable` | Closed as N/A |
| `report_comment_created` | New comment added |
| `report_comments_closed` | Comments closed |
| `report_agreed_on_going_public` | Disclosure agreed |
| `report_became_public` | Report disclosed |
| `report_manually_disclosed` | Manual disclosure |
| `report_undisclosed` | Disclosure reverted |
| `report_retesting` | Retest started |
| `report_retest_approved` | Retest approved |
| `report_retest_rejected` | Retest rejected |
| `report_retest_user_completed` | Retester finished |
| `report_retest_user_expired` | Retester timed out |
| `report_retest_user_left` | Retester left |
| `report_custom_field_value_updated` | Custom field changed |
| `report_prioritised` | Priority changed |
| `report_user_assigned` | User assigned |
| `report_group_assigned` | Group assigned |

### Program Events

| Event | Trigger | Note |
|-------|---------|------|
| `program_hacker_joined` | Hacker joined program | Private programs only |
| `program_hacker_left` | Hacker left program | Private programs only |

## Delivery Headers

Every webhook POST includes three headers:

| Header | Description |
|--------|-------------|
| `X-H1-Event` | Event name (e.g., `report_created`) |
| `X-H1-Delivery` | Unique GUID for this delivery |
| `X-H1-Signature` | HMAC-SHA256 signature of request body |

## Payload Structure

JSON payload containing:
- Activity data (type, ID, timestamps, actor)
- Report details (ID, title, state, vulnerability info, timestamps)
- Reporter relationships (user profile)
- Severity ratings with author info

```json
{
  "data": {
    "id": "12345",
    "type": "activity-bounty-awarded",
    "attributes": {
      "message": "Thanks for the report!",
      "bounty_amount": "500.00",
      "bonus_amount": "0.00",
      "created_at": "2024-03-15T10:30:00.000Z",
      "internal": false
    },
    "relationships": {
      "actor": { "data": { "id": "1", "type": "user" } },
      "report": { "data": { "id": "6789", "type": "report" } }
    }
  }
}
```

## Signature Validation

When you set a secret during webhook setup, HackerOne signs each payload with HMAC-SHA256. The signature format is `sha256={hexdigest}`.

**Always use constant-time comparison** to prevent timing attacks.

### Python

```python
import hmac

def validate_request(request, secret, signature):
    _, digest = signature.split('=')
    generated_digest = hmac.new(
        secret.encode(),
        request['body'].encode(),
        "sha256"
    ).hexdigest()
    return hmac.compare_digest(digest, generated_digest)
```

### Ruby

```ruby
def validate_request(body, secret, signature)
  _, digest = signature.split("=")
  generated_digest = OpenSSL::HMAC.hexdigest(
    OpenSSL::Digest.new("sha256"), secret, body
  )
  Rack::Utils.secure_compare(generated_digest, digest)
end
```

### JavaScript (Node.js)

```javascript
const http = require('http');
const crypto = require('crypto');

const secret = process.env.WEBHOOK_SECRET;

http.createServer((req, res) => {
  const sig = req.headers['x-h1-signature'].split('=')[1];
  const data = [];

  req.on('data', chunk => data.push(chunk));
  req.on('end', () => {
    const hash = crypto
      .createHmac('sha256', secret)
      .update(data[0])
      .digest('hex');
    const valid = crypto.timingSafeEqual(
      Buffer.from(sig),
      Buffer.from(hash)
    );
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ signature_valid: valid }));
  });
}).listen(7777);
```

## Key Implementation Notes

1. Signature always starts with `sha256=` regardless of language
2. **Always** use constant-time comparison (`hmac.compare_digest`, `timingSafeEqual`, `secure_compare`)
3. If no secret is set, signature is computed with empty string as key
4. Webhook setup is done through the HackerOne platform UI, not via API
5. Failed deliveries should be handled gracefully — implement idempotent handlers
6. The `X-H1-Delivery` GUID can be used for deduplication
