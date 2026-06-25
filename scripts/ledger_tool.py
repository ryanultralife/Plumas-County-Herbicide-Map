#!/usr/bin/env python3
"""
ledger_tool.py - maintain the public Transparency ledger (data/ledger.json).

The Transparency tab in index.html reads data/ledger.json at runtime. Update that
file with this tool (or edit the JSON by hand), then run publish-data.ps1 to commit
and push - the live site updates automatically, exactly like the map data.

Every entry can carry a click-through source so the public can verify each figure:
  --src      a URL or repo-relative path (e.g. data/receipts/2026-07-15-invoice.pdf)
  --src-label the link text shown in the ledger (e.g. "Lab invoice")
Put backing documents in data/receipts/ and reference them with a relative path.

USAGE
  # show current totals (also run after any edit to sanity-check)
  python scripts/ledger_tool.py summary

  # add a donation
  python scripts/ledger_tool.py add-donation --date 2026-08-01 \
      --source "Online donor" --gross 100 --fees 3.20 \
      --type Unrestricted --platform Givebutter \
      --src data/receipts/2026-08-01-payout.pdf --src-label "Payout report"

  # add an expense  (bucket = Operations | Testing | Admin)
  python scripts/ledger_tool.py add-expense --date 2026-08-05 \
      --payee "NorCal Lab - glyphosate panel" --bucket Testing --amount 480 \
      --via Card --src data/receipts/2026-08-05-lab.pdf --src-label "Lab invoice"

  # add logged hours  (value = hours x rate is computed in the app)
  python scripts/ledger_tool.py add-hours --date 2026-08-03 \
      --person "R. Vukich" --task "Map updates" --role Operations \
      --hours 4 --rate 50 --approved-by "Board 7/28" \
      --src data/receipts/2026-08-05-timesheet.pdf --src-label "Timesheet"

  # bump the "last updated" date (defaults to today on any add)
  python scripts/ledger_tool.py touch
"""
import json, os, sys, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.normpath(os.path.join(HERE, "..", "data", "ledger.json"))
BUCKETS = ("Operations", "Testing", "Admin")
DON_TYPES = ("Unrestricted", "Restricted-Testing")


def load():
    if not os.path.exists(LEDGER):
        return {"org": "", "updated": "", "currency": "USD", "note": "",
                "donations": [], "expenses": [], "hours": []}
    with open(LEDGER, encoding="utf-8") as f:
        return json.load(f)


def save(d):
    d["updated"] = datetime.date.today().isoformat()
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    print("Updated", os.path.relpath(LEDGER))


def _src(a):
    out = {}
    if a.src:
        out["src"] = a.src
        out["srcLabel"] = a.src_label or "Source"
    return out


def summary(d):
    don, exp, hrs = d.get("donations", []), d.get("expenses", []), d.get("hours", [])
    gross = sum(float(x.get("gross", 0) or 0) for x in don)
    fees = sum(float(x.get("fees", 0) or 0) for x in don)
    net = gross - fees
    spent = sum(float(x.get("amount", 0) or 0) for x in exp)
    by = {b: 0.0 for b in BUCKETS}
    for x in exp:
        b = x.get("bucket")
        if b in by:
            by[b] += float(x.get("amount", 0) or 0)
    hours = sum(float(x.get("hours", 0) or 0) for x in hrs)
    labor = sum(float(x.get("hours", 0) or 0) * float(x.get("rate", 0) or 0) for x in hrs)
    missing = sum(1 for grp in (don, exp, hrs) for x in grp if not x.get("src"))

    def m(n): return "${:,.2f}".format(n)
    print("Transparency ledger summary")
    print("  Updated        :", d.get("updated", ""))
    print("  Gross donations:", m(gross), " Fees:", m(fees), " Net:", m(net))
    print("  Total spent    :", m(spent),
          "  (Operations {}, Testing {}, Admin {})".format(m(by['Operations']), m(by['Testing']), m(by['Admin'])))
    print("  Cash on hand   :", m(net - spent))
    print("  Hours logged   :", round(hours, 1), " Labor value:", m(labor),
          " Blended:", m(labor / hours) if hours else "$0.00", "/hr")
    print("  Entries        :", len(don), "donations,", len(exp), "expenses,", len(hrs), "hours")
    if missing:
        print("  NOTE:", missing, "entr(y/ies) have no source document (--src). Add one so the public can verify.")


def main():
    p = argparse.ArgumentParser(description="Maintain data/ledger.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("summary")
    sub.add_parser("touch")

    d1 = sub.add_parser("add-donation")
    d1.add_argument("--date", required=True)
    d1.add_argument("--source", required=True)
    d1.add_argument("--gross", type=float, required=True)
    d1.add_argument("--fees", type=float, default=0.0)
    d1.add_argument("--type", choices=DON_TYPES, default="Unrestricted")
    d1.add_argument("--platform", default="")
    d1.add_argument("--notes", default="")
    d1.add_argument("--src", default="")
    d1.add_argument("--src-label", default="")

    e1 = sub.add_parser("add-expense")
    e1.add_argument("--date", required=True)
    e1.add_argument("--payee", required=True)
    e1.add_argument("--bucket", choices=BUCKETS, required=True)
    e1.add_argument("--amount", type=float, required=True)
    e1.add_argument("--via", default="")
    e1.add_argument("--notes", default="")
    e1.add_argument("--src", default="")
    e1.add_argument("--src-label", default="")

    h1 = sub.add_parser("add-hours")
    h1.add_argument("--date", required=True)
    h1.add_argument("--person", required=True)
    h1.add_argument("--task", required=True)
    h1.add_argument("--role", default="")
    h1.add_argument("--hours", type=float, required=True)
    h1.add_argument("--rate", type=float, default=0.0)
    h1.add_argument("--approved-by", default="")
    h1.add_argument("--src", default="")
    h1.add_argument("--src-label", default="")

    a = p.parse_args()
    d = load()

    if a.cmd == "summary":
        summary(d)
        return
    if a.cmd == "touch":
        save(d)
        return
    if a.cmd == "add-donation":
        row = {"date": a.date, "source": a.source, "gross": a.gross, "fees": a.fees,
               "type": a.type, "platform": a.platform}
        if a.notes:
            row["notes"] = a.notes
        row.update(_src(a))
        d.setdefault("donations", []).append(row)
    elif a.cmd == "add-expense":
        row = {"date": a.date, "payee": a.payee, "bucket": a.bucket, "amount": a.amount, "via": a.via}
        if a.notes:
            row["notes"] = a.notes
        row.update(_src(a))
        d.setdefault("expenses", []).append(row)
    elif a.cmd == "add-hours":
        row = {"date": a.date, "person": a.person, "task": a.task, "role": a.role,
               "hours": a.hours, "rate": a.rate, "approvedBy": a.approved_by}
        row.update(_src(a))
        d.setdefault("hours", []).append(row)

    save(d)
    summary(d)


if __name__ == "__main__":
    main()
