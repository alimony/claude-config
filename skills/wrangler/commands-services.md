# Wrangler: Platform Service Commands
Based on Wrangler documentation from developers.cloudflare.com.

This reference covers the platform service commands that extend Workers: Pages, Hyperdrive, Vectorize, Pipelines, Containers, Workflows, and Workers for Platforms (dispatch namespaces).

---

## Pages

Cloudflare Pages is a full-stack deployment platform for static sites and serverless functions. Use `wrangler pages` to manage projects, deployments, secrets, and local development.

### Project Lifecycle

```bash
# Create a new Pages project
wrangler pages project create my-site --production-branch main

# List all projects
wrangler pages project list

# Delete a project (irreversible)
wrangler pages project delete my-site --yes
```

### Deploying

```bash
# Deploy static assets from a directory
wrangler pages deploy ./dist

# Deploy with git metadata (useful in CI)
wrangler pages deploy ./dist \
  --commit-hash=$(git rev-parse HEAD) \
  --commit-message="$(git log -1 --pretty=%B)" \
  --branch=$(git branch --show-current)

# Skip asset caching during deploy (useful for debugging)
wrangler pages deploy ./dist --skip-caching
```

### Local Development

```bash
# Run local dev server for a static directory
wrangler pages dev ./public --port 3000

# Dev with bindings (KV, D1, R2)
wrangler pages dev ./public \
  --kv MY_KV \
  --d1 MY_DB \
  --r2 MY_BUCKET

# HTTPS local dev
wrangler pages dev ./public \
  --local-protocol https \
  --https-key-path ./key.pem \
  --https-cert-path ./cert.pem
```

### Secrets

```bash
# Set a secret (prompts for value)
wrangler pages secret put API_KEY --project-name my-site

# Bulk upload secrets from JSON or .dev.vars file
wrangler pages secret bulk secrets.json --project-name my-site

# List and delete
wrangler pages secret list --project-name my-site
wrangler pages secret delete API_KEY --project-name my-site
```

### Deployment Management

```bash
# List deployments
wrangler pages deployment list --project-name my-site

# Tail live function logs
wrangler pages deployment tail --project-name my-site

# Tail with filters
wrangler pages deployment tail DEPLOYMENT_ID \
  --status error --method POST --search "timeout"

# Export project config as wrangler.toml (experimental)
wrangler pages download config my-site
```

### Build Functions

```bash
# Compile Pages Functions into a single Worker bundle
wrangler pages functions build --outfile _worker.js --minify --sourcemap
```

---

## Hyperdrive

Hyperdrive accelerates database connections from Workers by pooling connections and caching SQL responses at the edge. It sits between your Worker and your origin database (PostgreSQL or MySQL).

### Creating a Configuration

```bash
# Create with a connection string (most common)
wrangler hyperdrive create my-db \
  --connection-string="postgresql://user:pass@db.example.com:5432/mydb"

# Create with individual params
wrangler hyperdrive create my-db \
  --origin-host db.example.com \
  --origin-port 5432 \
  --database mydb \
  --origin-user user \
  --origin-password pass \
  --origin-scheme postgresql
```

### Caching Options

```bash
# Create with caching tuned
wrangler hyperdrive create my-db \
  --connection-string="postgresql://user:pass@host:5432/db" \
  --max-age 60 \
  --swr 30

# Create with caching disabled (for write-heavy workloads)
wrangler hyperdrive create my-db \
  --connection-string="postgresql://user:pass@host:5432/db" \
  --caching-disabled
```

**Caching note:** `--max-age` and `--caching-disabled` are mutually exclusive.

### SSL and mTLS

```bash
# Require SSL verification
wrangler hyperdrive create my-db \
  --connection-string="postgresql://user:pass@host:5432/db" \
  --sslmode verify-full

# With mTLS client certificate
wrangler hyperdrive create my-db \
  --connection-string="postgresql://user:pass@host:5432/db" \
  --mtls-certificate-id <CERT_UUID>
```

SSL modes: PostgreSQL uses `require | verify-ca | verify-full`. MySQL uses `REQUIRED | VERIFY_CA | VERIFY_IDENTITY`.

### Management

```bash
wrangler hyperdrive list                     # List all configs
wrangler hyperdrive get <CONFIG_ID>          # Get details
wrangler hyperdrive update <CONFIG_ID> --name new-name --max-age 120
wrangler hyperdrive delete <CONFIG_ID>       # Remove config
```

### Quick Reference

| Task | Command |
|------|---------|
| Create config | `hyperdrive create NAME --connection-string=...` |
| List configs | `hyperdrive list` |
| Get config details | `hyperdrive get ID` |
| Update caching | `hyperdrive update ID --max-age 60 --swr 15` |
| Delete config | `hyperdrive delete ID` |

---

## Vectorize

Vectorize is Cloudflare's vector database for similarity search and AI/ML embeddings. Indexes store vectors with optional metadata for filtered queries.

### Creating an Index

```bash
# Create with explicit dimensions and metric
wrangler vectorize create my-index --dimensions 1536 --metric cosine

# Create using a model preset (auto-sets dimensions/metric)
wrangler vectorize create my-index --preset openai-text-embedding-ada-002
```

**Metrics:** `cosine`, `euclidean`, `dot-product`. Choose based on your embedding model's recommendations.

### Inserting Vectors

Vectors are inserted via newline-delimited JSON (NDJSON) files:

```jsonl
{"id": "vec1", "values": [0.1, 0.2, ...], "namespace": "docs", "metadata": {"title": "Hello"}}
{"id": "vec2", "values": [0.3, 0.4, ...], "namespace": "docs", "metadata": {"title": "World"}}
```

```bash
# Insert vectors (batch size: 1,000)
wrangler vectorize insert my-index --file vectors.ndjson

# Upsert vectors (insert or update, batch size: 5,000)
wrangler vectorize upsert my-index --file vectors.ndjson
```

**Use `upsert` over `insert`** when you may have duplicate IDs -- it has higher throughput (5,000 vs 1,000 batch default).

### Querying

```bash
# Query by vector
wrangler vectorize query my-index \
  --vector="[0.1, 0.2, 0.3, ...]" \
  --top-k 10

# Query by existing vector ID
wrangler vectorize query my-index \
  --vector-id vec1 \
  --top-k 5 \
  --namespace docs

# Query with metadata filter
wrangler vectorize query my-index \
  --vector="[0.1, 0.2, ...]" \
  --top-k 10 \
  --filter '{"title": "Hello"}'
```

### Metadata Indexes

Create metadata indexes to enable filtered queries on specific fields:

```bash
# Index a string metadata field
wrangler vectorize create-metadata-index my-index \
  --propertyName title --type string

# Index a numeric field
wrangler vectorize create-metadata-index my-index \
  --propertyName score --type number

# List and delete metadata indexes
wrangler vectorize list-metadata-index my-index
wrangler vectorize delete-metadata-index my-index --propertyName title
```

**Important:** You must create metadata indexes BEFORE querying with filters on those fields.

### Vector Management

```bash
# Get specific vectors by ID
wrangler vectorize get-vectors my-index --ids vec1 vec2 vec3

# Delete specific vectors
wrangler vectorize delete-vectors my-index --ids vec1 vec2

# List vector IDs (paginated, max 1,000 per call)
wrangler vectorize list-vectors my-index --count 100

# Get index stats
wrangler vectorize info my-index
```

### Quick Reference

| Task | Command |
|------|---------|
| Create index | `vectorize create NAME --dimensions N --metric cosine` |
| Insert vectors | `vectorize insert NAME --file data.ndjson` |
| Upsert vectors | `vectorize upsert NAME --file data.ndjson` |
| Query | `vectorize query NAME --vector="[...]" --top-k 10` |
| Add metadata index | `vectorize create-metadata-index NAME --propertyName X --type string` |
| Delete index | `vectorize delete NAME --force` |

---

## Pipelines

Pipelines ingest data from HTTP or Workers and write it to R2 in batched, compressed files. Useful for logging, analytics, and event streaming.

### Setup and Creation

```bash
# Interactive setup (recommended for first time)
wrangler pipelines setup --name my-pipeline

# Create with SQL transform
wrangler pipelines create my-pipeline --sql "SELECT timestamp, level, message FROM _"

# Create with SQL from file
wrangler pipelines create my-pipeline --sql-file transform.sql
```

### Streams (Ingestion Sources)

```bash
# Create an HTTP stream with schema validation
wrangler pipelines streams create my-stream \
  --pipeline my-pipeline \
  --schema-file schema.json \
  --http-enabled \
  --http-auth

# Create with CORS support
wrangler pipelines streams create my-stream \
  --pipeline my-pipeline \
  --cors-origin "https://example.com"

# List and manage streams
wrangler pipelines streams list --pipeline my-pipeline
wrangler pipelines streams get my-stream --pipeline my-pipeline
wrangler pipelines streams delete my-stream --pipeline my-pipeline
```

### Sinks (Output Destinations)

```bash
# Create an R2 sink with Parquet output
wrangler pipelines sinks create my-sink \
  --pipeline my-pipeline \
  --type r2 \
  --bucket my-r2-bucket \
  --format parquet \
  --compression zstd \
  --path "logs/" \
  --roll-interval 300

# With R2 data catalog integration
wrangler pipelines sinks create my-sink \
  --pipeline my-pipeline \
  --type r2-data-catalog \
  --bucket my-r2-bucket \
  --namespace my-namespace \
  --table my-table \
  --catalog-token TOKEN
```

### Legacy Pipeline Update (Batch Tuning)

```bash
wrangler pipelines update my-pipeline \
  --r2-bucket my-bucket \
  --batch-max-mb 50 \
  --batch-max-rows 100000 \
  --batch-max-seconds 60 \
  --compression zstd \
  --shard-count 4
```

**Batch defaults:** 100 MB max, 10M rows max, 300s max age. Tune these based on your throughput and latency needs.

### Management

```bash
wrangler pipelines list                          # List all pipelines
wrangler pipelines list --json                   # JSON output
wrangler pipelines get my-pipeline               # Get details
wrangler pipelines delete my-pipeline --force    # Delete without prompt
```

---

## Containers

Containers let you run Docker containers on Cloudflare's network alongside Workers. Use `wrangler containers` to build, push, and manage container images and instances.

### Build and Push

```bash
# Build a container image from a Dockerfile
wrangler containers build . --tag my-app:latest

# Build and push in one step
wrangler containers build . --tag my-app:latest --push

# Push a previously built image
wrangler containers push my-app:latest
```

### Instance Management

```bash
# List all containers
wrangler containers list

# Get container details and running instances
wrangler containers info <CONTAINER_ID>

# List instances of a specific application
wrangler containers instances <APPLICATION_ID>

# Delete a container
wrangler containers delete <CONTAINER_ID>
```

### SSH into Running Instances

```bash
# Interactive SSH session
wrangler containers ssh <INSTANCE_ID>

# Execute a remote command
wrangler containers ssh <INSTANCE_ID> -- ls -al /app
wrangler containers ssh <INSTANCE_ID> -- cat /var/log/app.log
```

### Registry Management

```bash
# List images in the Cloudflare registry
wrangler containers images list

# Delete an image
wrangler containers images delete <IMAGE_ID>

# Configure an external registry (e.g., ECR)
wrangler containers registries configure
wrangler containers registries list
wrangler containers registries credentials
wrangler containers registries delete
```

---

## Workflows

Workflows provide durable, multi-step execution on Cloudflare. Use `wrangler workflows` to manage workflow definitions and their running instances. Requires Wrangler v3.83.0+.

### Managing Workflows

```bash
# List all workflows
wrangler workflows list

# Describe a specific workflow
wrangler workflows describe my-workflow

# Delete a workflow (also deletes all its instances)
wrangler workflows delete my-workflow
```

### Triggering and Running

```bash
# Trigger a workflow run
wrangler workflows trigger my-workflow

# Trigger with JSON parameters
wrangler workflows trigger my-workflow '{"key": "value", "count": 42}'

# Trigger with a custom instance ID
wrangler workflows trigger my-workflow '{"key": "value"}' --id my-custom-id
```

### Instance Management

```bash
# List all instances of a workflow
wrangler workflows instances list my-workflow

# List only errored instances
wrangler workflows instances list my-workflow --status errored

# Filter by status: queued | running | paused | errored | terminated | complete
wrangler workflows instances list my-workflow --status running

# Describe an instance (defaults to latest)
wrangler workflows instances describe my-workflow latest
wrangler workflows instances describe my-workflow <INSTANCE_ID>

# Control instance lifecycle
wrangler workflows instances pause my-workflow <INSTANCE_ID>
wrangler workflows instances resume my-workflow <INSTANCE_ID>
wrangler workflows instances terminate my-workflow <INSTANCE_ID>
wrangler workflows instances restart my-workflow <INSTANCE_ID>

# Send an event to a running/paused instance
wrangler workflows instances send-event my-workflow <INSTANCE_ID> \
  --type "approval" \
  --payload '{"approved": true}'
```

### Quick Reference

| Task | Command |
|------|---------|
| List workflows | `workflows list` |
| Trigger a run | `workflows trigger NAME '{"params": ...}'` |
| List instances | `workflows instances list NAME --status running` |
| Inspect latest | `workflows instances describe NAME latest` |
| Pause/resume | `workflows instances pause/resume NAME ID` |
| Terminate | `workflows instances terminate NAME ID` |
| Send event | `workflows instances send-event NAME ID --type T --payload '{}'` |

---

## Workers for Platforms (Dispatch Namespaces)

Workers for Platforms enables multi-tenant architectures. Dispatch namespaces isolate tenant Workers so a platform can deploy and route to customer-specific code.

### Commands

```bash
# Create a dispatch namespace
wrangler dispatch-namespace create tenant-workers

# List all namespaces
wrangler dispatch-namespace list

# Get namespace details
wrangler dispatch-namespace get tenant-workers

# Rename a namespace
wrangler dispatch-namespace rename tenant-workers customer-workers

# Delete a namespace (must remove all user Workers first)
wrangler dispatch-namespace delete tenant-workers
```

**Deletion constraint:** You must delete ALL user Workers inside a dispatch namespace before you can delete the namespace itself.

### Quick Reference

| Task | Command |
|------|---------|
| Create namespace | `dispatch-namespace create NAME` |
| List namespaces | `dispatch-namespace list` |
| Get details | `dispatch-namespace get NAME` |
| Rename | `dispatch-namespace rename OLD NEW` |
| Delete | `dispatch-namespace delete NAME` |

---

## Best Practices

### General

- Always use `--json` output in CI/CD scripts for machine-readable results
- Use `--config` to point to a specific `wrangler.toml` when managing multiple projects
- Use `--env` to target specific environments (staging, production)

### Pages

- Set `--production-branch` at project creation time to match your git workflow
- Use `pages secret bulk` over individual `secret put` in CI for faster secret management
- Use `pages download config` to generate a `wrangler.toml` from an existing dashboard-configured project

### Hyperdrive

- Enable caching (`--max-age`, `--swr`) for read-heavy workloads; disable for write-heavy
- Use `--sslmode verify-full` in production for maximum security
- Connection string format: `protocol://user:password@host:port/database`

### Vectorize

- Always create metadata indexes before deploying queries that filter on those fields
- Prefer `upsert` over `insert` for idempotent data pipelines
- Match `--dimensions` exactly to your embedding model's output size
- Choose `--metric` based on your model's documentation (cosine is most common)

### Pipelines

- Use `--sql` transforms to filter or reshape data before it lands in R2
- Tune batch settings based on your volume: smaller batches = lower latency, larger = fewer files
- Use Parquet format with zstd compression for analytics workloads

### Containers

- Use `--push` with `build` to combine build+push in CI pipelines
- Use `ssh` for debugging running instances, not for production operations

### Workflows

- Use `--status` filters when listing instances to find problems quickly
- Use custom instance IDs (`--id`) for idempotency when triggering from external systems
- Deleting a workflow deletes all its instances -- be careful in production
