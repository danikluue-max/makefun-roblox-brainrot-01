#!/usr/bin/env python3
"""Visual overhaul of the cast (round 2): give every brainrot a FACE and
make the models bigger, in src/shared/BrainrotData.luau itself — so the
in-game models (CharacterFactory) and the renders (derived from this file)
improve together.

- Adds per-character face parts: white eye balls + black pupils on the +Z
  face of the head, plus a mouth/beard where the design needs one.
- Scales every part (size/diameter/height/offset) by SCALE so characters
  read at a glance in the screenshots.

Face coordinates are given in ORIGINAL (pre-scale) units and scaled here.
Part lines are written in the exact format rebuild_scene.py's PART_RE parses.
"""
import re, os

ROUND = os.path.expanduser("~/workspace/makefun/entries/roblox-brainrot-01-r1")
PATH = os.path.join(ROUND, "src", "shared", "BrainrotData.luau")
SCALE = 1.25

# id -> list of face parts. eye(dx, y, z, white_r, pupil_r) / mouth(x, y, z, w, h, color)
def eye(dx, y, z, wr=0.5, pr=0.26):
    return [
        {"shape": "Ball", "size": (wr, wr, wr), "offset": (dx, y, z),
         "color": (255, 255, 255)},
        {"shape": "Ball", "size": (pr, pr, pr), "offset": (dx, y, z + 0.22),
         "color": (20, 20, 20)},
    ]

def mouth(x, y, z, w, h, color=(30, 30, 30)):
    return [{"shape": "Block", "size": (w, h, 0.15), "offset": (x, y, z),
             "color": color}]

FACES = {
    "quackington": eye(-0.42, 3.65, 0.78) + eye(0.42, 3.65, 0.78),
    "banana_bus": eye(-1.15, 3.0, 0.85, 0.45, 0.24) + eye(-0.05, 3.0, 0.85, 0.45, 0.24)
        + mouth(-0.6, 2.45, 0.95, 1.0, 0.18),
    "toilet_tornado": eye(-0.55, 1.55, 1.3, 0.45, 0.24) + eye(0.55, 1.55, 1.3, 0.45, 0.24)
        + mouth(0, 1.05, 1.32, 0.7, 0.2),
    "pizza_penguin": eye(-0.38, 3.85, 0.7, 0.45, 0.24) + eye(0.38, 3.85, 0.7, 0.45, 0.24),
    "cactus_cowboy": eye(-0.42, 4.45, 0.78) + eye(0.42, 4.45, 0.78),
    "disco_dolphin": None,  # set below (head faces +X, eyes along Z)
    "ninja_noodle": eye(-0.42, 3.2, 1.02, 0.42, 0.22) + eye(0.42, 3.2, 1.02, 0.42, 0.22)
        + mouth(0, 2.55, 0.82, 0.6, 0.18),
    "turbo_turtle": eye(-0.35, 2.45, 2.52, 0.42, 0.22) + eye(0.35, 2.45, 2.52, 0.42, 0.22)
        + mouth(0, 2.05, 2.55, 0.55, 0.16),
    # Eyes sit ON the glass helmet surface (z 1.2 orig), not inside it —
    # the first version's eyes were buried in the helmet and invisible.
    "galactic_giraffe": eye(-0.4, 6.0, 1.2, 0.56, 0.28) + eye(0.4, 6.0, 1.2, 0.56, 0.28)
        + mouth(0, 5.45, 1.16, 0.55, 0.16),
    "volcano_viking": eye(-0.42, 4.45, 0.78) + eye(0.42, 4.45, 0.78)
        + [{"shape": "Block", "size": (1.3, 0.7, 0.4), "offset": (0, 3.65, 0.75),
            "color": (220, 100, 40)}]
        + mouth(0, 3.8, 0.98, 0.5, 0.15),
    "golden_goblin_king": eye(-0.42, 3.65, 0.78) + eye(0.42, 3.65, 0.78)
        + mouth(0, 3.05, 0.82, 0.6, 0.18),
    "quantum_quokka": eye(-0.38, 3.45, 0.72, 0.45, 0.24) + eye(0.38, 3.45, 0.72, 0.45, 0.24)
        + mouth(0, 2.85, 0.75, 0.55, 0.15),
}

# The dolphin has ONE head on the +X end: two eyes side by side along Z.
FACES["disco_dolphin"] = (
    [{"shape": "Ball", "size": (0.42, 0.42, 0.42), "offset": (2.2, 2.3, 0.62), "color": (255, 255, 255)},
     {"shape": "Ball", "size": (0.22, 0.22, 0.22), "offset": (2.2, 2.3, 0.84), "color": (20, 20, 20)},
     {"shape": "Ball", "size": (0.42, 0.42, 0.42), "offset": (2.55, 2.3, 0.55), "color": (255, 255, 255)},
     {"shape": "Ball", "size": (0.22, 0.22, 0.22), "offset": (2.72, 2.3, 0.72), "color": (20, 20, 20)}]
    + mouth(2.6, 1.7, 0.6, 0.45, 0.14)
)

def fmt_part(p):
    """One part line in BrainrotData format, coordinates already scaled."""
    ox, oy, oz = [round(v * SCALE, 3) for v in p["offset"]]
    r, g, b = p["color"]
    if p["shape"] == "Cylinder":
        return ('\t\t\t{ shape = "Cylinder", diameter = %.3f, height = %.3f, '
                'offset = Vector3.new(%s, %s, %s), color = Color3.fromRGB(%d, %d, %d) },'
                % (p["d"] * SCALE, p["h"] * SCALE, ox, oy, oz, r, g, b))
    sx, sy, sz = [round(v * SCALE, 3) for v in p["size"]]
    return ('\t\t\t{ shape = "%s", size = Vector3.new(%s, %s, %s), '
            'offset = Vector3.new(%s, %s, %s), color = Color3.fromRGB(%d, %d, %d) },'
            % (p["shape"], sx, sy, sz, ox, oy, oz, r, g, b))

def scale_num(m):
    return str(round(float(m.group(0)) * SCALE, 3))

src = open(PATH).read()

# 1) Scale every existing part dimension/offset (only inside the CHARACTERS
# table: the file has Vector3.new / diameter / height nowhere else).
char_start = src.index("BrainrotData.CHARACTERS = {")
char_end = src.index("}\n\nBrainrotData.BY_ID")
head, chars, tail = src[:char_start], src[char_start:char_end], src[char_end:]
chars = re.sub(r"(?<=Vector3\.new\()([\d\.\-, ]+)(?=\))",
               lambda m: ", ".join(str(round(float(v) * SCALE, 3)) for v in m.group(1).split(",")),
               chars)
chars = re.sub(r"(?<=diameter = )[\d\.]+", scale_num, chars)
chars = re.sub(r"(?<=height = )[\d\.]+", scale_num, chars)

# 2) Insert face parts at the end of each character's parts list.
CHAR_RE = re.compile(
    r'(\{ id = "([^"]+)", name = "[^"]+", rarity = "[^"]+", rate = \d+, cost = \d+, tagline = "[^"]*",\s*'
    r'parts = \{(.*?)\n\t\t\},)', re.S)

def add_faces(m):
    cid = m.group(2)
    assert cid in FACES, "no face spec for %s" % cid
    face_lines = "\n".join(fmt_part(p) for p in FACES[cid])
    return m.group(1)[:-len("\n\t\t},")] + "\n" + face_lines + "\n\t\t},"
    # (the last existing part already ends with a comma)
chars2, n = CHAR_RE.subn(add_faces, chars)
assert n == 12, "expected 12 characters, patched %d" % n

open(PATH, "w").write(head + chars2 + tail)
print("gen_cast: scaled x%.2f + faces added for %d characters -> %s" % (SCALE, n, PATH))
