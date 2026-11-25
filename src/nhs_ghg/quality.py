"""Data-quality checks on trust activity.

These do not change any number. They mark entries a reviewer should query
with the trust before the inventory is relied on, the way a verifier would.
"""
from __future__ import annotations

import pandas as pd

from .inventory import ENERGY_KEYS, add_derived

PLACEHOLDER_MAX_KWH = 10  # a whole-site annual figure below this is almost certainly a stub
PEER_MIN = 5              # smallest trust-type group used for the intensity check
OUTLIER_FACTOR = 3.0      # flag intensity outside [median/3, median*3] for the trust type
BIOFUEL_SHARE = 0.25      # biofuel share of combustion energy above which D6 is material

CHECKS = {
    "DQ01": "Green-tariff and other electricity are identical (likely the same figure entered twice)",
    "DQ02": "Two heat fields are identical (steam, hot water, CHP heat) - possible double entry",
    "DQ03": f"An energy field is between 0 and {PLACEHOLDER_MAX_KWH} kWh for the whole year (likely a placeholder)",
    "DQ04": f"Non-fossil renewable fuel is at least {BIOFUEL_SHARE:.0%} of fuel burned: the unspecified-fuel assumption (wood pellets, D6) matters",
    "DQ05": "Gas fed to CHP exceeds total gas consumed, which ERIC's definitions say includes CHP feed",
    "DQ06": "Gas reported but no electricity of any kind",
    "DQ07": f"Energy intensity outside 1/{OUTLIER_FACTOR:g}x-{OUTLIER_FACTOR:g}x the median for its trust type",
    "DQ08": "Fewer than half of sites report energy (the rest are mostly landlord-serviced leases): coverage gap",
    "DQ09": "Energy reported but no water",
}


def flag(activity: pd.DataFrame) -> pd.DataFrame:
    a = add_derived(activity).set_index("trust_code")
    rows = []

    def add(code: str, mask: pd.Series, detail: pd.Series) -> None:
        for tc in mask[mask].index:
            rows.append({"trust_code": tc, "check": code, "detail": detail.get(tc, "")})

    green, other = a["elec_green_tariff_kwh"], a["elec_other_kwh"]
    add("DQ01", (green > 0) & (green == other), green.map(lambda v: f"both {v:,.0f} kWh"))

    pairs = [("steam_kwh", "hot_water_kwh"), ("steam_kwh", "heat_chp_import_kwh"), ("hot_water_kwh", "heat_chp_import_kwh")]
    for x, y in pairs:
        add("DQ02", (a[x] > 0) & (a[x] == a[y]), a[x].map(lambda v, x=x, y=y: f"{x} = {y} = {v:,.0f} kWh"))

    energy = a[ENERGY_KEYS + ["chp_gas_input_kwh"]]
    stub = (energy > 0) & (energy < PLACEHOLDER_MAX_KWH)
    detail = stub.apply(lambda r: ", ".join(f"{k}={energy.at[r.name, k]:g}" for k in r.index[r]), axis=1)
    add("DQ03", stub.any(axis=1), detail)

    burned = a["gas_kwh"] + a["oil_kwh"] + a["biofuel_kwh"]
    share = (a["biofuel_kwh"] / burned.where(burned > 0)).fillna(0.0)
    add("DQ04", share >= BIOFUEL_SHARE,
        a.apply(lambda r: f"biofuel {r.biofuel_kwh:,.0f} kWh = {share[r.name]:.0%} of fuel burned", axis=1))

    add("DQ05", a["chp_gas_input_kwh"] > a["gas_kwh"],
        a.apply(lambda r: f"CHP gas {r.chp_gas_input_kwh:,.0f} vs gas {r.gas_kwh:,.0f} kWh", axis=1))

    elec_any = a["grid_elec_kwh"] + a["elec_solar_own_kwh"] + a["elec_solar_3p_kwh"] + a["elec_other_renewables_kwh"]
    add("DQ06", (a["gas_kwh"] > 0) & (elec_any == 0), pd.Series("", index=a.index))

    gia = a["gia_energy_reporting_m2"].where(a["gia_energy_reporting_m2"] > 0)
    intensity = a["energy_kwh"] / gia
    med = intensity.groupby(a["trust_type"]).transform("median")
    n = intensity.groupby(a["trust_type"]).transform("count")
    out = (n >= PEER_MIN) & ((intensity > med * OUTLIER_FACTOR) | (intensity < med / OUTLIER_FACTOR))
    add("DQ07", out.fillna(False),
        pd.Series({tc: f"{intensity[tc]:,.0f} kWh/m² vs type median {med[tc]:,.0f}" for tc in a.index if pd.notna(intensity[tc])}))

    cov = a["n_energy_sites"] / a["n_sites"]
    add("DQ08", cov < 0.5, a.apply(lambda r: f"{r.n_energy_sites} of {r.n_sites} sites", axis=1))

    add("DQ09", (a["energy_kwh"] > 0) & (a["water_m3"] == 0), pd.Series("", index=a.index))

    flags = pd.DataFrame(rows, columns=["trust_code", "check", "detail"])
    flags["description"] = flags["check"].map(CHECKS)
    names = a["trust_name"]
    flags.insert(1, "trust_name", flags["trust_code"].map(names))
    return flags.sort_values(["check", "trust_code"]).reset_index(drop=True)
