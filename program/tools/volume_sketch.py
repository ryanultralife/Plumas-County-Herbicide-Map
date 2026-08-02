#!/usr/bin/env python3
"""
Landscape MBF sketch: clearcut baseline vs multi-entry working forest.

ILLUSTRATIVE until defaults are replaced with Plumas / mill / CalTREES inputs.
Exit code 0 always (it is a calculator). Prints PASS/FAIL/UNKNOWN for T1 volume only.

Usage:
  python program/tools/volume_sketch.py
  python program/tools/volume_sketch.py --baseline-acres 1000 --baseline-mbf-ac 30 \\
      --thin-acres 4000 --thin-mbf-ac 8 --json
"""
from __future__ import annotations

import argparse
import json
import sys


def parity(mbf_w: float, mbf_b: float) -> tuple[float | None, str]:
    if mbf_b <= 0:
        return None, "UNKNOWN"
    r = mbf_w / mbf_b
    if r >= 1.0:
        return r, "PASS"
    return r, "FAIL"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Illustrative 10-year landscape MBF sketch")
    p.add_argument("--window-years", type=float, default=10.0)
    # Baseline: acres of regeneration harvest over the window × MBF/ac
    p.add_argument("--baseline-acres", type=float, default=1000.0,
                   help="Acres of clearcut/regen harvest in the window (illustrative default)")
    p.add_argument("--baseline-mbf-ac", type=float, default=30.0)
    # Working forest: thin acres × MBF/ac (+ optional gap harvest)
    p.add_argument("--thin-acres", type=float, default=4000.0,
                   help="Acres commercially thinned in the window")
    p.add_argument("--thin-mbf-ac", type=float, default=8.0)
    p.add_argument("--gap-acres", type=float, default=0.0)
    p.add_argument("--gap-mbf-ac", type=float, default=25.0)
    p.add_argument("--biomass-mbf-equivalent", type=float, default=0.0,
                   help="Optional MBF-equivalent credited from biomass contracts")
    p.add_argument("--json", action="store_true")
    p.add_argument("--label", default="illustrative-defaults-not-plumas-validated")
    args = p.parse_args(argv)

    mbf_b = args.baseline_acres * args.baseline_mbf_ac
    mbf_w = (
        args.thin_acres * args.thin_mbf_ac
        + args.gap_acres * args.gap_mbf_ac
        + args.biomass_mbf_equivalent
    )
    ratio, verdict = parity(mbf_w, mbf_b)

    result = {
        "label": args.label,
        "window_years": args.window_years,
        "disclaimer": (
            "ILLUSTRATIVE. Not a Plumas harvest forecast. "
            "Replace inputs with CalTREES/FACTS/mill data before public volume claims. "
            "T1 only — does not test owner NPV, mill offtake, or logger rates."
        ),
        "baseline": {
            "acres": args.baseline_acres,
            "mbf_per_ac": args.baseline_mbf_ac,
            "mbf_total": mbf_b,
        },
        "working_forest": {
            "thin_acres": args.thin_acres,
            "thin_mbf_per_ac": args.thin_mbf_ac,
            "gap_acres": args.gap_acres,
            "gap_mbf_per_ac": args.gap_mbf_ac,
            "biomass_mbf_equivalent": args.biomass_mbf_equivalent,
            "mbf_total": mbf_w,
        },
        "parity_ratio": ratio,
        "t1_volume_verdict": verdict,
    }

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print("Plumas Working Forests — volume sketch (T1 only)")
    print("=" * 56)
    print(f"Label:   {args.label}")
    print(f"Window:  {args.window_years:g} years")
    print()
    print("BASELINE (clearcut / regen pathway)")
    print(f"  {args.baseline_acres:g} ac × {args.baseline_mbf_ac:g} MBF/ac = {mbf_b:,.0f} MBF")
    print()
    print("WORKING FOREST (thin + optional gaps)")
    print(f"  thin: {args.thin_acres:g} ac × {args.thin_mbf_ac:g} MBF/ac = {args.thin_acres * args.thin_mbf_ac:,.0f} MBF")
    if args.gap_acres:
        print(f"  gaps: {args.gap_acres:g} ac × {args.gap_mbf_ac:g} MBF/ac = {args.gap_acres * args.gap_mbf_ac:,.0f} MBF")
    if args.biomass_mbf_equivalent:
        print(f"  biomass eq: {args.biomass_mbf_equivalent:,.0f} MBF")
    print(f"  TOTAL: {mbf_w:,.0f} MBF")
    print()
    if ratio is None:
        print("T1 verdict: UNKNOWN (baseline MBF is zero)")
    else:
        print(f"Parity ratio (W/B): {ratio:.3f}")
        print(f"T1 volume verdict:  {verdict}")
        if verdict == "FAIL":
            print("  → Under these inputs, working forest does NOT match baseline MBF.")
            print("  → Options: more thin acres, higher MBF/ac, biomass credit, or accept lower harvest.")
        elif verdict == "PASS":
            print("  → Under these inputs, volume parity holds. Still must pass mill, logger, owner NPV tests.")
    print()
    print(result["disclaimer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
