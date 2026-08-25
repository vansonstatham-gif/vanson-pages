/* =========================================================
   万森小镇 · 前端（俯视像素地图渲染）
   数据源：
     - art/manifest.json （美术清单：spritesheet 规格 / 居民 / 地图 / 站点站位）
     - snapshot.json     （引擎静态快照：location_hub / residents_summary / events）
   全自托管、相对路径、无 CDN。
   ========================================================= */
(async () => {
  'use strict';

  /* ---------- 读取两份 JSON（都可离线兜底） ---------- */
  async function loadJSON(url) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } catch (e) {
      console.warn('读取失败:', url, e);
      return null;
    }
  }

  const [manifest, snapshot] = await Promise.all([
    loadJSON('art/manifest.json'),
    loadJSON('snapshot.json'),
  ]);

  const $ = id => document.getElementById(id);
  const mapEl = $('map');
  const foot = $('foot');
  const vinEl = $('vin');
  const dateEl = $('meta-date');
  const phaseEl = $('meta-phase');
  const eventsUl = $('events');

  /* ---------- 常量 / 兜底表（即使 manifest 缺失也有基本可渲染的东西） ---------- */
  const FALLBACK_FACES = { 'Rei': '🗂️', 'Fitness Coach': '💪', 'Financial Advisor': '📈',
                           'Entertainment': '🎬', 'Ops': '🛠️', 'Wilde': '📜' };
  const EMOTE_SYM = { calm: '😌', happy: '🙂', amused: '😄', annoyed: '🙄', tired: '😴' };
  // 行顺序必须与 manifest.sprite_sheets.row_order 一致；默认向下
  const ROW_ORDER = ['down', 'left', 'up', 'right'];
  // 地图设计尺寸（px）；若 manifest 缺失用默认 1280×720
  const MW = (manifest && manifest.map && manifest.map.width) || 1280;
  const MH = (manifest && manifest.map && manifest.map.height) || 720;

  /* 居民元数据：引擎 key → { sprite 相对路径, cn 名 }（融合 manifest + 兜底） */
  const fallbackResidents = {
    'Rei':               { cn: 'Rei',     sprite: 'art/sprites/Rei_walk.png' },
    'Fitness Coach':     { cn: '健身教练', sprite: 'art/sprites/Fitness_walk.png' },
    'Financial Advisor': { cn: '财经顾问', sprite: 'art/sprites/Finance_walk.png' },
    'Entertainment':     { cn: '娱乐助手', sprite: 'art/sprites/Entertainment_walk.png' },
    'Ops':               { cn: '运维',     sprite: 'art/sprites/Ops_walk.png' },
    'Wilde':             { cn: 'Wilde',    sprite: 'art/sprites/Wilde_walk.png' },
  };
  const RESIDENTS = buildResidents(manifest, fallbackResidents, 'art');

  /* 站点：站点 key → { cn, stand:[x,y] }（融合 manifest + 兜底置中） */
  const fallbackSites = {
    town_hall: { cn: '市政厅' }, teahouse: { cn: '茶馆' }, gym: { cn: '健身房' },
    canteen:   { cn: '食堂' },   stage:    { cn: '舞台' }, sysroom: { cn: '机房' },
  };
  const SITES = buildSites(manifest, fallbackSites);

  /* 地图图层：分层渲染（ground/buildings/objects/canopy），canopy 在最前制造遮挡纵深 */
  const MAP_LAYER_Z = { ground: 1, buildings: 2, objects: 3, canopy: 6 };
  const mapLayers = (manifest && manifest.map && manifest.map.layers) ? manifest.map.layers : null;

  /* ---------- 顶栏 + 页脚 ---------- */
  dateEl.textContent = '◷ ' + ((snapshot && snapshot.world && snapshot.world.today) || '未知日期');
  phaseEl.textContent = '◔ ' + ((snapshot && snapshot.world && snapshot.world.phase) || '');
  const vin = (snapshot && (snapshot.vin != null ? snapshot.vin : (snapshot.world && snapshot.world.vin))) || 0;
  vinEl.textContent = 'VIN ' + vin;
  foot.textContent = (snapshot
    ? '✅ 已读取快照 ' + ((snapshot.world && snapshot.world.today) || '') + ' · 契约 iface_v=' + (snapshot.iface_v || '-')
    : '⚠️ 未读到 snapshot.json。请先让引擎跑 one_tick 生成快照。')
    + ' · 美术 ' + (manifest ? 'manifest v' + (manifest.format_version || '?') : '缺失(用兜底表)');

  /* ---------- 1) 底图（分层，或单张兜底） ---------- */
  if (mapLayers && typeof mapLayers === 'object') {
    const assetRoot = (manifest && manifest.asset_root) ? manifest.asset_root : 'art';
    Object.keys(mapLayers).forEach(name => {
      const path = mapLayers[name];
      if (!path) return;
      const img = document.createElement('img');
      img.className = 'map-layer';
      img.alt = '地图层 ' + name;
      img.src = assetRoot + '/' + path;
      img.style.zIndex = MAP_LAYER_Z[name] || 1;
      mapEl.appendChild(img);
    });
  } else {
    const mapSrc = (manifest && manifest.asset_root && manifest.map && manifest.map.image)
      ? manifest.asset_root + '/' + manifest.map.image
      : 'art/bg/town_map.png';
    const bg = document.createElement('img');
    bg.className = 'map-bg';
    bg.alt = '俯视小镇地图';
    bg.src = mapSrc;
    bg.onerror = function () {
      // 底图加载失败：退化为纯色占位，居民仍能叠上去
      const placeholder = document.createElement('div');
      placeholder.className = 'map-bg-missing';
      placeholder.textContent = '🏘️ 小镇地图（图片缺失）';
      mapEl.insertBefore(placeholder, mapEl.firstChild);
      bg.remove();
    };
    mapEl.appendChild(bg);
  }

  /* 没有快照也把居民画上（用 manifest 全量居民，站到各站点） */
  const world = (snapshot && snapshot.world) || {};
  const hub = world.location_hub || {};
  const summary = world.residents_summary || {};

  /* ---------- 2) 在地图上铺居民 ---------- */
  // 每位居民一个渲染对象，便于微散步动画驱动
  const residents = [];

  // 没有 location_hub 时，默认一个 site 一个居民，尽量把 6 个都放上去
  function defaultHubKeys() {
    const keys = Object.keys(RESIDENTS);
    const siteKeys = Object.keys(SITES);
    const out = {};
    keys.forEach((k, i) => { out[k] = siteKeys[i % siteKeys.length] || Object.keys(fallbackSites)[0]; });
    return out;
  }
  const effectiveHub = Object.keys(hub).length ? hub : defaultHubKeys();

  // 按「站点」分组，以便同站错开
  const residentsOfSite = {};
  const residentKeys = Object.keys(RESIDENTS);
  const placed = new Set();
  residentKeys.forEach(rk => {
    const siteId = effectiveHub[rk];
    const group = residentKeys.filter(r => effectiveHub[r] === siteId);
    // 稳定排序，保证错开顺序固定；把不认识的 key 也计入
    (residentsOfSite[siteId] = residentsOfSite[siteId] || []).push(rk);
  });

  residentKeys.forEach(rk => {
    const meta = RESIDENTS[rk];
    const cn = (meta && meta.cn) || rk;
    let siteId = effectiveHub[rk];
    // 站点不认得 → 兜底置中
    if (!SITES[siteId]) siteId = null;

    // 计算站位坐标（地图 px），同站多居民横向错开
    let standX, standY;
    if (siteId && SITES[siteId].stand) {
      const stand = SITES[siteId].stand;
      standX = stand[0];
      standY = stand[1];
      const group = (residentsOfSite[siteId] || [rk]);
      const n = group.length;
      const i = group.indexOf(rk);
      if (n > 1) {
        // 错开 ±28px，别重叠；n 为奇数时居中者不动
        standX += (i - (n - 1) / 2) * 30;
      }
    } else {
      standX = MW / 2;
      standY = MH / 2;
    }

    const resEl = document.createElement('div');
    resEl.className = 'resident';
    // 数据绑定到元素，供微散步使用
    resEl.__pos = { baseX: standX, baseY: standY, x: standX, y: standY, rk: rk, dir: 0 };

    // 站立初始方向（向下）
    const dirRow = 0;

    // 气泡内容
    const s = summary[rk] || {};
    const mood = typeof s.mood === 'number' ? s.mood : null;
    let title = (typeof s.title === 'string' && s.title.trim()) ? s.title.trim() : '';
    // 去掉极啰嗦的占位符，安静占位
    if (/^（本回合.*留在原地。\)?$/.test(title)) title = '';
    const emotion = s.emotion || '';
    const emotionSym = EMOTE_SYM[emotion] || (s.emotion ? '🙂' : '');

    const moodDot = mood != null
      ? `<span class="mood-dot" style="background:${moodColor(mood)}" title="mood:${mood}"></span>`
      : '';
    const bubbleBody = (title || !moodDot)
      ? `${moodDot}${escapeHtml(title || '🌿 安静地待着')}`
      : `${moodDot}`;
    const bubbleCls = title ? '' : ' no-title';

    // 纸娃娃：meta.parts（四层路径，已含 asset_root 前缀）优先；否则退化单张 sprite；再不行 emoji 占位
    const parts = (meta && meta.parts && typeof meta.parts === 'object') ? meta.parts : null;
    const partKeys = parts ? Object.keys(parts) : [];
    const spritePath = (meta && meta.sprite) || '';
    const fallbackFace = FALLBACK_FACES[rk] || '🫥';
    resEl.innerHTML = `
      <div class="bubble${bubbleCls}${emotionSym ? '' : ''}">${bubbleBody}</div>
      <div class="sprite" data-rk="${escapeHtml(rk)}"></div>
      <div class="pname">${escapeHtml(cn)}</div>
      ${emotionSym ? `<div class="emote-ico" title="${escapeHtml(emotion)}">${emotionSym}</div>` : ''}
    `;

    const sprEl = resEl.querySelector('.sprite');
    if (partKeys.length) {
      // 四层部件按 z 顺序叠在同一格，共享同一方向行 + 走路帧动画
      const zOrder = (manifest && manifest.sprite_sheets && Array.isArray(manifest.sprite_sheets.part_z_order))
        ? manifest.sprite_sheets.part_z_order.filter(p => parts[p])
        : partKeys;
      zOrder.forEach(partKey => {
        const path = parts[partKey];
        if (!path) return;
        const p = document.createElement('div');
        p.className = 'part';
        p.dataset.part = partKey;
        p.style.backgroundImage = `url('${path}')`;
        sprEl.appendChild(p);
      });
      setDir(sprEl, dirRow, ROW_ORDER);
      // 任一部件加载失败 → 自愈为 emoji 占位（不崩、不留隐形小人）
      const probe = new Image();
      let failed = false;
      probe.onload = function () { /* 部件正常 */ };
      probe.onerror = function () {
        if (failed || !sprEl.parentNode) return;
        failed = true;
        sprEl.removeAttribute('style');
        sprEl.innerHTML = '';
        sprEl.classList.remove('sprite');
        sprEl.classList.add('sprite-missing');
        sprEl.textContent = fallbackFace;
      };
      probe.src = zOrder[0] ? parts[zOrder[0]] : (partKeys[0] ? parts[partKeys[0]] : '');
    } else if (spritePath) {
      // 旧单张 spritesheet
      sprEl.classList.add('sprite-solo');
      sprEl.style.backgroundImage = `url('${spritePath}')`;
      setDir(sprEl, dirRow, ROW_ORDER);
      const probe = new Image();
      probe.onload = function () { /* sheet 正常加载 */ };
      probe.onerror = function () {
        if (!sprEl.parentNode) return;
        sprEl.removeAttribute('style');
        sprEl.classList.remove('sprite', 'sprite-solo');
        sprEl.classList.add('sprite-missing');
        sprEl.textContent = fallbackFace;
      };
      probe.src = spritePath;
    } else {
      sprEl.classList.remove('sprite');
      sprEl.classList.add('sprite-missing');
      sprEl.textContent = fallbackFace;
    }

    applyPos(resEl);
    mapEl.appendChild(resEl);

    residents.push({ el: resEl, rk: rk, cn: cn, mood: mood, emotionSym: emotionSym });
  });

  /* ---------- 3) 微散步：居民在站点附近小范围随机走动 ---------- */
  setupMicroWalk(residents, MW, MH, ROW_ORDER);

  /* ---------- 4) 底部：小镇动态 ---------- */
  const rawEvents = (snapshot && snapshot.events && Array.isArray(snapshot.events))
    ? snapshot.events
    : [];
  const entries = rawEvents.slice(-50).reverse();

  if (!entries.length) {
    eventsUl.innerHTML = '<li class="timeline-empty">📮 还没有大事发生，居民都在安静过自己的日子。</li>';
  } else {
    eventsUl.innerHTML = entries.map(e => {
      const who = (e.actor && RESIDENTS[e.actor]) ? RESIDENTS[e.actor].cn : (e.actor || '某人');
      const loc = e.location ? (SITES[e.location] ? SITES[e.location].cn : e.location) : '';
      const bits = [];
      if (e.date)  bits.push(`<span class="tl-badge">${escapeHtml(e.date)}</span>`);
      if (e.phase) bits.push(`<span class="tl-badge tl-phase">${escapeHtml(e.phase)}</span>`);
      if (loc)     bits.push(`<span class="tl-badge tl-site">📍${escapeHtml(loc)}</span>`);
      bits.push(`<span class="tl-who">${escapeHtml(who)}</span>`);
      return `
        <li class="timeline-item">
          <div class="tl-meta">${bits.join('')}</div>
          <div class="tl-summary">${escapeHtml(e.summary || '（无内容）')}</div>
        </li>`;
    }).join('');
  }

  /* =========================================================
     工具函数
     ========================================================= */

  // 融合 manifest 与兜底表：manifest 优先（含正确中文名与 sprite 相对路径）
  function buildResidents(mf, fallback, assetRoot) {
    const out = {};
    const src = (mf && mf.residents) ? mf.residents : {};
    Object.keys(fallback).forEach(k => {
      out[k] = Object.assign({}, fallback[k]);
    });
    if (typeof src === 'object' && src) {
      Object.keys(src).forEach(k => {
        const v = src[k];
        if (!v) return;
        const sprite = (typeof v.sprite === 'string' && v.sprite) ? assetRoot + '/' + v.sprite : (out[k] ? out[k].sprite : '');
        // 纸娃娃四层（hair/top/bottom/shoes），每层路径都拼上 asset_root
        const parts = {};
        if (v.parts && typeof v.parts === 'object') {
          Object.keys(v.parts).forEach(p => {
            if (typeof v.parts[p] === 'string' && v.parts[p]) parts[p] = assetRoot + '/' + v.parts[p];
          });
        }
        out[k] = { cn: (v.cn || (out[k] && out[k].cn) || k), sprite: sprite, parts: parts };
      });
    }
    return out;
  }

  // 融合站点：manifest.stand 与 cn 优先
  function buildSites(mf, fallback) {
    const out = {};
    const src = (mf && mf.sites) ? mf.sites : {};
    Object.keys(fallback).forEach(k => {
      out[k] = { cn: fallback[k].cn, stand: null };
    });
    if (typeof src === 'object' && src) {
      Object.keys(src).forEach(k => {
        const v = src[k];
        if (!v) return;
        out[k] = {
          cn: (typeof v.cn === 'string' && v.cn) ? v.cn : ((out[k] && out[k].cn) || k),
          stand: (Array.isArray(v.stand) && v.stand.length >= 2)
            ? [Number(v.stand[0]) || 0, Number(v.stand[1]) || 0]
            : (out[k] ? out[k].stand : null),
        };
      });
    }
    return out;
  }

  // 按方向设置 sprite 的 background-position-y（行号）
  function setDir(sprEl, dirIndex, rowOrder) {
    const idx = typeof dirIndex === 'number' ? dirIndex : rowOrder.indexOf('down');
    const y = (-idx * 96) + 'px';
    const parts = sprEl.querySelectorAll('.part');
    if (parts.length) {
      parts.forEach(p => { p.style.backgroundPositionY = y; });
    } else {
      sprEl.style.backgroundPositionY = y;
    }
  }

  // 用「脚底」位置更新元素 left/top（百分比），translate 负责底部锚点
  function applyPos(resEl) {
    const p = resEl.__pos;
    resEl.style.left = (p.x / MW * 100) + '%';
    resEl.style.top = (p.y / MH * 100) + '%';
  }

  // mood 0~1 → 绿 / 黄 / 红
  function moodColor(m) {
    if (m >= 0.65) return '#7fe089';
    if (m >= 0.35) return '#e8d06a';
    return '#ef7a66';
  }

  // 微散步：每个居民周期性挑方向走几步，脚步则切 sprite 行
  function setupMicroWalk(residents, mw, mh, rowOrder) {
    if (!MW || !MH) return;
    const DIRS = [
      { dx: 0,  dy: -1, row: rowOrder.indexOf('up') },    // 上
      { dx: 0,  dy: 1,  row: rowOrder.indexOf('down') },  // 下
      { dx: -1, dy: 0,  row: rowOrder.indexOf('left') },  // 左
      { dx: 1,  dy: 0,  row: rowOrder.indexOf('right') }, // 右
    ];
    const STEP_PX = 3.5;      // 每步在地图 px（1280 坐标系）上的移动量
    const MAX_OFF = 26;       // 最大偏离站点距离，超了就往回走
    const STEP_MS = 70;       // 每步间隔

    let walking = [];

    function stepOnce(rec) {
      // rec: { rk, x, y, baseX, baseY, facing }  当前已偏离量
      const dxWorld = rec.x - rec.baseX;
      const dyWorld = rec.y - rec.baseY;
      const dist = Math.abs(dxWorld) + Math.abs(dyWorld);

      // 选方向：若离得太远，强制走回中心；否则随机走一个相邻方向
      let d;
      if (dist >= MAX_OFF) {
        // 朝基地方向走
        d = Math.abs(dxWorld) > 0
          ? (dxWorld > 0 ? DIRS[3] : DIRS[2])
          : (dyWorld > 0 ? DIRS[1] : DIRS[0]);
      } else {
        d = DIRS[(Math.random() * 4) | 0];
      }

      let nx = rec.x + d.dx * STEP_PX;
      let ny = rec.y + d.dy * STEP_PX;
      // 地图边界限制
      nx = Math.max(10, Math.min(mw - 10, nx));
      ny = Math.max(10, Math.min(mh - 10, ny));

      // 切方向行 + 移动
      const el = residents.find(r => r.rk === rec.rk);
      if (el) {
        const spr = el.el.querySelector('.sprite');
        if (spr && !spr.classList.contains('sprite-missing')) {
          const row = (d.row >= 0) ? d.row : 0;
          setDir(spr, row, rowOrder);
        }
        el.el.__pos.x = nx;
        el.el.__pos.y = ny;
        applyPos(el.el);
      }

      rec.x = nx;
      rec.y = ny;
      rec.remaining--;
      if (rec.remaining > 0) {
        rec.timer = setTimeout(() => stepOnce(rec), STEP_MS);
      } else {
        // 走完回站：平滑归来
        rec.homeTimer = setTimeout(() => goHome(rec), 120);
      }
    }

    function goHome(rec) {
      const el = residents.find(r => r.rk === rec.rk);
      if (!el) return;
      // 直接回到站位（脚底），并把方向行切回 down
      el.el.__pos.x = rec.baseX;
      el.el.__pos.y = rec.baseY;
      applyPos(el.el);
      const spr = el.el.querySelector('.sprite');
      if (spr && !spr.classList.contains('sprite-missing')) {
        setDir(spr, rowOrder.indexOf('down'), rowOrder);
      }
    }

    // 每 3~5.5s 给某位居民安排一次 4~9 步的微散步（错峰）
    setInterval(() => {
      if (!residents.length) return;
      // 避免多人同时动，一次只挑 1~2 位
      const count = 1 + ((Math.random() * 2) | 0);
      const indices = [];
      for (let i = 0; i < residents.length && indices.length < count; i++) {
        if (Math.random() < 0.6) indices.push(i);
      }
      if (!indices.length) indices.push((Math.random() * residents.length) | 0);

      indices.forEach(i => {
        const r = residents[i];
        const key = r.rk;
        if (walking.includes(key)) return;
        walking.push(key);
        const pos = r.el.__pos;
        const rec = {
          rk: key, x: pos.x, y: pos.y,
          baseX: pos.baseX, baseY: pos.baseY, remaining: 4 + ((Math.random() * 6) | 0),
        };
        rec.timer = setTimeout(() => {
          stepOnce(rec);
          const k = walking.indexOf(key);
          if (k >= 0) walking.splice(k, 1);
        }, STEP_MS);
      });
    }, 4200);
  }

  // HTML 转义
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
})();
