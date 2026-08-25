# -*- coding: utf-8 -*-
"""Generate 6 resident "paper-doll" multi-layer spritesheets.

Design directly at 64x64 native resolution (no 32->64 upscale) so each
character silhouette reads crisper and more detailed than the chibi pass.

Each resident outputs 4 transparent layering sheets into sprites/parts/:
  * <Name>_hair.png   -- hair + head + face + accessory (beret / glasses)
  * <Name>_top.png    -- torso + arms + shirt / jacket / vest layer
  * <Name>_bottom.png -- pants / legs layer
  * <Name>_shoes.png  -- shoes / feet layer

All four layers share exactly the same 64x64 grid so stacking them aligns
into one complete resident (transparent cells let lower layers show).

Per sheet: 4 direction rows x 3 walk frames, row order [down, left, up, right].
Rows for left / right are produced by horizontally flipping the down pose.

Body layout on the grid (rows):
  06..26  head zone (drawn in hair layer; face rows ~11..30)
  30..45  torso (top layer)
  45..56  legs  (bottom layer)
  57..60  shoes (shoes layer)

The torso (top) layer partially overlaps the neck/face bottom and the legs;
because each sheet is its own layer, the overlap is intended and stacks cleanly.

All art is original procedural pixel art (layering concept only, no external
assets copied).
"""
import os
from PIL import Image

OUT_DIR = os.path.join(os.path.dirname(__file__), 'sprites', 'parts')
os.makedirs(OUT_DIR, exist_ok=True)

FRAME = 64
DIRS = ['down', 'left', 'up', 'right']
FRAMES_PER_DIR = 3
SHEET_W = FRAME * FRAMES_PER_DIR     # 192
SHEET_H = FRAME * len(DIRS)          # 256

# ---------------------------------------------------------------- palette helpers
OUTLINE = (36, 34, 44)
OUTLINE_D = (24, 22, 30)
EYE = (34, 34, 42)

def skin_c(tone=0):
    return [(233, 196, 168), (235, 188, 150), (224, 172, 132), (203, 153, 120)][tone % 4]

def shade(c, f=0.70):
    return tuple(max(0, int(x * f)) for x in c)
def shade2(c, f=0.52):
    return tuple(max(0, int(x * f)) for x in c)
def light(c, f=1.26):
    return tuple(min(255, int(x * f)) for x in c)
def blend(c, d, t=0.35):
    return tuple(int(a * (1 - t) + b * t) for a, b in zip(c, d))


# ---------------------------------------------------------------- resident configs
RESIDENTS = {
    'Rei': dict(
        cn='Rei', hair='bob', hair_c=(108, 116, 130),
        shirt=(190, 204, 224), vest=(120, 140, 168),
        pants=(90, 100, 120), shoes=(70, 76, 92),
        accent=(255, 255, 255), skin_t=0,
        accessory='none', shoe_style='loafer',
    ),
    'Fitness': dict(
        cn='健身教练', hair='spiky', hair_c=(70, 62, 54),
        shirt=(20, 205, 175), vest=None,
        pants=(245, 158, 11), shoes=(255, 255, 255),
        accent=(255, 120, 40), skin_t=1,
        accessory='none', shoe_style='sneaker',
    ),
    'Finance': dict(
        cn='财经顾问', hair='side', hair_c=(40, 42, 48),
        shirt=(60, 74, 100), vest=(47, 58, 82),
        pants=(44, 52, 66), shoes=(30, 34, 42),
        accent=(227, 93, 93), skin_t=0,
        accessory='glasses', shoe_style='oxford',
    ),
    'Entertainment': dict(
        cn='娱乐助手', hair='fluffy', hair_c=(255, 96, 175),
        shirt=(165, 94, 234), vest=None,
        pants=(70, 50, 120), shoes=(255, 210, 90),
        accent=(255, 210, 90), skin_t=0,
        accessory='none', shoe_style='boot',
    ),
    'Ops': dict(
        cn='运维', hair='hooded', hair_c=(66, 58, 50),
        shirt=(90, 122, 90), vest=None,
        pants=(58, 64, 72), shoes=(56, 48, 44),
        accent=(210, 214, 222), skin_t=1,
        accessory='glasses', shoe_style='boot',
    ),
    'Wilde': dict(
        cn='骚客', hair='wild', hair_c=(58, 48, 44),
        shirt=(122, 90, 58), vest=None,
        pants=(64, 62, 70), shoes=(58, 50, 44),
        accent=(201, 68, 62), skin_t=0,
        accessory='beret', shoe_style='oxford',
    ),
}

# ---------------------------------------------------------------- grid api
class Grid:
    def __init__(self):
        self.g = [[None for _ in range(FRAME)] for _ in range(FRAME)]

    def px(self, x, y, c):
        if 0 <= x < FRAME and 0 <= y < FRAME and c is not None:
            self.g[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def set_rows(self, rows):
        self.g = [list(r) for r in rows]

    def flip_h(self):
        return Grid.with_rows([list(reversed(r)) for r in self.g])

    @classmethod
    def with_rows(cls, rows):
        g = cls(); g.set_rows(rows); return g

    def to_image(self):
        img = Image.new('RGBA', (FRAME, FRAME), (0, 0, 0, 0))
        pxd = img.load()
        for y in range(FRAME):
            row = self.g[y]
            for x in range(FRAME):
                c = row[x]
                if c is not None:
                    pxd[x, y] = (c[0], c[1], c[2], 255)
        return img


# ---------------------------------------------------------------- fixed body rows
# Constant rows (no bob) so all 4 layers align perfectly every frame.
# Walk animation = only the leg/foot swing changes below the fixed torso.
BT = 30               # torso top row
LT = BT + 15          # hip/leg top row (=45)
SHOE_TOP = 56         # shoe upper row


# =====================================================================
# LAYER 1: HEAD (hair + face + accessory)
# =====================================================================
def draw_head_layer(cfg):
    g = Grid()
    sk = skin_c(cfg['skin_t'])
    sk_s = shade(sk)
    sk_h = light(sk, 1.18)
    sk_d2 = shade2(sk)
    hair = cfg['hair_c']
    hair_s = shade(hair)
    hair_h = light(hair, 1.22)
    hair_d2 = shade2(hair)
    acc = cfg['accessory']
    accent = cfg['accent']

    fx = 32                       # horizontal center of face
    facY0 = 12                    # face top row
    facY1 = 30                    # face bottom row
    face_x0, face_x1 = 18, 46

    # ---- face base
    g.rect(face_x0, facY0, face_x1, facY1, sk)
    g.px(face_x0 + 1, facY0 - 1, sk); g.px(face_x1 - 1, facY0 - 1, sk)   # top corners
    g.rect(face_x0, facY1, face_x1, facY1, sk_s)                          # jaw shade
    g.px(face_x0 - 1, facY0 + 1, sk_s); g.px(face_x1 + 1, facY0 + 1, sk_s)
    g.rect(face_x0 + 2, facY0 + 3, face_x0 + 5, facY0 + 6, sk_h)          # cheek hi
    g.rect(face_x1 - 5, facY0 + 3, face_x1 - 2, facY0 + 6, sk_h)

    H = cfg['hair']

    if H == 'bob':                 # Rei: neat grey-ash bob
        top = facY0 - 5
        g.rect(face_x0 - 2, top, face_x1 + 2, facY0 - 1, hair)            # crown
        g.rect(face_x0 - 4, top + 1, face_x0 - 2, facY0 + 4, hair)        # left side
        g.rect(face_x1 + 2, top + 1, face_x1 + 4, facY0 + 4, hair)        # right side
        g.rect(face_x0 - 4, facY0 + 4, face_x0 - 3, facY0 + 10, hair)     # longer locks
        g.rect(face_x1 + 3, facY0 + 4, face_x1 + 4, facY0 + 10, hair)
        g.rect(face_x0 - 4, facY0 + 10, face_x0 - 3, facY0 + 11, OUTLINE)
        g.rect(face_x1 + 3, facY0 + 10, face_x1 + 4, facY0 + 11, OUTLINE)
        for i in range(-6, 7):                                             # parted fringe
            g.px(fx + i, facY0 - 2, hair_h if (i + 14) % 4 == 0 else hair)
        g.px(fx - 2, facY0 - 1, hair_s)
        g.rect(face_x0 - 2, top, face_x1 + 2, top, hair_s)                 # top shade
        g.rect(face_x0 - 2, top - 1, face_x1 + 2, top - 1, OUTLINE)

    elif H == 'spiky':             # Fitness: dark short buzz with spikes
        top = facY0 - 4
        g.rect(fx - 12, top, fx + 12, facY0, hair)
        for cx in (fx - 11, fx - 6, fx - 1, fx + 4, fx + 9):
            g.px(cx, top - 1, hair)
            g.px(cx, top - 2, hair_h)
        g.px(fx - 11, top - 3, hair); g.px(fx + 5, top - 1, hair)
        g.rect(fx - 12, top - 1, fx + 12, top - 1, OUTLINE)
        g.rect(fx - 13, top + 1, fx - 13, top + 3, hair_s)
        g.rect(fx + 13, top + 1, fx + 13, top + 3, hair_s)
        g.px(fx - 13, top + 4, OUTLINE); g.px(fx + 13, top + 4, OUTLINE)

    elif H == 'side':              # Finance: neat black side-part
        top = facY0 - 5
        g.rect(fx - 14, top, fx + 14, facY0 - 1, hair)
        g.rect(fx - 16, top + 1, fx - 14, facY0 + 6, hair)      # left sweep
        g.rect(fx + 13, top + 1, fx + 15, facY0 + 5, hair)      # right sweep
        g.rect(fx - 16, facY0 + 6, fx - 15, facY0 + 9, OUTLINE)
        g.rect(fx + 14, facY0 + 5, fx + 15, facY0 + 8, OUTLINE)
        g.px(fx - 2, top, OUTLINE); g.px(fx - 1, top, OUTLINE)  # part line
        for i in range(-6, 4):
            g.px(fx + i, facY0 - 2, hair_h if i % 3 == 0 else hair)
        g.rect(fx - 14, top, fx + 14, top, OUTLINE)

    elif H == 'fluffy':            # Entertainment: big fluffy pink pouf
        top = facY0 - 6
        g.rect(fx - 15, top, fx + 15, facY0, hair)
        g.rect(fx - 17, top + 1, fx + 17, facY0 - 1, hair)
        for cx in (fx - 16, fx + 16, fx - 13, fx + 13, fx, fx - 6, fx + 6):
            g.px(cx, top - 1, hair)
            if cx in (fx - 16, fx + 16):
                g.px(cx, top - 2, hair)
        g.rect(fx - 17, facY0 + 6, fx - 17, facY0 + 8, hair)     # wide over jaw
        g.rect(fx + 17, facY0 + 6, fx + 17, facY0 + 8, hair)
        g.rect(fx - 17, facY0 + 8, fx - 16, facY0 + 9, OUTLINE)
        g.rect(fx + 16, facY0 + 8, fx + 17, facY0 + 9, OUTLINE)
        g.rect(fx - 16, top, fx + 16, top, OUTLINE)
        for cx in (fx - 8, fx, fx + 8):
            g.px(cx, top + 1, hair_h)
            g.px(cx + (1 if cx < fx else -1), top + 2, hair_h)
        g.px(fx - 4, top + 2, hair_h)

    elif H == 'hooded':            # Ops: brown hair under green hood (mostly hidden)
        top = facY0 - 4
        g.rect(fx - 13, top, fx + 13, facY0 - 1, hair)
        g.rect(fx + 12, top + 1, fx + 14, facY0, hair)
        g.rect(fx - 14, top + 1, fx - 12, facY0, hair)
        g.rect(fx - 12, facY0 - 1, fx + 12, facY0 - 1, hair_s)

    elif H == 'wild':              # Wilde: messy dark + beret
        top = facY0 - 6
        g.rect(fx - 14, top, fx + 14, facY0, hair)
        g.rect(fx - 16, top + 2, fx - 14, facY0 + 4, hair)
        g.rect(fx + 14, top + 2, fx + 16, facY0 + 4, hair)
        g.rect(fx - 16, facY0 + 4, fx - 15, facY0 + 7, OUTLINE)
        g.rect(fx + 15, facY0 + 4, fx + 16, facY0 + 7, OUTLINE)
        for cx in (fx - 9, fx - 4, fx + 1, fx + 6, fx + 10):
            g.px(cx, top - 1, hair_h if (cx + 12) % 3 == 0 else hair)
        g.rect(fx - 14, top, fx + 14, top - 1, OUTLINE)

    # ---- face features
    fy = facY0 + 8                # eye row
    if acc == 'glasses':
        g.rect(fx - 5, fy, fx - 2, fy + 1, EYE)
        g.rect(fx + 2, fy, fx + 5, fy + 1, EYE)
        g.rect(fx - 6, fy - 2, fx - 2, fy + 2, OUTLINE)
        g.rect(fx + 2, fy - 2, fx + 6, fy + 2, OUTLINE)
        g.rect(fx - 2, fy, fx + 2, fy, OUTLINE)
        g.px(fx - 7, fy + 1, OUTLINE); g.px(fx + 7, fy + 1, OUTLINE)
    else:
        g.rect(fx - 4, fy, fx - 2, fy, EYE)
        g.rect(fx + 2, fy, fx + 4, fy, EYE)
        g.px(fx - 4, fy + 1, EYE); g.px(fx + 4, fy + 1, EYE)
        g.px(fx - 5, fy - 1, hair_d2); g.px(fx + 5, fy - 1, hair_d2)
    g.px(fx - 1, fy + 3, sk_d2); g.px(fx, fy + 3, sk_d2); g.px(fx + 1, fy + 3, sk_d2)
    g.rect(fx - 3, fy + 6, fx + 3, fy + 6, (206, 128, 110))
    g.px(fx - 3, fy + 7, sk_s); g.px(fx + 3, fy + 7, sk_s)

    # ---- beret accessory
    if acc == 'beret':
        ber_y = top - 3
        g.rect(fx - 9, ber_y, fx + 9, top - 1, accent)
        g.rect(fx - 11, ber_y + 1, fx + 11, top - 1, accent)
        g.rect(fx - 11, ber_y + 1, fx + 11, ber_y + 1, shade(accent))
        g.px(fx, ber_y, shade(accent))
        g.px(fx + 8, top - 2, OUTLINE)
        g.rect(fx - 11, ber_y + 3, fx - 10, top - 1, shade2(accent))
        g.rect(fx + 10, ber_y + 3, fx + 11, top - 1, shade2(accent))

    return g


# =====================================================================
# LAYER 2: TOP (torso + arms + shirt/jacket/vest + hood/scarf)
# =====================================================================
def draw_top_layer(cfg):
    g = Grid()
    sk = skin_c(cfg['skin_t'])
    sk_s = shade(sk)
    shirt = cfg['shirt']
    shirt_s = shade(shirt)
    shirt_d2 = shade2(shirt)
    shirt_h = light(shirt, 1.18)
    vest = cfg.get('vest')
    accent = cfg['accent']
    H = cfg['hair']

    bt = BT
    tx0, tx1 = 17, 46              # torso columns (30 wide)
    # neck
    g.rect(27, bt - 3, 36, bt - 1, sk_s)
    # torso block
    g.rect(tx0, bt, tx1, bt + 15, shirt)
    g.rect(tx0 - 2, bt + 1, tx0 - 1, bt + 7, shirt)     # left arm
    g.rect(tx1 + 1, bt + 1, tx1 + 2, bt + 7, shirt)     # right arm
    g.px(tx0, bt, shirt_h); g.px(tx1, bt, shirt_h)

    # center + side creases (fabric)
    g.rect(tx0 + 2, bt + 3, tx0 + 2, bt + 12, shirt_d2)
    g.rect(tx1 - 2, bt + 3, tx1 - 2, bt + 12, shirt_d2)
    g.rect(31, bt + 6, 32, bt + 6, shirt_s)             # waist fold
    g.rect(31, bt + 11, 32, bt + 11, shirt_s)

    if H == 'spiky':               # Fitness: athletic tank
        g.rect(tx0 + 1, bt + 1, tx1 - 1, bt + 13, shirt)
        g.rect(tx0 + 1, bt + 1, tx1 - 1, bt + 1, shade(shirt, 0.9))   # rib neck
        # tank neckline (skin V)
        g.px(30, bt + 1, sk); g.px(31, bt + 1, sk); g.px(32, bt + 1, sk); g.px(33, bt + 1, sk)
        g.px(30, bt + 2, sk); g.px(32, bt + 2, sk)
        g.px(31, bt + 3, sk)
        # center accent stripe
        g.rect(31, bt + 2, 32, bt + 12, accent)
        g.px(31, bt + 2, shade2(accent)); g.px(32, bt + 2, shade2(accent))
        g.px(31, bt + 12, shade2(accent)); g.px(32, bt + 12, shade2(accent))
        # shoulder contrast panels
        g.rect(tx0 + 1, bt + 1, tx0 + 5, bt + 3, shirt_d2)
        g.rect(tx1 - 5, bt + 1, tx1 - 1, bt + 3, shirt_d2)
        # arm tone highlight
        g.px(tx0 - 2, bt + 3, shade2(shirt)); g.px(tx1 + 2, bt + 3, shade2(shirt))

    elif vest is not None:         # suits / jackets
        # shirt collar folding over
        g.rect(28, bt - 1, 35, bt, shirt_h)
        g.px(28, bt - 1, shirt_s)
        # lapels
        g.rect(tx0 + 1, bt + 2, tx0 + 5, bt + 4, shirt_h)
        g.rect(tx1 - 5, bt + 2, tx1 - 1, bt + 4, shirt_h)
        g.rect(tx0 + 1, bt + 5, tx0 + 4, bt + 6, shirt_s)
        g.rect(tx1 - 4, bt + 5, tx1 - 1, bt + 6, shirt_s)
        # vest panel
        g.rect(tx0 + 5, bt + 3, tx1 - 5, bt + 15, vest)
        g.rect(tx0 + 5, bt + 3, tx1 - 5, bt + 3, shade(vest))
        g.px(tx0 + 5, bt + 13, shade(vest)); g.px(tx1 - 5, bt + 13, shade(vest))
        g.rect(30, bt + 15, 33, bt + 15, shirt_s)        # vest hem over shirt

        if H == 'side':            # Finance: red tie + buttons
            g.rect(30, bt + 2, 34, bt + 13, accent)
            g.px(30, bt + 2, shade2(accent)); g.px(34, bt + 2, shade2(accent))
            g.rect(30, bt + 5, 34, bt + 5, shade2(accent))   # tie knot shadow
            g.px(31, bt + 3, shade(accent)); g.px(33, bt + 3, shade(accent))
            g.rect(31, bt + 13, 33, bt + 15, accent)
            g.px(31, bt + 7, shade(accent)); g.px(31, bt + 10, shade(accent))
            # button
            g.px(31, bt + 5, (190, 185, 140)); g.px(31, bt + 8, (190, 185, 140))
        elif H == 'bob':           # Rei: peter-pan white collar + blazer buttons
            g.rect(29, bt + 1, 34, bt + 2, accent)
            g.px(28, bt + 1, accent); g.px(35, bt + 1, accent)
            g.px(29, bt + 3, accent); g.px(34, bt + 3, accent)
            g.px(31, bt + 4, (190, 185, 140))
            g.px(31, bt + 7, (190, 185, 140))
            g.px(31, bt + 10, (190, 185, 140))
        # inner jacket lining hint at the open front
        g.rect(29, bt + 1, 29, bt + 4, shade2(shirt))
        g.rect(34, bt + 1, 34, bt + 4, shade2(shirt))

    elif H == 'fluffy':            # Entertainment: purple jacket, open front
        g.rect(tx0, bt, tx1, bt + 15, shirt)
        g.rect(29, bt + 1, 34, bt + 15, shade2(shirt))          # open lining
        g.rect(30, bt + 2, 33, bt + 14, shade(shirt, 0.5))      # darker inner
        # lapels
        g.rect(tx0 + 1, bt + 2, tx0 + 4, bt + 5, shirt_h)
        g.rect(tx1 - 4, bt + 2, tx1 - 1, bt + 5, shirt_h)
        # belt + buckle
        g.rect(tx0 + 1, bt + 12, tx1 - 1, bt + 13, accent)
        g.px(29, bt + 12, shade2(accent)); g.px(34, bt + 12, shade2(accent))
        g.px(31, bt + 12, shade2(accent)); g.px(31, bt + 13, shade2(accent))
        g.px(32, bt + 12, shade2(accent)); g.px(32, bt + 13, shade2(accent))
        # pocket flaps
        g.rect(tx0 + 3, bt + 9, tx0 + 7, bt + 9, shade2(shirt))
        g.rect(tx1 - 7, bt + 9, tx1 - 3, bt + 9, shade2(shirt))
        # shoulder puff
        g.rect(tx0 - 2, bt + 1, tx0 - 2, bt + 2, shirt_h)
        g.rect(tx1 + 2, bt + 1, tx1 + 2, bt + 2, shirt_h)

    elif H == 'hooded':            # Ops: green hoodie
        hood = shade(shirt, 0.82)
        g.rect(tx0, bt, tx1, bt + 15, shirt)
        g.px(tx0, bt, shirt_s); g.px(tx1, bt, shirt_s)
        # hood rising behind neck (dark green)
        g.rect(20, bt - 7, 43, bt - 3, hood)
        g.rect(19, bt - 4, 20, bt - 1, shade(hood, 0.72))
        g.rect(43, bt - 4, 44, bt - 1, shade(hood, 0.72))
        g.rect(20, bt - 7, 43, bt - 7, shade2(hood))          # hood crown shade
        g.rect(21, bt - 6, 42, bt - 4, shade2(hood))          # hood opening (void)
        # kangaroo pouch
        g.rect(tx0 + 6, bt + 9, tx1 - 6, bt + 14, shade2(shirt))
        g.rect(tx0 + 6, bt + 9, tx1 - 6, bt + 9, shade(shirt, 0.9))
        # drawstrings
        for cx in (29, 34):
            g.px(cx, bt + 1, accent); g.px(cx, bt + 2, accent)
            g.px(cx, bt + 3, accent); g.px(cx, bt + 4, accent)
            g.px(cx, bt + 5, accent)
        g.px(30, bt + 6, accent); g.px(33, bt + 6, accent)
        # hem rib
        g.rect(tx0 + 2, bt + 15, tx1 - 2, bt + 16, shirt_s)
        # sleeve cuff highlight + arms
        g.px(tx0 - 2, bt + 4, shirt_d2); g.px(tx1 + 2, bt + 4, shirt_d2)

    elif H == 'wild':              # Wilde: long brown coat, open + red scarf
        g.rect(tx0 - 2, bt, tx1 + 2, bt + 18, shirt)         # long coat
        g.rect(tx0 - 2, bt + 18, tx1 + 2, bt + 19, shade2(shirt))
        g.rect(tx0 - 2, bt + 1, tx0, bt + 17, shirt_s)       # left edge
        g.rect(tx1, bt + 1, tx1 + 2, bt + 17, shirt_s)       # right edge
        g.rect(27, bt + 2, 36, bt + 18, shade2(shirt))       # open front lining
        for yy in (bt + 4, bt + 8, bt + 12, bt + 16):        # buttons
            g.px(27, yy, shade(shirt, 0.5))
        # red scarf wraps neck
        g.rect(23, bt - 1, 40, bt + 2, accent)
        g.rect(23, bt - 1, 40, bt - 1, blend(accent, (0, 0, 0), 0.25))
        g.px(23, bt + 1, accent); g.px(40, bt + 1, accent)
        g.px(23, bt + 2, accent); g.px(40, bt + 2, accent)
        # scarf tail draping
        g.rect(24, bt + 3, 29, bt + 5, accent)
        g.rect(24, bt + 6, 27, bt + 8, shade(accent))
        # coat pocket flaps
        g.rect(tx0 + 2, bt + 9, tx0 + 7, bt + 9, shade2(shirt))
        g.rect(tx1 - 7, bt + 9, tx1 - 2, bt + 9, shade2(shirt))

    # ---- silhouette ink rim on torso
    g.rect(tx0 - 2, bt + 1, tx0 - 2, bt + 12, OUTLINE)
    g.rect(tx1 + 2, bt + 1, tx1 + 2, bt + 12, OUTLINE)
    g.rect(tx0 - 2, bt + 12, tx1 + 2, bt + 12, OUTLINE)

    return g


# =====================================================================
# LAYER 3: BOTTOM (pants / legs)
# =====================================================================
def draw_bottom_layer(cfg):
    g = Grid()
    pants = cfg['pants']
    pants_s = shade(pants)
    pants_h = light(pants, 1.15)
    pants_d = shade2(pants)
    H = cfg['hair']

    lt = LT
    short = H == 'spiky'           # Fitness wears shorts

    hip_x0, hip_x1 = 17, 46
    # hips
    g.rect(hip_x0, lt, hip_x1, lt + 3, pants)
    g.px(hip_x0, lt, pants_s); g.px(hip_x1, lt, pants_s)

    leg_bottom = SHOE_TOP - 1      # = 55
    if short:
        leg_bottom = lt + 8        # short hems

    # left leg block
    g.rect(hip_x0, lt + 2, hip_x0 + 12, leg_bottom, pants)
    g.rect(hip_x0 + 8, lt + 2, hip_x0 + 12, leg_bottom, pants_s)
    # right leg block
    g.rect(hip_x1 - 12, lt + 2, hip_x1, leg_bottom, pants)
    g.rect(hip_x1 - 12, lt + 2, hip_x1 - 8, leg_bottom, pants_s)
    # center crotch split (a dark gap between legs)
    g.rect(hip_x0 + 12, lt + 2, hip_x1 - 12, leg_bottom, blend(pants, (0, 0, 0), 0.30))
    # leg fold crease lines
    g.rect(26, lt + 5, 26, leg_bottom - 1, pants_d)
    g.rect(37, lt + 5, 37, leg_bottom - 1, pants_d)
    # knee highlights
    g.rect(hip_x0 + 3, lt + 7, hip_x0 + 5, lt + 7, pants_h)
    g.rect(hip_x1 - 5, lt + 7, hip_x1 - 3, lt + 7, pants_h)
    # hem cuff
    g.rect(hip_x0, leg_bottom, hip_x0 + 12, leg_bottom, pants_s)
    g.rect(hip_x1 - 12, leg_bottom, hip_x1, leg_bottom, pants_s)

    if short:
        g.rect(hip_x0, lt + 8, hip_x1, lt + 9, pants_s)

    # character-specific touches
    if H == 'bob':                 # Rei pressed slacks crease
        g.rect(26, lt + 2, 26, leg_bottom - 1, pants_d)
        g.rect(37, lt + 2, 37, leg_bottom - 1, pants_d)
    if H == 'side':                # Finance belt + crease
        g.rect(17, lt, 46, lt + 2, (52, 60, 74))
        g.rect(17, lt, 46, lt, shade((52, 60, 74)))
        g.px(31, lt + 1, (190, 185, 140)); g.px(32, lt + 1, (190, 185, 140))
        g.rect(26, lt + 2, 26, leg_bottom - 1, pants_d)
        g.rect(37, lt + 2, 37, leg_bottom - 1, pants_d)
    if H == 'hooded':              # Ops cargo pockets
        g.rect(15, lt + 4, 21, lt + 5, pants_d)
        g.rect(42, lt + 4, 48, lt + 5, pants_d)

    # leg outline rims
    g.rect(hip_x0 - 1, lt + 1, hip_x0 - 1, leg_bottom, OUTLINE)
    g.rect(hip_x1 + 1, lt + 1, hip_x1 + 1, leg_bottom, OUTLINE)

    return g


# =====================================================================
# LAYER 4: SHOES (feet)
# =====================================================================
def _foot_grid(x0, y_off, cfg):
    g = Grid()
    shoes = cfg['shoes']
    shoes_s = shade(shoes)
    shoes_h = light(shoes, 1.22)
    shoes_d = shade2(shoes)
    style = cfg['shoe_style']
    sy = SHOE_TOP

    # left foot points toward +x; we draw the "toe away from center" == +x.
    # For the right-side foot we flip horizontal at assembly, so only a single
    # foot glyph is needed here then mirrored (asymmetric toes avoided).
    w = 9
    # shoe body
    g.rect(x0, sy + y_off, x0 + w - 1, sy + 1 + y_off, shoes)
    g.px(x0, sy + y_off, shoes_h); g.px(x0 + w - 1, sy + y_off, shoes_h)
    # sole / heel band
    g.rect(x0, sy + 2 + y_off, x0 + w - 1, sy + 2 + y_off, OUTLINE)
    g.rect(x0, sy + 3 + y_off, x0 + w - 1, sy + 3 + y_off, shoes_d)

    if style == 'sneaker':
        g.rect(x0 + w - 3, sy + y_off, x0 + w - 1, sy + y_off, shoes_h)  # toe cap
        g.rect(x0 + 2, sy + y_off, x0 + 3, sy + y_off, (235, 240, 245))  # lace
        g.px(x0 + 6, sy + y_off, (200, 205, 210))                         # lace eyelet
    elif style == 'loafer':
        g.px(x0 + 2, sy + y_off, shoes_d)                                 # strap slot
        g.px(x0 + 3, sy + y_off, shoes_d)
        g.px(x0 + 1, sy + y_off, (120, 128, 140))                         # bit
    elif style == 'oxford':
        g.rect(x0 + 3, sy + y_off, x0 + 6, sy + y_off, OUTLINE)           # cap line
        g.rect(x0, sy + 1 + y_off, x0 + 2, sy + 1 + y_off, shoes_h)       # toe sheen
    elif style == 'boot':
        g.rect(x0, sy + y_off - 3, x0 + w - 1, sy + 1 + y_off, shoes)     # low shaft
        g.rect(x0 + 5, sy + y_off - 3, x0 + 6, sy + y_off, shoes_d)       # lace zone
        g.rect(x0, sy + y_off - 3, x0 + w - 1, sy + y_off - 3, OUTLINE)   # boot top
    return g


# unified shoe renderer: both feet, pose-dependent
def render_feet(cfg, frame):
    g = Grid()
    sy = SHOE_TOP
    w = 9

    if frame == 0:                 # idle: feet together, centered under body
        _stitch_left(g, _foot_grid(18, 0, cfg), 18, 0)
        _stitch_right(g, _foot_grid(37, 0, cfg), 37, 0)
        return g
    elif frame == 1:               # left foot steps forward (and up)
        _stitch_left(g, _foot_grid(18, -1, cfg), 18, -1)
        _stitch_right(g, _foot_grid(39, 1, cfg), 39, 1)
    else:                          # right foot forward
        _stitch_left(g, _foot_grid(21, 1, cfg), 21, 1)
        _stitch_right(g, _foot_grid(37, -1, cfg), 37, -1)
    return g


def _stitch_left(g, src, ox, oy):
    for y in range(FRAME):
        for x in range(FRAME):
            c = src.g[y][x]
            if c is not None:
                g.px(x, y, c)


def _stitch_right(g, src, ox, oy):
    for y in range(FRAME):
        for x in range(FRAME):
            c = src.g[y][x]
            if c is not None:
                g.px(63 - x, y, c)


# ---------------------------------------------------------------- sheet assembly
def make_layer_sheet(cfg, layer):
    canvas = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))

    for r, d in enumerate(DIRS):
        for f in range(FRAMES_PER_DIR):
            if layer == 'shoes':
                g = render_feet(cfg, f)
            elif layer == 'hair':
                g = draw_head_layer(cfg)
            elif layer == 'top':
                g = draw_top_layer(cfg)
            else:
                g = draw_bottom_layer(cfg)
            # left/right = horizontal flip of the base pose
            if d in ('left', 'right'):
                g = g.flip_h()
            img = g.to_image()
            canvas.paste(img, (f * FRAME, r * FRAME))
    return canvas


def main():
    produced = {}
    for name, cfg in RESIDENTS.items():
        for layer in ('hair', 'top', 'bottom', 'shoes'):
            sheet = make_layer_sheet(cfg, layer)
            fname = f'{name}_{layer}.png'
            path = os.path.join(OUT_DIR, fname)
            sheet.save(path)
            assert sheet.size == (SHEET_W, SHEET_H), (name, layer, sheet.size)
            produced[name + '_' + layer] = fname
            print('saved', path, sheet.size)
    print('DONE', len(produced), 'sheets')


if __name__ == '__main__':
    main()
