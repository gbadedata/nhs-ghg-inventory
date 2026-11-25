# East Suffolk and North Essex NHS Foundation Trust (RDE) - 2025/26

A worked example of the audit trail: every number below can be recomputed by hand as activity x factor, and every factor found in the DESNZ 2025 flat file by its ID.

- Trust type: Acute - Large; East of England Commissioning Region
- Sites: 19, of which 6 report energy (195,024 m² of floor area). The other 13 report 'Not Applicable' for energy (leased sites the landlord services wholly or partly, or unoccupied). Some of that use may belong in the trust's own Scope 1-2; it is a known gap (D3).

## Totals (t CO2e)

|  | t CO2e |
|---|---|
| Scope 1 | 4,911.9 |
| Scope 2 (location) | 5,672.3 |
| Scope 2 (market, approximate) | 0.1 |
| Scope 3 (cat 1, 3, 5) | 3,808.5 |
| Total (location) | 14,392.7 |
| Total (market) | 8,720.6 |
| Outside of scopes (biogenic CO2) | 6,874.3 |

Scope 1+2 (location) intensity: 54.3 kg CO2e/m². Energy: 77.35 GWh.

## Line items

| scope | line | activity | activity_value | activity_unit | factor_id | factor_kgco2e_per_unit | basis | tCO2e |
|---|---|---|---|---|---|---|---|---|
| Scope 1 | S1_gas | gas_kwh | 25,612,532.00 | kWh | 1_100_1004_6_1 | 0.18296 | both | 4,686.07 |
| Scope 1 | S1_biofuel | biofuel_kwh | 19,640,789.00 | kWh | 2_104_1045_5_1 | 0.01150 | both | 225.87 |
| Scope 2 | S2_elec_loc | grid_elec_kwh | 32,046,822.00 | kWh | 7_400_4000_5_1 | 0.17700 | location | 5,672.29 |
| Scope 2 | S2_elec_mkt | market_elec_kwh | 735.00 | kWh | 7_400_4000_5_1 | 0.17700 | market | 0.13 |
| Scope 3 | S3_wtt_gas | gas_kwh | 25,612,532.00 | kWh | 11_100_1004_6_1 | 0.03021 | both | 773.75 |
| Scope 3 | S3_wtt_biofuel | biofuel_kwh | 19,640,789.00 | kWh | 12_901_1045_5_1 | 0.03744 | both | 735.35 |
| Scope 3 | S3_wtt_elec_gen | grid_elec_kwh | 32,046,822.00 | kWh | 15_917_4000_5_1 | 0.04590 | both | 1,470.95 |
| Scope 3 | S3_td_elec | grid_elec_kwh | 32,046,822.00 | kWh | 13_402_4000_5_1 | 0.01853 | both | 593.83 |
| Scope 3 | S3_wtt_td_elec | grid_elec_kwh | 32,046,822.00 | kWh | 15_918_4000_5_1 | 0.00397 | both | 127.23 |
| Scope 3 | S3_water_supply | water_m3 | 285,680.00 | m3 | 17_404_4005_1_1 | 0.19130 | both | 54.65 |
| Scope 3 | S3_wastewater | wastewater_m3 | 271,396.00 | m3 | 18_405_4006_1_1 | 0.17088 | both | 46.38 |
| Scope 3 | S3_waste_recycling | waste_domestic_recycling_t | 688.22 | tonnes | 20_506_5450_15_1 | 4.68568 | both | 3.22 |
| Scope 3 | S3_waste_incin | waste_domestic_incin_t | 527.30 | tonnes | 20_507_5311_15_1 | 4.68568 | both | 2.47 |
| Scope 3 | S3_waste_food | waste_domestic_food_t | 40.00 | tonnes | 20_507_5293_15_1 | 8.98311 | both | 0.36 |
| Scope 3 | S3_waste_confidential | waste_confidential_t | 64.70 | tonnes | 20_506_5457_15_1 | 4.68568 | both | 0.30 |
| Outside of scopes | OOS_biofuel_co2 | biofuel_kwh | 19,640,789.00 | kWh | 99_104_1045_5_2 | 0.35000 | both | 6,874.28 |

## Waste not converted

| Stream | Tonnes |
|---|---|
| waste_clinical_incin_t | 1,021.60 |
| waste_clinical_alt_t | 172.07 |
| waste_offensive_t | 581.01 |

## Data-quality flags

| check | description | detail |
|---|---|---|
| DQ04 | Non-fossil renewable fuel is at least 25% of fuel burned: the unspecified-fuel assumption (wood pellets, D6) matters | biofuel 19,640,789 kWh = 43% of fuel burned |
| DQ08 | Fewer than half of sites report energy (the rest are mostly landlord-serviced leases): coverage gap | 6 of 19 sites |
