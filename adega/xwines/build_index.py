# Builds the compact X-Wines index published with the app:
#   xw/wineries.json            [[WineryID, WineryName], ...]
#   xw/w/NNN.json  (NNN = WineryID % SHARDS)   {WineryID: [[WineID, WineName, Type, Grapes, Country, Region, ABV, Body, Acidity, Harmonize, avg, n, "vintage:avg:n,..."], ...]}
import csv, json, sys, os, ast, collections
DATA, OUT, SHARDS, MINV = sys.argv[1], sys.argv[2], 128, 5
tot = collections.defaultdict(lambda: [0.0, 0]); vin = collections.defaultdict(lambda: [0.0, 0])
with open(os.path.join(DATA, "XWines_Full_21M_ratings.csv"), encoding="utf-8") as f:
    next(f)
    for line in f:
        p = line.split(",")
        r = float(p[4]); a = tot[p[2]]; a[0] += r; a[1] += 1
        b = vin[(p[2], p[3])]; b[0] += r; b[1] += 1
byv = collections.defaultdict(list)
for (wid, v), (s, n) in vin.items():
    if n >= MINV and v.isdigit(): byv[wid].append((v, round(s / n, 2), n))
def lst(t):
    try: return "|".join(str(x) for x in ast.literal_eval(t))
    except Exception: return ""
shards = [collections.defaultdict(list) for _ in range(SHARDS)]; wineries = {}
with open(os.path.join(DATA, "XWines_Full_100K_wines.csv"), encoding="utf-8") as f:
    for w in csv.DictReader(f):
        wid, wy = w["WineID"], int(w["WineryID"])
        wineries[wy] = w["WineryName"]
        s, n = tot.get(wid, (0.0, 0))
        vs = ",".join(f"{v}:{a}:{c}" for v, a, c in sorted(byv.get(wid, []), reverse=True))
        try: abv = float(w["ABV"])
        except Exception: abv = None
        shards[wy % SHARDS][str(wy)].append([int(wid), w["WineName"], w["Type"], lst(w["Grapes"]), w["Country"], w["RegionName"], abv, w["Body"], w["Acidity"], lst(w["Harmonize"]), round(s / n, 2) if n else None, n, vs])
os.makedirs(os.path.join(OUT, "w"), exist_ok=True)
json.dump(sorted(wineries.items()), open(os.path.join(OUT, "wineries.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
sizes = []
for i, sh in enumerate(shards):
    p = os.path.join(OUT, "w", f"{i:03d}.json")
    json.dump(sh, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":")); sizes.append(os.path.getsize(p))
print("wineries", len(wineries), os.path.getsize(os.path.join(OUT, "wineries.json")) // 1024, "KB | shards", len(sizes), "avg", sum(sizes) // len(sizes) // 1024, "KB max", max(sizes) // 1024, "KB total", sum(sizes) // 1024 // 1024, "MB")
