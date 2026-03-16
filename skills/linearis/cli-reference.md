# Linearis: CLI Reference
Based on Linearis 2025.12.3 documentation.

## Overview

Linearis is a CLI tool for [Linear.app](https://linear.app) that outputs structured JSON. Designed for LLM agents and humans who prefer structured data. Key traits:

- **All output is JSON** (except help/usage text) — pipe to `jq`, scripts, or other tools
- **Smart ID resolution** — use `ABC-123` instead of UUIDs
- **Optimized GraphQL queries** — sub-second response times
- **Token-efficient** — `linearis usage` describes all commands in under 1000 tokens

```bash
linearis usage    # Show all commands and options (great for LLM agents)
linearis          # Show available top-level commands
linearis issues   # Show subcommands for a domain
```

## Authentication

Three methods, checked in this order:

| Method | Example |
|--------|---------|
| `--api-token` flag | `linearis --api-token lin_api_... issues list` |
| `LINEAR_API_TOKEN` env var | `LINEAR_API_TOKEN=lin_api_... linearis issues list` |
| Token file `~/.linear_api_token` | `echo "lin_api_..." > ~/.linear_api_token` (one-time setup) |

Get a token: Linear Settings → Security & Access → Personal API keys → Create new key.

## Smart ID Resolution

You can use human-friendly identifiers everywhere — Linearis resolves them to UUIDs automatically:

| Entity | Input Format | Example |
|--------|-------------|---------|
| Issue | `TEAM-number` | `DEV-456`, `ABC-123` |
| Project | Name string | `"Mobile App"`, `"Auth Service"` |
| Label | Name string | `"Bug"`, `"Enhancement"` |
| Team | Key or name | `"ABC"` (key) or `"Backend"` (name) |
| Cycle | Name string | `"Sprint 2025-10"` (disambiguates with `--team`) |

UUIDs are also accepted directly when you have them.

## Commands

### Issues

The primary command group. Supports full CRUD plus search.

**List issues:**
```bash
linearis issues list -l 10                # Recent issues (limit 10)
```

**Search issues:**
```bash
linearis issues search "authentication" --team Platform --project "Auth Service"
```

**Read issue details:**
```bash
linearis issues read DEV-456              # Supports ABC-123 format
# Returns JSON with all fields including embeds array (uploaded files)
```

**Create issue:**
```bash
linearis issues create "Fix login timeout" --team Backend --assignee user123 \
  --labels "Bug,Critical" --priority 1 --description "Users can't stay logged in"
```

**Update issue:**
```bash
linearis issues update ABC-123 --status "In Review" --priority 2

# Label management
linearis issues update DEV-789 --labels "Frontend,UX" --label-by adding   # Add to existing
linearis issues update ABC-123 --labels "Bug"                              # Replace all labels
linearis issues update ABC-123 --clear-labels                              # Remove all labels

# Parent-child relationships
linearis issues update SUB-001 --parent-ticket EPIC-100
```

### Comments

```bash
linearis comments create ABC-123 --body "Fixed in PR #456"
```

### Documents

Standalone markdown files that can be associated with projects or linked to issues.

```bash
# Create
linearis documents create --title "API Design" --content "# Overview\n\n..."
linearis documents create --title "Bug Analysis" --project "Backend" --attach-to ABC-123

# List
linearis documents list
linearis documents list --project "Backend"
linearis documents list --issue ABC-123

# Read / Update / Delete
linearis documents read <document-id>
linearis documents update <document-id> --title "New Title" --content "Updated content"
linearis documents delete <document-id>
```

### Embeds (File Downloads & Uploads)

The `issues read` command returns an `embeds` array with uploaded file URLs and expiration timestamps.

**Download files:**
```bash
linearis embeds download "https://uploads.linear.app/.../file.png?signature=..." --output ./screenshot.png
linearis embeds download "https://uploads.linear.app/.../file.png?signature=..." --output ./screenshot.png --overwrite
```

**Upload files:**
```bash
linearis embeds upload ./screenshot.png
# Returns: { "success": true, "assetUrl": "https://uploads.linear.app/...", "filename": "screenshot.png" }

# Upload and attach to a comment
URL=$(linearis embeds upload ./bug.png | jq -r .assetUrl)
linearis comments create ABC-123 --body "See attached: ![$URL]($URL)"
```

**Embed details:**
- Signed URLs expire after ~1 hour (`expiresAt` field in ISO 8601)
- Smart auth: signed URLs don't need Bearer token authentication
- Embed extraction happens automatically when reading issues

### Projects

```bash
linearis projects list
```

### Labels

```bash
linearis labels list --team Backend
```

### Teams

```bash
linearis teams list
```

### Users

```bash
linearis users list
linearis users list --active    # Only active users
```

### Cycles

```bash
linearis cycles list --team Backend --limit 10
linearis cycles list --team Backend --active
linearis cycles read "Sprint 2025-10" --team Backend
```

**Finding active and adjacent cycles:**

Cycle JSON includes `isActive`, `isNext`, `isPrevious`, and `number` fields.

```bash
# Get active cycle
linearis cycles list --team Backend --active --limit 1

# Get surrounding cycles (active ± N)
linearis cycles list --team Backend --around-active 3
```

**Valid flag combinations:**

| Flags | Result |
|-------|--------|
| `cycles list` | All cycles, all teams |
| `cycles list --team X` | All cycles for team X |
| `cycles list --active` | Active cycles, all teams |
| `cycles list --team X --active` | Team X's active cycle |
| `cycles list --team X --around-active 3` | Team X's active cycle ± 3 |
| `cycles list --around-active 3` | **Error** — requires `--team` |

## Output & Piping

All commands output JSON. Combine with `jq` or other tools:

```bash
# Extract identifiers and titles
linearis issues list -l 5 | jq '.[] | .identifier + ": " + .title'

# Get assignee of a specific issue
linearis issues read ABC-123 | jq '.assignee.name'

# Upload file and use URL in comment
URL=$(linearis embeds upload ./bug.png | jq -r .assetUrl)
linearis comments create ABC-123 --body "Screenshot: ![$URL]($URL)"
```

Error output is also JSON:
```json
{ "error": "Team 'XYZ' not found" }
```

## LLM Agent Integration

Linearis was designed specifically for LLM agent use. Key points:

- `linearis usage` outputs all commands in under 1000 tokens (vs ~13k for Linear MCP)
- All output is structured JSON — no parsing needed
- Smart ID resolution means agents can use human-readable identifiers from conversation context

**Example agent rule for your CLAUDE.md or system prompt:**

```markdown
We track our tickets and projects in Linear (https://linear.app). We use the
`linearis` CLI tool for communicating with Linear. Use your Bash tool to call
the `linearis` executable. Run `linearis usage` to see usage information.

Ticket numbers follow the format "ABC-<number>". Always reference tickets by
their number.

If you create a ticket and it's not clear which project to assign it to, prompt
the user. When creating subtasks, use the project of the parent ticket by default.

When the status of a task in the ticket description has changed, update the
description accordingly. When updating a ticket with a progress report that is
more than just a checkbox change, add that report as a ticket comment.

The `issues read` command returns an `embeds` array containing files uploaded to
Linear (screenshots, documents, etc.) with signed download URLs and expiration
timestamps. Use `embeds download` to download these files when needed.
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `linearis usage` | Show all commands (LLM-friendly, <1000 tokens) |
| `linearis issues list -l N` | List recent issues |
| `linearis issues search "query" --team T` | Search issues |
| `linearis issues read ID` | Read issue details + embeds |
| `linearis issues create "title" --team T` | Create issue |
| `linearis issues update ID --status S` | Update issue |
| `linearis comments create ID --body "text"` | Add comment |
| `linearis documents create --title T` | Create document |
| `linearis documents list` | List documents |
| `linearis embeds download URL --output path` | Download file |
| `linearis embeds upload path` | Upload file |
| `linearis projects list` | List projects |
| `linearis labels list --team T` | List labels |
| `linearis teams list` | List teams |
| `linearis users list [--active]` | List users |
| `linearis cycles list [--team T] [--active]` | List cycles |
| `linearis cycles read ID` | Read cycle details |
