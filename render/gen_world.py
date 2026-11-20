#!/usr/bin/env python3
"""Round 2 visual overhaul: densify Brainrot Bay's world in
default.project.json (the actual game place, so the game itself and the
renders improve together).

Adds ~340 props: sand walkways + radial paths, lane fences, market stalls,
lamp posts, trees, bushes, flower beds, a fountain, hills, clouds,
billboards, crates, coins, benches, torches, a second pool. Every new part
is named V2_* and the generator first removes any old V2_* parts, so it is
idempotent (re-run safe). Nothing existing is touched.

Ground is y=0 (baseplate top). Lane belt occupies |z|<6.5, |x|<115.
Bases sit on a ring at radius ~105 (26x26 platforms). Plaza is (0,48),
shop is (0,-52), pool is (78,78). Props keep clear of those.
"""
import json, math, os, random

ROUND = os.path.expanduser("~/workspace/makefun/entries/roblox-brainrot-01-r1")
PATH = os.path.join(ROUND, "default.project.json")
rng = random.Random(20261120)

def C(r, g, b):
    return [round(v / 255, 4) for v in (r, g, b)]

def part(shape, pos, size, color, material="SmoothPlastic", rotation=(0, 0, 0),
         transparency=0.0, cancollide=False):
    props = {
        "Anchored": True, "CanCollide": cancollide, "Color": color,
        "Material": material, "Position": [float(v) for v in pos],
        "Rotation": [float(v) for v in rotation], "Shape": shape,
        "Size": [float(v) for v in size], "Transparency": transparency,
        "Locked": False,
    }
    return {"$className": "Part", "$properties": props}

def cyl(name, pos, diameter, height, color, material="SmoothPlastic",
        transparency=0.0, cancollide=False):
    # Rojo cylinders: Size [height, diameter, diameter], Rotation +90 Z.
    return (name, part("Cylinder", pos, (height, diameter, diameter), color,
                       material, rotation=(0, 0, 90), transparency=transparency,
                       cancollide=cancollide))

def ball(name, pos, diameter, color, material="SmoothPlastic", transparency=0.0):
    return (name, part("Ball", pos, (diameter, diameter, diameter), color,
                       material, transparency=transparency))

def box(name, pos, size, color, material="SmoothPlastic", rotation=(0, 0, 0),
        transparency=0.0, cancollide=False):
    return (name, part("Block", pos, size, color, material,
                       rotation=rotation, transparency=transparency,
                       cancollide=cancollide))

proj = json.load(open(PATH))
ws = proj["tree"]["Workspace"]

# remove any previous V2 generation
for k in [k for k in ws if k.startswith("V2_")]:
    del ws[k]

BASE_ANGLES = [22.5 + 45 * i for i in range(8)]
BASE_CENTERS = [(105 * math.cos(math.radians(a)), 105 * math.sin(math.radians(a)))
                for a in BASE_ANGLES]

def clear_of(x, z, margin=0.0):
    """True if (x,z) is free ground: off the lane, off bases, off plaza/shop/pool."""
    if abs(z) < 8 + margin and abs(x) < 118:
        return False
    for bx, bz in BASE_CENTERS:
        if math.hypot(x - bx, z - bz) < 17 + margin:
            return False
    if math.hypot(x, z - 48) < 13 + margin:
        return False
    if math.hypot(x, z + 52) < 11 + margin:
        return False
    if math.hypot(x - 78, z - 78) < 15 + margin:
        return False
    if math.hypot(x + 78, z + 78) < 15 + margin:
        return False
    if math.hypot(x, z) > 152:
        return False
    return True

new = {}
def add(item):
    name, node = item
    assert name not in ws and name not in new, "duplicate part name %s" % name
    new[name] = node

SAND = C(235, 210, 160)
WOOD = C(139, 90, 43)
LEAF = [C(34, 160, 70), C(46, 180, 80), C(28, 140, 60)]
WARM = C(255, 200, 90)

# ---- sand walkways flanking the lane
for z in (-10, 10):
    add(box("V2_Walk_%d" % z, (0, 0.12, z), (230, 0.24, 4.5), SAND))
# ---- radial paths from the centre to each base
for i, a in enumerate(BASE_ANGLES):
    r = math.radians(a)
    add(box("V2_Path_%d" % i, (55 * math.cos(r), 0.12, 55 * math.sin(r)),
            (88, 0.24, 4.5), SAND, rotation=(0, -a, 0)))

# ---- lane fences: posts + rails
for z in (-8, 8):
    add(box("V2_FenceRail_%d" % z, (0, 1.5, z), (230, 0.3, 0.3), C(240, 240, 240)))
    for x in range(-108, 109, 12):
        add(cyl("V2_FencePost_%d_%d" % (z, x), (x, 0.8, z), 0.45, 1.6, WOOD))

# ---- market stalls (4): counter, posts, striped awning, goods
STALL_SPOTS = [(-45, 14), (45, 14), (-85, -14), (85, -14)]
AWN = [C(220, 38, 38), C(255, 255, 255), C(124, 97, 212)]
for si, (sx, sz) in enumerate(STALL_SPOTS):
    add(box("V2_StallCounter_%d" % si, (sx, 1.0, sz), (7, 2, 3.5), WOOD))
    for dx, dz in ((-3, -1.5), (3, -1.5), (-3, 1.5), (3, 1.5)):
        add(cyl("V2_StallPost_%d_%d_%d" % (si, dx, dz), (sx + dx, 2.6, sz + dz),
                0.4, 3.2, WOOD))
    for k in range(3):
        add(box("V2_StallAwn_%d_%d" % (si, k), (sx - 2.4 + k * 2.4, 4.4, sz),
                (2.4, 0.3, 4.5), AWN[k % 3]))
    for k, col in enumerate([C(255, 80, 80), C(255, 200, 60), C(80, 200, 120),
                             C(120, 140, 255), C(255, 120, 200)]):
        add(ball("V2_StallGoods_%d_%d" % (si, k), (sx - 2.4 + k * 1.2, 2.5, sz), 0.9, col))

# ---- lamp posts (8) at radius 40, warm neon tops
for i, a in enumerate([36 * k for k in range(10) if k % 5 != 0]):
    r = math.radians(a)
    x, z = 40 * math.cos(r), 40 * math.sin(r)
    add(cyl("V2_LampPole_%d" % i, (x, 3, z), 0.5, 6, C(60, 60, 70), "Metal"))
    add(ball("V2_LampTop_%d" % i, (x, 6.4, z), 1.5, WARM, "Neon"))

# ---- trees (16 new): trunk + 3 leaf balls, deterministic scatter
placed = 0
tries = 0
while placed < 16 and tries < 400:
    tries += 1
    ang = rng.uniform(0, 360)
    rad = rng.uniform(58, 138)
    x, z = rad * math.cos(math.radians(ang)), rad * math.sin(math.radians(ang))
    if not clear_of(x, z, 4):
        continue
    g = rng.choice(LEAF)
    add(cyl("V2_TreeTrunk_%d" % placed, (x, 2.5, z), 1.3, 5, WOOD))
    add(ball("V2_TreeLeafA_%d" % placed, (x, 6.5, z), 4.2, g))
    add(ball("V2_TreeLeafB_%d" % placed, (x - 1.6, 5.2, z + 0.8), 3.0, g))
    add(ball("V2_TreeLeafC_%d" % placed, (x + 1.5, 5.6, z - 0.9), 2.8, g))
    placed += 1

# ---- bushes (24)
placed = 0
tries = 0
while placed < 24 and tries < 400:
    tries += 1
    ang = rng.uniform(0, 360)
    rad = rng.uniform(22, 140)
    x, z = rad * math.cos(math.radians(ang)), rad * math.sin(math.radians(ang))
    if not clear_of(x, z, 2):
        continue
    add(ball("V2_Bush_%d" % placed, (x, 1.0, z), rng.uniform(2.0, 3.2),
             rng.choice(LEAF)))
    placed += 1

# ---- flower beds: 6 clusters x 4 flowers
FLOWER_COLS = [C(255, 80, 120), C(255, 200, 60), C(140, 120, 255), C(255, 255, 255)]
for c in range(6):
    ang = rng.uniform(0, 360)
    rad = rng.uniform(25, 60)
    cx, cz = rad * math.cos(math.radians(ang)), rad * math.sin(math.radians(ang))
    if not clear_of(cx, cz, 3):
        continue
    for f in range(4):
        fx, fz = cx + rng.uniform(-3, 3), cz + rng.uniform(-3, 3)
        add(cyl("V2_FlowerStem_%d_%d" % (c, f), (fx, 0.5, fz), 0.25, 1.0, C(40, 160, 70)))
        add(ball("V2_FlowerTop_%d_%d" % (c, f), (fx, 1.2, fz), 0.9, FLOWER_COLS[(c + f) % 4]))

# ---- fountain at (-60, 60)
add(cyl("V2_FountainBasin", (-60, 0.6, 60), 12, 1.2, C(200, 200, 210)))
add(cyl("V2_FountainWater", (-60, 1.0, 60), 10, 0.4, C(60, 160, 255), "Neon", 0.15))
add(cyl("V2_FountainPillar", (-60, 2.8, 60), 1.6, 3.6, C(220, 220, 225)))
add(ball("V2_FountainTop", (-60, 4.9, 60), 2.4, C(90, 180, 255), "Neon"))

# ---- hills at the map edge (6)
for i, a in enumerate([0, 60, 120, 180, 240, 300]):
    r = math.radians(a)
    x, z = 146 * math.cos(r), 146 * math.sin(r)
    d = rng.uniform(24, 32)
    add(ball("V2_Hill_%d" % i, (x, 0.5, z), d, rng.choice(LEAF)))
    # squash vertically by rebuilding as a flattened ball via size override
    new["V2_Hill_%d" % i]["$properties"]["Size"] = [d, d * 0.35, d]

# ---- clouds (8 more)
for i in range(8):
    ang = rng.uniform(0, 360)
    rad = rng.uniform(60, 140)
    add(ball("V2_Cloud_%d" % i,
             (rad * math.cos(math.radians(ang)), rng.uniform(48, 58),
              rad * math.sin(math.radians(ang))),
             rng.uniform(8, 13), C(255, 255, 255), transparency=0.1))

# ---- billboards (3): pole + bright board facing the centre
for i, (bx, bz, col) in enumerate([(-35, -28, C(124, 97, 212)),
                                   (35, -28, C(245, 158, 11)),
                                   (0, 75, C(6, 182, 212))]):
    ang = math.degrees(math.atan2(-bz, -bx))  # face the centre
    add(cyl("V2_BoardPole_%d" % i, (bx, 5.5, bz), 1.0, 11, C(60, 60, 70), "Metal"))
    add(box("V2_Board_%d" % i, (bx, 12.5, bz), (12, 6.5, 0.6), col,
            rotation=(0, ang, 0)))
    add(box("V2_BoardTrim_%d" % i, (bx, 9.0, bz), (12, 0.8, 0.7), C(255, 255, 255),
            rotation=(0, ang, 0)))

# ---- crates & barrels near stalls (12)
for i, (sx, sz) in enumerate(STALL_SPOTS):
    for k in range(3):
        ox, oz = (-5.5 if k == 0 else 5.5 if k == 1 else 0), (-3.5 if k == 2 else 3.5)
        if k < 2:
            add(box("V2_Crate_%d_%d" % (i, k), (sx + ox, 1.25, sz + oz), (2.5, 2.5, 2.5), WOOD))
        else:
            add(cyl("V2_Barrel_%d" % i, (sx + ox, 1.5, sz + oz), 2.0, 3.0, C(90, 140, 200)))

# ---- coins along the walkways (10)
for i in range(10):
    x = -100 + i * 22
    z = 10 if i % 2 == 0 else -10
    add(cyl("V2_Coin_%d" % i, (x, 0.35, z), 1.6, 0.35, C(255, 215, 0), "Metal"))

# ---- benches along the walkways (6)
for i, (bx, bz) in enumerate([(-70, 13), (-20, -13), (20, 13), (70, -13), (-100, 13), (100, -13)]):
    add(box("V2_BenchSeat_%d" % i, (bx, 1.0, bz), (4.5, 0.5, 1.6), WOOD))
    add(box("V2_BenchBack_%d" % i, (bx, 1.9, bz - 0.7), (4.5, 1.6, 0.4), WOOD))
    add(box("V2_BenchLegA_%d" % i, (bx - 1.8, 0.4, bz), (0.5, 0.8, 1.4), C(60, 60, 70)))
    add(box("V2_BenchLegB_%d" % i, (bx + 1.8, 0.4, bz), (0.5, 0.8, 1.4), C(60, 60, 70)))

# ---- torches at each base entrance (8)
for i, a in enumerate(BASE_ANGLES):
    r = math.radians(a)
    x, z = 88 * math.cos(r), 88 * math.sin(r)
    add(cyl("V2_TorchPole_%d" % i, (x, 1.5, z), 0.4, 3.0, WOOD))
    add(ball("V2_TorchFlame_%d" % i, (x, 3.5, z), 1.1, C(255, 140, 40), "Neon"))

# ---- second pool at (-78, -78): sand ring + water
add(cyl("V2_Pool2Sand", (-78, 0.15, -78), 28, 0.3, SAND))
add(cyl("V2_Pool2Water", (-78, 0.35, -78), 24, 0.5, C(40, 120, 220), "Neon", 0.1))

ws.update(new)
with open(PATH, "w") as f:
    json.dump(proj, f, indent=1)
print("gen_world: added %d parts -> %s" % (len(new), PATH))
