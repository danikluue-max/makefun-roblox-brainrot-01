#!/usr/bin/env python3
"""Round 3 world pass: beach landmarks in default.project.json (the actual
game place, so the game itself and the renders improve together).

Adds ~60 props, all named V3_*; the generator first removes any old V3_*
parts, so it is idempotent (re-run safe). Nothing existing is touched.

  - Pier on the south edge (wooden deck + posts + end hut), between bases
    6 and 7, reaching the map edge.
  - Lighthouse on the west edge (striped tower + warm neon lamp room).
  - 4 surfboards leaning near the pool and plaza.
  - 3 beach umbrellas (pole + striped canopy).
  - 5 beach balls scattered on the sand.
  - A big wave sculpture by the pool (stacked curling tiers + foam).
  - 2 sandcastles.

Ground is y=0 (baseplate top). Lane belt occupies |z|<6.5, |x|<115.
Bases sit on a ring at radius ~105. Every landmark keeps clear of the
lane, the bases, the plaza (0,48), the shop (0,-52) and both pools.
"""
import json, math, os

ROUND = os.path.expanduser("~/workspace/makefun/entries/roblox-brainrot-01-r1")
PATH = os.path.join(ROUND, "default.project.json")

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

# remove any previous V3 generation
for k in [k for k in ws if k.startswith("V3_")]:
    del ws[k]

new = {}
def add(item):
    name, node = item
    assert name not in ws and name not in new, "duplicate part name %s" % name
    new[name] = node

WOOD = C(139, 90, 43)
SAND = C(235, 210, 160)
WHITE = C(255, 255, 255)

# ---- pier (south edge, x=0, z -118..-156)
for i, z in enumerate((-126, -138, -150)):
    add(box("V3_PierDeck_%d" % i, (0, 0.8, z), (12, 1, 12), WOOD))
for i, (px, pz) in enumerate([(-5, -124), (5, -124), (-5, -136), (5, -136),
                              (-5, -148), (5, -148), (-5, -156), (5, -156)]):
    add(cyl("V3_PierPost_%d" % i, (px, 0.6, pz), 0.6, 2.0, WOOD))
add(box("V3_PierHut", (0, 4.0, -154), (8, 5, 6), C(200, 220, 240)))
add(box("V3_PierRoof", (0, 7.0, -154), (9, 1, 7), C(220, 38, 38)))
add(box("V3_PierCrate", (-3.5, 1.6, -150), (2.5, 2.5, 2.5), WOOD))

# ---- lighthouse (west edge, -132, 0)
add(cyl("V3_LightTowerA", (-132, 5, 0), 8, 10, WHITE))
add(cyl("V3_LightTowerB", (-132, 15, 0), 7, 10, C(220, 38, 38)))
add(cyl("V3_LightTowerC", (-132, 25, 0), 6, 10, WHITE))
add(box("V3_LightRoom", (-132, 31.5, 0), (5, 4, 5), C(255, 200, 90), "Neon"))
add(box("V3_LightCap", (-132, 34.5, 0), (7, 1, 7), C(60, 60, 70)))
add(box("V3_LightDock", (-124, 0.8, 0), (10, 1, 8), WOOD))

# ---- surfboards leaning near the pool / plaza
BOARD_COLS = [C(255, 80, 80), C(70, 130, 255), C(255, 217, 61), C(34, 197, 94)]
for i, (bx, bz, tilt) in enumerate([(60, 62, 18), (66, 70, -14),
                                    (-58, -58, 16), (30, 42, -20)]):
    add(box("V3_Surfboard_%d" % i, (bx, 3.0, bz), (1.4, 6.0, 0.35),
            BOARD_COLS[i], rotation=(0, 0, tilt)))
    add(box("V3_SurfStripe_%d" % i, (bx, 4.2, bz + 0.1), (1.5, 0.7, 0.4),
            WHITE, rotation=(0, 0, tilt)))

# ---- beach umbrellas (pole + striped canopy)
UMB_COLS = [C(220, 38, 38), C(70, 130, 255), C(255, 217, 61)]
for i, (ux, uz) in enumerate([(-50, 30), (50, -30), (20, 62)]):
    add(cyl("V3_UmbPole_%d" % i, (ux, 2.5, uz), 0.5, 5, WHITE, "Metal"))
    add(ball("V3_UmbTop_%d" % i, (ux, 5.6, uz), 7, UMB_COLS[i]))
    # squash the canopy ball flat (rebuild size directly, like the hills)
    new["V3_UmbTop_%d" % i]["$properties"]["Size"] = [7, 2.2, 7]
    add(ball("V3_UmbKnob_%d" % i, (ux, 6.8, uz), 0.9, WHITE))

# ---- beach balls
BALL_COLS = [C(255, 80, 80), C(70, 130, 255), C(255, 217, 61),
             C(34, 197, 94), C(255, 120, 200)]
for i, (bx, bz) in enumerate([(-30, -20), (30, 20), (-70, 50), (70, -50), (10, -70)]):
    add(ball("V3_BeachBall_%d" % i, (bx, 1.4, bz), 2.8, BALL_COLS[i]))

# ---- big wave sculpture by the pool (110, 110)
add(box("V3_WaveBase", (110, 2, 110), (18, 4, 6), C(40, 120, 255)))
add(box("V3_WaveMid", (108, 6, 110), (14, 4, 5), C(60, 140, 255)))
add(box("V3_WaveTop", (105, 10, 110), (10, 4, 4), C(80, 170, 255)))
add(ball("V3_WaveFoamA", (100, 12.5, 110), 3.5, WHITE))
add(ball("V3_WaveFoamB", (105, 12.8, 110), 3.0, WHITE))
add(ball("V3_WaveFoamC", (110, 12.5, 110), 2.5, WHITE))

# ---- sandcastles
for i, (sx, sz) in enumerate([(-20, 70), (85, 20)]):
    add(box("V3_CastleBase_%d" % i, (sx, 1.5, sz), (5, 3, 5), SAND))
    add(cyl("V3_CastleTower_%d" % i, (sx, 4.0, sz), 2.5, 2.5, SAND))
    add(box("V3_CastleFlag_%d" % i, (sx, 5.8, sz), (1.2, 0.8, 0.15), C(220, 38, 38)))

ws.update(new)
with open(PATH, "w") as f:
    json.dump(proj, f, indent=1)
print("gen_world3: added %d parts -> %s" % (len(new), PATH))
