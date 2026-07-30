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

st = open("include/constants/species.h", encoding="utf-8").read()
bynum = {}
for m in re.finditer(r'SPECIES_(\w+)\s*=\s*(\d+),', st):
    n = int(m.group(2))
    if 1 <= n <= 386 and n not in bynum:
        bynum[n] = m.group(1)
GEN13 = [bynum[i] for i in sorted(bynum)]
NUM = {v: k for k, v in bynum.items()}

d = json.load(open("src/data/wild_encounters.json", encoding="utf-8"))
hoenn, kanto = set(), set()
for g in d["wild_encounter_groups"]:
    for e in g.get("encounters", []):
        lab = e.get("base_label", "")
        frlg = lab.endswith("_FireRed") or lab.endswith("_LeafGreen")
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
    "CASTFORM_NORMAL",                         # Weather Institute gift
    "LILEEP", "ANORITH",                       # fossils
    "WYNAUT",                                  # Lavaridge egg
    "FEEBAS",                                  # gWildFeebas, Route 119 tiles
    "KECLEON",                                 # static overworld battles
    "KYOGRE", "GROUDON", "RAYQUAZA",           # story statics
    "LATIAS", "LATIOS",                        # roamer
    "REGIROCK", "REGICE", "REGISTEEL",         # Braille puzzles
    "BELDUM",                                  # Steven's gift (+ now wild)
}
EVENT = {"DEOXYS_NORMAL", "JIRACHI"}           # Mystery Gift only - NOT obtainable
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
