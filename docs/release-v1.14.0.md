# v1.14.0 Release Notes

## Midnight Analytics redesign

- Rebuilt the visual system from the supplied dark financial-dashboard reference using a near-black canvas, graphite cards, cyan analytical accents, compact controls, and stronger information hierarchy.
- Updated the sidebar, filters, upload surface, six-section navigation, hero, KPI cards, alerts, tabs, expanders, tables, AI workspace, report controls, and floating agent launcher.
- Re-themed the full Plotly chart suite, including timelines, maps, hierarchies, 3D scenes, animated charts, hover labels, range controls, and modebars.
- Preserved real chart data and labels while changing only their presentation.

## Accessibility and performance

- Retained minimum 44px targets, visible focus, forced-colors support, responsive navigation, and complete reduced-motion behavior.
- Avoided backdrop blur, parallax, layout animation, and perpetual full-screen motion.
- Kept chart hover effects repaint-safe and removed decorative layers on narrow mobile screens.

## Documentation and QA

- Added the Midnight Analytics design-system specification and research rationale.
- Added regression coverage for the new token palette, native Streamlit configuration, chart palette, static background treatment, and accessibility states.
