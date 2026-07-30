#!/usr/bin/env python3
"""emerald+ : audit trainer parties against the project's balance rules.

    python3 tools/emerald_plus/party_audit.py            # every Hoenn trainer
    python3 tools/emerald_plus/party_audit.py --list     # ...and name each miss
    python3 tools/emerald_plus/party_audit.py Route102:MAP_ROUTE102 ...

RULES (see BALANCE.md in the docs repo)
  - every trainer            >= 2 Pokemon
  - trainers inside a gym    >= 3
  - Roxanne 4, Brawly 5, all remaining leaders and Elite Four members 6
  - no trainer Pokemon below the minimum wild level of the map it is on

Scope notes, each of which took a wrong answer to learn:

  Hoenn maps are the ones WITHOUT the _Frlg suffix - 525 of 944 map dirs.

  Rematch parties come from gRematchTable in src/battle_setup.c and nowhere
  else. Guessing them from the _1/_2 name suffix is wrong: TRAINER_GRUNT_..._2
  is a different grunt, not a rematch of _1.

  A trainer is counted once per map even when the script references it twice.

  The level floor is the map's own land table. Battles scripted from a route's
  file but actually fought indoors - the Winstrate family sits in a house on
  Route 111 - are exempt, because there is no grass in a living room.

Reports only; it never edits. Exits non-zero if anything is short.
"""
import json, re, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
os.chdir(ROOT)

HDR = re.compile(r'^(Name|Class|Pic|Gender|Music|Items|AI|Battle Type|Mugshot'
                 r'|Starting Status|Multi Party|Double Battle):')

LEADER_TARGET = {
    "TRAINER_ROXANNE_1": 4, "TRAINER_BRAWLY_1": 5,
    "TRAINER_WATTSON_1": 6, "TRAINER_FLANNERY_1": 6, "TRAINER_NORMAN_1": 6,
    "TRAINER_WINONA_1": 6, "TRAINER_TATE_AND_LIZA_1": 6, "TRAINER_JUAN_1": 6,
    "TRAINER_SIDNEY": 6, "TRAINER_PHOEBE": 6, "TRAINER_GLACIA": 6,
    "TRAINER_DRAKE": 6, "TRAINER_WALLACE": 6,
}

# Wally's Mauville battle is the Ralts he has just caught - the one documented
# exception to the 2-Pokemon minimum. His later battles carry full parties.
EXEMPT_SIZE = {"TRAINER_WALLY_MAUVILLE"}

# Fought indoors, scripted from the route's file.
EXEMPT_FLOOR = {"TRAINER_VICTOR", "TRAINER_VICTORIA", "TRAINER_VIVI",
                "TRAINER_VICKY"}


def load_parties():
    txt = open("src/data/trainers.party", encoding="utf-8").read()
    out = {}
    for b in re.split(r'(?m)^=== ', txt)[1:]:
        name = b.split("===")[0].strip()
        mons = []
        for chunk in b.split("===", 1)[1].split("\n\n"):
            c = chunk.strip()
            if not c or HDR.match(c.split("\n")[0].strip()):
                continue
            lv = re.search(r'^Level:\s*(\d+)', c, re.M)
            sp = re.sub(r'\s*\(.*?\)\s*', '', c.split("\n")[0].split("@")[0]).strip()
            mons.append((sp, int(lv.group(1)) if lv else None))
        out[name] = mons
    return out


def min_wild_level():
    d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
    out = {}
    for g in d["wild_encounter_groups"]:
        if g["label"] != "gWildMonHeaders":
            continue
        for e in g.get("encounters", []):
            lab = e.get("base_label", "")
            if lab.endswith("_FireRed") or lab.endswith("_LeafGreen"):
                continue
            if "land_mons" in e and e.get("map"):
                lo = min(m["min_level"] for m in e["land_mons"]["mons"])
                out[e["map"]] = min(out.get(e["map"], 99), lo)
    return out


def rematches():
    src = open("src/battle_setup.c", encoding="utf-8").read()
    body = src[src.index("gRematchTable[REMATCH_TABLE_ENTRIES]"):]
    out = {}
    for m in re.finditer(r'REMATCH\(([^)]*)\)', body):
        parts = [p.strip() for p in m.group(1).split(",")]
        ids = [p for p in parts if p.startswith("TRAINER_")]
        mp = next((p for p in parts if p.startswith("MAP_")), None)
        for t in ids[1:]:
            out[t] = mp
    return out


def hoenn_scope():
    """[(label, MAP_ const, is_gym, trainer)] for all of Hoenn."""
    rows, seen = [], set()
    for dirn in sorted(os.listdir("data/maps")):
        if dirn.endswith("_Frlg"):
            continue
        sp = f"data/maps/{dirn}/scripts.inc"
        if not os.path.exists(sp):
            continue
        ids = dict.fromkeys(re.findall(
            r'trainerbattle\w*\s+(TRAINER_[A-Z0-9_]+)',
            open(sp, encoding="utf-8").read()))
        if not ids:
            continue
        mc = ""
        jp = f"data/maps/{dirn}/map.json"
        if os.path.exists(jp):
            mc = json.load(open(jp, encoding="utf-8")).get("id", "")
        for t in ids:
            if t not in seen:
                seen.add(t)
                rows.append((dirn, mc, "Gym" in dirn, t))
    for t, mc in rematches().items():
        if t not in seen:
            seen.add(t)
            rows.append((f"rematch:{(mc or '')[4:]}", mc, False, t))
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--list" in sys.argv
    parties = load_parties()
    floors = min_wild_level()

    if args:
        scope = []
        for a in args:
            dirn, mc = a.split(":")
            p = f"data/maps/{dirn}/scripts.inc"
            ids = dict.fromkeys(re.findall(
                r'trainerbattle\w*\s+(TRAINER_[A-Z0-9_]+)',
                open(p, encoding="utf-8").read())) if os.path.exists(p) else {}
            scope += [(dirn, mc, "Gym" in dirn, t) for t in ids]
    else:
        scope = hoenn_scope()

    short = under = counted = 0
    for label, mc, is_gym, t in scope:
        mons = parties.get(t)
        if mons is None:
            continue
        counted += 1
        need = LEADER_TARGET.get(t, 3 if is_gym else 2)
        gap = 0 if t in EXEMPT_SIZE else max(0, need - len(mons))
        floor = None if t in EXEMPT_FLOOR else floors.get(mc)
        low = [l for _, l in mons if l is not None and floor and l < floor]
        short += gap
        under += 1 if low else 0
        if verbose and (gap or low):
            lv = ",".join(str(l) for _, l in mons)
            warn = f"  << floor L{floor}" if low else ""
            print(f"{t:<38}{label:<28}{len(mons)}/{need}  {lv}{warn}")

    print(f"trainers checked: {counted}")
    print(f"party slots short: {short}    trainers under the level floor: {under}")
    return 1 if (short or under) else 0


if __name__ == "__main__":
    sys.exit(main())
