# Wrangler: Storage & Data Commands (KV, D1, R2, Queues)
Based on Wrangler documentation from developers.cloudflare.com.

## When to Use What

| Service | Model | Best For | Latency | Max Size |
|---------|-------|----------|---------|----------|
| **KV** | Key-value (eventually consistent) | Config, feature flags, cached content, session data | Low reads, slower writes | 25 MB/value |
| **D1** | SQLite (relational) | Structured data, queries with joins, CRUD apps | Low | 10 GB/db |
| **R2** | Object storage (S3-compatible) | Files, images, videos, backups, static assets | Varies | 5 TB/object |
| **Queues** | Message queue | Async processing, event-driven workflows, batching | N/A | 128 KB/message |

**Decision guide:**
- Need fast key lookups? **KV**
- Need SQL queries or relational data? **D1**
- Need to store files or large blobs? **R2**
- Need to decouple producers from consumers? **Queues**
- Need R2 change notifications? **R2 notifications + Queues** (they work together)

---

## KV (Key-Value Store)

### Core Concepts
KV is a globally distributed, eventually consistent key-value store. Reads are fast everywhere; writes propagate globally within ~60 seconds. Ideal for read-heavy workloads.

### Namespace Management

```bash
# Create a namespace (outputs ID for wrangler config)
wrangler kv namespace create MY_KV

# List all namespaces on your account
wrangler kv namespace list

# Delete a namespace
wrangler kv namespace delete --namespace-id <ID>

# Rename a namespace
wrangler kv namespace rename MY_KV --new-name NEW_NAME
```

### Reading & Writing Keys

```bash
# Write a value
wrangler kv key put --binding MY_KV "user:123" '{"name":"Alice"}'

# Write from a file (binary-safe)
wrangler kv key put --binding MY_KV "image.png" --path ./image.png

# Write with TTL (seconds) or expiration (unix timestamp)
wrangler kv key put --binding MY_KV "session:abc" "data" --ttl 3600
wrangler kv key put --binding MY_KV "temp" "data" --expiration 1700000000

# Write with metadata
wrangler kv key put --binding MY_KV "doc:1" "content" --metadata '{"version":2}'

# Read a value (returns raw bytes by default)
wrangler kv key get --binding MY_KV "user:123" --text

# List keys (optionally filtered by prefix)
wrangler kv key list --binding MY_KV --prefix "user:"

# Delete a key
wrangler kv key delete --binding MY_KV "user:123"
```

### Bulk Operations

```bash
# Bulk put from JSON file (array of {key, value, expiration?, metadata?})
wrangler kv bulk put --binding MY_KV data.json

# Bulk delete from JSON file (array of key strings)
wrangler kv bulk delete --binding MY_KV keys.json --force

# Bulk get from JSON file
wrangler kv bulk get --binding MY_KV keys.json
```

**Bulk put JSON format:**
```json
[
  {"key": "user:1", "value": "{\"name\":\"Alice\"}", "expiration": 1700000000},
  {"key": "user:2", "value": "{\"name\":\"Bob\"}", "metadata": {"role": "admin"}}
]
```

### KV Pitfalls

- **Eventually consistent**: Writes may take up to 60s to propagate globally. Do not use KV for data that requires immediate read-after-write consistency.
- **`--text` flag for reads**: Without `--text`, `kv key get` returns raw bytes. Always use `--text` for string values.
- **Preview vs production**: Use `--preview` flag to target preview namespaces during development. Easy to accidentally write to production.
- **Namespace ID vs binding**: CLI commands accept either `--binding` (requires wrangler config) or `--namespace-id` (works standalone). Use `--namespace-id` in CI scripts.

---

## D1 (SQLite Database)

### Core Concepts
D1 is Cloudflare's serverless SQLite database. It runs at the edge, supports standard SQL, has built-in migrations, time-travel (point-in-time restore), and automatic backups.

### Database Lifecycle

```bash
# Create a database (outputs binding config for wrangler.toml/jsonc)
wrangler d1 create my-app-db

# Create with location hint and jurisdiction
wrangler d1 create my-app-db --location wnam --jurisdiction eu

# List all databases
wrangler d1 list --json

# Get database info (size, state, etc.)
wrangler d1 info my-app-db --json

# Delete a database
wrangler d1 delete my-app-db --skip-confirmation
```

**Location hints:** `wnam` (Western North America), `enam` (Eastern NA), `weur` (Western Europe), `eeur` (Eastern Europe), `apac` (Asia Pacific), `oc` (Oceania).

### Executing SQL

```bash
# Run a single query against remote
wrangler d1 execute my-app-db --remote --command "SELECT * FROM users LIMIT 10"

# Run multiple statements (semicolon-separated)
wrangler d1 execute my-app-db --remote --command "INSERT INTO users (name) VALUES ('Alice'); SELECT * FROM users;"

# Run from SQL file
wrangler d1 execute my-app-db --remote --file ./seed.sql

# Run against local dev database
wrangler d1 execute my-app-db --local --command "SELECT * FROM users"

# Output as JSON (useful for scripting)
wrangler d1 execute my-app-db --remote --command "SELECT * FROM users" --json
```

### Migrations

```bash
# Create a migration file (goes to ./migrations/0001_create_users.sql)
wrangler d1 migrations create my-app-db "create_users"

# List unapplied migrations
wrangler d1 migrations list my-app-db --remote

# Apply pending migrations to remote (prompts for confirmation)
wrangler d1 migrations apply my-app-db --remote

# Apply to local dev database
wrangler d1 migrations apply my-app-db --local
```

### Time Travel & Export

```bash
# Check available restore points
wrangler d1 time-travel info my-app-db --json

# Restore to a timestamp (within last 30 days)
wrangler d1 time-travel restore my-app-db --timestamp "2025-01-15T10:00:00Z"

# Restore using a bookmark
wrangler d1 time-travel restore my-app-db --bookmark <bookmark-id>

# Export full database
wrangler d1 export my-app-db --remote --output backup.sql

# Export schema only
wrangler d1 export my-app-db --remote --output schema.sql --no-data

# Export specific tables, data only
wrangler d1 export my-app-db --remote --output users.sql --table users --no-schema
```

### Query Insights

```bash
# Show top 5 slowest queries (last 24h)
wrangler d1 insights my-app-db --sort-by time --sort-type sum --sort-direction DESC

# Show query insights as JSON
wrangler d1 insights my-app-db --json --limit 10 --time-period 7d
```

### D1 Pitfalls

- **`--local` vs `--remote`**: You MUST specify one. Forgetting `--remote` when targeting production is a common mistake. Local is for `wrangler dev` only.
- **Migration rollback**: If a migration fails, D1 automatically rolls it back. But successful migrations are not reversible via the tool -- use time-travel restore instead.
- **Time travel limit**: Restore points are only available for the last 30 days.
- **CI/CD**: Confirmation prompts are automatically skipped in non-interactive environments. Use `--yes` to be explicit.
- **Jurisdiction lock-in**: Once set, a database's jurisdiction cannot be changed. Plan data residency requirements upfront.

---

## R2 (Object Storage)

### Core Concepts
R2 is S3-compatible object storage with zero egress fees. Use it for files, media, backups, and any blob storage. Objects are addressed as `{bucket}/{key}`.

### Bucket Management

```bash
# Create a bucket
wrangler r2 bucket create my-bucket

# Create with location and storage class
wrangler r2 bucket create my-bucket --location wnam --storage-class InfrequentAccess

# Create in a specific jurisdiction
wrangler r2 bucket create my-bucket --jurisdiction eu

# List all buckets
wrangler r2 bucket list

# Get bucket info
wrangler r2 bucket info my-bucket --json

# Delete a bucket (must be empty)
wrangler r2 bucket delete my-bucket
```

### Object Operations

```bash
# Upload a file
wrangler r2 object put my-bucket/images/photo.jpg --file ./photo.jpg \
  --content-type image/jpeg --cache-control "max-age=86400"

# Upload from stdin (pipe)
cat data.csv | wrangler r2 object put my-bucket/data.csv --pipe \
  --content-type text/csv

# Download a file
wrangler r2 object get my-bucket/images/photo.jpg --file ./downloaded.jpg

# Download to stdout
wrangler r2 object get my-bucket/data.csv --pipe > output.csv

# Delete an object
wrangler r2 object delete my-bucket/images/photo.jpg

# Upload with specific storage class
wrangler r2 object put my-bucket/archive/old.zip --file ./old.zip \
  --storage-class InfrequentAccess
```

### Public Access & Custom Domains

```bash
# Enable public r2.dev URL
wrangler r2 bucket dev-url enable my-bucket

# Check public access status
wrangler r2 bucket dev-url get my-bucket

# Disable public access
wrangler r2 bucket dev-url disable my-bucket --force

# Add a custom domain
wrangler r2 bucket domain add my-bucket --domain cdn.example.com --zone-id <zone-id>

# List custom domains
wrangler r2 bucket domain list my-bucket

# Remove custom domain
wrangler r2 bucket domain remove my-bucket --domain cdn.example.com
```

### CORS Configuration

```bash
# Set CORS rules from JSON file
wrangler r2 bucket cors set my-bucket --file cors.json

# List current CORS rules
wrangler r2 bucket cors list my-bucket

# Remove all CORS rules
wrangler r2 bucket cors delete my-bucket --force
```

### Lifecycle Rules

```bash
# Auto-delete objects after 90 days
wrangler r2 bucket lifecycle add my-bucket "cleanup" "logs/" --expire-days 90

# Transition to Infrequent Access after 30 days
wrangler r2 bucket lifecycle add my-bucket "archive" "data/" --ia-transition-days 30

# Abort incomplete multipart uploads after 7 days
wrangler r2 bucket lifecycle add my-bucket "abort-multipart" "" --abort-multipart-days 7

# List lifecycle rules
wrangler r2 bucket lifecycle list my-bucket

# Remove a rule
wrangler r2 bucket lifecycle remove my-bucket --name "cleanup"

# Set full lifecycle config from JSON
wrangler r2 bucket lifecycle set my-bucket --file lifecycle.json
```

### Event Notifications (R2 + Queues)

```bash
# Notify a queue when objects are created or deleted
wrangler r2 bucket notification create my-bucket \
  --queue my-queue \
  --event-types object-create --event-types object-delete \
  --prefix "uploads/" --suffix ".jpg"

# List notification rules
wrangler r2 bucket notification list my-bucket

# Delete a notification rule
wrangler r2 bucket notification delete my-bucket --queue my-queue --rule <rule-id>
```

### Sippy (Incremental Migration)

Sippy lets you migrate from AWS S3 or GCS to R2 incrementally -- objects are copied on first access.

```bash
# Enable Sippy from AWS S3
wrangler r2 bucket sippy enable my-bucket --provider AWS \
  --bucket source-bucket --region us-east-1 \
  --access-key-id <key> --secret-access-key <secret> \
  --r2-access-key-id <r2-key> --r2-secret-access-key <r2-secret>

# Check Sippy status
wrangler r2 bucket sippy get my-bucket

# Disable Sippy after migration
wrangler r2 bucket sippy disable my-bucket
```

### Bucket Locks (Retention)

```bash
# Lock objects for 365 days
wrangler r2 bucket lock add my-bucket "compliance" "records/" --retention-days 365

# Lock indefinitely
wrangler r2 bucket lock add my-bucket "legal-hold" "legal/" --retention-indefinite

# List lock rules
wrangler r2 bucket lock list my-bucket
```

### R2 Pitfalls

- **Object path format**: Always `bucket/key` -- e.g., `my-bucket/path/to/file.txt`. No leading slash on the key.
- **Bucket must be empty to delete**: You cannot delete a bucket with objects in it. Use lifecycle rules or a script to empty it first.
- **Jurisdiction is permanent**: Like D1, once set on a bucket, jurisdiction cannot be changed.
- **`--force` for destructive ops**: Enabling/disabling public access and deleting CORS rules require confirmation. Use `--force` / `-y` in automation.
- **Storage classes affect cost**: Use `InfrequentAccess` for rarely-accessed data to save money, but be aware of minimum storage duration charges.

---

## Queues (Message Queue)

### Core Concepts
Queues provide reliable, at-least-once message delivery between Workers. Producers send messages; consumers process them in batches. Supports both Worker-based and HTTP pull consumers.

### Queue Lifecycle

```bash
# Create a queue
wrangler queues create my-queue

# Create with delivery delay and retention
wrangler queues create my-queue \
  --delivery-delay-secs 30 \
  --message-retention-period-secs 86400

# List all queues
wrangler queues list

# Get queue info
wrangler queues info my-queue

# Update queue settings
wrangler queues update my-queue --delivery-delay-secs 60

# Delete a queue
wrangler queues delete my-queue
```

### Worker Consumers

```bash
# Attach a Worker consumer
wrangler queues consumer add my-queue my-consumer-worker \
  --batch-size 10 \
  --batch-timeout 5 \
  --message-retries 3 \
  --dead-letter-queue my-dlq \
  --max-concurrency 5 \
  --retry-delay-secs 10

# Remove a consumer
wrangler queues consumer remove my-queue my-consumer-worker
```

### HTTP Pull Consumers

```bash
# Create an HTTP pull consumer
wrangler queues consumer http add my-queue \
  --visibility-timeout-secs 30

# Remove HTTP consumer
wrangler queues consumer http remove my-queue
```

### Queue Operations

```bash
# Pause message delivery (consumers stop receiving)
wrangler queues pause-delivery my-queue

# Resume delivery
wrangler queues resume-delivery my-queue

# Purge all messages (irreversible!)
wrangler queues purge my-queue --force
```

### Event Subscriptions

```bash
# Subscribe to events (e.g., from Workers AI or Workflows)
wrangler queues subscription create my-queue \
  --source workers-ai \
  --events "model-inference" \
  --model-name "@cf/meta/llama-3-8b-instruct"

# List subscriptions
wrangler queues subscription list my-queue --json

# Delete a subscription
wrangler queues subscription delete my-queue --id <subscription-id> --force
```

### Queues Pitfalls

- **Retention limits by plan**: Free tier: 60s-86400s (1 day). Paid: 60s-1209600s (14 days). Messages beyond retention are lost.
- **At-least-once delivery**: Messages may be delivered more than once. Your consumer MUST be idempotent.
- **Dead letter queue**: Always configure a DLQ for production queues. Messages that exhaust retries go there instead of being lost.
- **Purge is irreversible**: `queues purge` cannot be undone. Always use `--force` deliberately.
- **Delivery delay max**: Maximum delivery delay is 86400 seconds (24 hours).

---

## Quick Reference: Common Operations

| Task | Command |
|------|---------|
| **KV: Write a key** | `wrangler kv key put --binding B "key" "value"` |
| **KV: Read a key** | `wrangler kv key get --binding B "key" --text` |
| **KV: Bulk import** | `wrangler kv bulk put --binding B data.json` |
| **D1: Run SQL** | `wrangler d1 execute DB --remote --command "SQL"` |
| **D1: Run migration** | `wrangler d1 migrations apply DB --remote` |
| **D1: Backup** | `wrangler d1 export DB --remote --output backup.sql` |
| **D1: Restore** | `wrangler d1 time-travel restore DB --timestamp T` |
| **R2: Upload file** | `wrangler r2 object put bucket/key --file ./f` |
| **R2: Download file** | `wrangler r2 object get bucket/key --file ./f` |
| **R2: Enable CDN** | `wrangler r2 bucket dev-url enable bucket` |
| **Queues: Create** | `wrangler queues create my-queue` |
| **Queues: Add consumer** | `wrangler queues consumer add Q worker-name` |
| **Queues: Purge** | `wrangler queues purge Q --force` |

## Global Flags (All Commands)

| Flag | Description |
|------|-------------|
| `--config` / `-c` | Path to wrangler config file |
| `--env` / `-e` | Target environment |
| `--cwd` | Run from specified directory |
| `--json` | Output as JSON (where supported) |
| `--experimental-provision` | Auto-provision resources (default: true) |

## Best Practices Summary

1. **Always specify `--remote` or `--local`** for D1 commands. Never rely on defaults in scripts.
2. **Use `--json` output** in CI/CD pipelines for reliable parsing.
3. **Set up DLQs** for every production queue. Failed messages need a safety net.
4. **Use lifecycle rules** on R2 to automatically clean up old objects and abort stale multipart uploads.
5. **Use bulk operations** for KV when writing more than a few keys. Individual puts are rate-limited.
6. **Use migrations, not raw execute** for D1 schema changes. Migrations are versioned and trackable.
7. **Use `--skip-confirmation`** / `--force` / `--yes` in CI/CD, but never in interactive use without thinking.
8. **Plan jurisdictions upfront** for both D1 and R2. They cannot be changed after creation.
9. **Design consumers to be idempotent** when using Queues. At-least-once delivery means duplicates happen.
10. **Connect R2 notifications to Queues** for event-driven file processing pipelines.
