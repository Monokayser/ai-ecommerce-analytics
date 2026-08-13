# Performance and Storage Trade-offs

DuckDB scans registered pandas/Arrow-backed columns with vectorized execution and no database server. pandas remains convenient for Streamlit display and scikit-learn integration. CSV is portable but slow and weakly typed; Parquet is preferred for repeated analysis because it is compressed, typed, and columnar.

The application records load time, schema time, memory usage, and every query duration. The UI benchmark performs one warm-up followed by seven measured filtered aggregations and reports median/p95 latency. The sub-500 ms target is accepted only with the actual dataset dimensions and hardware recorded.

For more than one million rows, production deployments should prefer DuckDB `read_parquet`/`read_csv_auto` lazy relations from an internally controlled dataset path, push filters and aggregation into DuckDB, and fetch only limited results. Browser uploads still require bounded temporary/in-memory handling and should not be used for unrestricted files.

## Measured v1.12.0 development baseline

On 2026-08-13, `scripts/run_performance_baseline.py` measured 15 warmed filtered aggregations on the deterministic 2,000-row × 14-column synthetic CSV. The Windows host reported Python 3.12.13 on an AMD64 Family 23 Model 17 processor, 105.77 MB process RSS, 16.761 ms median, and 17.715 ms p95. CSV load time was 25.187 ms.

This measurement meets the `<500 ms` target only for that dataset and host. It is not evidence for the unavailable official dataset or for every Streamlit Community Cloud allocation. CI writes its own JSON evidence to a short-lived artifact with its runner, dataset dimensions, median, p95, and memory rather than committing transient benchmark output.
