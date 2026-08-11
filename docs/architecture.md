# System Architecture

## Data flow

```mermaid
flowchart LR
    A["Raw Dataset / Upload"] --> B["Validated Loader"]
    B --> C["Alias Resolver, Cleaner, Profiler"]
    C --> D["DuckDB In-Memory Analytics"]
    D --> E["Direct Query Engine"]
    C --> F["Gemini 3.6 Flash / OpenAI / Ollama Planner"]
    C --> M["Deterministic Local Planner"]
    F --> G["SQL / Pandas AST Validator"]
    M --> G
    G --> H["Safe Query Executor"]
    H --> I["Result Formatter"]
    I --> J["Automatic Chart Selector"]
    E --> K["Streamlit Dashboard"]
    J --> K
    K --> L["PDF / Word / PNG / SVG Export"]
```

## Layer responsibilities

- **UI:** session state, controls, accessibility, progress, and presentation. It does not contain analytical rules.
- **Data:** loading, canonicalization, cleaning, profiling, query construction, execution, and timing.
- **AI:** provider abstraction, Gemini-native JSON Schema output, deterministic no-key planner, prompt policy, evidence building, validation, one correction attempt, bounded provider retry, and five-turn memory.
- **Visualization:** deterministic selection and reusable Plotly constructors.
- **Advanced analytics:** deterministic anomaly and comparison calculations; the LLM only explains verified results.
- **Reporting:** provider-independent `ReportPayload` to styled Word/PDF output.

All components use typed Pydantic contracts so UI, test, and provider implementations can change independently.
