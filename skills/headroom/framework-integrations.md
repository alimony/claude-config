# Headroom: Framework integrations
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill when you add Headroom to an app built on an agent framework or a provider software development kit (SDK). Each integration compresses what you send to the model: messages, tool output, chat history or retrieved documents. The model's response comes back unchanged.

## Integrations at a glance

| Framework | Language | Integration point | Wiring call |
| --- | --- | --- | --- |
| Vercel AI SDK | TypeScript | Wrap the model (middleware) | `withHeadroom(openai('gpt-4o'))` |
| OpenAI Node.js SDK | TypeScript | Wrap the client | `withHeadroom(new OpenAI())` |
| Anthropic TypeScript SDK | TypeScript | Wrap the client | `withHeadroom(new Anthropic())` |
| LangChain chat models | Python | Wrap the model | `HeadroomChatModel(ChatOpenAI(model="gpt-4o"))` |
| LangChain agents | Python | Wrap tools | `wrap_tools_with_headroom([query_database], min_chars_to_compress=1000)` |
| LangGraph | Python | Graph node | `graph.add_node("compress", create_compress_tool_messages_node(min_tokens_to_compress=100))` |
| LangChain memory | Python | Wrap the chat history | `HeadroomChatMessageHistory(InMemoryChatMessageHistory(), ...)` |
| LangChain retrievers | Python | Document compressor | `ContextualCompressionRetriever(base_compressor=HeadroomDocumentCompressor(...), base_retriever=...)` |
| LiteLLM | Python | Callback | `litellm.callbacks = [HeadroomCallback()]` |
| LiteLLM Proxy or any Asynchronous Server Gateway Interface (ASGI) app | Python | Middleware | `app.add_middleware(CompressionMiddleware)` |
| Agno | Python | Wrap the model, plus observability hooks | `HeadroomAgnoModel(wrapped_model=OpenAIChat(id="gpt-4o"))` |
| Strands | Python | Wrap the model | `HeadroomStrandsModel(wrapped_model=model)` |
| Strands | Python | Hook for tool output | `Agent(model=model, hooks=[HeadroomHookProvider(compress_tool_outputs=True)])` |
| CrewAI | Python | Wrap tools | `wrap_tools_with_headroom([search_database])` |
| AutoGen | Python | Wrap tools | `wrap_tools_with_headroom([tool])` |

## Core concepts

- **TypeScript wrappers need a running Headroom proxy.** They send messages to the proxy's `POST /v1/compress` endpoint and swap in the result. Start the proxy before you use the SDK.
- **Python integrations do not ask for the proxy.** The LiteLLM page states that its callback, middleware and `compress()` run Headroom inside the LiteLLM process. The other Python pages do not mention the proxy. The one exception is the LiteLLM guardrail, which calls the proxy over the network.
- **Only the outgoing request changes.** Compression happens before the request is sent. Streaming, tool calling, structured output and the response format behave as they do without Headroom.
- **You choose the interception point.** A model or client wrapper compresses the whole message list on every call. A tool wrapper or hook compresses each tool output before it enters the agent's context. A LangGraph node compresses tool messages between the tool step and the agent step.
- **Entry points use different engines, so savings differ.** The Strands model wrapper runs the full pipeline (CacheAligner, ContentRouter). The Strands hook calls SmartCrusher directly. The LangChain tool wrapper goes through the Model Context Protocol (MCP) compressor. The CrewAI and AutoGen wrappers call `compress_tool_result()`.
- **Thresholds gate compression.** Content below a threshold passes through unchanged. Short prompts show zero savings by design, because savings appear once tool output and history fill the context.
- **Tool output gives the biggest gains.** Large JavaScript Object Notation (JSON) arrays, logs, database results and search results compress most. The Agno page cites 70–90% reduction on tool output.

## Setup

### Start the proxy for TypeScript

```bash
pip install "headroom-ai[proxy]"
headroom proxy
```

`POST /v1/compress` accepts loopback traffic only by default, so a proxy on the same machine needs no extra configuration. In container environments, the proxy admits host gateway traffic automatically. If the proxy runs on another host, start it with `HEADROOM_COMPRESS_ALLOW_REMOTE=1`, or requests come back `404`.

### Install and import

| Integration | Install | Import from |
| --- | --- | --- |
| Vercel AI SDK | `npm install headroom-ai ai @ai-sdk/openai` | `headroom-ai/vercel-ai` |
| OpenAI Node.js SDK | `npm install headroom-ai openai` | `headroom-ai/openai` |
| Anthropic TypeScript SDK | `npm install headroom-ai @anthropic-ai/sdk` | `headroom-ai/anthropic` |
| LangChain | `pip install "headroom-ai[langchain]"` | `headroom.integrations` |
| LangGraph | `pip install "headroom-ai[langgraph]"` | `headroom.integrations.langchain` (node and `compress_tool_messages`) |
| LiteLLM | `pip install headroom-ai litellm` | `headroom.integrations.litellm_callback`, `headroom.integrations.asgi` |
| Agno | `pip install "headroom-ai[agno]" agno` | `headroom.integrations.agno` |
| Strands | `pip install headroom-ai strands-agents` | `headroom.integrations.strands` |
| CrewAI | `pip install headroom-ai crewai` | `headroom.integrations.crewai` |
| AutoGen | `pip install headroom-ai autogen-agentchat` (0.7 or later) | `headroom.integrations.autogen` |

The `[langchain]` extra installs `langchain-core` and `langchain-openai`, and `[langgraph]` adds `langgraph`. Install other LangChain packages yourself, as you would without Headroom: `langchain-anthropic` for `ChatAnthropic`, `langchain` for `create_agent` and `init_chat_model`, and `langchain-classic` for `ContextualCompressionRetriever`. `HeadroomConfig`, `HeadroomMode` and `compress` import from `headroom` itself.

## TypeScript integrations

### Vercel AI SDK

Start with `withHeadroom()`, because it is one line and works with any provider package, such as `@ai-sdk/openai`, `@ai-sdk/anthropic` or `@ai-sdk/google`. Use `headroomMiddleware()` when you compose Headroom with other middleware. Use `compressVercelMessages()` in a custom pipeline where you do not want to wrap a model.

```ts
import { withHeadroom, headroomMiddleware, compressVercelMessages } from 'headroom-ai/vercel-ai';
import { openai } from '@ai-sdk/openai';
import { generateText, wrapLanguageModel } from 'ai';

// Default: wrapLanguageModel + headroomMiddleware() in one call
const model = withHeadroom(openai('gpt-4o'));
const { text } = await generateText({ model, messages: [{ role: 'user', content: 'Summarize these results...' }] });

// Composition with other middleware (the options object is optional)
const middleware = headroomMiddleware({ model: 'gpt-4o', baseUrl: 'http://localhost:8787' });
const composed = wrapLanguageModel({ model: openai('gpt-4o'), middleware });

// Standalone: compress Vercel-format messages in a custom pipeline
const result = await compressVercelMessages(messages, { model: 'gpt-4o' });
console.log(`Saved ${result.tokensSaved} tokens`); // result.messages stays in Vercel format
```

The wrapper converts messages from Vercel format to OpenAI format, compresses them through `/v1/compress`, and converts them back. `streamText`, structured output through `generateText` with `Output.object(...)`, and tool calling all work unchanged.

### OpenAI Node.js SDK

```ts
import { withHeadroom } from 'headroom-ai/openai';
import OpenAI from 'openai';

const client = withHeadroom(new OpenAI()); // optional 2nd argument: { model, baseUrl }
const stream = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: longConversation, // tool calls and tool output are compressed too
  stream: true,               // compression runs before the request, so streaming is unaffected
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? '');
}
```

The wrapper intercepts `chat.completions.create()` only. It extracts `messages`, sends them to `POST /v1/compress`, swaps in the result and forwards the request to OpenAI. Embeddings, images and audio pass through unchanged.

### Anthropic TypeScript SDK

```ts
import { withHeadroom } from 'headroom-ai/anthropic';
import Anthropic from '@anthropic-ai/sdk';

const client = withHeadroom(new Anthropic(), { model: 'claude-sonnet-4-5-20250929', baseUrl: 'http://localhost:8787' });
const response = await client.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  messages: longConversation, // tool_result blocks get the biggest savings
  max_tokens: 1024,
});
```

- The wrapper intercepts `messages.create()` only, and `stream: true` works as usual.
- The adapter converts `text`, `tool_use` and `tool_result` blocks to OpenAI format, compresses them, and converts them back. The docs call this conversion lossless.
- The conversion is an SDK choice, not a requirement of the endpoint. `POST /v1/compress` compresses Anthropic content blocks natively. When you call the endpoint directly, from a gateway or LiteLLM's `headroom` guardrail, send Anthropic-shaped messages as they are. You get the same shape back.

## Python integrations

### LangChain chat model

`HeadroomChatModel` wraps any LangChain chat model, such as `ChatOpenAI` or `ChatAnthropic`, and compresses messages on the way out. Everything else about the model stays the same, including `bind_tools(...)`, `stream`, `ainvoke` and `astream`.

```python
from langchain_openai import ChatOpenAI
from headroom import HeadroomConfig, HeadroomMode
from headroom.integrations import HeadroomChatModel

llm = HeadroomChatModel(ChatOpenAI(model="gpt-4o"))
response = llm.invoke("Hello!")
print(llm.get_savings_summary())
# {'total_requests': 1, 'total_tokens_saved': 0, 'average_savings_percent': 0.0,
#  'total_tokens_before': 9, 'total_tokens_after': 9}
# Optional pipeline config
llm = HeadroomChatModel(ChatOpenAI(model="gpt-4o"), config=HeadroomConfig(default_mode=HeadroomMode.OPTIMIZE))
```

### LangChain agents and tool wrapping

`wrap_tools_with_headroom` compresses tool output before it re-enters the agent's context. The wrapped tool keeps its argument schema, so the model sees the same parameters. It also exposes a coroutine, so `await agent.ainvoke(...)` compresses as well.

```python
import json
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from headroom.integrations import HeadroomChatModel, wrap_tools_with_headroom, get_tool_metrics

@tool
def query_database(query: str) -> str:
    """Query the users database. Returns JSON rows."""
    return json.dumps({"results": [...], "total": 300})

llm = HeadroomChatModel(ChatOpenAI(model="gpt-4o-mini"))
tools = wrap_tools_with_headroom([query_database], min_chars_to_compress=1000)
agent = create_agent(llm, tools)
result = agent.invoke({"messages": [("user", "How many users signed up last week?")]})
print(get_tool_metrics().get_summary())
# {'total_invocations': 1, 'total_compressions': 1, 'total_chars_saved': 4202,
#  'average_compression_ratio': 0.901,
#  'by_tool': {'query_database': {'invocations': 1, 'compressions': 1, 'chars_saved': 4202}}}
```

`create_agent` comes from the `langchain` package. LangGraph's `create_react_agent` still works as a drop-in substitute, but it is deprecated as of LangGraph 1.0 and slated for removal in 2.0.

### LangGraph compression node

On the same 300-row JSON tool output of 42,597 characters, the two paths differ a lot:

| Path | Result | Saved |
| --- | ---: | ---: |
| `wrap_tools_with_headroom` | 38,395 chars | 10% |
| `create_compress_tool_messages_node` | 18,390 chars | 57% |

The tool wrapper uses the MCP compressor, which keeps its output parseable as JSON for downstream tool consumers. That rules out schema hoisting, the rewrite that turns 300 repeated objects into one schema line plus comma-separated values (CSV) rows. On an array of similar records, the tool wrapper therefore mostly removes whitespace. The graph node has no such constraint, because only the model reads the value.

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from headroom.integrations.langchain import create_compress_tool_messages_node

graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tools_node)
graph.add_node("compress", create_compress_tool_messages_node(min_tokens_to_compress=100))
graph.add_edge(START, "agent")
graph.add_edge("tools", "compress")   # tools -> compress -> agent
graph.add_edge("compress", "agent")   # plus your usual agent -> tools routing
app = graph.compile()
```

The node rewrites `ToolMessage` content and preserves `tool_call_id`, so the graph stays valid. To compress outside a graph, call the function directly. Messages below the threshold come back unchanged.

```python
from headroom.integrations.langchain import compress_tool_messages
result = compress_tool_messages(state["messages"], min_tokens_to_compress=100)
result.messages             # the rewritten message list
result.messages_compressed  # 1
result.total_tokens_saved   # 6052
```

### LangChain memory

`HeadroomChatMessageHistory` wraps any `BaseChatMessageHistory`. It compresses older turns once the history crosses a token budget and never touches the most recent turns. Use it anywhere LangChain accepts a chat history. A higher `keep_recent_turns` protects more recent context, but it leaves fewer turns to compress.

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from headroom.integrations import HeadroomChatMessageHistory

history = HeadroomChatMessageHistory(
    InMemoryChatMessageHistory(),
    compress_threshold_tokens=4000,   # start compressing above 4K tokens
    keep_recent_turns=5,              # never touch the last 5 turns
)
chain = RunnableWithMessageHistory(llm, lambda session_id: history)
print(history.get_compression_stats())   # compression_count, total_tokens_saved, threshold_tokens, keep_recent_turns
```

### LangChain retriever

`HeadroomDocumentCompressor` scores retrieved documents against the query and keeps the best. Retrieve widely for recall, then narrow for precision. `prefer_diverse=True` adds maximal marginal relevance (MMR)-style diversity. The class is a real `BaseDocumentCompressor`, so you can call `compressor.compress_documents(retrieved_docs, query)` on its own or plug it into `ContextualCompressionRetriever`.

```python
from langchain_classic.retrievers import ContextualCompressionRetriever
from headroom.integrations import HeadroomDocumentCompressor
compressor = HeadroomDocumentCompressor(max_documents=10, min_relevance=0.3, prefer_diverse=True)
base = vectorstore.as_retriever(search_kwargs={"k": 50})
retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=base)
docs = retriever.invoke("What is Python?")   # retrieves 50, returns 10
```

### LiteLLM in the same process

The callback compresses messages in LiteLLM's `async_pre_call_hook`, before they reach any LiteLLM provider. The response comes back unchanged.

```python
import litellm
from headroom.integrations.litellm_callback import HeadroomCallback

litellm.callbacks = [HeadroomCallback()]
# All calls now compressed automatically
response = litellm.completion(model="gpt-4o", messages=[...])
response = litellm.completion(model="bedrock/claude-sonnet", messages=[...])
```

For a LiteLLM Proxy server, add the ASGI middleware, or register the callback in the LiteLLM config file:

```python
from litellm.proxy.proxy_server import app
from headroom.integrations.asgi import CompressionMiddleware
app.add_middleware(CompressionMiddleware)
```

```yaml
# litellm_config.yaml
litellm_settings:
  callbacks: ["headroom.integrations.litellm_callback.HeadroomCallback"]
```

`CompressionMiddleware` works in any ASGI app, such as FastAPI. It intercepts `/v1/messages`, `/v1/chat/completions`, `/v1/responses` and `/chat/completions`. It adds the response headers `x-headroom-compressed: true` and `x-headroom-tokens-saved: 1234`.

Call `compress()` directly when you want to choose which calls to compress, or need a savings figure for each call:

```python
from headroom import compress
compressed = compress(messages, model="bedrock/claude-sonnet")
response = litellm.completion(model="bedrock/claude-sonnet", messages=compressed.messages)
print(f"Saved {compressed.tokens_saved} tokens")
```

### LiteLLM guardrail over the network

When LiteLLM runs as its own proxy and calls Headroom over the network, point it at `POST /v1/compress`. LiteLLM swaps `messages` for the compressed result and forwards the request to the provider. Install the proxy extras and opt in to remote access:

```bash
pip install "headroom-ai[proxy]"
# Headroom is loopback-only by default and answers remote callers with 404.
HEADROOM_COMPRESS_ALLOW_REMOTE=1 headroom proxy
```

- A remote caller without `HEADROOM_COMPRESS_ALLOW_REMOTE=1` gets `404`, not `403`. A blocked guardrail therefore looks exactly like a wrong address.
- If you set `HEADROOM_PROXY_TOKEN`, send it in the `X-Headroom-Proxy-Token` header, or you get `401`.
- Leave `config.mode` unset, because the default pipeline is marker-free. `mode: "ccr"` emits Compress-Cache-Retrieve (CCR) retrieval markers. They dangle unless you also inject the `headroom_retrieve` tool and can reach `/v1/retrieve`.
- Send the real model name, such as `claude-sonnet-4-6`, `bedrock/anthropic.claude-3-5-sonnet` or `gemini-2.5-pro`. Headroom uses it to resolve the right tokenizer and context limit.
- In multi-turn agent loops, set `config.frozen_message_count` to the number of messages the provider has already cached. Send back the messages you forwarded before, not the pristine originals. Getting this wrong silently destroys the provider's prefix cache.

### Agno

`HeadroomAgnoModel` wraps any Agno model. The hooks add tracking without changing the model. `create_headroom_hooks()` is a convenience factory; you can also build `HeadroomPreHook()` and `HeadroomPostHook(token_alert_threshold=10000)` yourself.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from headroom.integrations.agno import HeadroomAgnoModel, create_headroom_hooks

model = HeadroomAgnoModel(wrapped_model=OpenAIChat(id="gpt-4o"))
pre_hook, post_hook = create_headroom_hooks(token_alert_threshold=5000, log_level="DEBUG")
agent = Agent(model=model, pre_hooks=[pre_hook], post_hooks=[post_hook])
response = agent.run("Analyze this large dataset...")
print(model.get_savings_summary())   # same keys as HeadroomChatModel; also model.total_tokens_saved
if post_hook.alerts:
    print(f"{len(post_hook.alerts)} requests exceeded threshold")
model.reset()   # start the next session with fresh metrics
```

- Headroom auto-detects these Agno models: `OpenAIChat`, `OpenAILike`, `Claude`, `AwsBedrock`, `Gemini`, `VertexAI`, `Groq`, `Mistral` and `Ollama`.
- In async code, use `await model.aresponse(messages)` and `async for chunk in model.aresponse_stream(messages)`. Without a model, call `optimized, metrics = optimize_messages(messages, model="gpt-4o")` and read `metrics['tokens_saved']`.

### Strands

Strands offers two patterns, and you get the most savings when you combine them. `HeadroomStrandsModel` wraps the Strands `Model` interface and compresses the full message list, history included, on every `stream()` call. `HeadroomHookProvider` compresses each tool output through Strands' hook system, with SmartCrusher for fast JSON compression. The hook keeps error items, anomalous values (statistical outliers), items that match the query context, and the first and last items.

```python
from strands import Agent
from strands.models.bedrock import BedrockModel
from headroom import HeadroomConfig
from headroom.integrations.strands import HeadroomStrandsModel, HeadroomHookProvider

model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")
optimized = HeadroomStrandsModel(wrapped_model=model, config=HeadroomConfig())
hooks = HeadroomHookProvider(compress_tool_outputs=True, min_tokens_to_compress=200, preserve_errors=True)
agent = Agent(model=optimized, hooks=[hooks])
response = agent("Investigate the production incident")
print(f"Model wrapper saved: {optimized.total_tokens_saved}, hooks saved: {hooks.total_tokens_saved}")
for m in optimized.metrics_history:
    print(f"  {m.tokens_before} -> {m.tokens_after} ({m.tokens_saved} saved)")
```

### CrewAI and AutoGen

Both integrations wrap tools. Each tool output longer than `min_chars_to_compress` (default 1000) goes through Headroom's `compress_tool_result()` before it enters the agent's context. The wrapper keeps the tool's name, description and argument schema, so it is a drop-in replacement.

```python
# CrewAI
import json
from crewai import Agent, Crew, Task
from crewai.tools.base_tool import tool
from headroom.integrations.crewai import HeadroomToolWrapper, wrap_tools_with_headroom

@tool
def search_database(query: str) -> str:
    """Search the database and return results."""
    return json.dumps({"results": [...], "total": 1000})

tools = wrap_tools_with_headroom([search_database], min_chars_to_compress=500)
# One tool at a time: the wrapper is itself a BaseTool
# tools = [HeadroomToolWrapper(search_database, min_chars_to_compress=500)]
agent = Agent(role="Researcher", goal="Answer questions using data", backstory="You research things.", tools=tools)
task = Task(description="Find all active users", agent=agent, expected_output="Summary")
Crew(agents=[agent], tasks=[task]).kickoff()
```

```python
# AutoGen (autogen-agentchat 0.7 or later); the tool function can be sync or async
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from headroom.integrations.autogen import HeadroomToolWrapper, wrap_tools_with_headroom
tool = FunctionTool(search_database, description="Search the database")
tools = wrap_tools_with_headroom([tool])
# One tool at a time: ask the wrapper for a FunctionTool
# tools = [HeadroomToolWrapper(tool, min_chars_to_compress=500).as_function_tool()]
agent = AssistantAgent(name="researcher", model_client=model_client, tools=tools)
```

CrewAI's wrapper subclasses `BaseTool` and overrides `_run()` around the original `run()`. AutoGen's wrapper builds a new `FunctionTool` around the original function and measures the stringified return value. Both modules expose the same metrics helpers:

```python
# Same names in headroom.integrations.autogen
from headroom.integrations.crewai import ToolMetricsCollector, get_tool_metrics, reset_tool_metrics, wrap_tools_with_headroom
print(get_tool_metrics().get_summary())   # global totals plus a by_tool breakdown
reset_tool_metrics()                      # clear the global counters between sessions
collector = ToolMetricsCollector()        # isolated counters for one crew or agent
wrapped = wrap_tools_with_headroom([search_database], metrics_collector=collector)
print(collector.get_summary())
```

The LangChain page shows that its JSON-preserving tool wrapper saves little on uniform arrays. The CrewAI and AutoGen pages do not say whether `compress_tool_result()` shares that constraint, so check `get_tool_metrics()` before you rely on a figure.

## What gets compressed

| Integration point | Compresses | Leaves alone |
| --- | --- | --- |
| TypeScript client wrappers | `messages` in `chat.completions.create()` or `messages.create()`, including tool calls and tool output | Every other client method |
| Vercel model wrapper and middleware | The prompt messages before each model call | Tool calling, structured output, streaming |
| Python model wrappers (LangChain, Agno, Strands) | The full message list on every call | – |
| Tool wrappers (LangChain, CrewAI, AutoGen) | Each tool output above `min_chars_to_compress` | Shorter output; tool name, description and schema |
| Strands hook | JSON arrays in tool output above `min_tokens_to_compress` | Errors, outliers, query matches, first and last items |
| LangGraph node | `ToolMessage` content above `min_tokens_to_compress` | `tool_call_id`; messages below the threshold |
| `HeadroomChatMessageHistory` | Older turns once history passes `compress_threshold_tokens` | The last `keep_recent_turns` turns |
| `HeadroomDocumentCompressor` | The document list, cut to the most relevant | – |
| LiteLLM callback and ASGI middleware | Messages before they reach the provider | The response |

## Reading metrics

| Where | How to read it | Unit |
| --- | --- | --- |
| `compressVercelMessages()` (TypeScript) | `result.tokensSaved` | Tokens |
| `compress()` (Python) | `compressed.tokens_saved` | Tokens |
| `CompressionMiddleware` | Response headers `x-headroom-compressed` and `x-headroom-tokens-saved` | Tokens |
| `HeadroomChatModel`, `HeadroomAgnoModel` | `get_savings_summary()` | Tokens |
| `HeadroomAgnoModel`, `HeadroomStrandsModel`, `HeadroomHookProvider` | `total_tokens_saved` | Tokens |
| `HeadroomStrandsModel` | `metrics_history`, each entry with `tokens_before`, `tokens_after`, `tokens_saved` | Tokens |
| `optimize_messages()` (Agno) | `metrics['tokens_saved']` | Tokens |
| `compress_tool_messages()` | `result.total_tokens_saved`, `result.messages_compressed` | Tokens |
| `HeadroomChatMessageHistory` | `get_compression_stats()` | Tokens |
| Tool wrappers (LangChain, CrewAI, AutoGen) | `get_tool_metrics().get_summary()`; CrewAI and AutoGen also offer `collector.get_summary()` | Characters |

- Do not add tool metrics to the other counters. Tool wrappers count characters (`total_chars_saved`), while everything else counts tokens.
- Read `average_compression_ratio` as output size over input size, so lower means more compression. The LangChain example reports 0.901 next to 4,202 characters saved, which matches the 10% row above (42,597 → 38,395 characters).
- Counters accumulate. Reset them between sessions with `model.reset()` (Agno) or `reset_tool_metrics()` (CrewAI, AutoGen). A separate `ToolMetricsCollector` for each run keeps runs apart without a global reset.
- The `withHeadroom()` pages for OpenAI, Anthropic and Vercel document no savings counter. In Vercel code, use `compressVercelMessages()` when you need a figure for each call. For proxy-side tracking, see [observability](./observability.md).

## Configuring compression

| Setting | Where | What it controls |
| --- | --- | --- |
| `model`, `baseUrl` | Options of `withHeadroom()` and `headroomMiddleware()`; `compressVercelMessages()` takes `model` | The target model name, and the proxy address (`http://localhost:8787` in the examples) |
| `config=HeadroomConfig(...)` | `HeadroomChatModel`, `HeadroomStrandsModel` | Pipeline settings, for example `default_mode=HeadroomMode.OPTIMIZE` |
| `min_chars_to_compress` | `wrap_tools_with_headroom`, `HeadroomToolWrapper` | The shortest tool output that gets compressed (default 1000 on the CrewAI and AutoGen pages) |
| `min_tokens_to_compress` | `create_compress_tool_messages_node`, `compress_tool_messages`, `HeadroomHookProvider` | The smallest content that gets compressed, in tokens |
| `compress_threshold_tokens`, `keep_recent_turns` | `HeadroomChatMessageHistory` | When history compression starts, and how many recent turns stay intact |
| `max_documents`, `min_relevance`, `prefer_diverse` | `HeadroomDocumentCompressor` | How many documents survive, the relevance floor, and diversity |
| `config.mode`, `config.frozen_message_count` | Guardrail requests to `POST /v1/compress` | CCR markers (leave `mode` unset) and prefix-cache protection |

These pages document no flag that turns compression off for a single call. For per-request overrides, see [configuration](./configuration.md). Within these pages, use one of these routes:

- Rely on the thresholds. Content below a threshold passes through unchanged.
- Use a standalone function for per-call control. `compress()`, `compressVercelMessages()`, `optimize_messages()` and `compress_tool_messages()` compress only what you pass them.
- Keep the unwrapped original. Each wrapper returns a new object around your client or model, so call the original for requests you want to send as they are.

## Do this, not that

| Do this | Not this | Why |
| --- | --- | --- |
| Use `create_compress_tool_messages_node` when only the model reads tool output | Rely on `wrap_tools_with_headroom` to shrink large uniform JSON arrays | The JSON-preserving tool wrapper saved 10% where the node saved 57% |
| Use `wrap_tools_with_headroom` when downstream code parses the tool output | Put the graph node in front of a JSON consumer | The node may rewrite JSON into a schema line plus CSV rows |
| Combine `HeadroomStrandsModel` with `HeadroomHookProvider` | Expect the hook alone to shrink conversation history | The model wrapper covers history; the hook covers individual tool output |
| Pass `headroomMiddleware()` to `wrapLanguageModel` when you compose middleware | Reach for `withHeadroom()` when you also need other middleware | The docs name the middleware as the composition route; `withHeadroom()` is the one-liner for the plain case |
| Retrieve widely (`k=50`) and narrow with `HeadroomDocumentCompressor` | Retrieve only the final few documents | Wide retrieval protects recall; the compressor restores precision |
| Wrap the AutoGen tool function | Compress through `tool_call_summary_formatter` | It only shapes the final summary and never reaches the `FunctionExecutionResult` in `model_context` |
| Route Claude Code over native Anthropic transport | Route Claude Code through LiteLLM | Claude Code may fall back to its billable client-side auto-mode classifier |

## Pitfalls by integration

- **All TypeScript wrappers:** The Headroom proxy must be running. A remote proxy without `HEADROOM_COMPRESS_ALLOW_REMOTE=1` answers `404`, which looks like a wrong address rather than a block.
- **OpenAI and Anthropic SDKs:** Only `chat.completions.create()` and `messages.create()` are compressed; other methods go out unchanged. When you call `/v1/compress` yourself, do not convert Anthropic messages to OpenAI format first, because the endpoint handles Anthropic blocks natively.
- **LangChain:** Zero savings on short prompts is expected. Most classes import from `headroom.integrations`, but the graph node and `compress_tool_messages` import from `headroom.integrations.langchain`. The page documents `get_tool_metrics()` but no reset helper.
- **LiteLLM:** The callback is not the Headroom proxy's `--backend vertex_ai` / `bedrock` option, which makes the proxy call cloud providers through LiteLLM. Schema-translating routes such as LiteLLM are not claimed to preserve Claude Code's server-side auto-mode classifier protocol, although requests still fail open as ordinary model traffic.
- **Agno:** `total_tokens_saved` and `get_savings_summary()` keep accumulating until you call `model.reset()`.
- **Strands:** `structured_output()` is an async generator that delegates to the wrapped model. Consume it with `async for event in optimized.structured_output(Analysis, messages)`, not `await`. Provider detection covers `BedrockModel` (Anthropic via Bedrock) and `OllamaModel` (OpenAI-compatible); a custom `Model` falls back to estimation.
- **CrewAI:** `HeadroomToolWrapper` is already a `BaseTool`, so pass it directly. The threshold counts characters, not tokens.
- **AutoGen:** You need `autogen-agentchat` 0.7 or later. `HeadroomToolWrapper` is not a tool, so pass `wrapper.as_function_tool()`.
- **Across frameworks:** `wrap_tools_with_headroom` exists in `headroom.integrations`, `headroom.integrations.crewai` and `headroom.integrations.autogen`. Import the one for your framework, because each produces that framework's tool type.

LangChain 1.0 removed several modules that older Headroom docs used. Headroom's own classes kept the same arguments. The LangChain page was verified against langchain-core 1.6.1, langchain 1.3.18 and langgraph 1.2.11.

| Removed in LangChain 1.0 | Use instead |
| --- | --- |
| `langchain.memory.ConversationBufferMemory` | `RunnableWithMessageHistory`, or a LangGraph checkpointer |
| `langchain_community.chat_message_histories.ChatMessageHistory` | `langchain_core.chat_history.InMemoryChatMessageHistory` |
| `langchain.retrievers.ContextualCompressionRetriever` | The same class, now in `langchain-classic` |
| `langchain.agents.create_openai_tools_agent` + `AgentExecutor` | `langchain.agents.create_agent` |
| `langchain_community.vectorstores.*` | Provider packages, or `langchain_core.vectorstores.InMemoryVectorStore` for tests |

## Related skills

- [getting-started](./getting-started.md) – installation and extras, including the `headroom-ai[proxy]` install that the TypeScript wrappers depend on.
- [compression](./compression.md) – the pipeline these integrations call: ContentRouter, CacheAligner, SmartCrusher and the type-specific compressors.
- [ccr-and-caching](./ccr-and-caching.md) – CCR markers, `headroom_retrieve`, and keeping the provider's prefix cache intact with `frozen_message_count`.
- [memory](./memory.md) – Headroom's persistent memory and SharedContext, which are separate from `HeadroomChatMessageHistory`.
- [proxy](./proxy.md) – `POST /v1/compress`, its message format, remote access, proxy tokens and the `--backend` options.
- [coding-agents](./coding-agents.md) – Claude Code and other coding agents; read it before you route Claude Code through LiteLLM.
- [configuration](./configuration.md) – `HeadroomConfig`, modes, per-request overrides and environment variables.
- [observability](./observability.md) – savings tracking and metrics beyond the counters each integration exposes.
- [sdk-reference](./sdk-reference.md) – full Python and TypeScript signatures, including `compress()`, and error handling.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – symptoms such as a `404` from `/v1/compress`, and safety limits.
- [architecture-and-security](./architecture-and-security.md) – how the SDKs, proxy and pipeline fit together, and the security model.

## Source pages

- https://docs.headroomlabs.ai/docs/vercel-ai-sdk
- https://docs.headroomlabs.ai/docs/openai-sdk
- https://docs.headroomlabs.ai/docs/anthropic-sdk
- https://docs.headroomlabs.ai/docs/langchain
- https://docs.headroomlabs.ai/docs/litellm
- https://docs.headroomlabs.ai/docs/agno
- https://docs.headroomlabs.ai/docs/strands
- https://docs.headroomlabs.ai/docs/crewai
- https://docs.headroomlabs.ai/docs/autogen
