/* AI Trader console. Every value comes from the API; a missing value renders as N/A. */
"use strict";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const NA = '<span class="muted">N/A</span>';
const num = (x, d = 2) => (x === null || x === undefined || Number.isNaN(x)) ? NA : Number(x).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const signed = (x, d = 3) => (x === null || x === undefined) ? NA : `<span class="${x >= 0 ? "pos" : "neg"}">${x >= 0 ? "+" : ""}${Number(x).toFixed(d)}</span>`;
const pct = (x, d = 1) => (x === null || x === undefined) ? NA : `${(x * 100).toFixed(d)}%`;
const ts = (t) => t ? new Date(t * 1000).toISOString().replace("T", " ").slice(0, 16) : NA;
const tile = (k, v) => `<div class="tile"><div class="k">${esc(k)}</div><div class="v">${v}</div></div>`;
let selected = null;
let lastEventSeq = 0;

async function api(path, opts = {}) {
  const r = await fetch(path, { cache: "no-store", ...opts });
  let body = null;
  try { body = await r.json(); } catch (_) { /* non-JSON */ }
  if (!r.ok) throw Object.assign(new Error(body?.error || r.statusText), { status: r.status, body });
  return body;
}

function aiRecord(r) {
  if (!r || !r.trades) return "no closed trades yet";
  return `${r.trades} trades, win ${Math.round(r.win_rate * 100)}%, ${r.avg_R >= 0 ? "+" : ""}${r.avg_R}R (${r.sample})`;
}

// What the team said, in speaking order, and the joint decision. Presentation only.
function renderRoom(room) {
  if (!room || !(room.members || []).length) return "";
  const plan = (x) => !x || !x.action ? esc(x?.status || "—")
    : `${esc(x.action)}${x.action !== "NO_TRADE" ? ` ${esc(x.timeframe)} SL ${num(x.stop, 5)} TP ${num(x.target, 5)}` : ""}`;
  const said = (room.discussion || []).map((d, i) => `<li><b>${i + 1}. ${esc(d.role || "")} · ${esc(d.member)}</b> <span class="muted small">${esc(d.model || "")}</span><br>
      <span class="small">${d.action ? plan(d) : `<span class="neg">${esc(d.status)}</span>`}${d.dropped ? ` <span class="neg">(unusable: ${esc(d.dropped)})</span>` : ""}</span>
      ${d.thesis ? `<br><span class="small muted">${esc(d.thesis)}</span>` : ""}
      ${d.to_team ? `<br><span class="small">to the team: ${esc(d.to_team)}</span>` : ""}</li>`).join("");
  const j = room.joint;
  return `<div class="agent"><h4>TRADING ROOM <span class="muted small">one team, ${room.members.length} minds</span></h4>
    <div class="small">${esc(room.outcome || "")}</div><ol class="plain">${said}</ol>
    ${j ? `<div class="small"><b>Joint decision${room.head ? ` (written by ${esc(room.head)})` : ""}:</b> ${plan(j)}<br><span class="muted">${esc(j.thesis || "")}</span></div>` : ""}</div>`;
}

function chip(label, value, level) {
  return `<span class="chip ${level}" title="${esc(label)}">${esc(label)}: ${esc(value)}</span>`;
}
function lvl(v, good, bad) {
  if (good.some((g) => String(v).startsWith(g))) return "good";
  if (bad.some((b) => String(v).startsWith(b))) return "critical";
  return "warning";
}

/* ── status bar ─────────────────────────────────────────────────────── */
function renderStatus(s) {
  $("mode").textContent = s.mode;
  const c = s.components;
  const ks = s.kill_switch;
  const killed = !ks || ks.active !== false;
  $("status-row").innerHTML = [
    chip("SYSTEM", s.system, s.system === "ONLINE" ? "good" : "critical"),
    chip("DATA", `${c.data}${c.data_source === "yahoo" ? " · Yahoo" : ""}`, c.data === "CONNECTED" ? "good" : c.data.startsWith("QUOTES ONLY") ? "critical" : lvl(c.data, ["CONNECTED"], ["NOT"])),
    chip("BROKER", c.broker, lvl(c.broker, ["CONNECTED", "PAPER"], ["NOT"])),
    chip("AI", c.ai, lvl(c.ai, ["READY"], [])),
    // One chip per AI provider: calls that worked, calls that failed, and the last failure.
    // One chip per AI provider: calls that worked, calls that failed, and each model's own last
    // failure; a model resting after a spent quota or an unknown name is said to be resting.
    ...Object.entries(c.ai_providers || {}).map(([name, p]) => {
      const short = (m) => String(m).split(":").slice(1).join(":") || m;
      const errs = Object.entries(p.errors || {}).map(([m, e]) =>
        `${short(m)}: ${String(e).replace(/^HTTP_ERROR: /, "").slice(0, 110)}${(p.resting || {})[m] ? ` [resting ${p.resting[m]} min]` : ""}`);
      const bad = Object.keys(p.errors || {}).length;
      return chip(name.toUpperCase(), `${p.ok} ok · ${p.failed} failed${errs.length ? " · " + errs.join(" · ") : ""}`,
        !bad ? "good" : p.ok ? "warning" : "critical");
    }),
    chip("DATABASE", c.database, c.database === "HEALTHY" ? "good" : "critical"),
    // Whether the account survives a redeploy: without a volume it restarts at the start balance.
    c.storage ? chip("STORAGE", c.storage.status === "PERSISTENT" ? "SAVED ON VOLUME" : `${c.storage.status} (${c.storage.detail})`,
      c.storage.status === "PERSISTENT" ? "good" : c.storage.status === "NOT PERSISTENT" ? "critical" : "warning") : "",
    // A live memory that could not be read was set aside at start: say so where the memory is shown.
    String(c.knowledge_base?.memory_source || "").startsWith("base (the live copy")
      ? chip("MEMORY", c.knowledge_base.memory_source, "warning") : "",
    // Two facts in one chip: the files loaded and matched their card (✓), and the research verdict on the
    // strategy they encode. FAILED is that verdict (PR-001 found no edge), not a fault; it stays visible.
    chip("KNOWLEDGE", c.regime_model === "LOADED"
      ? ((c.knowledge_base && c.knowledge_base.status) === "FAILED" ? "LOADED ✓ · no proven edge yet (research test: FAILED)"
        : `LOADED ✓ · ${(c.knowledge_base && c.knowledge_base.status) || "status N/A"}`)
      : (c.knowledge_integrity || "MISSING"),
      c.regime_model !== "LOADED" ? "critical" : ((c.knowledge_base && c.knowledge_base.status) === "VALIDATED" ? "good" : "warning")),
    killed ? chip("STOP", "ACTIVE" + (ks && ks.reason ? ` (${ks.reason})` : ""), "critical") : chip("STOP", "off", "good"),
    s.paused ? chip("TRADING", "PAUSED", "warning") : chip("TRADING", "running", "good"),
    chip("DECIDES", ["llm_trader", "trading_room", "experimental_ai"].includes(c.decision_mode)
      ? `${c.decision_mode === "trading_room" ? `TRADING ROOM (${(c.trading_room?.members || []).length} AIs)` : c.decision_mode === "experimental_ai" ? "EXPERIMENTAL AI" : "AI TRADER"}${c.decision_interval_min ? ` · every ${c.decision_interval_min} min, ${c.symbols_per_cycle} pairs/cycle` : " · every 4 h"} · ${aiRecord(c.ai_trader_record)}`
      : c.decision_mode === "edges" ? "PROMOTED EDGES" : "EVIDENCE SYNTHESIS", c.decision_mode === "evidence" ? "good" : "warning"),
    // Where a trade goes. LIVE does not exist in this build; experimental trades are labelled as such.
    chip("ORDERS", s.mode === "PAPER" ? "PAPER (simulated, no broker order)"
      : (s.config?.experimental_execute ? "DEMO · experimental trades SENT to the demo account" : "DEMO · validated only; experimental = SHADOW (not sent)"),
      s.mode === "PAPER" ? "good" : "warning"),
    chip("EDGE", "none validated · results are EXPERIMENTAL", "warning"),
    chip("LIVE", "impossible in this build", "good"),
    s.halted ? chip("HALT", "drawdown halt", "critical") : "",
    chip("LAST DATA", s.last_market_update ? ts(s.last_market_update) : "never", s.last_market_update ? "good" : "warning"),
    c.history_desk ? chip("HISTORY", c.history_desk.trades ? `${(c.history_desk.trades / 1e6).toFixed(2)}M past trades · ${c.history_desk.integrity}`
      : c.history_desk.integrity, (c.history_desk.integrity || "") === "VERIFIED" ? "good" : c.history_desk.trades ? "warning" : "critical") : "",
    ...(c.news_calendar && c.news_calendar.status !== "NOT_CONFIGURED"
      ? [chip("NEWS", ["UNAVAILABLE", "PENDING"].includes(c.news_calendar.status) ? `${c.news_calendar.status} (${c.news_calendar.reason || "?"})`
          : `${c.news_calendar.status} · ${c.news_calendar.age_min} min old`,
          c.news_calendar.status === "FRESH" ? "good" : c.news_calendar.status === "UNAVAILABLE" ? "critical" : "warning")] : []),
    chip("LAST CYCLE", s.last_cycle ? ts(s.last_cycle) : "never", s.last_cycle_error ? "critical" : (s.last_cycle ? "good" : "warning")),
  ].join("");
  $("clock").textContent = new Date(s.time * 1000).toISOString().slice(11, 19);
  const up = s.uptime_s; $("uptime").textContent = `${Math.floor(up / 3600)}h ${Math.floor(up % 3600 / 60)}m`;
  $("health").innerHTML = [
    tile("DB latency", c.db_latency_ms !== null ? `${c.db_latency_ms} ms` : NA),
    tile("Decisions", num(s.counts.decisions, 0)), tile("No-trade", num(s.counts.no_trade, 0)),
    tile("Risk rejected", num(s.counts.risk_rejected, 0)), tile("Executed", num(s.counts.executed, 0)),
    tile("Shadow", num(s.counts.shadow ?? 0, 0)),
    tile("Errors", num(s.counts.errors, 0)),
    tile("Last error", s.last_cycle_error ? `<span class="neg small">${esc(s.last_cycle_error)}</span>` : "none"),
    tile("Demo check", c.demo_verification ? (c.demo_verification.verified ? "PASS" : `<span class="neg">FAIL</span>`) : NA),
  ].join("");
}

/* ── account ────────────────────────────────────────────────────────── */
function renderAccount(a) {
  if (!a.available) { $("account").innerHTML = `<p class="muted">Account not available: ${esc(a.reason)}</p>`; return; }
  const o = a.performance?.overall || {};
  $("account").innerHTML = [
    tile("Start", num(a.start_balance)), tile("Balance", num(a.balance)), tile("Equity", num(a.equity)),
    tile("Floating P/L", signed(a.floating_pnl, 2)), tile("Realized P/L", a.realized_pnl === null ? NA : signed(a.realized_pnl, 2)),
    tile("Daily P/L", a.daily_pnl === null ? NA : signed(a.daily_pnl, 2)),
    tile("Drawdown", a.drawdown_pct === null ? NA : `${a.drawdown_pct}%`),
    tile("Daily loss limit", `${a.daily_loss_limit_pct}%`), tile("Risk / trade", `${a.risk_per_trade_pct}%`),
    tile("Open positions", a.open_positions), tile("Trades", o.n ?? 0),
    tile("Win rate", o.n ? pct(o.win_rate) : NA), tile("Expectancy", o.n ? `${signed(o.avg_R)} R` : NA),
    tile("Profit factor", o.profit_factor_R ?? NA),
    tile("Sample", o.sample ? esc(o.sample) : NA),
  ].join("");
}

/* ── markets ────────────────────────────────────────────────────────── */
function renderMarket(rows) {
  if (!selected && rows.length) selected = rows[0].symbol;
  if (!rows.length) {
    $("market").querySelector("tbody").innerHTML = `<tr><td colspan="8" class="muted">No pairs configured (SYMBOLS).</td></tr>`;
    return;
  }
  $("market").querySelector("tbody").innerHTML = rows.map((r) => {
    const digits = r.symbol.includes("JPY") ? 3 : 5;
    return `<tr data-s="${esc(r.symbol)}" class="${r.symbol === selected ? "sel" : ""}">
      <td><b>${esc(r.symbol)}</b>${r.exposure ? ` <span class="chip">${esc(r.exposure)}</span>` : ""}${r.quote_error ? `<br><span class="small neg">${esc(r.quote_error)}</span>` : ""}</td>
      <td class="num">${num(r.bid, digits)}</td><td class="num">${num(r.ask, digits)}</td>
      <td class="num">${r.spread === null ? NA : num(r.spread, digits)}</td>
      <td>${esc(r.regime ?? "—")}</td><td>${esc(r.vol ?? "—")}</td>
      <td>${r.familiar === false ? '<span class="chip critical">unfamiliar</span>' : r.familiar ? "familiar" : "—"}</td>
      <td title="${esc(r.reason ?? "")}">${esc(r.decision ?? "—")} <span class="muted small">${r.last_decision_t ? ts(r.last_decision_t) : ""}</span>${r.decision === "NO_DATA" && r.reason ? `<br><span class="small neg">${esc(r.reason)}</span>` : ""}</td></tr>`;
  }).join("");
  $("market").querySelectorAll("tbody tr").forEach((tr) => tr.onclick = () => { selected = tr.dataset.s; refreshSelected(); });
}

/* ── charts (SVG, crosshair tooltip) ────────────────────────────────── */
function svgEl(w, h) { return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role="img">`; }

function candleChart(el, data) {
  const bars = data.bars || [];
  if (!data.available || bars.length < 2) { el.innerHTML = `<p class="muted">No bars: market data not connected.</p>`; return; }
  const W = Math.max(el.clientWidth, 320), H = 260, pad = { l: 6, r: 56, t: 8, b: 18 };
  const lo = Math.min(...bars.map((b) => b.l)), hi = Math.max(...bars.map((b) => b.h));
  const levels = (data.open || []).flatMap((p) => [p.entry, p.stop, p.target]).filter((x) => x);
  const min = Math.min(lo, ...levels), max = Math.max(hi, ...levels);
  const x = (i) => pad.l + (i + 0.5) * (W - pad.l - pad.r) / bars.length;
  const y = (v) => pad.t + (max - v) / (max - min || 1) * (H - pad.t - pad.b);
  const bw = Math.max(1, (W - pad.l - pad.r) / bars.length * 0.6);
  let s = svgEl(W, H);
  for (let k = 0; k <= 4; k++) {
    const v = min + (max - min) * k / 4, yy = y(v);
    s += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${yy}" y2="${yy}" stroke="var(--grid)" stroke-width="1"/>`;
    s += `<text x="${W - pad.r + 4}" y="${yy + 4}" font-size="10" fill="var(--muted)">${v.toFixed(v > 50 ? 2 : 4)}</text>`;
  }
  bars.forEach((b, i) => {
    const up = b.c >= b.o, col = up ? "var(--series-1)" : "var(--series-8)";
    s += `<line x1="${x(i)}" x2="${x(i)}" y1="${y(b.h)}" y2="${y(b.l)}" stroke="${col}" stroke-width="1"/>`;
    const top = y(Math.max(b.o, b.c)), hgt = Math.max(1, Math.abs(y(b.o) - y(b.c)));
    s += `<rect x="${x(i) - bw / 2}" y="${top}" width="${bw}" height="${hgt}" rx="1" fill="${up ? "var(--surface-1)" : col}" stroke="${col}" stroke-width="1"/>`;
  });
  (data.open || []).forEach((p) => {
    [["entry", p.entry, "var(--text-secondary)"], ["SL", p.stop, "var(--critical)"], ["TP", p.target, "var(--good)"]].forEach(([n, v, c]) => {
      if (!v) return;
      s += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="${c}" stroke-dasharray="4 3" stroke-width="1.5"/>`;
      s += `<text x="${pad.l + 4}" y="${y(v) - 3}" font-size="10" fill="var(--text-secondary)">${n} ${Number(v).toFixed(String(data.symbol || selected || "").includes("JPY") ? 3 : 5)}</text>`;
    });
  });
  (data.marks || []).forEach((m) => {
    const i = bars.findIndex((b) => b.t + 3600 >= m.time);
    if (i < 0) return;
    const up = m.decision === "BUY";
    s += `<text x="${x(i)}" y="${up ? y(bars[i].l) + 12 : y(bars[i].h) - 4}" text-anchor="middle" font-size="11" fill="var(--text-primary)">${up ? "▲" : "▼"}</text>`;
  });
  s += `<line id="xh" x1="0" x2="0" y1="${pad.t}" y2="${H - pad.b}" stroke="var(--axis)" stroke-width="1" visibility="hidden"/></svg><div class="tip"></div>`;
  el.innerHTML = s;
  const svg = el.querySelector("svg"), tip = el.querySelector(".tip"), xh = el.querySelector("#xh");
  svg.style.height = H + "px";
  svg.addEventListener("pointermove", (ev) => {
    const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) / r.width * W;
    const i = Math.min(bars.length - 1, Math.max(0, Math.floor((px - pad.l) / ((W - pad.l - pad.r) / bars.length))));
    const b = bars[i];
    xh.setAttribute("x1", x(i)); xh.setAttribute("x2", x(i)); xh.setAttribute("visibility", "visible");
    tip.style.display = "block"; tip.style.left = Math.min(r.width - 170, ev.clientX - r.left + 10) + "px"; tip.style.top = "10px";
    tip.innerHTML = `${ts(b.t)}<br>O ${b.o.toFixed(5)} H ${b.h.toFixed(5)}<br>L ${b.l.toFixed(5)} C ${b.c.toFixed(5)}<br>ticks ${b.v}`;
  });
  svg.addEventListener("pointerleave", () => { tip.style.display = "none"; xh.setAttribute("visibility", "hidden"); });
}

function lineChart(el, points, label, fmtY, empty = "not enough closed trades yet.") {
  if (!points || points.length < 2) { el.innerHTML = `<p class="muted small">${esc(label)}: ${esc(empty)}</p>`; return; }
  const W = Math.max(el.clientWidth, 320), H = 150, pad = { l: 6, r: 56, t: 16, b: 16 };
  const ys = points.map((p) => p[1]);
  let min = Math.min(...ys), max = Math.max(...ys);
  if (max - min < 1e-9) { const m = Math.abs(max) * 1e-4 || 1; min -= m; max += m; }  // a flat line sits mid-chart, not on the top edge
  const x = (i) => pad.l + i * (W - pad.l - pad.r) / (points.length - 1);
  const y = (v) => pad.t + (max - v) / (max - min || 1) * (H - pad.t - pad.b);
  let s = svgEl(W, H) + `<text x="${pad.l}" y="11" font-size="11" fill="var(--text-secondary)">${esc(label)}</text>`;
  [min, max].forEach((v) => { s += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${y(v)}" y2="${y(v)}" stroke="var(--grid)"/><text x="${W - pad.r + 4}" y="${y(v) + 4}" font-size="10" fill="var(--muted)">${fmtY(v)}</text>`; });
  s += `<polyline fill="none" stroke="var(--series-1)" stroke-width="2" points="${points.map((p, i) => `${x(i)},${y(p[1])}`).join(" ")}"/>`;
  s += `<circle id="dot" r="4" fill="var(--series-1)" stroke="var(--surface-1)" stroke-width="2" visibility="hidden"/></svg><div class="tip"></div>`;
  el.innerHTML = s;
  const svg = el.querySelector("svg"), tip = el.querySelector(".tip"), dot = el.querySelector("#dot");
  svg.style.height = H + "px";
  svg.addEventListener("pointermove", (ev) => {
    const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) / r.width * W;
    const i = Math.min(points.length - 1, Math.max(0, Math.round((px - pad.l) / ((W - pad.l - pad.r) / (points.length - 1)))));
    dot.setAttribute("cx", x(i)); dot.setAttribute("cy", y(points[i][1])); dot.setAttribute("visibility", "visible");
    tip.style.display = "block"; tip.style.left = Math.min(r.width - 150, ev.clientX - r.left + 10) + "px"; tip.style.top = "8px";
    tip.innerHTML = `${ts(points[i][0])}<br>${esc(label)}: ${fmtY(points[i][1])}`;
  });
  svg.addEventListener("pointerleave", () => { tip.style.display = "none"; dot.setAttribute("visibility", "hidden"); });
}

/* ── decision, agents, risk ─────────────────────────────────────────── */
function stepState(status) {
  if (/% WON$/.test(status || "")) return "info";  // a measurement, not a verdict: no colour
  if (["OK", "PASSED", "FILLED", "APPROVED", "DESCRIBE", "SUPPORT", "NEUTRAL", "BUY", "SELL"].includes(status)) return "ok";
  if (["ERROR", "TIMEOUT", "REJECTED", "BLOCKED", "OPPOSE"].includes(status)) return "rej";
  return "warn";
}
function renderDecision(det) {
  $("pipe-symbol").textContent = selected || "";
  if (!det) {
    $("pipeline").innerHTML = ["DATA", "FEATURES", "MARKET", "SETUP", "RISK ANALYST", "ADVERSARY", "REVIEWER", "RISK ENGINE", "EXECUTION"]
      .map((n) => `<li><b>${n}</b><span class="st">WAITING</span></li>`).join("");
    $("decision-line").innerHTML = `<span class="muted">No decision recorded for ${esc(selected || "this market")} yet.</span>`;
    $("agents").innerHTML = `<p class="muted">No decision recorded yet.</p>`;
    return;
  }
  const d = det.decision, ag = det.agents || {};
  const f = d.context?.features;
  const room = d.independent_evidence?.room;
  const hist = historyLine(d.context?.history, d.decision);
  const steps = room ? [
    // The trading room: each mind in the order it spoke, the joint call, then what history and the
    // risk engine said. Nothing here is computed in the page except the count of who agreed.
    ["DATA", (d.context?.data_flags || []).length ? "FLAGGED" : "OK"],
    ...(room.discussion || []).map((x) => [`${x.role || "?"} · ${x.member}`, x.action || x.status || "—"]),
    ["TEAM", room.joint ? room.joint.action || room.joint.status : (d.decision === "NO_TRADE" ? "NO_TRADE" : "—")],
    ["HISTORY", hist.step],
    ["RISK ENGINE", det.risk ? (det.risk.approved ? "APPROVED" : "REJECTED") : (d.decision === "NO_TRADE" ? "NOT NEEDED" : "PENDING")],
    ["EXECUTION", det.execution ? det.execution.status : "—"],
  ] : [
    ["DATA", (d.context?.data_flags || []).length ? "FLAGGED" : "OK"],
    ["FEATURES", f && (f.missing || []).length ? `MISSING ${f.missing.length}` : "OK"],
    ["MARKET", ag.market?.status || "UNAVAILABLE"], ["SETUP", ag.setup ? `${ag.setup.stance}` : "UNAVAILABLE"],
    ["RISK ANALYST", ag.risk ? ag.risk.stance : "UNAVAILABLE"], ["ADVERSARY", ag.adversary ? ag.adversary.stance : "UNAVAILABLE"],
    ["REVIEWER", d.decision], ["RISK ENGINE", det.risk ? (det.risk.approved ? "APPROVED" : "REJECTED") : (d.decision === "NO_TRADE" ? "NOT NEEDED" : "PENDING")],
    ["EXECUTION", det.execution ? det.execution.status : "—"],
  ];
  $("pipeline").innerHTML = steps.map(([n, st]) => `<li class="${stepState(st)}"><b>${n}</b><span class="st">${esc(st)}</span></li>`).join("");
  const conf = d.confidence === null || d.confidence === undefined ? "" : ` · confidence ${pct(d.confidence, 0)} (P(expectancy &gt; required), from analogue evidence)`;
  const spoke = room ? (room.discussion || []).filter((x) => x.action) : [];
  const agree = spoke.filter((x) => x.action === d.decision).length;
  const team = room ? `<br><span class="small">Team: <b>${agree} of ${spoke.length}</b> minds that answered said ${esc(d.decision)}${
    (room.discussion || []).length > spoke.length ? ` · ${(room.discussion || []).length - spoke.length} could not answer` : ""}</span>` : "";
  $("decision-line").innerHTML = `<b>${esc(d.decision)}</b> ${esc(d.instrument)} at ${ts(d.timestamp)}${conf}${team}${hist.line}<br><span class="small">${esc(d.no_trade_reason || d.thesis)}</span>`;
  $("agents").innerHTML = renderRoom(d.independent_evidence?.room) + ["market", "setup", "risk", "adversary", "reviewer"].map((k) => {
    const r = ag[k];
    if (!r) return `<div class="agent"><h4>${k}</h4><p class="muted">UNAVAILABLE</p></div>`;
    const objs = (r.objections || []).map((o) => `<li><b>${esc(o.severity)}</b> ${esc(o.code)} — ${esc(o.message)}</li>`).join("");
    const ev = (r.evidence || []).slice(0, 5).map((e) => `<li>${esc(e.claim)}</li>`).join("");
    const cands = (r.candidates || []).slice(0, 4).map((c) => `<li>${esc(c.family)} ${esc(c.action)}: analogues ${c.expected_r === null ? "n/a" : c.expected_r.toFixed(3)}R (lower ${c.lower_r === null ? "n/a" : c.lower_r.toFixed(3)}, n=${c.n_analogs})</li>`).join("");
    const llm = r.llm ? `<p class="small muted">LLM: ${esc(r.llm.status || (r.llm.ok ? "OK" : "FAILED"))}${r.llm.model ? " · " + esc(r.llm.model) : ""}${r.llm.data?.summary ? " — " + esc(r.llm.data.summary) : (r.llm.summary ? " — " + esc(r.llm.summary) : "")}</p>` : "";
    return `<div class="agent"><h4>${esc(k.toUpperCase())} <span class="chip ${stepState(r.stance) === "ok" ? "good" : stepState(r.stance) === "rej" ? "critical" : "warning"}">${esc(r.stance)}</span> <span class="muted small">${esc(r.status)} · ${r.latency_ms ?? "—"} ms</span></h4>
      <div class="small">${esc(r.summary)}</div>${ev ? `<ul>${ev}</ul>` : ""}${cands ? `<ul>${cands}</ul>` : ""}${objs ? `<ul>${objs}</ul>` : ""}${llm}</div>`;
  }).join("");
}

// What the history desk measured for this decision point: for each side, the fixed trade whose
// lower-bound expectancy was best, with its win rate over the most similar past situations. These
// numbers were given to the team before it decided; the page only picks which to show.
function historyLine(h, decision) {
  if (!h) return { step: "—", line: "" };
  if (!h.available) return { step: "N/A", line: `<br><span class="small muted">History: ${esc(h.reason || "not available")}</span>` };
  const best = (side) => Object.values(h.trades || {}).length && Object.entries(h.trades)
    .filter(([k]) => k.endsWith(":" + side)).map(([, v]) => v)
    .sort((a, b) => b.avg_R_lower_bound - a.avg_R_lower_bound)[0];
  const b = best("BUY"), s = best("SELL");
  const part = (side, v) => v ? `${side} won <b>${Math.round(v.win_rate * 100)}%</b> (${v.avg_R >= 0 ? "+" : ""}${v.avg_R.toFixed(2)} R avg)` : `${side} N/A`;
  const pick = decision === "BUY" ? b : decision === "SELL" ? s : null;
  return {
    step: pick ? `${Math.round(pick.win_rate * 100)}% WON` : "SEEN",
    line: `<br><span class="small" title="${esc((b && b.what) || "")} / ${esc((s && s.what) || "")}">History, ${h.neighbours} most similar past situations (${h.distinct_episodes} different days): ${part("BUY", b)} · ${part("SELL", s)}</span>`,
  };
}

function renderRisk(risk, det) {
  const L = risk.limits;
  const v = det?.risk;
  const checks = v ? (v.checks || []).map((c) => `<li class="${c.passed ? "" : "neg"}">${c.passed ? "✓" : "✗"} ${esc(c.name)} — ${esc(c.detail)}</li>`).join("") : "";
  $("risk").innerHTML = `<div class="tiles">
      ${tile("Risk / trade", `${L.risk_per_trade_pct}%`)}${tile("Daily loss", `${L.daily_loss_limit_pct}%`)}
      ${tile("Max drawdown", `${L.max_drawdown_pct}%`)}${tile("Max positions", L.max_open_positions)}
      ${tile("Per currency", L.max_positions_per_currency)}${tile("Min R:R", L.min_reward_risk)}
      ${tile("Funded rules", risk.funded ? esc(risk.funded.name) : "none set")}</div>
    ${v ? `<h3>Last verdict for ${esc(selected)}: <span class="chip ${v.approved ? "good" : "critical"}">${v.approved ? "RISK APPROVED" : "RISK REJECTED"}</span></h3>
      <div class="small">size ${num(v.qty, 2)} lots · risk ${num(v.risk_amount, 2)} (${num(v.risk_pct, 3)}%)</div><ul class="small">${checks}</ul>` :
      `<p class="muted small">No risk verdict for ${esc(selected || "this market")}: the last decision did not propose a trade.</p>`}`;
}

/* ── trades, performance, memory, research, events ─────────────────── */
function renderTrades(open, closed) {
  $("open-trades").innerHTML = open.length ? `<div class="table-wrap"><table><thead><tr><th>Symbol</th><th>Side</th><th class="num">Entry</th><th class="num">Now</th><th class="num">SL</th><th class="num">TP</th><th class="num">Lots</th><th class="num">R now</th><th class="num">Hours</th></tr></thead><tbody>${
    open.map((t) => `<tr><td>${esc(t.symbol)}</td><td>${esc(t.side)}</td><td class="num">${num(t.entry, 5)}</td><td class="num">${num(t.current, 5)}</td><td class="num">${num(t.stop, 5)}</td><td class="num">${num(t.target, 5)}</td><td class="num">${num(t.qty, 2)}</td><td class="num">${t.r_now === null ? NA : signed(t.r_now, 2)}</td><td class="num">${t.duration_h}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">None.</p>`;
  $("closed").querySelector("tbody").innerHTML = closed.slice(0, 15).map((t) =>
    `<tr title="${esc(t.explanation)}"><td>${esc(t.symbol)}</td><td>${esc(t.side)}</td><td class="num">${t.r === null ? NA : signed(t.r, 2)}</td><td>${esc(t.exit_reason)}</td><td>${esc(t.cause)}</td></tr>`).join("") || `<tr><td colspan="5" class="muted">No closed trades yet.</td></tr>`;
}

function renderPerformance(p) {
  $("perf-body").hidden = !p.available;  // no empty chart frames before there is anything to plot
  if (!p.available) {
    $("perf-tiles").innerHTML = `<p class="muted">${esc(p.reason)}.</p>`; $("equity").innerHTML = ""; $("drawdown").innerHTML = "";
    $("by-regime").querySelector("tbody").innerHTML = ""; return;
  }
  const o = p.overall, e = p.equity;
  $("perf-tiles").innerHTML = [tile("Trades", o.n), tile("Expectancy", `${signed(o.avg_R)} R`), tile("t-stat", o.t ?? NA),
    tile("Win rate", pct(o.win_rate)), tile("Avg win", o.avg_win_R ?? NA), tile("Avg loss", o.avg_loss_R ?? NA),
    tile("Profit factor", e.profit_factor ?? NA), tile("Max DD", `${e.max_drawdown_pct}%`), tile("Sharpe", e.sharpe_daily_ann ?? NA),
    tile("Sortino", e.sortino_daily_ann ?? NA), tile("Max losing run", p.max_consecutive_losses), tile("Sample", esc(o.sample))].join("");
  const curve = e.curve || [];
  lineChart($("equity"), curve, "Realised equity", (v) => v.toFixed(0));
  let peak = -Infinity;
  lineChart($("drawdown"), curve.map(([t, v]) => { peak = Math.max(peak, v); return [t, (v - peak) / peak * 100]; }), "Drawdown %", (v) => v.toFixed(1) + "%");
  $("by-regime").querySelector("tbody").innerHTML = Object.entries(p.by_regime || {}).map(([k, s]) =>
    `<tr><td>${esc(k)}</td><td class="num">${s.n}</td><td class="num">${signed(s.avg_R)}</td><td class="num">${pct(s.win_rate)}</td><td>${esc(s.sample)}</td></tr>`).join("");
}

function renderMemory(m) {
  const s = m.semantic, ep = m.episodic;
  $("memory-tiles").innerHTML = [tile("Decisions", ep.decisions), tile("Trades", ep.trades), tile("Episodes", ep.episodes),
    tile("Post-mortems", ep.postmortems), tile("Patterns", num(m.pattern.patterns, 0)), tile("Knowledge v", s.knowledge_version),
    ...Object.entries(s.by_status).map(([k, v]) => tile(`Lessons ${k.toLowerCase()}`, v)),
    tile("History intact", Object.values(m.chains).every(Boolean) ? "verified" : `<span class="neg">CHAIN BROKEN</span>`)].join("");
  $("lessons").querySelector("tbody").innerHTML = s.lessons.map((l) => {
    const ev = l.validation || l.discovery || {};
    return `<tr><td class="small">${esc(l.statement)}</td><td>${esc(l.status)}</td><td>${l.version}</td><td class="num">n=${ev.n ?? "—"} ${ev.mean !== undefined ? signed(ev.mean) : ""}</td></tr>`;
  }).join("") || `<tr><td colspan="4" class="muted">No lessons yet: a lesson needs dozens of resolved outcomes, never one trade.</td></tr>`;
  const r = m.reflection;
  if (r && r.kind === "trade") {  // model modes: the team's own review of its last closed trade
    $("reflection").innerHTML = `<div class="small"><b>Self-review of its last trade</b> <span class="muted">${esc(r.model || "")}</span><br>
      What happened: ${esc(r.text || "—")}<br>Was it a mistake: ${r.was_it_a_mistake === true ? "yes" : r.was_it_a_mistake === false ? "no" : "not said"}${r.mistake ? ` — ${esc(r.mistake)}` : ""}<br>
      Lesson: ${r.lesson ? esc(r.lesson) : '<span class="muted">none</span>'}</div>`;
    return;
  }
  $("reflection").innerHTML = r ? `<div class="small">Resolved ${r.resolved} · traded ${r.traded.n} (avg ${r.traded.mean ?? "n/a"}R) · skipped ${r.skipped_shadow.n} (shadow avg ${r.skipped_shadow.mean ?? "n/a"}R)
    ${r.overconfidence_R !== undefined ? ` · overconfidence ${r.overconfidence_R}R` : ""}${r.drift_alarm ? ' · <span class="neg">DRIFT ALARM</span>' : ""}</div>
    <ul class="small">${(r.hypotheses || []).map((h) => `<li>${esc(h.kind)}: ${esc(h.text)}</li>`).join("") || "<li>No hypotheses raised.</li>"}</ul>
    <div class="small">Loss causes: ${esc(JSON.stringify(r.loss_causes || {}))}</div>` : `<span class="muted">None yet.</span>`;
}

function renderResearch(r) {
  $("research-meta").textContent = `Holdout from ${r.holdout.start}: ${r.holdout.spent ? "SPENT" : "sealed"} · the next test on this data must beat |t| > ${r.next_threshold_t}`;
  $("research").querySelector("tbody").innerHTML = r.trials.map((t) =>
    `<tr><td class="small">${esc(t.id)}</td><td>${esc(t.status)}</td><td class="num">${t.tests}</td><td>${esc(t.registered.slice(0, 10))}</td></tr>`).join("");
  const props = r.proposals || [];
  $("proposals").innerHTML = props.length
    ? `<ul class="small">${props.map((x) => `<li><b>${esc(x.kind)}</b> ${esc(x.statement)} <span class="muted">— ${esc(x.suggested_test)} · ${esc(x.status)}</span></li>`).join("")}</ul>`
    : `<span class="muted small">None yet. Reflection proposes experiments; only the research lab runs and counts them.</span>`;
  const p = r.pr001;
  const v = r.pr001_verdicts;
  const verdictLine = v ? `<div class="small">Pre-registered verdicts: ${Object.entries(v).map(([k, x]) => `${esc(k.split("_")[0])} <b class="${x === "PASS" ? "pos" : "neg"}">${esc(x)}</b>`).join(" · ")}</div>` : `<div class="small muted">Verdicts: not judged yet.</div>`;
  $("pr001").innerHTML = p ? `<h3>PR-001 ablation — judged period 2010–2016</h3>${verdictLine}<div class="small muted">A agents only · B + memory · C + learning (full system) · R random. Rows ending “-nohalt” are the exploratory arm: no verdict.</div><div class="table-wrap"><table><thead><tr><th>Variant</th><th class="num">Trades</th><th class="num">Avg R</th><th class="num">t</th><th class="num">Win</th><th class="num">Max DD</th></tr></thead><tbody>${
    Object.entries(p).map(([k, v]) => { const o = v.metrics.overall; return `<tr><td>${esc(k)}</td><td class="num">${o.n}</td><td class="num">${o.n ? signed(o.avg_R) : NA}</td><td class="num">${o.t ?? NA}</td><td class="num">${o.n ? pct(o.win_rate) : NA}</td><td class="num">${v.metrics.equity.max_drawdown_pct}%</td></tr>`; }).join("")}</tbody></table></div>` : "";
}

function renderEvents(evs) {
  if (!evs.length) return;
  lastEventSeq = Math.max(lastEventSeq, ...evs.map((e) => e.seq));
  const html = evs.map((e) => `<li><code>${ts(e.ts)}</code> <b>${esc(e.type)}</b> <span class="muted">${esc(JSON.stringify(e.payload).slice(0, 160))}</span></li>`).join("");
  $("events").innerHTML = (html + $("events").innerHTML).split("</li>").slice(0, 120).join("</li>");
}

/* ── controls ───────────────────────────────────────────────────────── */
// The token survives a reload of this tab (sessionStorage). "Remember on this
// device" keeps it in localStorage instead. Storage can be missing or throw
// (private mode, blocked site data): the dashboard then simply asks again.
const TOKEN_KEY = "aitrader.dashboardToken";
function tokenStore(kind) { try { return window[kind] || null; } catch { return null; } }
function forgetToken() {
  for (const kind of ["sessionStorage", "localStorage"]) { try { tokenStore(kind)?.removeItem(TOKEN_KEY); } catch { /* unavailable */ } }
}
function saveToken() {
  const tok = $("token").value.trim();
  forgetToken();
  if (!tok) return;
  try { tokenStore($("remember").checked ? "localStorage" : "sessionStorage")?.setItem(TOKEN_KEY, tok); } catch { /* unavailable */ }
}
function loadToken() {
  for (const kind of ["localStorage", "sessionStorage"]) {
    let v = null;
    try { v = tokenStore(kind)?.getItem(TOKEN_KEY); } catch { /* unavailable */ }
    if (v) { $("token").value = v; $("remember").checked = kind === "localStorage"; return; }
  }
}
loadToken();
$("token").addEventListener("input", saveToken);
$("remember").addEventListener("change", saveToken);

async function control(path, needsToken, body = {}) {
  const headers = { "Content-Type": "application/json" };
  const tok = $("token").value.trim();
  if (needsToken && tok) headers["X-Dashboard-Token"] = tok;
  try {
    const r = await api(path, { method: "POST", headers, body: JSON.stringify(body) });
    $("control-msg").textContent = `OK: ${JSON.stringify(r)}`;
  } catch (e) {
    $("control-msg").textContent = `Refused (${e.status}): ${e.body?.error || e.message}`;
    if (needsToken && e.status === 401) { forgetToken(); $("token").value = ""; $("remember").checked = false; }  // a wrong token is not kept
  }
  refreshFast();
}
$("btn-kill").onclick = () => { if (confirm("Emergency stop: no new orders until cleared with the token.")) control("/api/control/kill", false, { reason: "dashboard emergency stop" }); };
$("btn-pause").onclick = () => control("/api/control/pause", false, { reason: "dashboard pause" });
$("btn-resume").onclick = () => control("/api/control/resume", true);
$("btn-clear").onclick = () => control("/api/control/kill/clear", true);
$("btn-scan").onclick = () => control("/api/control/scan", true);

/* ── live panel: the account as it moves ───────────────────────────── */
const liveSamples = [];  // [time, equity] seen since this page opened; nothing is interpolated
let liveShown = null;
const money = (x) => (x === null || x === undefined) ? NA : `${x >= 0 ? "+" : "−"}${Math.abs(x).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const moneyCls = (x) => x === null || x === undefined ? "" : x >= 0 ? "pos" : "neg";
const ago = (t, now) => { const s = Math.max(0, now - t); return s < 90 ? `${s}s` : s < 5400 ? `${Math.round(s / 60)} min` : `${(s / 3600).toFixed(1)} h`; };

function countTo(el, from, to) {
  // Eases the shown number to the new value; the last frame is exactly the value read.
  const fmt = (v) => v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (from === null || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { el.textContent = fmt(to); return; }
  const t0 = performance.now(), dur = 700;
  const step = (now) => {
    const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    el.textContent = fmt(k < 1 ? from + (to - from) * e : to);
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* A trade that opens or closes is announced across the top of the screen, so it cannot be missed.
   Only changes seen while the page is open are announced; what was already open is not. */
let seenOpen = null, seenClosed = null;
const toastQueue = [];
function toast(kind, big, line) {
  toastQueue.push({ kind, big, line });
  if (toastQueue.length === 1) showNextToast();
}
function showNextToast() {
  const t = toastQueue[0], el = $("toast");
  if (!t) { el.hidden = true; return; }
  el.className = `toast ${t.kind}`;
  el.innerHTML = `<div class="big">${t.big}</div><div class="line">${t.line}</div><div class="hint">tap to close</div>`;
  el.hidden = false;
  const done = () => { clearTimeout(timer); el.onclick = null; toastQueue.shift(); el.hidden = true; setTimeout(showNextToast, 250); };
  const timer = setTimeout(done, 10000);
  el.onclick = done;
  try { navigator.vibrate?.([80, 60, 80]); } catch (_) { /* not every phone */ }
}
function announce(L) {
  const d = (s) => (String(s).includes("JPY") ? 3 : 5);
  const openKeys = new Map((L.positions || []).map((p) => [`${p.symbol}|${p.opened}`, p]));
  const lt = L.last_trade, closedKey = lt ? `${lt.symbol}|${lt.closed}` : null;
  if (seenOpen !== null) {
    for (const [k, p] of openKeys) if (!seenOpen.has(k)) {
      toast(p.side === "BUY" ? "buy" : "sell", `${p.side === "BUY" ? "▲ BUY" : "▼ SELL"} ${esc(p.symbol)} — TRADE OPENED`,
        `entry ${num(p.entry, d(p.symbol))} · stop ${num(p.stop, d(p.symbol))} · target ${num(p.target, d(p.symbol))}`);
    }
    if (closedKey && closedKey !== seenClosed) {
      const kind = lt.pnl === null ? "flat" : lt.pnl > 0 ? "win" : lt.pnl < 0 ? "loss" : "flat";
      toast(kind, `${esc(lt.symbol)} ${esc(lt.side)} CLOSED ${money(lt.pnl)}`,
        `${lt.r === null ? "" : (lt.r >= 0 ? "+" : "") + lt.r.toFixed(2) + " R · "}${esc(lt.exit_reason)}`);
    }
  }
  seenOpen = new Set(openKeys.keys());
  seenClosed = closedKey;
}

/* How far the trade has gone: 0% at entry, +100% at the target, −100% at the stop, for either side.
   Computed from the trade's own levels and the price now; the ring fills like a loading circle. */
function tradeProgress(p) {
  if (p.current === null || p.current === undefined) return null;
  const side = p.side === "BUY" ? 1 : -1, move = (p.current - p.entry) * side;
  const span = move >= 0 ? Math.abs(p.target - p.entry) : Math.abs(p.entry - p.stop);
  return span > 0 ? move / span * 100 : null;
}
function progressRing(p, d) {
  const pc = tradeProgress(p);
  const R = 30, C = 2 * Math.PI * R, frac = pc === null ? 0 : Math.min(1, Math.abs(pc) / 100);
  const good = pc !== null && pc >= 0, col = pc === null ? "var(--muted)" : good ? "var(--good)" : "var(--critical)";
  const label = pc === null ? "N/A" : `${pc >= 0 ? "+" : "−"}${Math.abs(pc).toFixed(0)}%`;
  const words = pc === null ? "no price right now" : good ? `of the way to the target (${num(p.target, d)})` : `of the way to the stop (${num(p.stop, d)})`;
  // Toward the target the ring fills clockwise; toward the stop, anticlockwise.
  return `<div class="tc-prog"><svg viewBox="0 0 76 76" class="ring" role="img" aria-label="${esc(label + " " + words)}">
      <circle cx="38" cy="38" r="${R}" fill="none" stroke="var(--grid)" stroke-width="8"/>
      <circle cx="38" cy="38" r="${R}" fill="none" stroke="${col}" stroke-width="8" stroke-linecap="round"
        stroke-dasharray="${(frac * C).toFixed(1)} ${C.toFixed(1)}" transform="${good ? "" : "translate(76 0) scale(-1 1) "}rotate(-90 38 38)"
        style="transition: stroke-dasharray .6s ease"/>
      <text x="38" y="43" text-anchor="middle" font-size="15" font-weight="800" fill="${col}">${label}</text></svg>
    <div class="tc-prog-t"><div class="${good ? "pos" : pc === null ? "muted" : "neg"}"><b>${label}</b> ${esc(words)}</div>
      <div class="muted small">stop ${num(p.stop, d)} · entry ${num(p.entry, d)} · target ${num(p.target, d)}</div></div></div>`;
}

function renderLive(L) {
  const hero = $("live-equity"), dot = $("live-dot");
  if (!L.available) {
    dot.classList.remove("on");
    hero.innerHTML = NA; $("live-sub").innerHTML = `<span class="neg">${esc(L.reason)}</span>`; return;
  }
  dot.classList.add("on");
  announce(L);
  if (liveShown !== null && L.equity !== liveShown) {
    hero.classList.remove("up", "down"); void hero.offsetWidth;
    hero.classList.add(L.equity > liveShown ? "up" : "down");
    setTimeout(() => hero.classList.remove("up", "down"), 1200);
  }
  countTo(hero, liveShown, L.equity);
  liveShown = L.equity;
  const last = liveSamples[liveSamples.length - 1];
  if (!last || last[0] !== L.time || last[1] !== L.equity) liveSamples.push([L.time, L.equity]);
  if (liveSamples.length > 1440) liveSamples.shift();
  const td = L.today;
  $("live-sub").innerHTML = [
    `<span>Floating <b class="${moneyCls(L.floating_pnl)}">${money(L.floating_pnl)}</b></span>`,
    `<span>Today <b class="${moneyCls(L.daily_pnl)}">${money(L.daily_pnl)}</b></span>`,
    `<span>Since start <b class="${moneyCls(L.total_pnl)}">${money(L.total_pnl)}</b></span>`,
    td ? `<span>Trades today <b>${td.trades}</b>${td.trades ? ` · ${td.wins} won` : ""}</span>` : "",
  ].filter(Boolean).join("");
  $("live-age").textContent = `${L.currency || ""} · read ${new Date(L.time * 1000).toISOString().slice(11, 19)} UTC`;
  lineChart($("live-spark"), liveSamples, "Equity since this page opened", (v) => v.toFixed(2),
    "the line starts with the next change in equity.");
  $("live-positions").innerHTML = (L.positions || []).map((p) => {
    const d = p.symbol.includes("JPY") ? 3 : 5, side = p.side === "BUY" ? "buy" : "sell";
    const left = p.max_hold_minutes ? p.opened + p.max_hold_minutes * 60 - L.time : null;
    const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
    return `<div class="trade-card ${side}">
      <div class="tc-top"><span class="tc-side">${p.side === "BUY" ? "▲ BUY" : "▼ SELL"}</span><span class="tc-sym">${esc(p.symbol)}</span>
        <span class="muted small">${esc(p.timeframe || "")}${p.qty ? ` · ${num(p.qty, 2)} lots` : ""}</span>
        <span class="tc-pnl ${moneyCls(p.pnl)}">${money(p.pnl)}</span></div>
      <div class="tc-sub">entry <b>${num(p.entry, d)}</b> → now <b>${num(p.current, d)}</b> · <b>${p.r_now === null ? NA : signed(p.r_now, 2) + " R"}</b></div>
      ${progressRing(p, d)}
      <div class="tc-meta"><span>open ${ago(p.opened, L.time)}</span><span>${left === null ? "no time limit" : left > 0 ? `closes by time in ${mmss(left)}` : "closing now (time)"}</span></div>
      ${p.thesis ? `<div class="tc-why"><b>Why${p.method ? ` (${esc(p.method)})` : ""}:</b> ${esc(p.thesis)}</div>` : ""}</div>`;
  }).join("") || `<div class="trade-card empty">No open trade right now · the team is watching the market</div>`;
  const lt = L.last_trade, ld = L.last_decision;
  $("live-last").innerHTML = [
    lt ? `Last closed: <b>${esc(lt.symbol)} ${esc(lt.side)}</b> ${lt.r === null ? "" : signed(lt.r, 2) + " R"} <span class="${moneyCls(lt.pnl)}">${money(lt.pnl)}</span> · ${esc(lt.exit_reason)} · ${ago(lt.closed, L.time)} ago` : "",
    ld ? `Team's latest call: <b>${esc(ld.symbol)} ${esc(ld.decision)}</b> <span class="muted">${ld.time ? ago(ld.time, L.time) + " ago" : ""}${ld.reason ? " — " + esc(String(ld.reason).slice(0, 160)) : ""}</span>` : "",
  ].filter(Boolean).join("<br>");
}
/* ── team analysis: the discussion as it happens ───────────────────── */
const ROLE_NAME = { TREND: "Trend", PRICE: "Price", NEWS: "News", RISK: "Risk" };
function renderAnalysis(r) {
  if (!r || !r.boxes) return;
  const running = r.stage === "discussing" || r.stage === "deciding";
  const res = r.result, out = r.outcome;
  $("an-symbol").textContent = `${r.symbol || ""} · ${r.t ? new Date(r.t * 1000).toISOString().slice(11, 16) : ""}`;
  $("an-pct").textContent = `${r.pct ?? 0}%`;
  const bar = $("an-bar");
  bar.className = "an-bar" + (running ? " run" : res && res.action === "BUY" ? " buy" : res && res.action === "SELL" ? " sell" : "");
  bar.setAttribute("aria-valuenow", r.pct ?? 0);
  $("an-fill").style.width = `${r.pct ?? 0}%`;
  $("an-boxes").innerHTML = r.boxes.map((b) => {
    const cls = b.state === "done" ? (b.action || "") : String(b.state).replace(/ /g, "-");
    const st = b.state === "thinking" ? `<span class="dots">thinking</span>`
      : b.state === "done" ? `${esc(b.action)}${b.action !== "NO_TRADE" && b.timeframe ? " · " + esc(b.timeframe) : ""}`
      : b.state === "waiting" ? `<span class="muted">waiting</span>`
      : `<span class="muted">${esc(b.state)}${b.status ? " (" + esc(b.status) + ")" : ""}</span>`;
    return `<div class="an-box ${esc(cls)}"><div class="in"><div class="role">${esc(ROLE_NAME[b.role] || b.role)} · ${Math.round(100 / r.boxes.length)}%</div>
      <div class="who">${esc(b.member)}</div><div class="st">${st}</div>${b.method ? `<div class="who">method: ${esc(b.method)}</div>` : ""}${b.thesis ? `<div class="th">${esc(b.thesis)}</div>` : ""}</div></div>`;
  }).join("");
  // What the team is looking at: structure per timeframe (from the market map) and the related markets.
  const cx = r.context || {};
  const st = Object.entries(cx.structure || {}).map(([tf, v]) => `${tf} ${esc(v.trend || "?")}${v.last_break ? ` (${esc(v.last_break)})` : ""}`).join(" · ");
  const im = Object.entries(cx.intermarket_4h || {}).filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => `${esc(k)} <span class="${v >= 0 ? "pos" : "neg"}">${v >= 0 ? "+" : ""}${Number(v).toFixed(2)}%</span>`).join(" · ");
  const fire = (cx.firing || []).map(esc).join(" · ");
  const best = (cx.best_recent || []).map(esc).join(" · ");
  const ctxLine = (st || im || fire || best) ? `<div class="small muted" style="margin-bottom:8px">${st ? `Structure: ${st}` : ""}${cx.session ? ` · session ${esc(cx.session)}` : ""}${im ? `<br>Related markets (4h): ${im}` : ""}${fire ? `<br>Strategies firing now: ${fire}` : "<br>Strategies firing now: none of the 16"}${best ? `<br>Best on M5 recently: ${best}` : ""}</div>` : "";
  let line;
  if (r.stage === "discussing") line = `<span class="muted">The team is discussing ${esc(r.symbol)}…</span>`;
  else if (r.stage === "deciding") line = `<b>100%</b> · ${esc(r.head || "the team")} is writing the team's decision<span class="dots"></span>`;
  else if (!res) line = "";
  else if (res.action === "NO_TRADE") line = `<b>NO TRADE</b> <span class="muted">— ${esc(String(res.reason || "").slice(0, 220))}</span>`;
  else {
    const d = String(r.symbol || "").includes("JPY") ? 3 : 5;
    const plan = `<b class="${res.action === "BUY" ? "pos" : "neg"}">${esc(res.action)}</b> ${esc(res.timeframe || "")}${res.method ? ` · ${esc(res.method)}` : ""} · SL ${num(res.stop, d)} · TP ${num(res.target, d)}${res.max_hold_minutes ? ` · up to ${res.max_hold_minutes} min` : ""}`;
    const after = !out ? `<span class="muted">checking with the risk engine…</span>`
      : out.executed ? `<span class="an-placed ${res.action === "BUY" ? "buy" : "sell"}">✔ TRADE OPENED · ${num(out.qty, 2)} lots</span> <span class="muted small">sized by the risk engine</span>`
      : out.risk === "REJECTED" ? `<span class="neg">✗ refused by the risk engine: ${esc((out.reasons || [])[0] || "")}</span>`
      : `<span class="muted">not placed</span>`;
    line = `${plan}<br>${after}`;
  }
  $("an-result").innerHTML = ctxLine + line;
}
async function refreshAnalysis() { await safe(async () => renderAnalysis(await api("/api/room"))); }

async function refreshLive() { await safe(async () => renderLive(await api("/api/live"))); }

// PAPER FORWARD TEST: presentation only. Every number is the server's; a missing one renders as N/A.
function renderPaperForward(P) {
  const card = $("pf-card");
  card.hidden = !P.active;
  if (!P.active) return;
  const A = P.account || {}, O = (P.performance || {}).overall || {};
  $("pf-sub").textContent = `${P.research_status} · profile ${P.profile}`;
  const money = (x) => (x === null || x === undefined) ? NA : `$${num(x, 2)}`;
  $("pf-tiles").innerHTML = [
    tile("Mode", "PAPER FORWARD"), tile("Account", money(P.start_balance)), tile("Equity", money(A.equity)),
    tile("P&L today", money(A.today_pnl)), tile("Total P&L", money(A.total_pnl)),
    tile("Drawdown", money(A.drawdown_from_start)), tile("Open positions", String((P.open_positions || []).length)),
    tile("Trades", String(O.trades ?? 0)), tile("Win rate", pct(O.win_rate)),
    tile("Expectancy", O.expectancy_r === null || O.expectancy_r === undefined ? NA : `${signed(O.expectancy_r)}R`),
    tile("Profit factor", num(O.profit_factor)), tile("Risk status", esc(P.risk_status || "N/A")),
    tile("Bot status", esc(P.bot_status || "N/A")),
  ].join("");
  $("pf-sample").textContent = O.trades ? `${O.trades} trades · sample ${O.sample}` : "none yet";
  $("pf-pipeline").innerHTML = (P.pipeline || []).map((e) => {
    const stages = (e.stages || []).map((s) => `<span class="${/REJECTED|NOT EXECUTED|SHADOW/.test(s) ? "stage-no" : "stage-ok"}">${esc(s)}</span>`).join(" → ");
    return `<li>${ts(e.t)} · ${esc(e.symbol)} ${esc(e.decision)} · ${stages}${e.reason ? `<br><span class="muted">${esc(e.reason)}</span>` : ""}</li>`;
  }).join("") || '<li class="muted">No trade decision yet.</li>';
  $("pf-trades").querySelector("tbody").innerHTML = (P.recent_trades || []).map((t) => `<tr><td>${ts(t.closed)}</td>
    <td>${esc(t.symbol)}</td><td>${esc(t.direction)}</td><td>${signed(t.net_pnl, 2)}</td><td>${signed(t.r, 2)}</td>
    <td>${num(t.costs_total)}</td><td>${esc(t.exit_reason)}</td><td>${esc(t.agent || t.source || "")}</td></tr>`).join("");
}
async function refreshPaperForward() { await safe(async () => renderPaperForward(await api("/api/paper_forward"))); }

// DUAL AI: presentation only. The key is never sent to the page; only whether it is set and its last 4 characters.
function renderDualAI(D) {
  const card = $("dai-card");
  card.hidden = !D.active;
  if (!D.active) return;
  const O = D.openrouter || {}, P = D.performance || {}, R = D.record || {}, L = D.last_analysis;
  const conf = (a) => (a && a.confidence !== null && a.confidence !== undefined) ? `${num(a.confidence, 0)}` : NA;
  $("dai-sub").textContent = `OpenRouter ${O.status || "N/A"} · key ${O.configured ? `set (${O.key_hint || "…"})` : "NOT SET"} · free models only · calls today ${O.calls_today ?? 0}/${O.daily_budget ?? "?"}`;
  $("dai-tiles").innerHTML = [
    tile("OpenRouter", esc(O.status || "N/A")), tile("Trader 1 (vision)", esc(O.vision_model || "none")),
    tile("Trader 2", esc(O.judge_model || "none")), tile("Debate", esc(O.verifier_model || "none")),
    tile("Trader 1 says", L && L.trader1 ? `${esc(L.trader1.direction)} · ${conf(L.trader1)}` : NA),
    tile("Trader 2 says", L && L.trader2 ? `${esc(L.trader2.direction)} · ${conf(L.trader2)}` : NA),
    tile("Desk", L && L.consensus ? esc(L.consensus.rule) : NA),
    tile("Risk engine", L && L.risk ? (L.risk.approved ? "APPROVED" : "REJECTED") : NA),
    tile("Open positions", String((D.open_positions || []).length)),
    tile("AI trades", String(P.trades ?? 0)), tile("Wins", String(P.wins ?? 0)), tile("Losses", String(P.losses ?? 0)),
    tile("Expectancy", P.expectancy_r === null || P.expectancy_r === undefined ? NA : `${signed(P.expectancy_r)}R`),
    tile("Profit factor", num(P.profit_factor)), tile("Max drawdown", P.max_drawdown_usd === undefined ? NA : `$${num(P.max_drawdown_usd, 2)}`),
    tile("Sample", esc(P.sample || "none")), tile("Agreement", R.agreement_rate === null || R.agreement_rate === undefined ? NA : pct(R.agreement_rate)),
  ].join("");
  $("dai-when").textContent = L ? `${ts(L.t)} · ${L.symbol}` : "none yet";
  if (L) {
    const m = L.models || {};
    const line = (name, a, model) => a ? `<div><b>${name}</b> <span class="muted">${esc(model || "")}</span>: ${esc(a.direction || "")} · confidence ${conf(a)}${a.entry ? ` · entry ${num(a.entry, 5)} SL ${num(a.stop_loss, 5)} TP ${num(a.take_profit, 5)} RR ${num(a.risk_reward)}` : ""}<br><span class="muted">${esc(String(a.reason || "").slice(0, 300))}</span></div>` : "";
    $("dai-last").innerHTML = line("Trader 1 (vision)", L.trader1, m.trader1) + line("Trader 2 (independent)", L.trader2, m.trader2)
      + line("Debate", L.verifier, m.verifier)
      + `<div><b>Final: ${esc(L.decision)}</b> <span class="muted">${esc(String(L.reason || "").slice(0, 300))}</span></div>`;
    const fig = $("dai-figure");
    fig.hidden = !L.chart;
    if (L.chart && (D.charts || {})[L.symbol]) {
      $("dai-img").src = `/api/dual_ai/chart.png?symbol=${encodeURIComponent(L.symbol)}&t=${D.charts[L.symbol].t}`;
      $("dai-cap").textContent = `${L.symbol} · ${L.chart.execution_timeframe}/${L.chart.higher_timeframe || "-"} · completed bars to ${ts(L.chart.last_bar_available)} · sha256 ${String(L.chart.sha256 || "").slice(0, 12)}`;
    } else fig.hidden = true;
  } else $("dai-last").innerHTML = '<span class="muted">No analysis yet.</span>';
  $("dai-table").querySelector("tbody").innerHTML = (D.analyses || []).map((a) => `<tr><td>${ts(a.t)}</td><td>${esc(a.symbol)}</td>
    <td>${a.trader1 ? `${esc(a.trader1.direction)} ${conf(a.trader1)}` : NA}</td><td>${a.trader2 ? `${esc(a.trader2.direction)} ${conf(a.trader2)}` : "—"}</td>
    <td>${a.verifier ? esc(a.verifier.direction) : "—"}</td><td>${esc((a.consensus || {}).rule || "")}</td><td>${esc(a.decision)}</td>
    <td>${a.risk ? (a.risk.approved ? "APPROVED" : `<span class="neg">REJECTED</span>`) : "—"}</td></tr>`).join("")
    || '<tr><td colspan="8" class="muted">No analysis yet.</td></tr>';
}
async function refreshDualAI() { await safe(async () => renderDualAI(await api("/api/dual_ai"))); }

/* ── forward evidence ───────────────────────────────────────────────── */
const sampleTag = (x) => esc(x || "none");
const statTd = (st) => `<td class="num">${st?.n ?? 0}</td><td class="num">${st?.n ? signed(st.expectancy_r) : NA}</td>`;
function renderEvidence(ev, lessons) {
  $("ev-statement").textContent = ev.statement || "";
  const a = ev.all || {};
  $("ev-tiles").innerHTML = [
    tile("Proposals", num(a.proposals ?? 0, 0)), tile("Resolved", num(a.n ?? 0, 0)), tile("Pending", num(a.unresolved ?? 0, 0)),
    tile("Gross R", a.n ? signed(a.gross_r_total, 2) : NA), tile("Costs R", a.n ? num(a.cost_r_total, 2) : NA),
    tile("Net R", a.n ? signed(a.net_r_total, 2) : NA), tile("Expectancy", a.n ? `${signed(a.expectancy_r)} R` : NA),
    tile("Median R", a.n ? signed(a.median_r) : NA), tile("Win rate", a.n ? pct(a.win_rate) : NA),
    tile("Profit factor", a.profit_factor ?? NA), tile("Max DD", a.n ? `${num(a.max_drawdown_r, 2)} R` : NA),
    tile("Loss streak", a.n ? a.max_consecutive_losses : NA), tile("t", a.t ?? NA),
    tile("Net, costs ×2", a.n ? signed(a.net_avg_costs_x2) : NA), tile("Sample", sampleTag(a.sample)),
    tile("Evaluation n", num(ev.evaluation?.n ?? 0, 0)),
  ].join("");
  const body = (id, html, cols, empty) => { $(id).querySelector("tbody").innerHTML = html || `<tr><td colspan="${cols}" class="muted">${empty}</td></tr>`; };
  body("ev-class", Object.entries(ev.by_signal_class || {}).map(([k, v]) => `<tr><td><span class="tag exp">${esc(k)}</span></td>${statTd(v.all)}
    <td class="num">${v.all?.n ? signed(v.all.net_r_total, 2) : NA}</td><td class="num">${v.all?.n ? num(v.all.cost_r_total, 2) : NA}</td>
    <td class="num">${v.all?.t ?? NA}</td><td>${sampleTag(v.all?.sample)}</td><td>${esc(v.eligibility?.status || "—")}</td></tr>`).join(""), 8, "No proposals yet.");
  body("ev-route", Object.entries(ev.by_route || {}).map(([k, v]) => `<tr><td><span class="tag ${k === "SHADOW" ? "shadow" : ""}">${esc(k)}</span></td>${statTd(v)}
    <td class="num">${v.n ? pct(v.win_rate) : NA}</td><td>${sampleTag(v.sample)}</td></tr>`).join(""), 5, "No proposals yet.");
  body("ev-model", Object.entries(ev.by_model || {}).map(([k, v]) => { const c = (ev.calibration_by_model || {})[k] || {};
    return `<tr><td>${esc(k)}</td>${statTd(v)}<td class="num">${c.n ? pct(c.stated) : NA}</td><td class="num">${c.n ? pct(c.realised) : NA}</td><td>${sampleTag(v.sample)}</td></tr>`; }).join(""), 6, "No model proposals yet.");
  const dims = [...Object.entries(ev.by_symbol || {}).map(([k, v]) => [k, v]), ...Object.entries(ev.by_regime || {}).map(([k, v]) => [`regime ${k}`, v])];
  body("ev-dims", dims.map(([k, v]) => `<tr><td>${esc(k)}</td>${statTd(v)}<td class="num">${v.n ? pct(v.win_rate) : NA}</td>
    <td class="num">${v.profit_factor ?? NA}</td><td>${sampleTag(v.sample)}</td></tr>`).join(""), 6, "No proposals yet.");
  body("ev-recent", (ev.recent || []).map((r) => `<tr><td>${ts(r.t)}</td><td>${esc(r.symbol)}</td><td>${r.side > 0 ? "BUY" : "SELL"}</td>
    <td>${esc(r.signal_class || "?")}</td><td><span class="tag ${r.edge_status === "VALIDATED" ? "val" : "exp"}">${esc(r.edge_status)}</span></td>
    <td><span class="tag ${r.route === "SHADOW" ? "shadow" : ""}">${esc(r.route)}</span></td><td>${esc((r.partition || "").slice(0, 5))}</td>
    <td>${esc(r.outcome)}</td><td class="num">${r.net_r === null || r.net_r === undefined ? NA : signed(r.net_r)}</td></tr>`).join(""), 9, "No proposals yet.");
  body("fw-lessons", ((lessons && lessons.forward) || []).map((l) => { const e = l.evaluation_evidence || l.learning_evidence || {};
    return `<tr><td title="${esc(l.statement)}">${esc(l.code)}</td><td>${esc(l.scope)}</td><td>${esc(l.status)}</td>
    <td class="num">${e.n ?? NA}</td><td class="num">${e.share !== undefined ? pct(e.share) : NA}</td></tr>`; }).join(""), 5,
    "None yet: a lesson needs at least 30 resolved outcomes in its scope.");
}

/* ── refresh loops ──────────────────────────────────────────────────── */
async function safe(fn) { try { await fn(); } catch (e) { console.warn(e); } }
async function refreshSelected() {
  if (!selected) return;
  $("chart-symbol").textContent = selected;
  await safe(async () => candleChart($("chart"), await api(`/api/market/${selected}/bars?n=160`)));
  await safe(async () => {
    const ds = await api(`/api/decisions?limit=1&symbol=${selected}`);
    const det = ds.length ? await api(`/api/decisions/${ds[0].id}`) : null;
    renderDecision(det);
    renderRisk(await api("/api/risk"), det);
  });
}
async function refreshFast() {
  await safe(async () => renderStatus(await api("/api/status")));
  await safe(async () => renderAccount(await api("/api/account")));
  try { renderMarket(await api("/api/market")); } catch (e) {
    // Say so instead of leaving an empty table that looks like "no pairs".
    $("market").querySelector("tbody").innerHTML = `<tr><td colspan="8" class="neg">Market data request failed (${esc(e.status || "")}): ${esc(e.body?.error || e.message)}</td></tr>`;
  }
  await safe(async () => { renderTrades(await api("/api/trades?status=open"), await api("/api/trades?limit=15")); });
  await safe(async () => renderEvents(await api(`/api/events?since=${lastEventSeq}&limit=60`)));
}
async function refreshSlow() {
  await refreshSelected();
  await safe(async () => renderPerformance(await api("/api/performance")));
  await safe(async () => renderMemory(await api("/api/memory")));
  await safe(async () => renderResearch(await api("/api/research")));
  await safe(async () => renderEvidence(await api("/api/evidence"), await api("/api/lessons")));
}
refreshFast().then(refreshSlow);
refreshLive();
setInterval(refreshLive, 2500);
setInterval(refreshPaperForward, 10000);
refreshPaperForward();
setInterval(refreshDualAI, 15000);
refreshDualAI();
refreshAnalysis();
setInterval(refreshAnalysis, 1000);  // the discussion: who is thinking now  // the account itself; prices behind it refresh about every 10 s
setInterval(refreshFast, 10000);  // prices are cached 10 s server-side: refreshing faster only costs requests
setInterval(refreshSlow, 20000);
