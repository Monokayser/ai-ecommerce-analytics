# Production Hardening and Compatibility

## Browser and device strategy

The interface uses standards-based HTML, CSS, Streamlit widgets, Plotly, and WebGL without external font or UI-framework downloads. The compatibility target is the current and previous major releases of Chrome, Edge, Firefox, and Safari, plus modern iOS Safari and Android Chrome.

- The font stack is `system-ui`, Apple system fonts, Segoe UI, Arial, Helvetica, and generic sans-serif. It avoids render-blocking web fonts and respects native platform hinting.
- Responsive breakpoints at 1,200 px, 900 px, and 640 px adapt spacing, typography, controls, tabs, cards, and navigation.
- Streamlit's automatic sidebar mode keeps filters open on wide screens and collapses them on small screens.
- Touch controls have a minimum 44 px target. Tabs scroll horizontally instead of overflowing.
- Both standard and `-webkit-` backdrop filters are provided. Browsers without glass-filter support receive opaque high-contrast panel fallbacks.
- The 3D insight space uses Plotly WebGL. The 2D Relationship and Distribution views remain available when WebGL is disabled or constrained.

Automated application and responsive checks run in Chromium. Firefox and Safari compatibility is supported through standards/fallback review; final deployment acceptance should include a short manual smoke test in the actual institutional browser versions.

## Accessibility

The application targets WCAG 2.2 AA interaction principles:

- semantic native headings and controls;
- a keyboard-visible “Skip to main content” link;
- visible `:focus-visible` outlines and keyboard-operable Streamlit widgets;
- text/background contrast designed for the dark theme;
- `aria-live` filter-scope updates and descriptive image alternative text;
- `prefers-reduced-motion` support that disables decorative movement;
- Windows forced-colors/high-contrast fallbacks;
- responsive text that remains usable under browser zoom and mobile text scaling.

Plotly chart titles, legends, captions, and evidence tables provide a non-pointer path to the same analytical meaning. Exported result tables remain the authoritative accessible alternative for dense charts.

## Performance budgets

- Dataset preparation is cached by Streamlit.
- Scatter plots use WebGL and deterministic samples capped at 8,000 points.
- The 3D chart is capped at 4,000 WebGL points.
- Histograms are capped at 50,000 sampled rows and correlations at 100,000 rows.
- Hierarchy charts aggregate before serialization instead of sending every transaction to the browser.
- Time, geography, animation, and comparison charts aggregate before rendering.
- PNG/SVG AI chart export is user-triggered instead of running after every answer.
- WebSocket compression is enabled and result tables remain bounded by `MAX_RESULT_ROWS`.

Performance claims must be reported with dataset dimensions, hardware, browser, and warmed median/p95 timings. The application does not claim universal latency independent of deployment resources.

## Application security

- Streamlit CORS and XSRF protections are explicitly enabled.
- Upload and WebSocket message limits are bounded.
- Detailed server exceptions are hidden from browser users.
- Provider endpoints accept only credential-free HTTP(S) URLs from trusted environment configuration.
- Environment-controlled timeouts, retries, output rows, uploads, questions, and dataset dimensions are bounded even when invalid values are supplied.
- Generated SQL and pandas expressions pass the existing AST sandboxes; no `eval` or `exec` is used.
- Prompts delimit cell values as untrusted data, and hosted-provider failures fall back safely.
- API keys remain in environment/hosting secrets and are excluded from Git and Docker build context.

The Docker image runs as an unprivileged user, includes a health check, drops Linux capabilities in Compose, prevents privilege escalation, and uses a read-only application filesystem with bounded temporary mounts. A public production deployment should terminate TLS at a trusted platform or reverse proxy and add organization-specific CSP, HSTS, rate limiting, authentication, and audit retention policies.

## Scalability

The default limits are 200 MB per upload, 5 million processed rows, 500 columns, 1,000 returned rows, and a 10-second query timeout. Tune them only after measuring memory and concurrency on the deployment target.

Streamlit session state is process-local. A multi-instance production deployment should use sticky sessions and external object storage/cache for shared datasets and durable artifacts. For datasets beyond the in-memory envelope, stage approved Parquet files in governed storage and move scanning/aggregation to a managed DuckDB-compatible or warehouse service rather than increasing browser payloads.

## Verification checklist

1. Run `python -m compileall -q app.py config src tests benchmarks`.
2. Run `python -m pytest -q` and coverage/security regression checks.
3. Validate `python -m pip check`, run `python -m pip_audit -r requirements.txt`, and scan staged files for credentials.
4. Run `python -m bandit -r app.py config src benchmarks` for static Python security analysis.
5. Confirm the Streamlit health endpoint.
6. Exercise desktop and mobile navigation, filter reset, AI question, evidence tabs, 3D rotation, and on-demand export.
7. Build the Docker image and confirm it runs as `appuser` when Docker is available.
8. Smoke-test the deployed URL in Chrome/Edge, Firefox, Safari, iOS Safari, and Android Chrome.

The 1.3.0 release passed 67 automated tests with 83% measured coverage. Its dependency audit reported no known vulnerabilities, Bandit reported no unsuppressed findings, and the tracked-file secret signature scan was clean. Docker definitions were statically reviewed and exercised by repository tests; a runtime image build still requires Docker on the workstation or CI runner.
