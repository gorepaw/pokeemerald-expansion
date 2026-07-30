#!/usr/bin/env python3
"""emerald+ : audit trainer parties against the project's balance rules.

    python3 tools/emerald_plus/party_audit.py Route102:MAP_ROUTE102 ...
    python3 tools/emerald_plus/party_audit.py --done      # every route signed off so far

RULES (see BALANCE.md in the docs repo)
  - every trainer            >= 2 Pokemon
  - trainers inside a gym    >= 3
  - Roxanne 4, Brawly 5, all remaining leaders and Elite Four members 6
  - no trainer Pokemon below the minimum wild level of the map it is on

Reports the shortfall per trainer; it does not edit anything. Fillers are a
design choice - draw them from the route's own wild table where there is one,
and from the trainer class's theme where there is not.
"""
import json, re, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
os.chdir(ROOT)

HDR = re.compile(r'^(Name|Class|Pic|Gender|Music|Items|AI|Battle Type|Mugshot'
                 r'|Starting Status|Multi Party|Double Battle):')

LEADER_TARGET = {
    "TRAINER_ROXANNE_1": 4,
    "TRAINER_BRAWLY_1": 5,
    "TRAINER_WATTSON_1": 6, "TRAINER_FLANNERY_1": 6, "TRAINER_NORMAN_1": 6,
    "TRAINER_WINONA_1": 6, "TRAINER_TATE_AND_LIZA_1": 6, "TRAINER_JUAN_1": 6,
    "TRAINER_SIDNEY": 6, "TRAINER_PHOEBE": 6, "TRAINER_GLACIA": 6,
    "TRAINER_DRAKE": 6, "TRAINER_WALLACE": 6,
}

# routes signed off so far, in story order
DONE = [
    ("Route101", "MAP_ROUTE101"), ("Route102", "MAP_ROUTE102"),
    ("Route103", "MAP_ROUTE103"), ("Route104", "MAP_ROUTE104"),
    ("PetalburgWoods", "MAP_PETALBURG_WOODS"),
    ("RustboroCity", "MAP_RUSTBORO_CITY"),
    ("RustboroCity_Gym", "MAP_RUSTBORO_CITY_GYM"),
    ("Route116", "MAP_ROUTE116"),
    ("RusturfTunnel", "MAP_RUSTURF_TUNNEL"),
    ("Route106", "MAP_ROUTE106"),
    ("DewfordTown_Gym", "MAP_DEWFORD_TOWN_GYM"),
]


def min_wild_level():
    d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
    out = {}
    for g in d["wild_encounter_groups"]:
        for e in g.get("encounters", []):
            if "land_mons" in e and e.get("map"):
                out[e["map"]] = min(m["min_level"] for m in e["land_mons"]["mons"])
    return out


def load_parties():
    txt = open("src/data/trainers.party", encoding="utf-8").read()
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


def main():
    args = sys.argv[1:]
    maps = DONE if (not args or args[0] == "--done") else \
        [tuple(a.split(":")) for a in args]

    floors = min_wild_level()
    parties = load_parties()

    print(f"{'trainer':<36}{'map':<20}{'has':>4}{'need':>6}   levels")
    print("-" * 92)
    short = under = 0
    for mapdir, mapconst in maps:
        floor = floors.get(mapconst)
        is_gym = "Gym" in mapdir
        # dict.fromkeys, not set(): a trainer referenced twice in one script
        # (a second trainerbattle for the post-battle line, say) is still one
        # trainer, but the order the script lists them in is worth keeping.
        for t in dict.fromkeys(
                re.findall(r'trainerbattle\w*\s+(TRAINER_[A-Z0-9_]+)',
                           open(f"data/maps/{mapdir}/scripts.inc", encoding="utf-8").read())
                if os.path.exists(f"data/maps/{mapdir}/scripts.inc") else []):
            mons = parties.get(t)
            if mons is None:
                continue
            need = LEADER_TARGET.get(t, 3 if is_gym else 2)
            gap = max(0, need - len(mons))
            short += gap
            lo = [f"{l}" for _, l in mons]
            warn = ""
            if floor and any(l is not None and l < floor for _, l in mons):
                warn = f"   << below wild floor L{floor}"
                under += 1
            flag = f"+{gap}" if gap else "ok"
            print(f"{t:<36}{mapdir:<20}{len(mons):>4}{flag:>6}   {','.join(lo)}{warn}")
    print("-" * 92)
    print(f"party slots short: {short}    trainers under the level floor: {under}")
    return 1 if (short or under) else 0


if __name__ == "__main__":
    sys.exit(main())
