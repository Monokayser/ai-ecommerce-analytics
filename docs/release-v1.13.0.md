# v1.13.0 Release Notes

## Smooth scrolling

- Removed fixed background attachment and continuous full-page aurora movement.
- Replaced desktop backdrop blur on the header, sticky navigation, hero, and agent launcher with opaque composited surfaces.
- Disabled chart mouse-wheel zoom so the page keeps control of normal scrolling.
- Reduced repaint-heavy chart hover filters and broad container entrance animations.
- Preserved responsive hover feedback and complete reduced-motion behavior.

## More capable analytics agent

- Expanded the typed plan with analytical intent, user-facing plan steps, assumptions, and dataset-grounded follow-up questions.
- Added deterministic support for period growth, percentage contribution, profit margin, distributions, data quality, multi-metric analysis, and two-dimensional comparisons.
- Added contextual follow-up resolution for short requests such as "now by category" in no-key mode.
- Added one bounded retry for malformed Gemini structured output before the safe local fallback.
- Lazily renders only the selected Answer, Chart, Data, or Verification workspace.
- Generates Word/PDF and PNG/SVG deliverables only when requested.

## Verification

- 119 Python tests pass, including the expanded analytics task matrix.
- The browser-verified local agent executed a 36-period growth task through planning, validation, DuckDB execution, and grounded response assembly.
- The assistant rendered zero Plotly charts in Answer view and exactly one after Chart was selected.
- The main scroll container responded to forward and reverse wheel input, uses `scroll-behavior: auto`, has no horizontal overflow, and has no custom fixed blur layers.

The hosted model remains Gemini 3.6 Flash. It proposes typed plans only; all data access remains application-controlled, read-only, bounded, and locally revalidated.
