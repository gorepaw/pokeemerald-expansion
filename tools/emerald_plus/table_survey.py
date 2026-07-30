#!/usr/bin/env python3
"""One compact line per Hoenn table, with a spam flag."""
import json, os, collections, sys

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RATES = {"land_mons": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1],
         "water_mons": [60, 30, 5, 4, 1], "rock_smash_mons": [60, 30, 5, 4, 1],
         "fishing_mons": [70, 30, 60, 20, 20, 40, 40, 15, 4, 1]}

d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
kind = sys.argv[1] if len(sys.argv) > 1 else "land_mons"

rows = []
for g in d["wild_encounter_groups"]:
    for e in g.get("encounters", []):
        lab = e.get("base_label", "")
        if lab.endswith("_FireRed") or lab.endswith("_LeafGreen"):
            continue
        blk = e.get(kind)
        if not blk:
            continue
        agg = collections.Counter()
        lo = min(m["min_level"] for m in blk["mons"])
        hi = max(m["max_level"] for m in blk["mons"])
        for i, m in enumerate(blk["mons"]):
            agg[m["species"].replace("SPECIES_", "").title()] += RATES[kind][i]
        top = agg.most_common()
        spam = "SPAM" if (len(agg) <= 2 or top[0][1] >= 60) else "    "
        rows.append((e.get("map") or lab, lo, hi, spam, top, blk["encounter_rate"]))

rows.sort(key=lambda r: r[0])
print(f"### {kind}: {len(rows)} Hoenn tables\n")
for mp, lo, hi, spam, top, rate in rows:
    body = " ".join(f"{s}{p}" for s, p in top)
    print(f"{spam} {mp[4:]:<34} L{lo}-{hi:<3} r{rate:<3} {body}")
