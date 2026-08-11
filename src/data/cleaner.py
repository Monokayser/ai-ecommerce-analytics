"""Auditable, non-destructive e-commerce data cleaning."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from src.data.schema import canonicalize_columns
from src.models import CleaningAction

DATE_COLUMNS = {"Order Date", "Ship Date"}
NUMERIC_COLUMNS = {"Sales", "Quantity", "Discount", "Profit"}


def _flag_name(column: str) -> str:
    return "_outlier_" + re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_")


def clean_dataset(
    frame: pd.DataFrame,
    aliases: dict[str, list[str]],
    *,
    remove_duplicates: bool = True,
) -> tuple[pd.DataFrame, list[CleaningAction], list[str], dict[str, str]]:
    """Return a cleaned copy, a transparent cleaning log, and warnings."""
    cleaned, source_map, warnings = canonicalize_columns(frame.copy(deep=True), aliases)
    log: list[CleaningAction] = []
    for column in DATE_COLUMNS.intersection(cleaned.columns):
        before_non_null = int(cleaned[column].notna().sum())
        parsed = pd.to_datetime(cleaned[column], errors="coerce")
        invalid = before_non_null - int(parsed.notna().sum())
        cleaned[column] = parsed
        log.append(CleaningAction(operation="parse_date", column=column, affected_rows=invalid, detail="Invalid values set to missing."))
    for column in NUMERIC_COLUMNS.intersection(cleaned.columns):
        original_non_null = int(cleaned[column].notna().sum())
        converted = pd.to_numeric(cleaned[column], errors="coerce")
        invalid = original_non_null - int(converted.notna().sum())
        cleaned[column] = converted
        log.append(CleaningAction(operation="convert_numeric", column=column, affected_rows=invalid, detail="Unparseable values set to missing."))
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        before = cleaned[column].astype("string")
        after = before.str.strip().str.replace(r"\s+", " ", regex=True)
        changed = int((before.fillna("") != after.fillna("")).sum())
        cleaned[column] = after
        log.append(CleaningAction(operation="standardize_text", column=column, affected_rows=changed, detail="Trimmed and collapsed whitespace."))
    duplicate_count = int(cleaned.duplicated().sum())
    if remove_duplicates and duplicate_count:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    log.append(CleaningAction(operation="remove_exact_duplicates" if remove_duplicates else "retain_exact_duplicates", affected_rows=duplicate_count))
    for column in [c for c in cleaned.select_dtypes(include=np.number).columns if not c.startswith("_outlier_")]:
        series = cleaned[column]
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        mask = pd.Series(False, index=cleaned.index) if pd.isna(iqr) else (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)
        cleaned[_flag_name(column)] = mask.fillna(False)
        log.append(CleaningAction(operation="mark_iqr_outliers", column=column, affected_rows=int(mask.sum()), detail="Rows marked; values were not removed or capped."))
    return cleaned, log, warnings, source_map
