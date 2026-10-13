# Headroom: Observability
Based on Headroom documentation as of 2026-10-13 (headroom-ai 0.40.0).

Use this skill to measure what Headroom saves, monitor the proxy, cap spend, and preview compression before you turn it on. It covers the `headroom savings` command, the proxy's stats and Prometheus endpoints, OpenTelemetry export, the metrics APIs in both software development kits (SDKs), and simulation.

## Core concepts

- **Tokens saved** is tokens before compression minus tokens after. The log line `45000 -> 4500 tokens (saved 40500, 90.0% reduction)` shows the relationship.
- **Savings percentage** is tokens saved ÷ tokens before × 100. The `headroom savings` report, the pipeline logs and the Python examples all use this definition.
- **Compression ratio** (`compressionRatio` in TypeScript) is tokens after ÷ tokens before, as the API reference defines it. Lower is better: `45000 -> 4500` gives 0.1, which is a 90% saving. The saved share is `1 - compressionRatio`.
- **Cost avoided** is the dollar value of the saved input tokens. Output tokens don't count toward it.
- **Each savings store has its own scope and lifetime.** Their numbers don't have to agree, so pick the store that answers your question.
- **Simulation** runs the full transform pipeline locally and never calls the large language model (LLM) API. It incurs no provider cost or latency.

### Where savings live

| Store | Covers | Lifetime | Location |
| --- | --- | --- | --- |
| Savings ledger, read by `headroom savings` | Compressions from the proxy and from every Model Context Protocol (MCP) server process | 30 days; survives proxy and agent restarts | `~/.headroom/savings_events.jsonl` |
| `persistent_savings` in `/stats` | Proxy compression | Lifetime; survives proxy restarts | `~/.headroom/proxy_savings.json` (the persistent savings file) |
| `headroom_tokens_saved_total` | The current proxy process | Since the process started | Runtime counter |
| `headroom_stats` | One session | One session | In memory |
| Python `client.get_stats()` | The current client session | One session | No database query |
| Python `client.get_metrics()`, `client.get_summary()` | Stored metrics | Stored history | Database |

The savings ledger is the durable, cross-process source of truth. Use it when you need one total for all agents and the proxy together. The only reset these pages document is `headroom savings --reset`.

## Quick reference

The examples assume the proxy listens on `localhost:8787`.

| Task | Command or API |
| --- | --- |
| Savings summary, last 30 days | `headroom savings` (add `--json` for scripts) |
| Shorter lookback window (1–30 days) | `headroom savings --days 7` |
| Delete the savings ledger | `headroom savings --reset` |
| Live proxy totals | `curl http://localhost:8787/stats` |
| Daily history as comma-separated values (CSV) | `curl "http://localhost:8787/stats-history?format=csv&series=daily"` |
| Prometheus scrape | `curl http://localhost:8787/metrics` |
| Real 95th and 99th percentile (p95, p99) latency | `headroom perf` |
| Budget check with estimated share | `headroom doctor` |
| Hard spend limit | `headroom proxy --budget 10.00` |
| Verbose proxy logs, written to a file | `HEADROOM_LOG_LEVEL=debug headroom proxy --log-file headroom.jsonl` |
| Preview compression | Python: `client.chat.completions.simulate(model=..., messages=...)`; TypeScript: `compress()` without sending the result |

## Track savings with `headroom savings`

```bash
headroom savings            # human-readable summary
headroom savings --json     # machine-readable report for scripts
headroom savings --days 7   # lookback window: 1-30 days, default 30
headroom savings --reset    # delete the savings ledger and start fresh
```

The summary shows three time windows, then cost avoided per model, then calls and tokens saved per client. Each window row shows the savings percentage, tokens saved out of the total, and cost avoided.

```text
Today       ███████████░░░░░  67.9%  saved 19,000 / 28,000 tokens  $0.0850
Last 7 days ███████████░░░░░  67.1%  saved 47,000 / 70,000 tokens  $0.2250
Last 30 days ██████████░░░░░░  65.0%  saved 78,000 / 120,000 tokens  $0.2680

Cost avoided per model:
  claude-opus-4-8          $0.1750
  gpt-5.5                  $0.0350
  unknown                  $0.0330
  claude-haiku-4-5         $0.0250

Savings by client:
  claude-code              4 calls · 60,000 tokens saved
  codex                    2 calls · 18,000 tokens saved
```

### How the savings ledger works

- Every compression appends one line to the savings ledger. `headroom savings` aggregates the file each time you run it.
- The savings ledger is append-only and file-locked. Headroom's MCP server runs as several processes (the main agent plus each subagent), and the proxy is another process. A locked append log lets all of them write without lost updates.
- The file is on disk, so totals survive proxy and agent restarts.
- Headroom drops events older than 30 days on read and compacts the file once it grows large. That retention is also the hard maximum for `--days`.

Two compression paths write to the savings ledger:

| Path | Records | Priced with |
| --- | --- | --- |
| MCP tool path – each `headroom_compress` call | MCP client name and tokens saved; the model is `unknown` | A blended per-token rate, or the `HEADROOM_MCP_MODEL` hint |
| Proxy path – each request | The real upstream model | LiteLLM list pricing for that model |

### How cost avoided is priced

Cost avoided values the saved input tokens at LiteLLM list pricing when Headroom knows the model. That is the case for proxy traffic. MCP tool compressions can't see the agent's upstream model, so they record `model="unknown"` and use a blended per-token rate. You get an estimate instead of `$0`. Read cost avoided as an estimate, not an invoice figure: it uses list prices, it excludes output tokens, and the `unknown` line is a blend.

### Configure the savings ledger

| Variable | Purpose |
| --- | --- |
| `HEADROOM_SAVINGS_EVENTS_PATH` | Move the savings ledger (default `~/.headroom/savings_events.jsonl`) |
| `HEADROOM_MCP_CLIENT` | Override the client label that the MCP tool path records |
| `HEADROOM_MCP_MODEL` | Price MCP tool compressions against a known model instead of the blended rate |

- Set `HEADROOM_MCP_MODEL` when one model carries most of your agent traffic. The trade-off: the hint names one model, so every MCP tool compression gets that model's price, even when your agent used another model.
- Set `HEADROOM_MCP_CLIENT` when the MCP client name doesn't tell your setups apart under "Savings by client".
- If you move the savings ledger, give `HEADROOM_SAVINGS_EVENTS_PATH` the same value for the proxy, the MCP server and the shell that runs `headroom savings`. Otherwise the writers and the reader use different files.

### Do this, not that: resets

`--reset` deletes the savings ledger, including every client and model. Don't use it to get a clean number, because you lose up to 30 days of history. Read a shorter window instead. The trade-off: `--days` is a rolling lookback, so it doesn't line up exactly with the start of an experiment. If you need an exact baseline, save the `--json` report before you reset.

```bash
# Don't: wipe history to get a clean number
headroom savings --reset

# Do: keep history and read a shorter window
headroom savings --days 1
```

## Monitor the proxy

### `/stats` – live totals

```bash
curl -s http://localhost:8787/stats | jq .tokens
```

| Field | Meaning |
| --- | --- |
| `tokens.input`, `tokens.output`, `tokens.saved`, `tokens.savings_percent` | Token totals and the savings percentage |
| `persistent_savings.lifetime.tokens_saved`, `persistent_savings.lifetime.compression_savings_usd` | Lifetime proxy savings from the persistent savings file |
| `cost.total_cost_usd`, `cost.total_savings_usd` | Spend and savings in US dollars |
| `requests.total` | Completed requests only |
| `requests.failed`, `requests.failed_by_provider` | Upstream failures, attributed to the provider that produced them |
| `requests.rate_limited`, `requests.rate_limited_by_source` | 429 responses, split into `headroom` (Headroom's own limiter) and `upstream` (the provider) |
| `cost.budget_basis` | Measured versus estimated spend (see budget alerts below) |

A request that ends in a 4xx, 5xx or 429 goes to `requests.failed` or `requests.rate_limited`. It never reaches `requests.total`. Move the persistent savings file with `HEADROOM_SAVINGS_PATH` – not `HEADROOM_SAVINGS_EVENTS_PATH`, which moves the savings ledger.

### `/stats-history` – durable rollups

```bash
curl http://localhost:8787/stats-history
curl "http://localhost:8787/stats-history?format=csv&series=daily"
```

The endpoint returns durable compression history with hourly, daily, weekly and monthly rollups. The docs show CSV export for the `daily` and `monthly` series. Use the CSV export when savings go into a spreadsheet or a recurring report.

### Prometheus metrics

```bash
curl http://localhost:8787/metrics
```

| Metric | Meaning | Target |
| --- | --- | --- |
| `headroom_tokens_saved_total` | Tokens saved since this proxy process started | Higher is better |
| `headroom_persistent_savings_tokens_saved_total` | Durable lifetime input tokens saved by proxy compression | Higher is better |
| `headroom_overhead_ms_sum`, `headroom_overhead_ms_count` | Latency that Headroom itself adds | Low |
| `headroom_latency_ms_sum`, `headroom_latency_ms_count` | Request latency | – |
| `headroom_provider_cache_hit_requests_total`, `headroom_provider_cache_requests_total` | Provider prompt-cache hits and requests, by `provider` | Hit rate above 20% |
| `headroom_requests_failed_total{provider}` | Upstream 4xx and 5xx, excluding 429 | 0 |
| `headroom_requests_rate_limited_total{source}` | 429s; `source` is `headroom` or `upstream` | 0 |
| `headroom_requests_total` | Completed requests only | – |
| `headroom_inbound_requests_total` | All traffic | – |

Start from these Prometheus Query Language (PromQL) queries, taken from the docs:

```promql
# Mean latency that Headroom adds
rate(headroom_overhead_ms_sum[5m]) / rate(headroom_overhead_ms_count[5m])

# Provider cache hit rate
sum by (provider) (rate(headroom_provider_cache_hit_requests_total[5m]))
  / sum by (provider) (rate(headroom_provider_cache_requests_total[5m]))
```

Graph `headroom_persistent_savings_tokens_saved_total` for lifetime trends. The runtime counter starts again with each proxy process, so a raw graph of it drops at every restart.

#### Do this, not that: failure rate

`headroom_requests_total` leaves out failed and rate-limited requests. A failure rate that divides by it alone overstates the rate.

```promql
# Don't: the denominator leaves out the failures
sum(rate(headroom_requests_failed_total[5m])) / sum(rate(headroom_requests_total[5m]))

# Do: add the failures back into the denominator
sum(rate(headroom_requests_failed_total[5m]))
  / (sum(rate(headroom_requests_total[5m])) + sum(rate(headroom_requests_failed_total[5m])))
```

For an all-traffic denominator, use `headroom_inbound_requests_total`.

#### Labels and missing buckets

- `headroom_requests_failed_total` carries a `provider` label, and `headroom_requests_rate_limited_total` carries a `source` label. An unaggregated query on either returns several series. Wrap it in `sum without (provider) (...)` or `sum without (source) (...)` to get one series.
- Keep the `source` label when you alert on 429s. A 429 from Headroom's own limiter and a 429 from the provider need different fixes.
- `/metrics` has no histogram buckets for compression ratio or latency. Build averages from the `_sum` and `_count` pairs. Run `headroom perf` when you need real p95 and p99.

### Grafana dashboard

The template [`examples/grafana/headroom-dashboard.json`](https://github.com/headroomlabs-ai/headroom/blob/main/examples/grafana/headroom-dashboard.json) uses the right metric names. Every panel query also filters on a `pool` label that no metric emits, so the panel dropdowns are empty after import. Remove the `pool=~"..."` filter from each query, or build panels from the PromQL above.

### OpenTelemetry export

The proxy can push its counters to any OpenTelemetry Protocol (OTLP) HTTP endpoint. Export needs the `otel` extra (`headroom-ai[proxy,otel]`).

```bash
HEADROOM_OTEL_METRICS_ENABLED=1
HEADROOM_OTEL_METRICS_ENDPOINT=http://127.0.0.1:4318/v1/metrics
HEADROOM_OTEL_SERVICE_NAME=headroom-proxy
HEADROOM_OTEL_RESOURCE_ATTRIBUTES=deployment.environment=prod

# Confirm the exporter is live
curl -s http://localhost:8787/stats | jq .otel
```

| Variable | Default | Notes |
| --- | --- | --- |
| `HEADROOM_OTEL_METRICS_ENABLED` | `0` | Set to `1` to export |
| `HEADROOM_OTEL_METRICS_EXPORTER` | `otlp_http` | `console` for local debugging |
| `HEADROOM_OTEL_METRICS_ENDPOINT` | unset | Full metrics URL; Headroom doesn't append `/v1/metrics` |
| `HEADROOM_OTEL_METRICS_HEADERS` | unset | Comma-separated `key=value` auth headers |
| `HEADROOM_OTEL_METRICS_EXPORT_INTERVAL_MS` | `10000` | Export interval in milliseconds |
| `HEADROOM_OTEL_SERVICE_NAME` | `headroom-proxy` | OpenTelemetry `service.name` |
| `HEADROOM_OTEL_RESOURCE_ATTRIBUTES` | unset | Comma-separated resource attributes |

| Counter | Counts |
| --- | --- |
| `headroom.proxy.requests` | Requests |
| `headroom.proxy.tokens.input`, `headroom.proxy.tokens.output` | Input and output tokens |
| `headroom.proxy.tokens.saved` | All layers: compression savings plus tool-schema deferral savings |
| `headroom.proxy.tokens.tool_schema_saved` | The tool-schema deferral part only |
| `headroom.compression.tokens.saved` | The compression-pipeline part only |

`headroom.proxy.tokens.saved` can exceed compression-only figures, because it includes tool-schema deferral. Compare compression results with `headroom.compression.tokens.saved`.

If your application already configures a global OpenTelemetry meter provider, leave every `HEADROOM_OTEL_*` variable unset. Headroom records into that ambient provider automatically, so it needs no exporter of its own.

#### Dynatrace

```bash
HEADROOM_OTEL_METRICS_ENABLED=1
HEADROOM_OTEL_METRICS_ENDPOINT="https://<env-id>.live.dynatrace.com/api/v2/otlp/v1/metrics"
HEADROOM_OTEL_METRICS_HEADERS="Authorization=Api-Token dt0c01.XXXX"
OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=DELTA
HEADROOM_OTEL_SERVICE_NAME=headroom-proxy
```

- Give the API token the `metrics.ingest` scope.
- Always set `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=DELTA`. Dynatrace ingests only delta counters, and the OpenTelemetry SDK defaults to cumulative. Without it, Dynatrace rejects every Headroom metric with `UNSUPPORTED_METRIC_TYPE_MONOTONIC_CUMULATIVE_SUM`, and the proxy logs no error.
- Restart the proxy, then search the metric explorer for `headroom.proxy.tokens.saved`. Data appears within about 30 seconds.
- For an ActiveGate, use `https://<activegate>:9999/e/<env-id>/api/v2/otlp/v1/metrics`.
- If you run an OpenTelemetry Collector, point Headroom at it and add the `cumulativetodelta` processor. The collector then holds the token, and you don't need the temporality variable.

Traces are separate. Headroom's self-configured tracing targets Langfuse only. To send spans to Dynatrace, leave `HEADROOM_LANGFUSE_*` unset. Then run the proxy under `opentelemetry-instrument` with `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS` and `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`.

### Health check and logs

```bash
curl http://localhost:8787/health          # status, version, uptime_seconds
headroom proxy --log-file headroom.jsonl   # write proxy logs to a file
HEADROOM_LOG_LEVEL=debug headroom proxy    # more detail; there is no --log-level flag
```

In Python, the standard `logging` module controls the detail:

```python
import logging
logging.basicConfig(level=logging.INFO)     # compression summaries
# logging.basicConfig(level=logging.DEBUG)  # detailed transform decisions
```

INFO prints compression summaries, such as `Pipeline complete: 45000 -> 4500 tokens (saved 40500, 90.0% reduction)` and the SmartCrusher strategy applied. DEBUG adds detailed transform decisions, such as which items SmartCrusher kept and where the errors and warnings were.

## Read metrics from the SDKs

The two SDKs expose different things. The TypeScript SDK reads the proxy's stats and returns metrics from each `compress()` call. The Python SDK reports on its own client session and on stored metrics.

### TypeScript

```ts
import { HeadroomClient, compress } from 'headroom-ai';

// Proxy-wide stats
const client = new HeadroomClient();
const stats = await client.proxyStats();
console.log(`Tokens saved: ${stats.tokens.saved} (${stats.tokens.savingsPercent}%)`);

// Every compress() call returns its own metrics
const result = await compress(messages, { model: 'gpt-4o' });
console.log(`Tokens: ${result.tokensBefore} -> ${result.tokensAfter}`);
console.log(`Transforms: ${result.transformsApplied.join(', ')}`);
```

`compressionRatio` is the share of tokens kept, not the share saved. The metrics page's example prints `compressionRatio * 100` under the label "Saved". For a 90% saving, that line reports 10.0%.

```ts
// Don't: this prints the kept share under a "Saved" label
console.log(`Saved: ${result.tokensSaved} (${(result.compressionRatio * 100).toFixed(1)}%)`);

// Do: the saved share is 1 - compressionRatio
console.log(`Saved: ${result.tokensSaved} (${((1 - result.compressionRatio) * 100).toFixed(1)}%)`);
```

### Python

In these examples, `client` is a Python `HeadroomClient`. "Compare configurations" below shows how to build one.

```python
from datetime import datetime, timedelta

# Current session: cheap, no database query
stats = client.get_stats()
print(stats["config"]["mode"], stats["session"]["tokens_saved_total"], stats["session"]["requests_optimized"])

# Stored history: queries the database
for m in client.get_metrics(start_time=datetime.utcnow() - timedelta(hours=1), limit=100):
    print(f"{m.timestamp}: {m.tokens_input_before} -> {m.tokens_input_after}")

summary = client.get_summary()
print(summary["total_requests"], summary["total_tokens_saved"], summary["avg_tokens_saved"])
```

`get_stats()` returns three groups. `session` holds `requests_total`, `requests_optimized`, `requests_audit`, `tokens_saved_total` and `cache_hits`. `config` holds `mode`, `provider`, `cache_optimizer` and `semantic_cache`. `transforms` holds `smart_crusher_enabled` and `cache_aligner_enabled`.

Use `get_stats()` for frequent checks, because it skips the database. Use `get_metrics()` and `get_summary()` for history and reports, at the cost of a database query.

## Cap spend with budget alerts

```bash
headroom proxy --budget 10.00
headroom proxy --budget 10.00 --budget-estimated-basis count   # count is the default
```

When spend exceeds the budget, requests return a budget-exceeded error. `/stats` shows the budget status, and the logs record the budget state.

### Measured versus estimated spend

- `measured` – the provider response included a usage breakdown.
- `estimated` – the response had no usage breakdown. Headroom used its own `tokens_sent` count so that input cost still reaches the budget. It logs one warning per model the first time this happens.

`/stats` keeps the two apart under `cost.budget_basis`:

```json
{
  "cost": {
    "budget_limit_usd": 10.0,
    "budget_period": "daily",
    "budget_estimated_basis": "count",
    "budget_basis": {
      "total_usd": 3.1400,
      "measured_usd": 2.9000,
      "estimated_usd": 0.2400,
      "estimated_pct": 7.6,
      "records": 412,
      "estimated_records": 31
    }
  }
}
```

An estimate can drift in either direction. Choose how estimates affect the hard limit with `--budget-estimated-basis` or the `HEADROOM_BUDGET_ESTIMATED_BASIS` environment variable:

| Value | Effect | Trade-off |
| --- | --- | --- |
| `count` (default) | Estimated spend consumes the budget like measured spend | Matches historical behavior, but drift can trip the limit early or late |
| `ignore` | Estimated spend is booked and reported but doesn't consume the budget | Unmeasured spend can run past the limit |
| `block` | Refuses requests once the period holds any estimated spend | Never enforces the limit against a guess, but one response without usage data stops traffic for the period |

Run `headroom doctor` to see the estimated share next to the budget check. A high `estimated_pct` tells you the budget leans on Headroom's own counts.

## Preview compression with simulation

Simulation shows what Headroom would do to your messages without sending them to the LLM. Use it to estimate savings, debug compression, and find where token waste comes from.

```python
plan = client.chat.completions.simulate(model="gpt-4o", messages=large_conversation)

print(f"Tokens: {plan.tokens_before} -> {plan.tokens_after}")
print(f"Would save: {plan.tokens_saved} ({plan.tokens_saved / plan.tokens_before * 100:.1f}%)")
print(f"Transforms: {plan.transforms}")
```

These pages show no separate simulate call for TypeScript. Call `compress()` as in the TypeScript SDK example above, and don't send the result to your LLM. `compress()` returns the same result structure either way. Waste signals and block kinds appear only in the Python examples.

### Find the waste

`plan.waste_signals` is a `dict[str, int]` of tokens per waste type. The simulation page lists `json_bloat`, `html_noise`, `whitespace`, `dynamic_date` and `repetition`, and the API reference adds `base64`, `reread` and `reread_compressed`. Rank them to see what to fix first:

```python
for signal, tokens in sorted(plan.waste_signals.items(), key=lambda kv: kv[1], reverse=True):
    print(f"{signal:14} {tokens} tokens")
```

The parser also splits the conversation into block kinds: `system`, `user`, `assistant`, `tool_call`, `tool_result` and `rag` (retrieved document context). The docs name `tool_result` as the largest source of waste, so start with tool outputs. The pages don't show which attribute holds the per-block counts.

### Estimate savings before you enable `optimize` mode

Run simulation on a representative sample of your workload. Sum the token counts before you divide. That weights each conversation by its size, so small conversations can't skew the estimate.

```python
total_before = total_after = 0
for messages in sample_conversations:
    plan = client.chat.completions.simulate(model="gpt-4o", messages=messages)
    total_before += plan.tokens_before
    total_after += plan.tokens_after

print(f"Estimated savings: {(1 - total_after / total_before) * 100:.1f}%")
print(f"Tokens saved: {total_before - total_after:,}")
```

### Debug a conversation that doesn't compress

```python
import json

plan = client.chat.completions.simulate(model="gpt-4o", messages=messages)
if plan.tokens_saved == 0:
    print("No compression applied")
else:
    print(f"Transforms applied: {plan.transforms}")
    print(json.dumps(plan.messages_optimized, indent=2))
```

When `tokens_saved` is 0, check three causes: tool outputs under 200 tokens each, no tool output with a compressible JSON array, or content that is already compact, such as code or grep results.

### Compare configurations

```python
from openai import OpenAI
from headroom import HeadroomClient, HeadroomConfig, OpenAIProvider
from headroom.transforms import SmartCrusherConfig

for max_items in (10, 25, 50):
    client = HeadroomClient(
        original_client=OpenAI(),
        provider=OpenAIProvider(),
        config=HeadroomConfig(smart_crusher=SmartCrusherConfig(max_items_after_crush=max_items)),
    )
    plan = client.chat.completions.simulate(model="gpt-4o", messages=messages)
    print(f"max_items={max_items}: {plan.tokens_saved} tokens saved")
```

Read `plan.messages_optimized` for each setting, not only the token count. A smaller `max_items_after_crush` keeps fewer items. It saves more tokens but can drop items your task needs.

## Verify that Headroom saves tokens

Run these checks in order, quickest first:

1. **Proxy is up** – `curl http://localhost:8787/health` returns `"status": "healthy"`.
2. **Proxy compresses** – after some traffic, `curl -s http://localhost:8787/stats | jq .tokens` shows `saved` above 0.
3. **Logs agree** – with Python INFO logging, each compression logs a `Pipeline complete` line with before and after counts.
4. **Python SDK compresses** – `client.get_stats()["session"]["tokens_saved_total"]` grows. If `requests_optimized` stays at 0, check `stats["config"]["mode"]`. The docs treat `optimize` as the mode you enable once simulation looks right.
5. **TypeScript SDK compresses** – `result.tokensSaved` is above 0 and `result.transformsApplied` isn't empty.
6. **MCP tool records** – `headroom savings` lists your agent under "Savings by client".
7. **Savings hold on your workload** – before a rollout, simulation on a representative sample shows savings worth having.

### Interpret the numbers

| Number | What it means | Watch out for |
| --- | --- | --- |
| Tokens saved (`tokens_saved` in Python, `tokensSaved` in TypeScript) | Tokens before minus tokens after | – |
| Savings percentage | Tokens saved ÷ tokens before × 100; `45000 -> 4500` is a 90.0% reduction | Across samples, sum the tokens before you divide |
| `compressionRatio` (TypeScript) | Tokens after ÷ tokens before; lower is better | It is the kept share – the saved share is `1 - compressionRatio` |
| Cost avoided | Dollar value of saved input tokens at list prices | Excludes output tokens; the `unknown` line uses a blended rate |
| `requests.total`, `headroom_requests_total` | Completed requests | Excludes 4xx, 5xx and 429 |
| `headroom.proxy.tokens.saved` | Compression plus tool-schema deferral | Use `headroom.compression.tokens.saved` for compression alone |
| `estimated_pct` | Share of spend that Headroom estimated | High values mean the budget leans on estimates |

## Common pitfalls

- **Comparing stores with different scopes.** `headroom savings`, `/stats`, `headroom_stats` and `get_stats()` measure different things. Pick one store per question.
- **Reading the `unknown` model as an error.** It holds MCP tool traffic at a blended rate. Set `HEADROOM_MCP_MODEL` for a known price.
- **Mixing up the two path variables.** `HEADROOM_SAVINGS_EVENTS_PATH` moves the savings ledger. `HEADROOM_SAVINGS_PATH` moves the persistent savings file.
- **Passing `--log-level` to the proxy.** The flag doesn't exist. Set `HEADROOM_LOG_LEVEL` instead.
- **Importing the Grafana template unchanged.** Its `pool` filter matches no metric, so the panels stay empty.
- **Leaving out delta temporality for Dynatrace.** Every metric is dropped, and the proxy logs no error.
- **Ending `HEADROOM_OTEL_METRICS_ENDPOINT` at the port.** Headroom doesn't append `/v1/metrics`, so give the full URL, such as `http://127.0.0.1:4318/v1/metrics`.
- **Dividing by `headroom_requests_total` for a failure rate.** It excludes the failures you are counting.
- **Looking for percentile buckets.** There are none. Use `_sum` / `_count` averages or `headroom perf`.
- **Reporting `compressionRatio` as the saving.** It is the kept share. Report `1 - compressionRatio`, or `tokensSaved / tokensBefore`.

## Related skills

- [proxy](./proxy.md) – `headroom proxy` flags such as `--budget` and `--log-file`, and the full endpoint list.
- [configuration](./configuration.md) – `HeadroomConfig`, modes such as `optimize`, and environment variables.
- [compression](./compression.md) – the transforms behind `transforms` and `transformsApplied`, including SmartCrusher.
- [coding-agents](./coding-agents.md) – MCP tools such as `headroom_compress`, which feed the savings ledger.
- [ccr-and-caching](./ccr-and-caching.md) – cache optimization behind the provider cache-hit metrics and `cache_optimizer`.
- [sdk-reference](./sdk-reference.md) – full `HeadroomClient` and `compress()` reference for both SDKs.
- [framework-integrations](./framework-integrations.md) – the LiteLLM page, which the savings docs link for list pricing.
- [troubleshooting-and-limits](./troubleshooting-and-limits.md) – symptom-based fixes when savings stay at zero.
- [architecture-and-security](./architecture-and-security.md) – benchmarks to compare your numbers with.

## Source pages

- https://docs.headroomlabs.ai/docs/savings
- https://docs.headroomlabs.ai/docs/metrics
- https://docs.headroomlabs.ai/docs/simulation
- https://docs.headroomlabs.ai/docs/api-reference – consulted only for the `compressionRatio` definition
