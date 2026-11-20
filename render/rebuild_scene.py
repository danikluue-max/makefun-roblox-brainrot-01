#!/usr/bin/env python3
"""Rebuild /tmp/scene.json from the round dir itself (after the /tmp wipe):
  - world geometry from default.project.json (Rojo tree)
  - characters/rarities/mutations parsed back out of src/shared/BrainrotData.luau
  - cameras/HUD per shot (latest values, as before the wipe)

The scene spec is what the Blender headless render uses; it must match the
game's own world, characters and colors, which it does by construction
here because it is DERIVED from the same files the game ships.
"""
import json, math, os, re

ROUND = os.path.expanduser("~/workspace/makefun/entries/roblox-brainrot-01-r1")

def C(rgb):
    return [round(v / 255, 4) for v in rgb]

# ---------------------------------------------------------------- world from project.json
proj = json.load(open(os.path.join(ROUND, "default.project.json")))
ws = proj["tree"]["Workspace"]

world = []
bases = []

def walk(node, name):
    cls = node.get("$className")
    props = node.get("$properties", {})
    if cls == "Part":
        shape = props.get("Shape", "Block")
        size = props.get("Size", [1, 1, 1])
        rot = props.get("Rotation", [0, 0, 0])
        if shape == "Cylinder":
            # Rojo stores cylinders as Size [height, diameter, diameter], Rotation +90 Z.
            scene_size = [size[1], size[0], size[1]]
            scene_rot = [rot[0], rot[1], rot[2] - 90]
        else:
            scene_size = size
            scene_rot = rot
        world.append({
            "name": name, "shape": shape,
            "pos": [float(v) for v in props.get("Position", [0, 0, 0])],
            "size": [float(v) for v in scene_size],
            "color": [round(v * 255) for v in props.get("Color", [1, 1, 1])],
            "rotation": [float(v) for v in scene_rot],
            "material": props.get("Material", "SmoothPlastic"),
            "transparency": props.get("Transparency", 0),
        })
    for k, v in node.items():
        if k.startswith("$"):
            continue
        if isinstance(v, dict):
            walk(v, k)

for name, node in ws.items():
    if name.startswith("$"):
        continue
    walk(node, name)

# bases: Platform position + color per Base model
for i in range(1, 9):
    base = ws.get("Base%d" % i, {})
    plat = base.get("Platform", {}).get("$properties", {})
    pos = plat.get("Position", [0, 0, 0])
    col = [round(v * 255) for v in plat.get("Color", [1, 1, 1])]
    ang = 22.5 + 45 * (i - 1)
    bases.append({"index": i, "center": [round(pos[0], 2), round(pos[2], 2)],
                  "angle": ang, "color": col, "scene": []})

# ---------------------------------------------------------------- characters from BrainrotData.luau
src = open(os.path.join(ROUND, "src", "shared", "BrainrotData.luau")).read()

rarities = {}
for m in re.finditer(r'(\w+) = \{ color = Color3\.fromRGB\((\d+), (\d+), (\d+)\), weight = (\d+), order = (\d+) \}', src):
    rarities[m.group(1)] = [int(m.group(2)), int(m.group(3)), int(m.group(4))]

mutations = {}
for m in re.finditer(r'\{ name = "(\w+)", mult = (\d+), weight = (\d+), color = (Color3\.fromRGB\((\d+), (\d+), (\d+)\)|nil) \}', src):
    col = None
    if m.group(4) != "nil":
        col = [int(m.group(5)), int(m.group(6)), int(m.group(7))]
    mutations[m.group(1)] = {"mult": int(m.group(2)), "color": col}

CHAR_RE = re.compile(
    r'\{ id = "([^"]+)", name = "([^"]+)", rarity = "([^"]+)", rate = (\d+), cost = (\d+), tagline = "([^"]*)",\s*'
    r'parts = \{(.*?)\n\t\t\},\n\t\},', re.S)
PART_RE = re.compile(
    r'\{ shape = "(Ball|Block|Cylinder)", (?:size = Vector3\.new\(([\d\.\-, ]+)\)|diameter = ([\d\.]+), height = ([\d\.]+)), '
    r'offset = Vector3\.new\(([\d\.\-, ]+)\), color = Color3\.fromRGB\((\d+), (\d+), (\d+)\)'
    r'(?:, material = Enum\.Material\.(\w+))? \}')

characters = []
for m in CHAR_RE.finditer(src):
    parts = []
    for pm in PART_RE.finditer(m.group(7)):
        shape = pm.group(1)
        if shape == "Cylinder":
            parts.append({"shape": "cyl", "d": float(pm.group(3)), "h": float(pm.group(4)),
                          "offset": [float(v) for v in pm.group(5).split(",")],
                          "color": [int(pm.group(6)), int(pm.group(7)), int(pm.group(8))],
                          **({"material": pm.group(9)} if pm.group(9) else {})})
        else:
            parts.append({"shape": shape.lower(), "size": [float(v) for v in pm.group(2).split(",")],
                          "offset": [float(v) for v in pm.group(5).split(",")],
                          "color": [int(pm.group(6)), int(pm.group(7)), int(pm.group(8))],
                          **({"material": pm.group(9)} if pm.group(9) else {})})
    characters.append({"id": m.group(1), "name": m.group(2), "rarity": m.group(3),
                       "rate": int(m.group(4)), "cost": int(m.group(5)),
                       "tagline": m.group(6), "parts": parts})

assert len(characters) == 36, "expected 36 characters, got %d" % len(characters)
assert len(rarities) == 7, "expected 7 rarities, got %d" % len(rarities)
assert len(mutations) == 6, "expected 6 mutations, got %d" % len(mutations)

scene = {
    "world": world,
    "characters": characters,
    "rarities": rarities,
    "mutations": mutations,
    "bases": bases,
    "lane_chars": [
        {"id": "starla_starfish", "x": -70, "mutation": "None"},
        {"id": "surfboard_sammy", "x": -52, "mutation": "Golden"},
        {"id": "coral_clownfish", "x": -34, "mutation": "None"},
        {"id": "lifeguard_larry", "x": -17, "mutation": "Neon"},
        {"id": "octo_ollie", "x": 0, "mutation": "None"},
        {"id": "captain_coral", "x": 17, "mutation": "Diamond"},
        {"id": "pearl_pufferfish", "x": 34, "mutation": "None"},
        {"id": "kraken_karl", "x": 52, "mutation": "Rainbow"},
        {"id": "sun_god_surfer", "x": 70, "mutation": "Cosmic"},
    ],
    "docked": [
        {"id": "quackington", "slot": 1, "mutation": "None"},
        {"id": "banana_bus", "slot": 2, "mutation": "Golden"},
        {"id": "pizza_penguin", "slot": 3, "mutation": "None"},
        {"id": "cactus_cowboy", "slot": 4, "mutation": "None"},
        {"id": "disco_dolphin", "slot": 5, "mutation": "Diamond"},
        {"id": "ninja_noodle", "slot": 6, "mutation": "None"},
    ],
    # Heroes: big characters staged close to the camera per shot, so the
    # frame is full of readable creatures (not empty green). Round 3: the
    # cover shows the two new Divine characters + the Secret leviathan;
    # 2-play shows two new mid-tier heroes (Epic octopus, Legendary
    # pufferfish); 3-end shows the wave bosses (Legendary tsunami tiki +
    # neptune). 4-book has no heroes: the prize-book panel owns the frame.
    "heroes": {
        "1-start": [
            # BEACH STAGING (round 3, fifth try): ... Heroes face south
            # (-Z) toward the camera: rot 180 (faces were +Z), leviathan
            # rot 90 (face was +X). The right flank was Poseidon Pelican
            # but its all-white body+head read as a featureless blob, so
            # it was swapped for Sun God Surfer (Divine, gold Neon body +
            # sun rays + skin head — reads instantly).
            {"id": "sun_god_surfer", "x": -7, "z": -22, "mutation": "None", "rot": 180},
            {"id": "ocean_oracle", "x": 7, "z": -22, "mutation": "Cosmic", "rot": 180},
            {"id": "rainbow_reef_leviathan", "x": 0, "z": -23, "mutation": "None", "rot": 90},
        ],
        "2-play": [
            {"id": "octo_ollie", "x": -18, "z": 0, "mutation": "None"},
            {"id": "pearl_pufferfish", "x": -10, "z": -1, "mutation": "Diamond"},
        ],
        "3-end": [
            # Wave bosses on the beach south of the lane (round 3, third
            # try): the north-side cameras kept putting the plaza flags in
            # the foreground and the heroes at the frame edges. Shooting
            # from just north of the lane, looking south, puts the flags
            # BEHIND the camera and the wave behind the heroes. The lane
            # is in the lower foreground (depth, not a blocker).
            {"id": "tsunami_tiki", "x": -7, "z": -12, "mutation": "None"},
            {"id": "neptune_nemo", "x": 4, "z": -12, "mutation": "None"},
        ],
        "4-book": [],
    },
    "shots": {
        "1-start": {
            # COVER FRAMING (round 3, fifth try — beach staging): camera
            # from the south over the open beach, heroes facing it. The
            # straight-on north cameras were blocked by Flag7/Flag8 and the
            # diagonal east camera let each hero's own body swallow its
            # face. Here nothing stands between camera and heroes. Target
            # Target y=7 (was 4, then 9): y=4 put the flank heads behind
            # the subtitle strip, y=9 pushed the leviathan behind the hint
            # bar. y=7 splits the difference.
            "camera": {"pos": [0, 7, -46], "target": [0, 7, -22], "lens": 30},
            "hud": {"title": "BRAINROT BAY", "subtitle": "Collect absurd friends  •  Earn $ every second  •  Steal  •  Survive the wave",
                    "ladder": "36 BRAINROTS  •  7 RARITIES  •  6 MUTATIONS",
                    "money": "$100", "income": "+$0/s", "hint": "Walk the conveyor — buy your first brainrot!"},
            "note": "cover",
        },
        "2-play": {
            # PLAY FRAMING (round 3, second try): the first camera was too
            # close for the bigger round-3 heroes — the octopus and the
            # pufferfish were cropped and their 3D labels collided with the
            # quests panel / the right edge. Camera pulled back to z=30,
            # wider lens, heroes repositioned so their labels land clear of
            # the quests panel (left) and the frame edge (right).
            "camera": {"pos": [-14, 10, 30], "target": [-12, 4, -2], "lens": 28},
            "hud": {"money": "$2,480", "income": "+$165/s",
                    "carry": "Carrying: Disco Dolphin — take it home!",
                    "shop": [{"name": "Disco Dolphin", "rarity": "Epic", "rate": "$150/s", "cost": "$1,500"},
                             {"name": "Ninja Noodle", "rarity": "Legendary", "rate": "$300/s", "cost": "$3,000"},
                             {"name": "Turbo Turtle", "rarity": "Legendary", "rate": "$500/s", "cost": "$5,000"},
                             {"name": "Galactic Giraffe", "rarity": "Mythic", "rate": "$1,200/s", "cost": "$12,000"}],
                    "quests": [{"name": "Buy 3 brainrots", "progress": 2, "target": 3, "reward": "$500"},
                               {"name": "Steal 1 brainrot", "progress": 0, "target": 1, "reward": "$1,500"},
                               {"name": "Survive a tsunami", "progress": 1, "target": 1, "reward": "$1,000", "claim": True}],
                    "book_count": "34/36"},
            "note": "play",
        },
        "3-end": {
            # WAVE FRAMING (round 3, third try): camera just north of the
            # lane looking south — heroes on the beach, wave towering
            # behind them, plaza flags behind the camera. Camera offset to
            # x=14: centred on x=0 the rainbow arch's north end sat right
            # in front of the lens and its balls filled the frame; offset,
            # the arch falls to the left edge as an accent. Camera raised
            # to y=12: the lane (with its walking brainrots) drops to the
            # bottom of the frame instead of blocking the tiki. Lens 35
            # (was 30): the foreground lane brainrot at the left sits
            # ~32 deg off-axis, just outside a 35mm lens's ~27 deg
            # half-FOV, while both heroes (~9-12 deg) stay in.
            "camera": {"pos": [14, 12, 18], "target": [-3, 4, -25], "lens": 35},
            "hud": {"money": "$8,940", "income": "+$412/s",
                    "wave": "TSUNAMI INCOMING — RUN TO YOUR BASE!",
                    "wave_timer": "WAVE IN 8s"},
            "wave": True,
            "note": "wave",
        },
        "4-book": {
            "camera": {"pos": [0, 16, 70], "target": [0, 4, 0], "lens": 35},
            "hud": {"money": "$41,200", "income": "+$2,150/s",
                    "found": 34, "total": 36},
            "note": "prize book",
        },
    },
}

with open("/tmp/scene.json", "w") as f:
    json.dump(scene, f, indent=1)
print("world parts:", len(world), "| bases:", len(bases),
      "| characters:", len(characters), "| rarities:", len(rarities), "| mutations:", len(mutations))
print("wrote /tmp/scene.json")
