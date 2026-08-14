# AI Model Selection

## Decision

The default hosted provider is **Gemini 3.6 Flash** through Google's native `google-genai` SDK and Interactions API. Google lists the model as generally available and optimized for agentic execution, with structured outputs, function calling, thinking, and a 1,048,576-token input window. These characteristics fit a query planner that must understand varied analytical outcomes and return a compact typed object quickly and reliably.

The application remains provider-neutral and always has a deterministic local planner. A hosted model expands language coverage; it does not bypass validation or execute queries directly.

## Agent design

Google's function-calling guidance separates planning from execution: the model selects a typed action, the application executes it, and verified results are returned for user-facing formatting. This project follows the same security boundary without exposing general-purpose application functions. The model returns one `GeneratedQuery` task plan containing the analytical intent, concise steps, assumptions, required columns, a read-only SQL/pandas operation, chart recommendation, and follow-up questions. The application then validates and executes that plan itself.

Complex requests use one DuckDB statement with CTEs or window functions. This supports compositional analytics while retaining the validator's single-statement guarantee. The current implementation covers summaries, rankings, multi-metric and two-dimensional comparisons, trends, period growth, contribution, profit margin, distributions, relationships, anomalies, and data-quality audits. A contextual local resolver also handles short follow-ups such as "now by category" when hosted AI is unavailable.

## Alternatives considered

| Option | Strength | Constraint for this project | Decision |
|---|---|---|---|
| Gemini 3.6 Flash | Stable GA model, free tier, native JSON Schema, strong quality/latency balance | Free-tier data may be used to improve Google products | Default hosted model |
| Groq with `openai/gpt-oss-20b` | Very high token throughput and a free developer limit | Strict structured output is not supported for this model; JSON is best-effort | Not the default query planner |
| OpenAI GPT-5.6 family | Strong Responses API and schema support | API usage is paid | Supported optional provider |
| Local Ollama | Data can remain locally controlled; no per-request API charge | Requires suitable local hardware and model management | Supported privacy-first provider |
| LM Studio + `openai/gpt-oss-20b` | Local OpenAI-compatible endpoint, JSON Schema output, no per-request charge | Requires a running local server and sufficient RAM/VRAM | Recommended free real-time local option |
| Deterministic local planner | Instant, private, reproducible, no key | Covers known e-commerce intents rather than arbitrary language | Automatic fallback |

## Runtime policy

- **Fast:** the selected model with low planning effort, followed by a deterministic computed narrative. This uses one model pass.
- **Balanced:** the selected model with configured medium planning effort and a concise evidence-grounded narrative. This is the default.
- **Deep:** the selected model with high effort for both planning and evidence-grounded narrative formatting.
- Output: provider-native JSON Schema plus local Pydantic validation.
- Transport: one bounded retry for transient provider or malformed structured-output errors.
- Invalid query: one sanitized correction attempt followed by full revalidation.
- Provider unavailable: complete the question through the deterministic local planner and disclose the fallback.
- Execution: generated output always goes through the SQL or pandas security validator.
- Progress: planning, validation, execution, and evidence-grounding stages are emitted live; hidden reasoning is never displayed.
- Rendering: only the selected answer/chart/data/verification workspace is built; report and chart files are generated on demand.

## Privacy choice

The Gemini API free tier is suitable for synthetic, public, or approved demonstration data. Google's pricing documentation says free-tier content may be used to improve products. For private business data, select the deterministic planner, LM Studio, local Ollama, or an appropriately governed paid provider and review the provider's current data-use terms. LM Studio is the preferred free real-time option for this reference architecture because it exposes JSON Schema structured output through an OpenAI-compatible localhost endpoint; model quality and latency still depend on the chosen model and hardware.

## Primary references

- [Gemini 3.6 Flash model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash)
- [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API pricing and free-tier data use](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini thinking levels](https://ai.google.dev/gemini-api/docs/thinking)
- [Groq production models](https://console.groq.com/docs/models)
- [Groq structured outputs](https://console.groq.com/docs/structured-outputs)
- [OpenAI models](https://developers.openai.com/api/docs/models)
- [LM Studio OpenAI compatibility](https://lmstudio.ai/docs/developer/openai-compat)
- [LM Studio structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
