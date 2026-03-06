# Vercel: Security
Based on Vercel documentation.

## Architecture: Request Protection Layers

Every incoming request passes through these layers in order:

1. **Platform-wide firewall** — automatic DDoS mitigation (L3/L4/L7), free on all plans, no config needed
2. **Deployment protection** — access control (Vercel Auth, password, Trusted IPs) at the project level
3. **WAF custom rules** — user-defined rules evaluated in configured order
4. **WAF managed rulesets** — OWASP core rules, bot protection, AI bot blocking (Enterprise)

If a persistent action blocks a request, the source IP is stored at the platform firewall level so future requests are blocked before reaching the WAF.

---

## DDoS Mitigation

Automatic for all plans. Vercel does not charge for traffic blocked by DDoS mitigation.

**How it works:**
- Continuous traffic monitoring with hundreds of signals and detection factors
- Malicious traffic blocked or challenged automatically
- Resources scale dynamically during attacks
- Covers L3 (network), L4 (transport/SYN floods), and L7 (application/HTTP floods)

**During an active attack:**
1. Enable **Attack Challenge Mode** (free, all plans) — challenges all visitors
2. Add **IP Blocking** rules for known bad IPs
3. Add **Custom Rules** to deny/challenge specific traffic patterns
4. Use Middleware for geolocation blocking or rate limiting

**Bypass system mitigations** (temporarily, 24h max):
- Useful when DDoS protection blocks trusted proxies/shared networks (e.g., Black Friday traffic)
- Dashboard: Firewall tab > ellipsis menu > Pause System Mitigations
- For permanent granular bypass, use **System Bypass Rules** (Pro/Enterprise)

**Enterprise:** Dedicated DDoS support with direct communication from CSMs.

---

## Vercel WAF

Customizable per-project. Configuration changes propagate globally within **300ms** and support instant rollback to prior versions via the audit log.

### Rule Execution Order

1. DDoS mitigation rules
2. IP blocking rules
3. Custom rules (user-ordered)
4. Managed rulesets

### Actions

| Action | Behavior | Usage billing |
|--------|----------|---------------|
| **Log** | Request proceeds; logged for analysis | Normal usage |
| **Deny** | Returns `403 Forbidden`; request never reaches app | Edge request + ingress only |
| **Challenge** | JS challenge verifies real browser; session valid 1h | Free if blocked |
| **Bypass** | Skips subsequent firewall/managed rules | Normal usage |

**Challenge details:**
- Visitor sees "Vercel Security Checkpoint" (localized, respects color scheme)
- Session valid for 1 hour, tied to the browser
- Subrequests (API calls) within a valid session succeed automatically
- Direct API calls from scripts/cURL/Postman **will fail** if challenge is required
- For legitimate automation, use Bypass rules

### Plan Limits

| Feature | Hobby | Pro | Enterprise |
|---------|-------|-----|------------|
| Project IP blocks | 10 | 100 | Custom |
| Account IP blocks | N/A | N/A | Custom |
| Custom rules | 3 | 40 | 1,000 |
| Managed rulesets | N/A | N/A | Yes |

---

## WAF Custom Rules

### Creating Rules

1. Dashboard > Project > Firewall > Configure > Add New Rule
2. Name the rule descriptively
3. Add **If** conditions (combine with AND/OR)
4. Set **Then** action (Log, Deny, Challenge, Bypass, Redirect, Rate Limit)
5. Save Rule > Review Changes > Publish

**Best practice workflow:**
1. Start with **Log** action
2. Monitor live traffic for ~10 minutes
3. Verify behavior matches intent
4. Update to **Deny**, **Challenge**, or **Bypass**

### Persistent Actions

Add a time-based block to Challenge or Deny actions. When triggered:
- The client's IP is blocked at the platform firewall level for the specified duration
- Subsequent requests are blocked **before** firewall processing (no CDN/traffic usage incurred)
- Configure via the **for** dropdown when setting a rule action (default: 1 minute)

### Configuration in vercel.json

```json
{
  "routes": [
    {
      "src": "/(.*)",
      "has": [
        { "type": "header", "key": "x-suspicious-header" }
      ],
      "mitigate": {
        "action": "deny"
      }
    }
  ]
}
```

Only `challenge` and `deny` actions are supported in `vercel.json` (not log, bypass, or redirect).

---

## IP Blocking

### Project-Level

1. Firewall > Configure > IP Blocking > + Add IP
2. Enter IP address or CIDR range
3. Specify **Host** (exact domain match, e.g., `www.my-site.com`)
4. Add separate entries for each subdomain
5. Publish changes

### Account-Level (Enterprise)

Team Settings > Security > IP Blocking > Create New Rule. Same host rules apply.
CIDR limits: `/16` for IPv4, `/48` for IPv6.

For geo-blocking or regulation-based blocking, use Custom Rules instead of IP blocking.

---

## Managed Rulesets (Enterprise)

### OWASP Core Ruleset

Predefined rules based on OWASP Top Ten. Enable per-rule with Log or Deny action.
**Always start with Log** to monitor before enforcing.

### Bot Protection

Challenges traffic unlikely to be a real browser. Actions: Log or Challenge.

### AI Bots Ruleset

Blocks or logs traffic identified as AI crawlers. Actions: Log or Deny.

### Bypassing Rulesets

Create a Custom Rule with **Bypass** action targeting the traffic you want to allow. Place bypass rules **above** blocking rules in the custom rules list (rules execute top-to-bottom, custom rules run before managed rulesets).

---

## Attack Challenge Mode

Emergency security feature — challenges **all** visitors with a JS verification.

- **Free on all plans**, blocked requests incur zero cost
- Known bots (search engines, webhook providers) are automatically allowed through
- Internal requests (Functions, Cron Jobs, same-account projects) pass without challenge
- SEO is not affected — crawlers like Googlebot are allowlisted
- Can be kept enabled for extended periods safely

**Enable:** Dashboard > Project > Firewall > Bot Management > Attack Challenge Mode > Enable

**Limitations:** Standalone APIs and non-browser automated services may be blocked. Use Custom Rules for granular control.

---

## TLS Fingerprinting (JA3/JA4)

Vercel uses TLS fingerprints to identify malicious traffic patterns that share the same TLS handshake characteristics across multiple IPs/user agents.

**Request headers available in Functions:**
- `x-vercel-ja4-digest` (preferred) — JA4 fingerprint hash
- `x-vercel-ja3-digest` — JA3 fingerprint hash (legacy)

Monitor JA4 signatures in the WAF traffic view grouped by "JA4 Digest".

---

## Deployment Protection

Controls who can access preview and production URLs. Configured per-project.

### Protection Methods

| Method | Plans | How it works |
|--------|-------|-------------|
| **Vercel Authentication** | All | Requires Vercel account with team/project access |
| **Password Protection** | Enterprise, or Pro + $150/mo add-on | Single shared password per project |
| **Trusted IPs** | Enterprise | Allowlist of IPv4 addresses/CIDR ranges; returns 404 for others |

### Protection Scope

| Scope | Plans | What it protects |
|-------|-------|-----------------|
| **Standard Protection** | All | All URLs except production domains |
| **All Deployments** | Pro, Enterprise | Everything including production domains |
| **Only Production** | Enterprise | Production only (via Trusted IPs) |

### Bypassing Deployment Protection

| Method | Use case |
|--------|----------|
| **Shareable Links** | External access to specific branch deployments via secure query param |
| **Protection Bypass for Automation** | E2E tests, webhooks; header `x-vercel-protection-bypass: <secret>` or query param |
| **Deployment Protection Exceptions** | Exempt specific preview domains from all protection |
| **OPTIONS Allowlist** | Allow CORS preflight requests on specified paths |

**Automation bypass secret:**
```
# As header (recommended for test tools)
x-vercel-protection-bypass: <VERCEL_AUTOMATION_BYPASS_SECRET>

# As query parameter (for webhooks)
?x-vercel-protection-bypass=<secret>
```

### Vercel Authentication Details

- Token is scoped to a single URL (not transferable between URLs)
- Disabling protection makes all deployments unprotected immediately
- Re-enabling preserves sessions for previously authenticated users
- Hobby plan: 1 external user per account

### Configuring via API

```json
// Enable Vercel Authentication
{
  "ssoProtection": {
    "deploymentType": "prod_deployment_urls_and_all_previews"
  }
}

// Enable Password Protection
{
  "passwordProtection": {
    "deploymentType": "all",
    "password": "<password>"
  }
}

// Disable either
{ "ssoProtection": null }
{ "passwordProtection": null }
```

`deploymentType` values: `prod_deployment_urls_and_all_previews` | `all` | `preview`

---

## Encryption & TLS

All deployments served over HTTPS. HTTP requests redirected with `308 Moved Permanently`. Cannot be disabled.

| Feature | Details |
|---------|---------|
| TLS versions | 1.2 and 1.3 |
| Ciphers | AES-128-GCM, AES-256-GCM, CHACHA20-POLY1305 (all with forward secrecy) |
| Post-quantum | X25519MLKEM768 (Chrome 131+, Firefox 132+, Safari 26+) |
| OCSP stapling | Enabled (improves TTFB for first-time visitors) |
| Session resumption | Session Identifiers + Session Tickets (improves TTFB for returning visitors) |
| Data at rest | AES-256 encryption |
| Data in transit | HTTPS/TLS 1.3 |
| Certificates | Auto-generated via LetsEncrypt, wildcard for `.vercel.app` |
| Custom certs | Keys encrypted at rest in database, cached in memory for performance |

### HSTS

```
# .vercel.app (preloaded)
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload;

# Custom domains
Strict-Transport-Security: max-age=63072000;
```

Customizable via response headers configuration. Submit to [hstspreload.org](https://hstspreload.org/) for browser preload list inclusion.

---

## Security Headers

Configure in `vercel.json` or `next.config.js` headers config.

### Content-Security-Policy (CSP)

```
Content-Security-Policy: default-src 'self'; script-src 'self' cdn.example.com; img-src 'self' img.example.com; style-src 'self';
```

**CSP best practices:**
1. Start with `Content-Security-Policy-Report-Only` to monitor violations without blocking
2. Avoid `unsafe-inline` and `unsafe-eval` — use nonces or hashes instead
3. Be specific with sources (avoid wildcard `*` and broad `.domain.com`)
4. Update directives as your dependencies change
5. Test across multiple browsers

**CSP protects against:** XSS (inline script injection, unauthorized script sources), clickjacking, data injection, plugin exploits.

### Recommended Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | Force HTTPS |
| `Content-Security-Policy` | Project-specific allowlist | Prevent XSS/injection |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer data |
| `Permissions-Policy` | Restrict features as needed | Control browser features |

---

## Firewall Observability

### Overview Page (per project)

- Line graph of total incoming traffic (last hour, last 24h, or live 10-min window)
- **Alerts** section: detected attacks and DDoS events
- **Rules** section: traffic breakdown by matched rule
- **Events** section: platform firewall actions with expandable request details
- **Denied IPs** section: most commonly blocked sources

### Traffic Page

Filter by rule, action, or group by:
- Client IP, User Agent, Request Path, ASN, JA4 digest, Country

### DDoS Attack Alerts

Triggered when malicious traffic exceeds **100,000 requests in 10 minutes**.

**Notification methods:**
- Webhook: subscribe to "Attack Detected Firewall Event"
- Slack: `/vercel subscribe {team_id} firewall_attack`

### Log Drains

Send firewall logs to your SIEM via Log Drains for long-term retention and analysis.

---

## Compliance & Certifications

| Framework | Status |
|-----------|--------|
| **SOC 2 Type 2** | Attested (Security, Confidentiality, Availability) |
| **ISO 27001:2022** | Certified |
| **GDPR** | Supported; EU SCCs for data transfers |
| **PCI DSS v4.0** | SAQ-D (service provider) + SAQ-A (merchant) AOC available |
| **HIPAA** | Supported as business associate; BAA available for Enterprise |
| **EU-U.S. Data Privacy Framework** | Certified |
| **TISAX AL2** | Assessed (automotive industry) |

Documentation available at [security.vercel.com](https://security.vercel.com/).

---

## Shared Responsibility Model

### Vercel Manages

- Infrastructure security and availability (20 regions, Anycast network)
- Compute isolation (Functions, containers)
- Storage encryption and access controls
- Network security and monitoring
- SSL/TLS certificates and encryption in transit
- DDoS mitigation
- Platform authentication
- Data backups (every 2h, retained 30 days, globally replicated)
- Penetration testing and daily code review

### Customer Manages

- Application code security and source code storage
- Server-side data encryption
- Client-side data security
- Identity and access management (IAM) for their app
- Region selection for compute resources
- Spend management configuration
- Security requirements assessment
- Payment processing (PCI DSS: use iframe with payment gateway)
- Environment variables and secrets management

### Shared

- **Data ownership:** Customer controls access; Vercel protects data once received
- **Encryption:** Vercel handles transit/rest for its services; customer secures third-party integrations
- **Authentication:** Customer handles app auth; Vercel handles platform auth and deployment protection
- **Log management:** Vercel provides short-term runtime logs; customer sets up log drains for retention

---

## Common Pitfalls

1. **Using `VERCEL_URL` for fetch requests with Standard Protection** — protected deployment URLs will fail. Use relative paths for client-side requests or forward the incoming request origin for server-side requests.

2. **Expecting API routes to work with Challenge mode** — direct API calls from scripts/cURL cannot solve JS challenges. Use Bypass rules for legitimate automation.

3. **Not testing WAF rules with Log first** — deploying Deny rules without monitoring can block legitimate traffic. Always start with Log.

4. **Forgetting subdomain entries in IP blocking** — each subdomain (`www.`, `blog.`, `docs.`) needs a separate IP block entry.

5. **Disabling Vercel Authentication temporarily** — all deployments become immediately unprotected. Re-enabling does not force re-authentication for users with existing cookies.

6. **Ignoring persistent action costs** — persistent actions block at the platform level (free), but the initial triggering request still incurs edge usage.

7. **Over-permissive CSP** — using `unsafe-inline`, `unsafe-eval`, or `*` undermines CSP protection entirely. Use nonces/hashes instead.

8. **Not setting up firewall alerts** — without webhook or Slack notifications, you may not know about attacks until users report issues.

---

## Infrastructure Notes

- Primary provider: AWS with 20 regions and Anycast network
- Enterprise teams have isolated build infrastructure
- Multi-AZ redundancy for Functions by default
- AWS Global Accelerator for automatic regional failover
- Core database: globally replicated with rapid manual failover
- Regular resiliency testing simulating regional failures
