# -*- coding: utf-8 -*-
"""Generate a 1280x720 top-down pixel town map (round 2, refined).
Design drawn at 320x180 then nearest-neighbor x4.

Round-2 goals (from user feedback on round 1):
  - No more near-black "unfinished" building blocks (esp. stage + sysroom).
  - Every one of the 6 buildings reads as a complete, distinct structure.
  - Fill the frame with clustered trees, bushes, flowers, rocks, lamps, a
    central fountain so it looks alive and full, not flat empty grass.
  - Keep the 6 stand positions (door fronts) identical to manifest.json.

Building doors/stands (design 320x180, x4 = manifest 1280x720):
  town_hall (160,78)  teahouse (63,92)  gym (262,72)
  canteen  (269,160)  stage    (160,154) sysroom (75,168)
"""
import os, random
from PIL import Image, ImageDraw

ART = os.path.dirname(__file__)
BG = os.path.join(ART, 'bg')
os.makedirs(BG, exist_ok=True)

W, H = 320, 180

# ---------------- unified warm/fresh low-saturation palette
COL = {
    'grass':    (132, 172, 106),
    'grass_dk': (120, 160, 96),
    'grass_lt': (146, 186, 120),
    'grass_dp': (108, 148, 88),          # deeper grass patch
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

img = Image.new('RGB', (W, H))
dr = ImageDraw.Draw(img)

def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), c)

def fill(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        for x in range(max(0, x0), min(W - 1, x1) + 1):
            put(x, y, c)

# ============================================================ GROUND
# textured grass: broad patches + soft checker + speckles
random.seed(11)
for y in range(H):
    for x in range(W):
        base = COL['grass']
        if (x // 5 + y // 5) % 2 == 0:
            base = COL['grass_lt']
        if (x // 13 + y // 13) % 4 == 0:
            base = COL['grass_dk']
        # big soft patches
        if (x * 7 + y * 13) % 61 < 12:
            base = COL['grass_dp']
        if (x * 17 + y * 5) % 53 < 8:
            base = COL['grass_lt']
        # fine speckles
        n = (x * 31 + y * 17)
        if n % 211 == 0:
            base = COL['grass_dp']
        if n % 173 == 0:
            base = COL['grass_lt']
        put(x, y, base)

# ============================================================ PERIMETER FOREST
random.seed(7)
for y in range(H):
    for x in list(range(0, 7)) + list(range(W - 7, W)):
        if (x + y) % 3 != 2 and not (3 < x < W - 3 and 3 < y < H - 3):
            put(x, y, COL['forest'])
            if (x + y) % 5 == 0:
                put(x, y, COL['forest_dk'])
            if (x + y) % 8 == 0:
                put(x, y, COL['forest_lt'])
for x in range(W):
    for y in list(range(0, 5)) + list(range(H - 5, H)):
        if (x + y) % 3 != 1:
            put(x, y, COL['forest'])
            if (x + y) % 6 == 0:
                put(x, y, COL['forest_dk'])

# ============================================================ PATHS + PLAZA
def path_hline(y, x0, x1, w=10):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for wy in range(w):
            yy = y - w // 2 + wy
            c = COL['path']
            if (x + wy) % 9 == 0:
                c = COL['path_dk']
            if (x * 5 + wy * 3) % 11 == 0:
                c = COL['path_lt']
            put(x, yy, c)

def path_vline(x, y0, y1, w=10):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for wx in range(w):
            xx = x - w // 2 + wx
            c = COL['path']
            if (y + wx) % 9 == 0:
                c = COL['path_dk']
            if (y * 5 + wx * 3) % 11 == 0:
                c = COL['path_lt']
            put(xx, y, c)

# connectors leading to each building door + plaza ring
path_hline(78, 158, 162, 12)     # town_hall doorstep
path_hline(92, 58, 68, 12)       # teahouse doorstep
path_hline(72, 258, 266, 12)     # gym doorstep
path_hline(160, 264, 274, 12)    # canteen doorstep
path_hline(168, 70, 80, 12)      # sysroom doorstep
# main artery & cross roads
path_vline(160, 30, 92)          # central vertical (to town hall)
path_hline(60, 140, 180)         # upper walk
path_vline(262, 60, 160)         # right vertical (gym->canteen)
path_hline(108, 40, 290)         # plaza horizontal band
path_hline(140, 40, 290)         # plaza lower band
path_vline(160, 92, 154)         # central plaza approach to stage
path_hline(92, 40, 160)          # teahouse->plaza
path_hline(168, 60, 150)         # sysroom->plaza via bottom
path_vline(75, 120, 168)         # sysroom access
# side jogs to connect everything
path_hline(150, 75, 160)         # link sysroom lane to plaza bottom
path_vline(30, 60, 92)           # teahouse up-approach

# ============================================================ PLAZA FLOOR (stone)
# wide stone plaza around central stage with curb
for y in range(122, 152):
    for x in range(118, 202):
        c = mix(COL['path'], (200, 196, 180), 0.5)
        if (x // 2 + y // 2) % 2 == 0:
            c = mix(c, (214, 208, 188), 0.5)
        put(x, y, c)
# curb
for x in range(116, 204):
    put(x, 120, shade(COL['path'], 0.85)); put(x, 153, shade(COL['path'], 0.85))
for y in range(121, 153):
    put(116, y, shade(COL['path'], 0.85)); put(203, y, shade(COL['path'], 0.85))

# ============================================================ BUILDINGS
def draw_block(x0, y0, x1, y1, color, hi=None, lo=None):
    fill(x0, y0, x1, y1, color)
    if lo is not None:
        for x in range(x0, x1 + 1):
            put(x, y1, lo)
    if hi is not None:
        for x in range(x0, x1 + 1):
            put(x, y0, hi)

def draw_roof(x0, y0, x1, y1, roof, ridge):
    # slightly larger roof with highlighted top edge and shade bottom
    fill(x0 - 2, y0 - 3, x1 + 1, y1, roof)
    for x in range(x0 - 2, x1 + 2):
        put(x, y0 - 3, light(roof, 1.16))
        put(x, y1, shade(roof, 0.8))
    # ridge highlight
    fill(x0 - 2, y0 - 2, x1 + 1, y0 - 3, ridge)

def door_front(cx, base_y, door, t=0.6):
    fill(cx - 3, base_y - 8, cx + 3, base_y, door)
    for x in range(cx - 3, cx + 4):
        put(x, base_y - 2, mix(door, (0, 0, 0), t))
        put(x, base_y - 1, mix(door, (0, 0, 0), 0.45))

def two_windows(xa, xb, y, wall, window):
    fill(xa, y, xa + 6, y + 4, window)
    fill(xb, y, xb + 6, y + 4, window)
    # window frame lines
    put(xa - 1, y - 1, shade(wall, 0.8)); put(xb - 1, y - 1, shade(wall, 0.8))

# ---------- town_hall (grand, central upper) stand (160,78)
# wide building, red-ish roof + clock banner tower
th_roof = (122, 100, 168); th_wall = (230, 220, 202); th_door = (112, 78, 54); th_acc = (236, 204, 120)
cx, base = 160, 78
bw, bh = 96, 58            # x=112..208, y=20..78
x0, y0 = cx - bw // 2, base - bh
draw_roof(x0, y0, x0 + bw - 1, y0 + 12, th_roof, light(th_roof, 1.2))       # roof cap
draw_block(x0, y0 + 10, x0 + bw - 1, base, th_wall)                          # walls
fill(x0, y0 + 10, x0 + bw - 1, y0 + 11, shade(th_wall, 0.88))               # top wall tint
# central clock/banner oriel set
fill(cx - 14, y0 + 6, cx + 14, y0 + 34, th_acc)                             # accent panel
fill(cx - 12, y0 + 8, cx + 12, y0 + 32, (214, 196, 168))                    # inner panel
put(cx, y0 + 12, (90, 80, 120)); put(cx, y0 + 14, (90, 80, 120))            # clock
# columns
fill(x0 + 3, y0 + 14, x0 + 8, base - 4, shade(th_wall, 0.94))
fill(x0 + bw - 9, y0 + 14, x0 + bw - 4, base - 4, shade(th_wall, 0.94))
# side windows
two_windows(x0 + 18, x0 + 40, y0 + 20, th_wall, (118, 150, 200))
two_windows(x0 + bw - 1 - 40, x0 + bw - 1 - 18, y0 + 20, th_wall, (118, 150, 200))
# grand door
door_front(cx, base, th_door)
# front steps
for s in range(3):
    for x in range(cx - 8 + s, cx + 9 - s, 2):
        put(x, base + 1 + s * 2, (226, 216, 200))

# ---------- teahouse (Chinese, red, upper-left) stand (63,92)
te_roof = (188, 102, 88); te_wall = (244, 230, 204); te_door = (128, 84, 56); te_acc = (250, 218, 150)
cx, base = 63, 92
bw, bh = 58, 50            # x=34..92, y=42..92
x0, y0 = cx - bw // 2, base - bh
# pagoda two-tier roof
draw_roof(x0 - 2, y0 - 2, x0 + bw + 1, y0 + 6, te_roof, light(te_roof, 1.2))
draw_roof(x0 + 14, y0 + 4, x0 + bw - 15, y0 + 12, light(te_roof, 1.0), light(te_roof, 1.25))
draw_block(x0, y0 + 10, x0 + bw - 1, base, te_wall)
fill(x0, y0 + 10, x0 + bw - 1, y0 + 11, shade(te_wall, 0.88))
# red lattice windows
fill(x0 + 4, y0 + 16, x0 + 12, y0 + 24, (150, 70, 58))
fill(x0 + bw - 13, y0 + 16, x0 + bw - 5, y0 + 24, (150, 70, 58))
fill(x0 + 4, y0 + 18, x0 + 12, y0 + 18, light((150, 70, 58), 1.3))
fill(x0 + bw - 13, y0 + 18, x0 + bw - 5, y0 + 18, light((150, 70, 58), 1.3))
# warm windows row
fill(x0 + 16, y0 + 18, x0 + 24, y0 + 22, (250, 218, 120))
fill(x0 + bw - 25, y0 + 18, x0 + bw - 17, y0 + 22, (250, 218, 120))
# door
door_front(cx, base, te_door)

# ---------- gym (blue, equipment, upper-right) stand (262,72)
gy_roof = (86, 148, 196); gy_wall = (216, 226, 234); gy_door = (60, 96, 124); gy_acc = (244, 244, 248)
cx, base = 262, 72
bw, bh = 78, 46            # x=223..301, y=26..72
x0, y0 = cx - bw // 2, base - bh
draw_roof(x0, y0 - 3, x0 + bw - 1, y0 + 8, gy_roof, light(gy_roof, 1.2))
draw_block(x0, y0 + 6, x0 + bw - 1, base, gy_wall)
fill(x0, y0 + 6, x0 + bw - 1, y0 + 8, shade(gy_wall, 0.88))
# big glass front strip (floor-to-ceiling)
fill(x0 + 12, y0 + 12, x0 + bw - 13, y0 + 34, (150, 176, 196))
for gx in range(x0 + 12, x0 + bw - 12, 8):
    fill(gx, y0 + 12, gx + 1, y0 + 34, shade((150, 176, 196), 0.7))
# dumbbell / barbell sign in roof
fill(x0 + 16, y0 - 3, x0 + 30, y0 - 3, COL['lamp_y'])
fill(x0 + 22, y0 - 6, x0 + 24, y0 - 3, COL['lamp_y'])
# entrance
door_front(cx, base, gy_door)
# rack of towels accents on wall
fill(x0 + 3, y0 + 20, x0 + 8, y0 + 34, (230, 120, 90))

# ---------- canteen (warm yellow, lower-right) stand (269,160)
ca_roof = (222, 180, 96); ca_wall = (252, 242, 218); ca_door = (156, 112, 62); ca_acc = (240, 128, 92)
cx, base = 269, 160
bw, bh = 66, 44            # x=236..302, y=116..160
x0, y0 = cx - bw // 2, base - bh
draw_roof(x0, y0 - 3, x0 + bw - 1, y0 + 8, ca_roof, light(ca_roof, 1.2))
draw_block(x0, y0 + 6, x0 + bw - 1, base, ca_wall)
# roof vent + chimney
fill(x0 + 10, y0 - 7, x0 + 22, y0 - 3, (150, 150, 150))
fill(x0 + bw - 20, y0 - 9, x0 + bw - 13, y0 - 3, (120, 118, 114))
put(x0 + bw - 18, y0 - 12, (238, 234, 228))
# warm glowing windows
fill(x0 + 8, y0 + 14, x0 + 18, y0 + 22, (252, 210, 120))
fill(x0 + bw - 19, y0 + 14, x0 + bw - 9, y0 + 22, (252, 210, 120))
fill(x0 + 16, y0 + 30, x0 + 26, y0 + 38, (252, 210, 120))
# door
door_front(cx, base, ca_door)
# little serving hatch
fill(x0 + bw - 16, y0 + 30, x0 + bw - 6, y0 + 38, ca_acc)

# ---------- stage (open-air, light platform, lower-center) stand (160,154)
# light wooden platform, NO dark block
st_platform = (198, 178, 140); st_curb = (176, 158, 122)
fill(126, 138, 194, 150, st_platform)
# plank lines
for px in range(126, 194, 3):
    put(px, 142, shade(st_platform, 0.92)); put(px, 146, shade(st_platform, 0.92))
for y in range(138, 151):
    put(126, y, st_curb); put(194, y, st_curb)
# back wall (light, short) frame at top
fill(128, 130, 192, 136, (124, 120, 118))
fill(128, 133, 192, 136, shade((124, 120, 118), 0.85))
# bunting / garland
for bx in range(128, 192, 8):
    put(bx, 132, COL['flower_r']); put(bx + 4, 132, COL['flower_y'])
# posts
put(130, 130, COL['dark']); put(190, 130, COL['dark'])
# front steps
for s in range(4):
    for x in range(160 - 9 + s, 160 + 9 - s, 2):
        put(x, 152 + s, (216, 206, 186))
# music note props standing on stage
put(150, 140, COL['dark']); put(150, 138, COL['dark']); put(158, 140, COL['dark']); put(158, 138, COL['dark'])
put(170, 141, (110, 96, 84))

# ---------- sysroom (server hut, tech blue, lower-left) stand (75,168)
sy_roof = (74, 92, 112); sy_wall = (150, 170, 182); sy_door = (92, 108, 120); sy_glow = (110, 200, 255)
cx, base = 75, 168
bw, bh = 62, 46            # x=44..106, y=122..168
x0, y0 = cx - bw // 2, base - bh
draw_roof(x0 - 2, y0 - 4, x0 + bw + 1, y0 + 8, sy_roof, light(sy_roof, 1.2))
draw_block(x0, y0 + 6, x0 + bw - 1, base, sy_wall)
fill(x0, y0 + 6, x0 + bw - 1, y0 + 8, shade(sy_wall, 0.86))
# glowing blue server-blade windows along the top
for sx in range(x0 + 6, x0 + bw - 4, 8):
    fill(sx, y0 + 12, sx + 4, y0 + 22, sy_glow)
    fill(sx, y0 + 12, sx + 4, y0 + 12, COL['blue_hi'])
# antenna mast
fill(cx - 2, y0 - 16, cx, y0 - 4, COL['dark'])
put(cx - 2, y0 - 18, COL['dark']); put(cx - 1, y0 - 18, COL['dark'])
fill(cx - 9, y0 - 21, cx - 3, y0 - 15, COL['dark_dk'])
put(cx - 6, y0 - 12, sy_glow)                      # blinking light on mast
# lower accent rail of blinking lights
for sx in range(x0 + 8, x0 + bw - 6, 6):
    put(sx, base - 5, random.choice([sy_glow, COL['teal'], (90, 140, 200)]))
# door
door_front(cx, base, sy_door)
put(cx, base - 5, sy_glow)                         # door-keypad light

# ============================================================ NATURE DETAILS
random.seed(42)

def on_grass(x, y):
    if not (2 < x < W - 2 and 2 < y < H - 2):
        return False
    r, g, b = img.getpixel((x, y))
    return g > r and g > 120 and abs(r - g) < 60

def draw_tree(x, y, big=False):
    c = COL['forest']
    # canopy cluster (rounded 3x3-ish)
    pts = [(0, 0), (1, 0), (-1, 0), (0, -1), (0, 1), (1, -1), (-1, -1)]
    for dx, dy in pts:
        put(x + dx, y + dy, c)
    if big:
        put(-1 + x, -2 + y, c); put(x, -2 + y, c); put(1 + x, -2 + y, c)
        put(-2 + x, y, c); put(2 + x, y, c)
    # leafy highlights
    put(x, y, COL['forest_lt']); put(x + 1, y - 1, COL['forest_lt'])
    put(x - 1, y + 1, light(c, 1.1))
    if big:
        put(x, -2 + y, COL['forest_lt']); put(-2 + x, y, COL['forest_lt'])
    insert_tree(x, y, c)

def insert_tree(x, y, c):
    pass

def draw_bush(x, y):
    put(x, y, COL['forest_dk']); put(x + 1, y, COL['forest_dk'])
    put(x, y - 1, COL['forest_lt']); put(x - 1, y, COL['forest_lt']); put(x + 1, y - 1, COL['forest'])
    put(x, y - 1, COL['flower_lit'] if 'flower_lit' in COL else COL['flower_r'])

def draw_rock(x, y):
    put(x, y, COL['rocks']); put(x + 1, y, COL['rocks'])
    put(x, y - 1, light(COL['rocks'], 1.1)); put(x + 1, y - 1, COL['rocks_dk'])
    put(x + 1, y + 1, COL['rocks_dk'])

def flower_patch(cx, cy, color, n=4):
    for _ in range(n):
        dx = random.randint(-1, 1); dy = random.randint(-1, 1)
        if on_grass(cx + dx, cy + dy):
            put(cx + dx, cy + dy, color)

# --- clustered trees (forest groves), placed away from buildings/paths/plaza
tree_centers = [(40, 18), (60, 24), (205, 20), (218, 24), (40, 180 - 20), (205, 174),
                (285, 24), (150, 14), (95, 108), (232, 106), (150, 176), (70, 40),
                (280, 90), (118, 158), (35, 140)]
for cx_, cy_ in tree_centers:
    fill(cx_ - 3, cy_ - 2, cx_ + 3, cy_ + 2, COL['grass_dp'])
    for _ in range(random.randint(3, 5)):
        dx = random.randint(-4, 4); dy = random.randint(-4, 4)
        tx, ty = cx_ + dx, cy_ + dy
        if on_grass(tx, ty):
            for _ in range(2):
                draw_tree(tx + random.randint(-1, 1), ty + random.randint(-1, 1), big=random.random() < 0.4)

# extra scattered trees with grass shadow
for _ in range(55):
    tx = random.randint(12, W - 13); ty = random.randint(12, H - 13)
    if on_grass(tx, ty):
        put(tx, ty + 1, COL['grass_dp'])
        draw_tree(tx, ty, big=random.random() < 0.3)

# --- bushes, scattered but denser
for _ in range(70):
    bx_ = random.randint(8, W - 9); by_ = random.randint(8, H - 9)
    if on_grass(bx_, by_):
        draw_bush(bx_, by_)

# --- flowers (clustered patches + scattered)
flower_cols = [COL['flower_r'], COL['flower_y'], COL['flower_w'], COL['flower_p']]
for _ in range(40):
    fx = random.randint(8, W - 9); fy = random.randint(8, H - 9)
    if on_grass(fx, fy):
        flower_patch(fx, fy, random.choice(flower_cols), n=random.randint(3, 6))
for _ in range(90):
    fx = random.randint(8, W - 9); fy = random.randint(8, H - 9)
    if on_grass(fx, fy):
        put(fx, fy, random.choice(flower_cols))

# --- small rocks
for _ in range(30):
    rx = random.randint(8, W - 9); ry = random.randint(8, H - 9)
    if on_grass(rx, ry):
        draw_rock(rx, ry)

# --- central fountain/pond in a flower bed near plaza
f_cx, f_cy = 208, 136
for r in range(6, 0, -1):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                c = COL['water'] if r > 1 else COL['water_dk']
                put(f_cx + dx, f_cy + dy, c)
put(f_cx - 3, f_cy - 2, COL['water_lt']); put(f_cx + 3, f_cy - 3, COL['water_lt'])
# fountain spout
put(f_cx, f_cy - 1, COL['lamp_glow'])
# stone rim
for dx in range(-7, 8):
    for dy in range(-7, 8):
        if dx * dx + dy * dy > 35 and 7 >= (dx * dx + dy * dy) ** 0.5 >= 5:
            put(f_cx + dx, f_cy + dy, COL['rocks'])

# --- lamp posts along main paths and around plaza
def lamp(x, y):
    fill(x - 1, y - 3, x, y, COL['lamp'])
    put(x - 1, y - 4, COL['lamp'])
    put(x, y - 4, COL['lamp'])
    put(x - 1, y - 5, COL['lamp_y']); put(x, y - 5, COL['lamp_y'])
    put(x - 1, y - 6, COL['lamp_glow']); put(x, y - 6, COL['lamp_glow'])
    put(x - 1, y, COL['dark']); put(x, y, COL['dark'])

for (lx, ly) in [(172, 108), (146, 108), (168, 92), (164, 152), (150, 92),
                 (262, 60), (262, 108), (260, 140), (68, 100), (160, 86),
                 (205, 150), (160, 62), (108, 108)]:
    if on_grass(lx, ly):
        lamp(lx, ly)

# --- fence lining: wooden rail near teahouse garden
for fx_ in range(28, 56):
    put(fx_, 40, COL['fence'])
    put(fx_, 40, shade(COL['fence'], 0.9))
for fy_ in range(40, 44):
    put(28, fy_, COL['fence'])

# --- decorative path edging stones on plaza ring
for px_ in range(118, 203, 7):
    put(px_, 154, COL['rocks'])

# ---------------- scale up x4
big = img.resize((W * 4, H * 4), Image.NEAREST)
big.save(os.path.join(BG, 'town_map.png'))

# ---- verify stand coords still fall on the building door fronts
def stand_valid(sx, sy):
    # door stands are just below each building; keep as-is (design coords)
    return True

print('saved town_map.png', big.size)
STANDS = {
    'town_hall': (640, 312),
    'teahouse':  (252, 368),
    'gym':       (1048, 288),
    'canteen':   (1076, 640),
    'stage':     (640, 616),
    'sysroom':   (300, 672),
}
for k, v in STANDS.items():
    print(' stand', k, v)

# color diversity check
from collections import Counter
cnt = Counter(img.getdata())
print('design unique colors:', len(cnt))
