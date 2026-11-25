"""Read the ERIC site-data CSV and roll sites up to trusts.

The file has two header rows (field codes, then field names), is encoded
windows-1252 (the m² and m³ in field names break a UTF-8 reader), and uses
the text "Not Applicable" for fields a site does not report. That text means
missing, not zero: an unoccupied site has no gas bill, but the trust has
not told us it used 0 kWh.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from pathlib import Path

import pandas as pd

from . import config

ENCODING = "cp1252"
NUMBER = re.compile(r"^-?\d+(\.\d+)?$")

ID_COLUMNS = {
    "Trust Code": "trust_code",
    "Trust Name": "trust_name",
    "Commissioning Region": "region",
    "Trust Type": "trust_type",
    "EFM Site Id": "efm_site_id",
    "Site Code": "site_code",
    "Site Name": "site_name",
    "Site Type": "site_type",
    "Tenure": "tenure",
    "Type of Lease": "lease_type",
}


class SchemaError(ValueError):
    """The file no longer matches the field contract in config/mapping.yaml."""


def _parse_value(raw: str, na_token: str) -> float:
    if raw == na_token or raw == "":
        return math.nan
    if NUMBER.match(raw):
        return float(raw)
    raise ValueError(raw)


def read_site_csv(path: Path) -> pd.DataFrame:
    text = Path(path).read_bytes().decode(ENCODING)
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if len(rows) < 3:
        raise SchemaError(f"{path}: fewer than three rows")
    codes, names, data = rows[0], rows[1], [r for r in rows[2:] if any(r)]

    id_idx = {}
    for label, key in ID_COLUMNS.items():
        hits = [i for i, n in enumerate(names) if n == label]
        if len(hits) != 1:
            raise SchemaError(f"identifier column {label!r} found {len(hits)} times")
        id_idx[key] = hits[0]

    na = config.mapping()["not_applicable_token"]
    field_idx = {}
    for f in config.eric_fields():
        hits = [i for i, c in enumerate(codes) if c == f.code]
        if len(hits) != 1:
            raise SchemaError(f"field code {f.code} found {len(hits)} times")
        i = hits[0]
        if names[i] != f.name:
            raise SchemaError(f"{f.code}: expected name {f.name!r}, file has {names[i]!r}")
        field_idx[f.key] = i

    records, bad = [], []
    for n, r in enumerate(data, start=3):
        rec = {k: r[i] for k, i in id_idx.items()}
        for key, i in field_idx.items():
            try:
                rec[key] = _parse_value(r[i], na)
            except ValueError:
                bad.append((n, key, r[i]))
                rec[key] = math.nan
        records.append(rec)
    if bad:
        sample = "; ".join(f"row {n} {k}={v!r}" for n, k, v in bad[:5])
        raise SchemaError(f"{len(bad)} non-numeric values in numeric fields: {sample}")
    return pd.DataFrame.from_records(records)


def aggregate_trusts(sites: pd.DataFrame) -> pd.DataFrame:
    keys = config.activity_keys()
    reporting = sites["gas_kwh"].notna()
    g = sites.groupby("trust_code", sort=False)
    out = g[["trust_name", "region", "trust_type"]].first()
    out["n_sites"] = g.size()
    out["n_energy_sites"] = reporting.groupby(sites["trust_code"], sort=False).sum().astype(int)
    out["gia_energy_reporting_m2"] = (
        sites["gia_m2"].where(reporting, 0.0).fillna(0.0).groupby(sites["trust_code"], sort=False).sum()
    )
    sums = g[keys].sum(min_count=0)  # all-missing -> 0, matching the golden extract
    out = out.join(sums)
    # Same rounding as the golden extract, so a raw rebuild is byte-identical
    # rather than differing in the 13th significant figure.
    num = ["gia_energy_reporting_m2", *keys]
    out[num] = out[num].round(6)
    return out.reset_index()[canonical_columns()]


def canonical_columns() -> list[str]:
    return [
        "trust_code", "trust_name", "region", "trust_type",
        "n_sites", "n_energy_sites", "gia_energy_reporting_m2",
        *config.activity_keys(),
    ]


def load_golden() -> pd.DataFrame:
    gd = config.GOLDEN_DIR
    manifest = json.loads((gd / "MANIFEST.json").read_text(encoding="utf-8"))
    act = pd.read_csv(gd / "eric_2025_26_trust_activity.csv", dtype={"trust_code": str})
    code_to_key = {f.code: f.key for f in config.eric_fields()}
    act = act.rename(columns=code_to_key)
    keys = config.activity_keys()
    act[keys] = act[keys].fillna(0.0).astype(float)
    act["region"] = act.pop("region_idx").map(dict(enumerate(manifest["region_idx"])))
    act["trust_type"] = act.pop("type_idx").map(dict(enumerate(manifest["type_idx"])))
    names = pd.read_csv(gd / "eric_2025_26_trust_names.csv", dtype=str)
    gia = pd.read_csv(gd / "eric_2025_26_trust_gia_energy.csv", dtype={"trust_code": str})
    out = act.merge(names, on="trust_code", how="left", validate="1:1")
    out = out.merge(gia, on="trust_code", how="left", validate="1:1")
    out["gia_energy_reporting_m2"] = out["gia_energy_reporting_m2"].astype(float)
    return out[canonical_columns()]


def compare_to_golden(built: pd.DataFrame, golden: pd.DataFrame | None = None) -> list[str]:
    """Return human-readable differences; an empty list means they match."""
    golden = load_golden() if golden is None else golden
    problems: list[str] = []
    b = built.set_index("trust_code")
    gld = golden.set_index("trust_code")
    missing = sorted(set(gld.index) - set(b.index))
    extra = sorted(set(b.index) - set(gld.index))
    if missing:
        problems.append(f"trusts missing from build: {missing}")
    if extra:
        problems.append(f"trusts not in golden: {extra}")
    numeric = ["n_sites", "n_energy_sites", "gia_energy_reporting_m2", *config.activity_keys()]
    for code in sorted(set(b.index) & set(gld.index)):
        for col in ["trust_name", "region", "trust_type"]:
            if b.at[code, col] != gld.at[code, col]:
                problems.append(f"{code} {col}: {b.at[code, col]!r} != {gld.at[code, col]!r}")
        for col in numeric:
            x, y = float(b.at[code, col]), float(gld.at[code, col])
            if not math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-6):
                problems.append(f"{code} {col}: built {x} != golden {y}")
    return problems
