#!/usr/bin/env python3
"""Add people to the network list (public.network_signups) who signed up by email,
at an event, or any way other than the site form. Same merge rules as the site:
lists are merged, the first sign-up date is kept, and anyone who unsubscribed stays off.

Usage (DBURL from C:/Users/ryanv/.pg_dburl, never echoed or committed):
  DBURL=... python build/network_signup.py --email a@b.org --name "A. Person" [--list mailing --list action] [--source email] [--note "..."]
  DBURL=... python build/network_signup.py --csv signups.csv        # columns: email,name[,lists][,source][,note]; lists like "mailing;action"
  DBURL=... python build/network_signup.py --unsubscribe a@b.org
  DBURL=... python build/network_signup.py --export network.csv     # active sign-ups, for the mailing tool
"""
import argparse, csv, os, re, subprocess, sys

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LISTS = ("mailing", "action")


def lit(s):
    return "null" if s is None or s == "" else "'" + str(s).replace("'", "''") + "'"


def psql(dburl, sql, csv_out=None):
    args = ["psql", dburl, "-v", "ON_ERROR_STOP=1", "-qAt"]
    if csv_out:
        args = ["psql", dburl, "-v", "ON_ERROR_STOP=1", "-q", "--csv"]
    r = subprocess.run(args + ["-f", "-"], input=sql, capture_output=True, text=True)  # -f shows every result
    if r.returncode:
        sys.exit(r.stderr.strip())
    return r.stdout


def row_sql(email, name, lists, source, note):
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ValueError("bad email: %r" % email)
    bad = [l for l in lists if l not in LISTS]
    if bad:
        raise ValueError("unknown list(s) %s; use %s" % (bad, ", ".join(LISTS)))
    arr = "array[%s]::text[]" % ",".join(lit(l) for l in (lists or ["mailing"]))
    return "select %s, public.network_signup(%s,%s,%s,%s,%s);" % (lit(email), lit(email), lit((name or "").strip()), arr, lit(source), lit(note))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email"); ap.add_argument("--name")
    ap.add_argument("--list", action="append", default=[], choices=LISTS)
    ap.add_argument("--source", default="email"); ap.add_argument("--note")
    ap.add_argument("--csv"); ap.add_argument("--unsubscribe"); ap.add_argument("--export")
    a = ap.parse_args()
    dburl = os.environ.get("DBURL") or sys.exit("set DBURL")

    if a.export:
        out = psql(dburl, "select email, name, array_to_string(lists,';') lists, source, created_at::date signed_up "
                          "from public.network_signups where unsubscribed_at is null order by created_at", csv_out=True)
        with open(a.export, "w", encoding="utf-8", newline="") as f:
            f.write(out)
        print("exported", max(out.count("\n") - 1, 0), "active sign-ups to", a.export)
        return
    if a.unsubscribe:
        e = a.unsubscribe.strip().lower()
        n = psql(dburl, "with u as (update public.network_signups set unsubscribed_at=now(), updated_at=now() "
                        "where email=%s and unsubscribed_at is null returning 1) select count(*) from u;" % lit(e))
        print("unsubscribed" if n.strip() == "1" else "not found or already unsubscribed", e)
        return

    stmts = []
    if a.csv:
        with open(a.csv, encoding="utf-8-sig", newline="") as f:
            for i, r in enumerate(csv.DictReader(f), 2):
                lists = [l.strip() for l in re.split(r"[;,|]", r.get("lists") or "") if l.strip()]
                try:
                    stmts.append(row_sql(r.get("email"), r.get("name"), lists, r.get("source") or a.source, r.get("note")))
                except ValueError as ex:
                    sys.exit("line %d: %s" % (i, ex))
    elif a.email:
        try:
            stmts.append(row_sql(a.email, a.name, a.list, a.source, a.note))
        except ValueError as ex:
            sys.exit(str(ex))
    else:
        ap.error("give --email, --csv, --unsubscribe or --export")
    out = psql(dburl, "begin;\n" + "\n".join(stmts) + "\ncommit;")
    for line in out.split():
        e, _, status = line.partition("|")
        print("%-9s %s" % (status, e))


if __name__ == "__main__":
    main()
