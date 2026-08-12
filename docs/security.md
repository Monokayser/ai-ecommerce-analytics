# Security Model

## Threat model

Threats include prompt injection stored inside dataset cells, malicious uploads, arbitrary SQL/Python generation, filesystem and network access, denial-of-service queries, secret leakage, and verbose error disclosure.

## Controls

- Uploads are limited to CSV/JSON/Parquet, sanitized to a basename, bounded to 200 MB, decoded in memory, and never used as arbitrary server paths.
- Dataset values are delimited as untrusted samples, truncated, and explicitly denied instructional authority.
- LLM output must match strict Pydantic schemas. The displayed `reason` is a short rationale, not hidden reasoning.
- SQL is parsed with sqlglot. Only one `SELECT`/`WITH` statement is accepted; tables are limited to `dataset` and CTEs. Catalogs, schemas, DDL/DML, commands, external scans, file readers, extension loading, and multiple statements are rejected.
- The executor applies an outer row limit, uses an in-memory connection, registers only the active DataFrame, and interrupts execution after the configured timeout.
- Pandas fallback parses an expression AST and recursively interprets only literals, literal column selection, and allowlisted DataFrame methods. It never uses `eval`, `exec`, imports, globals, built-ins, modules, files, or network calls.
- Model errors are sanitized before the single correction attempt. Users see concise messages while logs contain exception types, not secrets or complete rows.
- API keys remain in environment configuration. Logs include operation, timing, row count, and status but never secret values or raw private rows.
- Explicit current filters override historical context; only the last five compact interactions are retained in session memory.
- Local analytics mode does not transmit dataset values to an external service. Hosted Gemini/OpenAI mode sends only bounded schema samples and bounded verified result evidence to the configured endpoint. Ollama and LM Studio send the same bounded context only to the explicitly configured endpoint; the documented defaults are localhost.

## Provider privacy

Google states that Gemini API free-tier content may be used to improve its products. Do not submit confidential, regulated, or personally identifying data through the free tier. Use the deterministic local planner, LM Studio, or a locally controlled Ollama deployment when data must remain on the machine; use an appropriately contracted paid provider when organizational data-handling terms are required. The demo deployment should contain synthetic or approved public data only.

## Residual risk

Parser and dependency defects remain possible, so dependencies are pinned and security regression tests cover representative bypass attempts. This is an analytical sandbox, not a general-purpose code-execution environment.
