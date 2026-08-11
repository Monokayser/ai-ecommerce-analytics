# Prompt Design

The query system prompt contains the dataset purpose, structured schema, types, bounded sample values, aliases, active filters, output schema, and safety policy. Instructions appear once and active filters are explicitly higher precedence than conversation context.

The LLM returns `GeneratedQuery` JSON: interpreted question, language, query, columns, filters, aggregation, chart recommendation, and a short user-facing rationale. No hidden reasoning is requested or displayed.

Planning and narration use separate controls. Gemini 3.6 Flash is the hosted default. The user can select Fast, Balanced, or Deep response mode: Fast performs one low-effort hosted planning pass and formats the verified result locally; Balanced uses configured medium planning plus a concise model narrative; Deep uses high effort and higher narrative detail. The native Gemini SDK receives a Pydantic-derived JSON Schema and the response is validated again locally. Transient provider failures receive at most one transport retry, while an invalid generated query receives exactly one sanitized correction attempt.

The pipeline exposes only named operational stages—planning, validation, execution, evidence grounding, and completion—to the Streamlit status component. These are emitted during execution for responsive feedback and never reveal chain-of-thought or hidden reasoning.

After execution, only the question, verified result sample, numeric summary, missing counts, filters, timing, truncation status, and generated query are passed to the narrative prompt inside an untrusted-data boundary. The output distinguishes direct answer, analysis, findings, limitations, and caption. Captions containing unsupported numeric claims fall back to a neutral computed statement.

## No-key mode

Without Gemini, OpenAI, or Ollama configuration, `OfflineQueryPlanner` recognizes the capstone's frequent e-commerce intents: KPI summaries, rankings, named-subset comparisons, monthly/yearly trends, discount/profit relationships, loss markets, average order value, and unusual high-discount loss orders. It emits DuckDB SQL through the same validator and executor as model-generated plans. Its narrative is explicitly labeled deterministic and contains only computed result facts. A hosted-provider timeout, rate limit, or availability error also falls back to this planner for that request and exposes the fallback status in the UI.

## Alias examples

| User wording | Canonical field |
|---|---|
| revenue / income / turnover | Sales |
| earnings / net income | Profit |
| category / product type | Product Category |
| customer type / segment | Customer Segment |
| shipping method / delivery mode | Ship Mode |
| units / volume | Quantity |

Ambiguous `location` is not silently resolved when both Region and Country are available; the model receives both candidates and the schema values.
