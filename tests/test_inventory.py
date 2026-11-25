"""Emission arithmetic, scope logic and the guards on the mapping."""
import pytest

from nhs_ghg import config, inventory


@pytest.fixture(scope="module")
def result(golden, pinned):
    items = inventory.line_items(golden, pinned)
    return items, inventory.summarise(items, golden).set_index("trust_code")


def test_rde_by_hand(result):
    """East Suffolk and North Essex, recomputed from the raw site rows and the DESNZ values."""
    _, s = result
    r = s.loc["RDE"]
    gas, biofuel = 25_612_532, 19_640_789
    grid = 32_046_087 + 735 + 0          # green tariff + other + CHP import
    assert r["scope1_t"] == pytest.approx((gas * 0.18296 + biofuel * 0.0115) / 1000)
    assert r["scope2_location_t"] == pytest.approx(grid * 0.177 / 1000)
    assert r["scope2_market_t"] == pytest.approx(735 * 0.177 / 1000)  # REGO tariff counted at zero
    assert r["outside_scopes_t"] == pytest.approx(biofuel * 0.35 / 1000)


def test_wastewater_uses_return_fraction(result):
    items, _ = result
    ww = items[(items["trust_code"] == "RDE") & (items["line"] == "S3_wastewater")].iloc[0]
    assert ww["activity_value"] == pytest.approx(285_680 * 0.95)
    assert ww["kgco2e"] == pytest.approx(285_680 * 0.95 * 0.17088)


def test_outside_of_scopes_never_in_totals(result):
    _, s = result
    assert (s["total_location_t"] == s["scope1_t"] + s["scope2_location_t"] + s["scope3_t"]).all()


def test_market_never_exceeds_location(result):
    _, s = result
    assert (s["scope2_market_t"] <= s["scope2_location_t"] + 1e-9).all()


def test_scope3_categories_add_up(result):
    _, s = result
    parts = s["scope3_cat1_t"] + s["scope3_cat3_t"] + s["scope3_cat5_t"]
    assert parts.values == pytest.approx(s["scope3_t"].values)


def test_national_scope1_from_gas_dominates(result):
    items, _ = result
    gas_kt = items.loc[items["line"] == "S1_gas", "kgco2e"].sum() / 1e6
    assert gas_kt == pytest.approx(8_076_793_595 * 0.18296 / 1e6)


def _line(**kw):
    base = {"line": "X", "scope": "Scope 1", "category": "c", "activity": "gas_kwh",
            "factor": "1_100_1004_6_1", "basis": "both"}
    return {**base, **kw}


def test_mapping_guard_scope_mismatch(pinned):
    with pytest.raises(ValueError, match="Scope 1 but factor"):
        inventory.check_mapping(pinned, [_line(factor="11_100_1004_6_1")])  # a WTT (Scope 3) factor


def test_mapping_guard_unit_mismatch(pinned):
    with pytest.raises(ValueError, match="activity in m3"):
        inventory.check_mapping(pinned, [_line(activity="water_m3")])


def test_mapping_guard_unquoted_yaml_id(pinned):
    with pytest.raises(TypeError, match="quote it"):
        inventory.check_mapping(pinned, [_line(factor=1100100461)])


def test_every_mapped_activity_exists(golden):
    df = inventory.add_derived(golden)
    for ln in config.mapping()["emission_lines"]:
        assert ln["activity"] in df.columns, ln["line"]


def test_totals_match_independent_end_to_end_recomputation(result):
    """Every trust's total equals a separate JavaScript recomputation from the raw site rows."""
    import pandas as pd

    _, s = result
    js = pd.read_csv(config.GOLDEN_DIR / "eric_2025_26_trust_totals_independent.csv").set_index("trust_code")
    assert set(js.index) == set(s.index)
    assert (js["loc_t"] - s.loc[js.index, "total_location_t"]).abs().max() < 0.0006
    assert (js["mkt_t"] - s.loc[js.index, "total_market_t"]).abs().max() < 0.0006
