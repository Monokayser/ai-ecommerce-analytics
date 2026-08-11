# AI Model Selection

## Decision

The default hosted provider is **Gemini 3.6 Flash** through Google's native `google-genai` SDK. The model is stable, fast, supports native JSON Schema structured output, exposes controllable thinking levels, and has a free API tier for development and small projects. These characteristics fit a query planner that must return a compact typed object quickly and reliably.

The application remains provider-neutral and always has a deterministic local planner. A hosted model expands language coverage; it does not bypass validation or execute queries directly.

## Alternatives considered

| Option | Strength | Constraint for this project | Decision |
|---|---|---|---|
| Gemini 3.6 Flash | Stable GA model, free tier, native JSON Schema, strong quality/latency balance | Free-tier data may be used to improve Google products | Default hosted model |
| Groq with `openai/gpt-oss-20b` | Very high token throughput and a free developer limit | Strict structured output is not supported for this model; JSON is best-effort | Not the default query planner |
| OpenAI GPT-5.6 family | Strong Responses API and schema support | API usage is paid | Supported optional provider |
| Local Ollama | Data can remain locally controlled; no per-request API charge | Requires suitable local hardware and model management | Supported privacy-first provider |
| Deterministic local planner | Instant, private, reproducible, no key | Covers known e-commerce intents rather than arbitrary language | Automatic fallback |

## Runtime policy

- **Fast:** Gemini 3.6 Flash with `low` planning effort, followed by a deterministic computed narrative. This uses one hosted-model pass.
- **Balanced:** Gemini 3.6 Flash with configured `medium` planning effort and a concise `low`-effort AI narrative. This is the default.
- **Deep:** Gemini 3.6 Flash with `high` effort for both planning and evidence-grounded narrative formatting.
- Output: provider-native JSON Schema plus local Pydantic validation.
- Transport: one bounded retry for transient errors.
- Invalid query: one sanitized correction attempt followed by full revalidation.
- Provider unavailable: complete the question through the deterministic local planner and disclose the fallback.
- Execution: generated output always goes through the SQL or pandas security validator.
- Progress: planning, validation, execution, and evidence-grounding stages are emitted live; hidden reasoning is never displayed.

## Privacy choice

The Gemini API free tier is suitable for synthetic, public, or approved demonstration data. Google's pricing documentation says free-tier content may be used to improve products. For private business data, select local mode/Ollama or an appropriately governed paid provider and review the provider's current data-use terms.

## Primary references

- [Gemini 3.6 Flash model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API pricing and free-tier data use](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini thinking levels](https://ai.google.dev/gemini-api/docs/thinking)
- [Groq production models](https://console.groq.com/docs/models)
- [Groq structured outputs](https://console.groq.com/docs/structured-outputs)
- [OpenAI models](https://developers.openai.com/api/docs/models)
