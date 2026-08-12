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
| LM Studio + `openai/gpt-oss-20b` | Local OpenAI-compatible endpoint, JSON Schema output, no per-request charge | Requires a running local server and sufficient RAM/VRAM | Recommended free real-time local option |
| Deterministic local planner | Instant, private, reproducible, no key | Covers known e-commerce intents rather than arbitrary language | Automatic fallback |

## Runtime policy

- **Fast:** the selected model with low planning effort, followed by a deterministic computed narrative. This uses one model pass.
- **Balanced:** the selected model with configured medium planning effort and a concise evidence-grounded narrative. This is the default.
- **Deep:** the selected model with high effort for both planning and evidence-grounded narrative formatting.
- Output: provider-native JSON Schema plus local Pydantic validation.
- Transport: one bounded retry for transient errors.
- Invalid query: one sanitized correction attempt followed by full revalidation.
- Provider unavailable: complete the question through the deterministic local planner and disclose the fallback.
- Execution: generated output always goes through the SQL or pandas security validator.
- Progress: planning, validation, execution, and evidence-grounding stages are emitted live; hidden reasoning is never displayed.

## Privacy choice

The Gemini API free tier is suitable for synthetic, public, or approved demonstration data. Google's pricing documentation says free-tier content may be used to improve products. For private business data, select the deterministic planner, LM Studio, local Ollama, or an appropriately governed paid provider and review the provider's current data-use terms. LM Studio is the preferred free real-time option for this reference architecture because it exposes JSON Schema structured output through an OpenAI-compatible localhost endpoint; model quality and latency still depend on the chosen model and hardware.

## Primary references

- [Gemini 3.6 Flash model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API pricing and free-tier data use](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini thinking levels](https://ai.google.dev/gemini-api/docs/thinking)
- [Groq production models](https://console.groq.com/docs/models)
- [Groq structured outputs](https://console.groq.com/docs/structured-outputs)
- [OpenAI models](https://developers.openai.com/api/docs/models)
- [LM Studio OpenAI compatibility](https://lmstudio.ai/docs/developer/openai-compat)
- [LM Studio structured output](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
