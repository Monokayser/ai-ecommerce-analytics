# Performance and Storage Trade-offs

DuckDB scans registered pandas/Arrow-backed columns with vectorized execution and no database server. pandas remains convenient for Streamlit display and scikit-learn integration. CSV is portable but slow and weakly typed; Parquet is preferred for repeated analysis because it is compressed, typed, and columnar.

The application records load time, schema time, memory usage, and every query duration. The UI benchmark performs one warm-up followed by seven measured filtered aggregations and reports median/p95 latency. The sub-500 ms target is accepted only with the actual dataset dimensions and hardware recorded.

For more than one million rows, production deployments should prefer DuckDB `read_parquet`/`read_csv_auto` lazy relations from an internally controlled dataset path, push filters and aggregation into DuckDB, and fetch only limited results. Browser uploads still require bounded temporary/in-memory handling and should not be used for unrestricted files.
