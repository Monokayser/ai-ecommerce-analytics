# Limitations and Future Work

- Live accuracy depends on the configured model, prompt, data cleanliness, latency, rate limits, and API availability.
- The included synthetic dataset is development-only and cannot support official analytical conclusions.
- Country-name choropleths may fail for uncommon names; the app provides a labeled bar fallback.
- IQR assumes a broadly stable distribution; Isolation Forest flags statistical rarity, not business error or fraud.
- Comparisons are descriptive and can be distorted by unequal sample sizes or missing dimensions.
- A ten-second interrupt limits long queries but does not provide operating-system process isolation.
- Streamlit session memory is ephemeral and single-session; no authentication or durable conversation store is included.
- Kaleido requires a working Chrome/Chromium installation.

Future work: ISO geographic normalization, role-based access, persistent audit storage, provider-specific evaluation sets, time-series forecasting, and process-level query isolation.
