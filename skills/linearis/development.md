# Linearis: Development
Based on Linearis 2025.12.3 documentation.

## Setup & Build

### Installation

```bash
# npm (recommended)
npm install -g linearis

# From source
git clone https://github.com/czottmann/linearis.git
cd linearis
npm install    # Auto-builds via prepare script (clean + build)
npm link       # Creates global 'linearis' command
```

### Requirements

- Node.js >= 22.0.0
- ES modules (`"type": "module"` in package.json)
- All imports use `.js` extensions (TypeScript resolves `.js` → `.ts` during compilation)

### Build Commands

| Command | Purpose |
|---------|---------|
| `npm start <command>` | Development mode via tsx (~0.64s startup) |
| `npm run build` | Compile TypeScript → `dist/` (production) |
| `npm run clean` | Remove `dist/` directory (cross-platform) |
| `npm run prepare` | Auto-runs on `npm install`: clean + build |
| `npm test` | Run test suite |
| `npm test:watch` | Tests in watch mode |
| `npm test:coverage` | Generate coverage report |
| `npm test:commands` | CLI command coverage report |

### Development vs Production

| | Development | Production |
|---|-----------|-----------|
| Command | `npm start issues list` | `node dist/main.js issues list` |
| Engine | tsx (TypeScript at runtime) | Compiled JavaScript |
| Startup | ~0.64s | ~0.15s |
| Use case | Local development | Deployment, CI, daily use |

### TypeScript Configuration

- **Target:** ES2023
- **Module:** ESNext with ES modules output
- **Output:** `dist/` directory with declaration files
- **Optimizations:** Remove comments, no source maps for production
- **Strict mode** enabled

## Code Patterns

### Command Setup Pattern

Each command domain gets its own file exporting a setup function:

```typescript
// src/commands/issues.ts
export function setupIssuesCommands(program: Command): void {
  const issues = program.command("issues").description("Issue operations");

  // Show help when no subcommand given
  issues.action(() => { issues.help(); });

  issues.command("read <issueId>")
    .description("Get issue details (supports UUID and ABC-123 format)")
    .action(handleAsyncCommand(async (issueId: string, options: any, command: Command) => {
      const service = await createLinearService(command.parent!.parent!.opts());
      const result = await service.getIssueById(issueId);
      outputSuccess(result);
    }));
}
```

Register in `src/main.ts`:
```typescript
import { setupIssuesCommands } from "./commands/issues.js";
setupIssuesCommands(program);
```

### Service Creation Pattern

```typescript
export async function createLinearService(options: CommandOptions): Promise<LinearService> {
  const apiToken = await getApiToken(options);
  return new LinearService(apiToken);
}
```

### Async Error Handling

All commands use `handleAsyncCommand()` wrapper for consistent JSON error output:

```typescript
export function handleAsyncCommand(
  asyncFn: (...args: any[]) => Promise<void>,
): (...args: any[]) => Promise<void> {
  return async (...args: any[]) => {
    try {
      await asyncFn(...args);
    } catch (error) {
      outputError(error instanceof Error ? error : new Error(String(error)));
    }
  };
}
```

Service methods throw descriptive errors:
```typescript
throw new Error("Team 'ABC' not found");
// Output: { "error": "Team 'ABC' not found" }
```

### Smart ID Resolution Pattern

```typescript
import { isUuid } from "../utils/uuid.js";

// UUID validation
export function isUuid(value: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(value);
}

// Flexible identifier handling in service methods
if (isUuid(issueId)) {
  issue = await this.client.issue(issueId);
} else {
  // Parse team-number format like "ABC-123"
  const parts = issueId.split("-");
  const teamKey = parts.slice(0, -1).join("-");
  const issueNumber = parseInt(parts[parts.length - 1]);
  // ... resolve via team.key + issue.number query
}
```

### GraphQL Patterns

**Single-query strategy** — fetch all relationships in one request:
```typescript
async getIssues(limit: number = 25): Promise<LinearIssue[]> {
  const result = await this.graphQLService.rawRequest(GET_ISSUES_QUERY, {
    first: limit,
    orderBy: "updatedAt" as any,
  });
}
```

**Batch resolution** — resolve multiple names to UUIDs in one query:
```typescript
const resolveResult = await this.graphQLService.rawRequest(
  BATCH_RESOLVE_FOR_CREATE_QUERY,
  { teamName, projectName, labelNames },
);
```

**Label management** — add vs overwrite modes:
```typescript
if (labelMode === "adding") {
  finalLabelIds = [...new Set([...currentIssueLabels, ...resolvedLabels])];
} else {
  finalLabelIds = resolvedLabels;  // Replace all
}
```

## Adding New Commands

Step-by-step workflow:

1. **Define interfaces** in `src/utils/linear-types.d.ts`
   ```typescript
   export interface CreateWidgetArgs { name: string; teamId?: string; }
   ```

2. **Create GraphQL queries** in `src/queries/<entity>.ts`
   - Reuse fragments from `src/queries/common.ts` where possible
   - Design for single-query fetching (embed relationships)

3. **Implement service methods** in `src/utils/graphql-issues-service.ts` (or create a new `graphql-<entity>-service.ts`)

4. **Create command handler** in `src/commands/<entity>.ts`
   - Export `setup<Entity>Commands(program: Command)`
   - Use `handleAsyncCommand()` wrapper
   - Use `outputSuccess()` for results

5. **Register** in `src/main.ts`
   ```typescript
   import { setupWidgetCommands } from "./commands/widgets.js";
   setupWidgetCommands(program);
   ```

## Adding GraphQL Queries

1. **Define fragments** in `src/queries/common.ts` if reusable across operations
2. **Create query strings** in `src/queries/<entity>.ts`
3. **Use fragments** to ensure consistent data fetching
4. **Add service method** using `this.graphQLService.rawRequest()`
5. **Verify** all nested relationships are fetched in single query (no N+1)

## Testing with Vitest

### Test Structure

```
tests/
├── unit/                              # Fast, uses mocks, no API token needed
│   └── linear-service-cycles.test.ts
└── integration/                       # Slower, runs compiled CLI, needs API token
    ├── cycles-cli.test.ts
    └── project-milestones-cli.test.ts
```

### Running Tests

```bash
npm test                                          # All tests
npx vitest run tests/unit                         # Unit tests only
npx vitest run tests/integration                  # Integration tests only
npx vitest run tests/unit/linear-service-cycles.test.ts  # Specific file
npx vitest run -t "should fetch cycles"           # By test name
npm test:watch                                    # Watch mode
npm test:coverage                                 # Coverage report → coverage/index.html
npm test:commands                                 # CLI command coverage report
```

### Unit Test Example

```typescript
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LinearService } from "../../src/utils/linear-service.js";

describe("LinearService - getCycles()", () => {
  let mockClient: any;
  let service: LinearService;

  beforeEach(() => {
    mockClient = { cycles: vi.fn() };
    service = new LinearService("fake-token");
    service.client = mockClient;
  });

  it("should fetch cycles without filters", async () => {
    mockClient.cycles.mockResolvedValue({
      nodes: [{ id: "cycle-1", name: "Sprint 1" }],
    });

    const result = await service.getCycles();

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Sprint 1");
  });
});
```

- Use `vi.fn()` (not Jest's `jest.fn()`)
- Import from paths with `.js` extension
- No API token needed — mocks handle everything

### Integration Test Example

```typescript
import { describe, expect, it } from "vitest";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const hasApiToken = !!process.env.LINEAR_API_TOKEN;

describe("Cycles CLI", () => {
  it.skipIf(!hasApiToken)("should list cycles", async () => {
    const { stdout, stderr } = await execAsync("node ./dist/main.js cycles list");
    expect(stderr).not.toContain("query too complex");
    const cycles = JSON.parse(stdout);
    expect(Array.isArray(cycles)).toBe(true);
  });
});
```

- Requires `LINEAR_API_TOKEN` env var and built CLI (`npm run build`)
- Automatically skipped if token not set
- Default timeout: 30s (override with `{ timeout: 60000 }`)

### Test Naming Convention

```typescript
describe("ComponentName - methodName()", () => {
  it("should do something specific", async () => {
    // Arrange
    const input = { data: "test" };
    // Act
    const result = await methodName(input);
    // Assert
    expect(result).toBe(expected);
  });
});
```

### When to Write Which Type

| Unit tests | Integration tests |
|-----------|------------------|
| Complex business logic | New CLI commands |
| Data transformations | New command flags |
| Error handling | Critical user workflows |
| Edge cases / boundaries | Bug fix regressions |

### CI (GitHub Actions)

- **Test job:** Install → build → run tests → integration tests (if `LINEAR_API_TOKEN` secret configured)
- **Lint job:** TypeScript type check → verify clean build

## Deployment

### npm Package (Primary)

```bash
npm install -g linearis
```

### Git-Based Install

```bash
npm install git+https://github.com/czottmann/linearis.git
# Automatically builds via prepare script
```

### Container

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json tsconfig.json ./
COPY src/ ./src/
RUN npm install
ENTRYPOINT ["node", "dist/main.js"]
```

### Authentication in Deployment

| Environment | Recommended Method |
|-------------|-------------------|
| Container / CI | `LINEAR_API_TOKEN` env var |
| Server | Token file at `~/.linear_api_token` |
| Interactive | `--api-token` flag |

## Quick Reference

### Naming Conventions

| Entity | Convention | Examples |
|--------|-----------|----------|
| Files | kebab-case | `linear-service.ts`, `graphql-issues-service.ts` |
| Directories | lowercase | `commands`, `utils`, `queries` |
| Classes | PascalCase | `LinearService`, `GraphQLIssuesService` |
| Functions | camelCase | `createLinearService`, `handleAsyncCommand` |
| Interfaces | PascalCase + descriptive | `LinearIssue`, `CreateIssueArgs` |

### File Organization

| Directory | Purpose |
|-----------|---------|
| `src/main.ts` | CLI entry point |
| `src/commands/` | Command handlers (one file per domain) |
| `src/utils/` | Services, auth, output, types |
| `src/queries/` | GraphQL query definitions |
| `tests/unit/` | Unit tests with mocks |
| `tests/integration/` | CLI integration tests |
| `dist/` | Compiled output (auto-generated) |
| `docs/` | Project documentation |
