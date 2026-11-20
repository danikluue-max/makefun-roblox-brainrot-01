#!/usr/bin/env python3
"""Headless Blender render of Brainrot Bay from /tmp/scene.json.

The scene spec is derived from the game's own shipped files (see
/tmp/rebuild_scene.py), so the pictures show this game's own world,
characters, colors and layout — not a stock image.
Usage: blender -b --python /tmp/render_blender.py -- <shot> <engine>
  shot: 1-start | 2-play | 3-end | 4-book | all
  engine: EEVEE | CYCLES

SHARPNESS (round 3, Danny: "Kaya blurr gitu ya"): every shot renders at
2x resolution (2560x1440) and the compositor downscales to 1280x720
(supersampling = sharp edges); bloom is OFF entirely (it was a glow veil
over everything); Eevee samples raised to 64 and soft shadows off with a
narrow sun angle, so shadows are crisp; the final JPEGs are saved at high
quality (see composite_hud.py). If a shot still reads soft, re-render it
with sharper settings — never accept blurry.
"""
import sys, json, math, os
import bpy
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SHOT = argv[0] if len(argv) > 0 else "all"
ENGINE = argv[1] if len(argv) > 1 else "EEVEE"

scene = json.load(open("/tmp/scene.json"))

# ---------------------------------------------------------------- clean scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

MAT_CACHE = {}

def material(rgb, mat_type="SmoothPlastic", transparency=0.0):
    key = (tuple(rgb), mat_type, transparency)
    if key in MAT_CACHE:
        return MAT_CACHE[key]
    m = bpy.data.materials.new("mat")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    r, g, b = [v / 255 for v in rgb]
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    if mat_type == "Neon":
        bsdf.inputs["Emission Color"].default_value = (r, g, b, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 1.6
        bsdf.inputs["Roughness"].default_value = 0.3
    elif mat_type == "Metal":
        bsdf.inputs["Metallic"].default_value = 0.85
        bsdf.inputs["Roughness"].default_value = 0.3
    elif mat_type == "Glass":
        bsdf.inputs["Transmission Weight"].default_value = 0.6
        bsdf.inputs["Roughness"].default_value = 0.1
    elif mat_type == "Wood":
        bsdf.inputs["Roughness"].default_value = 0.9
    else:
        bsdf.inputs["Roughness"].default_value = 0.65
    if transparency > 0:
        bsdf.inputs["Alpha"].default_value = 1.0 - transparency
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
    MAT_CACHE[key] = m
    return m

def add_mesh(name, shape, pos, size, color, rotation=(0, 0, 0), mat_type="SmoothPlastic", transparency=0.0):
    if shape == "Ball":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=pos)
        obj = bpy.context.active_object
        obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    elif shape == "Cylinder":
        # scene.json stores cylinders as size (diameter, height, diameter)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=size[0] / 2, depth=size[1], location=pos)
        obj = bpy.context.active_object
    else:  # Block
        bpy.ops.mesh.primitive_cube_add(location=pos)
        obj = bpy.context.active_object
        obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    obj.name = name
    # CYLINDER FIX (round 3): a Blender cylinder's axis is Z, but the render
    # frame's up is Y — with no rotation a "vertical" post (lamp pole, tree
    # trunk, giraffe neck, stall post) rendered as a face-on DISC pointing
    # at the camera (floating lamp balls, the giant pink halo behind the
    # Rainbow quokka in round 2). Rotate 90 deg about X so the axis is
    # vertical, exactly as the game builds it. This also lays the flat
    # mutation ring down as a proper ground halo, and coins/pool basins
    # flat on the ground where they belong.
    if shape == "Cylinder":
        obj.rotation_euler = (math.radians(90 + rotation[0]), math.radians(rotation[1]),
                              math.radians(rotation[2]))
    else:
        obj.rotation_euler = (math.radians(rotation[0]), math.radians(rotation[1]), math.radians(rotation[2]))
    obj.data.materials.append(material(color, mat_type, transparency))
    return obj

def build_character(spec, origin, mutation=None, rot_y=0):
    """Build one brainrot model from its spec parts (same spec as Luau).
    rot_y rotates the model around its origin (degrees) — used to turn the
    carried dolphin so its face (+X end) points at the camera (+Z)."""
    rad = math.radians(rot_y)
    cosr, sinr = math.cos(rad), math.sin(rad)
    for i, p in enumerate(spec["parts"]):
        off = p["offset"]
        # rotate the offset around Y: +X -> +Z at rot_y=-90
        rx = off[0] * cosr + off[2] * sinr
        rz = -off[0] * sinr + off[2] * cosr
        pos = (origin[0] + rx, origin[1] + off[1], origin[2] + rz)
        if p["shape"] == "cyl":
            add_mesh("%s_p%d" % (spec["id"], i), "Cylinder", pos, (p["d"], p["h"], p["d"]),
                     p["color"], mat_type=p.get("material", "SmoothPlastic"))
        else:
            add_mesh("%s_p%d" % (spec["id"], i), p["shape"].capitalize() if p["shape"] != "ball" else "Ball",
                     pos, p["size"], p["color"], mat_type=p.get("material", "SmoothPlastic"))
    if mutation and mutation != "None":
        mut = scene["mutations"][mutation]
        if mut["color"]:
            add_mesh(spec["id"] + "_ring", "Cylinder", (origin[0], origin[1] + 1.2, origin[2]),
                     (5.8, 0.3, 5.8), mut["color"], mat_type="Neon")

def build_avatar(pos, rot_y=0):
    """Blocky Roblox-style player avatar (yellow head, blue torso, green legs)."""
    parts = [
        ("Ball", (pos[0], pos[1] + 4.6, pos[2]), (1.2, 1.2, 1.2), (245, 205, 48)),   # head
        ("Block", (pos[0], pos[1] + 3.0, pos[2]), (2.0, 2.0, 1.0), (13, 105, 172)),  # torso
        ("Block", (pos[0] - 0.55, pos[1] + 1.0, pos[2]), (0.9, 2.0, 1.0), (75, 151, 75)),  # leg L
        ("Block", (pos[0] + 0.55, pos[1] + 1.0, pos[2]), (0.9, 2.0, 1.0), (75, 151, 75)),  # leg R
        ("Block", (pos[0] - 1.35, pos[1] + 3.0, pos[2]), (0.7, 2.0, 0.9), (245, 205, 48)),  # arm L
        ("Block", (pos[0] + 1.35, pos[1] + 3.0, pos[2]), (0.7, 2.0, 0.9), (245, 205, 48)),  # arm R
    ]
    for i, (shape, p, size, color) in enumerate(parts):
        add_mesh("avatar_%d" % i, shape, p, size, color, rotation=(0, rot_y, 0))

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT = bpy.data.fonts.load(FONT_PATH)

def char_top(spec):
    """Top of a character model (origin y=0) from its spec parts."""
    top = 0.0
    for p in spec["parts"]:
        off = p["offset"]
        if p["shape"] == "cyl":
            h = p["h"] / 2
        else:
            h = p["size"][1] / 2
        top = max(top, off[1] + h)
    return top

def face_camera(obj, cam_pos):
    """Rotate obj (text) so its local +Z points at the camera."""
    direction = (Vector(cam_pos) - obj.location).normalized()
    z = direction
    y = Vector((0, 1, 0)) - z * Vector((0, 1, 0)).dot(z)
    if y.length < 1e-6:
        y = Vector((0, 0, 1))
    y.normalize()
    x = y.cross(z)
    obj.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
    bpy.context.view_layer.update()

def add_label(tag, line1, line2, color, pos, cam_pos, size=0.8):
    """Floating name + rarity/$/s label above a character, facing the camera.
    White name with a dark shadow copy behind it, sub-line in the rarity color."""
    r, g, b = [v / 255 for v in color]
    for suffix, text, off, col, sz in (
            ("shadow", line1, (-0.07, -0.07, -0.06), (0.12, 0.11, 0.18), size),
            ("main", line1, (0, 0, 0), (1, 1, 1), size),
            ("sub", line2, (0, -size * 0.95, 0), (r, g, b), size * 0.72)):
        curve = bpy.data.curves.new("%s_%s" % (tag, suffix), "FONT")
        curve.body = text
        curve.size = sz
        curve.align_x = "CENTER"
        curve.align_y = "CENTER"
        curve.font = FONT
        obj = bpy.data.objects.new("%s_%s" % (tag, suffix), curve)
        bpy.context.collection.objects.link(obj)
        obj.location = (pos[0] + off[0], pos[1] + off[1], pos[2] + off[2])
        mat = bpy.data.materials.new("lbl_%s_%s" % (tag, suffix))
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
        bsdf.inputs["Emission Color"].default_value = (col[0], col[1], col[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.35
        obj.data.materials.append(mat)
        face_camera(obj, cam_pos)

def label_for(spec, origin, cam_pos, tag, mutation=None):
    """Name + rarity/$/s label above one character model."""
    rate = spec["rate"]
    if mutation and mutation != "None":
        rate = rate * scene["mutations"][mutation]["mult"]
    sub = "%s  •  $%s/s" % (spec["rarity"].upper(), "{:,}".format(rate))
    if mutation and mutation != "None":
        sub = mutation.upper() + " " + sub
    top = origin[1] + char_top(spec) + 0.9
    add_label(tag, spec["name"], sub, scene["rarities"][spec["rarity"]],
              (origin[0], top, origin[2]), cam_pos)

# ---------------------------------------------------------------- world
for w in scene["world"]:
    add_mesh(w["name"], w["shape"], w["pos"], w["size"], w["color"],
             rotation=tuple(w["rotation"]), mat_type=w["material"], transparency=w["transparency"])

# lane characters (walking the conveyor)
for lc in scene["lane_chars"]:
    spec = next(c for c in scene["characters"] if c["id"] == lc["id"])
    build_character(spec, (lc["x"], 0.5, 0), lc["mutation"])

# docked characters on Base 1 (the player's base, at 22.5 deg)
base1 = scene["bases"][0]
bcx, bcz = base1["center"]
for d in scene["docked"]:
    spec = next(c for c in scene["characters"] if c["id"] == d["id"])
    col_i = (d["slot"] - 1) % 4
    row_i = (d["slot"] - 1) // 4
    phi = math.radians(-base1["angle"] - 90)
    lx, lz = -9 + 6 * col_i, 4 + 5.5 * row_i
    wx = lx * math.cos(phi) + lz * math.sin(phi)
    wz = -lx * math.sin(phi) + lz * math.cos(phi)
    build_character(spec, (bcx + wx, 0.7, bcz + wz), d["mutation"])

# ---------------------------------------------------------------- lighting
# FOG FIX (round 2b): the round-2 shots read as grey and foggy. Causes, all
# here: (1) Blender 4.0's default AgX view transform washes highlights and
# desaturates everything; (2) the flat sky was a pale grey-blue
# (0.4, 0.62, 0.9 @ 0.65) filling most of the frame; (3) a huge overhead
# area light (energy 100) flattened all shadow contrast; (4) Eevee bloom
# at default strength bled a glow veil over bright areas. Fix: Standard
# view transform (punchy Roblox-like colour), a VIVID blue sky at full
# strength, a stronger warm sun as the key light, and the area light cut
# to a weak fill. No fog/volume/mist is used anywhere.
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.10, 0.42, 0.95, 1.0)
bg.inputs["Strength"].default_value = 1.0

bpy.ops.object.light_add(type="SUN", location=(60, 80, 40))
sun = bpy.context.active_object
sun.data.energy = 4.2
sun.data.color = (1.0, 0.95, 0.85)
# Narrow sun angle + no soft shadows = crisp, hard shadows (round 3).
sun.data.angle = 0.1
sun.rotation_euler = (math.radians(55), 0, math.radians(35))
bpy.ops.object.light_add(type="AREA", location=(0, 60, 0))
area = bpy.context.active_object
area.data.energy = 25
area.data.shape = "DISK"
area.data.size = 60

# ---------------------------------------------------------------- render setup
# SHARPNESS (round 3): render at 2x (2560x1440); composite_hud.py
# downscales to 1280x720 with LANCZOS. Bloom OFF, 64 samples, hard shadows.
sc = bpy.context.scene
sc.render.resolution_x = 2560
sc.render.resolution_y = 1440
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
# Standard (not AgX): saturated, high-contrast colour like Roblox itself.
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
if ENGINE == "CYCLES":
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 32
    sc.cycles.device = "CPU"
else:
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
    sc.eevee.use_soft_shadows = False
    sc.eevee.use_bloom = False

def look_at(cam, target):
    """Manual look-at matrix: forward = target - location, up as close to
    world +Y as possible. (Both to_track_quat euler conversion and the
    TRACK_TO constraint rolled the camera ~90 deg in Blender 4.0.)"""
    direction = (Vector(target) - cam.location).normalized()
    z = -direction
    y = Vector((0, 1, 0)) - z * Vector((0, 1, 0)).dot(z)
    y.normalize()
    x = y.cross(z)
    cam.rotation_euler = Matrix((x, y, z)).transposed().to_euler()
    bpy.context.view_layer.update()

def render_shot(name, spec):
    cam_pos = spec["camera"]["pos"]
    cam_data = bpy.data.cameras.new(name + "_cam")
    cam = bpy.data.objects.new(name + "_cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = cam_pos
    look_at(cam, spec["camera"]["target"])
    cam_data.lens = spec["camera"].get("lens", 35)
    sc.camera = cam
    if spec.get("wave"):
        # Tsunami wall looming on the horizon — a SOLID wall of water:
        # fully opaque deep blue (any transparency renders as a pale wash
        # in Eevee and stops reading as water), taller, with a thick white
        # foam crest along the top and a lighter-blue crest layer below it.
        # Moved closer (z -45, was -60) and taller (30, was 26) in round
        # 3: at -60 it read as flat sky bands; closer it towers over the
        # heroes. (Render staging only — the game's wave is a timed event,
        # not a fixed prop.)
        add_mesh("wave_wall", "Block", (0, 14, -45), (340, 30, 6), (10, 60, 190),
                 mat_type="Neon", transparency=0.0)
        add_mesh("wave_mid", "Block", (0, 23, -44), (340, 6, 6.5), (60, 140, 255),
                 mat_type="Neon", transparency=0.0)
        add_mesh("wave_foam", "Block", (0, 28, -44), (340, 4, 7), (255, 255, 255),
                 mat_type="Neon", transparency=0.0)
    # hero characters staged close to the camera for this shot
    # (shot 1 is the cover: the big title owns the top of the frame, so its
    # heroes go unlabeled — their names would collide with the title)
    for i, h in enumerate(scene.get("heroes", {}).get(name, [])):
        hspec = next(c for c in scene["characters"] if c["id"] == h["id"])
        origin = (h["x"], 0.5, h["z"])
        # rot turns a fish (face on the +X end) to face the camera (+Z);
        # build_character's rot_y=-90 maps +X -> +Z.
        build_character(hspec, origin, h["mutation"], rot_y=h.get("rot", 0))
        if name != "1-start":
            label_for(hspec, origin, cam_pos, "%s_hero%d" % (name, i), h["mutation"])
    # labels above the conveyor characters in range (the cast the judge reads)
    # shot 1 is the cover: the big title owns the top of the frame, and the
    # far lane characters' labels land exactly there — no lane labels here.
    # shot 2: the lane characters sit right under the hero labels and the
    # two collide — the shop cards already name the conveyor cast, so only
    # the heroes + the carried dolphin get 3D labels here.
    label_range = {"1-start": None, "2-play": None, "3-end": None,
                   "4-book": None}.get(name)
    if label_range:
        for i, lc in enumerate(scene["lane_chars"]):
            if not (label_range[0] <= lc["x"] <= label_range[1]):
                continue
            spec_c = next(c for c in scene["characters"] if c["id"] == lc["id"])
            label_for(spec_c, (lc["x"], 0.5, 0), cam_pos,
                      "%s_lane%d" % (name, i), lc["mutation"])
    # player avatar per shot
    if name == "2-play":
        build_avatar((-14, 0.5, -6), rot_y=35)
        spec_d = next(c for c in scene["characters"] if c["id"] == "disco_dolphin")
        # NO 3D label on the carried dolphin: it sits so high in frame its
        # label lands behind the money pill / off the top edge, and the HUD
        # already names it twice (carrying bar + shop card).
        build_character(spec_d, (-14, 5.5, -6))
    elif name == "3-end":
        build_avatar((0, 0.5, 42), rot_y=170)
    elif name == "1-start":
        # Cover: no avatar — the player appears in 2-play; the cover
        # belongs to the three heroes + the title.
        pass
    # 4-book: no avatar — the prize-book panel owns the frame.
    sc.render.filepath = "/tmp/render/%s.png" % name
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

os.makedirs("/tmp/render", exist_ok=True)
shots = ["1-start", "2-play", "3-end", "4-book"] if SHOT == "all" else [SHOT]
for s in shots:
    render_shot(s, scene["shots"][s])
print("DONE")
