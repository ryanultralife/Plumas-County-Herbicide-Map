#!/usr/bin/env python3
"""Keep dots off DEVELOPED (residential/urban) land using USDA Cropland Data Layer.

Place polygons conflate farmland with towns; CDL classifies each 30m pixel as
developed / crop / forest / water / etc., which is the true "is this a house or a
field" signal. For every map_agg cell: query CDL at its point; if the pixel is
developed (121-124) or water (111), ring-search the cell's own ~1-sq-mi section
(Albers meters) for the nearest non-developed, non-water pixel and move the dot
there; if none within the section, the dot is unmappable (bad geocode on built land).

Reads cells.csv (lat,lon,albers_x,albers_y). Writes result.csv
(old_lat,old_lon,new_ax,new_ay,status). CDL results cached to cdl_cache.json so
the run is resumable. Reprojection of chosen Albers points back to lat/lon is done
afterward in PostGIS. External dependency: NASS CropScape CDLService (per-point).
"""
import sys, os, csv, json, time, math, threading
import requests
from concurrent.futures import ThreadPoolExecutor

SC = os.path.dirname(os.path.abspath(__file__)) if False else \
    r"C:/Users/ryanv/AppData/Local/Temp/claude/C--Users-ryanv-Projects-Plumas-County-Herbicide-Map--claude-worktrees-suspicious-sammet-763560/789979aa-c938-4c27-99dc-88d26a6ef09c/scratchpad"
CELLS = os.path.join(SC, "cells.csv")
OUT = os.path.join(SC, "result.csv")
CACHE = os.path.join(SC, "cdl_cache.json")
YEAR = 2022
URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue"
DEV = {121, 122, 123, 124}
WATER = {111, 0}          # 0 = NoData/background -> unusable
RING_R = [90, 180, 270, 360, 450, 540, 630, 720, 810]   # meters (section half-width ~805m)
RING_A = [0, 45, 90, 135, 180, 225, 270, 315]

_cache = {}
_lock = threading.Lock()
_sess = requests.Session()


def load_cache():
    global _cache
    if os.path.exists(CACHE):
        try:
            _cache = json.load(open(CACHE))
        except Exception:
            _cache = {}


def save_cache():
    with _lock:
        tmp = CACHE + ".tmp"
        json.dump(_cache, open(tmp, "w"))
        os.replace(tmp, CACHE)


def cdl(ax, ay):
    """CDL class code at Albers (ax,ay), cached, with retries. -1 on failure."""
    key = f"{int(round(ax))},{int(round(ay))}"
    v = _cache.get(key)
    if v is not None:
        return v
    for attempt in range(4):
        try:
            r = _sess.get(URL, params={"year": YEAR, "x": ax, "y": ay}, timeout=60)
            t = r.text
            i = t.find('value:')
            val = int(t[i + 6:t.find(',', i)].strip()) if i >= 0 else -1
            with _lock:
                _cache[key] = val
            return val
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return -1


def relocate(ax, ay):
    """Nearest non-dev/non-water pixel within the section; (nax,nay) or None."""
    for r in RING_R:
        best = None
        for a in RING_A:
            nx = ax + r * math.cos(math.radians(a))
            ny = ay + r * math.sin(math.radians(a))
            c = cdl(nx, ny)
            if c not in DEV and c not in WATER and c != -1:
                best = (nx, ny, r)
                break
        if best:
            return best[0], best[1]
    return None


def main():
    load_cache()
    cells = []
    for line in open(CELLS):
        p = line.strip().split(",")
        if len(p) != 4:
            continue
        try:
            cells.append((float(p[0]), float(p[1]), float(p[2]), float(p[3])))
        except ValueError:
            continue
    print(f"cells: {len(cells):,}", flush=True)

    # Phase 1: classify every cell
    done = [0]
    def classify(c):
        v = cdl(c[2], c[3])
        with _lock:
            done[0] += 1
            if done[0] % 300 == 0:
                print(f"  classified {done[0]:,}/{len(cells):,}", flush=True); save_cache()
        return (c, v)
    with ThreadPoolExecutor(max_workers=4) as ex:
        classified = list(ex.map(classify, cells))
    save_cache()
    bad = [(c, v) for c, v in classified if v in DEV or v in WATER]
    print(f"on developed/water: {len(bad):,}", flush=True)

    # Phase 2: relocate the bad ones
    rows = []
    dn = [0]
    def fixone(item):
        c, v = item
        nn = relocate(c[2], c[3])
        with _lock:
            dn[0] += 1
            if dn[0] % 50 == 0:
                print(f"  relocated {dn[0]:,}/{len(bad):,}", flush=True); save_cache()
        if nn:
            return [c[0], c[1], round(nn[0], 1), round(nn[1], 1), "move"]
        return [c[0], c[1], "", "", "null"]
    with ThreadPoolExecutor(max_workers=4) as ex:
        rows = list(ex.map(fixone, bad))
    save_cache()

    with open(OUT, "w", newline="") as o:
        w = csv.writer(o, lineterminator="\n")
        for r in rows:
            w.writerow(r)
    moved = sum(1 for r in rows if r[4] == "move")
    print(f"DONE  bad={len(bad):,}  moved={moved:,}  unmappable={len(bad)-moved:,}  -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
