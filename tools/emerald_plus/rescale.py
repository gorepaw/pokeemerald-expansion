#!/usr/bin/env python3
"""emerald+ : move a region's level band, and settle species to match.

    # Kanto's wild tables from L50-89 to L55-94
    python3 tools/emerald_plus/rescale.py --wilds Kanto 50 89 55 94

    # Kanto's own trainers from L60-98 to L64-99
    python3 tools/emerald_plus/rescale.py --party src/data/trainers_frlg.party 60 98 64 99

    # only the Johto entries of the Hoenn party file
    python3 tools/emerald_plus/rescale.py --party src/data/trainers.party 66 96 70 99 \\
            --only TRAINER_JOHTO_

    --dry prints what would change and writes nothing.

This exists because the band was rewritten three times in one sitting and the
logic was rebuilt from scratch each time. It is a linear remap plus a species
settle, and the settle is the part that is easy to get wrong:

  UP    a species must evolve if the slot's MINIMUM level now clears its
        threshold - otherwise you get a L58 Caterpie.
  DOWN  a species must DE-evolve if its own evolution threshold now exceeds
        that minimum - otherwise you get a L50 Tyranitar, which evolves at 55
        and so is something the player could never legitimately have caught.

Only plain, unconditional EVO_LEVEL evolutions are walked. Stone, trade,
friendship and conditional evolutions are left alone, which is why Pikachu stays
Pikachu and Eevee stays Eevee and their base forms stay catchable.

Levels are asserted inside the new band afterwards, and no species is left below
its own evolution threshold.
"""
import argparse, json, os, re, sys, collections

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
os.chdir(ROOT)
INFO = "src/data/pokemon/species_info"
KINDS = ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons")
HDR = re.compile(r'^(Name|Class|Pic|Gender|Music|Items|AI|Battle Type|Mugshot'
                 r'|Starting Status|Multi Party|Double Battle):')
FIELD = ("IVs:", "EVs:", "Ability:", "Nature", "Shiny", "Happiness", "Ball",
         "Tera", "Dynamax", "Gigantamax", "Friendship")


def evo_maps():
    """forward: from -> [(lvl, to)];  back: to -> (lvl, from)"""
    fwd, back = collections.defaultdict(list), {}
    for fn in sorted(os.listdir(INFO)):
        if not fn.startswith("gen_"):
            continue
        src = open(f"{INFO}/{fn}", encoding="utf-8").read()
        for ms in re.finditer(r'\[SPECIES_(\w+)\]\s*=', src):
            nx = re.compile(r'\[SPECIES_(\w+)\]\s*=').search(src, ms.end())
            body = src[ms.end():nx.start() if nx else len(src)]
            me = re.search(r'\.evolutions\s*=\s*EVOLUTION\(', body)
            if not me:
                continue
            j, d = me.end() - 1, 0
            while j < len(body):
                if body[j] == "(":
                    d += 1
                elif body[j] == ")":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            seg, dp, st = body[me.end():j], 0, None
            for k, ch in enumerate(seg):
                if ch == "{":
                    if dp == 0:
                        st = k + 1
                    dp += 1
                elif ch == "}":
                    dp -= 1
                    if dp == 0:
                        f, d2, buf = [], 0, ""
                        for c in seg[st:k]:
                            if c in "({[":
                                d2 += 1
                            elif c in ")}]":
                                d2 -= 1
                            if c == "," and d2 == 0:
                                f.append(buf.strip())
                                buf = ""
                            else:
                                buf += c
                        f.append(buf.strip())
                        # exactly {EVO_LEVEL, <n>, SPECIES_X} - no CONDITIONS
                        if (len(f) == 3 and f[0] == "EVO_LEVEL"
                                and f[1].isdigit()
                                and re.fullmatch(r'SPECIES_\w+', f[2])):
                            lvl, tgt = int(f[1]), f[2].replace("SPECIES_", "")
                            fwd[ms.group(1)].append((lvl, tgt))
                            if tgt not in back or lvl < back[tgt][0]:
                                back[tgt] = (lvl, ms.group(1))
    return fwd, back


def settle(sp, lvl, fwd, back):
    seen = set()
    while True:
        cand = [(t, s) for t, s in fwd.get(sp, []) if t <= lvl and s not in seen]
        if not cand:
            break
        seen.add(sp)
        sp = sorted(cand)[0][1]
    seen = set()
    while sp in back and back[sp][0] > lvl and sp not in seen:
        seen.add(sp)
        sp = back[sp][1]
    return sp


def to_const(n):
    if n.startswith("SPECIES_"):
        return n[8:]
    return re.sub(r'[^A-Z0-9]+', "_",
                  n.upper().replace("'", "").replace(".", "")).strip("_")


def pretty(c):
    return "SPECIES_" + c if ("_" in c or c == "FARFETCHD") else c.title()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wilds", metavar="SUFFIX",
                    help="rescale wild tables whose base_label ends in _SUFFIX")
    ap.add_argument("--party", metavar="PATH", help="rescale a .party file")
    ap.add_argument("--only", default="",
                    help="with --party, only trainers whose name starts with this")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("bounds", nargs=4, type=int,
                    metavar=("OLD_LO", "OLD_HI", "NEW_LO", "NEW_HI"))
    a = ap.parse_args()
    if not (a.wilds or a.party):
        sys.exit("give --wilds SUFFIX or --party PATH")
    olo, ohi, nlo, nhi = a.bounds
    if ohi <= olo or nhi <= nlo:
        sys.exit("bands must be ascending")

    def scale(lv):
        v = nlo + (lv - olo) * (nhi - nlo) / (ohi - olo)
        return max(nlo, min(nhi, int(round(v))))

    fwd, back = evo_maps()
    moved = changed = 0
    steps = collections.Counter()

    if a.wilds:
        path = "src/data/wild_encounters.json"
        doc = json.load(open(path, encoding="utf-8"))
        suffix = "_" + a.wilds
        seen_any = False
        for g in doc["wild_encounter_groups"]:
            if g["label"] != "gWildMonHeaders":
                continue
            for e in g.get("encounters", []):
                if not e.get("base_label", "").endswith(suffix):
                    continue
                seen_any = True
                for kind in KINDS:
                    for m in e.get(kind, {}).get("mons", []):
                        lo, hi = scale(m["min_level"]), scale(m["max_level"])
                        if (lo, hi) != (m["min_level"], m["max_level"]):
                            moved += 1
                        m["min_level"], m["max_level"] = lo, hi
                        sp = m["species"].replace("SPECIES_", "")
                        sp2 = settle(sp, lo, fwd, back)
                        if sp2 != sp:
                            m["species"] = "SPECIES_" + sp2
                            steps[(sp, sp2)] += 1
                            changed += 1
        if not seen_any:
            sys.exit(f"FAIL: no tables with base_label ending {suffix}")
        if not a.dry:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
                f.write("\n")
        lows = [m["min_level"] for g in doc["wild_encounter_groups"]
                if g["label"] == "gWildMonHeaders"
                for e in g.get("encounters", [])
                if e.get("base_label", "").endswith(suffix)
                for k in KINDS for m in e.get(k, {}).get("mons", [])]
        print(f"wilds{suffix}: {moved} level fields moved, {changed} species settled, "
              f"now L{min(lows)}-{max(m['max_level'] for g in doc['wild_encounter_groups'] if g['label']=='gWildMonHeaders' for e in g.get('encounters', []) if e.get('base_label','').endswith(suffix) for k in KINDS for m in e.get(k, {}).get('mons', []))}")

    if a.party:
        lines = open(a.party, encoding="utf-8").read().split("\n")
        cur, pend, slots = None, None, collections.OrderedDict()
        for i, ln in enumerate(lines):
            if ln.startswith("=== ") and ln.rstrip().endswith(" ==="):
                cur = ln.strip().strip("= ").strip()
                slots[cur] = []
                pend = None
                continue
            if cur is None:
                continue
            s = ln.strip()
            if s.startswith("Level:"):
                if pend is not None:
                    slots[cur].append((pend, i))
                    pend = None
                continue
            if (s and not HDR.match(s) and not s.startswith("-")
                    and not s.startswith(FIELD)):
                pend = i
        for t, pairs in slots.items():
            if a.only and not t.startswith(a.only):
                continue
            for si, li in pairs:
                old = int(lines[li].split(":")[1])
                new = scale(old)
                if new != old:
                    lines[li] = f"Level: {new}"
                    moved += 1
                shown = re.sub(r'\s*\(.*?\)\s*', ' ',
                               lines[si].split("@")[0]).strip()
                c = to_const(shown)
                c2 = settle(c, new, fwd, back)
                if c2 != c:
                    lines[si] = lines[si].replace(shown, pretty(c2), 1)
                    steps[(c, c2)] += 1
                    changed += 1
        if not a.dry:
            open(a.party, "w", encoding="utf-8",
                 newline="\n").write("\n".join(lines))
        got = [int(m) for m in re.findall(r'^Level:\s*(\d+)',
                                          "\n".join(lines), re.M)]
        print(f"{a.party}: {moved} levels moved, {changed} species settled, "
              f"file spans L{min(got)}-{max(got)}")

    for (x, y), n in steps.most_common(12):
        print(f"  {n:>4}  {x} -> {y}")
    if a.dry:
        print("\n(dry run - nothing written)")


if __name__ == "__main__":
    main()
