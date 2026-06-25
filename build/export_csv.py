#!/usr/bin/env python3
"""Stream the SQLite applications table to stdout as CSV (header + NULLs as empty),
for piping into `psql \\copy ... FROM STDIN CSV`."""
import sqlite3, csv, sys, os
DB = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ryanv\plumas_db_backup\applications.sqlite"
COLS = ["app_id","source","region","date","year","lat","lon","county","land_type","owner",
        "product","active_ingredient","amount","unit","method","activity","project","status","url","pulled"]
try:
    sys.stdout.reconfigure(encoding="utf-8", newline="")   # no CRLF translation; psql wants \n
except Exception:
    pass
cx = sqlite3.connect("file:///" + DB.replace("\\","/") + "?mode=ro", uri=True)
w = csv.writer(sys.stdout, lineterminator="\n")
w.writerow(COLS)
n = 0
for row in cx.execute("SELECT " + ",".join(COLS) + " FROM applications"):
    w.writerow(["" if v is None else v for v in row])
    n += 1
sys.stderr.write(f"streamed {n} rows\n")
