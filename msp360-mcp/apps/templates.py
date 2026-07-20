"""Inline HTML/JS templates for MCP Apps (official ext-apps SDK)."""

# Version suffix busts host HTML caches after app template changes.
BACKUP_MONITORING_URI = "ui://msp360/backup-monitoring@v3.html"
RMM_FLEET_URI = "ui://msp360/rmm-fleet-summary@v3.html"

# FastMCP / Claude Desktop require the official SDK + await app.connect().
# CDN must be declared in ResourceCSP(resource_domains=["https://unpkg.com"]).
_SDK_IMPORT = "https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps"


def _shell(title: str, caption: str, body_html: str, render_js: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="color-scheme" content="light dark">
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, -apple-system, sans-serif; }}
    body {{ margin: 0; padding: 16px; background: transparent; color: CanvasText; min-height: 200px; }}
    h1 {{ font-size: 1.1rem; margin: 0 0 4px; font-weight: 600; }}
    .caption {{ opacity: 0.7; font-size: 0.85rem; margin: 0 0 14px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 16px; }}
    .card {{ border: 1px solid color-mix(in srgb, CanvasText 20%, transparent); border-radius: 8px; padding: 10px; }}
    .card .label {{ font-size: 0.75rem; opacity: 0.75; }}
    .card .value {{ font-size: 1.25rem; font-weight: 700; margin-top: 4px; }}
    .ok {{ color: #15803d; }} .warn {{ color: #b45309; }} .alarm, .fail {{ color: #b91c1c; }} .run {{ color: #1d4ed8; }}
    .bar {{ height: 8px; border-radius: 4px; background: color-mix(in srgb, CanvasText 12%, transparent); overflow: hidden; margin-top: 4px; }}
    .bar > span {{ display: block; height: 100%; border-radius: 4px; }}
    .bar > span.ok {{ background: #22c55e; }}
    .bar > span.warn {{ background: #f59e0b; }}
    .bar > span.alarm {{ background: #ef4444; }}
    .endpoint {{ border: 1px solid color-mix(in srgb, CanvasText 15%, transparent); border-radius: 10px; padding: 12px; margin-bottom: 12px; }}
    .endpoint h2 {{ font-size: 1rem; margin: 0 0 8px; }}
    .metric {{ margin: 8px 0; }}
    .metric-row {{ display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 2px; }}
    canvas {{ width: 100%; max-width: 520px; height: 180px; display: block; }}
    .empty {{ opacity: 0.75; font-size: 0.9rem; padding: 8px 0; }}
    #status {{ font-size: 0.75rem; opacity: 0.55; margin-top: 12px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="caption">{caption}</p>
  {body_html}
  <p id="status">Connecting to host…</p>
  <script type="module">
    import {{ App }} from "{_SDK_IMPORT}";

    function extractPayload(result) {{
      if (!result) return null;
      if (result.structuredContent) return result.structuredContent;
      const blocks = result.content || [];
      for (const block of blocks) {{
        if (block.type === "text" && block.text) {{
          try {{ return JSON.parse(block.text); }} catch (_) {{ return block.text; }}
        }}
      }}
      return result;
    }}

    const statusEl = document.getElementById("status");
    {render_js}

    const app = new App({{ name: "msp360", version: "2.2.1" }});
    app.ontoolresult = (result) => {{
      statusEl.textContent = "Updated";
      window.renderApp(extractPayload(result));
    }};
    try {{
      await app.connect();
      statusEl.textContent = "Ready — waiting for tool result…";
    }} catch (err) {{
      statusEl.textContent = "Host connect failed: " + (err && err.message ? err.message : String(err));
    }}
  </script>
</body>
</html>"""


def backup_monitoring_html() -> str:
    body = """
<div id="stats" class="cards"></div>
<canvas id="chart" width="520" height="180"></canvas>
<p id="empty" class="empty">Waiting for monitoring data…</p>
"""
    render_js = r"""
const STATUS_KEYS = [
  ["success", "Success", "ok", "#22c55e"],
  ["warning", "Warning", "warn", "#f59e0b"],
  ["failed", "Failed", "fail", "#ef4444"],
  ["running", "Running", "run", "#3b82f6"],
];

function asItems(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.items)) return payload.items;
  if (Array.isArray(payload.Items)) return payload.Items;
  if (Array.isArray(payload.data)) return payload.data;
  if (Array.isArray(payload.Data)) return payload.Data;
  return [];
}

function normalizeStatus(value) {
  if (!value) return "unknown";
  return String(value).toLowerCase().replace(/[^a-z]/g, "");
}

function countStatuses(items) {
  const counts = { success: 0, warning: 0, failed: 0, running: 0, unknown: 0 };
  for (const item of items) {
    const raw = item.Status ?? item.status ?? item.State ?? item.state;
    const key = normalizeStatus(raw);
    if (key.includes("success") || key.includes("ok") || key.includes("complete")) counts.success += 1;
    else if (key.includes("warn")) counts.warning += 1;
    else if (key.includes("fail") || key.includes("error")) counts.failed += 1;
    else if (key.includes("run") || key.includes("progress")) counts.running += 1;
    else counts.unknown += 1;
  }
  return counts;
}

function renderStats(counts) {
  const root = document.getElementById("stats");
  root.innerHTML = STATUS_KEYS.map(([key, label, cls]) =>
    `<div class="card"><div class="label">${label}</div><div class="value ${cls}">${counts[key] || 0}</div></div>`
  ).join("");
}

function renderChart(counts) {
  const canvas = document.getElementById("chart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const series = STATUS_KEYS.map(([key, label, , color]) => ({
    label, value: counts[key] || 0, color,
  })).filter((s) => s.value > 0);
  if (!series.length) return;
  const max = Math.max(...series.map((s) => s.value), 1);
  const barW = Math.min(72, (canvas.width - 40) / series.length - 12);
  const baseY = canvas.height - 28;
  series.forEach((s, i) => {
    const h = (s.value / max) * (canvas.height - 56);
    const x = 24 + i * (barW + 12);
    const y = baseY - h;
    ctx.fillStyle = s.color;
    ctx.fillRect(x, y, barW, h);
    ctx.fillStyle = getComputedStyle(document.body).color || "#111";
    ctx.font = "12px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(String(s.value), x + barW / 2, y - 6);
    ctx.fillText(s.label, x + barW / 2, baseY + 16);
  });
}

window.renderApp = function (payload) {
  const items = asItems(payload);
  const empty = document.getElementById("empty");
  if (!items.length) {
    empty.textContent = "No backup plan runs in this page (0 monitoring items).";
    empty.hidden = false;
    document.getElementById("stats").innerHTML = "";
    return;
  }
  empty.hidden = true;
  const counts = countStatuses(items);
  renderStats(counts);
  renderChart(counts);
};
"""
    return _shell(
        "Backup monitoring overview",
        "Plan run status from backup_rm_get_monitoring",
        body,
        render_js,
    )


def rmm_fleet_html() -> str:
    body = """
<div id="cards" class="cards"></div>
<div id="endpoints"></div>
<p id="empty" class="empty">Waiting for fleet data…</p>
"""
    render_js = r"""
function asItems(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.items)) return payload.items;
  return [];
}

function stateClass(state) {
  const s = String(state || "").toLowerCase();
  if (s.includes("alarm") || s.includes("fail")) return "alarm";
  if (s.includes("warn")) return "warn";
  return "ok";
}

function metricBar(label, metric) {
  if (!metric || metric.value === "" || metric.value == null) return "";
  const pct = Math.min(100, Math.max(0, parseFloat(metric.value) || 0));
  const cls = stateClass(metric.state);
  return `<div class="metric"><div class="metric-row"><span>${label}</span><span class="${cls}">${metric.value}% · ${metric.state || "OK"}</span></div><div class="bar"><span class="${cls}" style="width:${pct}%"></span></div></div>`;
}

function renderEndpoint(item) {
  const header = item.header || {};
  const metrics = (item.data && item.data[0]) || {};
  const name = header.computerName || "Unknown";
  const hid = header.hid || "";
  const overall = metrics.computerState || "Unknown";
  let html = `<div class="endpoint"><h2>${name} <span class="${stateClass(overall)}">(${overall})</span></h2>`;
  html += metricBar("CPU", metrics.cpu);
  html += metricBar("RAM", metrics.ram);
  html += metricBar("HDD", metrics.hdd);
  if (metrics.update && metrics.update.value) {
    html += `<div class="metric-row"><span>Pending updates</span><span class="warn">${metrics.update.value}</span></div>`;
  }
  if (hid) html += `<div class="caption">HID: ${hid}</div>`;
  html += "</div>";
  return html;
}

window.renderApp = function (payload) {
  const items = asItems(payload);
  const empty = document.getElementById("empty");
  const cards = document.getElementById("cards");
  const endpoints = document.getElementById("endpoints");
  if (!items.length) {
    empty.textContent = "No RMM summary endpoints in this page.";
    empty.hidden = false;
    cards.innerHTML = "";
    endpoints.innerHTML = "";
    return;
  }
  empty.hidden = true;
  const alarms = items.filter((i) => {
    const d = (i.data && i.data[0]) || {};
    return String(d.computerState || "").toLowerCase().includes("alarm");
  }).length;
  cards.innerHTML = [
    ["Endpoints", items.length],
    ["Alarm", alarms],
    ["OK", items.length - alarms],
  ].map(([label, value]) =>
    `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`
  ).join("");
  endpoints.innerHTML = items.map(renderEndpoint).join("");
};
"""
    return _shell(
        "RMM fleet summary",
        "Endpoint health from rmm_fleet_overview (stat_type=summary)",
        body,
        render_js,
    )
