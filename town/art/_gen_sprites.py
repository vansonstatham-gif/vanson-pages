# -*- coding: utf-8 -*-
"""Generate 6 chibi pixel residents as 4-direction walk spritesheets.
Design at 32x32, then nearest upscale x2 -> 64x64 per frame.
Sheets: 4 rows (DOWN, LEFT, UP, RIGHT) x 3 walk frames.
All art is original procedural pixel art (no external assets)."""
import os
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), 'sprites')
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- palette
# Color helpers (RGB). Each resident defined with distinct hair/clothes/accessory.
# Unified: same skin base, same shadow color, same outline (dark slate).

OUTLINE = (40, 40, 52)
def skin(tone=0):
    skins = [(233, 196, 168), (235, 188, 150), (224, 172, 132), (203, 153, 120)]
    return skins[tone % len(skins)]
def shade(c, f=0.72):
    return tuple(int(x * f) for x in c)
def light(c, f=1.25):
    return tuple(min(255, int(x * f)) for x in c)

# ---------------------------------------------------------------- design configs
# Each resident: dict of options
RESIDENTS = {
    'Rei': dict(
        cn='Rei',
        hair='short',      # neat bob
        hair_c=(108, 116, 130),      # grey-ash
        shirt=(190, 204, 224),       # pale blue
        vest=(120, 140, 168),        # darker blazer
        pants=(90, 100, 120),
        shoes=(70, 76, 92),
        accent=(255, 255, 255),      # collar
        skin_t=0,
        accessory='none',
    ),
    'Fitness': dict(
        cn='健身教练',
        hair='sports',     # short spiky
        hair_c=(70, 62, 54),         # dark brown
        shirt=(20, 205, 175),        # teal tank
        vest=None,
        pants=(245, 158, 11),        # orange shorts
        shoes=(255, 255, 255),
        accent=(255, 120, 40),
        skin_t=1,
        accessory='none',
    ),
    'Finance': dict(
        cn='财经顾问',
        hair='neat',       # neat side
        hair_c=(40, 42, 48),         # black
        shirt=(60, 74, 100),         # navy suit
        vest=(47, 58, 82),
        pants=(44, 52, 66),
        shoes=(30, 34, 42),
        accent=(227, 93, 93),        # red tie
        skin_t=0,
        accessory='glasses',
    ),
    'Entertainment': dict(
        cn='娱乐助手',
        hair='fluffy',     # fluff / dyed pink
        hair_c=(255, 96, 175),       # pink
        shirt=(165, 94, 234),        # purple jacket
        vest=None,
        pants=(70, 50, 120),
        shoes=(255, 210, 90),
        accent=(255, 210, 90),
        skin_t=0,
        accessory='none',
    ),
    'Ops': dict(
        cn='运维',
        hair='blunt',      # blunt under hood
        hair_c=(66, 58, 50),         # brown
        shirt=(90, 122, 90),         # green hoodie
        vest=(72, 98, 72),
        pants=(58, 64, 72),
        shoes=(56, 48, 44),
        accent=(210, 214, 222),      # hood rim
        skin_t=1,
        accessory='glasses',
    ),
    'Wilde': dict(
        cn='骚客',
        hair='wild',       # messy + beret
        hair_c=(58, 48, 44),         # dark hair
        shirt=(122, 90, 58),         # long brown coat
        vest=None,
        pants=(64, 62, 70),
        shoes=(58, 50, 44),
        accent=(201, 68, 62),        # red scarf
        skin_t=0,
        accessory='beret',
    ),
}

# ---------------------------------------------------------------- drawing primitives
def blank():
    return [[None for _ in range(32)] for _ in range(32)]

def px(g, x, y, c):
    if 0 <= y < 32 and 0 <= x < 32 and c is not None:
        g[y][x] = c

def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(g, x, y, c)

def blit_glyph(g, glyph, ox, oy, c=None):
    """glyph: list of strings, each char -> sample; map any non-space, or map a
    char palette if c is a dict {char: color}."""
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == ' ':
                continue
            col = c
            if isinstance(c, dict):
                if ch not in c or c[ch] is None:
                    continue
                col = c[ch]
            px(g, ox + i, oy + j, col)

# ---------------------------------------------------------------- character drawing
def draw_character(g, cfg, pose):
    """pose: 0=idle, 1=left-step, 2=right-step. Draws base 32x32 chibi."""
    hair_c = cfg['hair_c']; shirt = cfg['shirt']
    vest = cfg.get('vest'); pants = cfg['pants']
    shoes = cfg['shoes']; accent = cfg['accent']
    sk = skin(cfg['skin_t'])
    sk_d = shade(sk); sk_h = light(sk)
    hair_d = shade(hair_c); hair_h = light(hair_c)
    shirt_d = shade(shirt); vest_d = shade(vest) if vest else None
    shd = (150, 140, 120)  # generic ground shadow (blended later behind)

    # ---- feet offset based on pose (3/4 top-down, slight bob)
    bob = [0, 2, 1][pose]

    # ===== HEAD =====
    # face (rows 4..12), rounded top corners for cuteness
    rect(g, 7, 4 + bob, 22, 12 + bob, sk)
    rect(g, 8, 3 + bob, 21, 12 + bob, sk)
    px(g, 9, 2 + bob, sk); px(g, 20, 2 + bob, sk)
    px(g, 7, 5 + bob, sk_d); px(g, 22, 5 + bob, sk_d)
    px(g, 7, 11 + bob, sk_d); px(g, 22, 11 + bob, sk_d)

    # hair =========
    H = cfg['hair']
    if H == 'short':  # neat bob (Rei)
        rect(g, 6, 3 + bob, 23, 5 + bob, hair_c)          # top
        rect(g, 6, 3 + bob, 6, 8 + bob, hair_c)           # left side
        rect(g, 23, 3 + bob, 23, 8 + bob, hair_c)         # right side
        rect(g, 7, 6 + bob, 11, 7 + bob, hair_h)          # fringe
        px(g, 6, 9 + bob, hair_c); px(g, 23, 9 + bob, hair_c)
    elif H == 'sports':  # short spiky (Fitness)
        rect(g, 7, 3 + bob, 22, 4 + bob, hair_c)
        px(g, 6, 4 + bob, hair_c); rect(g, 6, 4 + bob, 7, 4 + bob, hair_c)
        px(g, 23, 4 + bob, hair_c); px(g, 23, 6 + bob, hair_c)
        px(g, 9, 2 + bob, hair_c); px(g, 14, 2 + bob, hair_c); px(g, 19, 2 + bob, hair_c)
        rect(g, 8, 5 + bob, 21, 5 + bob, hair_c)
    elif H == 'neat':  # neat side-part (Finance)
        rect(g, 6, 3 + bob, 23, 4 + bob, hair_c)
        rect(g, 6, 3 + bob, 6, 9 + bob, hair_c)
        rect(g, 23, 3 + bob, 23, 9 + bob, hair_c)
        rect(g, 7, 5 + bob, 13, 6 + bob, hair_h)          # side fringe
    elif H == 'fluffy':  # puffy (Entertainment)
        rect(g, 5, 2 + bob, 24, 3 + bob, hair_c)
        px(g, 7, 4 + bob, hair_c); px(g, 22, 4 + bob, hair_c)
        px(g, 8, 2 + bob, hair_c); px(g, 20, 2 + bob, hair_c)
    elif H == 'blunt':  # blunt under hood (Ops) - little hair visible
        rect(g, 7, 4 + bob, 22, 5 + bob, hair_c)
        rect(g, 7, 4 + bob, 7, 6 + bob, hair_c)
        rect(g, 22, 4 + bob, 22, 6 + bob, hair_c)
    elif H == 'wild':  # messy + beret (Wilde)
        px(g, 6, 5 + bob, hair_c); px(g, 8, 3 + bob, hair_c)
        px(g, 13, 2 + bob, hair_c); px(g, 17, 3 + bob, hair_c)
        rect(g, 6, 4 + bob, 22, 6 + bob, hair_c)          # fringe
        rect(g, 21, 4 + bob, 23, 9 + bob, hair_c)         # side hair
        rect(g, 5, 4 + bob, 6, 9 + bob, hair_c)

    # eyes/face (2 px, dark)
    ey = 9 + bob
    if cfg.get('accessory') == 'glasses':
        px(g, 10, ey, OUTLINE); px(g, 11, ey, OUTLINE)
        px(g, 19, ey, OUTLINE); px(g, 20, ey, OUTLINE)
        rect(g, 9, ey - 1, 12, ey + 1, OUTLINE); rect(g, 18, ey - 1, 21, ey + 1, OUTLINE)
        px(g, 12, ey - 1, OUTLINE); px(g, 17, ey - 1, OUTLINE)  # bridge
    else:
        px(g, 11, ey, (40, 40, 46)); px(g, 19, ey, (40, 40, 46))
    px(g, 15, ey + 2, (206, 128, 110))  # mouth

    # hair front extra
    if H == 'beret' or cfg.get('accessory') == 'beret':
        rect(g, 10, 0 + bob, 22, 1 + bob, accent)         # beret top
        rect(g, 9, 1 + bob, 23, 2 + bob, accent)
        px(g, 10, 1 + bob, shade(accent)); px(g, 22, 1 + bob, shade(accent))

    # ===== BODY / TORSO =====
    bt = 12 + bob  # body top
    # shoulders: widen slightly for a rounded A-line chibi
    rect(g, 7, bt, 24, bt + 3, shirt)
    rect(g, 8, bt + 3, 23, bt + 3, shirt)
    px(g, 7, bt, shirt_d); px(g, 24, bt, shirt_d)
    px(g, 8, bt, shirt_d if cfg.get('vest') else shirt)
    px(g, 23, bt, shirt_d if cfg.get('vest') else shirt)
    # torso
    rect(g, 9, bt + 1, 22, bt + 8, shirt)
    # collar / accents
    if cfg.get('vest'):
        rect(g, 10, bt + 1, 21, bt + 1, accent)          # collar/chest line
        rect(g, 8, bt + 2, 23, bt + 2, vest)
        rect(g, 9, bt + 3, 22, bt + 8, vest)
        px(g, 8, bt + 2, vest_d); px(g, 23, bt + 2, vest_d)
        rect(g, 10, bt, 13, bt, vest); rect(g, 18, bt, 21, bt, vest)  # lapels
    else:
        rect(g, 12, bt, 19, bt + 1, accent)              # chest trim
        rect(g, 10, bt, 21, bt, shirt_d if not cfg.get('vest') else shirt)
    # arms (split sides)
    rect(g, 7, bt + 2, 7, bt + 7, shirt_d)
    rect(g, 24, bt + 2, 24, bt + 7, shirt_d)
    # Wilde's red scarf reads from the non-vest accent chest band below

    # ===== PANTS / LEGS (A-line, slightly flared = cute) =====
    lp = bt + 8
    lp2 = lp
    if cfg.get('vest'):
        lp = bt + 8
    rect(g, 9, lp, 22, lp + 9, pants)
    rect(g, 10, lp + 1, 21, lp + 8, pants)
    px(g, 9, lp, shade(pants)); px(g, 22, lp, shade(pants))
    # leg seam / two legs
    rect(g, 15, lp, 16, lp + 9, shade(pants, 0.8))

    # ===== FEET (pose-dependent walk) =====
    fy = lp + 9
    if pose == 0:  # idle: feet together
        rect(g, 11, fy, 15, fy + 1, shoes)
        rect(g, 17, fy, 21, fy + 1, shoes)
        px(g, 11, fy, shade(shoes)); px(g, 17, fy, shade(shoes))
    elif pose == 1:  # left-foot forward
        rect(g, 10, fy, 18, fy + 1, shoes)               # left forward
        rect(g, 18, fy + 1, 22, fy + 1, shoes)           # right back
        px(g, 11, fy, shade(shoes)); px(g, 12, fy, shade(shoes))
        px(g, 18, fy + 1, shade(shoes))
    else:  # right-foot forward
        rect(g, 14, fy, 22, fy + 1, shoes)               # right forward
        rect(g, 10, fy + 1, 14, fy + 1, shoes)           # left back
        px(g, 21, fy, shade(shoes)); px(g, 20, fy, shade(shoes))
        px(g, 10, fy + 1, shade(shoes))

    # ===== ARMS for side poses (extra life) =====
    # nose/profile handled by flip for left/right rows below.

# ---------------------------------------------------------------- sheet building
def make_sheet(cfg):
    frames = 3
    rows = 4  # DOWN, LEFT, UP, RIGHT
    cell = 32
    sheet = Image.new('RGBA', (cell * frames, cell * rows), (0, 0, 0, 0))
    import copy
    for row in range(rows):
        for f in range(frames):
            g = blank()
            draw_character(g, cfg, f)
            # flip for LEFT (row1) and RIGHT(row3); UP needs mirrored pose
            if row == 1:      # LEFT: flip horizontal
                g = flip_h(g)
            elif row == 3:    # RIGHT: flip horizontal
                g = flip_h(g)
            # UP (row2): back view - just keep, but tint head/hair darker is fine
            frame_img = grid_to_image(g, cell)
            sheet.paste(frame_img, (f * cell, row * cell))
    # nearest upscale x2 -> 64x64 cells
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    return sheet

def flip_h(g):
    return [list(reversed(row)) for row in g]

def grid_to_image(g, cell):
    img = Image.new('RGBA', (cell, cell), (0, 0, 0, 0))
    for y in range(cell):
        for x in range(cell):
            c = g[y][x]
            if c:
                img.putpixel((x, y), c + (255,))
    return img

# ---------------------------------------------------------------- generate all
manifest = {}
for name, cfg in RESIDENTS.items():
    sheet = make_sheet(cfg)
    fname = f'{name}_walk.png'
    sheet.save(os.path.join(OUT, fname))
    manifest[name] = fname
    print('saved', fname, sheet.size)

print('DONE')
