"""DESNZ conversion factors: the pinned subset and its check against the source.

Only the 23 factor rows this inventory uses are committed, copied with every
descriptive column so a reviewer can find each one in the official file by
its ID. `verify_against_official` re-reads the full DESNZ flat file and fails
if any pinned row differs in any column.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config

TEXT_COLUMNS = ["scope", "level_1", "level_2", "level_3", "level_4", "column_text", "uom", "ghg_unit"]
FLAT_HEADER = ["ID", "Scope", "Level 1", "Level 2", "Level 3", "Level 4", "Column Text", "UOM", "GHG/Unit"]


def load_pinned(path: Path = config.FACTOR_SUBSET) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if df["id"].duplicated().any():
        raise ValueError("duplicate factor IDs in pinned subset")
    df["factor"] = df["factor_raw"].astype(float)
    return df.set_index("id")


def read_official_flat(path: Path) -> dict[str, list]:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb["Factors by Category"]
    rows = ws.iter_rows(values_only=True)
    for row in rows:
        if row and row[0] == "ID":
            header = list(row)
            break
    else:
        raise ValueError("header row not found in 'Factors by Category'")
    if header[: len(FLAT_HEADER)] != FLAT_HEADER or not str(header[9]).startswith("GHG Conversion Factor"):
        raise ValueError(f"unexpected flat-file header: {header[:10]}")
    out = {}
    for row in rows:
        if row and row[0]:
            out[row[0]] = ["" if v is None else v for v in row[:10]]
    wb.close()
    return out


def verify_against_official(xlsx_path: Path, pinned: pd.DataFrame | None = None) -> list[str]:
    pinned = load_pinned() if pinned is None else pinned
    official = read_official_flat(xlsx_path)
    problems = []
    for fid, row in pinned.iterrows():
        if fid not in official:
            problems.append(f"{fid}: not in official file")
            continue
        o = official[fid]
        for col, val in zip(TEXT_COLUMNS, o[1:9], strict=True):
            if str(val) != row[col]:
                problems.append(f"{fid} {col}: pinned {row[col]!r}, official {val!r}")
        if float(o[9]) != row["factor"]:
            problems.append(f"{fid} factor: pinned {row['factor']}, official {o[9]}")
    return problems
