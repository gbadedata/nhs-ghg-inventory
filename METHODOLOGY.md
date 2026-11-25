# Methodology and decisions

This is the document a reviewer or verifier should read. It sets out the boundary, how each ERIC field maps
to a DESNZ factor, and every judgement call, with its reason and the size of its effect where that is known.
Each decision has an ID (D1-D13) that the code, config and outputs refer to.

Standard followed: the GHG Protocol Corporate Standard and Scope 2 Guidance, using the UK Government
conversion factors (DESNZ 2025) as the UK SECR guidance recommends.

## Sources

| | Source | Pinned by |
|---|---|---|
| Activity | NHS England, *Estates Returns Information Collection (ERIC) 2025/26*, site data v3, published 15 Oct 2026. Covers 1 Apr 2025 to 31 Mar 2026. | URL, 6,184,296 bytes, SHA-256 `b77cf695...` |
| Factors | DESNZ, *GHG Conversion Factors for Company Reporting 2025*, flat file, version 1 (final). | URL, 505,634 bytes, SHA-256 `8bfdb45b...` |

Both are under the Open Government Licence v3.0. Full URLs and hashes: [config/sources.yaml](config/sources.yaml).
The DESNZ file's hash matches one recorded independently by another public project, which downloaded it
directly from gov.uk on 2026-09-15.

## Field to factor mapping

| ERIC field (CSV code) | Activity | Scope / category | DESNZ factor (ID) | kg CO2e per unit |
|---|---|---|---|---|
| Gas consumed (S05_11) | gas_kwh | Scope 1 | Natural gas, kWh gross CV (1_100_1004_6_1) | 0.18296 |
| | | Scope 3 cat 3 | WTT natural gas (11_100_1004_6_1) | 0.03021 |
| Oil consumed (S05_12) | oil_kwh | Scope 1 | Gas oil, kWh gross CV (1_101_1014_6_1) | 0.25650 |
| | | Scope 3 cat 3 | WTT gas oil (11_101_1014_6_1) | 0.05913 |
| Non-fossil fuel - renewable consumed (S22_06) | biofuel_kwh | Scope 1 | Wood pellets, CH4 + N2O (2_104_1045_5_1) | 0.0115 |
| | | Scope 3 cat 3 | WTT wood pellets (12_901_1045_5_1) | 0.03744 |
| | | Outside of scopes | Wood pellets, biogenic CO2 (99_104_1045_5_2) | 0.35 |
| Electricity - green tariff + other + purchased from CHP (S05_14, S05_41, S05_52) | grid_elec_kwh | Scope 2 location | UK electricity (7_400_4000_5_1) | 0.17700 |
| | | Scope 3 cat 3 | WTT generation (15_917_4000_5_1), T&D (13_402_4000_5_1), WTT T&D (15_918_4000_5_1) | 0.04590, 0.01853, 0.00397 |
| Electricity - other + purchased from CHP (S05_41, S05_52) | market_elec_kwh | Scope 2 market | UK electricity (7_400_4000_5_1) | 0.17700 |
| Steam + hot water + thermal energy purchased from CHP (S06_08, S06_09, S05_54) | heat_kwh | Scope 2 | District heat and steam (10_401_4003_5_1) | 0.17529 |
| | | Scope 3 cat 3 | WTT heat (16_919_4003_5_1), distribution loss (13_403_4004_5_1), WTT loss (16_920_4004_5_1) | 0.03341, 0.00945, 0.00176 |
| Water volume (S09_01) | water_m3 | Scope 3 cat 1 | Water supply (17_404_4005_1_1) | 0.1913 |
| | wastewater_m3 = 95% of water | Scope 3 cat 5 | Water treatment (18_405_4006_1_1) | 0.17088 |
| Domestic waste - landfill (S10_48) | | Scope 3 cat 5 | C&I waste, landfill (20_507_5313_15_1) | 520.53 per t |
| Domestic waste - recycling (S10_50) | | Scope 3 cat 5 | Paper and board mixed, closed-loop (20_506_5450_15_1) | 4.69 per t |
| Domestic waste - incineration (S10_74) | | Scope 3 cat 5 | C&I waste, incineration with energy recovery (20_507_5311_15_1) | 4.69 per t |
| Domestic waste - food (S10_52) | | Scope 3 cat 5 | Food and drink waste, anaerobic digestion (20_507_5293_15_1) | 8.98 per t |
| Confidential waste (S10_64) | | Scope 3 cat 5 | Paper and board, closed-loop (20_506_5457_15_1) | 4.69 per t |
| Trust-owned solar, third-party solar, other renewables (S05_35, S05_37, S05_39) | | Zero in both Scope 2 methods (D5) | - | 0 |
| Clinical, offensive and on-site-treated waste (6 fields) | | Reported in tonnes, not converted (D9) | - | - |
| Fossil gas input to CHP (S04_31) | | Not used: already inside S05_11 (D2) | - | - |

The mapping is code, not prose: [config/mapping.yaml](config/mapping.yaml). Before any arithmetic the
pipeline checks that each line's factor exists, is in the same scope as the line, and is per the same unit
as the activity.

## Decisions

**D1. Boundary: the sites each trust reports utilities for.**
The inventory covers all 205 trusts in ERIC and, within them, the 2,165 sites that report energy. That is the
nearest the data gets to an operational-control boundary. Private Finance Initiative (PFI) sites are already
in the site file: all 146 sites in ERIC's separate PFI file also appear there. Where both files give a gas
figure and they differ (50 sites), the site file's is always the larger, so the PFI file covers part of a
site and adding it would double count. It is not used.

**D2. Gas fed to CHP is already inside "Gas consumed".**
ERIC's definition of *Gas consumed* says to include gas used to feed CHP plant, and CHP gas input is also
reported separately (3.07 TWh nationally). Summing the energy fields without CHP input gives 11.21 TWh,
against the 11.2 billion kWh NHS England publishes for 2025/26; adding it would give 14.28 TWh. So the
published total confirms the definition, and CHP input is used only as a check (flag DQ05 fires for two
trusts whose CHP gas exceeds their total gas, which the definition says cannot happen).

**D3. "Not Applicable" means missing, not zero.**
ERIC writes "Not Applicable" where a site does not report a field. For energy that is 758 of 2,923 sites:
all 416 leased sites fully serviced by the landlord, 338 of the 556 leased and part serviced, and 4
unoccupied sites. The reader keeps these as missing and rejects any other text in a numeric field.
Consumption at those sites is not estimated. Under operational control
some of it may belong in the trust's Scope 1-2 (or in Scope 3 category 8 if the trust is a tenant without
control). Flag DQ08 lists the 24 trusts where fewer than half of sites report energy.

**D4. "Gas consumed" includes LPG; all of it is treated as natural gas.**
ERIC folds LPG into gas with no split. The DESNZ LPG factor (0.2145) is 17% above natural gas (0.18296),
so any LPG in the figure is understated by up to that much. Mains gas dominates NHS estates, so the effect
is expected to be small, but it cannot be sized from ERIC. The LPG factor is pinned only to record this bound.

**D5. Scope 2 is dual-reported; the market-based figure is approximate.**
Location-based: all electricity delivered over the grid or bought from a neighbour's CHP, at the UK grid
average. Market-based: electricity on a green tariff (which ERIC's definition requires to be backed by REGO
certificates) at zero, and the rest at the grid average. DESNZ publishes no residual-mix factor, and a
residual mix is normally above the grid average, so this understates market-based Scope 2. Electricity
bought from another organisation's CHP is treated as grid electricity for want of supplier-specific data.
On-site solar and private-wire renewables are not drawn from the grid and count as zero under both methods.
The effect is large: green tariffs are 40% of grid-delivered NHS electricity, 85 trusts are over 90% green
tariff and 98 have none, so market-based Scope 2 is 37% below location-based (337 vs 532 kt).

**D6. Unspecified renewable fuel is treated as wood pellets.**
ERIC's *Non-fossil fuel - renewable consumed* covers biomass, biogas and other renewable fuels without
saying which. Wood pellets shares its Scope 1 factor (0.0115) with wood chips and logs and has the highest
WTT factor of the DESNZ biomass and biogas options (0.03744, against 0.00792 for chips and 0.01851 for
biogas), so it is the conservative choice. Biogenic CO2 is reported outside the scopes, as DESNZ and the GHG
Protocol require. Flag DQ04 marks trusts where this fuel is at least 25% of fuel burned. At East Suffolk and
North Essex it is 43% (19.6 GWh, all at Ipswich Hospital). There the choice moves Scope 3 by up to 0.58 kt
(wood chips instead) and Scope 1 by 0.22 kt (biogas instead), so the fuel type should be confirmed with the
trust.

**D7. Unspecified oil is treated as gas oil.**
ERIC's *Oil consumed* includes heating oil and diesel for generators. Gas oil (0.2565) is the usual fuel
for oil-fired boilers and standby generators. Diesel (average biofuel blend) is 0.24411, 5% lower, so the choice moves Scope 1
by at most 0.8 kt nationally.

**D8. Purchased steam, hot water and CHP heat use the district heat factor.**
All three come from another organisation's plant. DESNZ's district heat and steam factor applies, with its
5% distribution-loss and WTT lines in Scope 3 category 3.

**D9. Clinical and offensive waste is reported but not converted.**
DESNZ has no factor for clinical waste. Its *incineration with energy recovery* factor (4.69 kg/t) covers
only transport to the plant, because DESNZ assigns combustion emissions to the energy produced. Applied to
clinical waste, much of which is burned in dedicated incinerators, that would understate emissions, so these
six streams (162,743 tonnes, 44% of all waste reported) are carried in tonnes with no CO2e. This is the largest
known gap in Scope 3. Healthcare-specific factors exist outside the DESNZ set and would be the next step.

**D10. Water: supply in category 1, wastewater in category 5.**
Wastewater volume is taken as 95% of supply, the standard UK return-to-sewer allowance used in sewerage
charging. It is a parameter in `config/mapping.yaml`. At 100% the national figure would rise by 0.3 kt.

**D11. 2025 factors, using the DESNZ "majority" approach.**
DESNZ says an April to March reporting year should use the factors for the calendar year holding most of
the data, so 2025/26 uses the 2025 set. DESNZ also allows a "blended" approach (2025 factors for April to
December, 2026 for January to March). This inventory does not compute it.

**D12. How the inputs are verified.**
- Both sources are pinned by URL, size and SHA-256. `nhs-ghg fetch` refuses a file that differs.
- Only the 23 factor rows used are committed ([data/reference](data/reference/desnz_2025_factor_subset.csv)),
  with every descriptive column, and `nhs-ghg verify` re-reads the official DESNZ file and fails on any
  difference.
- The trust totals in [tests/golden](tests/golden/) were computed by a separate implementation (JavaScript,
  run in a browser against the official CSV), not by this code. The Python reader must reproduce them: on the
  19 committed raw rows for one trust in every test run, and on the full file in `nhs-ghg verify` and CI.
- The final per-trust totals were also recomputed end to end by that separate implementation, from the raw
  site rows and the DESNZ values. All 205 trusts match the Python inventory to the kilogram, for both
  location- and market-based totals, and a test holds them there.
- The reader matches each field on code *and* exact name, because ERIC's codes are not stable: the 2025/26
  Data Definitions workbook numbers the same fields differently from the CSV (e.g. *Steam consumed* is S06_08
  in the CSV and S07_22 in the definitions, where S06_08 is *Exported electricity*).
- The file is decoded as windows-1252, not UTF-8 (its field names contain m² and m³ in that encoding).

**D13. Data-quality flags never change a number.**
Nine checks (DQ01-DQ09) list entries a reviewer should query with the trust: duplicated figures, placeholder
values, contradictions with ERIC's own definitions, outlying energy intensity and low coverage. Correcting
them is the trust's job; the inventory reports them.

## Not included

ERIC describes estates, so this is an estate inventory, not an NHS trust's full footprint. It omits:
refrigerant leaks (F-gases), anaesthetic and inhaler gases, owned and leased vehicles (including ambulance
fuel), business travel and commuting, and purchased goods and services beyond water. For most trusts the
supply chain and medicines are far larger than the estate.

## Reproducing a number by hand

Every row of [outputs/line_items_2025_26.csv](outputs/line_items_2025_26.csv) is one activity x one factor.
For example, East Suffolk and North Essex's gas: 25,612,532 kWh x 0.18296 kg/kWh = 4,686,068 kg = 4,686.1 t
CO2e, factor `1_100_1004_6_1` in the DESNZ 2025 flat file. [outputs/trusts/RDE.md](outputs/trusts/RDE.md)
walks through the whole trust.
