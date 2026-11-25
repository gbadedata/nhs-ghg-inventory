# NHS trust estate GHG inventory, 2025/26

A Scope 1, 2 and 3 greenhouse-gas inventory for the estate of every NHS trust in England, built from NHS
England's published estates data (ERIC 2025/26) and the UK Government's 2025 conversion factors. Every
tonne traces back to one activity figure, one factor ID and one documented decision.

**2.49 Mt CO2e** location-based (2.29 Mt market-based) across 205 trusts and 2,165 sites, for
1 April 2025 to 31 March 2026.

| kt CO2e | Location-based | Market-based |
|---|---:|---:|
| Scope 1 (gas, oil, biofuel) | 1,493.2 | 1,493.2 |
| Scope 2 (electricity, heat) | 532.5 | 337.2 |
| Scope 3 (categories 1, 3 and 5) | 464.3 | 464.3 |
| **Total** | **2,490.0** | **2,294.7** |
| Outside of scopes (biogenic CO2) | 11.4 | 11.4 |

Full results: [outputs/SUMMARY.md](outputs/SUMMARY.md). One trust, line by line:
[East Suffolk and North Essex](outputs/trusts/RDE.md).

## What the data showed

- **Market-based reporting hides over a third of Scope 2.** 40% of grid electricity is on REGO-backed green
  tariffs, so market-based Scope 2 is 37% below location-based. East Suffolk and North Essex's market-based
  Scope 2 is 0.1 t against 5,672 t location-based. Dual reporting matters.
- **44% of reported NHS waste has no DESNZ factor.** 162,743 t of clinical, offensive and on-site-treated waste is
  carried in tonnes, not converted. Using DESNZ's incineration factor, which covers only transport, would
  have understated it. This is the largest known gap.
- **The obvious join double counts.** ERIC reports CHP gas input separately, but "Gas consumed" already
  includes it. The energy fields sum to 11.21 TWh, matching NHS England's published 11.2 billion kWh;
  adding CHP input would give 14.28 TWh. The PFI file overlaps the site file the same way.
- **35 data-quality flags across 32 trusts**, including two trusts whose CHP gas exceeds their total gas
  (which ERIC's own definitions rule out), and one where green-tariff and other electricity carry the same
  4,094,352 kWh.

## How the inputs are verified

- **Pinned sources.** Both files are pinned by URL, byte size and SHA-256 ([config/sources.yaml](config/sources.yaml)).
  `nhs-ghg fetch` refuses anything that has changed.
- **Pinned factors.** Only the 23 DESNZ rows used are committed, each with all its descriptive columns.
  `nhs-ghg verify` re-reads the official flat file and fails on any difference.
- **Two independent implementations.** The trust totals in [tests/golden](tests/golden/) were computed by a
  separate JavaScript reader run against the official CSV. The Python pipeline must reproduce them: for one
  trust's 19 raw rows on every test run, and for the whole file in `nhs-ghg verify`. A second, end-to-end
  recomputation from the raw rows gives the same total for all 205 trusts, to the kilogram.
- **A field contract.** ERIC's field codes are not stable: the 2025/26 definitions workbook numbers the
  same fields differently from the CSV. The reader matches every field on code *and* exact name, decodes
  windows-1252, and rejects any value that is neither a number nor "Not Applicable".
- **Mapping guards.** Before any arithmetic, each line's factor must exist, share the line's scope, and be
  per the activity's unit. Writing the factor IDs unquoted in YAML turns `1_100_1004_6_1` into the integer
  1100100461. This guard caught that on the first run, and a test now keeps it from coming back.

Every judgement call (LPG inside gas, unspecified oil and biofuel, residual mix, wastewater share, factor
year) is written up with its reason and effect in [METHODOLOGY.md](METHODOLOGY.md).

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                 # 47 tests; 2 need the raw downloads and skip without them
nhs-ghg run            # writes outputs/ (from the verified golden extract if raw files are absent)

nhs-ghg fetch          # downloads both sources from gov.uk / NHS England and checks SHA-256
nhs-ghg verify         # pinned factors vs official DESNZ file; raw ERIC rebuild vs golden
nhs-ghg run --source raw
```

Or `make all`. Python 3.10+, pandas, PyYAML, openpyxl.

## Layout

```
config/sources.yaml        pinned URLs, sizes, SHA-256, reporting period
config/mapping.yaml        ERIC field contract, field -> factor lines, parameters
data/reference/            the 23 DESNZ 2025 factor rows used
data/processed/            trust activity table (written by `run`)
src/nhs_ghg/               fetch, eric (reader + roll-up), factors, inventory, quality, report, cli
tests/golden/              independently computed trust totals + manifest of hashes
tests/fixtures/            19 raw ERIC rows for one trust, byte-for-byte format of the source
outputs/                   trust inventory, line-item audit trail, data-quality flags, summary
```

## Scope and limits

This is an estate inventory: energy, water and waste. It does not cover refrigerants, anaesthetic and
inhaler gases, vehicle fuel, travel or the supply chain, which for most trusts are larger than the estate.
Sites that report "Not Applicable" for energy (mostly leases serviced by the landlord) are not estimated.
Market-based Scope 2 uses the grid average for non-REGO supply because DESNZ publishes no residual mix, so it is
a lower bound. See [METHODOLOGY.md](METHODOLOGY.md#not-included).

## Data licence

Contains public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/):
NHS England, *Estates Returns Information Collection 2025/26*; Department for Energy Security and Net Zero,
*Greenhouse gas reporting: conversion factors 2025*. Code: MIT.
