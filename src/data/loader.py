"""Validated CSV, JSON, and Parquet ingestion."""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from config.settings import Settings
from src.models import DatasetBundle, DatasetMetadata
from src.utils.exceptions import DataLoadError

LOGGER = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".csv", ".json", ".parquet"}


def _read_frame(source: Path | BinaryIO | io.BytesIO, suffix: str) -> pd.DataFrame:
    """Read a supported source into a DataFrame."""
    if suffix == ".csv":
        return pd.read_csv(source, low_memory=False)
    if suffix == ".json":
        try:
            return pd.read_json(source)
        except ValueError:
            if hasattr(source, "seek"):
                source.seek(0)
            return pd.read_json(source, lines=True)
    if suffix == ".parquet":
        return pd.read_parquet(source)
    raise DataLoadError(f"Unsupported file type: {suffix or 'unknown'}")


def load_dataset(
    source: Path | bytes | BinaryIO,
    settings: Settings,
    *,
    filename: str | None = None,
    is_demo: bool = False,
) -> DatasetBundle:
    """Load a controlled path or uploaded byte stream with size and type checks."""
    started = time.perf_counter()
    display_name: str
    read_source: Path | BinaryIO | io.BytesIO
    if isinstance(source, Path):
        path = source.resolve()
        if not path.is_file():
            raise DataLoadError("Dataset file was not found.")
        size = path.stat().st_size
        suffix = path.suffix.lower()
        display_name = path.name
        read_source = path
    else:
        display_name = Path(filename or "upload").name
        suffix = Path(display_name).suffix.lower()
        if isinstance(source, bytes):
            size = len(source)
            read_source = io.BytesIO(source)
        else:
            try:
                current = source.tell()
                source.seek(0, 2)
                size = source.tell()
                source.seek(current)
            except (AttributeError, OSError):
                raise DataLoadError("Uploaded file size could not be validated.") from None
            read_source = source
    if suffix not in ALLOWED_EXTENSIONS:
        raise DataLoadError("Upload a CSV, JSON, or Parquet file.")
    if size > settings.max_upload_mb * 1024 * 1024:
        raise DataLoadError(f"Dataset exceeds the {settings.max_upload_mb} MB upload limit.")
    if size == 0:
        raise DataLoadError("Dataset file is empty.")
    try:
        frame = _read_frame(read_source, suffix)
    except DataLoadError:
        raise
    except Exception as exc:
        LOGGER.exception("dataset_load_failed", extra={"event": "dataset_load"})
        raise DataLoadError("The dataset is malformed or could not be decoded.") from exc
    if frame.empty or len(frame.columns) == 0:
        raise DataLoadError("The dataset contains no usable rows or columns.")
    frame.columns = [str(column).strip() for column in frame.columns]
    elapsed = (time.perf_counter() - started) * 1000
    metadata = DatasetMetadata(
        name=display_name,
        source="demo" if is_demo else "upload" if not isinstance(source, Path) else str(source),
        rows=len(frame),
        columns=len(frame.columns),
        memory_bytes=int(frame.memory_usage(deep=True).sum()),
        load_time_ms=elapsed,
        is_demo=is_demo,
        official_demo_ready=len(frame) >= settings.official_demo_min_rows and not is_demo,
    )
    LOGGER.info(
        "dataset_loaded",
        extra={"event": "dataset_load", "duration_ms": elapsed, "row_count": len(frame), "column_count": len(frame.columns)},
    )
    return DatasetBundle(raw=frame.copy(deep=True), cleaned=frame.copy(deep=True), metadata=metadata)
