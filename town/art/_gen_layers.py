# -*- coding: utf-8 -*-
"""Generate 4 layered 1280x720 town maps (upgrade from single flat map).

Replaces the single town_map.png approach with draw-order layers so the
front-end can interleave characters and depth:
  1. ground.png    transparent=false : grass, roads, stone plaza, fountain pool
  2. buildings.png transparent       : 6 buildings (roof+wall+door+window) + foot shadows
  3. objects.png   transparent       : trees, bushes, flowers, rocks, lamps, fences, fountain (BEHIND chars)
  4. canopy.png    transparent       : a few tree canopies / foreground foliage (IN FRONT of chars)

Design drawn at 320x180 then nearest-neighbor x4 => 1280x720.
Building door/stand coords are IDENTICAL to _gen_map.py / manifest.json
(design coords here are the /4 of the 1280x720 STANDS):
  town_hall (160,78)  teahouse (63,92)  gym (262,72)
  canteen  (269,160)  stage    (160,154) sysroom (75,168)
"""
import os, random
from PIL import Image, ImageDraw

ART = os.path.dirname(__file__)
LAYERS = os.path.join(ART, 'bg', 'layers')
os.makedirs(LAYERS, exist_ok=True)

W, H = 320, 180
SCALE = 4

# ---------------- unified warm/fresh low-saturation palette
COL = {
    'grass':    (132, 172, 106),
    'grass_dk': (120, 160, 96),
    'grass_lt': (146, 186, 120),
    'grass_dp': (108, 148, 88),          # deeper grass patch / shadow
    'path':     (206, 188, 152),
    'path_dk':  (188, 170, 134),
    'path_lt':  (216, 200, 168),
    'forest':   (72, 122, 78),
    'forest_dk':(60, 106, 66),
    'forest_lt':(98, 148, 96),
    'trunk':    (108, 82, 62),
    'trunk_dk': (88, 66, 50),
    'water':    (102, 160, 198),
    'water_dk': (86, 146, 186),
    'water_lt': (150, 200, 212),
    'dark':     (56, 60, 66),
    'dark_dk':  (44, 48, 52),
    'rocks':    (164, 160, 152),
    'rocks_dk': (138, 134, 126),
    'lamp':     (70, 74, 82),
    'lamp_y':   (255, 226, 132),
    'lamp_glow':(248, 220, 160),
    'flower_r': (236, 130, 122),
    'flower_y': (248, 210, 124),
    'flower_w': (244, 244, 248),
    'flower_p': (216, 150, 190),
    'fence':    (178, 152, 116),
    'blue_glow':(110, 200, 255),
    'blue_hi':  (150, 226, 255),
    'teal':     (64, 170, 190),
}

def light(c, f=1.15):
    return tuple(min(255, int(x * f)) for x in c)
def shade(c, f=0.8):
    return tuple(int(x * f) for x in c)
def mix(a, b, t=0.5):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

# RGBA layers. ground is opaque; others transparent.
ground    = Image.new('RGBA', (W, H))
buildings = Image.new('RGBA', (W, H))
objects   = Image.new('RGBA', (W, H))
canopy    = Image.new('RGBA', (W, H))

gd = ImageDraw.Draw(ground)
bd = ImageDraw.Draw(buildings)
od = ImageDraw.Draw(objects)
cd = ImageDraw.Draw(canopy)

def gput(x, y, c, drift=None):
    if 0 <= x < W and 0 <= y < H:
        ground.putpixel((x, y), c if drift is None else drift)
def balloc_put(img, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), c)
bput = lambda x, y, c: balloc_put(buildings, x, y, c)
oput = lambda x, y, c: balloc_put(objects, x, y, c)
cput = lambda x, y, c: balloc_put(canopy, x, y, c)

def fill_g(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        for x in range(max(0, x0), min(W - 1, x1) + 1):
            gput(x, y, c)

def fill_a(img, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        for x in range(max(0, x0), min(W - 1, x1) + 1):
            balloc_put(img, x, y, c)

# =====================================================================
# 1) GROUND  (opaque): grass texture + forest border + roads + plaza + pool
# =====================================================================
random.seed(11)
for y in range(H):
    for x in range(W):
        base = COL['grass']
        if (x // 5 + y // 5) % 2 == 0:
            base = COL['grass_lt']
        if (x // 13 + y // 13) % 4 == 0:
            base = COL['grass_dk']
        if (x * 7 + y * 13) % 61 < 12:
            base = COL['grass_dp']
        if (x * 17 + y * 5) % 53 < 8:
            base = COL['grass_lt']
        n = (x * 31 + y * 17)
        if n % 211 == 0:
            base = COL['grass_dp']
        if n % 173 == 0:
            base = COL['grass_lt']
        gput(x, y, base)

# perimeter forest border (a distinct richer band; actual tree canopies in objects)
random.seed(7)
for y in range(H):
    for x in list(range(0, 7)) + list(range(W - 7, W)):
        if (x + y) % 3 != 2 and not (3 < x < W - 3 and 3 < y < H - 3):
            gput(x, y, shade(COL['forest'], 0.9))
            if (x + y) % 5 == 0:
                gput(x, y, COL['forest_dk'])
            if (x + y) % 8 == 0:
                gput(x, y, light(COL['forest_lt'], 0.9))
for x in range(W):
    for y in list(range(0, 5)) + list(range(H - 5, H)):
        if (x + y) % 3 != 1:
            gput(x, y, shade(COL['forest'], 0.95))
            if (x + y) % 6 == 0:
                gput(x, y, COL['forest_dk'])

# --- roads / paths ---------------------------------------------------
def path_hline(y, x0, x1, w=10):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for wy in range(w):
            yy = y - w // 2 + wy
            c = COL['path']
            if (x + wy) % 9 == 0:
                c = COL['path_dk']
            if (x * 5 + wy * 3) % 11 == 0:
                c = COL['path_lt']
            gput(x, yy, c)

def path_vline(x, y0, y1, w=10):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for wx in range(w):
            xx = x - w // 2 + wx
            c = COL['path']
            if (y + wx) % 9 == 0:
                c = COL['path_dk']
            if (y * 5 + wx * 3) % 11 == 0:
                c = COL['path_lt']
            gput(xx, y, c)

# doorsteps (narrower, lighter arrivals)
path_hline(78, 158, 162, 12)
path_hline(92, 58, 68, 12)
path_hline(72, 258, 266, 12)
path_hline(160, 264, 274, 12)
path_hline(168, 70, 80, 12)
# main arteries
path_vline(160, 30, 92)
path_hline(60, 140, 180)
path_vline(262, 60, 160)
path_hline(108, 40, 290)
path_hline(140, 40, 290)
path_vline(160, 92, 154)
path_hline(92, 40, 160)
path_hline(168, 60, 150)
path_vline(75, 120, 168)
path_hline(150, 75, 160)
path_vline(30, 60, 92)

# --- stone plaza floor + curb -----------------------------------------
for y in range(122, 152):
    for x in range(118, 202):
        c = mix(COL['path'], (200, 196, 180), 0.5)
        if (x // 2 + y // 2) % 2 == 0:
            c = mix(c, (214, 208, 188), 0.5)
        gput(x, y, c)
for x in range(116, 204):
    gput(x, 120, shade(COL['path'], 0.85)); gput(x, 153, shade(COL['path'], 0.85))
for y in range(121, 153):
    gput(116, y, shade(COL['path'], 0.85)); gput(203, y, shade(COL['path'], 0.85))
# plaza corner accents (light tiles every so often)
for py in range(122, 152, 2):
    for px in range(118, 202, 4):
        if ((px + py) % 8) == 0:
            gput(px, py, mix((200,196,180), (232,226,206), 0.6))

# --- fountain/pond WATER POOL (stone rim + spout go to objects) ---------
f_cx, f_cy = 208, 136
for r in range(6, 0, -1):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                c = COL['water'] if r > 1 else COL['water_dk']
                gput(f_cx + dx, f_cy + dy, c)
gput(f_cx - 3, f_cy - 2, COL['water_lt']); gput(f_cx + 3, f_cy - 3, COL['water_lt'])

# =====================================================================
# 2) BUILDINGS (transparent): 6 buildings + soft ground shadows
# =====================================================================
def foot_shadow(cx, base, hw, depth=5):
    # soft 2-tone elliptical shadow pooled at the door base (under a char it stays)
    for dx in range(-hw, hw + 1):
        for dy in range(0, depth + 1):
            x, y = cx + dx, base - 1 + dy
            if 0 <= x < W and 0 <= y < H:
                d = abs(dx)
                alpha = 120 if dy else 90
                c = shade(COL['grass_dp'], 0.9)
                cur = buildings.getpixel((x, y))
                oc = cur[:3]
                # blend shadow over existing building pixels near door base
                if cur[3] == 0:
                    bput(x, y, (c[0], c[1], c[2], alpha))

def draw_block(x0, y0, x1, y1, color, hi=None, lo=None):
    fill_a(buildings, x0, y0, x1, y1, color)
    if lo is not None:
        for x in range(x0, x1 + 1):
            bput(x, y1, lo)
    if hi is not None:
        for x in range(x0, x1 + 1):
            bput(x, y0, hi)

def draw_roof(x0, y0, x1, y1, roof, ridge):
    fill_a(buildings, x0 - 2, y0 - 3, x1 + 1, y1, roof)
    for x in range(x0 - 2, x1 + 2):
        bput(x, y0 - 3, light(roof, 1.16))
        bput(x, y1, shade(roof, 0.8))
    fill_a(buildings, x0 - 2, y0 - 2, x1 + 1, y0 - 3, ridge)

def door_front(cx, base_y, door, t=0.6):
    fill_a(buildings, cx - 3, base_y - 8, cx + 3, base_y, door)
    for x in range(cx - 3, cx + 4):
        bput(x, base_y - 2, mix(door, (0, 0, 0), t))
        bput(x, base_y - 1, mix(door, (0, 0, 0), 0.45))

def two_windows(xa, xb, y, wall, window):
    fill_a(buildings, xa, y, xa + 6, y + 4, window)
    fill_a(buildings, xb, y, xb + 6, y + 4, window)
    bput(xa - 1, y - 1, shade(wall, 0.8)); bput(xb - 1, y - 1, shade(wall, 0.8))

# ---------- town_hall (grand central upper) stand (160,78) -------------
th_roof = (122, 100, 168); th_wall = (230, 220, 202); th_door = (112, 78, 54); th_acc = (236, 204, 120)
cx, base = 160, 78
bw = 96; x0 = cx - bw // 2; y0 = base - 58
# red-tile roof with shaded eaves + light highlight band under ridge
draw_roof(x0, y0, x0 + bw - 1, y0 + 12, th_roof, light(th_roof, 1.2))
for x in range(x0 - 2, x0 + bw + 1):
    if (x + y0) % 4 == 0:
        bput(x, y0 + 5, light(th_roof, 1.05))     # tile glint
    if (x + y0) % 7 == 0:
        bput(x, y0 - 1, light(th_roof, 1.25))     # top highlight
# clock/banner tower + turret finial
fill_a(buildings, cx - 14, y0 - 10, cx + 14, y0 - 4, th_roof)          # tower crown rises above eaves
bput(cx, y0 - 12, (90, 80, 120)); bput(cx - 1, y0 - 12, (90, 80, 120))  # finial
# walls with top tint
draw_block(x0, y0 + 10, x0 + bw - 1, base, th_wall, hi=shade(th_wall, 0.9), lo=shade(th_wall, 0.92))
# accent column + clock
fill_a(buildings, cx - 14, y0 + 6, cx + 14, y0 + 34, th_acc)
fill_a(buildings, cx - 12, y0 + 8, cx + 12, y0 + 32, (214, 196, 168))
bput(cx, y0 + 12, (90, 80, 120)); bput(cx, y0 + 14, (90, 80, 120)); bput(cx - 1, y0 + 13, (250, 244, 220))
# columns
fill_a(buildings, x0 + 3, y0 + 14, x0 + 8, base - 4, shade(th_wall, 0.94))
fill_a(buildings, x0 + bw - 9, y0 + 14, x0 + bw - 4, base - 4, shade(th_wall, 0.94))
two_windows(x0 + 18, x0 + 40, y0 + 20, th_wall, (118, 150, 200))
two_windows(x0 + bw - 1 - 40, x0 + bw - 1 - 18, y0 + 20, th_wall, (118, 150, 200))
door_front(cx, base, th_door)
# front steps
for s in range(3):
    for x in range(cx - 8 + s, cx + 9 - s, 2):
        if base + 1 + s * 2 < H:
            bput(x, base + 1 + s * 2, (226, 216, 200))
foot_shadow(cx, base, 12, depth=6)

# ---------- teahouse (Chinese, red, upper-left) stand (63,92) ----------
te_roof = (188, 102, 88); te_wall = (244, 230, 204); te_door = (128, 84, 56); te_acc = (250, 218, 150)
cx, base = 63, 92
bw = 58; x0 = cx - bw // 2; y0 = base - 50
# two-tier pagoda roof, deeper overhang, highlight under eaves
draw_roof(x0 - 2, y0 - 2, x0 + bw + 1, y0 + 6, te_roof, light(te_roof, 1.2))
draw_roof(x0 + 14, y0 + 4, x0 + bw - 15, y0 + 12, te_roof, light(te_roof, 1.25))
for x in range(x0 - 2, x0 + bw + 2):
    bput(x, y0 + 11, shade(te_roof, 0.86))        # eave shadow under upper tier
# gold corner finials on roof
bput(x0 - 2, y0 - 4, (250, 218, 150)); bput(x0 + bw + 1, y0 - 4, (250, 218, 150))
draw_block(x0, y0 + 10, x0 + bw - 1, base, te_wall, hi=shade(te_wall, 0.9), lo=shade(te_wall, 0.92))
# red lattice windows
for wx_ in (x0 + 4, x0 + bw - 13):
    fill_a(buildings, wx_, y0 + 16, wx_ + 8, y0 + 24, (150, 70, 58))
    fill_a(buildings, wx_, y0 + 18, wx_ + 8, y0 + 18, light((150, 70, 58), 1.3))
fill_a(buildings, x0 + 16, y0 + 18, x0 + 24, y0 + 22, (250, 218, 120))
fill_a(buildings, x0 + bw - 25, y0 + 18, x0 + bw - 17, y0 + 22, (250, 218, 120))
door_front(cx, base, te_door)
foot_shadow(cx, base, 8, depth=5)

# ---------- gym (glass, upper-right) stand (262,72) ---------------------
gy_roof = (86, 148, 196); gy_wall = (216, 226, 234); gy_door = (60, 96, 124); gy_acc = (244, 244, 248)
cx, base = 262, 72
bw = 78; x0 = cx - bw // 2; y0 = base - 46
# flat tech roof with parapet + blue glow band
draw_roof(x0, y0 - 3, x0 + bw - 1, y0 + 8, gy_roof, light(gy_roof, 1.2))
fill_a(buildings, x0 - 4, y0 - 5, x0 + bw + 3, y0 - 3, shade(gy_roof, 0.85))   # parapet
draw_block(x0, y0 + 6, x0 + bw - 1, base, gy_wall, hi=shade(gy_wall, 0.9), lo=shade(gy_wall, 0.94))
# glass curtain wall: reflective bands + mullions
for gx in range(x0 + 8, x0 + bw - 14, 7):
    fill_a(buildings, gx, y0 + 12, gx + 5, y0 + 36, (150, 176, 196))
    bput(gx + 4, y0 + 13, light((150, 176, 196), 1.2))                    # glass glint
    bput(gx + 4, y0 + 15, (160, 186, 206))
fill_a(buildings, x0 + 12, y0 + 12, x0 + bw - 13, y0 + 36, (150, 176, 196))  # backing
for gx in range(x0 + 12, x0 + bw - 12, 8):
    fill_a(buildings, gx, y0 + 12, gx + 1, y0 + 36, shade((150, 176, 196), 0.7))
# blue accent band lighting up the front
fill_a(buildings, x0 + 12, y0 + 26, x0 + bw - 13, y0 + 27, COL['blue_glow'])
# dumbbell roof sign
fill_a(buildings, x0 + 16, y0 - 3, x0 + 30, y0 - 3, COL['lamp_y'])
fill_a(buildings, x0 + 22, y0 - 6, x0 + 24, y0 - 3, COL['lamp_y'])
door_front(cx, base, gy_door)
foot_shadow(cx, base, 12, depth=5)

# ---------- canteen (warm yellow, lower-right) stand (269,160) ----------
ca_roof = (222, 180, 96); ca_wall = (252, 242, 218); ca_door = (156, 112, 62); ca_acc = (240, 128, 92)
cx, base = 269, 160
bw = 66; x0 = cx - bw // 2; y0 = base - 44
draw_roof(x0, y0 - 3, x0 + bw - 1, y0 + 8, ca_roof, light(ca_roof, 1.2))
for x in range(x0, x0 + bw):
    if (x * 3 + y0) % 4 == 0:
        bput(x, y0 + 4, light(ca_roof, 1.06))     # straw-tile texture
draw_block(x0, y0 + 6, x0 + bw - 1, base, ca_wall, hi=shade(ca_wall, 0.92), lo=shade(ca_wall, 0.9))
# chimney with smoke + roof vent
fill_a(buildings, x0 + 10, y0 - 7, x0 + 22, y0 - 3, (150, 150, 150))
fill_a(buildings, x0 + bw - 20, y0 - 9, x0 + bw - 13, y0 - 3, (120, 118, 114))
bput(x0 + bw - 18, y0 - 12, (238, 234, 228))
# warm glowing kitchen windows
fill_a(buildings, x0 + 8, y0 + 14, x0 + 18, y0 + 22, (252, 210, 120))
fill_a(buildings, x0 + bw - 19, y0 + 14, x0 + bw - 9, y0 + 22, (252, 210, 120))
fill_a(buildings, x0 + 16, y0 + 30, x0 + 26, y0 + 38, (252, 210, 120))
bput(x0 + 13, y0 + 18, light((252, 210, 120), 1.2)); bput(x0 + bw - 14, y0 + 18, light((252, 210, 120), 1.2))
door_front(cx, base, ca_door)
fill_a(buildings, x0 + bw - 16, y0 + 30, x0 + bw - 6, y0 + 38, ca_acc)   # serving hatch
foot_shadow(cx, base, 10, depth=5)

# ---------- stage (open-air wood platform, lower-center) stand (160,154) -
st_platform = (198, 178, 140); st_curb = (176, 158, 122)
# platform boards with grain
for py in range(138, 151):
    for px in range(126, 194):
        bput(px, py, st_platform)
        if (px // 2) % 2 == 0:
            bput(px, py, shade(st_platform, 0.97))
for px in range(126, 194, 3):
    bput(px, 142, shade(st_platform, 0.9)); bput(px, 146, shade(st_platform, 0.9))
for y in range(138, 151):
    bput(126, y, st_curb); bput(194, y, st_curb)
# back wall frame (light)
fill_a(buildings, 128, 130, 192, 136, (124, 120, 118))
fill_a(buildings, 128, 133, 192, 136, shade((124, 120, 118), 0.85))
# bunting
for bx in range(128, 192, 8):
    bput(bx, 132, COL['flower_r']); bput(bx + 4, 132, COL['flower_y'])
bput(130, 130, COL['dark']); bput(190, 130, COL['dark'])
# front steps
for s in range(4):
    for x in range(160 - 9 + s, 160 + 9 - s, 2):
        if 152 + s < H:
            bput(x, 152 + s, (216, 206, 186))
# stage props (music stands float on platform)
bput(150, 140, COL['dark']); bput(150, 138, COL['dark']); bput(158, 140, COL['dark']); bput(158, 138, COL['dark'])
bput(170, 141, (110, 96, 84))
foot_shadow(160, 154, 14, depth=4)

# ---------- sysroom (server hut, tech blue, lower-left) stand (75,168) ---
sy_roof = (74, 92, 112); sy_wall = (150, 170, 182); sy_door = (92, 108, 120); sy_glow = (110, 200, 255)
cx, base = 75, 168
bw = 62; x0 = cx - bw // 2; y0 = base - 46
draw_roof(x0 - 2, y0 - 4, x0 + bw + 1, y0 + 8, sy_roof, light(sy_roof, 1.2))
for x in range(x0 - 2, x0 + bw + 2):
    bput(x, y0 - 4, light(sy_roof, 1.28))
    bput(x, y0 + 7, shade(sy_roof, 0.8))
draw_block(x0, y0 + 6, x0 + bw - 1, base, sy_wall, hi=shade(sy_wall, 0.9), lo=shade(sy_wall, 0.9))
# glowing blue server-blade windows
for sx in range(x0 + 6, x0 + bw - 4, 8):
    fill_a(buildings, sx, y0 + 12, sx + 4, y0 + 22, sy_glow)
    fill_a(buildings, sx, y0 + 12, sx + 4, y0 + 12, COL['blue_hi'])
# second row of softer server lights
for sx in range(x0 + 8, x0 + bw - 6, 8):
    bput(sx, y0 + 28, mix(sy_glow, (60, 120, 160), 0.4))
# antenna mast with blinking beacon
fill_a(buildings, cx - 2, y0 - 16, cx, y0 - 4, COL['dark'])
bput(cx - 2, y0 - 18, COL['dark']); bput(cx - 1, y0 - 18, COL['dark'])
fill_a(buildings, cx - 9, y0 - 21, cx - 3, y0 - 15, COL['dark_dk'])
bput(cx - 6, y0 - 12, sy_glow)
# door + keypad glow
door_front(cx, base, sy_door)
bput(cx, base - 5, sy_glow)
foot_shadow(cx, base, 10, depth=5)

# =====================================================================
# 3) OBJECTS (transparent, BEHIND chars): trees/bushes/flowers/rocks/lamps/fence/fountain
# =====================================================================
random.seed(42)

def on_grass_area(x, y, img_check=None):
    if not (2 < x < W - 2 and 2 < y < H - 2):
        return False
    r, g, b = ground.getpixel((x, y))[:3]
    return g > r and g > 120 and abs(r - g) < 60

def draw_tree(x, y, big=False):
    c = COL['forest']
    pts = [(0, 0), (1, 0), (-1, 0), (0, -1), (0, 1), (1, -1), (-1, -1)]
    for dx, dy in pts:
        oput(x + dx, y + dy, c)
    if big:
        for dx, dy in [(-1, -2), (0, -2), (1, -2), (-2, 0), (2, 0)]:
            oput(x + dx, y + dy, c)
    oput(x, y, COL['forest_lt']); oput(x + 1, y - 1, COL['forest_lt'])
    oput(x - 1, y + 1, light(c, 1.1))
    if big:
        oput(x, -2 + y, COL['forest_lt']); oput(-2 + x, y, COL['forest_lt'])

def draw_bush(x, y):
    oput(x, y, COL['forest_dk']); oput(x + 1, y, COL['forest_dk'])
    oput(x, y - 1, COL['forest_lt']); oput(x - 1, y, COL['forest_lt']); oput(x + 1, y - 1, COL['forest'])
    oput(x, y - 1, COL['flower_r'])

def draw_rock(x, y):
    oput(x, y, COL['rocks']); oput(x + 1, y, COL['rocks'])
    oput(x, y - 1, light(COL['rocks'], 1.1)); oput(x + 1, y - 1, COL['rocks_dk'])
    oput(x + 1, y + 1, COL['rocks_dk'])

def flower_patch(cx_, cy_, color, n=4):
    for _ in range(n):
        dx = random.randint(-1, 1); dy = random.randint(-1, 1)
        if on_grass_area(cx_ + dx, cy_ + dy):
            oput(cx_ + dx, cy_ + dy, color)

# grass shadow pads under each tree cluster (drawn in objects layer, still behind chars)
tree_centers = [(40, 18), (60, 24), (205, 20), (218, 24), (40, 160), (205, 156),
                (285, 24), (150, 14), (95, 108), (232, 106), (150, 176), (70, 40),
                (280, 90), (118, 158), (35, 140), (150, 40)]
random.seed(42)
for cx_, cy_ in tree_centers:
    for dx in range(-3, 4):
        for dy in range(-2, 3):
            x, y = cx_ + dx, cy_ + dy
            if on_grass_area(x, y):
                oput(x, y, COL['grass_dp'])
    for _ in range(random.randint(3, 5)):
        dx = random.randint(-4, 4); dy = random.randint(-4, 4)
        tx, ty = cx_ + dx, cy_ + dy
        if on_grass_area(tx, ty):
            draw_tree(tx + random.randint(-1, 1), ty + random.randint(-1, 1), big=random.random() < 0.4)

# scattered trees
for _ in range(55):
    tx = random.randint(12, W - 13); ty = random.randint(12, H - 13)
    if on_grass_area(tx, ty):
        oput(tx, ty + 1, COL['grass_dp'])
        draw_tree(tx, ty, big=random.random() < 0.3)

# bushes
for _ in range(70):
    bx_ = random.randint(8, W - 9); by_ = random.randint(8, H - 9)
    if on_grass_area(bx_, by_):
        draw_bush(bx_, by_)

# flowers
flower_cols = [COL['flower_r'], COL['flower_y'], COL['flower_w'], COL['flower_p']]
for _ in range(40):
    fx = random.randint(8, W - 9); fy = random.randint(8, H - 9)
    if on_grass_area(fx, fy):
        flower_patch(fx, fy, random.choice(flower_cols), n=random.randint(3, 6))
for _ in range(90):
    fx = random.randint(8, W - 9); fy = random.randint(8, H - 9)
    if on_grass_area(fx, fy):
        oput(fx, fy, random.choice(flower_cols))

# rocks
for _ in range(30):
    rx = random.randint(8, W - 9); ry = random.randint(8, H - 9)
    if on_grass_area(rx, ry):
        draw_rock(rx, ry)

# fountain STONE RIM + SPOUT (the water pool is in ground)
for dx in range(-7, 8):
    for dy in range(-7, 8):
        d2 = dx * dx + dy * dy
        if d2 > 35 and 5 <= (d2) ** 0.5 <= 7:
            oput(f_cx + dx, f_cy + dy, COL['rocks'])
oput(f_cx, f_cy - 1, COL['lamp_glow'])
oput(f_cx, f_cy, (214, 202, 176)); oput(f_cx - 1, f_cy - 1, light((214, 202, 176), 1.1))

# lamp posts along paths / around plaza (in front of grass, behind chars)
def lamp(x, y):
    fill_a(objects, x - 1, y - 3, x, y, COL['lamp'])
    oput(x - 1, y - 4, COL['lamp']); oput(x, y - 4, COL['lamp'])
    oput(x - 1, y - 5, COL['lamp_y']); oput(x, y - 5, COL['lamp_y'])
    oput(x - 1, y - 6, COL['lamp_glow']); oput(x, y - 6, COL['lamp_glow'])
    oput(x - 1, y, COL['dark']); oput(x, y, COL['dark'])
for (lx, ly) in [(172, 108), (146, 108), (168, 92), (164, 152), (150, 92),
                 (262, 60), (262, 108), (260, 140), (68, 100), (160, 86),
                 (205, 150), (160, 62), (108, 108)]:
    if on_grass_area(lx, ly):
        lamp(lx, ly)

# wooden rail fence by teahouse garden
for fx_ in range(28, 56):
    oput(fx_, 40, shade(COL['fence'], 0.9))
for fy_ in range(40, 44):
    oput(28, fy_, COL['fence'])
for fx_ in range(28, 56, 3):
    oput(fx_, 39, light(COL['fence'], 1.1))   # rail highlight

# decorative edging stones on plaza ring
for px_ in range(118, 203, 7):
    oput(px_, 154, COL['rocks'])

# =====================================================================
# 4) CANOPY (transparent, IN FRONT of chars): foreground tree crowns
# =====================================================================
# a few large, low-hanging canopies placed along the bottom / near path
# edges so walking characters pass under them for occlusion depth.
random.seed(2026)
def canopy_grove(cx_, cy_, spread, color):
    for dx in range(-spread, spread + 1):
        for dy in range(-spread, spread + 1):
            if dx * dx + dy * dy <= spread * spread:
                x, y = cx_ + dx, cy_ + dy
                if 0 <= x < W and 0 <= y < H:
                    c = color
                    if (abs(dx) + abs(dy)) % 5 == 0:
                        c = COL['forest_lt']
                    cput(x, y, c)
                    if (abs(dx) + abs(dy)) % 9 == 0:
                        cput(x, y, light(color, 1.15))

# foreground canopy arches: bottom edge + a couple lower-left/right clusters
canopy_grove(150, 178, 22, COL['forest'])    # broad low bower across the bottom
canopy_grove(95, 176, 16, COL['forest'])     # bottom-left overhang
canopy_grove(240, 176, 14, COL['forest_dk']) # bottom-right
# a leafy screen partway up right side, near gym edge (depth over path)
canopy_grove(306, 150, 18, COL['forest'])
canopy_grove(308, 120, 12, COL['forest_lt'])
# behind teahouse upper-left, drooping low
canopy_grove(14, 96, 14, COL['forest_dk'])
opleaf = COL['forest_lt']
for (ax, ay) in [(40, 168), (44, 172), (120, 178), (128, 174), (200, 178),
                 (240, 180), (270, 176), (290, 172), (18, 100)]:
    cput(ax, ay, opleaf); cput(ax + 1, ay, opleaf)

# =====================================================================
# scale each layer x4 nearest and save
# =====================================================================
def save_layer(layer, name):
    big = layer.resize((W * SCALE, H * SCALE), Image.NEAREST)
    path = os.path.join(LAYERS, name)
    big.save(path)
    print('saved', name, big.size)
    return big

g_img = save_layer(ground, 'ground.png')
b_img = save_layer(buildings, 'buildings.png')
o_img = save_layer(objects, 'objects.png')
c_img = save_layer(canopy, 'canopy.png')

# =====================================================================
# verify stands still fall on door fronts (1280x720 coords)
STANDS = {
    'town_hall': (640, 312),
    'teahouse':  (252, 368),
    'gym':       (1048, 288),
    'canteen':   (1076, 640),
    'stage':     (640, 616),
    'sysroom':   (300, 672),
}
print('--- stand points (1280x720) ---')
for k, v in STANDS.items():
    # design coords = //4 ; check a building pixel exists just above stand (door front)
    dx_, dy_ = v[0] // 4, v[1] // 4
    print(' stand', k, v, '-> design', (dx_, dy_))
from collections import Counter
print('ground unique colors:', len(Counter(ground.getdata())))
print('buildings nonzero alpha px :', sum(1 for p in buildings.getdata() if p[3]))
print('objects  nonzero alpha px :', sum(1 for p in objects.getdata() if p[3]))
print('canopy   nonzero alpha px :', sum(1 for p in canopy.getdata() if p[3]))
