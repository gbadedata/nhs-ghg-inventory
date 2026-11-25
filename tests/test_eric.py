"""The ERIC reader: encoding, header contract, 'Not Applicable', roll-up."""
import math

import pytest

from conftest import FIXTURE, raw_or_skip
from nhs_ghg import config, eric


def test_fixture_reads_all_sites(fixture_sites):
    assert len(fixture_sites) == 19
    assert set(fixture_sites["trust_code"]) == {"RDE"}


def test_not_applicable_is_missing_not_zero(fixture_sites):
    mill_road = fixture_sites.set_index("site_name").loc["MILL ROAD THERAPY CENTRE"]
    assert math.isnan(mill_road["gas_kwh"])
    assert mill_road["waste_confidential_t"] == pytest.approx(0.09)  # real value on the same row


def test_values_parse_exactly(fixture_sites):
    ipswich = fixture_sites.set_index("site_name").loc["IPSWICH HOSPITAL"]
    assert ipswich["gas_kwh"] == 4303136
    assert ipswich["biofuel_kwh"] == 19640789
    assert ipswich["elec_green_tariff_kwh"] == 15766562
    assert ipswich["waste_clinical_incin_t"] == 395


def test_roll_up_matches_independent_extract(fixture_sites, golden):
    """The Python roll-up of RDE's 19 raw rows equals the browser-computed golden row."""
    built = eric.aggregate_trusts(fixture_sites)
    problems = eric.compare_to_golden(built, golden[golden["trust_code"] == "RDE"])
    assert problems == []


def test_file_must_be_read_as_windows_1252():
    raw = FIXTURE.read_bytes()
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    assert "m²" in raw.decode("cp1252")


def _mutated(tmp_path, old: str, new: str):
    text = FIXTURE.read_bytes().decode("cp1252")
    assert old in text
    p = tmp_path / "mutated.csv"
    p.write_bytes(text.replace(old, new, 1).encode("cp1252"))
    return p


def test_renamed_field_is_refused(tmp_path):
    p = _mutated(tmp_path, "Steam consumed (kWh)", "Exported electricity (kWh)")
    with pytest.raises(eric.SchemaError, match="S06_08"):
        eric.read_site_csv(p)


def test_unexpected_text_value_is_refused(tmp_path):
    p = _mutated(tmp_path, ",4303136,", ",4.3m,")
    with pytest.raises(eric.SchemaError, match="non-numeric"):
        eric.read_site_csv(p)


def test_missing_field_code_is_refused(tmp_path):
    p = _mutated(tmp_path, "S05_11", "S05_99")
    with pytest.raises(eric.SchemaError, match="S05_11"):
        eric.read_site_csv(p)


def test_full_raw_file_rebuilds_golden():
    path = raw_or_skip("eric_2025_26_site")
    built = eric.aggregate_trusts(eric.read_site_csv(path))
    assert eric.compare_to_golden(built) == []


def test_canonical_columns_cover_every_mapped_field():
    cols = eric.canonical_columns()
    assert all(k in cols for k in config.activity_keys())
