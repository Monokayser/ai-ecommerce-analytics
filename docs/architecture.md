# System Architecture

## Data flow

```mermaid
flowchart TB
    subgraph DATA["Data layer"]
        A["Validated CSV / JSON / Parquet upload"] --> B["Raw DatasetBundle"]
        B --> C["Alias resolution, reversible cleaning, profiling"]
        C --> D["PyArrow / pandas cleaned view"]
        D --> E["Global filter application"]
        E --> F["Fresh DuckDB query connection"]
    end

    subgraph UI["Streamlit control layer"]
        G["Upload + filter sidebar"] --> H["Six responsive workspaces"]
        H --> I["Overview / Exploration / Advanced / Quality / Export"]
        H --> J["AI Assistant"]
    end

    subgraph AGENT["AI assistant pipeline"]
        K["Capability preset"] --> M["Phase 1 — structured query plan"]
        L["Natural-language task"] --> M
        M --> N["Phase 2 — Pydantic + SQL/pandas AST validation"]
        N --> O["Bounded read-only execution"]
        O -->|"sanitized error; one attempt"| M
        O --> P["Phase 3 — evidence-grounded response"]
        P --> Q["Answer + result + chart + safety trace"]
        Q --> R["Session history / saved responses"]
        Q --> S["Word / PDF / CSV / PNG / SVG"]
    end

    E --> G
    J --> K
    J --> L
    F --> O
    T["Gemini / OpenAI / Ollama / LM Studio"] --> M
    U["Deterministic local planner"] --> M
```

## Layer responsibilities

- **UI:** session state, controls, accessibility, progress, and presentation. It does not contain analytical rules.
- **Data:** loading, canonicalization, cleaning, profiling, query construction, execution, and timing.
- **AI:** provider abstraction, Gemini-native or OpenAI-compatible JSON Schema output, Fast/Balanced/Deep modes, capability presets, natural-language tasks, live safe-stage callbacks, deterministic no-key planner, prompt policy, evidence building, one correction attempt, bounded provider retry, five-turn conversation memory, and ten saved session responses.
- **Visualization:** deterministic selection and reusable Plotly constructors.
- **Advanced analytics:** deterministic anomaly and comparison calculations; the LLM only explains verified results.
- **Reporting:** provider-independent `ReportPayload` to styled Word/PDF output.

All components use typed Pydantic contracts so UI, test, and provider implementations can change independently. The reference architecture's code-generation and formatting phases are retained conceptually, but unrestricted `exec()` is replaced by parsed SQL and a custom allowlisted pandas interpreter.
