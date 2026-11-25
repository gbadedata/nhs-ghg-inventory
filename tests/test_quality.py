"""Each data-quality check fires on the real case that motivated it."""
import pytest

from nhs_ghg import quality


@pytest.fixture(scope="module")
def flags(golden):
    f = quality.flag(golden)
    return set(zip(f["trust_code"], f["check"], strict=True))


@pytest.mark.parametrize("trust,check", [
    ("RXT", "DQ01"),  # green tariff == other electricity, 4,094,352 kWh each
    ("REN", "DQ02"),  # steam == CHP heat, 3,264,586 kWh each
    ("RRE", "DQ03"),  # steam = 1 kWh for a year
    ("RDE", "DQ04"),  # 19.6 GWh unspecified biofuel = 43% of fuel burned
    ("RJ7", "DQ05"),  # CHP gas input larger than total gas
    ("RDE", "DQ08"),  # 6 of 19 sites report energy
])
def test_known_case_is_flagged(flags, trust, check):
    assert (trust, check) in flags


def test_flags_do_not_change_activity(golden):
    before = golden.copy()
    quality.flag(golden)
    assert golden.equals(before)
