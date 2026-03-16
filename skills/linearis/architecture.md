# Linearis: Architecture
Based on Linearis 2025.12.3 documentation.

## Overview

Linearis follows a modular, service-oriented architecture with clear separation of concerns:

- **Command layer** — Commander.js CLI interface (`src/commands/`)
- **Service layer** — Dual GraphQL + SDK services (`src/utils/`)
- **Query layer** — Optimized GraphQL queries with fragments (`src/queries/`)
- **Type system** — TypeScript interfaces for all Linear entities

The architecture emphasizes performance through GraphQL batch operations, single-query optimizations, and smart ID resolution. All output is structured JSON.

## Component Map

### Command Layer (`src/commands/`)

Each file exports a `setup*Commands(program)` function registered in `src/main.ts`.

| File | Responsibility |
|------|---------------|
| `src/main.ts` | CLI entry point, Commander.js setup, global options, command routing |
| `commands/issues.ts` | Issue CRUD + search, label management, parent relationships |
| `commands/projects.ts` | Project list and read |
| `commands/comments.ts` | Comment creation with lightweight issue ID resolution |
| `commands/teams.ts` | Team listing |
| `commands/users.ts` | User listing with active filtering |
| `commands/embeds.ts` | File download/upload for Linear attachments |
| `commands/cycles.ts` | Cycle listing and reading |
| `commands/documents.ts` | Document CRUD |

### Service Layer (`src/utils/`)

| File | Responsibility |
|------|---------------|
| `graphql-service.ts` | GraphQL client wrapper, raw query execution, batch operations |
| `graphql-issues-service.ts` | Optimized single-query issue operations (604 lines — the largest file) |
| `linear-service.ts` | SDK-based API service, smart ID resolution, fallback operations |
| `auth.ts` | Multi-source authentication (flag → env var → file) |
| `output.ts` | JSON formatting, error handling, `handleAsyncCommand()` wrapper |
| `embed-parser.ts` | Markdown parsing to extract Linear upload URLs |
| `file-service.ts` | Authenticated file downloads with signed URL support |
| `uuid.ts` | UUID validation for smart ID resolution |
| `linear-types.d.ts` | TypeScript interfaces for all Linear entities and operation args |

### Query Layer (`src/queries/`)

| File | Responsibility |
|------|---------------|
| `common.ts` | Reusable GraphQL fragments (`COMPLETE_ISSUE_FRAGMENT`, etc.) |
| `issues.ts` | Issue-specific queries and mutations |
| `index.ts` | Query exports |

## Two-Layer Service Architecture

The codebase uses a dual-service pattern optimized for different concerns:

### 1. GraphQLService + GraphQLIssuesService (Primary)

Direct GraphQL queries with batch operations. Used by all primary commands.

- Eliminates N+1 query problems
- Single-query fetches for complex relationships
- Batch ID resolution (resolve team + project + labels in one query)

```
commands/*.ts → graphql-issues-service.ts → graphql-service.ts → @linear/sdk GraphQL client
```

### 2. LinearService (ID Resolution + Fallback)

SDK-based operations for smart ID resolution and complex workflows.

- Human-friendly ID conversions (`ABC-123` → UUID, `"Bug"` → label UUID)
- Fallback for operations not yet migrated to GraphQL
- `resolve*Id()` methods for all entity types

```
commands/*.ts → linear-service.ts → @linear/sdk
```

### When each is used

| Use case | Service |
|----------|---------|
| List/search/read/create/update issues | GraphQLIssuesService |
| Resolve `ABC-123` → UUID | LinearService |
| Resolve project/team/label names → UUIDs | LinearService (or batch GraphQL) |
| Comment creation | LinearService (lightweight) |
| File downloads | FileService |

## Data Flow

### Command Execution

```
1. CLI args parsed         → src/main.ts (Commander.js)
2. Auth token resolved     → src/utils/auth.ts (flag → env → file)
3. Service created         → createLinearService() or createGraphQLService()
4. API operation executed  → Optimized GraphQL or SDK call
5. Response formatted      → src/utils/output.ts → JSON to stdout
```

### Smart ID Resolution

Linear uses UUIDs internally, but users prefer human-readable identifiers:

| Input | Resolution Strategy |
|-------|-------------------|
| `ABC-123` | Parse team key (`ABC`) + issue number (`123`) → query by `team.key` + `issue.number` |
| `"Mobile App"` (project) | Query projects by name → return UUID |
| `"ABC"` (team) | Try team key first, then team name → return UUID |
| `"Bug"` (label) | Query labels by name (scoped to team) → return UUID |
| `"Sprint 2025-10"` (cycle) | Query by name, disambiguate with active/next/previous status |
| Valid UUID | Pass through directly |

### Embed Extraction Flow

```
GraphQL response → graphql-issues-service.ts → embed-parser.ts → embeds array in JSON output
```

Each embed includes: file URL, filename, `expiresAt` timestamp (signed URLs expire in ~1 hour).

## GraphQL Optimization Patterns

### The N+1 Problem (What Was Fixed)

Original SDK approach for listing 10 issues:

```
1 query:  Fetch issues list
10 × 5:  For each issue → state, team, assignee, project, labels
= 51 API calls, 10+ seconds
```

### Solution 1: Single-Query Strategy

One GraphQL query fetches issues with all relationships embedded:

```graphql
fragment CompleteIssue on Issue {
  id identifier title description priority estimate
  state { id name }
  assignee { id name }
  team { id key name }
  project { id name }
  labels { nodes { id name } }
  createdAt updatedAt
}
```

```typescript
// 1 query instead of 51
const result = await this.graphQLService.rawRequest(GET_ISSUES_QUERY, {
  first: limit,
  orderBy: "updatedAt",
});
```

### Solution 2: Batch ID Resolution

When creating or updating issues, resolve all name-to-UUID lookups in a single query:

```typescript
// Before: 7+ sequential API calls (team, project, each label separately)
// After: 1 batch query resolves everything
const resolveResult = await this.graphQLService.rawRequest(
  BATCH_RESOLVE_FOR_CREATE_QUERY,
  { teamName, projectName, labelNames },
);
```

### Solution 3: Fragment Reuse

Shared fragments in `src/queries/common.ts` ensure consistent, complete data fetching across all operations without redundant field definitions.

## Performance Results

| Operation | Before (SDK) | After (GraphQL) | Improvement |
|-----------|-------------|-----------------|-------------|
| Single issue read | ~10+ seconds | ~0.9-1.1s | **90%+** |
| List 10 issues | ~30+ seconds | ~0.9s | **95%+** |
| Create issue | ~2-3 seconds | ~1.1s | **50%+** |
| Search issues | ~15+ seconds | ~1.0s | **93%+** |

Compiled CLI startup: ~0.15s (vs ~0.64s with tsx in development).

## File Structure

### By size and complexity

| File | Lines | Role |
|------|-------|------|
| `graphql-issues-service.ts` | 604 | Core GraphQL operations (largest) |
| `linear-service.ts` | 485 | SDK fallback + ID resolution |
| `queries/issues.ts` | 301 | GraphQL query definitions |
| `commands/issues.ts` | 211 | Issue command handlers |
| `file-service.ts` | 111 | File download service |
| `embed-parser.ts` | 86 | Markdown embed extraction |
| `graphql-service.ts` | 62 | GraphQL client wrapper |
| `commands/embeds.ts` | 58 | Embeds command handler |
| `commands/comments.ts` | 46 | Comments command handler |
| `auth.ts` | 39 | Authentication |
| `output.ts` | 34 | JSON output formatting |
| `main.ts` | 25 | CLI entry point |

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@linear/sdk` | ^58.1.0 | Official Linear SDK + GraphQL client |
| `commander` | ^14.0.0 | CLI framework |
| `tsx` | ^4.20.5 | TypeScript execution (dev only) |
| `typescript` | ^5.0.0 | Compiler (dev only) |

### Requirements

- Node.js >= 22.0.0
- ES modules (`"type": "module"` in package.json)
- All imports use `.js` extensions for ES module compatibility

## Key Code Locations

| Concern | Location |
|---------|----------|
| CLI entry + routing | `src/main.ts` |
| Global `--api-token` option | `src/main.ts` |
| Issue list/search/read/create/update | `src/utils/graphql-issues-service.ts` |
| Smart ID resolution (`resolve*Id`) | `src/utils/linear-service.ts` |
| GraphQL fragments | `src/queries/common.ts` |
| Issue queries + mutations | `src/queries/issues.ts` |
| Auth token resolution chain | `src/utils/auth.ts` |
| JSON output + error wrapper | `src/utils/output.ts` |
| Label add vs replace logic | `src/utils/graphql-issues-service.ts` (lines 188-196) |
| UUID validation | `src/utils/uuid.ts` |
| Embed URL extraction | `src/utils/embed-parser.ts` |
| Linear GraphQL schema reference | `docs/Linear-API@current.graphql` |
