"""Turn trust activity into an auditable line-item inventory and scope totals."""
from __future__ import annotations

import pandas as pd

from . import config

UNIT_OK = {
    "kWh": {"kWh", "kWh (Gross CV)"},
    "m3": {"cubic metres"},
    "tonnes": {"tonnes"},
}
DERIVED_UNITS = {"grid_elec_kwh": "kWh", "market_elec_kwh": "kWh", "heat_kwh": "kWh", "wastewater_m3": "m3"}

ENERGY_KEYS = [
    "gas_kwh", "oil_kwh", "biofuel_kwh",
    "elec_green_tariff_kwh", "elec_other_kwh", "elec_chp_import_kwh",
    "elec_solar_own_kwh", "elec_solar_3p_kwh", "elec_other_renewables_kwh",
    "heat_chp_import_kwh", "steam_kwh", "hot_water_kwh",
]


def activity_units() -> dict[str, str]:
    units = {f.key: f.unit for f in config.eric_fields()}
    units.update(DERIVED_UNITS)
    return units


def add_derived(activity: pd.DataFrame) -> pd.DataFrame:
    m = config.mapping()
    df = activity.copy()
    for name, spec in m["derived"].items():
        if isinstance(spec, list):
            df[name] = df[spec].sum(axis=1)
        else:
            df[name] = df[spec["from"]] * m["parameters"][spec["times_parameter"]]
    df["energy_kwh"] = df[ENERGY_KEYS].sum(axis=1)
    return df


def check_mapping(factors: pd.DataFrame, lines: list[dict] | None = None) -> None:
    """Fail before computing anything if a line points at a wrong factor."""
    units = activity_units()
    for ln in config.mapping()["emission_lines"] if lines is None else lines:
        if not isinstance(ln["factor"], str):
            raise TypeError(f"{ln['line']}: factor ID {ln['factor']!r} is not a string (quote it in YAML)")
        fid = ln["factor"]
        if fid not in factors.index:
            raise KeyError(f"{ln['line']}: factor {fid} is not in the pinned subset")
        f = factors.loc[fid]
        if f["scope"].lower() != ln["scope"].lower():
            raise ValueError(f"{ln['line']}: line is {ln['scope']} but factor {fid} is {f['scope']}")
        unit = units[ln["activity"]]
        if f["uom"] not in UNIT_OK[unit]:
            raise ValueError(f"{ln['line']}: activity in {unit} but factor {fid} is per {f['uom']}")
        if ln["scope"] != "Outside of scopes" and f["ghg_unit"] != "kg CO2e":
            raise ValueError(f"{ln['line']}: factor {fid} is {f['ghg_unit']}, expected kg CO2e")


def line_items(activity: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    check_mapping(factors)
    df = add_derived(activity)
    units = activity_units()
    parts = []
    for ln in config.mapping()["emission_lines"]:
        f = factors.loc[ln["factor"]]
        part = pd.DataFrame({
            "trust_code": df["trust_code"],
            "line": ln["line"],
            "scope": ln["scope"],
            "category": ln["category"],
            "basis": ln["basis"],
            "activity": ln["activity"],
            "activity_value": df[ln["activity"]].astype(float),
            "activity_unit": units[ln["activity"]],
            "factor_id": ln["factor"],
            "factor_label": " / ".join(x for x in [f["level_1"], f["level_2"], f["level_3"], f["column_text"]] if x),
            "factor_uom": f["uom"],
            "factor_kgco2e_per_unit": f["factor"],
        })
        part["kgco2e"] = part["activity_value"] * part["factor_kgco2e_per_unit"]
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def summarise(items: pd.DataFrame, activity: pd.DataFrame) -> pd.DataFrame:
    t = items.assign(t=items["kgco2e"] / 1000.0)

    def total(mask) -> pd.Series:
        return t[mask].groupby("trust_code")["t"].sum()

    s = pd.DataFrame(index=activity["trust_code"])
    s["scope1_t"] = total(t["scope"] == "Scope 1")
    s["scope2_location_t"] = total((t["scope"] == "Scope 2") & t["basis"].isin(["location", "both"]))
    s["scope2_market_t"] = total((t["scope"] == "Scope 2") & t["basis"].isin(["market", "both"]))
    s["scope3_cat1_t"] = total(t["category"].str.startswith("Cat 1"))
    s["scope3_cat3_t"] = total(t["category"].str.startswith("Cat 3"))
    s["scope3_cat5_t"] = total(t["category"].str.startswith("Cat 5"))
    s["scope3_t"] = total(t["scope"] == "Scope 3")
    s["outside_scopes_t"] = total(t["scope"] == "Outside of scopes")
    s = s.fillna(0.0)
    s["total_location_t"] = s["scope1_t"] + s["scope2_location_t"] + s["scope3_t"]
    s["total_market_t"] = s["scope1_t"] + s["scope2_market_t"] + s["scope3_t"]

    a = add_derived(activity).set_index("trust_code")
    s["energy_kwh"] = a["energy_kwh"]
    gia = a["gia_energy_reporting_m2"].where(a["gia_energy_reporting_m2"] > 0)
    s["energy_kwh_per_m2"] = a["energy_kwh"] / gia
    s["s1_s2_location_kg_per_m2"] = (s["scope1_t"] + s["scope2_location_t"]) * 1000.0 / gia
    unq = config.mapping()["unquantified_waste"]
    q = [ln["activity"] for ln in config.mapping()["emission_lines"] if ln["category"] == "Cat 5 - Waste"]
    s["waste_quantified_t"] = a[q].sum(axis=1)
    s["waste_unquantified_t"] = a[unq].sum(axis=1)
    meta = a[["trust_name", "region", "trust_type", "n_sites", "n_energy_sites", "gia_energy_reporting_m2"]]
    return meta.join(s).reset_index()
