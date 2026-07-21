import openpyxl, csv, os

def sheet_for(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    for ws in wb.worksheets:
        if ws.title.strip().lower().startswith("search criteria"):
            continue
        return wb, ws
    return wb, wb.worksheets[0]

def extract(path, out, county):
    wb, ws = sheet_for(path)
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h else "" for h in next(rows)]
    lower = [h.lower() for h in header]
    i_id = lower.index("permit number")
    i_nm = lower.index("operator")
    i_ty = lower.index("permit type") if "permit type" in lower else None
    seen = {}
    for r in rows:
        if r is None or len(r) <= max(i_id, i_nm): continue
        oid = str(r[i_id]).strip() if r[i_id] is not None else ""
        nm  = str(r[i_nm]).strip() if r[i_nm] is not None else ""
        if not oid or not nm or oid.lower() == "none": continue
        ty = str(r[i_ty]).strip() if i_ty is not None and r[i_ty] is not None else ""
        seen.setdefault(oid, (nm, ty))
    wb.close()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["operator_id", "name", "entity_type", "county"])
        for oid, (nm, ty) in sorted(seen.items()):
            w.writerow([oid, nm, ty, county])
    print(f"{out}: {len(seen)} unique operator IDs  (from {os.path.basename(path)})")

extract("sanjoaquin/2025 Permits Commodities.xlsx", "sanjoaquin-2025.csv", "San Joaquin")
extract("sanjoaquin/2026 Permits Commodities.xlsx", "sanjoaquin-2026.csv", "San Joaquin")
extract("Madera County Permits Sites Commodities 2020 to 2026.xlsx", "madera-2020-2026.csv", "Madera")
extract("Spraymap California Data Request.xlsx", "tulare-2020-2026.csv", "Tulare")
