#!/usr/bin/env python3
"""emerald+ : report wild encounters and trainer battles for given maps.

    python3 tools/emerald_plus/encounter_report.py Route102:MAP_ROUTE102 ...
    python3 tools/emerald_plus/encounter_report.py --raw MAP_ROUTE102 ...

Two modes:
  default  aggregated view - species, level band, and combined % per table,
           plus every trainer battle scripted on that map with its party
  --raw    the twelve land slots individually, which is what you need when
           deciding WHICH slot to overwrite

Slot rates are fixed by position and defined in src/data/wild_encounters.h
(generated). They are duplicated here deliberately so the report does not
depend on parsing generated output:

  land        20 20 10 10 10 10  5  5  4  4  1  1
  water       60 30  5  4  1
  rock smash  60 30  5  4  1
  fishing     Old 70 30 | Good 60 20 20 | Super 40 40 15 4 1

NOTE the Good Rod's rarest slot is 20%. There is no way to express a sub-15%
Good Rod encounter without changing those global constants, which would move
every fishing table in the game.
"""
import json, re, os, sys, collections

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
os.chdir(ROOT)

LAND  = [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]
WATER = [60, 30, 5, 4, 1]
ROCK  = [60, 30, 5, 4, 1]
FISH  = [70, 30, 60, 20, 20, 40, 40, 15, 4, 1]
ROD   = ["Old", "Old", "Good", "Good", "Good", "Super", "Super", "Super", "Super", "Super"]

HDR = re.compile(r'^(Name|Class|Pic|Gender|Music|Items|AI|Battle Type|Mugshot'
                 r'|Starting Status|Multi Party|Double Battle):')


def rates(kind):
    return {"land_mons": LAND, "water_mons": WATER,
            "rock_smash_mons": ROCK, "fishing_mons": FISH}[kind]


def load_encounters():
    d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
    by_map = {}
    for g in d["wild_encounter_groups"]:
        for e in g.get("encounters", []):
            if e.get("map"):
                by_map.setdefault(e["map"], []).append(e)
    return by_map


def load_parties(path="src/data/trainers.party"):
    txt = open(path, encoding="utf-8").read()
    out = {}
    for b in re.split(r'(?m)^=== ', txt)[1:]:
        name = b.split("===")[0].strip()
        body = b.split("===", 1)[1]
        mons = []
        for chunk in body.split("\n\n"):
            c = chunk.strip()
            if not c or HDR.match(c.split("\n")[0].strip()):
                continue
            lv = re.search(r'^Level:\s*(\d+)', c, re.M)
            sp = re.sub(r'\s*\(.*?\)\s*', '', c.split("\n")[0].split("@")[0]).strip()
            mons.append((sp, int(lv.group(1)) if lv else None))
        out[name] = mons
    return out


def trainers_on(mapdir):
    p = f"data/maps/{mapdir}/scripts.inc"
    if not os.path.exists(p):
        return []
    txt = open(p, encoding="utf-8").read()
    ids = []
    for m in re.finditer(r'trainerbattle\w*\s+(TRAINER_[A-Z0-9_]+)', txt):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def show_raw(by_map, mapconst):
    for e in by_map.get(mapconst, []):
        if "land_mons" not in e:
            continue
        print(f"\n{mapconst}  (rate {e['land_mons']['encounter_rate']})")
        for i, m in enumerate(e["land_mons"]["mons"]):
            sp = m["species"].replace("SPECIES_", "")
            print(f"  slot{i:<3}{LAND[i]:>3}%  {sp:<14} L{m['min_level']}-{m['max_level']}")


def show_aggregated(by_map, mapconst):
    entries = by_map.get(mapconst)
    if not entries:
        print("    (no wild encounters)")
        return
    for e in entries:
        for kind in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
            blk = e.get(kind)
            if not blk:
                continue
            r = rates(kind)
            agg = collections.OrderedDict()
            for i, m in enumerate(blk["mons"]):
                pct = r[i] if i < len(r) else 0
                sp = m["species"].replace("SPECIES_", "").title()
                key = ((ROD[i],) if kind == "fishing_mons" else ()) + \
                      (sp, m["min_level"], m["max_level"])
                agg[key] = agg.get(key, 0) + pct
            print(f"    {kind.replace('_mons','').replace('_',' ')}  "
                  f"(rate {blk['encounter_rate']})")
            for key, pct in sorted(agg.items(), key=lambda kv: -kv[1]):
                *pre, sp, lo, hi = key
                lv = f"L{lo}" if lo == hi else f"L{lo}-{hi}"
                tag = f"{pre[0]:<6}" if pre else ""
                print(f"        {tag}{sp:<18}{lv:<9}{pct:>5.0f}%")
            print(f"        {'':<24}{'total':<9}{sum(agg.values()):>5.0f}%")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    by_map = load_encounters()
    if args[0] == "--raw":
        for mc in args[1:]:
            show_raw(by_map, mc)
        return 0

    parties = load_parties()
    for spec in args:
        mapdir, mapconst = spec.split(":")
        print("\n" + "=" * 68)
        print(mapdir)
        print("=" * 68)
        print("  WILD:")
        show_aggregated(by_map, mapconst)
        print("  TRAINERS:")
        ids = trainers_on(mapdir)
        if not ids:
            print("    (none)")
        for t in ids:
            mons = parties.get(t)
            if mons is None:
                print(f"    {t}  (not in trainers.party)")
                continue
            print(f"    {t}")
            print("        " + ", ".join(f"{s} L{l}" for s, l in mons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
