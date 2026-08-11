# 15-Minute Presentation and 5-Minute Q&A

## Timing

1. **0:00-1:00 - Problem and objective:** natural language to validated analytical evidence.
2. **1:00-2:00 - Dataset:** source, dimensions, schema, and development-versus-official readiness.
3. **2:00-4:00 - Architecture:** trace the raw-data-to-export Mermaid flow.
4. **4:00-6:00 - Data layer:** aliases, cleaning log, profiler, DuckDB, and measured latency.
5. **6:00-9:00 - LLM pipeline:** schema prompt, structured query, AST validation, one retry, and narrative grounding.
6. **9:00-12:00 - Dashboard:** filters, KPIs, six-plus charts, fresh AI question, and follow-up.
7. **12:00-14:00 - Advanced features:** IQR/Isolation Forest and subset comparison.
8. **14:00-15:00 - Evaluation:** benchmark, limitations, conclusion, and responsible AI disclosure.

## Live-demo sequence

1. Upload the approved 5,000+ row CSV and confirm the readiness badge.
2. Show the data-quality summary, schema, and cleaning log.
3. Apply Region and date filters; show active row count.
4. Demonstrate trend, map, heatmap, distribution, sunburst, and grouped bar views.
5. Ask: “Which region has the highest total sales?”
6. Expand the generated query and validation details.
7. Show the result, automatic chart, caption, and export buttons.
8. Ask: “Now compare it with the South region.”
9. Run Isolation Forest on Profit and explain facts versus interpretations.
10. Compare two regions and discuss unequal sample size.
11. Export the validated analysis as PDF/Word and one chart as PNG.

## Likely Q&A

- **Why DuckDB?** Vectorized in-process analytical SQL, good pandas/Arrow interoperability, and no server administration.
- **Why Streamlit?** Fast Python-native delivery, reliable session controls, and sufficient responsiveness for this academic scope.
- **How are queries secured?** Structured output, SQL AST allowlist, one dataset table, external-scan denial, row/time limits, and a no-eval pandas interpreter.
- **How are hallucinations reduced?** Schema/sample grounding, deterministic execution, result-only narratives, caption numeric checks, and explicit limitations.
- **How does memory work?** Five provider-independent compact records; current filters always win and reset clears them.
- **Why one retry?** It improves recoverability while keeping latency, cost, and failure behavior bounded.
- **How was performance measured?** Warm-up plus seven runs, median/p95, full dataset dimensions, and machine context.
- **LLM limitations?** Provider availability and interpretation errors remain; the system validates computation, not business truth.
- **Anomaly limitations?** Statistical unusualness is not causation, fraud, or error; subject-matter validation is mandatory.
- **How is leakage prevented?** No raw-row logging, bounded samples/results, environment secrets, and no model-generated file/network access.
- **How was AI coding used?** Disclosed assistance for scaffolding, implementation, testing, and documentation; the team reviews and explains every submitted line.
