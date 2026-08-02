#!/usr/bin/env python3
"""Validate and print the Working Forests cost ledger (data/working_forests_costs.json)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "data" / "working_forests_costs.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(d: dict) -> str:
    lines: list[str] = []
    lines.append(f"# {d.get('title', 'Cost ledger')}")
    lines.append(f"Updated: {d.get('updated')} · schema {d.get('schema_version')}")
    lines.append("")
    lines.append(d.get("disclaimer", ""))
    lines.append("")

    ph = d.get("plumas_harvest_mbf") or {}
    if ph:
        lines.append("## Plumas harvest (MBF)")
        lines.append(f"Source: {ph.get('source')} [{ph.get('confidence')}]")
        der = ph.get("derived") or {}
        lines.append(
            f"- Latest {der.get('latest_year')}: **{der.get('latest_total_mbf'):,}** MBF "
            f"(private share {100 * float(der.get('latest_private_share') or 0):.0f}%)"
        )
        lines.append(f"- Avg total 2018–2020 (pre-spike): {der.get('avg_total_2018_2020'):,} MBF")
        lines.append(f"- Avg total 2021–2023 (fire years): {der.get('avg_total_2021_2023'):,} MBF")
        lines.append("")

    lines.append("## Cost line items")
    lines.append("| ID | Label | Range | Unit | Conf |")
    lines.append("|---|---|---|---|---|")
    for item in d.get("cost_line_items") or []:
        lo, mid, hi = item.get("low"), item.get("mid"), item.get("high")
        if lo is None and hi is None and mid is None:
            rng = "—"
        elif lo is not None and hi is not None:
            rng = f"{lo}–{hi}" + (f" (mid {mid})" if mid is not None else "")
        else:
            rng = str(mid if mid is not None else lo if lo is not None else hi)
        lines.append(
            f"| `{item.get('id')}` | {item.get('label')} | {rng} | {item.get('unit')} | {item.get('confidence')} |"
        )
    lines.append("")

    filled = sum(
        1
        for i in (d.get("cost_line_items") or [])
        if i.get("confidence") in ("A", "B") and (i.get("low") is not None or i.get("mid") is not None)
    )
    gaps = sum(1 for i in (d.get("cost_line_items") or []) if i.get("confidence") == "D")
    lines.append(f"**Filled (A/B with numbers): {filled} · Gaps (D): {gaps}**")
    lines.append("")
    lines.append("## Next fills")
    for n in d.get("next_fills_priority") or []:
        lines.append(f"- {n}")
    lines.append("")
    return "\n".join(lines)


def check(d: dict) -> list[str]:
    errs: list[str] = []
    if d.get("schema_version") != 1:
        errs.append("schema_version must be 1")
    if not d.get("plumas_harvest_mbf", {}).get("series"):
        errs.append("missing plumas harvest series")
    for item in d.get("cost_line_items") or []:
        conf = item.get("confidence")
        if conf not in ("A", "B", "C", "D"):
            errs.append(f"{item.get('id')}: bad confidence {conf}")
        if conf == "D":
            continue
        if item.get("low") is None and item.get("mid") is None and item.get("high") is None:
            errs.append(f"{item.get('id')}: {conf} but no numeric values")
        if conf in ("A", "B") and not item.get("source"):
            errs.append(f"{item.get('id')}: {conf} missing source")
    return errs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--path", type=Path, default=DEFAULT)
    p.add_argument("--json-check", action="store_true", help="exit 1 on validation errors only")
    p.add_argument("--write-md", type=Path, default=None, help="write markdown summary path")
    args = p.parse_args(argv)

    if not args.path.is_file():
        print(f"missing {args.path}", file=sys.stderr)
        return 1
    d = load(args.path)
    errs = check(d)
    if args.json_check:
        if errs:
            for e in errs:
                print("ERROR:", e, file=sys.stderr)
            return 1
        print("OK", args.path)
        return 0

    text = summarize(d)
    print(text)
    if errs:
        print("## Validation issues")
        for e in errs:
            print(f"- {e}")
    if args.write_md:
        args.write_md.parent.mkdir(parents=True, exist_ok=True)
        args.write_md.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {args.write_md}")
    return 0 if not errs else 2


if __name__ == "__main__":
    raise SystemExit(main())
