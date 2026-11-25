from pathlib import Path

import pytest

from nhs_ghg import config, eric, factors

FIXTURE = Path(__file__).parent / "fixtures" / "eric_2025_26_site_RDE.csv"


@pytest.fixture(scope="session")
def fixture_sites():
    return eric.read_site_csv(FIXTURE)


@pytest.fixture(scope="session")
def golden():
    return eric.load_golden()


@pytest.fixture(scope="session")
def pinned():
    return factors.load_pinned()


def raw_or_skip(name: str) -> Path:
    path = config.raw_path(name)
    if not path.exists():
        pytest.skip(f"{path.name} not downloaded; run `nhs-ghg fetch`")
    return path
