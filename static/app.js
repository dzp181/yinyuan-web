/* ============ 月老姻缘 · 前端逻辑 ============ */
"use strict";

const $ = (s, el) => (el || document).querySelector(s);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const ZODIAC_LIST = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"];
const SEX_OPTIONS = ["男", "女"];

/* ---------------- 日期组件（年/月/日手动输入 + 时辰下拉） ---------------- */
const SHICHEN_OPTS = [
  ["", "不知道时辰（按午时 12:00）"],
  ["23", "子时 23:00–00:59"], ["1", "丑时 01:00–02:59"], ["3", "寅时 03:00–04:59"],
  ["5", "卯时 05:00–06:59"], ["7", "辰时 07:00–08:59"], ["9", "巳时 09:00–10:59"],
  ["11", "午时 11:00–12:59"], ["13", "未时 13:00–14:59"], ["15", "申时 15:00–16:59"],
  ["17", "酉时 17:00–18:59"], ["19", "戌时 19:00–20:59"], ["21", "亥时 21:00–22:59"],
];

function mkNum(name, ph, val, maxlen) {
  const i = document.createElement("input");
  i.type = "text"; i.inputMode = "numeric"; i.name = name;
  i.placeholder = ph; i.maxLength = maxlen; i.autocomplete = "off";
  if (val) i.value = val;
  return i;
}
/* 生日：年(默认2000)/月/日 三个手动输入框 */
function fillYMD(container, prefix) {
  container.append(
    mkNum(prefix + "-y", "年", "2000", 4),
    mkNum(prefix + "-m", "月", "", 2),
    mkNum(prefix + "-d", "日", "", 2),
  );
}
/* 手动输入拼成 YYYY-MM-DD 并校验（非法日期直接抛错，由表单错误区展示） */
function dstr(d, k) {
  const y = +(d[k + "-y"] || ""), m = +(d[k + "-m"] || ""), dd = +(d[k + "-d"] || "");
  if (!y || !m || !dd) throw new Error("请把生日的年、月、日填完整");
  const thisYear = new Date().getFullYear();
  if (y < 1900 || y > thisYear) throw new Error("年份需在 1900–" + thisYear + " 之间");
  if (m < 1 || m > 12) throw new Error("月份需在 1–12 之间");
  const max = new Date(y, m, 0).getDate();
  if (dd < 1 || dd > max) throw new Error(y + " 年 " + m + " 月没有 " + dd + " 日，请检查");
  return y + "-" + String(m).padStart(2, "0") + "-" + String(dd).padStart(2, "0");
}
const hval = (d, k) => (d[k] === "" || d[k] == null ? 12 : +d[k]);

const MODES = {
  hehun: {
    title: "八字合婚", sub: "双方生辰八字，六维加权评分（天干 / 地支 / 日柱 / 五行 / 纳音）",
    fields: [
      { k: "a_date", label: "你的生日", type: "birth", required: true },
      { k: "a_hour", label: "你的出生时辰（可选）", type: "shichen" },
      { k: "a_sex", label: "你的性别", type: "select", options: SEX_OPTIONS, def: "男" },
      { k: "b_date", label: "对方生日", type: "birth", required: true },
      { k: "b_hour", label: "对方出生时辰（可选）", type: "shichen" },
      { k: "b_sex", label: "对方性别", type: "select", options: SEX_OPTIONS, def: "女" },
    ],
    submit: "开始合婚",
    api: "/api/hehun",
    collect: (f) => ({
      a_date: dstr(f, "a_date"), a_hour: hval(f, "a_hour"), a_minute: 0, a_sex: f.a_sex,
      b_date: dstr(f, "b_date"), b_hour: hval(f, "b_hour"), b_minute: 0, b_sex: f.b_sex,
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
      { k: "date", label: "出生日期", type: "birth", required: true },
      { k: "hour", label: "出生时辰（可选）", type: "shichen" },
      { k: "sex", label: "性别", type: "select", options: SEX_OPTIONS, def: "男" },
    ],
    submit: "排夫妻宫",
    api: "/api/ziwei",
    collect: (f) => ({ date: dstr(f, "date"), hour: hval(f, "hour"), minute: 0, sex: f.sex }),
    render: renderZiwei, badge: "紫微夫妻宫",
  },
  taohua: {
    title: "桃花运势", sub: "本命桃花位 · 旺月 · 流年桃花一表看清",
    fields: [
      { k: "year", label: "出生年份", type: "text", def: "2000", required: true, maxlength: 4, numeric: true },
      { k: "status", label: "当前感情状态", type: "select", options: ["单身", "暗恋中", "恋爱中", "已婚", "顺其自然"] },
    ],
    submit: "查看桃花",
    api: "/api/taohua",
    collect: (f) => {
      const y = +f.year;
      if (!y || y < 1900 || y > new Date().getFullYear()) throw new Error("请填写正确的出生年份（1900–" + new Date().getFullYear() + "）");
      return { year: y, status: f.status && f.status !== "顺其自然" ? f.status : "" };
    },
    render: renderTaohua, badge: "桃花运势",
  },
  hongxian: {
    title: "红线测算", sub: "正缘画像 + 未来八年缘分时间窗",
    fields: [
      { k: "date", label: "你的生日", type: "birth", required: true },
      { k: "hour", label: "出生时辰（可选）", type: "shichen" },
      { k: "sex", label: "性别", type: "select", options: SEX_OPTIONS, def: "男" },
      { k: "expect", label: "你的期待（可选）", type: "text", placeholder: "如：脱单 / 异地 / 结婚 / 复合 / 暗恋" },
    ],
    submit: "牵起红线",
    api: "/api/hongxian",
    collect: (f) => ({ date: dstr(f, "date"), hour: hval(f, "hour"), minute: 0, sex: f.sex, expect: f.expect || "" }),
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
let currentModeKey = null;

function openMode(key, preset) {
  const m = MODES[key];
  currentMode = m;
  currentModeKey = key;
  $("#modal-title").textContent = m.title;
  $("#modal-sub").textContent = m.sub || "";
  formEl.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "form-grid";
  m.fields.forEach((f) => {
    const wrap = document.createElement("div");
    wrap.className = "field" + (f.full ? " full" : "");
    const label = document.createElement("label");
    label.textContent = f.label + (f.required ? " *" : "");
    wrap.appendChild(label);

    if (f.type === "birth") {
      const ymd = document.createElement("div");
      ymd.className = "ymd";
      fillYMD(ymd, f.k);
      wrap.appendChild(ymd);
    } else {
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
      } else if (f.type === "shichen") {
        input = document.createElement("select");
        SHICHEN_OPTS.forEach(([v, t]) => {
          const opt = document.createElement("option");
          opt.value = v; opt.textContent = t;
          input.appendChild(opt);
        });
      } else {
        input = document.createElement("input");
        input.type = f.type || "text";
        if (f.def) input.value = f.def;
        if (f.placeholder) input.placeholder = f.placeholder;
        if (f.maxlength) input.maxLength = f.maxlength;
        if (f.numeric) input.inputMode = "numeric";
        if (f.min) input.min = f.min;
        if (f.max) input.max = f.max;
      }
      input.id = id;
      input.name = f.k;
      if (f.required) input.required = true;
      label.htmlFor = id;
      wrap.appendChild(input);
    }
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
  syncRecord(json);
}

/* 已登录则把测算结果静默保存到云端（失败不影响本次测算） */
function syncRecord(json) {
  if (!state.token) return;
  const summary = json.score != null ? (json.score + " 分 · " + (json.grade || "")) :
    (json.level || json.zodiac || json.fate_index != null ? "缘分指数 " + json.fate_index : "") || "";
  fetch("/api/records", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + state.token },
    body: JSON.stringify({
      mode: currentModeKey, title: currentMode.title + "报告",
      summary: summary, payload: json,
    }),
  }).catch(() => {});
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
    '<div class="pillars-note">你方：' + esc(r.a.lunar) + "　·　对方：" + esc(r.b.lunar) + "</div>" +
    pil(r.a.pillars, "你方") + pil(r.b.pillars, "对方") +
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

/* ---------------- 导航高亮 ---------------- */
const secIds = ["home", "cesuan", "baogao"];
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

/* ---------------- 用户系统（注册 / 登录 / 云同步） ---------------- */
const AUTH_KEY = "yy_token";
const authMask = $("#auth-mask"), recMask = $("#rec-mask");
let authMode = "login";

function authHeaders(extra) {
  const h = Object.assign({ "Content-Type": "application/json" }, extra || {});
  if (state.token) h.Authorization = "Bearer " + state.token;
  return h;
}

async function loadMe() {
  if (!state.token) { state.user = null; renderUserArea(); return; }
  try {
    const r = await fetch("/api/auth/me", { headers: authHeaders() });
    const j = await r.json();
    state.user = j.user || null;
    if (!j.user) { state.token = ""; localStorage.removeItem(AUTH_KEY); }
  } catch (e) {
    state.user = null;
  }
  renderUserArea();
}

function renderUserArea() {
  const el = $("#user-area");
  if (state.user) {
    el.innerHTML =
      '<button class="link-btn" id="btn-rec">我的测算</button>' +
      '<span class="u-mail">' + esc(state.user.email) + "</span>" +
      '<button class="btn-ghost btn-sm" id="btn-logout">退出</button>';
    $("#btn-logout").onclick = doLogout;
    $("#btn-rec").onclick = openRecords;
  } else {
    el.innerHTML =
      '<button class="link-btn" id="btn-login">登录</button>' +
      '<button class="btn-login" id="btn-reg">注册</button>';
    $("#btn-login").onclick = () => openAuth("login");
    $("#btn-reg").onclick = () => openAuth("register");
  }
}

function openAuth(mode) {
  authMode = mode === "register" ? "register" : "login";
  const isLogin = authMode === "login";
  $("#auth-title").textContent = isLogin ? "登录" : "注册";
  $("#auth-sub").textContent = isLogin
    ? "登录后，测算报告会自动保存到你的账号"
    : "注册即登录 · 邮箱仅用于登录，不会收到任何邮件";
  $("#auth-submit").textContent = isLogin ? "登录" : "注册并登录";
  $("#auth-switch-text").textContent = isLogin ? "还没有账号？" : "已经有账号了？";
  $("#auth-switch").textContent = isLogin ? "注册新账号" : "返回登录";
  $("#auth-password").setAttribute("autocomplete", isLogin ? "current-password" : "new-password");
  $("#auth-error").textContent = "";
  authMask.hidden = false;
  setTimeout(() => $("#auth-email").focus(), 30);
}

function closeAuth() { authMask.hidden = true; }
$("#auth-close").onclick = closeAuth;
authMask.addEventListener("click", (e) => { if (e.target === authMask) closeAuth(); });

$("#auth-switch").onclick = () => openAuth(authMode === "login" ? "register" : "login");

$("#auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = $("#auth-email").value.trim();
  const password = $("#auth-password").value;
  const errEl = $("#auth-error"), btn = $("#auth-submit");
  errEl.textContent = "";
  btn.disabled = true; btn.textContent = "处理中…";
  try {
    const r = await fetch(authMode === "login" ? "/api/auth/login" : "/api/auth/register", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "操作失败，请稍后再试");
    state.token = j.token; state.user = j.user;
    localStorage.setItem(AUTH_KEY, j.token);
    $("#auth-password").value = "";
    closeAuth();
    renderUserArea();
  } catch (ex) {
    errEl.textContent = ex.message;
  } finally {
    btn.disabled = false;
    $("#auth-submit").textContent = authMode === "login" ? "登录" : "注册并登录";
  }
});

async function doLogout() {
  if (state.token) {
    try {
      await fetch("/api/auth/logout", { method: "POST", headers: authHeaders() });
    } catch (e) { /* 忽略网络错误，本地照常退出 */ }
  }
  state.token = ""; state.user = null;
  localStorage.removeItem(AUTH_KEY);
  renderUserArea();
}

async function openRecords() {
  recMask.hidden = false;
  const box = $("#rec-list");
  box.innerHTML = '<p class="rec-empty">加载中…</p>';
  let list = [];
  try {
    const r = await fetch("/api/records", { headers: authHeaders() });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "加载失败");
    list = j.records || [];
    if (!list.length) {
      box.innerHTML = '<p class="rec-empty">还没有保存过测算，先去算一份吧～</p>';
      return;
    }
    box.innerHTML = list.map((rec, i) =>
      '<div class="rec-item" data-i="' + i + '">' +
      '<b>' + esc(rec.title) + "</b>" +
      '<span class="rec-sum">' + esc(rec.summary || "") + "</span>" +
      '<span class="rec-time">' + new Date(rec.created_at * 1000).toLocaleString("zh-CN") + "</span>" +
      "</div>").join("");
    box.querySelectorAll(".rec-item").forEach((it) => {
      it.onclick = () => {
        const rec = list[+it.dataset.i];
        const m = MODES[rec.mode];
        if (!m) return;
        try {
          const html = m.render(JSON.parse(rec.payload), m.badge);
          appendReport(html);
          recMask.hidden = true;
          document.getElementById("baogao").scrollIntoView({ behavior: "smooth" });
        } catch (ex) {
          alert("这条记录已损坏，无法打开");
        }
      };
    });
  } catch (ex) {
    box.innerHTML = '<p class="rec-empty">' + esc(ex.message) + "</p>";
  }
}
$("#rec-close").onclick = () => { recMask.hidden = true; };
recMask.addEventListener("click", (e) => { if (e.target === recMask) recMask.hidden = true; });

loadMe();
