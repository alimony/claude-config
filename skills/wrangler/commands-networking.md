# Wrangler: Networking & Security Commands
Based on Wrangler documentation from developers.cloudflare.com.

## Overview

Four command groups for connecting Workers to private networks, managing certificates, and handling secrets:

| Command Group | Purpose |
|---|---|
| `wrangler certificates` | Upload mTLS and CA certificates for Worker auth and Hyperdrive |
| `wrangler tunnel` | Create and manage Cloudflare Tunnels to expose local/private services |
| `wrangler vpc` | Connect Workers to private services via VPC + Tunnel |
| `wrangler secrets-store` | Centralized secrets management with scoped access |

---

## Certificates

Two command families exist: `mtls-certificate` (for Worker subrequest auth) and `cert` (for Hyperdrive/database connections). Both manage uploaded certificate pairs.

### When to Use Which

| Command | Use Case |
|---|---|
| `mtls-certificate` | Worker-to-origin mTLS authentication via bindings |
| `cert upload mtls-certificate` | mTLS certs for Hyperdrive database connections |
| `cert upload certificate-authority` | CA certs for Hyperdrive to verify server identity |

### Upload an mTLS Certificate (Worker Bindings)

```bash
# Certificate and key must be separate .pem files
npx wrangler mtls-certificate upload --cert cert.pem --key key.pem --name my-origin-cert
```

The output returns a certificate ID, issuer, and expiration. Use the ID or name in your `wrangler.jsonc` bindings.

### Upload Certificates for Hyperdrive

```bash
# mTLS cert for database client auth
npx wrangler cert upload mtls-certificate --cert client.pem --key client-key.pem --name DB_CLIENT_CERT

# CA cert to verify the database server
npx wrangler cert upload certificate-authority --ca-cert server-ca-chain.pem --name SERVER_CA_CHAIN
```

### List and Delete

```bash
# List all mTLS certificates (Worker bindings)
npx wrangler mtls-certificate list

# List all certificates (Hyperdrive)
npx wrangler cert list

# Delete by ID or name
npx wrangler mtls-certificate delete --id 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d
npx wrangler cert delete --name SERVER_CA_CHAIN
```

### Best Practices

- Keep certificate and private key in **separate** `.pem` files.
- Always use `--name` for human-readable identification; IDs are UUIDs.
- Rotate certificates before expiration -- upload the new cert, update bindings, then delete the old one.

---

## Tunnels

Cloudflare Tunnels connect local or private services to Cloudflare's network. Wrangler wraps the `cloudflared` binary (auto-downloaded unless `CLOUDFLARED_PATH` is set).

> All tunnel commands are **experimental** and may change without notice.

### Create and Run a Tunnel

```bash
# Create a named, remotely-managed tunnel
npx wrangler tunnel create my-app

# Run it (connects your local service to Cloudflare)
npx wrangler tunnel run my-app

# Run with a token (e.g., in CI/CD)
npx wrangler tunnel run --token $TUNNEL_TOKEN
```

Tunnels created via Wrangler are **always remotely managed** -- configure routing in the Cloudflare dashboard or via API.

### Quick Tunnel (Zero Config)

```bash
# Instant public URL for a local service, no account needed
npx wrangler tunnel quick-start http://localhost:8080
```

Creates a temporary `*.trycloudflare.com` subdomain. Ideal for demos and testing. These tunnels are anonymous and do not appear in your account.

### Inspect and Clean Up

```bash
# List all tunnels
npx wrangler tunnel list

# Get tunnel details (accepts name or UUID)
npx wrangler tunnel info my-app

# Delete a tunnel (permanent, cannot be undone)
npx wrangler tunnel delete my-app
npx wrangler tunnel delete f70ff985-a4ef-4643-bbbc-4a0ed4fc8415 --force
```

### Debugging

```bash
# Adjust log verbosity: debug | info | warn | error | fatal
npx wrangler tunnel run my-app --log-level debug
```

### Best Practices

- Pass tokens via the `TUNNEL_TOKEN` env var rather than CLI arguments to avoid leaking in logs.
- Set `CLOUDFLARED_PATH` in CI to use a pre-installed `cloudflared` and skip auto-download.
- Use named tunnels (not quick tunnels) for anything beyond local testing.

---

## VPC Services

VPC services connect Workers to private services on your network **through Cloudflare Tunnels**. The flow is: Worker --> VPC Service --> Tunnel --> Your private network.

### Create a VPC Service

```bash
# Route to a private service by IP
npx wrangler vpc service create my-api \
  --type http \
  --tunnel-id f70ff985-a4ef-4643-bbbc-4a0ed4fc8415 \
  --ipv4 10.0.1.50 \
  --http-port 8080

# Route to a private service by hostname (uses resolver)
npx wrangler vpc service create my-dns-service \
  --type http \
  --tunnel-id f70ff985-a4ef-4643-bbbc-4a0ed4fc8415 \
  --hostname internal-api.corp.local \
  --resolver-ips 10.0.0.2,10.0.0.3
```

**Required flags:** `--type`, `--tunnel-id`
**Address flags (pick one):** `--ipv4`, `--ipv6`, or `--hostname` (with `--resolver-ips`)
**Port defaults:** HTTP=80, HTTPS=443

### CRUD Operations

```bash
# List all VPC services
npx wrangler vpc service list

# Get details for a specific service
npx wrangler vpc service get <SERVICE-ID>

# Update a service (same flags as create)
npx wrangler vpc service update <SERVICE-ID> \
  --name new-name \
  --http-port 9090

# Delete a service
npx wrangler vpc service delete <SERVICE-ID>
```

### Best Practices

- Create the Tunnel first (`wrangler tunnel create`), then reference its UUID in `--tunnel-id`.
- Use `--ipv4`/`--ipv6` for stable endpoints; use `--hostname` + `--resolver-ips` for DNS-based discovery.
- `--ipv4` and `--ipv6` conflict with each other -- pick one per service.

---

## Secrets Store

Centralized secrets management for Workers. Secrets are scoped (e.g., `workers`) and accessed via store bindings.

> Secrets Store is in **open beta**. Currently limited to **one store per Cloudflare account**.

### The `--remote` Flag

Almost every secrets-store command defaults to **local development mode**. Add `--remote` to interact with the production Secrets Store.

### Store Lifecycle

```bash
# Create a store
npx wrangler secrets-store store create default --remote

# List stores (paginated)
npx wrangler secrets-store store list --remote --per-page 25

# Delete a store
npx wrangler secrets-store store delete <STORE-ID> --remote
```

### Managing Secrets

```bash
# Create a secret (prompted for value securely)
npx wrangler secrets-store secret create <STORE-ID> \
  --name API_KEY \
  --scopes workers \
  --comment "Third-party API key" \
  --remote

# List secrets in a store
npx wrangler secrets-store secret list <STORE-ID> --remote

# Get secret metadata
npx wrangler secrets-store secret get <STORE-ID> --secret-id <SECRET-ID> --remote

# Update a secret's value (prompted securely)
npx wrangler secrets-store secret update <STORE-ID> \
  --secret-id <SECRET-ID> \
  --scopes workers \
  --remote

# Duplicate a secret (copies value to a new name)
npx wrangler secrets-store secret duplicate <STORE-ID> \
  --secret-id <SECRET-ID> \
  --name API_KEY_STAGING \
  --scopes workers \
  --remote

# Delete a secret
npx wrangler secrets-store secret delete <STORE-ID> \
  --secret-id <SECRET-ID> \
  --remote
```

### Pagination

Both `store list` and `secret list` support `--page` (default: 1) and `--per-page` (default: 10).

### Best Practices

- **Never use `--value` in production.** It leaves the secret in plaintext in terminal history. Omit it and use the secure interactive prompt instead.
- Always pass `--remote` when working with real secrets; without it you're only modifying local dev state.
- Use `--scopes workers` to make secrets available to Workers (currently the primary scope).
- Use `--comment` to document what a secret is for -- you'll thank yourself during rotation.
- Use `duplicate` to create environment-specific copies (staging, production) from the same value.

---

## How These Connect Together

A typical private-service integration follows this pattern:

```
1. Upload certs      -->  wrangler cert upload / mtls-certificate upload
2. Create tunnel     -->  wrangler tunnel create my-tunnel
3. Run tunnel        -->  wrangler tunnel run my-tunnel (on your private network)
4. Create VPC svc    -->  wrangler vpc service create --tunnel-id <TUNNEL-UUID>
5. Store credentials -->  wrangler secrets-store secret create <STORE-ID> --name DB_PASS
6. Bind in Worker    -->  Reference VPC service + secrets in wrangler.jsonc
```

### Deployment Checklist

| Step | Command | Verify With |
|---|---|---|
| Tunnel exists | `tunnel create` | `tunnel list` |
| Tunnel running | `tunnel run` | `tunnel info` |
| VPC service configured | `vpc service create` | `vpc service get <ID>` |
| Certificates uploaded | `cert upload` / `mtls-certificate upload` | `cert list` / `mtls-certificate list` |
| Secrets stored | `secrets-store secret create` | `secrets-store secret list <STORE-ID>` |

---

## Quick Reference: Common Flags

These flags work across all four command groups:

| Flag | Short | Description |
|---|---|---|
| `--config` | `-c` | Path to wrangler config file |
| `--env` | `-e` | Environment to use |
| `--cwd` | | Run from a different directory |
| `--env-file` | | Load `.env` file (repeatable) |
| `--experimental-provision` | `-x-provision` | Auto-provision resources (default: true) |
