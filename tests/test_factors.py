"""Pinned DESNZ factors: integrity, use, and the check against the official file."""
import hashlib

from openpyxl import Workbook

from conftest import raw_or_skip
from nhs_ghg import config, factors

# SHA-256 of the subset as produced from the official file (verified 2026-11-25).
PINNED_SHA256 = "30d0d2762b7cf4265be840093c1c010f72f70cd1cd9bb0a58bc6958d06a5ef11"


def test_pinned_subset_unchanged():
    assert hashlib.sha256(config.FACTOR_SUBSET.read_bytes()).hexdigest() == PINNED_SHA256


def test_headline_values(pinned):
    assert pinned.loc["1_100_1004_6_1", "factor"] == 0.18296  # natural gas, kWh gross CV
    assert pinned.loc["7_400_4000_5_1", "factor"] == 0.177    # UK grid electricity
    assert pinned.loc["1_100_1004_6_1", "uom"] == "kWh (Gross CV)"


def test_every_mapped_factor_is_pinned_and_a_string(pinned):
    for ln in config.mapping()["emission_lines"]:
        assert isinstance(ln["factor"], str), ln["line"]  # regression: YAML read 1_100_... as an int
        assert ln["factor"] in pinned.index, ln["line"]


def test_every_pinned_factor_is_used_or_documented(pinned):
    used = {ln["factor"] for ln in config.mapping()["emission_lines"]}
    unused = set(pinned.index) - used
    assert unused == {"1_100_1003_6_1"}  # LPG: kept only to bound decision D4


def _fake_flat(path, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Factors by Category"
    for _ in range(5):
        ws.append([None])
    ws.append([*factors.FLAT_HEADER, "GHG Conversion Factor 2025"])
    for r in rows:
        ws.append(r)
    wb.save(path)


def _official_row(pinned, fid, value=None):
    r = pinned.loc[fid]
    return [fid, *[r[c] or None for c in factors.TEXT_COLUMNS], r["factor"] if value is None else value]


def test_verifier_passes_matching_file(tmp_path, pinned):
    p = tmp_path / "flat.xlsx"
    _fake_flat(p, [_official_row(pinned, fid) for fid in pinned.index])
    assert factors.verify_against_official(p, pinned) == []


def test_verifier_catches_a_changed_value(tmp_path, pinned):
    p = tmp_path / "flat.xlsx"
    rows = [_official_row(pinned, fid, 0.20705 if fid == "7_400_4000_5_1" else None) for fid in pinned.index]
    _fake_flat(p, rows)
    problems = factors.verify_against_official(p, pinned)
    assert len(problems) == 1 and "7_400_4000_5_1 factor" in problems[0]


def test_verifier_catches_a_missing_row(tmp_path, pinned):
    p = tmp_path / "flat.xlsx"
    _fake_flat(p, [_official_row(pinned, fid) for fid in pinned.index if fid != "17_404_4005_1_1"])
    assert factors.verify_against_official(p, pinned) == ["17_404_4005_1_1: not in official file"]


def test_pinned_matches_official_desnz_file(pinned):
    path = raw_or_skip("desnz_2025_flat")
    assert factors.verify_against_official(path, pinned) == []
