# Vercel: Domains & DNS
Based on Vercel documentation.

## Core Concepts

### How DNS Resolution Works

1. Browser checks local DNS cache for domain's IP address
2. If not cached, queries a **recursive resolver** (usually from ISP)
3. Resolver queries **root nameserver** -> **TLD nameserver** -> **authoritative nameserver**
4. Authoritative nameserver returns the A record (IP mapping)
5. Browser makes HTTP request to that IP

Vercel uses **anycast** IP addresses shared across all regions. Users are routed to the closest CDN region via BGP, regardless of where the IP geographically resolves.

### DNS Record Types

| Type | Purpose | Usage on Vercel |
|------|---------|-----------------|
| A | Maps domain to IPv4 address | Apex domains -> `76.76.21.21` |
| AAAA | Maps domain to IPv6 address | **Not supported** by Vercel |
| CNAME | Alias to another domain | Subdomains -> unique `*.vercel-dns-*.com` value |
| ALIAS | Like CNAME but at zone apex | Alternative for apex domains (provider-dependent) |
| CAA | Specifies allowed certificate authorities | Must include `0 issue "letsencrypt.org"` if other CAA records exist |
| HTTPS | CNAME-like at zone apex, with protocol info | Newer record type, not universally supported |
| MX | Mail server records | Required for email (Vercel has no mail service) |
| NS | Authoritative nameserver | Set at registrar level |
| TXT | Text information / verification | Used for domain ownership verification |
| SRV | Service location | Priority, weight, port, target |

### Vercel Nameservers

```
ns1.vercel-dns.com
ns2.vercel-dns.com
```

**Benefits of using Vercel nameservers:**
- Automatic DNS records for apex and first-level subdomains (no manual A/CNAME needed)
- Wildcard domain support (required for wildcards)
- Custom nameserver delegation from dashboard
- Automatic SSL certificate management via DNS-01 challenge

### Domain Types

| Type | Example | DNS Record | Notes |
|------|---------|------------|-------|
| Apex | `example.com` | A record | Cannot use CNAME at zone apex (RFC 1034) |
| Subdomain | `blog.example.com` | CNAME record | Each project gets a unique CNAME target |
| Wildcard | `*.example.com` | Nameservers method only | Requires Vercel nameservers for SSL cert generation |

### SSL Certificates

- Vercel auto-generates SSL via **Let's Encrypt** for every domain added to a project
- **Non-wildcard domains**: HTTP-01 challenge (automatic if DNS points to Vercel)
- **Wildcard domains**: DNS-01 challenge (requires Vercel nameservers)
- The `/.well-known` path is reserved and cannot be redirected or rewritten
- Custom SSL certificates: Enterprise plans only

**Certificate issuance flow:**
1. Vercel requests cert from Let's Encrypt
2. Let's Encrypt issues a challenge (HTTP-01 or DNS-01)
3. Vercel solves the challenge automatically
4. Let's Encrypt verifies and issues the certificate
5. Vercel installs it on infrastructure

## How-To Patterns

### Adding a Custom Domain

1. Go to **Project Settings > Domains**
2. Click **Add Domain**, enter your domain
3. Configure DNS based on domain type:
   - **Apex domain**: Add A record pointing to `76.76.21.21` at your registrar
   - **Subdomain**: Add CNAME record with the value shown in dashboard (e.g., `d1d4fc829fe7bc7c.vercel-dns-017.com`)
   - **Nameservers method**: Point NS records to `ns1.vercel-dns.com` and `ns2.vercel-dns.com`
4. Wait for DNS propagation and verification

When adding an apex domain, Vercel recommends also adding a `www` redirect.

### Adding a Wildcard Domain

1. Add `*.example.com` in Project Settings > Domains
2. Change nameservers at your registrar to Vercel's nameservers
3. Vercel handles DNS-01 challenge and certificate generation automatically

Wildcard domains **must** use the nameservers method -- no alternative.

### Buying a Domain Through Vercel

- Search at vercel.com/domains (pricing matches registrar, no search history logged)
- DNS and nameservers configured automatically -- no manual setup needed
- Renewals (domain + SSL) handled automatically
- Manage everything from team dashboard **Domains** tab

### Buying Through a Third-Party

- Use the "Add a custom domain" workflow to configure DNS records
- If using Vercel nameservers: manage DNS from Vercel dashboard
- If using external nameservers: manage DNS at your registrar
- You must migrate any existing DNS records to Vercel before switching nameservers

### Setting Up Email

Vercel **does not provide mail service**. You need a third-party email provider:
1. Choose a provider (e.g., ImprovMX, Forward Email, Google Workspace)
2. Add the required MX records to your DNS configuration
3. If using Vercel nameservers, add MX records in the Vercel dashboard

### Domain Verification (Cross-Account)

If a domain is used by another Vercel account:
1. Vercel prompts you to add a TXT record for verification
2. Add the TXT record at your DNS provider
3. Only one TXT verification record can be active at a time
4. This does **not** transfer domain ownership -- it grants usage rights

### Transferring a Domain to Vercel

- ICANN requires a **60-day wait** between transfers or after new registration
- Some registrars have additional transfer locks (check provider docs)
- Convert emoji domains to punycode (e.g., `jérémie.fr` -> `xn--jrmie-bsab.fr`)

## Best Practices

### DNS Migration Checklist

1. Audit existing DNS records and note current TTL values
2. **24 hours before migration**: Lower TTL to 60 seconds
3. Wait for old TTL to expire
4. Change DNS records to point to Vercel
5. Verify with `dig` commands or whatsmydns.net
6. Once confirmed working, optionally increase TTL

### Recommended Configuration

- **Use `www` subdomain as primary**, redirect apex to it:
  - `www` allows CNAME (faster DNS resolution on Vercel's anycast network)
  - Apex cookies/CAA records apply to all subdomains; `www` scopes them
- **Use Vercel nameservers when possible**: Automatic DNS, wildcard support, less manual config
- **Default TTL**: Vercel uses 60 seconds. Adjust based on update frequency:
  - Frequent changes: 30-60s (slower resolution)
  - Stable content: up to 86400s / 24h (faster loads, slower rollback)

### DNS Record Syntax

- **Name field**: Use only the prefix, not the full domain (`www`, not `www.example.com`)
- **CNAME value**: Copy exactly as shown, **including the trailing period** (`.`) -- it denotes a fully qualified domain name
- **A record for apex**: Always use the IP address provided in your Vercel dashboard

## Troubleshooting

### Quick Diagnostic Commands

```bash
# Check nameservers
dig ns example.com

# Check A record (apex)
dig a example.com

# Check CNAME (subdomain)
dig cname www.example.com

# Check CAA records
dig -t CAA +noall +ans example.com

# Check ACME challenge records (stale certs)
dig -t TXT _acme-challenge.example.com
```

**Online tools:**
- whatsmydns.net -- DNS propagation checker
- Let's Debug (letsdebug.net) -- SSL certificate diagnostics
- DNSViz (dnsviz.net) -- DNS behavior analysis
- Google Public DNS (dns.google) -- DNS record lookup

### Common Issues and Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Invalid Configuration alert | DNS records not set or not propagated | Add A/CNAME records per dashboard instructions; wait up to 48h |
| SSL certificate not generating | Missing CAA record | Add `0 issue "letsencrypt.org"` CAA record if other CAA records exist |
| SSL certificate not generating | Stale `_acme-challenge` TXT record | Remove old `_acme-challenge` records from previous provider |
| SSL not working for wildcard | Not using Vercel nameservers | Switch to nameservers method (required for wildcard SSL) |
| `/.well-known` path not working | Path is reserved by Vercel for challenges | Cannot redirect or rewrite; Enterprise can configure custom SSL |
| Domain used by another account | Domain linked to different Vercel team | Add TXT verification record, or transfer via Domains dashboard |
| Email stopped working | Switched to Vercel nameservers without MX records | Add MX records in Vercel DNS dashboard |
| DNS changes not visible | Propagation delay | Standard records: minutes to hours. Nameserver changes: up to 48h |
| IPv6 not working | Vercel does not support IPv6 | Use A records (IPv4) only; AAAA records cannot point to Vercel |
| Transfer-in failing | ICANN 60-day lock or registrar transfer lock | Wait 60 days; disable transfer lock at current registrar |

### Domain Ownership Errors

| Error | Meaning |
|-------|---------|
| "This team has already registered this domain" | Domain already connected to your current team |
| "You have already registered this domain" | Domain already on your personal account |
| "The domain is not available" / "Another Vercel account is using this domain" | Linked to another account -- verify ownership via TXT record or transfer |

### SSL Certificate Debugging

1. Check if domain points to Vercel: `dig a example.com` should return Vercel IP
2. Test with Let's Debug (letsdebug.net) for Let's Encrypt-specific issues
3. Check for conflicting CAA records: `dig -t CAA +noall +ans example.com`
4. Check for stale ACME challenges: `dig -t TXT _acme-challenge.example.com`
5. Ensure `/.well-known` path is not being redirected or rewritten
6. For wildcard domains, confirm nameservers are set to Vercel's

## Key Limits and Constraints

- **Hobby teams**: 50 custom domains per project
- **IPv6**: Not supported
- **Wildcard domains**: Nameservers method only
- **Custom SSL**: Enterprise plans only
- **Domain transfers**: 60-day ICANN wait period
- **`/.well-known` path**: Reserved, cannot be redirected
- **Email**: No mail service provided by Vercel
- **Domain purchases/renewals**: Non-refundable once processed
- **Pending purchases**: Some TLDs may take up to 5 days to finalize
