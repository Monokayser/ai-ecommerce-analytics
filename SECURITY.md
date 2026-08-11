# Security Policy

## Supported version

Security fixes target the latest release on `main`.

## Reporting a vulnerability

Do not open a public issue for a vulnerability or exposed credential. Use GitHub's private vulnerability reporting for this repository. Include the affected version, a minimal reproduction, impact, and any proposed mitigation. Please remove real customer data and API keys from evidence.

## Operational guidance

- Keep `.env` and `.streamlit/secrets.toml` outside version control.
- Use least-privilege API keys and rotate a key immediately if it is exposed.
- Do not deploy private customer data to a public demonstration instance.
- Review dependency alerts and rerun the security regression suite after parser, DuckDB, or AI-provider upgrades.
- Treat generated SQL, uploaded cell text, and model output as untrusted input.

The application sandbox reduces risk but is not intended to execute arbitrary user code.
