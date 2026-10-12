/* ============ 月老姻缘 · 前端逻辑 ============ */
"use strict";

const $ = (s, el) => (el || document).querySelector(s);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const ZODIAC_LIST = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];
const SEX_OPTIONS = ["男", "女"];

const MODES = {
  hehun: {
    title: "八字合婚", sub: "双方生辰八字，六维加权评分（天干 / 地支 / 日柱 / 五行 / 纳音）",
    fields: [
      { k: "a_date", label: "你的生日", type: "date", required: true },
      { k: "a_hour", label: "你的出生时刻", type: "time", def: "12:00" },
      { k: "a_sex", label: "你的性别", type: "select", options: SEX_OPTIONS, def: "男" },
      { k: "b_date", label: "对方生日", type: "date", required: true },
      { k: "b_hour", label: "对方出生时刻", type: "time", def: "12:00" },
      { k: "b_sex", label: "对方性别", type: "select", options: SEX_OPTIONS, def: "女" },
    ],
    submit: "开始合婚",
    api: "/api/hehun",
    collect: (f) => ({
      a_date: f.a_date, a_hour: +(f.a_hour || "12:00").split(":")[0], a_minute: +((f.a_hour || "12:00").split(":")[1] || 0), a_sex: f.a_sex,
      b_date: f.b_date, b_hour: +(f.b_hour || "12:00").split(":")[0], b_minute: +((f.b_hour || "12:00").split(":")[1] || 0), b_sex: f.b_sex,
    }),
    render: renderHehun, badge: "八字合婚",
  },
  zodiac: {
    title: "生肖配对", sub: "六合 / 三合 / 六冲 / 六害，一查便知",
    fields: [
      { k: "a_zodiac", label: "你的生肖", type: "select", options: ZODIAC_LIST, required: true },
      { k: "b_zodiac", label: "对方生肖", type: "select", options: ZODIAC_LIST, required: true },
    ],
    submit: "查看配对",
    api: "/api/zodiac",
    collect: (f) => ({ a_zodiac: f.a_zodiac, b_zodiac: f.b_zodiac }),
    render: renderZodiac, badge: "生肖配对",
  },
  ziwei: {
    title: "紫微夫妻宫", sub: "安星布局，看命盘里的婚姻格局",
    fields: [
      { k: "date", label: "出生日期", type: "date", required: true },
      { k: "hour", label: "出生时刻", type: "time", def: "12:00" },
      { k: "sex", label: "性别", type: "select", options: SEX_OPTIONS, def: "男" },
    ],
    submit: "排夫妻宫",
    api: "/api/ziwei",
    collect: (f) => ({ date: f.date, hour: +(f.hour || "12:00").split(":")[0], minute: +((f.hour || "12:00").split(":")[1] || 0), sex: f.sex }),
    render: renderZiwei, badge: "紫微夫妻宫",
  },
  taohua: {
    title: "桃花运势", sub: "本命桃花位 · 旺月 · 流年桃花一表看清",
    fields: [
      { k: "year", label: "出生年份", type: "number", def: "1995", min: 1900, max: 2020, required: true },
      { k: "status", label: "当前感情状态", type: "select", options: ["单身", "暗恋中", "恋爱中", "已婚", "顺其自然"] },
    ],
    submit: "查看桃花",
    api: "/api/taohua",
    collect: (f) => ({ year: +f.year, status: f.status && f.status !== "顺其自然" ? f.status : "" }),
    render: renderTaohua, badge: "桃花运势",
  },
  hongxian: {
    title: "红线测算", sub: "正缘画像 + 未来八年缘分时间窗",
    fields: [
      { k: "date", label: "你的生日", type: "date", required: true },
      { k: "hour", label: "出生时刻", type: "time", def: "12:00" },
      { k: "sex", label: "性别", type: "select", options: SEX_OPTIONS, def: "男" },
      { k: "expect", label: "你的期待（可选）", type: "text", placeholder: "如：脱单 / 异地 / 结婚 / 复合 / 暗恋" },
    ],
    submit: "牵起红线",
    api: "/api/hongxian",
    collect: (f) => ({ date: f.date, hour: +(f.hour || "12:00").split(":")[0], minute: +((f.hour || "12:00").split(":")[1] || 0), sex: f.sex, expect: f.expect || "" }),
    render: renderHongxian, badge: "红线测算",
  },
  qiuqian: {
    title: "求签问姻缘", sub: "心诚则灵 · 同一天同一问题得同一支签",
    fields: [
      { k: "name", label: "你的称呼（可选）", type: "text", placeholder: "如：阿明" },
      { k: "question", label: "想问的姻缘问题", type: "text", placeholder: "如：何时能遇到对的人？", required: true },
    ],
    submit: "诚心求签",
    api: "/api/qiuqian",
    collect: (f) => ({ name: f.name || "", question: f.question }),
    render: renderQian, badge: "姻缘签",
  },
};

/* ---------------- 表单定义 ---------------- */

/* ---------------- 弹窗 ---------------- */
const mask = $("#modal-mask"), formEl = $("#modal-form"), resEl = $("#modal-result");
let currentMode = null;

function openMode(key, preset) {
  const m = MODES[key];
  currentMode = m;
  $("#modal-title").textContent = m.title;
  formEl.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "form-grid";
  m.fields.forEach((f) => {
    const wrap = document.createElement("div");
    wrap.className = "field" + (f.full ? " full" : "");
    const id = "f-" + f.k;
    let input;
    if (f.type === "select") {
      input = document.createElement("select");
      f.options.forEach((o) => {
        const opt = document.createElement("option");
        opt.value = o; opt.textContent = o;
        if (f.def && o === f.def) opt.selected = true;
        input.appendChild(opt);
      });
    } else {
      input = document.createElement("input");
      input.type = f.type || "text";
      if (f.def) input.value = f.def;
      if (f.placeholder) input.placeholder = f.placeholder;
      if (f.min) input.min = f.min;
      if (f.max) input.max = f.max;
    }
    input.id = id;
    input.name = f.k;
    if (f.required) input.required = true;
    const label = document.createElement("label");
    label.htmlFor = id;
    label.textContent = f.label + (f.required ? " *" : "");
    wrap.appendChild(label); wrap.appendChild(input);
    grid.appendChild(wrap);
  });
  formEl.appendChild(grid);
  const actions = document.createElement("div");
  actions.className = "form-actions";
  actions.innerHTML = '<button type="submit" class="btn-primary">' + m.submit + '</button>';
  formEl.appendChild(actions);
  const err = document.createElement("div");
  err.className = "form-error"; err.id = "form-error";
  formEl.appendChild(err);

  resEl.hidden = true; resEl.innerHTML = "";
  if (preset) { // 预填（首页合婚入口）
    for (const [k, v] of Object.entries(preset)) {
      const el = formEl.querySelector('[name="' + k + '"]');
      if (el) el.value = v;
    }
  }
  mask.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeModal() { mask.hidden = true; document.body.style.overflow = ""; }
$("#modal-close").addEventListener("click", closeModal);
mask.addEventListener("click", (e) => { if (e.target === mask) closeModal(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });

document.querySelectorAll(".mode-card").forEach((btn) => {
  btn.addEventListener("click", () => openMode(btn.dataset.mode));
});

/* ---------------- 提交 ---------------- */
formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = $("#form-error");
  errEl.textContent = "";
  const data = {};
  new FormData(formEl).forEach((v, k) => (data[k] = v));
  const btn = formEl.querySelector('button[type="submit"]');
  btn.disabled = true; btn.textContent = "测算中…";
  try {
    const payload = currentMode.collect(data);
    const res = await fetch(currentMode.api, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "测算失败");
    showResult(json);
  } catch (ex) {
    errEl.textContent = ex.message;
  } finally {
    btn.disabled = false; btn.textContent = currentMode.submit;
  }
});

function showResult(json) {
  const html = currentMode.render(json, currentMode.badge);
  resEl.innerHTML = html;
  resEl.hidden = false;
  appendReport(html);
}

function appendReport(html) {
  $("#report-empty").style.display = "none";
  const list = $("#report-list");
  const div = document.createElement("div");
  div.innerHTML = html;
  list.insertBefore(div, list.firstChild);
  // 只保留最近 6 份
  while (list.children.length > 6) list.removeChild(list.lastChild);
}

/* ---------------- 渲染器 ---------------- */
function ring(score, label) {
  const r = 54, c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const off = c * (1 - pct);
  return '<div class="score-ring">' +
    '<svg width="130" height="130" viewBox="0 0 130 130">' +
    '<circle cx="65" cy="65" r="' + r + '" fill="none" stroke="#f0e6d8" stroke-width="10"/>' +
    '<circle cx="65" cy="65" r="' + r + '" fill="none" stroke="#b03a2e" stroke-width="10" stroke-linecap="round" stroke-dasharray="' + c + '" stroke-dashoffset="' + off + '"/>' +
    '</svg><div class="num"><b>' + score + "</b><span>" + esc(label || "分") + "</span></div></div>";
}

function card(title, badge, inner) {
  return '<div class="report-card"><h3>' + esc(title) +
    (badge ? '<span class="badge">' + esc(badge) + "</span>" : "") +
    "</h3>" + inner + "</div>";
}

function renderHehun(r) {
  const dims = r.dimensions.map((d) =>
    '<div class="dim-row"><span class="name">' + esc(d.name) + '</span><span class="bar"><i style="width:' +
    Math.round((d.score / d.full) * 100) + '%"></i></span><span class="val">' + d.score + "/" + d.full + "</span></div>"
  ).join("");
  const pil = (p, who) =>
    '<div class="pillars">' + ["year", "month", "day", "hour"].map((k) => {
      const names = { year: "年柱", month: "月柱", day: "日柱", hour: "时柱" };
      return '<div class="pillar"><em>' + names[k] + "·" + who + "</em><b>" + esc(p[k][0] + p[k][1]) + "</b></div>";
    }).join("") + "</div>";

  const inner =
    '<div class="score-wrap">' + ring(r.score) +
    '<div class="score-side"><div class="grade">' + esc(r.grade) + '</div><div class="desc">' + esc(r.grade_desc) + "</div></div></div>" +
    dims +
    '<div class="pillars-note" style="text-align:center;color:var(--ink-2);font-size:13px;margin-top:10px">双方命盘</div>' +
    pil(r.a, "你方") + pil(r.b, "对方") +
    '<ul class="notes">' + r.notes.map((n) => "<li>" + esc(n) + "</li>").join("") + "</ul>" +
    '<div class="report-foot">' + esc(r.summary) + "</div>";
  return card("八字合婚报告", "八字合婚", inner);
}

function renderZodiac(r) {
  const inner =
    '<div class="score-wrap">' + ring(r.score) +
    '<div class="score-side"><div class="grade">' + esc(r.a.zodiac) + " × " + esc(r.b.zodiac) + "</div>" +
    '<div class="stars">' + r.stars + "</div>" +
    '<div class="desc">' + esc(r.level_text) + " · " + esc(r.relation) + "</div></div></div>" +
    '<div class="kv"><b>关系</b><span>' + esc(r.title) + "</span></div>" +
    '<div class="kv"><b>解读</b><span>' + esc(r.text) + "</span></div>" +
    '<div class="kv"><b>月老建议</b><span>' + esc(r.advice) + "</span></div>" +
    '<div class="report-foot">六冲不代表不合，冲撞中也能找到平衡——关键在于是否愿意磨合。</div>';
  return card("生肖配对报告", "生肖配对", inner);
}

function renderZiwei(r) {
  const interp = r.interp.map((s) =>
    '<div style="margin:14px 0 4px"><div class="grade" style="font-family:var(--serif);font-size:20px;color:var(--red)">' +
    esc(s.star) + " 坐夫妻宫</div>" +
    '<div class="kv"><b>配偶特征</b><span>' + esc(s.mate) + "</span></div>" +
    '<div class="kv"><b>感情模式</b><span>' + esc(s.mode) + "</span></div>" +
    '<div class="kv"><b>感情课题</b><span>' + esc(s.lesson) + "</span></div>" +
    '<div class="kv"><b>月老建议</b><span>' + esc(s.advice) + "</span></div></div>"
  ).join("");
  const goods = Object.entries(r.good_effects || {}).map(([k, v]) => '<div class="kv"><b>吉星·' + esc(k) + "</b><span>" + esc(v) + "</span></div>").join("");
  const bads = Object.entries(r.bad_effects || {}).map(([k, v]) => '<div class="kv"><b>煞星·' + esc(k) + "</b><span>" + esc(v[0]) + "（化解：" + esc(v[1]) + "）</span></div>").join("");
  const sihua = (r.sihua_hits || []).map((h) => '<span class="tag">' + esc(h.star + "化" + h.hua) + "</span>").join("");
  const pattern = (r.pattern || []).map((p) => '<div class="kv"><b>格局</b><span>' + esc(p) + "</span></div>").join("");
  const inner =
    '<div class="kv"><b>出生</b><span>' + esc(r.lunar) + "（" + esc(r.solar) + "）</span></div>" +
    '<div class="kv"><b>命宫</b><span>' + esc(r.ming_gong.gan + r.ming_gong.zhi) + " · 身宫" + esc(r.shen_gong.zhi) + " · " + esc(r.wuxing_ju) + "</span></div>" +
    '<div class="kv"><b>夫妻宫</b><span>' + esc(r.fuchi.gan + r.fuchi.zhi) + "（对宫 " + esc(r.fuchi.duigong) + "）· 主星：" +
    (r.main_stars.length ? esc(r.main_stars.join("、")) : "空宫，借对宫") + "</span></div>" +
    interp + goods + bads + pattern +
    (sihua ? '<div style="margin-top:8px"><b style="font-size:13px;color:var(--ink-2)">生年四化入夫妻宫：</b>' + sihua + "</div>" : "") +
    '<div class="report-foot">' + esc(r.note) + "</div>";
  return card("紫微夫妻宫报告", "紫微夫妻宫", inner);
}

function renderTaohua(r) {
  const inner =
    '<div class="score-wrap">' + ring(r.stars_n * 20, "桃花") +
    '<div class="score-side"><div class="grade">' + esc(r.zodiac) + " · " + esc(r.flow_gz) + "年</div>" +
    '<div class="stars">' + r.stars + "</div>" +
    '<div class="desc">' + esc(r.brief) + "</div></div></div>" +
    '<div class="kv"><b>本命桃花位</b><span>' + esc(r.taohua_pos.fangwei) + "（" + esc(r.taohua_pos.zhi) + "）· " + esc(r.taohua_pos.meaning) + "</span></div>" +
    '<div class="kv"><b>旺桃花月份</b><span>' + esc(r.peak_months.join("、")) + " — 多社交</span></div>" +
    '<div class="kv"><b>需要安静的月份</b><span>' + esc(r.bad_month) + " — 不宜冲动表白</span></div>" +
    '<div class="kv"><b>桃花类型</b><span>' + esc(r.tao_type) + "</span></div>" +
    '<div class="kv"><b>开运色</b><span>' + esc(r.lucky_color) + " — " + esc(r.lucky_color_reason) + "</span></div>" +
    '<div class="kv"><b>行动建议</b><span>' + esc(r.status_tip) + "</span></div>" +
    '<div class="report-foot">月老寄语：' + esc(r.jiyu) + "</div>";
  return card(r.flow_year + " 桃花运势报告", "桃花运势", inner);
}

function renderHongxian(r) {
  const tl = r.timeline.map((t) =>
    '<div class="tl-row' + (t.score >= 3 ? " hot" : "") + '"><b>' + t.year + "</b><span class='tags'>" +
    (t.tags.length ? t.tags.map(esc).join("；") : "平淡经营") + "</span></div>"
  ).join("");
  const strong = r.strong_years.map((t) => '<span class="tag">' + t.year + " " + esc(t.tags[0] || "") + "</span>").join("");
  const inner =
    '<div class="score-wrap">' + ring(r.fate_index, "缘分") +
    '<div class="score-side"><div class="grade">日柱 ' + esc(r.day_pillar) + "</div>" +
    '<div class="desc">' + esc(r.portrait.desc) + "</div></div></div>" +
    '<div class="kv"><b>正缘性格</b><span>' + esc(r.portrait.trait) + "</span></div>" +
    '<div class="kv"><b>外貌倾向</b><span>' + esc(r.portrait.look) + "</span></div>" +
    '<div class="kv"><b>职业倾向</b><span>' + esc(r.portrait.career) + "</span></div>" +
    '<div class="kv"><b>本命桃花位</b><span>' + esc(r.taohua_pos.fangwei) + "（" + esc(r.taohua_pos.zhi) + "）— " + esc(r.taohua_pos.meaning) + "</span></div>" +
    '<div style="margin-top:10px"><b style="font-size:13px;color:var(--ink-2)">未来八年重点年份：</b>' + (strong || '<span class="tag gray">未来几年以平稳经营为主</span>') + "</div>" +
    '<div class="tl">' + tl + "</div>" +
    '<div class="kv" style="margin-top:10px"><b>月老建议</b><span>' + esc(r.advice) + "</span></div>" +
    '<div class="report-foot">' + esc(r.footer) + "</div>";
  return card("红线测算报告", "红线测算", inner);
}

function renderQian(r) {
  const inner =
    '<div class="qian-card">' +
    '<div class="qian-no">' + esc(r.no_cn) + "</div>" +
    '<div class="qian-level">' + esc(r.level) + "</div>" +
    '<div class="qian-poem">' + esc(r.poem) + "</div>" +
    (r.jie ? '<div class="qian-jie"><b>签解</b>' + esc(r.jie) + "</div>" : "") +
    (r.yuan ? '<div class="qian-jie"><b>姻缘</b>' + esc(r.yuan) + "</div>" : "") +
    '<div class="qian-jie"><b>签意</b>' + esc(r.meaning) + "</div>" +
    '<div class="report-foot">' + esc(r.footer) + "（" + esc(r.date) + " " + esc(r.shichen) + "时）</div></div>";
  return card("姻缘签 · " + r.no_cn, "姻缘签", inner);
}

/* ---------------- 首页合婚入口 ---------------- */
$("#hero-go").addEventListener("click", () => {
  const a = $("#hero-a").value, b = $("#hero-b").value;
  if (!a || !b) {
    openMode("hehun");
    $("#form-error").textContent = "请先填好双方生日";
    return;
  }
  openMode("hehun", { a_date: a, b_date: b });
  formEl.requestSubmit();
});
[$("#hero-a"), $("#hero-b")].forEach((el) =>
  el.addEventListener("keydown", (e) => { if (e.key === "Enter") $("#hero-go").click(); })
);

/* ---------------- 求签专区 ---------------- */
$("#qian-go").addEventListener("click", async () => {
  const name = $("#qian-name").value.trim();
  const question = $("#qian-question").value.trim();
  if (!question) { $("#qian-question").focus(); $("#qian-question").placeholder = "先写下你想问的问题吧～"; return; }
  const btn = $("#qian-go");
  btn.disabled = true; btn.textContent = "摇签中…";
  try {
    const res = await fetch("/api/qiuqian", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, question }),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "求签失败");
    const html = renderQian(json);
    appendReport(html);
    openMode("qiuqian", { name, question });
    resEl.innerHTML = html; resEl.hidden = false;
    $("#qian-question").value = "";
  } catch (ex) {
    alert(ex.message);
  } finally {
    btn.disabled = false; btn.textContent = "诚心求签";
  }
});

/* ---------------- 导航高亮 ---------------- */
const secIds = ["home", "cesuan", "qiuqian", "baogao"];
window.addEventListener("scroll", () => {
  let cur = "home";
  secIds.forEach((id) => {
    const el = document.getElementById(id);
    if (el && el.getBoundingClientRect().top < 140) cur = id;
  });
  document.querySelectorAll(".links a").forEach((a) => {
    a.classList.toggle("active", a.getAttribute("href") === "#" + cur);
  });
}, { passive: true });
