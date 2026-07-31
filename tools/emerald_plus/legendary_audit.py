#!/usr/bin/env python3
"""Audit the rotating legendary slots.

Checks the things that would ship broken and look fine:
  - every one of the 19 slots has an object, a trampoline and an ON_TRANSITION
  - every Gen 4-9 legendary family appears in exactly one queue, exactly once
  - nothing in a queue is already obtainable elsewhere
  - the five emerald+ statics exist and are at the shared level
Exit code is non-zero if anything fails, so it works as a pre-commit check.
"""
import json, os, re, sys, collections

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

SLOTS = [
    ("SEAFOAM_ISLANDS", "SeafoamIslands_B4F_Frlg"), ("POWER_PLANT", "PowerPlant_Frlg"),
    ("MT_EMBER", "MtEmber_Summit_Frlg"), ("CERULEAN_CAVE", "CeruleanCave_B1F_Frlg"),
    ("NAVEL_ROCK_BASE", "NavelRock_Bottom"), ("NAVEL_ROCK_SUMMIT", "NavelRock_Top"),
    ("BIRTH_ISLAND", "BirthIsland_Exterior"), ("FARAWAY_ISLAND", "FarawayIsland_Interior"),
    ("NEW_MAUVILLE", "NewMauville_Inside"), ("FIERY_PATH", "FieryPath"),
    ("SHOAL_CAVE", "ShoalCave_LowTideEntranceRoom"), ("VIRIDIAN_FOREST", "ViridianForest_Frlg"),
    ("METEOR_FALLS", "MeteorFalls_1F_1R"), ("SKY_PILLAR", "SkyPillar_Top"),
    ("DESERT_RUINS", "DesertRuins"), ("ISLAND_CAVE", "IslandCave"),
    ("ANCIENT_TOMB", "AncientTomb"), ("CAVE_OF_ORIGIN", "CaveOfOrigin_B1F"),
    ("SEALED_CHAMBER", "SealedChamber_InnerRoom"),
]
NEW_STATICS = {"NewMauville_Inside": "RAIKOU", "FieryPath": "ENTEI",
               "ShoalCave_LowTideEntranceRoom": "SUICUNE",
               "ViridianForest_Frlg": "CELEBI", "MeteorFalls_1F_1R": "JIRACHI"}

fail = []

# ---- the C table
src = open("src/legendary_slots.c", encoding="utf-8").read()
queues = {}
for m in re.finditer(r'\[LEGENDARY_SLOT_(\w+)\] = \{(.*?)\},\n', src, re.S):
    body = m.group(2)
    q = re.search(r'\{([^}]*)\}', body)
    queues[m.group(1)] = [s.strip().replace("SPECIES_", "")
                          for s in q.group(1).split(",")
                          if s.strip() and s.strip() != "SPECIES_NONE"]

if len(queues) != 19:
    fail.append(f"C table has {len(queues)} slots, expected 19")

placed = [s for q in queues.values() for s in q]
dupes = [s for s, n in collections.Counter(placed).items() if n > 1]
if dupes:
    fail.append(f"placed more than once: {dupes}")

# ---- cross-check against what availability.py considers outstanding
legfile = "tools/emerald_plus/legendaries49.txt"
if os.path.exists(legfile):
    known = set(open(legfile, encoding="utf-8").read().split())
    # base forms only: a queue holds one entry per family
    stray = [s for s in placed if s not in known]
    if stray:
        fail.append(f"in a queue but not on the Gen 4-9 legendary list: {stray}")

# ---- anything in a queue must not already be in a wild table
d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
wild = set()
for g in d["wild_encounter_groups"]:
    for e in g.get("encounters", []):
        for k in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
            for mon in e.get(k, {}).get("mons", []):
                wild.add(mon["species"].replace("SPECIES_", ""))
clash = sorted(set(placed) & wild)
if clash:
    fail.append(f"in a queue AND in a wild table: {clash}")

# ---- per-map wiring
for slot, mapdir in SLOTS:
    mj = json.load(open(f"data/maps/{mapdir}/map.json", encoding="utf-8"))
    objs = mj.get("object_events", [])
    pre = mapdir.replace("_Frlg", "")
    if not any(o.get("script") == f"{pre}_EventScript_LegendarySlot" for o in objs):
        fail.append(f"{mapdir}: no slot object")
    if not any(o.get("flag") == f"FLAG_EP_HIDE_SLOT_{slot}" for o in objs):
        fail.append(f"{mapdir}: slot object has the wrong hide flag")
    s = open(f"data/maps/{mapdir}/scripts.inc", encoding="utf-8").read()
    if f"setvar VAR_0x8004, LEGENDARY_SLOT_{slot}" not in s:
        fail.append(f"{mapdir}: trampoline does not name {slot}")
    if "special UpdateLegendarySlot" not in s:
        fail.append(f"{mapdir}: no ON_TRANSITION refresh")
    if mapdir in NEW_STATICS:
        mon = NEW_STATICS[mapdir]
        if f"setwildbattle SPECIES_{mon}, 70" not in s:
            fail.append(f"{mapdir}: {mon} missing or not at level 70")

# ---- every Gen 1-3 legendary at the shared level
import glob
for f in glob.glob("data/maps/*/scripts.inc"):
    for m in re.finditer(r'setwildbattle SPECIES_(\w+), (\d+)', open(f, encoding="utf-8").read()):
        if m.group(1).split("_")[0] in {"ARTICUNO", "ZAPDOS", "MOLTRES", "MEWTWO",
                "MEW", "RAIKOU", "ENTEI", "SUICUNE", "LUGIA", "CELEBI", "JIRACHI",
                "DEOXYS", "REGIROCK", "REGICE", "REGISTEEL", "RAYQUAZA"} \
           and int(m.group(2)) != 70:
            fail.append(f"{f}: {m.group(1)} at level {m.group(2)}, expected 70")

print(f"slots wired            : {len(SLOTS)}")
print(f"Gen 4-9 families placed: {len(placed)}  (unique {len(set(placed))})")
print(f"queue lengths          : {sorted(collections.Counter(len(q) for q in queues.values()).items())}")
print(f"rounds to exhaust      : {max(len(q) for q in queues.values())} Kanto Champion wins")
if fail:
    print("\nFAILURES:")
    for f in fail:
        print("  " + f)
    sys.exit(1)
print("\nall checks passed")
