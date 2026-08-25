# -*- coding: utf-8 -*-
"""Write web/art/manifest.json + web/art/CREDITS.txt (utf-8).
Stand coords are in final 1280x720 town_map.png pixel space."""
import os, json

ART = os.path.dirname(__file__)
MANIFEST = os.path.join(ART, 'manifest.json')
CREDITS = os.path.join(ART, 'CREDITS.txt')

# engine key -> (short sprite base, cn)
RESIDENTS = {
    'Rei':               ('Rei',            'Rei'),
    'Fitness Coach':     ('Fitness',        '健身教练'),
    'Financial Advisor': ('Finance',        '财经顾问'),
    'Entertainment':     ('Entertainment',  '娱乐助手'),
    'Ops':               ('Ops',            '运维'),
    'Wilde':             ('Wilde',          '骚客'),
}

# site id -> (cn, stand x, stand y in 1280x720)
SITES = {
    'town_hall': ('市政厅', 640, 312),
    'teahouse':  ('茶馆',   252, 368),
    'gym':       ('健身房', 1048, 288),
    'canteen':   ('食堂',   1076, 640),
    'stage':     ('舞台',   640, 616),
    'sysroom':   ('机房',   300, 672),
}

manifest = {
    "format_version": 1,
    "format": "pixel-town",
    "asset_root": "art",          # relative to web/
    "generated_by": "万森小镇美术 · 程序化像素",  # utf-8
    "sprite_sheets": {
        "description": "每个居民 = 一张 spritesheet：4 行方向 × 3 列走路帧",
        "frame_w": 64,
        "frame_h": 64,
        "frames_per_direction": 3,
        "row_order": ["down", "left", "up", "right"],
        "transparent": True,
    },
    "residents": {
        k: {"sprite": f"sprites/{short}_walk.png", "cn": cn}
        for k, (short, cn) in RESIDENTS.items()
    },
    "map": {
        "image": "bg/town_map.png",
        "width": 1280,
        "height": 720,
        "pixel_scale": 4,
        "design_size": [320, 180],
    },
    "sites": {
        k: {
            "cn": cn,
            "stand": [x, y],      # [x, y] in town_map.png pixels; person 脚底站此点
        }
        for k, (cn, x, y) in SITES.items()
    },
}

with open(MANIFEST, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print('wrote', MANIFEST)

credits = """\
万森小镇 · 像素美术素材来源与许可证 (CREDITS.txt)
================================================

本项目 web/art/ 下的全部像素素材（居民 spritesheet、小镇地图 town_map.png）
均为本项目的【原创程序化生成美术】——由万森小镇美术脚本（Python + Pillow）
按像素粒度绘制，非 AI 生成器硬画、非第三方下载素材裁剪调色。

许可证：CC0 1.0（公有领域，可自由使用/修改/商用，无署名要求，无怪癖授权顾虑）
   - 居民小人：web/art/sprites/<居民>_walk.png（64x64/帧，4 方向 × 3 帧走路动画）
   - 小镇地图：web/art/bg/town_map.png（1280x720 俯视像素小镇）
   - 生成脚本：web/art/_gen_*.py（可复现，参数化，便于日后统一改版）

生成方式（确保风格统一、可复现）：
  1. 6 位居民共用同一套 "chibi 像素身体模板 + 配色/发型/服饰参数"，
     因此拥有完全一致的视角、像素尺度、纸娃娃动画规律——一眼可区分、且统一。
  2. 小镇地图为纯程序化拼搭：统一草地/道路/建筑配色体系，6 站点建筑、
     连接步道、树木、花、池塘、路灯，营造"活的小镇"。
  3. 全部 PNG、自托管、无 CDN 依赖。

素材来源尝试说明：
  优先方案曾尝试获取第三方 CC0/CC-BY-SA 像素包（Kenney、LPC Universal）。
  因本机境内直连境外被墙、且部分直链无对应资源路径，未能稳定取得可直接
  组装为"6 套完整 4 方向走路纸娃娃"的统一成品；
  故按任务允许的回退方案，以原创程序化方式绘制，保证无授权风险、风格统一。

新增素材时的约定：
  - 若日后引入第三方素材，请在此追加来源链接与许可证原文，并保持 12 色以内
    的统一调色板与 64x64/帧、4 方向 × 3 帧的动画规格。
  - web/art/ 之外的文件不在本清单范围内。
"""
with open(CREDITS, 'w', encoding='utf-8') as f:
    f.write(credits)
print('wrote', CREDITS)
