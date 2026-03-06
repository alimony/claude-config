# Vercel: AI Tools & Agent Infrastructure
Based on Vercel documentation.

## AI SDK

The AI SDK (`ai` package) is a TypeScript toolkit for building AI-powered apps with Next.js, Vue, Svelte, and Node.js. It abstracts provider differences behind a unified API.

### Installation

```bash
npm i ai
```

### Core Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `generateText()` | Generate text from a prompt | `{ text }` |
| `generateObject()` | Generate structured data matching a Zod schema | `{ object }` |
| `streamObject()` | Stream structured data matching a Zod schema | stream |
| `tool()` | Define a tool for LLM tool-calling | tool definition |

### Text Generation

```ts
import { generateText } from 'ai';

const { text } = await generateText({
  model: 'openai/gpt-5.2',
  prompt: 'Explain quantum entanglement.',
});
```

Switch providers by changing the model string:

```ts
const { text } = await generateText({
  model: 'anthropic/claude-opus-4.5',
  prompt: 'How many people will live in the world in 2040?',
});
```

### Structured Output

```ts
import { generateObject } from 'ai';
import { z } from 'zod';

const { object } = await generateObject({
  model: 'openai/gpt-5.2',
  schema: z.object({
    recipe: z.object({
      name: z.string(),
      ingredients: z.array(z.object({ name: z.string(), amount: z.string() })),
      steps: z.array(z.string()),
    }),
  }),
  prompt: 'Generate a lasagna recipe.',
});
```

### Tool Calling

```ts
import { generateText, tool } from 'ai';
import { z } from 'zod';

const { text } = await generateText({
  model: 'openai/gpt-5.2',
  prompt: 'What is the weather in San Francisco?',
  tools: {
    getWeather: tool({
      description: 'Get the weather in a location',
      inputSchema: z.object({
        location: z.string().describe('The location to get the weather for'),
      }),
      execute: async ({ location }) => ({
        location,
        temperature: 72 + Math.floor(Math.random() * 21) - 10,
      }),
    }),
  },
});
```

---

## MCP (Model Context Protocol)

MCP is a standard interface letting LLMs communicate with external tools and data sources. Architecture: **Host** (AI app) -> **Client** (one per connection) -> **Server** (external service).

### Deploying MCP Servers on Vercel

Use the `mcp-handler` package with Next.js App Router or Vercel Functions.

```ts
// app/api/mcp/route.ts
import { z } from 'zod';
import { createMcpHandler } from 'mcp-handler';

const handler = createMcpHandler(
  (server) => {
    server.tool(
      'roll_dice',
      'Rolls an N-sided die',
      { sides: z.number().int().min(2) },
      async ({ sides }) => {
        const value = 1 + Math.floor(Math.random() * sides);
        return {
          content: [{ type: 'text', text: `You rolled a ${value}!` }],
        };
      },
    );
  },
  {},
  { basePath: '/api' },
);

export { handler as GET, handler as POST, handler as DELETE };
```

### MCP Host Configuration (Cursor example)

```json
{
  "mcpServers": {
    "server-name": {
      "url": "https://my-mcp-server.vercel.app/api/mcp"
    }
  }
}
```

### Securing MCP with OAuth

Wrap the handler with `withMcpAuth`:

```ts
import { withMcpAuth } from 'mcp-handler';

const verifyToken = async (req: Request, bearerToken?: string) => {
  if (!bearerToken) return undefined;
  const isValid = bearerToken === '123'; // Replace with real validation
  if (!isValid) return undefined;
  return { token: bearerToken, scopes: ['read:stuff'], clientId: 'user123' };
};

const authHandler = withMcpAuth(handler, verifyToken, {
  required: true,
  requiredScopes: ['read:stuff'],
  resourceMetadataPath: '/.well-known/oauth-protected-resource',
});

export { authHandler as GET, authHandler as POST };
```

Expose the OAuth metadata endpoint at `app/.well-known/oauth-protected-resource/route.ts`:

```ts
import { protectedResourceHandler, metadataCorsOptionsRequestHandler } from 'mcp-handler';

const handler = protectedResourceHandler({
  authServerUrls: ['https://your-auth-server.com'],
});
const corsHandler = metadataCorsOptionsRequestHandler();

export { handler as GET, corsHandler as OPTIONS };
```

### Vercel's Official MCP Server

Endpoint: `https://mcp.vercel.com`

Install for all agents: `npx add-mcp https://mcp.vercel.com`

Project-specific URL: `https://mcp.vercel.com/<teamSlug>/<projectSlug>`

**Client setup examples:**

```bash
# Claude Code
claude mcp add --transport http vercel https://mcp.vercel.com
```

```json
// Cursor (.cursor/mcp.json)
{ "mcpServers": { "vercel": { "url": "https://mcp.vercel.com" } } }
```

```json
// Windsurf (mcp_config.json)
{ "mcpServers": { "vercel": { "serverUrl": "https://mcp.vercel.com" } } }
```

```json
// Gemini Code Assist / Gemini CLI (~/.gemini/settings.json)
{ "mcpServers": { "vercel": { "command": "npx", "args": ["mcp-remote", "https://mcp.vercel.com"] } } }
```

### Vercel MCP Tools Reference

| Tool | Auth Required | Purpose |
|------|:---:|---------|
| `search_documentation` | No | Search Vercel docs by topic |
| `list_teams` | Yes | List teams for authenticated user |
| `list_projects` | Yes | List projects for a team |
| `get_project` | Yes | Get project details (framework, domains, latest deploy) |
| `list_deployments` | Yes | List deployments for a project |
| `get_deployment` | Yes | Get deployment details (build status, regions) |
| `get_deployment_build_logs` | Yes | Get build logs (debug failed deploys) |
| `get_runtime_logs` | Yes | Get runtime logs with filtering (level, status, time range) |
| `check_domain_availability_and_price` | Yes | Check domain availability and pricing |
| `buy_domain` | Yes | Purchase a domain |
| `get_access_to_vercel_url` | Yes | Create shareable link for protected deployments |
| `web_fetch_vercel_url` | Yes | Fetch content from a deployment URL |
| `use_vercel_cli` | Yes | Get help with Vercel CLI commands |
| `deploy_to_vercel` | Yes | Deploy the current project |

---

## Vercel Agent

AI-powered development tools integrated into the Vercel platform. Uses context from your codebase, deployment history, and runtime behavior.

### Code Review

Automatic AI code review on every PR. Runs patches in secure sandboxes with your real builds, tests, and linters. Only suggests validated fixes.

**Setup:** Dashboard > Agent > Enable > Configure repositories.

**GitHub interaction:** Comment `@vercel` on any PR:
- `@vercel run a review` -- full code review
- `@vercel fix the type errors` -- implements and commits a fix
- `@vercel why is this failing?` -- investigates the issue

**Code guidelines detection** (priority order): `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursor/rules/*.mdc`, `.cursorrules`, `.windsurfrules`, `.windsurf/rules/*.md`, `.clinerules`, `.github/instructions/*.instructions.md`, `.roo/rules/*.md`, `.aiassistant/rules/*.md`, `CONVENTIONS.md`, `.rules/*.md`, `agent.md`.

Guidelines are hierarchical (parent dirs inherited), scoped (only affect files within subtree), and capped at 50 KB total.

### Investigation

AI-powered anomaly alert analysis. Queries logs and metrics, finds patterns, identifies potential root causes.

**Requirements:** Observability Plus subscription (includes 10 investigations/billing cycle).

**Setup:** Team Settings > General > Vercel Agent > Investigations > Enabled.

### Installation

Auto-installs Web Analytics and Speed Insights via AI-generated PRs. Free for all teams.

**How:** Project > Analytics or Speed Insights tab > Enable > Implement.

### Pricing

$0.30 USD fixed per review/investigation + token costs at provider rate. Pro teams get $100 promotional credit. Installation is free.

---

## Vercel Sandbox

Ephemeral Firecracker microVMs for running untrusted code safely. Starts in milliseconds. Amazon Linux 2023 base.

### Key Specs

| Property | Value |
|----------|-------|
| Base OS | Amazon Linux 2023 |
| Runtimes | `node24`, `node22`, `python3.13` |
| Default timeout | 5 minutes (extendable to 45min hobby / 5hr pro) |
| Working directory | `/vercel/sandbox` |
| User | `vercel-sandbox` (with sudo) |
| Region | `iad1` |

### Sandbox vs Containers

Sandboxes use dedicated Firecracker microVMs with their own kernel (not shared like Docker). Designed for untrusted code with stronger isolation guarantees.

### SDK Setup

```bash
npm i @vercel/sandbox
```

```bash
# Link project and pull auth token
vercel link && vercel env pull
```

### Core SDK Usage

```ts
import { Sandbox } from '@vercel/sandbox';

// Create
const sandbox = await Sandbox.create({ runtime: 'node24' });

// Run command (blocking)
const result = await sandbox.runCommand('node', ['--version']);
console.log(result.exitCode);        // 0
console.log(await result.stdout());   // v24.x.x

// Run command (detached, for servers)
const server = await sandbox.runCommand({
  cmd: 'node', args: ['server.js'], detached: true,
});

// File operations
await sandbox.writeFiles([{ path: 'hello.txt', content: Buffer.from('hi') }]);
const buf = await sandbox.readFileToBuffer({ path: 'package.json' });
await sandbox.mkDir('assets');

// Get public URL for exposed port
const url = sandbox.domain(3000);

// Snapshots (saves state, stops sandbox)
const snapshot = await sandbox.snapshot({ expiration: 1000 * 60 * 60 * 24 * 14 });

// Resume from snapshot
const restored = await Sandbox.create({
  source: { type: 'snapshot', snapshotId: snapshot.snapshotId },
});

// Stop
await sandbox.stop();
```

### Network Policies

```ts
// Create with restricted network
const sandbox = await Sandbox.create({
  runtime: 'node24',
  networkPolicy: 'deny-all',
});

// Update network policy at runtime
await sandbox.updateNetworkPolicy({
  allow: ['google.com', 'api.openai.com'],
});

// Credential brokering (Pro/Enterprise)
await sandbox.updateNetworkPolicy({
  allow: {
    'ai-gateway.vercel.sh': [{
      transform: [{ headers: { 'x-api-key': 'secret-key' } }],
    }],
  },
});
```

### Sandbox Class Quick Reference

| Method | Returns | Notes |
|--------|---------|-------|
| `Sandbox.create(opts)` | `Promise<Sandbox>` | Options: `runtime`, `source`, `ports`, `timeout`, `networkPolicy`, `env` |
| `Sandbox.get({ sandboxId })` | `Promise<Sandbox>` | Reconnect to running sandbox |
| `Sandbox.list()` | Paginated list | Filter by `projectId`, `since`, `until` |
| `sandbox.runCommand(cmd, args)` | `Promise<CommandFinished>` | Blocking execution |
| `sandbox.runCommand({ cmd, detached: true })` | `Promise<Command>` | Non-blocking; call `.wait()` later |
| `sandbox.writeFiles(files)` | `Promise<void>` | Upload files to sandbox |
| `sandbox.readFileToBuffer({ path })` | `Promise<Buffer \| null>` | Read file contents |
| `sandbox.domain(port)` | `string` | Public URL for exposed port |
| `sandbox.snapshot()` | `Promise<Snapshot>` | Save state; sandbox stops after |
| `sandbox.stop()` | `Promise<Sandbox>` | Terminate and free resources |
| `sandbox.extendTimeout(ms)` | `Promise<void>` | Extend sandbox lifetime |
| `sandbox.updateNetworkPolicy(policy)` | `Promise<void>` | Change firewall rules at runtime |

### Common Pitfalls

- Filesystem is ephemeral -- data lost on stop unless you snapshot or export externally.
- Snapshots expire after 30 days by default (set `expiration: 0` to disable).
- Calling `snapshot()` automatically stops the sandbox.
- Exposed ports are publicly accessible -- be careful what services you run.
- Sandboxes are not for permanent hosting or persistent data storage.

---

## Agent Resources

### Markdown Access

Append `.md` to any Vercel docs URL for machine-readable markdown:

```
https://vercel.com/docs/functions.md
```

### llms-full.txt

Full Vercel docs optimized for LLMs: `https://vercel.com/docs/llms-full.txt`

### Skills.sh

Install reusable AI agent skills: `npx skills add <owner/repo>`

---

## Sign in with Vercel

OAuth 2.0 + OIDC authentication allowing users to log into your app with their Vercel account.

### OAuth Flow

1. User clicks "Sign in with Vercel"
2. Redirect to `https://vercel.com/oauth/authorize` with PKCE params
3. User consents on Vercel's consent page
4. Vercel redirects to your callback URL with `code`
5. Exchange `code` for tokens at `https://api.vercel.com/login/oauth/token`
6. Use tokens to identify user

### Tokens

| Token | Lifetime | Purpose |
|-------|----------|---------|
| ID Token | Signed JWT | Proves user identity (verify signature, read claims) |
| Access Token | 1 hour | Call Vercel REST API |
| Refresh Token | 30 days | Get new access token (rotates on use) |

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `https://vercel.com/oauth/authorize` | GET | Start authorization flow |
| `https://api.vercel.com/login/oauth/token` | POST | Exchange code for tokens |
| `https://api.vercel.com/login/oauth/token/revoke` | POST | Revoke a token |
| `https://api.vercel.com/login/oauth/token/introspect` | POST | Validate a token |
| `https://api.vercel.com/login/oauth/userinfo` | GET | Get user profile (with Bearer token) |

### Authorization Request Parameters

```ts
const queryParams = new URLSearchParams({
  client_id: process.env.NEXT_PUBLIC_VERCEL_APP_CLIENT_ID,
  redirect_uri: `${origin}/api/auth/callback`,
  state: generateSecureRandomString(43),
  nonce: generateSecureRandomString(43),
  code_challenge: crypto.createHash('sha256').update(code_verifier).digest('base64url'),
  code_challenge_method: 'S256',
  response_type: 'code',
  scope: 'openid email profile offline_access',
});
```

### Token Exchange

```ts
const params = new URLSearchParams({
  grant_type: 'authorization_code',
  client_id: process.env.NEXT_PUBLIC_VERCEL_APP_CLIENT_ID,
  client_secret: process.env.VERCEL_APP_CLIENT_SECRET,
  code,
  code_verifier,
  redirect_uri: `${origin}/api/auth/callback`,
});

const response = await fetch('https://api.vercel.com/login/oauth/token', {
  method: 'POST',
  body: params,
});
```

### Security Requirements

- Use PKCE (`code_verifier` + `code_challenge` with S256).
- Validate `state` and `nonce` on callback to prevent CSRF and replay attacks.
- Store `oauth_state`, `oauth_nonce`, `oauth_code_verifier` in httpOnly, secure, sameSite cookies (10 min TTL).
- Store tokens in httpOnly cookies, never expose to client-side JS.
- Revoke tokens on sign-out.

---

## Security Best Practices for AI Workloads

- **MCP servers:** Always verify the endpoint URL. Only use approved MCP clients. Enable human confirmation for tool execution.
- **Prompt injection:** Be aware that untrusted tools or agents could inject malicious instructions. Review permissions and data access levels for each agent.
- **Sandbox isolation:** Use `networkPolicy: 'deny-all'` when running untrusted code that shouldn't access the network. Use credential brokering instead of passing secrets directly into sandboxes.
- **Agent Code Review:** Guidelines are treated as context, not instructions -- the reviewer's core behavior (bugs, security, performance) takes precedence.
- **Sign in with Vercel:** Never store client secrets in client-side code. Use PKCE. Validate state/nonce. Use httpOnly cookies for tokens.
