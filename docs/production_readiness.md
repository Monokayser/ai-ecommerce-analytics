# Production Readiness — v1.14.0

## Release scope

Version `v1.14.0` preserves the six-section public Streamlit Community Cloud application while introducing the researched Midnight Analytics theme. The release maintains the single version source, machine-verifiable build marker, stable Gemini 3.6 Flash configuration, deterministic fallback, responsive and accessibility automation, measurable performance evidence, active CI, non-root container verification, and scheduled production smoke checks.

## Acceptance evidence

| Area | Automated evidence | Release condition |
|---|---|---|
| Python quality | Compile, full pytest suite, coverage XML | At least 85% coverage |
| Dependencies | `pip check`, pip-audit | No broken or known-vulnerable pinned dependency |
| Security | Bandit, Gitleaks, AST sandbox tests | No unsuppressed finding or committed secret |
| Exports | Word, PDF, PNG, SVG generation and signatures | All fixtures reopen or validate |
| Accessibility | axe WCAG tags, keyboard focus, reduced motion | No unwaived serious/critical issue |
| Responsive UI | Eight viewport sizes | No overflow, balanced nav, ≥44 px targets |
| Browsers | Chrome, Edge, Firefox, WebKit, Chromium, mobile emulation | Functional suite succeeds |
| Container | Build, non-root identity, startup health | Healthy unprivileged runtime |
| Production | Live DOM and `data-app-version` polling | Expected version and six workspaces visible |

Authentication is explicitly not applicable because the approved application remains public. The public deployment must use only synthetic or otherwise publication-approved data.

## AI release gate

Production secrets are entered only in Streamlit Community Cloud. A configured Gemini request must produce schema-valid output that passes the same local SQL/pandas validation as deterministic planning. Authentication, rate limit, timeout, server failure, empty output, truncated JSON, and invalid schema paths are tested with mocks. A provider failure must disclose fallback without exposing provider payloads, hidden reasoning, or secrets.

## Known limitations

- Streamlit Community Cloud availability and compute are platform-dependent; the project provides detection and recovery, not a permanent uptime guarantee.
- The official/private business dataset was not used for public QA. Performance acceptance against it remains a separately measured gate.
- WebKit automation is not branded Safari. Manual Safari and iOS Safari results must be recorded by the release owner.
- Conversations are session-local and there is no viewer authentication or durable audit store.
- Streamlit 1.61 emits a third-party axe issue for `aria-expanded` on its sidebar `<section>`; the test waiver matches only that exact node.

## Release procedure

Feature branch → pull request → required CI → merge to `main` → automatic Streamlit rebuild → production smoke → manual Safari check → tag and GitHub release. If production verification fails, do not tag; follow the recovery procedure in `docs/deployment.md`.
