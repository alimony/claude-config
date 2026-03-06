# Vercel: AI Gateway
Based on Vercel documentation.

Unified API to access hundreds of AI models through a single endpoint. One API key, automatic failover, spend monitoring, zero markup on tokens.

## Base URLs

| API | Base URL |
|-----|----------|
| OpenAI-compatible | `https://ai-gateway.vercel.sh/v1` |
| Anthropic-compatible | `https://ai-gateway.vercel.sh` |
| Models list (no auth) | `https://ai-gateway.vercel.sh/v1/models` |

## Authentication

Two methods. Only one needed per request.

**API key** -- Create at Vercel Dashboard > AI Gateway > API Keys. Store as `AI_GATEWAY_API_KEY`. Works anywhere.

**OIDC token** -- Auto-available as `VERCEL_OIDC_TOKEN` on Vercel deployments. Expires after 12 hours. For local dev, run `vercel link` then `vercel env pull`.

Fallback pattern:
```typescript
const apiKey = process.env.AI_GATEWAY_API_KEY || process.env.VERCEL_OIDC_TOKEN;
```

The AI SDK auto-detects `AI_GATEWAY_API_KEY` when you pass model as a plain string.

## Model Format

Models use `creator/model-name` format: `openai/gpt-5.2`, `anthropic/claude-sonnet-4.5`, `google/gemini-3-flash`, `xai/grok-4`.

## Quick Start: AI SDK (TypeScript)

The AI SDK is the primary integration path. Install `ai` (and optionally `@ai-sdk/gateway`).

```typescript
import { streamText } from 'ai';

const result = streamText({
  model: 'openai/gpt-5.2',  // plain string = auto-routes via AI Gateway
  prompt: 'Hello!',
});

for await (const part of result.textStream) {
  process.stdout.write(part);
}
```

With explicit gateway provider (useful for custom config or provider registry):
```typescript
import { gateway } from '@ai-sdk/gateway';
import { generateText } from 'ai';

const { text } = await generateText({
  model: gateway('anthropic/claude-sonnet-4.5'),
  prompt: 'Why is the sky blue?',
});
```

Custom gateway instance (custom API key or base URL):
```typescript
import { createGateway } from '@ai-sdk/gateway';

const gateway = createGateway({
  apiKey: process.env.AI_GATEWAY_API_KEY,
  baseURL: 'https://ai-gateway.vercel.sh/v1/ai',
});
```

## Quick Start: OpenAI SDK

Change `baseURL` and `apiKey`. Works with TypeScript and Python.

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env.AI_GATEWAY_API_KEY,
  baseURL: 'https://ai-gateway.vercel.sh/v1',
});

const response = await client.chat.completions.create({
  model: 'anthropic/claude-sonnet-4.5',  // any model, not just OpenAI
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv('AI_GATEWAY_API_KEY'),
    base_url='https://ai-gateway.vercel.sh/v1'
)

response = client.chat.completions.create(
    model='anthropic/claude-sonnet-4.5',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
```

## Quick Start: Anthropic SDK

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.AI_GATEWAY_API_KEY,
  baseURL: 'https://ai-gateway.vercel.sh',  // no /v1
});

const message = await client.messages.create({
  model: 'anthropic/claude-sonnet-4.5',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

```python
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv('AI_GATEWAY_API_KEY'),
    base_url='https://ai-gateway.vercel.sh'  # no /v1
)
```

## Claude Code Integration

Configure Claude Code to route through AI Gateway:

```bash
# Shell alias (add to ~/.zshrc)
alias claude-vercel='ANTHROPIC_BASE_URL="https://ai-gateway.vercel.sh" ANTHROPIC_AUTH_TOKEN="your-api-key" ANTHROPIC_API_KEY="" claude'
```

Key: `ANTHROPIC_API_KEY` must be set to empty string -- Claude Code checks it first and would bypass `ANTHROPIC_AUTH_TOKEN` otherwise.

## Provider Routing & Fallbacks

### Provider ordering

Control which provider serves a model (e.g., Claude via Bedrock vs. Anthropic direct):

```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt,
  providerOptions: {
    gateway: {
      order: ['bedrock', 'anthropic'],  // try Bedrock first
    },
  },
});
```

### Filter providers

Restrict to specific providers only:
```typescript
providerOptions: {
  gateway: {
    only: ['anthropic', 'vertex'],  // never use other providers
  },
}
```

When `only` and `order` are combined, `only` filters first, then `order` sets priority.

### Model fallbacks

Try backup models when the primary fails:
```typescript
const result = streamText({
  model: 'openai/gpt-5.2',           // primary
  prompt,
  providerOptions: {
    gateway: {
      models: ['anthropic/claude-sonnet-4.5', 'google/gemini-3-flash'],  // fallbacks
      order: ['azure', 'openai'],     // provider preference per model
    },
  },
});
```

Failover order: primary model (all providers) -> first fallback (all providers) -> second fallback (all providers).

### Provider timeouts

Fast failover for latency-sensitive apps. BYOK credentials only.

```typescript
providerOptions: {
  gateway: {
    order: ['anthropic', 'bedrock', 'vertex'],
    providerTimeouts: {
      byok: {
        anthropic: 10000,   // 10s
        bedrock: 15000,     // 15s
        // vertex: default gateway timeout
      },
    },
  },
}
```

Timeout range: 1,000ms - 789,000ms. Measures time until first token (including thinking tokens).

### Automatic caching

Use `caching: 'auto'` to let AI Gateway handle provider-specific cache control (adds `cache_control` breakpoints for Anthropic/MiniMax automatically):

```typescript
providerOptions: {
  gateway: { caching: 'auto' },
}
```

OpenAI, Google, DeepSeek cache implicitly without this setting.

### Check routing metadata

```typescript
const metadata = await result.providerMetadata;
// metadata.gateway.routing.resolvedProvider -> which provider served it
// metadata.gateway.routing.attempts -> attempt details including errors
// metadata.gateway.cost -> cost as decimal string
// metadata.gateway.generationId -> unique ID for generation lookup
```

## Available Providers (Selected)

| Slug | Provider | Slug | Provider |
|------|----------|------|----------|
| `anthropic` | Anthropic | `openai` | OpenAI |
| `google` | Google AI | `vertex` | Vertex AI |
| `bedrock` | Amazon Bedrock | `azure` | Azure |
| `xai` | xAI | `mistral` | Mistral |
| `deepseek` | DeepSeek | `groq` | Groq |
| `fireworks` | Fireworks | `togetherai` | Together AI |
| `cohere` | Cohere | `perplexity` | Perplexity |
| `cerebras` | Cerebras | `deepinfra` | DeepInfra |

35+ providers total. Full list at `https://ai-gateway.vercel.sh/v1/models`.

## Supported Endpoints (OpenAI-Compatible)

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/models` | List all models (no auth required) |
| `GET /v1/models/{model}` | Model details |
| `POST /v1/chat/completions` | Chat completions (streaming, tools, structured output, vision, PDF) |
| `POST /v1/responses` | OpenAI Responses API |
| `POST /v1/embeddings` | Vector embeddings |

Anthropic-compatible: `POST /v1/messages` (messages, streaming, tools, thinking, structured output, files).

## Embeddings

```typescript
import { embed, embedMany } from 'ai';

const { embedding } = await embed({
  model: 'openai/text-embedding-3-small',
  value: 'Sunny day at the beach',
});

const { embeddings } = await embedMany({
  model: 'openai/text-embedding-3-small',
  values: ['text one', 'text two'],
});
```

## Image Generation

Two model types with different APIs:

| Model Type | Function | Result Location | Format |
|------------|----------|-----------------|--------|
| Multimodal LLMs (Gemini image) | `generateText` | `result.files` | `uint8Array` |
| Image-only (Flux, Recraft, Imagen) | `experimental_generateImage` | `result.images` | `base64` string |

```typescript
// Multimodal LLM (e.g., Gemini)
import { generateText } from 'ai';
const result = await generateText({
  model: 'google/gemini-3-pro-image',
  prompt: 'A mountain landscape at sunset',
});
fs.writeFileSync('output.png', result.files[0].uint8Array);

// Image-only model (e.g., Flux)
import { experimental_generateImage as generateImage } from 'ai';
const result = await generateImage({
  model: 'bfl/flux-2-flex',
  prompt: 'A coral reef with tropical fish',
  aspectRatio: '4:3',
});
fs.writeFileSync('output.png', Buffer.from(result.images[0].base64, 'base64'));
```

## Video Generation

Experimental, requires AI SDK v6. Models: Google Veo, KlingAI, Wan, others.

```typescript
import { experimental_generateVideo as generateVideo } from 'ai';

const { videos } = await generateVideo({
  model: 'google/veo-3.1-generate-001',
  prompt: 'A mountain landscape at sunset with clouds drifting by',
  aspectRatio: '16:9',
  resolution: '1920x1080',
  duration: 8,
});
fs.writeFileSync('output.mp4', videos[0].uint8Array);
```

Video generation can take minutes. Extend Node.js fetch timeout:
```typescript
import { createGateway } from 'ai';
import { Agent } from 'undici';

const gateway = createGateway({
  fetch: (url, init) => fetch(url, {
    ...init,
    dispatcher: new Agent({
      headersTimeout: 15 * 60 * 1000,
      bodyTimeout: 15 * 60 * 1000,
    }),
  } as RequestInit),
});
```

## Web Search

### Perplexity Search (works with any model)

```typescript
import { gateway, streamText } from 'ai';

const result = streamText({
  model: 'openai/gpt-5.2',
  prompt: 'What happened in tech news today?',
  tools: {
    perplexity_search: gateway.tools.perplexitySearch({
      maxResults: 5,
      searchRecencyFilter: 'week',
      searchDomainFilter: ['reuters.com', 'bbc.com'],
    }),
  },
});
```

$5 per 1,000 requests.

### Parallel Search (works with any model)

```typescript
tools: {
  parallel_search: gateway.tools.parallelSearch({
    mode: 'one-shot',  // or 'agentic' for multi-step workflows
    maxResults: 10,
    sourcePolicy: { includeDomains: ['arxiv.org'], afterDate: '2025-01-01' },
  }),
}
```

### Provider-native search

```typescript
// Anthropic
import { anthropic } from '@ai-sdk/anthropic';
tools: { web_search: anthropic.tools.webSearch_20250305() }

// OpenAI
import { openai } from '@ai-sdk/openai';
tools: { web_search: openai.tools.webSearch({}) }

// Google (Vertex or AI Studio)
import { vertex } from '@ai-sdk/google-vertex';
tools: { google_search: vertex.tools.googleSearch({}) }
```

## Structured Outputs

### Via AI SDK (generateObject)

Use `response_format` with `json_schema` type.

### Via OpenAI-compatible API

```typescript
const completion = await openai.chat.completions.create({
  model: 'openai/gpt-5.2',
  messages: [{ role: 'user', content: 'Extract: John, 30, NYC' }],
  response_format: {
    type: 'json_schema',
    json_schema: {
      name: 'person',
      schema: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          age: { type: 'integer' },
          city: { type: 'string' },
        },
        required: ['name', 'age', 'city'],
        additionalProperties: false,
      },
    },
  },
});
const data = JSON.parse(completion.choices[0].message.content);
```

### Via Responses API

```typescript
const response = await client.responses.create({
  model: 'openai/gpt-5.2',
  input: 'List 3 colors with hex codes.',
  text: {
    format: {
      type: 'json_schema',
      name: 'colors',
      strict: true,
      schema: { /* ... */ },
    },
  },
});
```

## Tool Calling

Standard OpenAI function calling format works across all models:

```typescript
const completion = await openai.chat.completions.create({
  model: 'anthropic/claude-sonnet-4.5',
  messages: [{ role: 'user', content: 'Weather in SF?' }],
  tools: [{
    type: 'function',
    function: {
      name: 'get_weather',
      parameters: {
        type: 'object',
        properties: { location: { type: 'string' } },
        required: ['location'],
      },
    },
  }],
  tool_choice: 'auto',
});
```

## Reasoning Models

```typescript
const result = streamText({
  model: 'openai/gpt-oss-120b',
  prompt,
  providerOptions: {
    openai: {
      reasoningEffort: 'high',      // 'none'|'minimal'|'low'|'medium'|'high'
      reasoningSummary: 'detailed',  // 'auto'|'concise'|'detailed'
    },
  },
});
```

For `openai/gpt-5` and `openai/gpt-5.1`, both `reasoningEffort` and `reasoningSummary` must be set.

Via Responses API: `reasoning: { effort: 'high' }`.

## BYOK (Bring Your Own Key)

Configure in Dashboard > AI Gateway > BYOK, or per-request:

```typescript
providerOptions: {
  gateway: {
    byok: {
      anthropic: [{ apiKey: process.env.ANTHROPIC_API_KEY }],
      // Multiple credentials tried in order:
      vertex: [
        { project: 'proj-1', location: 'us-east5', googleCredentials: { privateKey: '...', clientEmail: '...' } },
        { project: 'proj-2', location: 'us-east5', googleCredentials: { privateKey: '...', clientEmail: '...' } },
      ],
      bedrock: [{ accessKeyId: '...', secretAccessKey: '...', region: 'us-east-1' }],
    },
  },
}
```

BYOK credentials: zero markup. If BYOK credentials fail, Gateway retries with system credentials.

## Zero Data Retention

Default: Gateway deletes prompts/responses after request completes. For strict compliance:

```typescript
providerOptions: {
  gateway: { zeroDataRetention: true },  // only routes to ZDR-verified providers
}
```

## Observability

Dashboard metrics (AI Gateway > Overview):
- Requests by model
- Time to first token (TTFT)
- Input/output token counts
- Spend over time

Available at team level (all projects) or project level (filtered). Request logs can be sorted and exported.

## Pricing

- **Pay-as-you-go** with AI Gateway Credits, zero markup on tokens.
- Free tier available (resets monthly, starts on first request).
- Purchasing credits moves you to paid tier (no monthly free credit).
- **BYOK: zero markup, zero fee.**
- Auto top-up configurable in dashboard.
- Perplexity/Parallel web search: $5 per 1,000 requests.

## Framework Integrations

| Framework | Integration Method |
|-----------|-------------------|
| LangChain | OpenAI-compatible endpoint |
| LlamaIndex | `llama-index-llms-vercel-ai-gateway` package |
| LiteLLM | `vercel_ai_gateway/` model prefix |
| Pydantic AI | Native `VercelProvider` |
| Mastra | Direct integration |
| LangFuse | Direct integration |

## Global Default Provider

Set a default provider for all AI SDK calls in Next.js `instrumentation.ts`:

```typescript
import { openai } from '@ai-sdk/openai';

export async function register() {
  globalThis.AI_SDK_DEFAULT_PROVIDER = openai;
}
```

## Common Pitfalls

1. **Anthropic SDK base URL has no `/v1`**: Use `https://ai-gateway.vercel.sh`, not `https://ai-gateway.vercel.sh/v1`.
2. **Claude Code `ANTHROPIC_API_KEY` override**: Must set to empty string `""` or it takes precedence over `ANTHROPIC_AUTH_TOKEN`.
3. **OIDC tokens expire in 12 hours**: Re-run `vercel env pull` during extended local dev sessions.
4. **Provider timeouts are BYOK-only**: `providerTimeouts` only applies to BYOK credentials, not system credentials.
5. **Video generation timeouts**: Node.js default fetch timeout (5 min) is too short. Use custom `undici.Agent`.
6. **Image model API mismatch**: Multimodal LLMs use `generateText` (returns `files`), image-only models use `experimental_generateImage` (returns `images`).
7. **Streaming structured output**: Collect all chunks before parsing JSON; individual chunks are not valid JSON.
8. **`gpt-5`/`gpt-5.1` reasoning**: Must set both `reasoningEffort` and `reasoningSummary` or you get no reasoning output.

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid request parameters |
| 401 | Invalid or missing authentication |
| 403 | Insufficient permissions |
| 404 | Model or endpoint not found |
| 429 | Rate limit exceeded |
| 500 | Server error |
