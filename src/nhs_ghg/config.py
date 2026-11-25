"""Paths and configuration loading."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"
PROCESSED_DIR = DATA_DIR / "processed"
GOLDEN_DIR = ROOT / "tests" / "golden"
OUTPUT_DIR = ROOT / "outputs"

FACTOR_SUBSET = REFERENCE_DIR / "desnz_2025_factor_subset.csv"
TRUST_ACTIVITY = PROCESSED_DIR / "trust_activity_2025_26.csv"


@dataclass(frozen=True)
class Field:
    code: str
    key: str
    unit: str
    name: str


@lru_cache(maxsize=None)
def sources() -> dict:
    return yaml.safe_load((CONFIG_DIR / "sources.yaml").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def mapping() -> dict:
    return yaml.safe_load((CONFIG_DIR / "mapping.yaml").read_text(encoding="utf-8"))


def eric_fields() -> list[Field]:
    return [Field(**f) for f in mapping()["eric_fields"]]


def activity_keys() -> list[str]:
    return [f.key for f in eric_fields()]


def raw_path(source_name: str) -> Path:
    return RAW_DIR / sources()["sources"][source_name]["filename"]
