#!/usr/bin/env python3
"""Round 3 (top-1 push): expand the cast 12 -> 36 ORIGINAL beach characters,
6 -> 7 rarities (adds Divine), 4 -> 6 mutations (adds Neon x3, Cosmic x10).

Patches src/shared/BrainrotData.luau in place:
  - RARITIES: Common 38 / Rare 26 / Epic 15 / Legendary 9 / Mythic 6 /
    Secret 4 / Divine 2 (weights sum 100). Divine colour is white.
  - MUTATIONS: None 70 x1 / Golden 14 x2 / Neon 3 x3 / Diamond 7 x4 /
    Rainbow 4 x8 / Cosmic 2 x10 (weights sum 100).
  - RARITIES_ARRAY weights updated to match.
  - 24 new character entries appended to CHARACTERS (table order does not
    matter: the server pools by rarity, BY_ID is a map).

All new characters are built from Ball + Block parts ONLY (no Cylinders):
a spec Cylinder is vertical in the game but renders as a depth bar in the
headless Blender pipeline, so Ball/Block keeps game and render identical.
Every character gets a FACE (white eye balls + black pupils on the +Z face
of the head, plus a mouth) in the same post-scale coordinates as the
round-2 file, so no re-scaling is applied here.

Names are all original beach inventions — nothing copied from the
leaderboard #1 entry or from Steal a Brainrot.
"""
import re, os

ROUND = os.path.expanduser("~/workspace/makefun/entries/roblox-brainrot-01-r1")
PATH = os.path.join(ROUND, "src", "shared", "BrainrotData.luau")

def f(v):
    """Float in the file's style: 3 decimals max, keeps a trailing .0."""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if "." in s else s + ".0"

def ball(size, off, color, mat=None):
    return ("Ball", size, off, color, mat)

def block(size, off, color, mat=None):
    return ("Block", size, off, color, mat)

def eyes(cx, cy, cz, spread=0.45, wr=0.55, pr=0.28):
    """Face on the +Z side of a head centred at (cx, cy, cz-front)."""
    return [
        ball((wr, wr, wr), (cx - spread, cy, cz), (255, 255, 255)),
        ball((pr, pr, pr), (cx - spread, cy, cz + 0.26), (20, 20, 20)),
        ball((wr, wr, wr), (cx + spread, cy, cz), (255, 255, 255)),
        ball((pr, pr, pr), (cx + spread, cy, cz + 0.26), (20, 20, 20)),
    ]

def eyes_x(hx, hy, hz, spread=0.55, wr=0.5, pr=0.26):
    """Face on the +X end of a fish head (eyes side by side along Z)."""
    return [
        ball((wr, wr, wr), (hx, hy, hz - spread), (255, 255, 255)),
        ball((pr, pr, pr), (hx + 0.26, hy, hz - spread), (20, 20, 20)),
        ball((wr, wr, wr), (hx, hy, hz + spread), (255, 255, 255)),
        ball((pr, pr, pr), (hx + 0.26, hy, hz + spread), (20, 20, 20)),
    ]

def mouth(x, y, z, w=0.6, h=0.18, color=(30, 30, 30)):
    return [block((w, h, 0.15), (x, y, z), color)]

# ------------------------------------------------------------------ new cast
# (id, name, rarity, rate, cost, tagline, [parts])
NEW = []

# --- Common: 4 new (total 6) ---
NEW.append(("starla_starfish", "Starla Starfish", "Common", 3, 30,
    "Five arms, zero worries, one big dream.",
    [ball((4.5, 1.75, 4.5), (0, 1.5, 0), (255, 140, 0)),
     ball((1.75, 1.75, 1.75), (2.2, 1.5, 0), (255, 140, 0)),
     ball((1.75, 1.75, 1.75), (-2.2, 1.5, 0), (255, 140, 0)),
     ball((1.75, 1.75, 1.75), (0, 1.5, 2.2), (255, 140, 0)),
     ball((1.75, 1.75, 1.75), (0, 1.5, -2.2), (255, 140, 0)),
     ball((2.0, 2.0, 2.0), (0, 2.6, 0.3), (255, 170, 60)),
     ball((0.9, 0.9, 0.9), (1.2, 2.9, -0.6), (255, 120, 180)),
     ] + eyes(0, 2.9, 1.15, spread=0.45) + mouth(0, 2.4, 1.2, w=0.55)))

NEW.append(("bobo_beachball", "Bobo Beachball", "Common", 12, 120,
    "He bounces. You profit. Everybody wins.",
    [ball((4.5, 4.5, 4.5), (0, 2.5, 0), (255, 255, 255)),
     ball((1.6, 1.6, 1.6), (-1.6, 3.4, 1.6), (220, 60, 60)),
     ball((1.6, 1.6, 1.6), (1.6, 3.4, 1.6), (70, 130, 255)),
     ball((1.6, 1.6, 1.6), (0, 1.6, 1.9), (255, 217, 61)),
     block((0.25, 2.0, 0.25), (0, 5.5, 0), (139, 90, 43)),
     block((1.2, 0.7, 0.15), (0.6, 6.2, 0), (255, 217, 61)),
     ] + eyes(0, 3.1, 2.0, spread=0.55) + mouth(0, 2.5, 2.1, w=0.6)))

NEW.append(("crabby_crabcake", "Crabby Crabcake", "Common", 18, 180,
    "Sideways is a lifestyle, not a limitation.",
    [ball((4.25, 2.5, 3.25), (0, 1.8, 0), (220, 60, 60)),
     ball((1.75, 1.75, 1.75), (2.75, 2.0, 0.75), (220, 60, 60)),
     ball((1.75, 1.75, 1.75), (-2.75, 2.0, 0.75), (220, 60, 60)),
     block((1.5, 0.35, 0.35), (2.3, 1.0, -0.9), (200, 40, 40)),
     block((1.5, 0.35, 0.35), (-2.3, 1.0, -0.9), (200, 40, 40)),
     block((1.5, 0.35, 0.35), (2.3, 1.0, 0.9), (200, 40, 40)),
     block((1.5, 0.35, 0.35), (-2.3, 1.0, 0.9), (200, 40, 40)),
     block((0.4, 1.25, 0.4), (-0.75, 3.6, 0.9), (220, 60, 60)),
     block((0.4, 1.25, 0.4), (0.75, 3.6, 0.9), (220, 60, 60)),
     ball((0.7, 0.7, 0.7), (-0.75, 4.35, 0.9), (255, 255, 255)),
     ball((0.35, 0.35, 0.35), (-0.75, 4.35, 1.25), (20, 20, 20)),
     ball((0.7, 0.7, 0.7), (0.75, 4.35, 0.9), (255, 255, 255)),
     ball((0.35, 0.35, 0.35), (0.75, 4.35, 1.25), (20, 20, 20)),
     ] + mouth(0, 1.5, 1.65, w=0.8)))

NEW.append(("shelly_seagull", "Shelly Seagull", "Common", 22, 220,
    "She saw your sandwich first. She always does.",
    [ball((3.5, 2.75, 4.25), (0, 2.25, 0), (255, 255, 255)),
     ball((2.0, 2.0, 2.0), (0, 4.5, 0.9), (255, 255, 255)),
     block((1.0, 0.45, 1.25), (0, 4.4, 2.1), (255, 140, 66)),
     block((0.5, 1.75, 2.5), (2.0, 2.5, 0), (220, 220, 230)),
     block((0.5, 1.75, 2.5), (-2.0, 2.5, 0), (220, 220, 230)),
     block((1.75, 0.5, 1.5), (0, 2.5, -2.5), (255, 255, 255)),
     block((1.0, 0.3, 1.25), (-0.75, 0.4, 0.75), (255, 140, 66)),
     block((1.0, 0.3, 1.25), (0.75, 0.4, 0.75), (255, 140, 66)),
     ] + eyes(0, 4.8, 1.75, spread=0.45)))

# --- Rare: 4 new (total 6) ---
NEW.append(("surfboard_sammy", "Surfboard Sammy", "Rare", 60, 600,
    "Hang ten, earn twenty. The math checks out.",
    [block((2.25, 5.5, 0.35), (0, 3.5, -1.5), (6, 182, 212)),
     block((2.25, 0.6, 0.4), (0, 4.5, -1.5), (255, 217, 61)),
     block((0.9, 2.0, 0.9), (-0.6, 1.25, 0), (245, 200, 160)),
     block((0.9, 2.0, 0.9), (0.6, 1.25, 0), (245, 200, 160)),
     block((2.5, 2.25, 1.25), (0, 3.25, 0), (59, 130, 246)),
     ball((2.0, 2.0, 2.0), (0, 5.25, 0), (245, 200, 160)),
     block((2.25, 0.75, 2.25), (0, 6.25, 0), (255, 217, 61)),
     block((0.7, 2.0, 0.7), (-1.6, 3.25, 0), (245, 200, 160)),
     block((0.7, 2.0, 0.7), (1.6, 3.25, 0), (245, 200, 160)),
     ] + eyes(0, 5.5, 0.95, spread=0.45) + mouth(0, 4.9, 1.0, w=0.55)))

NEW.append(("coral_clownfish", "Coral Clownfish", "Rare", 80, 800,
    "Orange, white, and absolutely not funny. He insists.",
    [ball((4.5, 2.75, 2.25), (0, 2.5, 0), (255, 140, 66)),
     ball((1.25, 1.25, 1.25), (-0.9, 2.9, 0), (255, 255, 255)),
     ball((1.25, 1.25, 1.25), (0.6, 2.9, 0), (255, 255, 255)),
     block((0.4, 1.75, 1.5), (-2.4, 2.5, 0), (255, 140, 66)),
     block((2.0, 0.9, 0.4), (0, 4.0, 0), (255, 140, 66)),
     ] + eyes_x(2.0, 2.8, 0, spread=0.55) + mouth(2.35, 2.2, 0, w=0.15, h=0.5)))

NEW.append(("tiki_tony", "Tiki Tony", "Rare", 120, 1200,
    "He has seen things. Mostly tourists. He judges.",
    [block((3.5, 4.5, 3.0), (0, 2.5, 0), (139, 90, 43)),
     block((2.5, 2.0, 2.0), (0, 5.5, 0), (160, 110, 60)),
     block((0.6, 2.0, 0.6), (-1.2, 6.8, 0), (220, 60, 60)),
     block((0.6, 2.4, 0.6), (0, 7.0, 0), (255, 217, 61)),
     block((0.6, 2.0, 0.6), (1.2, 6.8, 0), (70, 130, 255)),
     block((0.9, 2.0, 0.9), (-2.2, 2.5, 0), (139, 90, 43)),
     block((0.9, 2.0, 0.9), (2.2, 2.5, 0), (139, 90, 43)),
     block((1.0, 0.9, 0.3), (-0.5, 5.8, 1.05), (255, 255, 255)),
     block((1.0, 0.9, 0.3), (0.5, 5.8, 1.05), (255, 255, 255)),
     block((0.45, 0.45, 0.15), (-0.5, 5.8, 1.25), (20, 20, 20)),
     block((0.45, 0.45, 0.15), (0.5, 5.8, 1.25), (20, 20, 20)),
     block((1.4, 0.5, 0.3), (0, 4.9, 1.05), (30, 30, 30)),
     ]))

NEW.append(("mermaid_marla", "Mermaid Marla", "Rare", 160, 1600,
    "Half mermaid, half accountant. The tail does the earning.",
    [block((2.0, 3.0, 2.0), (0, 1.5, 0), (0, 180, 180)),
     block((1.75, 0.8, 0.5), (-1.0, 0.6, 0), (0, 200, 200)),
     block((1.75, 0.8, 0.5), (1.0, 0.6, 0), (0, 200, 200)),
     ball((2.5, 2.5, 2.5), (0, 3.8, 0), (245, 200, 160)),
     ball((2.0, 2.0, 2.0), (0, 5.8, 0), (245, 200, 160)),
     ball((2.5, 1.25, 2.5), (0, 6.4, -0.5), (255, 120, 180)),
     ball((0.9, 0.9, 0.9), (0, 7.0, 0.3), (255, 215, 0)),
     block((0.7, 2.0, 0.7), (-1.6, 3.8, 0), (245, 200, 160)),
     block((0.7, 2.0, 0.7), (1.6, 3.8, 0), (245, 200, 160)),
     ] + eyes(0, 6.0, 0.95, spread=0.45) + mouth(0, 5.4, 1.0, w=0.55)))

# --- Epic: 4 new (total 6) ---
NEW.append(("lifeguard_larry", "Lifeguard Larry", "Epic", 200, 2000,
    "Certified in saving swimmers and bank accounts.",
    [block((0.9, 2.0, 0.9), (-0.6, 1.25, 0), (245, 200, 160)),
     block((0.9, 2.0, 0.9), (0.6, 1.25, 0), (245, 200, 160)),
     block((2.75, 2.5, 1.5), (0, 3.5, 0), (220, 38, 38)),
     block((2.75, 0.6, 1.55), (0, 4.4, 0), (255, 255, 255)),
     ball((2.0, 2.0, 2.0), (0, 5.5, 0), (245, 200, 160)),
     block((2.25, 0.6, 2.25), (0, 6.5, 0), (255, 255, 255)),
     block((2.0, 0.5, 0.3), (0, 5.9, 0.95), (20, 20, 20)),
     block((0.7, 2.0, 0.7), (-1.7, 3.5, 0), (245, 200, 160)),
     block((0.7, 2.0, 0.7), (1.7, 3.5, 0), (245, 200, 160)),
     ball((2.5, 2.5, 0.8), (2.6, 3.0, 0.5), (255, 255, 255)),
     ball((1.5, 1.5, 0.9), (2.6, 3.0, 0.5), (220, 38, 38)),
     ] + eyes(0, 5.6, 0.95, spread=0.45) + mouth(0, 5.0, 1.0, w=0.55)))

NEW.append(("octo_ollie", "Octo Ollie", "Epic", 260, 2600,
    "Eight arms, eight bank accounts, zero regrets.",
    [ball((4.0, 4.0, 4.0), (0, 4.5, 0), (139, 92, 246)),
     block((0.9, 2.5, 0.9), (-2.2, 1.25, 0.8), (120, 70, 220)),
     block((0.9, 2.5, 0.9), (2.2, 1.25, 0.8), (120, 70, 220)),
     block((0.9, 2.5, 0.9), (-1.3, 1.25, 1.6), (120, 70, 220)),
     block((0.9, 2.5, 0.9), (1.3, 1.25, 1.6), (120, 70, 220)),
     block((0.9, 2.5, 0.9), (-2.6, 1.25, -0.8), (120, 70, 220)),
     block((0.9, 2.5, 0.9), (2.6, 1.25, -0.8), (120, 70, 220)),
     ball((0.8, 0.8, 0.8), (0, 6.6, 0.6), (255, 217, 61)),
     ] + eyes(0, 5.2, 1.85, spread=0.7, wr=0.65, pr=0.32) + mouth(0, 4.3, 1.95, w=0.9, h=0.22)))

NEW.append(("sandcastle_sandy", "Sandcastle Sandy", "Epic", 340, 3400,
    "Built to last. Mortgaged to the tide. Still standing.",
    [block((4.5, 3.5, 4.5), (0, 2.0, 0), (245, 210, 140)),
     block((2.5, 2.0, 2.5), (0, 4.75, 0), (240, 195, 120)),
     block((0.25, 1.75, 0.25), (0, 6.5, 0), (139, 90, 43)),
     block((1.1, 0.7, 0.15), (0.55, 7.1, 0), (220, 38, 38)),
     block((1.25, 1.75, 0.3), (0, 1.0, 2.3), (90, 60, 30)),
     block((0.8, 0.8, 0.3), (-1.4, 3.0, 2.3), (70, 130, 255)),
     block((0.8, 0.8, 0.3), (1.4, 3.0, 2.3), (70, 130, 255)),
     ] + eyes(0, 4.9, 1.3, spread=0.5) + mouth(0, 4.3, 1.35, w=0.6)))

NEW.append(("wave_rider_wanda", "Wave Rider Wanda", "Epic", 420, 4200,
    "She does not ride the wave. The wave rides her schedule.",
    [ball((5.0, 1.5, 3.0), (0, 1.0, 0), (40, 120, 255)),
     ball((3.5, 1.0, 2.5), (-1.5, 1.9, 0), (255, 255, 255)),
     block((1.75, 0.35, 5.5), (0, 2.2, 0), (255, 217, 61)),
     block((0.8, 1.75, 0.8), (-0.55, 3.25, 0), (245, 200, 160)),
     block((0.8, 1.75, 0.8), (0.55, 3.25, 0), (245, 200, 160)),
     block((2.25, 2.0, 1.25), (0, 5.0, 0), (220, 38, 38)),
     ball((1.9, 1.9, 1.9), (0, 6.9, 0), (245, 200, 160)),
     block((2.4, 1.0, 2.4), (0, 7.5, -0.6), (60, 40, 20)),
     block((0.65, 1.75, 0.65), (-1.5, 5.0, 0), (245, 200, 160)),
     block((0.65, 1.75, 0.65), (1.5, 5.0, 0), (245, 200, 160)),
     ] + eyes(0, 7.1, 0.9, spread=0.42) + mouth(0, 6.55, 0.95, w=0.5)))

# --- Legendary: 4 new (total 6) ---
NEW.append(("captain_coral", "Captain Coral", "Legendary", 650, 6500,
    "Captain of the reef, terror of the tide pool.",
    [ball((4.25, 2.5, 3.25), (0, 1.8, 0), (255, 120, 120)),
     ball((1.75, 1.75, 1.75), (2.75, 2.0, 0.75), (255, 120, 120)),
     block((0.5, 2.5, 0.5), (-2.9, 2.25, 0.75), (200, 200, 210), "Metal"),
     ball((1.75, 1.75, 1.75), (-2.75, 2.0, 0.75), (255, 120, 120)),
     block((3.5, 0.4, 3.5), (0, 4.3, 0.3), (20, 20, 20)),
     block((2.25, 1.5, 2.25), (0, 5.2, 0.3), (20, 20, 20)),
     ball((0.8, 0.8, 0.8), (0, 5.4, 1.5), (255, 255, 255)),
     block((1.25, 2.0, 0.9), (0, 3.6, 1.2), (180, 30, 30)),
     ] + eyes(0, 4.0, 1.6, spread=0.5) + mouth(0, 3.3, 1.65, w=0.7)))

NEW.append(("pearl_pufferfish", "Pearl Pufferfish", "Legendary", 850, 8500,
    "Puffed up with pride and at least nine pearls.",
    [ball((5.0, 5.0, 5.0), (0, 3.0, 0), (250, 240, 230)),
     ball((0.6, 0.6, 0.6), (-1.8, 4.6, 1.8), (220, 60, 60)),
     ball((0.6, 0.6, 0.6), (1.8, 4.6, 1.8), (220, 60, 60)),
     ball((0.6, 0.6, 0.6), (0, 5.3, 1.2), (220, 60, 60)),
     ball((0.6, 0.6, 0.6), (-2.2, 2.6, 1.2), (70, 130, 255)),
     ball((0.6, 0.6, 0.6), (2.2, 2.6, 1.2), (70, 130, 255)),
     ball((1.25, 1.25, 1.25), (0, 3.2, 2.2), (255, 255, 255)),
     block((0.4, 1.5, 1.25), (-2.6, 3.0, 0), (250, 240, 230)),
     block((0.4, 1.5, 1.25), (2.6, 3.0, 0), (250, 240, 230)),
     ] + eyes(0, 3.6, 2.35, spread=0.7, wr=0.6, pr=0.3) + mouth(0, 2.8, 2.4, w=0.7)))

NEW.append(("tsunami_tiki", "Tsunami Tiki", "Legendary", 1100, 11000,
    "When he wakes up, the ocean files a complaint.",
    [block((4.0, 5.0, 3.0), (0, 2.5, 0), (90, 60, 30)),
     block((2.75, 2.25, 2.25), (0, 6.25, 0), (110, 75, 40)),
     ball((3.5, 1.75, 3.0), (0, 8.0, 0), (40, 120, 255)),
     ball((2.5, 1.0, 2.25), (0, 8.9, 0), (255, 255, 255)),
     block((0.9, 2.25, 0.9), (-2.4, 2.75, 0), (90, 60, 30)),
     block((0.9, 2.25, 0.9), (2.4, 2.75, 0), (90, 60, 30)),
     ball((1.5, 1.5, 1.5), (-2.4, 4.2, 0.6), (40, 120, 255)),
     ball((1.5, 1.5, 1.5), (2.4, 4.2, 0.6), (40, 120, 255)),
     block((1.1, 1.0, 0.3), (-0.55, 6.6, 1.2), (255, 255, 255)),
     block((1.1, 1.0, 0.3), (0.55, 6.6, 1.2), (255, 255, 255)),
     block((0.5, 0.5, 0.15), (-0.55, 6.6, 1.4), (20, 20, 20)),
     block((0.5, 0.5, 0.15), (0.55, 6.6, 1.4), (20, 20, 20)),
     block((1.5, 0.55, 0.3), (0, 5.6, 1.25), (30, 30, 30)),
     ]))

NEW.append(("neptune_nemo", "Neptune Nemo", "Legendary", 1400, 14000,
    "King of the reef. The trident is real. The attitude is too.",
    [ball((5.0, 3.0, 2.5), (0, 2.5, 0), (255, 200, 80)),
     block((0.5, 1.75, 1.5), (-2.6, 2.5, 0), (255, 200, 80)),
     block((2.25, 0.8, 0.8), (0, 4.3, 0), (255, 215, 0), "Metal"),
     block((0.5, 2.25, 0.5), (2.9, 3.5, 0), (139, 90, 43)),
     block((0.35, 1.0, 0.35), (2.55, 4.6, 0), (255, 215, 0), "Metal"),
     block((0.35, 1.0, 0.35), (3.25, 4.6, 0), (255, 215, 0), "Metal"),
     block((1.5, 1.0, 0.4), (0, 1.6, 1.2), (255, 255, 255)),
     ] + eyes_x(2.3, 2.9, 0, spread=0.6) + mouth(2.6, 2.2, 0, w=0.15, h=0.55)))

# --- Mythic: 3 new (total 5) ---
NEW.append(("kraken_karl", "Kraken Karl", "Mythic", 2800, 28000,
    "Eight tentacles, one mortgage, zero mercy.",
    [ball((5.0, 5.0, 5.0), (0, 5.0, 0), (90, 40, 140)),
     block((1.0, 2.75, 1.0), (-2.4, 1.4, 1.0), (70, 30, 110)),
     block((1.0, 2.75, 1.0), (2.4, 1.4, 1.0), (70, 30, 110)),
     block((1.0, 2.75, 1.0), (-1.4, 1.4, 1.9), (70, 30, 110)),
     block((1.0, 2.75, 1.0), (1.4, 1.4, 1.9), (70, 30, 110)),
     block((1.0, 2.75, 1.0), (-2.6, 1.4, -1.0), (70, 30, 110)),
     block((1.0, 2.75, 1.0), (2.6, 1.4, -1.0), (70, 30, 110)),
     ball((0.55, 0.55, 0.55), (-2.4, 2.4, 1.3), (255, 255, 255)),
     ball((0.55, 0.55, 0.55), (2.4, 2.4, 1.3), (255, 255, 255)),
     block((1.25, 0.9, 0.5), (0, 3.9, 2.3), (255, 255, 255)),
     ] + eyes(0, 5.6, 2.3, spread=0.75, wr=0.7, pr=0.35) + mouth(0, 4.5, 2.4, w=0.9, h=0.22)))

NEW.append(("atlantis_anchor", "Atlantis Anchor", "Mythic", 3600, 36000,
    "Dropped once in 1923. Still holding the whole bay down.",
    [block((1.5, 5.0, 1.5), (0, 2.5, 0), (0, 150, 150), "Metal"),
     block((4.5, 1.0, 1.0), (0, 4.5, 0), (0, 150, 150), "Metal"),
     block((1.5, 1.0, 1.0), (-1.75, 1.25, 0), (0, 150, 150), "Metal"),
     block((1.5, 1.0, 1.0), (1.75, 1.25, 0), (0, 150, 150), "Metal"),
     ball((1.25, 1.25, 1.25), (0, 5.75, 0), (255, 215, 0), "Metal"),
     ball((1.0, 1.0, 1.0), (-1.2, 5.4, 0.8), (255, 120, 180)),
     ball((1.0, 1.0, 1.0), (1.2, 5.4, 0.8), (255, 120, 180)),
     block((0.6, 1.75, 0.6), (-2.0, 1.0, 0.8), (34, 197, 94)),
     block((0.6, 1.75, 0.6), (2.0, 1.0, 0.8), (34, 197, 94)),
     ] + eyes(0, 4.9, 0.8, spread=0.7, wr=0.6, pr=0.3) + mouth(0, 4.2, 0.85, w=0.8)))

NEW.append(("poseidon_pelican", "Poseidon Pelican", "Mythic", 4500, 45000,
    "God of the sea, part-time fish delivery service.",
    [ball((4.5, 3.5, 4.0), (0, 2.5, 0), (255, 255, 255)),
     ball((2.25, 2.25, 2.25), (0, 5.25, 0.9), (255, 255, 255)),
     block((1.5, 0.9, 2.75), (0, 5.1, 2.4), (255, 140, 66)),
     block((0.6, 1.75, 1.5), (-2.3, 2.75, 0), (240, 240, 245)),
     block((0.6, 1.75, 1.5), (2.3, 2.75, 0), (240, 240, 245)),
     block((0.5, 2.5, 0.5), (2.9, 3.5, 0), (139, 90, 43)),
     ball((0.9, 0.9, 0.9), (2.9, 5.0, 0), (0, 255, 255), "Neon"),
     ball((0.9, 0.9, 0.9), (-1.0, 6.2, 0.9), (34, 197, 94)),
     ball((0.9, 0.9, 0.9), (1.0, 6.2, 0.9), (34, 197, 94)),
     ] + eyes(0, 5.6, 1.9, spread=0.5) + mouth(0, 4.9, 1.95, w=0.6)))

# --- Secret: 3 new (total 5) ---
NEW.append(("golden_sand_dragon", "Golden Sand Dragon", "Secret", 10000, 100000,
    "Forged from beach gold. Breathes compliments and fire.",
    [ball((4.5, 3.0, 5.0), (0, 2.5, 0), (255, 215, 0), "Metal"),
     ball((2.5, 2.5, 2.5), (0, 4.5, 2.25), (255, 215, 0), "Metal"),
     block((0.4, 2.75, 2.25), (-3.0, 3.5, 0), (255, 215, 0), "Metal"),
     block((0.4, 2.75, 2.25), (3.0, 3.5, 0), (255, 215, 0), "Metal"),
     block((0.6, 1.75, 0.6), (-0.7, 6.0, 2.25), (255, 215, 0), "Metal"),
     block((0.6, 1.75, 0.6), (0.7, 6.0, 2.25), (255, 215, 0), "Metal"),
     block((0.5, 1.5, 2.5), (0, 2.0, -3.0), (255, 215, 0), "Metal"),
     ball((0.9, 0.9, 0.9), (0, 5.6, 0.5), (255, 80, 80)),
     ] + eyes(0, 4.9, 3.4, spread=0.55, wr=0.6, pr=0.3) + mouth(0, 4.1, 3.45, w=0.7)))

NEW.append(("crystal_coral_king", "Crystal Coral King", "Secret", 13000, 130000,
    "Every branch is a different tax bracket.",
    [block((1.0, 4.5, 1.0), (-1.5, 2.25, 0), (255, 120, 180)),
     block((1.0, 5.5, 1.0), (0, 2.75, 0), (0, 220, 255)),
     block((1.0, 4.5, 1.0), (1.5, 2.25, 0), (255, 120, 180)),
     ball((2.5, 2.5, 2.5), (0, 6.0, 0), (255, 200, 220)),
     block((1.25, 1.75, 1.25), (0, 7.75, 0), (0, 220, 255), "Neon"),
     block((3.0, 2.0, 1.5), (0, 1.25, 0), (139, 92, 246)),
     ball((1.0, 1.0, 1.0), (0, 3.0, 1.4), (255, 215, 0), "Metal"),
     ] + eyes(0, 6.3, 1.2, spread=0.55) + mouth(0, 5.6, 1.25, w=0.65)))

NEW.append(("rainbow_reef_leviathan", "Rainbow Reef Leviathan", "Secret", 16000, 160000,
    "Too big for the bay. The bay adjusted.",
    [ball((4.5, 3.5, 3.5), (-2.5, 2.5, 0), (220, 60, 60)),
     ball((4.5, 3.5, 3.5), (0.5, 2.5, 0), (255, 200, 80)),
     ball((4.5, 3.5, 3.5), (3.5, 2.5, 0), (70, 130, 255)),
     ball((3.0, 3.0, 3.0), (5.5, 3.0, 0), (34, 197, 94)),
     block((0.6, 2.25, 2.0), (5.5, 5.0, 0), (255, 255, 255)),
     block((0.6, 2.25, 2.0), (6.3, 5.0, 0), (255, 255, 255)),
     block((0.5, 2.0, 1.75), (-4.9, 2.5, 0), (220, 60, 60)),
     ] + eyes_x(6.6, 3.4, 0, spread=0.65, wr=0.55, pr=0.28) + mouth(6.9, 2.6, 0, w=0.15, h=0.6)))

# --- Divine: 2 new (total 2) ---
NEW.append(("sun_god_surfer", "Sun God Surfer", "Divine", 25000, 250000,
    "The sun asked HIM for light. He said yes, for a fee.",
    [ball((4.0, 4.0, 4.0), (0, 3.0, 0), (255, 215, 0), "Neon"),
     block((0.5, 2.5, 0.5), (-2.9, 5.0, 0), (255, 180, 0), "Neon"),
     block((0.5, 2.5, 0.5), (2.9, 5.0, 0), (255, 180, 0), "Neon"),
     block((0.5, 2.5, 0.5), (0, 6.3, 0), (255, 180, 0), "Neon"),
     block((0.5, 2.5, 0.5), (-2.0, 5.9, 0), (255, 180, 0), "Neon"),
     block((0.5, 2.5, 0.5), (2.0, 5.9, 0), (255, 180, 0), "Neon"),
     ball((2.25, 2.25, 2.25), (0, 6.0, 0), (255, 200, 120)),
     block((2.0, 0.4, 5.5), (0, 0.6, 0), (255, 215, 0), "Metal"),
     ] + eyes(0, 6.3, 1.05, spread=0.5, wr=0.6, pr=0.3) + mouth(0, 5.6, 1.1, w=0.65)))

NEW.append(("ocean_oracle", "Ocean Oracle", "Divine", 40000, 400000,
    "She knows which brainrot you will buy tomorrow.",
    [block((4.0, 5.0, 3.0), (0, 2.5, 0), (20, 40, 120)),
     ball((2.25, 2.25, 2.25), (0, 6.0, 0), (245, 200, 160)),
     ball((2.75, 1.5, 2.75), (0, 6.9, -0.4), (20, 40, 120)),
     ball((1.75, 1.75, 1.75), (0, 3.5, 2.0), (0, 255, 255), "Neon"),
     block((0.5, 3.0, 0.5), (2.4, 3.5, 0), (139, 90, 43)),
     ball((0.9, 0.9, 0.9), (2.4, 5.25, 0), (0, 255, 255), "Neon"),
     block((1.5, 0.5, 1.5), (-1.5, 5.5, 1.6), (255, 215, 0), "Metal"),
     block((1.5, 0.5, 1.5), (1.5, 5.5, 1.6), (255, 215, 0), "Metal"),
     ] + eyes(0, 6.3, 1.05, spread=0.5, wr=0.6, pr=0.3) + mouth(0, 5.6, 1.1, w=0.65)))

assert len(NEW) == 24, "expected 24 new characters, got %d" % len(NEW)

# ------------------------------------------------------------------ formatting

def fmt_part(p):
    shape, size, off, color, mat = p
    r, g, b = color
    m = (", material = Enum.Material.%s" % mat) if mat else ""
    if shape == "Cylinder":
        raise ValueError("round 3 uses no Cylinders")
    sx, sy, sz = [f(v) for v in size]
    ox, oy, oz = [f(v) for v in off]
    return ('\t\t\t{ shape = "%s", size = Vector3.new(%s, %s, %s), '
            'offset = Vector3.new(%s, %s, %s), color = Color3.fromRGB(%d, %d, %d)%s },'
            % (shape, sx, sy, sz, ox, oy, oz, r, g, b, m))

def fmt_char(entry):
    cid, name, rarity, rate, cost, tagline, parts = entry
    lines = ['\t{ id = "%s", name = "%s", rarity = "%s", rate = %d, cost = %d, tagline = "%s",'
             % (cid, name, rarity, rate, cost, tagline),
             '\t\tparts = {']
    lines += [fmt_part(p) for p in parts]
    lines += ['\t\t},', '\t},']
    return "\n".join(lines)

# ------------------------------------------------------------------ patching
src = open(PATH).read()

OLD_RARITIES = '''BrainrotData.RARITIES = {
\tCommon = { color = Color3.fromRGB(34, 197, 94), weight = 40, order = 1 },
\tRare = { color = Color3.fromRGB(59, 130, 246), weight = 28, order = 2 },
\tEpic = { color = Color3.fromRGB(139, 92, 246), weight = 16, order = 3 },
\tLegendary = { color = Color3.fromRGB(245, 158, 11), weight = 9, order = 4 },
\tMythic = { color = Color3.fromRGB(239, 68, 68), weight = 5, order = 5 },
\tSecret = { color = Color3.fromRGB(236, 72, 153), weight = 2, order = 6 },
}'''
NEW_RARITIES = '''BrainrotData.RARITIES = {
\tCommon = { color = Color3.fromRGB(34, 197, 94), weight = 38, order = 1 },
\tRare = { color = Color3.fromRGB(59, 130, 246), weight = 26, order = 2 },
\tEpic = { color = Color3.fromRGB(139, 92, 246), weight = 15, order = 3 },
\tLegendary = { color = Color3.fromRGB(245, 158, 11), weight = 9, order = 4 },
\tMythic = { color = Color3.fromRGB(239, 68, 68), weight = 6, order = 5 },
\tSecret = { color = Color3.fromRGB(236, 72, 153), weight = 4, order = 6 },
\tDivine = { color = Color3.fromRGB(255, 255, 255), weight = 2, order = 7 },
}'''
assert OLD_RARITIES in src, "RARITIES block not found"
src = src.replace(OLD_RARITIES, NEW_RARITIES)

OLD_MUT = '''BrainrotData.MUTATIONS = {
\t{ name = "None", mult = 1, weight = 75, color = nil },
\t{ name = "Golden", mult = 2, weight = 15, color = Color3.fromRGB(255, 215, 0) },
\t{ name = "Diamond", mult = 4, weight = 7, color = Color3.fromRGB(100, 220, 255) },
\t{ name = "Rainbow", mult = 8, weight = 3, color = Color3.fromRGB(255, 80, 200) },
}'''
NEW_MUT = '''BrainrotData.MUTATIONS = {
\t{ name = "None", mult = 1, weight = 70, color = nil },
\t{ name = "Golden", mult = 2, weight = 14, color = Color3.fromRGB(255, 215, 0) },
\t{ name = "Neon", mult = 3, weight = 3, color = Color3.fromRGB(0, 255, 255) },
\t{ name = "Diamond", mult = 4, weight = 7, color = Color3.fromRGB(100, 220, 255) },
\t{ name = "Rainbow", mult = 8, weight = 4, color = Color3.fromRGB(255, 80, 200) },
\t{ name = "Cosmic", mult = 10, weight = 2, color = Color3.fromRGB(168, 85, 247) },
}'''
assert OLD_MUT in src, "MUTATIONS block not found"
src = src.replace(OLD_MUT, NEW_MUT)

OLD_ARR = '''for _, r in ipairs({
\t{ name = "Common", weight = 40 },
\t{ name = "Rare", weight = 28 },
\t{ name = "Epic", weight = 16 },
\t{ name = "Legendary", weight = 9 },
\t{ name = "Mythic", weight = 5 },
\t{ name = "Secret", weight = 2 },
}) do table.insert(BrainrotData.RARITIES_ARRAY, r) end'''
NEW_ARR = '''for _, r in ipairs({
\t{ name = "Common", weight = 38 },
\t{ name = "Rare", weight = 26 },
\t{ name = "Epic", weight = 15 },
\t{ name = "Legendary", weight = 9 },
\t{ name = "Mythic", weight = 6 },
\t{ name = "Secret", weight = 4 },
\t{ name = "Divine", weight = 2 },
}) do table.insert(BrainrotData.RARITIES_ARRAY, r) end'''
assert OLD_ARR in src, "RARITIES_ARRAY block not found"
src = src.replace(OLD_ARR, NEW_ARR)

# Insert the 24 new entries at the end of the CHARACTERS table.
anchor = "\n}\n\nBrainrotData.BY_ID"
assert anchor in src, "CHARACTERS table end not found"
new_text = "\n" + "\n".join(fmt_char(e) for e in NEW) + anchor
src = src.replace(anchor, new_text, 1)

open(PATH, "w").write(src)
print("gen_cast36: added %d characters, 7 rarities, 6 mutations -> %s" % (len(NEW), PATH))
