"""Dataset loader tests."""

from __future__ import annotations

import json

import pytest

from config.settings import Settings
from src.data.loader import load_dataset
from src.utils.exceptions import DataLoadError


def test_valid_csv_loading(tmp_path, ecommerce_frame):
    path = tmp_path / "orders.csv"
    ecommerce_frame.to_csv(path, index=False)
    bundle = load_dataset(path, Settings())
    assert bundle.metadata.rows == 6
    assert bundle.metadata.columns == len(ecommerce_frame.columns)
    assert bundle.metadata.load_time_ms >= 0


def test_json_and_parquet_loading(tmp_path, ecommerce_frame):
    json_path = tmp_path / "orders.json"
    parquet_path = tmp_path / "orders.parquet"
    ecommerce_frame.to_json(json_path, orient="records", date_format="iso")
    ecommerce_frame.to_parquet(parquet_path)
    assert load_dataset(json_path, Settings()).metadata.rows == 6
    assert load_dataset(parquet_path, Settings()).metadata.rows == 6


@pytest.mark.parametrize("name,content", [("orders.exe", b"bad"), ("empty.csv", b"")])
def test_invalid_file_handling(name, content):
    with pytest.raises(DataLoadError):
        load_dataset(content, Settings(), filename=name)


def test_malformed_csv_returns_user_safe_error():
    with pytest.raises(DataLoadError):
        load_dataset(b'"unterminated', Settings(), filename="bad.csv")
