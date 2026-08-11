# Deployment Guide

## Streamlit Community Cloud

The project is ready for a public GitHub-backed deployment. Streamlit Community Cloud rebuilds the application when commits are pushed to the selected branch.

1. Push the full repository to GitHub. Keep it public for the free Community Cloud workflow.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub.
3. Select the repository, branch `main`, and entry point `app.py`.
4. Open Advanced settings, choose Python 3.11, and add secrets as shown below.
5. Deploy, wait for the health check, and test dataset loading, one AI question, filters, and one chart export.

### Secrets

Add these in Streamlit's secrets editor; never commit them:

```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "replace_with_real_key"
GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_MAX_OUTPUT_TOKENS = "4096"
LLM_QUERY_REASONING_EFFORT = "medium"
LLM_NARRATIVE_REASONING_EFFORT = "low"
LLM_RESPONSE_VERBOSITY = "low"
```

The app also works without these entries using the deterministic local planner. `packages.txt` installs Chromium for Kaleido; `runtime.txt` selects Python 3.11.

### Deployment verification

- The app opens without an exception and shows the demo-data banner.
- All six sections are reachable.
- AI mode accurately reports hosted Gemini or local fallback.
- A question returns a validated query and evidence table.
- Upload rejection, filter reset, and empty states are clear.
- PNG/SVG export capability is reported; if Chromium is unavailable, the UI gives an actionable message.

## Docker

```powershell
docker build -t ai-ecommerce-analytics .
docker run --env-file .env -p 8501:8501 ai-ecommerce-analytics
```

For Ollama, use `docker compose up --build`, pull the configured model into the Ollama service, and restart the application.

## GitHub release checklist

1. Run compilation, the full test suite, dependency validation, and the secret scan.
2. Confirm `.env`, `.streamlit/secrets.toml`, private datasets, generated reports, caches, and the virtual environment are ignored.
3. Review `git diff --cached` and repository file sizes.
4. Push `main` and confirm GitHub Actions succeeds.
5. Record measured benchmark results only after configuring a real provider key and approved dataset.

The reproducible GitHub Actions definition is stored at `docs/github-actions-ci.yml`. Copy it to `.github/workflows/ci.yml` after authorizing GitHub's `workflow` OAuth scope; GitHub blocks workflow uploads from tokens that have only repository scope.

## Troubleshooting

- **Hosted AI falls back:** verify the secret name, model name, API quota, and provider status. The local planner remains usable.
- **Module import failure:** confirm all runtime packages are pinned in `requirements.txt`, not only in `requirements-dev.txt`.
- **Static export failure:** inspect the startup capability message and confirm `packages.txt` installed Chromium.
- **Memory restart:** reduce the upload limit or pre-aggregate a large dataset; Community Cloud has finite resources.
- **Private data risk:** remove the dataset from the public deployment and rotate any exposed key immediately.

Primary references: [deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization), and [manage an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).
