"""Command line: fetch, verify, build activity, run the inventory."""
from __future__ import annotations

import argparse
import sys

from . import config, eric, factors, fetch, inventory, quality, report


def cmd_fetch(args) -> int:
    for name, path in fetch.fetch_all(force=args.force).items():
        print(f"ok  {name}: {path.relative_to(config.ROOT)} (sha256 verified)")
    return 0


def cmd_verify(args) -> int:
    failed = False
    xlsx = config.raw_path("desnz_2025_flat")
    if xlsx.exists():
        fetch.verify(xlsx, config.sources()["sources"]["desnz_2025_flat"])
        problems = factors.verify_against_official(xlsx)
        print(f"{'FAIL' if problems else 'ok  '} pinned factors vs official DESNZ file: {len(problems)} differences")
        for p in problems:
            print("    ", p)
        failed |= bool(problems)
    else:
        print("skip pinned factors: official DESNZ file not downloaded (run `nhs-ghg fetch`)")
    site = config.raw_path("eric_2025_26_site")
    if site.exists():
        fetch.verify(site, config.sources()["sources"]["eric_2025_26_site"])
        built = eric.aggregate_trusts(eric.read_site_csv(site))
        problems = eric.compare_to_golden(built)
        print(f"{'FAIL' if problems else 'ok  '} trust activity rebuilt from raw ERIC vs golden: {len(problems)} differences")
        for p in problems[:20]:
            print("    ", p)
        failed |= bool(problems)
    else:
        print("skip trust activity: raw ERIC file not downloaded (run `nhs-ghg fetch`)")
    return 1 if failed else 0


def build_activity(source: str):
    if source == "raw":
        site = config.raw_path("eric_2025_26_site")
        fetch.verify(site, config.sources()["sources"]["eric_2025_26_site"])
        built = eric.aggregate_trusts(eric.read_site_csv(site))
        problems = eric.compare_to_golden(built)
        if problems:
            raise SystemExit("raw rebuild differs from golden:\n" + "\n".join(problems[:20]))
        return built, "the raw ERIC site file (checked against the golden extract)"
    return eric.load_golden(), "the verified golden extract in tests/golden/"


def cmd_run(args) -> int:
    source = args.source
    if source == "auto":
        source = "raw" if config.raw_path("eric_2025_26_site").exists() else "golden"
    activity, label = build_activity(source)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    activity.to_csv(config.TRUST_ACTIVITY, index=False)
    f = factors.load_pinned()
    items = inventory.line_items(activity, f)
    summary = inventory.summarise(items, activity)
    flags = quality.flag(activity)
    report.write_outputs(summary, items, flags, activity, label)
    tot = summary[["scope1_t", "scope2_location_t", "scope2_market_t", "scope3_t", "total_location_t"]].sum() / 1000
    print(f"source: {label}")
    print(f"trusts: {len(summary)}  flags raised: {len(flags)}")
    print("kt CO2e  " + "  ".join(f"{k}={v:,.1f}" for k, v in tot.items()))
    print(f"outputs written to {config.OUTPUT_DIR.relative_to(config.ROOT)}/")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="nhs-ghg", description="NHS trust estate GHG inventory (ERIC 2025/26 x DESNZ 2025)")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download pinned sources and verify their SHA-256")
    f.add_argument("--force", action="store_true")
    f.set_defaults(func=cmd_fetch)
    v = sub.add_parser("verify", help="check pinned factors and the golden extract against the raw sources")
    v.set_defaults(func=cmd_verify)
    r = sub.add_parser("run", help="build the inventory and write outputs/")
    r.add_argument("--source", choices=["auto", "raw", "golden"], default="auto")
    r.set_defaults(func=cmd_run)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
