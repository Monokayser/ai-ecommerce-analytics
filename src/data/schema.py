"""Column canonicalization and LLM-ready schema inspection."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.models import ColumnProfile, SchemaProfile


def normalize_name(value: str) -> str:
    """Normalize a header or alias for deterministic matching."""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def load_aliases(path: Path) -> dict[str, list[str]]:
    """Load canonical-to-alias mappings."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {str(key): [str(item) for item in values] for key, values in data.items()}


def canonicalize_columns(
    frame: pd.DataFrame, aliases: dict[str, list[str]]
) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """Rename unambiguous aliases while reporting collisions and ambiguity."""
    canonical_norm = {normalize_name(name): name for name in aliases}
    reverse: dict[str, list[str]] = {}
    for canonical, values in aliases.items():
        for value in [canonical, *values]:
            reverse.setdefault(normalize_name(value), []).append(canonical)
    present_canonical = {canonical_norm[norm] for norm in canonical_norm if norm in {normalize_name(c) for c in frame.columns}}
    rename: dict[str, str] = {}
    mapping: dict[str, str] = {}
    warnings: list[str] = []
    used_targets = set(present_canonical)
    for column in frame.columns:
        norm = normalize_name(column)
        candidates = list(dict.fromkeys(reverse.get(norm, [])))
        if norm in canonical_norm:
            mapping[column] = canonical_norm[norm]
            if column != canonical_norm[norm]:
                rename[column] = canonical_norm[norm]
            continue
        if len(candidates) == 1 and candidates[0] not in used_targets:
            rename[column] = candidates[0]
            mapping[column] = candidates[0]
            used_targets.add(candidates[0])
        elif len(candidates) > 1:
            mapping[column] = column
            warnings.append(f"Ambiguous alias '{column}' could mean: {', '.join(candidates)}.")
        elif candidates and candidates[0] in used_targets:
            mapping[column] = column
            warnings.append(f"Column '{column}' was not renamed because '{candidates[0]}' already exists.")
        else:
            mapping[column] = column
    return frame.rename(columns=rename), mapping, warnings


def semantic_role(column: str, series: pd.Series) -> str:
    """Infer a compact semantic role from name and dtype."""
    name = normalize_name(column)
    if "id" in name or name.endswith("code"):
        return "identifier"
    if pd.api.types.is_datetime64_any_dtype(series) or "date" in name or "time" in name:
        return "date"
    if any(token in name for token in ("country", "region", "city", "state", "location")):
        return "geographic"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric measure"
    unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
    return "category" if unique_ratio < 0.2 else "text"


def _json_value(value: Any) -> Any:
    """Convert pandas scalars into safe JSON-like values."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value.item() if hasattr(value, "item") else value


def inspect_schema(frame: pd.DataFrame, canonical_map: dict[str, str] | None = None) -> SchemaProfile:
    """Build a complete serializable schema profile."""
    started = time.perf_counter()
    profiles: list[ColumnProfile] = []
    for column in frame.columns:
        series = frame[column]
        non_null = series.dropna()
        numeric = pd.to_numeric(non_null, errors="coerce") if not pd.api.types.is_datetime64_any_dtype(series) else None
        minimum = maximum = mean = median = None
        if pd.api.types.is_datetime64_any_dtype(series) and not non_null.empty:
            minimum, maximum = _json_value(non_null.min()), _json_value(non_null.max())
        elif numeric is not None and numeric.notna().sum() == len(non_null) and not non_null.empty:
            minimum, maximum = _json_value(numeric.min()), _json_value(numeric.max())
            mean, median = float(numeric.mean()), float(numeric.median())
        samples = [_json_value(value) for value in non_null.drop_duplicates().head(5).tolist()]
        profiles.append(
            ColumnProfile(
                name=column,
                canonical_name=(canonical_map or {}).get(column, column),
                dtype=str(series.dtype),
                semantic_role=semantic_role(column, series),
                unique_count=int(series.nunique(dropna=True)),
                missing_count=int(series.isna().sum()),
                missing_percent=round(float(series.isna().mean() * 100), 3),
                minimum=minimum,
                maximum=maximum,
                mean=mean,
                median=median,
                samples=samples,
            )
        )
    elapsed = (time.perf_counter() - started) * 1000
    return SchemaProfile(columns=profiles, generated_at=datetime.now(timezone.utc), generation_time_ms=elapsed)


def schema_for_llm(profile: SchemaProfile, max_sample_chars: int = 120) -> str:
    """Serialize bounded schema context without treating cell samples as instructions."""
    payload = profile.model_dump(mode="json")
    for column in payload["columns"]:
        column["samples"] = [str(value)[:max_sample_chars] for value in column["samples"]]
    return json.dumps(payload, ensure_ascii=True)
