# Headroom: Memory and shared context
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Headroom keeps context small across time and across agents with three features: persistent memory, SharedContext and failure learning. This skill shows you when to use each one, how to call it correctly and which pitfalls to avoid. It also explains how the three relate to compression and to Compress-Cache-Retrieve (CCR).

## Choose the right feature

| Feature | Problem it solves | Where the data lives | Interface |
| --- | --- | --- | --- |
| Persistent memory | Every conversation starts from zero, and long history overflows the context window | Embedded SQLite memory store with vector and full-text indexes | Python: `with_memory()`, `HierarchicalMemory` |
| SharedContext | Agent handoffs replay large outputs in full | Process memory, until an entry expires or is evicted | Python and TypeScript: `SharedContext` |
| Failure learning | Coding agents repeat the same failed reads, searches and commands | Markdown context files: `CLAUDE.local.md`, `MEMORY.md` or a `--target` file | Command line: `headroom learn` |

- Use persistent memory when users return and the model should recall their preferences, facts and decisions. The cost is 50–100 extra response tokens per call for the extraction block.
- Use SharedContext when one agent passes a large output to another agent in the same run. The trade-off is that the original lives only in process memory and expires.
- Use failure learning once a coding agent has past sessions on a project. It writes files that steer later sessions, so preview its output before you apply it.

## Core concepts

- **Temporal compression.** Persistent memory replaces conversation history with extracted facts. The docs' example carries 100 tokens of memories instead of 10,000 tokens of history.
- **Inline extraction.** The large language model (LLM) writes a `<memory>` block as part of its normal response. Headroom parses, stores and strips that block, so extraction needs no extra request.
- **Hierarchical scopes.** Each memory lives at user, session, agent or turn scope, from broadest to narrowest.
- **Supersession chains.** A changed fact supersedes the old memory instead of overwriting it. Queries return the current fact, and the chain keeps the history.
- **Compressed by default, original on demand.** SharedContext hands out the compressed version of an entry unless you ask for the original.
- **Success correlation.** `headroom learn` pairs each failure with what the model did to fix it. That yields specific corrections such as "`FirstClassEntity` is at `axion-scala-common/`, not `axion-formats/`", not generic advice.

## Persistent memory

### Wrap an OpenAI-compatible client

`with_memory()` wraps an OpenAI-compatible client and intercepts every chat completion call. You keep using the client as before.

```python
from openai import OpenAI
from headroom import with_memory

client = with_memory(OpenAI(), user_id="alice")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "I prefer Python for backend work"}]
)
# The preference is extracted inline, as part of this response.

# Later, in a new conversation:
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What language should I use?"}]
)
# The response uses the stored Python preference.
```

On each call, the wrapper runs six steps:

1. **Inject** – semantic search finds relevant memories and prepends them to the user message.
2. **Instruct** – the wrapper adds a memory extraction instruction to the system prompt.
3. **Call** – the wrapper forwards the request to the LLM.
4. **Parse** – the wrapper extracts the `<memory>` block from the response.
5. **Store** – the wrapper saves the memory with embeddings, a vector index and a full-text search index.
6. **Return** – the wrapper strips the memory block and returns the clean response.

The wrapper works with any OpenAI-compatible client. The docs show OpenAI, Azure OpenAI and Groq. They show Python only, with no TypeScript equivalent of `with_memory()`.

```python
client = with_memory(OpenAI(base_url="https://your-resource.openai.azure.com/..."), user_id="alice")  # Azure OpenAI
client = with_memory(Groq(), user_id="alice")  # Groq: from groq import Groq
```

### Scope memories by user and session

| Scope | Persists across | Use for |
| --- | --- | --- |
| User | All sessions, all time | Long-term preferences, identity |
| Session | Current session only | Current task context |
| Agent | Current agent in the session | Agent-specific context |
| Turn | A single turn only | Ephemeral working memory |

Reuse the same `user_id` for a person in every session, so user-level memories follow them. Give each conversation its own `session_id`, so session context stays in its session.

```python
# Session 1: "I prefer Go for performance-critical code" is stored at user level.
client1 = with_memory(OpenAI(), user_id="bob", session_id="morning-session")

# Session 2, same user: "What language for my new microservice?" recalls the Go preference.
client2 = with_memory(OpenAI(), user_id="bob", session_id="afternoon-session")
```

### Read and write memories directly

The wrapped client exposes a `.memory` attribute.

```python
client = with_memory(OpenAI(), user_id="alice")

results = client.memory.search("python preferences", top_k=5)  # semantic search
for memory in results:
    print(memory.content)

client.memory.add("User is a senior engineer", importance=0.9)  # add by hand
all_memories = client.memory.get_all()  # all memories for this user
stats = client.memory.stats()           # returns only {"total": N}
print(f"Total memories: {stats['total']}")
client.memory.clear()                   # clears all memories
```

### Tag memories with a category

`Memory` has no `category` field, and `add()` has no `category` parameter. Store a free-form category in the `metadata` dict instead. Headroom's own examples use these conventional values: `"preference"` (likes, dislikes, preferred approaches), `"fact"` (identity, role, constraints), `"context"` (current goals, ongoing tasks), `"entity"` (information about entities), `"decision"` (decisions made) and `"insight"` (derived insights).

```python
# memory = await HierarchicalMemory.create()  (see the next section)

# Don't: add() has no category keyword.
await memory.add(content="User works at Google", user_id="alice", category="fact")

# Do: put the category in metadata.
await memory.add(content="User works at Google", user_id="alice", metadata={"category": "fact"})
```

### Version facts that change

Use `HierarchicalMemory` when you manage memories yourself. When a fact changes, call `supersede()`. It links the old and new memories in a supersession chain and marks only the new one as current.

```python
from headroom.memory import HierarchicalMemory, MemoryFilter

# Await these calls inside an async function.
memory = await HierarchicalMemory.create()

orig = await memory.add(
    content="User works at Google",
    user_id="alice",
    metadata={"category": "fact"},
)

# The user changes jobs: supersede the old memory.
new = await memory.supersede(
    old_memory_id=orig.id,
    new_content="User now works at Anthropic",
)

# Current state only; superseded memories are excluded by default.
current = await memory.query(MemoryFilter(
    user_id="alice",
    include_superseded=False,
))
# Returns only "User now works at Anthropic"

# The full chain
chain = await memory.get_history(new.id)
# [
#   Memory(content="User works at Google", is_current=False),
#   Memory(content="User now works at Anthropic", is_current=True),
# ]
```

- **Do:** call `supersede()` when a fact changes. Default queries then return only the current fact, and `get_history()` still shows what changed.
- **Don't:** record a change as a second `add()`. Only `supersede()` is documented to mark the old memory as no longer current.

The chain gives you an audit trail, a way to debug why the LLM made a decision, and a point to roll back to.

### Configure embeddings and storage

`MemoryConfig` selects the embedder and tunes storage. The docs recommend the Open Neural Network Exchange (ONNX) backend.

```python
from headroom.memory import MemoryConfig, EmbedderBackend

# ONNX embeddings (recommended -- fast, free, private; ~30 MB int8-quantized)
config = MemoryConfig(
    embedder_backend=EmbedderBackend.ONNX,
    embedder_model="BAAI/bge-small-en-v1.5",
)
```

| Backend | Settings from the docs | Trade-off |
| --- | --- | --- |
| `EmbedderBackend.ONNX` | `embedder_model="BAAI/bge-small-en-v1.5"` | Recommended: fast, free and private; the int8-quantized model is about 30 MB |
| `EmbedderBackend.OPENAI` | `openai_api_key="sk-..."`, `embedder_model="text-embedding-3-small"` | Higher quality, but costs money |
| `EmbedderBackend.OLLAMA` | `ollama_base_url="http://localhost:11434"`, `embedder_model="nomic-embed-text"` | Local Ollama server with many models |
| `EmbedderBackend.LOCAL` | – | Requires PyTorch (about 2 GB); use ONNX instead |

Storage is embedded, so you run no external services. SQLite handles create, read, update, delete and filtering. A Hierarchical Navigable Small World (HNSW) index handles vector similarity search. SQLite's FTS5 full-text search module handles keyword search. The docs show these tuning settings as examples, not as defaults:

```python
config = MemoryConfig(
    db_path="memory.db",
    vector_dimension=384,
    hnsw_ef_construction=200,
    hnsw_m=16,
    hnsw_ef_search=50,
    cache_enabled=True,
    cache_max_size=1000,
)
```

### Offload the proxy's embedder on Apple Silicon

By default, the proxy's memory embedder runs on the ONNX central processing unit (CPU) backend. Under sustained load, embedding can saturate the CPU and make the proxy less responsive. On Apple Silicon, you can move the embedder to the Apple graphics processing unit (GPU) through Metal Performance Shaders (MPS).

```bash
pip install "headroom-ai[pytorch-mps]"   # also works as [pytorch_mps]
export HEADROOM_EMBEDDER_RUNTIME=pytorch_mps
```

- `pytorch_mps` is the only accepted value. Any other value, or no value, keeps the default ONNX CPU embedder.
- The environment variable is the only switch. There is no command-line flag.
- MPS activates only on Apple Silicon with torch installed. If MPS, torch or sentence-transformers is unavailable, Headroom logs a warning and falls back to ONNX when available, then to the local sentence-transformers fallback.
- torch-MPS is not thread-safe, so Headroom serializes MPS encode calls through a single-worker executor. You configure nothing.

The package extra accepts a hyphen or an underscore, but the variable accepts only the underscore:

```bash
# Don't: an unrecognized value keeps the default ONNX CPU embedder.
export HEADROOM_EMBEDDER_RUNTIME=pytorch-mps

# Do:
export HEADROOM_EMBEDDER_RUNTIME=pytorch_mps
```

After you switch, check the logs for the fallback warning, because a fallback means the GPU offload is not active.

### Performance budget

| Operation | Cost | Notes |
| --- | --- | --- |
| Memory injection | Under 50 ms | Local embeddings and HNSW search |
| Memory extraction | 50–100 extra tokens | Part of the LLM response (inline) |
| Memory storage | Under 10 ms | SQLite, HNSW and FTS5 indexing |
| Cache hit | Under 1 ms | Least recently used (LRU) cache lookup |

### Persistent memory pitfalls

- **Guessing scope keywords.** The docs show `user_id` and `session_id` on `with_memory()` and no keyword for agent or turn scope. Check the installed signature before you pass anything else.
- **Parsing the `<memory>` block.** The wrapper strips the block before it returns the response. Read stored memories through `client.memory` instead.
- **Expecting category counts.** `stats()` returns only `{"total": N}`, with no per-category breakdown.
- **Assuming `MemoryConfig` wiring.** The memory page builds `MemoryConfig` objects but never shows the call that receives one. Check the installed signatures, for example with `help(HierarchicalMemory.create)`, before you rely on a keyword.
- **Choosing the heavy local backend.** `EmbedderBackend.LOCAL` pulls in PyTorch at about 2 GB. ONNX is also free and private, at about 30 MB.

## SharedContext

SharedContext compresses what moves between agents. The docs report about 80% fewer tokens on typical agent handoffs.

### Hand off a large output

```typescript
import { SharedContext } from "headroom-ai";

const ctx = new SharedContext();
const entry = await ctx.put("research", bigResearchOutput, { agent: "researcher" }); // Agent A stores
const summary = ctx.get("research");               // Agent B: compressed version
const full = ctx.get("research", { full: true });  // Agent B: original, on demand
```

```python
from headroom import SharedContext

ctx = SharedContext()
ctx.put("research", big_research_output, agent="researcher")  # Agent A stores
summary = ctx.get("research")                # Agent B: compressed version
full = ctx.get("research", full=True)        # Agent B: original, on demand
```

Share one `SharedContext` instance between the agents, so every agent reads the entries the others stored. Pass the compressed version by default, and request the original only in the step that needs the details. Most handoffs stay small, and the original stays available until it expires or is evicted.

### Python and TypeScript names

| Purpose | Python | TypeScript |
| --- | --- | --- |
| Store an entry | `entry = ctx.put(key, content, agent="researcher")` | `const entry = await ctx.put(key, content, { agent: "researcher" })` |
| Read the compressed version | `ctx.get(key)` | `ctx.get(key)` |
| Read the original | `ctx.get(key, full=True)` | `ctx.get(key, { full: true })` |
| Missing key | Returns `None` | Returns `null` |
| Capacity option | `max_entries=100` | `maxEntries: 100` |
| Entry fields returned by `put()` | `original_tokens`, `compressed_tokens`, `savings_percent`, `transforms` | `originalTokens`, `compressedTokens`, `savingsPercent`, `transforms` |
| Totals from `ctx.stats()` | `entries`, `total_original_tokens`, `total_compressed_tokens`, `total_tokens_saved`, `savings_percent` | `entries`, `totalOriginalTokens`, `totalCompressedTokens`, `totalTokensSaved`, `savingsPercent` |

`keys()` lists all non-expired keys, and `clear()` removes all entries. A `transforms` value looks like `["router:json:0.20"]`. The docs' example entry goes from 20000 to 4000 tokens, a `savings_percent` of 80.0.

### Configure lifetime and capacity

```typescript
const ctx = new SharedContext({
  model: "claude-sonnet-4-5-20250929",  // For token counting
  ttl: 3600,                             // 1 hour (default)
  maxEntries: 100,                       // Evicts oldest when full
});
```

```python
ctx = SharedContext(
    model="claude-sonnet-4-5-20250929",  # For token counting
    ttl=3600,                             # 1 hour (default)
    max_entries=100,                      # Evicts oldest when full
)
```

- `model` is the model used for token counting. Set it to the model that reads the handoff, so the token figures match that model.
- Entries expire after `ttl` seconds. The default is 3600, which is 1 hour.
- When SharedContext reaches `max_entries` (`maxEntries` in TypeScript), it evicts the oldest entry. The docs' example uses 100 and states no default.

### Framework patterns

SharedContext is framework-agnostic. It works anywhere context moves between agents.

For LangGraph, keep the compressed version in graph state and fetch the original in the node that needs it.

```python
from headroom import SharedContext

ctx = SharedContext()

def researcher_node(state):
    result = do_research()
    ctx.put("research", result)
    return {"research_summary": ctx.get("research")}

def coder_node(state):
    # Compressed summary in state, full details on demand
    full = ctx.get("research", full=True)
    return {"code": write_code(full)}
```

For CrewAI, store the finished task's raw output and give the next task the compressed version.

```python
ctx.put("findings", researcher_task.output.raw)
coder_context = ctx.get("findings")
```

For the OpenAI Agents SDK, compress large messages in a handoff input filter. The example compresses only messages longer than 1000 characters. Keep a threshold like that, because short messages have little to remove.

```python
def compress_handoff(messages):
    for msg in messages:
        if len(msg.content) > 1000:
            ctx.put(msg.id, msg.content)
            msg.content = ctx.get(msg.id)
    return messages

handoff(agent=coder, input_filter=compress_handoff)
```

### SharedContext pitfalls

- **Forgetting `await` in TypeScript.** TypeScript's `put()` is awaited, but `get()` is not. Python's `put()` and `get()` are both synchronous. Without `await`, you hold a promise instead of an entry.
- **Ignoring missing entries.** `get()` returns `None` or `null` for a key it does not hold. Entries expire after `ttl`, and the oldest one is evicted at capacity, so check the result before you pass it on. If a pipeline can wait more than an hour between `put()` and `get()`, raise `ttl`.
- **Treating it as durable storage.** The original lives in process memory. Use SharedContext as a short-lived handoff buffer, and use persistent memory for facts that must outlive the run.
- **Assuming text always shrinks.** The router sends text to Kompress or passes it through unchanged. Check `transforms` and `savings_percent` before you count on savings for plain text.

## Failure learning

`headroom learn` analyzes past coding agent sessions. It finds what went wrong, correlates each failure with what eventually worked, and writes project-level learnings that prevent the same mistakes next session.

### Run the analysis

```bash
# See recommendations for the current project (dry run, no changes)
headroom learn

# Write recommendations to CLAUDE.local.md and MEMORY.md
headroom learn --apply

# Analyze a specific project
headroom learn --project ~/my-project --apply

# Analyze all discovered projects
headroom learn --all --apply

# Write to the team-shared CLAUDE.md instead of CLAUDE.local.md
headroom learn --apply --target CLAUDE.md

# Preview learnings from another agent's sessions
headroom learn --agent codex
```

Start with the dry run, because it shows the real counts for your project and changes nothing. The docs publish no typical figures, so measure on your own history.

| Option | Default | Effect |
| --- | --- | --- |
| `--apply` | Dry run | Write the recommendations |
| `--project PATH` | Current directory | Project directory to analyze |
| `--all` | – | Analyze all discovered projects |
| `--target TEXT` | `CLAUDE.local.md` | Context file to write to, for Claude Code only. Relative to the project root, or absolute |
| `--agent TEXT` | – | Agent to analyze, for example `claude`, `codex`, `gemini` or `opencode` |
| `--model TEXT` | – | LLM model to use for the analysis |
| `--workers INT` | – | Number of parallel workers |

A dash (–) means the docs state no default.

### What it learns

| Learning | Example from the docs |
| --- | --- |
| Environment facts: which runtime commands work or fail | Use `uv run python`, not `python3`, because modules are not available outside the virtual environment |
| File path corrections: wrong paths the model keeps guessing | `axion-common/src/.../AxionSparkConstants.scala` is actually at `axion-spark-common/src/.../AxionSparkConstants.scala` |
| Search scope: which directories to search | Don't search `axion-model/`; use `axion/`, the repository root |
| Command patterns: how commands should and should not run | The user rejected gradle 18 times, so show the command instead of running it |
| Known large files: files that need `offset`/`limit` with Read | `proxy/server.py` (about 8000 lines) |

### Where learnings go

| Pattern | Destination | Why |
| --- | --- | --- |
| Environment, paths, search scope, commands, large files | `CLAUDE.local.md` in the project directory | Personal, machine-specific facts belong in a gitignored file |
| Missing paths, retry patterns, permissions | `MEMORY.md` in `~/.claude/projects/*/memory/` | These may change and are agent-specific |

`CLAUDE.local.md` is the personal local memory file in Claude Code's memory convention. `MEMORY.md` is a Markdown file for the coding agent, not the SQLite memory store that persistent memory uses.

### Keep machine-specific learnings out of the team file

- **Do:** keep the default target and list `CLAUDE.local.md` in `.gitignore`. Absolute paths and tool-discovery byproducts then stay out of the shared repository.
- **Don't:** pass `--target CLAUDE.md` when the learnings include machine-specific paths. They would pollute the team-shared file.

```gitignore
CLAUDE.local.md
```

Pass `--target CLAUDE.md` only to opt into the shared file on purpose. Pass `--target <path>` for any custom location.

If an older Headroom version wrote a learned-patterns block into your team-shared `CLAUDE.md`, the next `headroom learn --apply` moves it into `CLAUDE.local.md` and prints a warning. If `CLAUDE.md` contained nothing but that block, Headroom removes the file entirely. Review the diff before you commit.

### Leave the managed block to Headroom

Headroom manages a delimited section in each file it writes:

```markdown
<!-- headroom:learn:start -->
## Headroom Learned Patterns
*Auto-generated by `headroom learn` -- do not edit manually*
...
<!-- headroom:learn:end -->
```

On re-run, Headroom replaces only the content between the markers and preserves the rest of the file. Write your own notes outside the markers, because the next `--apply` replaces anything inside them.

### Support another agent

`headroom learn` uses adapters, so one set of analyzers serves every agent system:

- **Scanners** read a tool's log format, such as `~/.claude/projects/*.jsonl`, and produce normalized `ToolCall` sequences.
- **Analyzers** work on `ToolCall` data, with the same logic for any agent system.
- **Writers** output to the tool's context injection mechanism, such as `CLAUDE.md`.

To add an agent such as Cursor, write a Scanner for its log format and a Writer that outputs to `.cursorrules`. The analyzers stay the same. Note that `--target` applies to Claude Code only.

## How the features relate to compression and CCR

- **SharedContext runs the compression pipeline.** `put()` calls `headroom.compress()`, the same pipeline the Headroom proxy uses. JavaScript Object Notation (JSON) arrays go to SmartCrusher (70–95% compression). The SharedContext page says code goes to the abstract syntax tree (AST)-aware code compressor, but the more specific code-compression page says library `compress()` sends code to Kompress unless you enable code-aware routing. Text goes to Kompress (ModernBERT-based) or passes through. See [compression](./compression.md).
- **SharedContext keeps its own originals.** It stores each original in process memory and returns it from `get(key, full=True)`. The SharedContext docs describe no retrieval path for the model, so your orchestration code fetches the original. For CCR, Headroom's reversible compression, see [CCR and caching](./ccr-and-caching.md).
- **Persistent memory compresses across time.** It replaces history with extracted memories instead of compressing individual payloads. The proxy runs its own memory embedder, which the Apple Silicon offload above applies to. See [proxy](./proxy.md).
- **Failure learning works offline.** It reads past session logs and writes context files that the agent reads in later sessions. It prevents repeated mistakes, such as guessing a wrong path or reading a known large file without `offset`/`limit`.

## Quick reference

| Task | Call |
| --- | --- |
| Give an OpenAI-compatible client memory (Python) | `client = with_memory(OpenAI(), user_id="alice")` |
| Search a user's memories (Python) | `client.memory.search("python preferences", top_k=5)` |
| Replace a changed fact (Python) | `await memory.supersede(old_memory_id=orig.id, new_content="...")` |
| Hand off an output (Python) | `ctx.put("research", output, agent="researcher")` |
| Hand off an output (TypeScript) | `await ctx.put("research", output, { agent: "researcher" })` |
| Read the original (Python / TypeScript) | `ctx.get("research", full=True)` / `ctx.get("research", { full: true })` |
| Preview learnings (command line) | `headroom learn` |
| Write learnings to the team file (command line) | `headroom learn --apply --target CLAUDE.md` |
| Run the proxy's embedder on the Apple GPU | `export HEADROOM_EMBEDDER_RUNTIME=pytorch_mps` |

## Related skills

- [Getting started](./getting-started.md) – overview, installation, Docker-native wrapper, persistent installs and Teams.
- [Compression](./compression.md) – the pipeline SharedContext calls, including SmartCrusher and the code and text compressors.
- [CCR and caching](./ccr-and-caching.md) – reversible compression, cache optimization, context management and agent orchestration.
- [Proxy](./proxy.md) – the proxy server, its options and endpoints, and agent wrapping.
- [Framework integrations](./framework-integrations.md) – CrewAI, LangChain and LangGraph, and other frameworks you can pair with SharedContext.
- [Coding agents](./coding-agents.md) – Claude Code, OpenCode and other agents whose sessions `headroom learn` analyzes.
- [Configuration](./configuration.md) – SDK and proxy configuration, environment variables and the filesystem contract.
- [Observability](./observability.md) – savings tracking, metrics and simulation.
- [SDK reference](./sdk-reference.md) – Python and TypeScript reference and error handling.
- [Troubleshooting and limits](./troubleshooting-and-limits.md) – troubleshooting by symptom, limitations and safety gates.
- [Architecture and security](./architecture-and-security.md) – architecture, security model, benchmarks and runtime rollouts.

## Source pages

- [Persistent Memory](https://docs.headroomlabs.ai/docs/memory)
- [SharedContext](https://docs.headroomlabs.ai/docs/shared-context)
- [Failure Learning](https://docs.headroomlabs.ai/docs/failure-learning)
