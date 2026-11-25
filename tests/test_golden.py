"""The committed extracts are exactly what was verified at source."""
import hashlib
import json

import pandas as pd
import pytest

from nhs_ghg import config

MANIFEST = json.loads((config.GOLDEN_DIR / "MANIFEST.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name,digest", MANIFEST["files"].items())
def test_golden_file_unchanged(name, digest):
    assert hashlib.sha256((config.GOLDEN_DIR / name).read_bytes()).hexdigest() == digest


def test_golden_sums_to_recorded_national_totals():
    df = pd.read_csv(config.GOLDEN_DIR / "eric_2025_26_trust_activity.csv")
    for code, expected in MANIFEST["national_totals"].items():
        assert df[code].fillna(0).sum() == pytest.approx(expected, abs=1e-3), code


def test_energy_reconciles_to_nhs_published_total(golden):
    energy_cols = [
        "gas_kwh", "oil_kwh", "biofuel_kwh", "elec_green_tariff_kwh", "elec_other_kwh",
        "elec_chp_import_kwh", "elec_solar_own_kwh", "elec_solar_3p_kwh", "elec_other_renewables_kwh",
        "heat_chp_import_kwh", "steam_kwh", "hot_water_kwh",
    ]
    total = golden[energy_cols].sum().sum()
    assert total == pytest.approx(11.2e9, abs=0.05e9)  # "11.2 billion kWh" on the ERIC 2025/26 page
    # ...and adding CHP gas input as well would overshoot badly, so it is not added (D2).
    assert total + golden["chp_gas_input_kwh"].sum() > 14e9


def test_golden_has_one_row_per_trust(golden):
    assert golden["trust_code"].is_unique
    assert len(golden) == 205
    assert golden["trust_name"].notna().all()
    assert golden["region"].notna().all() and golden["trust_type"].notna().all()
