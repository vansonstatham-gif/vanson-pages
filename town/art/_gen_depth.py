# -*- coding: utf-8 -*-
"""从现有 buildings.png 拆出「建筑主体遮挡片」+「底座层」，供前端按脚底 y 深度排序。

动机：俯视像素镇里，角色走到一栋建筑「后面（上方）」时，建筑主体应当盖住角色；
角色站在门前（下方）时则角色在前。整张 buildings.png 是固定 z-index 的，无法随
角色 y 动态互插，所以把每栋建筑拆成两半：

  body（屋顶 + 墙面 + 塔/烟囱/天线，含门的上半）  -> bg/occluders/<site>_body.png  （动态 z，按 anchor_y 排序）
  base（门底 + 门前台阶 + 脚底阴影）              -> bg/layers/buildings_base.png   （固定 z=2，永远在角色身后）

body 用紧凑 crop（节省体积、加载快），前端按 manifest 里的 x/y/w/h/anchor_y 定位并参与排序。
坐标全部是 1280x720 像素坐标（design 320x180 坐标 x4）。
"""
import os
from PIL import Image

ART = os.path.dirname(__file__)
SRC = os.path.join(ART, 'bg', 'layers', 'buildings.png')
LAYERS = os.path.join(ART, 'bg', 'layers')
OCC = os.path.join(ART, 'bg', 'occluders')
os.makedirs(OCC, exist_ok=True)

W, H = 1280, 720
src = Image.open(SRC).convert('RGBA')
assert src.size == (W, H), src.size

# body 裁剪区 [x0,y0]x[x1,y1]（1280 坐标）；base = 门底 y（= 脚底 anchor_y）
# 数据源：_gen_layers.py 里每栋建筑的 design 坐标 x4，再向外多留 ~2px 边。
SITES = {
    'town_hall': dict(x0=436, y0=28,  x1=840, y1=312, base=312),
    'teahouse':  dict(x0=124, y0=148, x1=376, y1=368, base=368),
    'gym':       dict(x0=872, y0=76,  x1=1216, y1=288, base=288),
    'canteen':   dict(x0=940, y0=412, x1=1208, y1=640, base=640),
    'stage':     dict(x0=500, y0=516, x1=780, y1=616, base=616),
    'sysroom':   dict(x0=164, y0=400, x1=432, y1=672, base=672),
}

base_canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
occluders = {}

for name, s in SITES.items():
    x0, y0, x1, y1, base = s['x0'], s['y0'], s['x1'], s['y1'], s['base']

    # body：屋顶 + 墙面主体（到门底 base 为止）
    body = src.crop((x0, y0, x1, y1))
    body_path = os.path.join(OCC, name + '_body.png')
    body.save(body_path)

    # base：门底 + 台阶 + 脚底阴影（base-4 到 base+40），原位合成到整层
    bx0, by0, bx1, by1 = x0, base - 4, x1, base + 40
    strip = src.crop((bx0, by0, bx1, by1))
    base_canvas.paste(strip, (bx0, by0))

    occluders[name] = dict(
        img='bg/occluders/%s_body.png' % name,
        x=x0, y=y0, w=x1 - x0, h=y1 - y0, anchor_y=base,
    )
    print('occluder %-10s body(%d,%d,%d,%d) size %dx%d anchor_y=%d'
          % (name, x0, y0, x1, y1, x1 - x0, y1 - y0, base))

base_path = os.path.join(LAYERS, 'buildings_base.png')
base_canvas.save(base_path)
print('saved', base_path)

import json
print('--- manifest occluders (copy into manifest.json) ---')
print(json.dumps(occluders, ensure_ascii=False, indent=2))
