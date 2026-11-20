#!/usr/bin/env python3
"""Composite the in-game HUD over the Blender renders and save JPEGs
(1280x720, each <= 256 KiB) into the round dir screenshots/.

The HUD drawn here is the SAME layout the client script builds in Roblox
(money pill top-centre, shop bar bottom-centre, wave banner, carry pill,
quests panel, action bar, prize book), so the pictures show the game as
it plays.

SHARPNESS (round 3, Danny: "Kaya blurr gitu ya"): the Blender renders are
2560x1440 and are DOWNSCALED here to 1280x720 with LANCZOS
(supersampling = sharp edges); bloom is off in the render, and the JPEGs
are saved at high quality (95 first, stepping down only if a shot is over
256 KiB). HUD text is drawn AFTER the downscale, so it stays vector-crisp.

Layout: every element has its own draw function below (money pill, title
screen, carry pill, shop bar + cards, wave banner, quests panel, action
bar, prize book); `composite` just picks which ones a shot needs, in the
same back-to-front order the client draws them. Coordinates are in the
1280x720 render frame.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROUND = os.path.expanduser("~/workspace/makefun/entries/roblox-brainrot-01-r1")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAX_BYTES = 262144

PURPLE = (124, 97, 212)
PEACH = (234, 174, 135)
GREEN = (22, 163, 74)
ORANGE = (217, 119, 6)
RED = (220, 38, 38)
DARK = (30, 27, 45)
WHITE = (255, 255, 255)
INK = (47, 40, 29)
GREY = (60, 55, 85)
MUTED = (180, 175, 200)

RARITY = {
    "Common": (34, 197, 94), "Rare": (59, 130, 246), "Epic": (139, 92, 246),
    "Legendary": (245, 158, 11), "Mythic": (239, 68, 68), "Secret": (236, 72, 153),
    "Divine": (255, 255, 255),
}
RARITY_ORDER = ["Common", "Rare", "Epic", "Legendary", "Mythic", "Secret", "Divine"]

# ---------------------------------------------------------------- primitives

def font(size):
    return ImageFont.truetype(FONT, size)

def text_center(draw, cx, y, s, f, fill, stroke=None, sw=0):
    """Draw text centred on cx at height y; return its pixel width."""
    bbox = draw.textbbox((0, 0), s, font=f)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), s, font=f, fill=fill,
              stroke_width=sw, stroke_fill=stroke)
    return w

def pill(draw, box, fill, outline=None, width=0, radius=16):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

# ---------------------------------------------------------------- HUD pieces

def draw_money_pill(draw, money, income):
    """Purple pill, top centre: the balance in big type, income under it."""
    pill(draw, [510, 14, 770, 78], PURPLE, outline=PEACH, width=3)
    text_center(draw, 640, 20, money, font(34), WHITE, stroke=INK, sw=1)
    text_center(draw, 640, 54, income, font(19), PEACH)

def draw_title_screen(draw, hud):
    """Start shot: big title, tagline, ladder strip, and the hint bar."""
    text_center(draw, 640, 160, hud["title"], font(72), WHITE, stroke=PURPLE, sw=4)
    text_center(draw, 640, 252, hud["subtitle"], font(26), WHITE, stroke=INK, sw=2)
    if "ladder" in hud:
        text_center(draw, 640, 296, hud["ladder"], font(22), PEACH, stroke=INK, sw=2)
    pill(draw, [300, 630, 980, 684], DARK + (225,), radius=16)
    text_center(draw, 640, 642, hud["hint"], font(22), WHITE)

def draw_carry_pill(draw, text):
    """Green pill above the shop bar: what the player is carrying."""
    pill(draw, [380, 520, 900, 568], GREEN, radius=14)
    text_center(draw, 640, 530, text, font(19), WHITE)

def draw_shop_card(draw, x, card):
    """One conveyor card: rarity colour, name, $/s rate, price."""
    col = RARITY[card["rarity"]]
    draw.rounded_rectangle([x, 626, x + 132, 690], radius=10, fill=col)
    draw.text((x + 6, 630), card["name"], font=font(13), fill=WHITE)
    draw.text((x + 6, 650), card["rate"], font=font(13), fill=WHITE)
    draw.text((x + 6, 668), card["cost"], font=font(14), fill=WHITE)

def draw_shop_bar(draw, hud):
    """Bottom-centre bar: heading plus one card per brainrot on the lane."""
    pill(draw, [360, 596, 920, 696], DARK + (225,), radius=16)
    text_center(draw, 640, 600, "CONVEYOR — TAP A CARD TO BUY", font(17), PEACH)
    for i, card in enumerate(hud["shop"]):
        draw_shop_card(draw, 368 + i * 140, card)

def draw_wave_banner(draw, hud):
    """End shot: red warning banner and the countdown pill under it."""
    pill(draw, [360, 92, 920, 148], RED, radius=14)
    text_center(draw, 640, 104, hud["wave"], font(20), WHITE)
    pill(draw, [560, 156, 720, 196], DARK + (225,), radius=12)
    text_center(draw, 640, 164, hud["wave_timer"], font(20), WHITE)

def draw_quests_panel(draw, hud):
    """Left side: the three quests with progress and a CLAIM button."""
    pill(draw, [16, 110, 316, 292], DARK + (225,), radius=16)
    draw.text((24, 116), "QUESTS", font=font(18), fill=PEACH)
    for i, q in enumerate(hud["quests"]):
        y = 146 + i * 48
        draw.text((24, y), q["name"], font=font(16), fill=WHITE)
        draw.text((24, y + 22), "%d/%d  •  %s" % (q["progress"], q["target"], q["reward"]),
                  font=font(14), fill=PEACH)
        claimable = q["progress"] >= q["target"] and not q.get("claimed")
        claimed = q.get("claimed")
        col = GREEN if claimable else GREY
        label = "DONE" if claimed else "CLAIM"
        draw.rounded_rectangle([230, y + 4, 308, y + 40], radius=10, fill=col)
        text_center(draw, 269, y + 12, label, font(15), WHITE)

def draw_action_bar(draw, hud):
    """Bottom right: LOCK / REBIRTH / PRIZE BOOK buttons."""
    x0, y0 = 1006, 640
    buttons = [
        ("LOCK", "$500", GREEN),
        ("REBIRTH", "$50K", ORANGE),
        ("BOOK", hud.get("book_count", "34/36"), PURPLE),
    ]
    for i, (top, bottom, col) in enumerate(buttons):
        x = x0 + i * 88
        draw.rounded_rectangle([x, y0, x + 82, y0 + 56], radius=14, fill=col)
        text_center(draw, x + 41, y0 + 6, top, font(15), WHITE)
        text_center(draw, x + 41, y0 + 28, bottom, font(15), WHITE)

def draw_prize_book(draw, scene, hud):
    """The prize-book modal: a 6x6 grid of all 36 characters, rarity
    order then $/s, found cells in rarity colour, the two not-found cells
    (the Divine pair) grey with question marks — exactly the grid the
    client builds from BrainrotData."""
    chars = sorted(scene["characters"],
                   key=lambda c: (RARITY_ORDER.index(c["rarity"]), c["rate"]))
    found_n = hud.get("found", 34)
    found = set(c["id"] for c in chars[:found_n])
    # panel
    pill(draw, [90, 96, 1190, 684], DARK + (235,), radius=18)
    draw.text((106, 106), "PRIZE BOOK", font=font(34), fill=PEACH)
    draw.text((380, 116), "%d/%d FOUND" % (found_n, len(chars)), font=font(22), fill=WHITE)
    draw.rounded_rectangle([1130, 106, 1170, 146], radius=12, fill=RED)
    text_center(draw, 1150, 112, "X", font(22), WHITE)
    for i, c in enumerate(chars):
        col, row = i % 6, i // 6
        x = 106 + col * 178
        y = 158 + row * 84
        if c["id"] in found:
            fill = RARITY[c["rarity"]]
            name, rate = c["name"], "$%s/s" % "{:,}".format(c["rate"])
            name_col, rate_col = WHITE, WHITE
        else:
            fill = GREY
            name, rate = "???", "NOT FOUND"
            name_col, rate_col = MUTED, MUTED
        draw.rounded_rectangle([x, y, x + 170, y + 76], radius=10, fill=fill)
        # Long names wrap to two lines (the client does the same with
        # TextWrapped); short names stay on one line.
        w = draw.textbbox((0, 0), name, font=font(15))[2]
        if w > 154:
            half = len(name) // 2
            cut = name.rfind(" ", 0, half + 4)
            if cut < 0:
                cut = name.find(" ", half)
            line1, line2 = name[:cut], name[cut + 1:]
            draw.text((x + 8, y + 6), line1, font=font(13), fill=name_col)
            draw.text((x + 8, y + 24), line2, font=font(13), fill=name_col)
            draw.text((x + 8, y + 44), rate, font=font(14), fill=rate_col)
            draw.text((x + 8, y + 60), c["rarity"].upper(), font=font(12), fill=rate_col)
        else:
            draw.text((x + 8, y + 8), name, font=font(15), fill=name_col)
            draw.text((x + 8, y + 32), rate, font=font(14), fill=rate_col)
            draw.text((x + 8, y + 52), c["rarity"].upper(), font=font(12), fill=rate_col)

# ---------------------------------------------------------------- composite

def composite(shot, hud, scene):
    """Load the Blender render for `shot` (2560x1440), downscale to
    1280x720 with LANCZOS, draw its HUD, return the image."""
    img = Image.open("/tmp/render/%s.png" % shot).convert("RGB")
    img = img.resize((1280, 720), Image.LANCZOS)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_money_pill(draw, hud.get("money", "$100"), hud.get("income", "+$0/s"))
    if shot == "1-start":
        draw_title_screen(draw, hud)
    elif shot == "2-play":
        if "carry" in hud:
            draw_carry_pill(draw, hud["carry"])
        draw_shop_bar(draw, hud)
        if "quests" in hud:
            draw_quests_panel(draw, hud)
        draw_action_bar(draw, hud)
    elif shot == "3-end":
        draw_wave_banner(draw, hud)
    elif shot == "4-book":
        draw_prize_book(draw, scene, hud)
    return img

def save_shot(img, shot):
    """Save one shot as JPEG at high quality, stepping down only until it
    fits under 256 KiB (95 first — minimal compression blur)."""
    out = os.path.join(ROUND, "screenshots", shot + ".jpg")
    for q in (95, 92, 88, 80, 72, 65):
        img.save(out, "JPEG", quality=q)
        size = os.path.getsize(out)
        if size <= MAX_BYTES:
            print(shot, "->", out, size, "bytes, quality", q)
            return
    print(shot, "STILL TOO BIG:", size)

def main():
    scene = json.load(open("/tmp/scene.json"))
    os.makedirs(os.path.join(ROUND, "screenshots"), exist_ok=True)
    for shot in ("1-start", "2-play", "3-end", "4-book"):
        img = composite(shot, scene["shots"][shot]["hud"], scene)
        save_shot(img, shot)
        # remove the old starter pngs if present
        old = os.path.join(ROUND, "screenshots", shot + ".png")
        if os.path.exists(old):
            os.remove(old)
    print("screenshot files:", sorted(os.listdir(os.path.join(ROUND, "screenshots"))))

if __name__ == "__main__":
    main()
