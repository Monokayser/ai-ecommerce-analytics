# v1.12.4 Release Notes

## Runtime and interaction optimization

- Data Exploration now builds only the selected visualization instead of constructing nine Plotly figures on every rerun.
- Advanced Analytics and Data Quality use lazy workspaces so hidden models and tables do not execute unnecessarily.
- Filter choices, ranges, and quality statistics are prepared once with the cached dataset.
- Global filters now combine predicates into one vectorized mask and use pandas copy-on-write views.
- Chart constructors project only required columns and retain bounded WebGL payloads.
- PDF and Word reports are generated on demand and reused for the active verified result.
- Infinite scan effects were replaced with one-time and hover feedback; expensive mobile blur and fixed-background effects are disabled.

## Measured local evidence

On the development workstation, a deterministic 200,000-row filter benchmark improved from a 121.68 ms median to 48.83 ms (2.49× faster). On the 2,000-row demo dataset, constructing the active exploration view took 84.14 ms versus 1,224.00 ms for the former all-view construction path, a 93.1% reduction. These results are hardware- and dataset-specific and are not universal performance claims.
