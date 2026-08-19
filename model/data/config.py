"""Environment-driven configuration for the AI Hub data pipeline."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AihubConfig:
    api_key: str | None
    dataset_key: str
    file_keys: list[str]
    data_dir: Path


def load_config() -> AihubConfig:
    file_keys_raw = os.environ.get("AIHUB_FILE_KEYS", "").strip()
    file_keys = [key.strip() for key in file_keys_raw.split(",") if key.strip()]
    return AihubConfig(
        api_key=os.environ.get("AIHUB_API_KEY") or None,
        dataset_key=os.environ.get("AIHUB_DATASET_KEY", "71792"),
        file_keys=file_keys,
        data_dir=Path(os.environ.get("AIHUB_DATA_DIR", "./data/raw")),
    )
