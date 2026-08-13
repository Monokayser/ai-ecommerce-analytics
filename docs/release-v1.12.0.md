# v1.12.0 Release Notes

## Added

- One authoritative version module and a subtle live build marker.
- Stable Gemini 3.6 Flash configuration with structured Interactions API output and expanded failure-path tests.
- Playwright/axe QA for Chrome, Edge, Firefox, WebKit, Chromium, and mobile emulation.
- Eight-size responsive matrix, touch-target, equal-spacing, focus, reduced-motion, overflow, and console assertions.
- Active GitHub CI for quality, browsers, container health, and six-hour production smoke checks.
- Dataset/hardware-specific median/p95 performance evidence and production recovery documentation.

## Changed

- Native Streamlit colors now match the emerald application palette.
- Deprecated Streamlit width parameters were replaced with the current responsive width API.
- Disabled controls and the deployment verification state have clearer theme-consistent presentation.

## Security and operations

- Secrets stay out of Git and chat; production Gemini configuration belongs only in Streamlit's secrets editor.
- The Docker runtime remains unprivileged and is built and health-tested in CI.
- `main` is protected after the first successful workflow run; pull requests and required checks are enforced while force pushes and branch deletion remain blocked.

No live Gemini benchmark or official-dataset result is claimed until those checks are executed with user-managed credentials and approved data.
