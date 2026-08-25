# -*- coding: utf-8 -*-
"""Generate a 1280x720 top-down pixel town map (original procedural art).
Design drawn at 320x180 then nearest-neighbor x4.
Includes 6 station buildings + paths + nature so it feels like a living town."""
import os
from PIL import Image, ImageDraw

ART = os.path.dirname(__file__)
BG = os.path.join(ART, 'bg')
os.makedirs(BG, exist_ok=True)

W, H = 320, 180

# ---------------- palette (12-color-ish unified woodland theme)
COL = {
    'grass':      (128, 170, 104),
    'grass_dk':   (116, 158, 94),
    'grass_lit':  (142, 184, 116),
    'path':       (202, 186, 152),
    'path_dk':    (182, 166, 134),
    'forest':     (70, 116, 74),
    'trunk':      (104, 78, 60),
    'water':      (96, 156, 196),
    'water_dk':   (82, 142, 182),
    'dark':       (48, 52, 60),
    'dark_dk':    (38, 42, 48),
    'lamp_y':     (255, 224, 130),
    'flower_r':   (232, 118, 118),
    'flower_y':   (246, 208, 120),
    'flower_w':   (240, 240, 244),
}
# building themes: roof, wall, door, accent
BUILD = {
    'town_hall': dict(roof=(120, 96, 160), roof_dk=(102, 80, 138), wall=(226, 216, 200),
                      door=(110, 76, 52), accent=(230, 200, 120), label='市政厅'),
    'teahouse':  dict(roof=(176, 92, 82),  roof_dk=(156, 78, 70),  wall=(240, 226, 200),
                      door=(120, 82, 58),  accent=(250, 214, 150), label='茶馆'),
    'gym':       dict(roof=(80, 140, 192), roof_dk=(66, 122, 172), wall=(212, 224, 232),
                      door=(58, 92, 120),  accent=(240, 240, 244), label='健身房'),
    'canteen':   dict(roof=(216, 176, 92), roof_dk=(196, 156, 76), wall=(250, 240, 216),
                      door=(150, 110, 64), accent=(230, 120, 90),  label='食堂'),
    'stage':     dict(roof=(120, 96, 90),  roof_dk=(104, 82, 76),  wall=(52, 50, 56),
                      door=(120, 96, 160), accent=(220, 210, 200), label='舞台'),
    'sysroom':   dict(roof=(70, 78, 92),   roof_dk=(58, 66, 78),   wall=(170, 180, 190),
                      door=(100, 110, 120),accent=(120, 210, 160), label='机房'),
}

img = Image.new('RGB', (W, H))
dr = ImageDraw.Draw(img)

# ---------------- ground: grass with subtle checker + speckle
for y in range(H):
    for x in range(W):
        base = COL['grass']
        if (x // 3 + y // 3) % 2 == 0:
            base = COL['grass_lit']
        if (x // 7 + y // 7) % 3 == 0:
            base = COL['grass_dk']
        # speckles
        if (x * 31 + y * 17) % 97 == 0:
            base = COL['grass_dk']
        img.putpixel((x, y), base)

def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), c)

def fill(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, c)

# ---------------- perimeter forest + edges
def forest_edges():
    import random
    random.seed(7)
    for y in range(H):
        for x in [0, 1, 2, 3, W-4, W-3, W-2, W-1]:
            if (x + y) % 3 == 0:
                put(x, y, COL['forest'])
    for x in range(W):
        for y in [0, 1, 2, 3, H-4, H-3, H-2, H-1]:
            if (x + y) % 3 == 0:
                put(x, y, COL['forest'])

forest_edges()

# ---------------- paths (dirt) walking grid connecting buildings
def path_hline(y, x0, x1, w=10):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for wy in range(w):
            put(x, y - w//2 + wy, COL['path'])
            if (x + wy) % 9 == 0:
                put(x, y - w//2 + wy, COL['path_dk'])

def path_vline(x, y0, y1, w=10):
    for y in range(min(y0, y1), max(y0, y1) + 1):
        for wx in range(w):
            put(x - w//2 + wx, y, COL['path'])
            if (y + wx) % 9 == 0:
                put(x - w//2 + wx, y, COL['path_dk'])

# central plaza bands
path_hline(108, 30, 290)   # north-south artery vertical strip later
# cross paths
path_hline(60, 40, 280)    # top horizontal
path_hline(118, 40, 280)   # plaza
path_hline(140, 40, 280)   # bottom
path_vline(160, 30, 166)   # central vertical
path_vline(96, 30, 166)    # left vertical
path_vline(240, 30, 166)   # right vertical

# ============================================================ BUILDINGS
def draw_building(bx0, by0, bw, bh, theme, stand):
    roof = theme['roof']; roof_dk = theme['roof_dk']; wall = theme['wall']
    door = theme['door']; accent = theme['accent']
    bx1 = bx0 + bw; by1 = by0 + bh
    # outer roof (slightly larger, pagoda offset)
    fill(bx0 - 3, by0 - 3, bx1 + 2, by1 - 1, roof)
    # roof top highlight row
    fill(bx0 - 3, by0 - 3, bx1 + 2, by0 - 3, light(roof, 1.18))
    # roof inner dark corner
    fill(bx0 - 3, by0 - 2, bx0 - 3, by1 - 1, roof_dk)
    fill(bx1 + 2, by0 - 2, bx1 + 2, by1 - 1, roof_dk)
    # wall
    fill(bx0, by0, bx1, by1, wall)
    fill(bx0, by0, bx1, by0, shade(wall, 0.86))
    # door (bottom center)
    dx = bx0 + bw // 2
    fill(dx - 3, by1 - 8, dx + 3, by1, door)
    fill(dx - 3, by1 - 2, dx + 3, by1, shade(door, 0.6))
    # two windows
    fill(bx0 + 3, by0 + 8, bx0 + 9, by0 + 12, accent)
    fill(bx1 - 9, by0 + 8, bx1 - 3, by0 + 12, accent)
    # roof ridge line
    fill(bx0 - 1, by0 - 2, bx1, by0 - 2, accent)
    return stand

def light(c, f):
    return tuple(min(255, int(x * f)) for x in c)
def shade(c, f=0.78):
    return tuple(int(x * f) for x in c)

# station stand coords stored in MANIFEST (final 1280x720 space)
STANDS = {}

# town_hall: large central-ish top
th = dict(BUILD['town_hall']); s = draw_building(118, 22, 84, 56, th, None)
STANDS['town_hall'] = (int((118 + 84 // 2) * 4), int((22 + 56) * 4))   # at door

# teahouse: left
draw_building(34, 44, 58, 48, BUILD['teahouse'], None)
STANDS['teahouse'] = (int((34 + 58 // 2) * 4), int((44 + 48) * 4))

# gym: top-right
draw_building(226, 26, 72, 46, BUILD['gym'], None)
# gym roof gear detail
fill(226 + 3, 26 - 4, 226 + 9, 26 - 1, COL['lamp_y'])
fill(226 + 8, 26 - 9, 226 + 11, 26 - 2, COL['lamp_y'])
STANDS['gym'] = (int((226 + 72 // 2) * 4), int((26 + 46) * 4))

# canteen: right-bottom
draw_building(236, 116, 66, 44, BUILD['canteen'], None)
# canteen vent
fill(236 + 8, 116 - 5, 236 + 20, 116 - 2, (150, 150, 150))
STANDS['canteen'] = (int((236 + 66 // 2) * 4), int((116 + 44) * 4))

# stage: center plaza platform
fill(120, 120, 200, 152, BUILD['stage']['wall'])
fill(120, 120, 200, 122, (70, 68, 74))
# stage roof canopy
fill(118, 116, 202, 124, BUILD['stage']['accent'])
fill(118, 116, 122, 124, shade(BUILD['stage']['accent']))
fill(198, 116, 202, 124, shade(BUILD['stage']['accent']))
# posts
put(122, 120, COL['dark']); put(198, 120, COL['dark'])
# steps at front of stage
for s in range(4):
    put(158 + s, 152, (220, 210, 200))
STANDS['stage'] = (int(160 * 4), int(154 * 4))

# sysroom: bottom-left
draw_building(44, 124, 62, 44, BUILD['sysroom'], None)
# antenna
fill(74 + 2, 124 - 12, 74 + 2, 124 - 1, COL['dark'])
fill(72, 124 - 12, 76, 124 - 9, COL['dark_dk'])
# server blinks
fill(46, 128, 52, 130, (120, 210, 160))
fill(80, 128, 86, 130, (120, 210, 160))
STANDS['sysroom'] = (int((44 + 62 // 2) * 4), int((124 + 44) * 4))

# ---------------- nature: trees, flowers, pond, lamps (random, seeded)
import random
random.seed(42)

def draw_tree(x, y):
    # canopy
    put(x, y, COL['forest']); put(x + 1, y, COL['forest'])
    put(x - 1, y, COL['forest']); put(x, y - 1, COL['forest']); put(x, y - 2, COL['forest'])
    put(x + 1, y - 1, COL['forest']); put(x - 1, y - 1, COL['forest'])
    put(x, y, light(COL['forest'], 1.15)); put(x + 1, y - 1, light(COL['forest'], 1.15))
    put(x, y + 1, COL['trunk'])

for _ in range(90):
    x = random.randint(10, W - 11); y = random.randint(14, H - 11)
    # avoid on paths/buildings: check pixel is grass-ish
    r, g, b = img.getpixel((x, y))
    if abs(r - COL['grass'][0]) < 24 and abs(g - COL['grass'][1]) < 24:
        draw_tree(x, y)

for _ in range(120):
    x = random.randint(10, W - 11); y = random.randint(14, H - 11)
    r, g, b = img.getpixel((x, y))
    if abs(r - COL['grass'][0]) < 24 and abs(g - COL['grass'][1]) < 24:
        put(x, y, random.choice([COL['flower_r'], COL['flower_y'], COL['flower_w']]))

# pond (bottom-ish left of plaza)
pond_cx, pond_cy = 172, 96
for r in range(5, 0, -1):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                c = COL['water'] if r > 1 else COL['water_dk']
                put(pond_cx + dx, pond_cy + dy, c)
put(pond_cx - 2, pond_cy - 1, (150, 200, 210))

# lamp posts near plaza
def lamp(x, y):
    put(x, y, COL['dark']); put(x, y - 1, COL['dark']); put(x, y - 2, COL['dark'])
    put(x, y - 3, COL['lamp_y']); put(x + 1, y - 3, COL['lamp_y'])
lamp(128, 106); lamp(192, 106)

# ---------------- scale up x4
big = img.resize((W * 4, H * 4), Image.NEAREST)
big.save(os.path.join(BG, 'town_map.png'))
print('saved town_map.png', big.size)
for k, v in STANDS.items():
    print(' stand', k, v)
