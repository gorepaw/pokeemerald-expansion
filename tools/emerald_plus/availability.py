#!/usr/bin/env python3
"""Gen 1-3 availability in Hoenn, by evolutionary FAMILY.

A family is a connected component of the evolution graph. In Gen 3 you can walk
a family in both directions - evolve forward, breed backward - so one member
present in a Hoenn wild table makes the whole family obtainable. The number that
actually matters is therefore: how many Gen 1-3 families have ZERO presence in
Hoenn right now.
"""
import json, re, os, collections

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# The species enum is NOT national dex order past ~1008 - it interleaves
# regional forms (Samurott-Hisui is 1000), the cosmetic Pikachu caps
# (1009-1023) and the Unown letters, while real Gen 8-9 species sit far higher
# (Pecharunt is 1434). Reading a generation off the enum value therefore places
# Pikachu hats and misses Hydrapple. The national dex list is the only correct
# source. For 1-386 the two happen to agree, which is why this went unnoticed.
st = open("include/constants/species.h", encoding="utf-8").read()
known = set(re.findall(r'SPECIES_(\w+)\s*=', st))
pdx = open("include/constants/pokedex.h", encoding="utf-8").read()
dexnames = re.findall(r'NATIONAL_DEX_(\w+),', pdx)      # [0] is NONE
NUM = {nm: i for i, nm in enumerate(dexnames) if i and nm in known}
GEN13 = [nm for nm, i in sorted(NUM.items(), key=lambda kv: kv[1]) if i <= 386]
GEN49 = [nm for nm, i in sorted(NUM.items(), key=lambda kv: kv[1])
         if 387 <= i <= 1025]

d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
hoenn, kanto = set(), set()
for g in d["wild_encounter_groups"]:
    for e in g.get("encounters", []):
        lab = e.get("base_label", "")
        frlg = lab.endswith("_Kanto")
        for k in ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons"):
            for mon in e.get(k, {}).get("mons", []):
                (kanto if frlg else hoenn).add(mon["species"].replace("SPECIES_", ""))

evo = collections.defaultdict(set)
for fn in sorted(os.listdir("src/data/pokemon/species_info")):
    if not fn.startswith("gen_"):
        continue
    src = open(f"src/data/pokemon/species_info/{fn}", encoding="utf-8").read()
    cur, i = None, 0
    while True:
        mspec = re.compile(r'\[SPECIES_(\w+)\]\s*=').search(src, i)
        mevo = re.compile(r'\.evolutions\s*=\s*EVOLUTION\(').search(src, i)
        if mevo is None:
            break
        if mspec is not None and mspec.start() < mevo.start():
            cur, i = mspec.group(1), mspec.end()
            continue
        j, depth = mevo.end() - 1, 0
        while j < len(src):
            if src[j] == "(":
                depth += 1
            elif src[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if cur:
            # Each entry is {METHOD, param, SPECIES_TARGET[, CONDITIONS(...)]}.
            # Take field 3 only - a blanket SPECIES_ grep also catches condition
            # species like IF_SPECIES_IN_PARTY's Remoraid, which would falsely
            # weld two unrelated families together.
            body = src[mevo.end():j]
            depth, start = 0, None
            for k, ch in enumerate(body):
                if ch == "{":
                    if depth == 0:
                        start = k + 1
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        fields, d2, buf = [], 0, ""
                        for c in body[start:k]:
                            if c in "({[":
                                d2 += 1
                            elif c in ")}]":
                                d2 -= 1
                            if c == "," and d2 == 0:
                                fields.append(buf.strip())
                                buf = ""
                            else:
                                buf += c
                        fields.append(buf.strip())
                        if len(fields) >= 3:
                            mt = re.fullmatch(r'SPECIES_(\w+)', fields[2])
                            if mt:
                                evo[cur].add(mt.group(1))
        i = j + 1

# undirected family graph
adj = collections.defaultdict(set)
for a, tos in evo.items():
    for b in tos:
        adj[a].add(b)
        adj[b].add(a)

fam_of, families = {}, []
for s in GEN13:
    if s in fam_of:
        continue
    comp, stack = set(), [s]
    while stack:
        c = stack.pop()
        if c in comp:
            continue
        comp.add(c)
        stack.extend(adj.get(c, ()))
    fid = len(families)
    families.append(comp)
    for c in comp:
        fam_of[c] = fid

# obtainable outside the wild tables
SCRIPT = {
    "TREECKO", "TORCHIC", "MUDKIP",
    "BULBASAUR", "CHARMANDER", "SQUIRTLE",     # Mr. Stone      (emerald+)
    "CHIKORITA", "CYNDAQUIL", "TOTODILE",      # Steven, R118   (emerald+)
    # Both spellings: the national dex calls it CASTFORM, the species constant
    # is CASTFORM_NORMAL, and the two sets are keyed differently.
    "CASTFORM_NORMAL", "CASTFORM",             # Weather Institute gift
    "LILEEP", "ANORITH",                       # fossils
    "WYNAUT",                                  # Lavaridge egg
    "FEEBAS",                                  # gWildFeebas, Route 119 tiles
    "KECLEON",                                 # static overworld battles
    "KYOGRE", "GROUDON", "RAYQUAZA",           # story statics
    "LATIAS", "LATIOS",                        # roamer
    "REGIROCK", "REGICE", "REGISTEEL",         # Braille puzzles
    "BELDUM",                                  # Steven's gift (+ now wild)
}
EVENT = {"DEOXYS_NORMAL", "DEOXYS", "JIRACHI"}  # Mystery Gift only - NOT obtainable
LEGEND = {"ARTICUNO", "ZAPDOS", "MOLTRES", "MEWTWO", "MEW", "RAIKOU", "ENTEI",
          "SUICUNE", "LUGIA", "HO_OH", "CELEBI"} | EVENT

present = hoenn | SCRIPT
fams_present = {fam_of[s] for s in present if s in fam_of}

missing_fams = collections.OrderedDict()
for s in GEN13:
    fid = fam_of[s]
    if fid in fams_present:
        continue
    missing_fams.setdefault(fid, []).append(s)

missing_species = [s for fid in missing_fams for s in missing_fams[fid]]
leg_f = {f: v for f, v in missing_fams.items() if any(s in LEGEND for s in v)}
non_f = {f: v for f, v in missing_fams.items() if not any(s in LEGEND for s in v)}

print(f"Gen 1-3 species reachable in Hoenn now : "
      f"{386 - len(missing_species)}/386")
print(f"Gen 1-3 FAMILIES with zero Hoenn presence: {len(missing_fams)}"
      f"  ({len(leg_f)} legendary, {len(non_f)} not)")
print(f"species those families account for       : {len(missing_species)}")
print()
print(f"--- {len(non_f)} ordinary families to place (one slot each is enough) ---")
rows = sorted(non_f.values(), key=lambda v: NUM.get(v[0], 999))
for fam in rows:
    fam = sorted(fam, key=lambda s: NUM.get(s, 999))
    head = fam[0]
    rest = fam[1:]
    inkanto = "K" if any(s in kanto for s in fam) else " "
    print(f"  {inkanto} {head:<13}" + (" -> " + ", ".join(rest) if rest else ""))
print()
print(f"--- {len(leg_f)} legendary/event families ---")
for fam in sorted(leg_f.values(), key=lambda v: NUM.get(v[0], 999)):
    print("   ", ", ".join(sorted(fam, key=lambda s: NUM.get(s, 999))))
print("\n(K = already lives in a Kanto-side table)")


# --------------------------------------------------------------------------
# Gen 4-9, which lives in Kanto. Same family logic, but reachability counts
# BOTH regions - Kanto is postgame, so hosting a line there still makes it
# obtainable, and plenty of Gen 4-9 arrive free by evolving a Gen 1-3 line.
# --------------------------------------------------------------------------
LEGEND49 = set()
_leg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legendaries49.txt")
if os.path.exists(_leg):
    LEGEND49 = set(open(_leg, encoding="utf-8").read().split())

fam2, comps = {}, []
for s in GEN13 + GEN49:
    if s in fam2:
        continue
    comp, stack = set(), [s]
    while stack:
        c = stack.pop()
        if c in comp:
            continue
        comp.add(c)
        stack.extend(adj.get(c, ()))
    cid = len(comps)
    comps.append(comp)
    for c in comp:
        fam2[c] = cid

reach = set(hoenn | kanto | SCRIPT)
stack = list(reach)
while stack:
    for nxt in adj.get(stack.pop(), ()):
        if nxt not in reach:
            reach.add(nxt)
            stack.append(nxt)

miss49 = collections.OrderedDict()
for s in GEN49:
    if s not in reach:
        miss49.setdefault(fam2[s], []).append(s)
leg49 = {f: v for f, v in miss49.items() if any(s in LEGEND49 for s in v)}
ord49 = {f: v for f, v in miss49.items() if f not in leg49}
gone = sum(len(v) for v in miss49.values())

print()
print("=" * 74)
print(f"Gen 4-9 species reachable (either region): {len(GEN49) - gone}/{len(GEN49)}")
print(f"families with zero presence anywhere     : {len(miss49)}"
      f"  ({len(leg49)} legendary/paradox, {len(ord49)} not)")
if ord49:
    print(f"\n--- {len(ord49)} ordinary Gen 4-9 families still homeless ---")
    for fam in sorted(ord49.values(), key=lambda v: NUM.get(v[0], 9999)):
        print("   ", ", ".join(sorted(fam, key=lambda s: NUM.get(s, 9999))))
