/* =========================================================
   万森小镇 · 前端（只读快照渲染 Q版小镇）
   数据源：snapshot.json（引擎每次过活后导出的静态快照）
   ========================================================= */
(async () => {
  /* ---------- 常量映射表（相对路线，web/ 自包含，供 GitHub Pages 用） ---------- */
  // 站点 id → 中文名 + 背景图相对路径
  const SITES = {
    town_hall: { cn: '市政厅', bg: 'art/bg/town_hall.png' },
    teahouse:  { cn: '茶馆',   bg: 'art/bg/teahouse.png' },
    gym:       { cn: '健身房', bg: 'art/bg/gym.png' },
    canteen:   { cn: '食堂',   bg: 'art/bg/canteen.png' },
    stage:     { cn: '舞台',   bg: 'art/bg/stage.png' },
    sysroom:   { cn: '机房',   bg: 'art/bg/sysroom.png' },
  };
  // 站点（顺序即卡片排列顺序；万一快照里没有，也保证 6 张卡都在）
  const SITE_ORDER = ['town_hall', 'teahouse', 'gym', 'canteen', 'stage', 'sysroom'];

  // 居民 key（location_hub 的 key）→ 中文名 + 表情 emote 相对路径
  const EMOTES = {
    calm: 'art/emotes/calm.png',
    amused: 'art/emotes/amused.png',
    happy: 'art/emotes/happy.png',
    annoyed: 'art/emotes/annoyed.png',
    tired: 'art/emotes/tired.png',
  };

  // 居民 key → 中文名 + sprite 文件名（去掉 _front.png 的基础名）
  //   注意：美术文件名用的是短 key（Fitness 而非 Fitness Coach、Finance 而非 Financial Advisor）
  const RESIDENTS = {
    'Rei':                { cn: 'Rei',       sprite: 'Rei' },
    'Fitness Coach':      { cn: '健身教练',   sprite: 'Fitness' },
    'Financial Advisor':  { cn: '财经顾问',   sprite: 'Finance' },
    'Entertainment':      { cn: '娱乐助手',   sprite: 'Entertainment' },
    'Ops':                { cn: '运维',       sprite: 'Ops' },
    'Wilde':              { cn: 'Wilde',      sprite: 'Wilde' }, // 中文可叫"骚客"
  };

  // 若某人既无 title 也无正经内容时的占位表情符号
  const FALLBACK_FACES = { 'Rei':'🗂️', 'Fitness Coach':'💪', 'Financial Advisor':'📈',
                           'Entertainment':'🎬', 'Ops':'🛠️', 'Wilde':'📜' };

  /* ---------- 读取快照 ---------- */
  let data = null, fetchErr = null;
  try {
    const res = await fetch('snapshot.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    data = await res.json();
  } catch (e) { fetchErr = e; }

  const $ = id => document.getElementById(id);
  const foot = $('foot'), vinEl = $('vin'), dateEl = $('meta-date'),
        phaseEl = $('meta-phase'), mapEl = $('map'), eventsUl = $('events');

  if (!data) {
    foot.textContent = '⚠️ 未读到 snapshot.json。请先让引擎跑一次 one_tick 生成快照。';
    eventsUl.innerHTML = '<li class="timeline-empty">还没有快照数据。</li>';
    mapEl.innerHTML = '<p class="timeline-empty">暂无地图数据。</p>';
    return;
  }

  const world = data.world || {};

  /* ---------- 顶栏：标题 / 日期 / 时段 / vin ---------- */
  dateEl.textContent  = '📅 ' + (world.today || '未知日期');
  phaseEl.textContent = '⏰ ' + (world.phase || '');
  vinEl.textContent   = '第 ' + (data.vin != null ? data.vin : world.vin != null ? world.vin : 0) + ' 帧';
  foot.textContent = '✅ 已读取静态快照（界面只读，不接触生活引擎）· 契约 iface_v=' + (data.iface_v || '-');

  const hub     = world.location_hub || {};      // 居民 key → 站点 id
  const summary = world.residents_summary || {}; // 居民 key → { mood, title }

  /* ---------- 1) 中部：小镇地图（站点卡片） ---------- */
  // 先按给定顺序渲染 6 张卡（保证地图稳定），再往里填居民
  SITE_ORDER.forEach(siteId => {
    const site = SITES[siteId] || { cn: siteId, bg: '' };

    const card = document.createElement('div');
    card.className = 'site-card';
    card.dataset.site = siteId;

    // 背景：没图就给描边占位
    const bgHTML = site.bg
      ? `<img class="bg" src="${site.bg}" alt="${site.cn}" onerror="this.style.display='none';">`
      : `<div class="bg-missing">${site.cn}</div>`;
    card.innerHTML = `
      <span class="site-name">${site.cn}</span>
      ${bgHTML}
    `;

    // 找出此刻在该站点的居民（可能 0 或多位，如快照里 Rei、Wilde 同在 teahouse）
    const occupants = Object.keys(hub).filter(rid => hub[rid] === siteId);

    if (occupants.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'site-empty';
      empty.textContent = '此刻无人，安安静静。';
      card.appendChild(empty);
    } else {
      // 多位居民时横向排开：index→相对位置（0 靠左 … 居中分布）
      const total = occupants.length;
      occupants.forEach((rid, i) => {
        const s = summary[rid] || {};
        const res = RESIDENTS[rid] || { cn: rid, sprite: '' };
        const mood = typeof s.mood === 'number' ? s.mood : null;
        const title = (typeof s.title === 'string' && s.title.trim()) ? s.title.trim() : '';
        const emotion = s.emotion || 'calm'; // 快照可能没 emotion，默认 calm

        const occ = document.createElement('div');
        occ.className = 'occupant';
        // 水平分布：单人居中(50%)；多人按序均匀分到 22%…78%
        const left = total === 1 ? 50 : (22 + (78 - 22) * (i / (total - 1)));
        occ.style.left = left + '%';
        occ.style.transform = 'translateX(-50%)';

        // 立绘：有 sprite 文件就用图，加载失败时换成占位表情（onerror 自愈）
        const spriteId = 'sp_' + rid.replace(/\s+/g, '_');
        const fallbackFace = FALLBACK_FACES[rid] || '🫥';
        const spriteHTML = res.sprite
          ? `<div class="sprite"><img id="${spriteId}" src="art/sprites/${res.sprite}_front.png" alt="${res.cn}"
                onerror="this.onerror=null;var p=this.parentNode;var d=document.createElement('div');d.className='sprite-missing';d.textContent='${fallbackFace}';p.replaceWith(d);"></div>`
          : `<div class="sprite-missing">${fallbackFace}</div>`;

        // 状态气泡：有 title 用 title，没有用贴心占位
        const bubbleBody = title
          ? `${mood != null ? '<span class="mood-dot" style="background:' + moodColor(mood) + '"></span>' : ''}${escapeHtml(title)}`
          : '<span class="no-title">🌿 正安静地待着</span>';
        const bubble = `<div class="bubble">${bubbleBody}</div>`;

        // 表情角标：有 emote 图用图，否则 emoji
        const emoteHTML = EMOTES[emotion]
          ? `<div class="emote-ico" title="mood:${mood == null ? '?' : mood}"><img src="${EMOTES[emotion]}" alt="${emotion}" onerror="this.remove();"></div>`
          : `<div class="emote-ico emote-sym-frame" title="mood:${mood == null ? '?' : mood}"><span class="emote-sym">😊</span></div>`;

        occ.innerHTML = `${bubble}${spriteHTML}<div class="pname">${escapeHtml(res.cn)}</div>${emoteHTML}`;
        card.appendChild(occ);
      });
    }

    mapEl.appendChild(card);
  });

  /* ---------- 2) 底部：小镇动态（事件时间线） ---------- */
  // 契约：data.events.entries 才是事件数组（旧版误用了 data.events 数组）
  const rawEvents = (data.events && Array.isArray(data.events.entries))
    ? data.events.entries
    : (Array.isArray(data.events) ? data.events : []);
  const entries = rawEvents.slice(-50).reverse(); // 最近 50 条，新的在上

  if (!entries.length) {
    eventsUl.innerHTML = '<li class="timeline-empty">📮 还没有大事发生，居民都在安静过自己的日子。</li>';
  } else {
    eventsUl.innerHTML = entries.map(e => {
      const who   = (e.actor && RESIDENTS[e.actor]) ? RESIDENTS[e.actor].cn : (e.actor || '某人');
      const loc   = e.location ? (SITES[e.location] ? SITES[e.location].cn : e.location) : '';
      const metaBits = [];
      if (e.date)  metaBits.push(`<span class="tl-badge">${escapeHtml(e.date)}</span>`);
      if (e.phase) metaBits.push(`<span class="tl-badge">${escapeHtml(e.phase)}</span>`);
      if (loc)     metaBits.push(`<span class="tl-badge">📍${escapeHtml(loc)}</span>`);
      return `
        <li class="timeline-item">
          <div class="tl-meta">${metaBits.join('')}<span class="tl-who">${escapeHtml(who)}</span></div>
          <div class="tl-summary">${escapeHtml(e.summary || '（无内容）')}</div>
        </li>`;
    }).join('');
  }

  /* ---------- 工具 ---------- */
  function moodColor(m) {
    // mood 0~1 → 绿(舒心)→黄(一般)→红(低落)
    if (m >= 0.65) return '#7fb069';
    if (m >= 0.35) return '#d9b455';
    return '#e2745b';
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
})();
