#!/usr/bin/env python3
"""Build the static GitHub Pages site into docs/ (stdlib only).

Reads the newest data-YYYY-MM-DD.json in the repo root and writes:
  docs/index.html  - self-contained page (data embedded, works from file://)
  docs/data.json   - raw aggregated data for external use
  docs/logo.svg    - MetaRank brand mark
  docs/favicon.svg - favicon derived from the mark
"""
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KNOWN_SOURCES = [
    {"id": "lmarena", "name": "LMArena", "url": "https://lmarena.ai/leaderboard",
     "what": "Millions of blind human votes, Bradley-Terry rating",
     "category": "chat"},
    {"id": "aa", "name": "Artificial Analysis", "url": "https://artificialanalysis.ai/",
     "what": "Independent Intelligence Index across ~10 evals",
     "category": "chat"},
    {"id": "aider", "name": "Aider", "url": "https://aider.chat/docs/leaderboards/",
     "what": "225 real coding exercises across 6 languages, % passing",
     "category": "coding"},
    {"id": "epoch", "name": "Epoch AI", "url": "https://epoch.ai/benchmarks",
     "what": "Independent re-runs of hard benchmarks, combined capability index",
     "category": "agents"},
    {"id": "livebench", "name": "LiveBench", "url": "https://livebench.ai/",
     "what": "Fresh monthly questions, contamination-resistant scores",
     "category": "general"},
    {"id": "openrouter", "name": "OpenRouter", "url": "https://openrouter.ai/models",
     "what": "Live per-token pricing: input/output $ per 1M tokens",
     "category": "pricing"},
]
CAT_LABEL = {"chat": "Chat", "coding": "Coding", "agents": "Agents",
             "general": "General", "pricing": "Pricing"}

# --- Brand assets ---------------------------------------------------------
# MetaRank mark: five ascending bars (a ranking chart) whose final,
# tallest bar carries the brand gradient -- many leaderboards in,
# one meta-ranking out.
_BARS = (
    '<rect x="4" y="36" width="8" height="22" rx="2.5" fill="#2f4a6b"/>'
    '<rect x="16" y="24" width="8" height="34" rx="2.5" fill="#3a5a80"/>'
    '<rect x="28" y="32" width="8" height="26" rx="2.5" fill="#2f4a6b"/>'
    '<rect x="40" y="16" width="8" height="42" rx="2.5" fill="#46648c"/>'
    '<rect x="52" y="8" width="8" height="50" rx="2.5" fill="url(#mrg)"/>'
)
_GRAD = (
    '<defs><linearGradient id="mrg" x1="0" y1="1" x2="1" y2="0">'
    '<stop offset="0" stop-color="#22d3ee"/>'
    '<stop offset="1" stop-color="#a78bfa"/>'
    "</linearGradient></defs>"
)
LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    + _GRAD + _BARS + "</svg>"
)
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#0b1220"/>' + _GRAD +
    '<g transform="translate(9,9) scale(0.71875)">' + _BARS + "</g></svg>"
)

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MetaRank &mdash; The leaderboard of leaderboards</title>
<meta name="description" content="MetaRank averages the web's top AI model leaderboards into one consensus meta-ranking.">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>
:root{
  --bg:#070b13; --card:#0e1726; --card2:#111c2f; --border:#1d2a40;
  --text:#eef3fa; --muted:#8fa1b8;
  --a1:#22d3ee; --a2:#a78bfa; --gold:#f0b429; --green:#34d399;
  --grad:linear-gradient(120deg,var(--a1),var(--a2));
}
*{box-sizing:border-box}
body{
  background:radial-gradient(1200px 520px at 50% -8%, #122540 0%, var(--bg) 58%) fixed, var(--bg);
  color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  margin:0; line-height:1.55; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1020px;margin:0 auto;padding:34px 20px 70px}
.hero{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.logo{width:64px;height:64px;flex:0 0 auto;filter:drop-shadow(0 4px 18px rgba(34,211,238,.25))}
.eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.22em;text-transform:uppercase;
  background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;margin:0 0 2px}
.hero h1{font-size:2.7rem;line-height:1;margin:0;font-weight:800;letter-spacing:-.03em}
.hero h1 .rk{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.stats{display:flex;gap:10px;margin-left:auto;flex-wrap:wrap}
.stat{background:rgba(14,23,38,.75);border:1px solid var(--border);border-radius:12px;
  padding:10px 16px;min-width:118px;backdrop-filter:blur(4px)}
.stat .v{font-size:1.25rem;font-weight:800;letter-spacing:-.01em}
.stat .v .grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.stat .k{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
.updated{font-size:.85rem;color:var(--muted);margin:14px 2px 0}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:20px 22px;margin:20px 0;box-shadow:0 8px 30px rgba(0,0,0,.25)}
.card h2{font-size:1.05rem;margin:0 0 10px;letter-spacing:.01em}
.card h2 .dot{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:var(--grad);margin-right:8px;vertical-align:1px}
.card p{margin:8px 0;color:#c9d5e4}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:640px){.grid2{grid-template-columns:1fr}.stats{margin-left:0}.hero h1{font-size:2.1rem}}
.def{background:var(--card2);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;font-size:.92rem;color:#c9d5e4}
.def b{color:var(--a1)}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0 0}
.tabs button{background:var(--card);color:var(--text);border:1px solid var(--border);
  border-radius:999px;padding:10px 22px;font-size:.95rem;font-weight:600;cursor:pointer;
  transition:transform .12s ease, box-shadow .12s ease}
.tabs button:hover{transform:translateY(-1px);border-color:#33507a}
.tabs button[aria-selected="true"]{background:var(--grad);border-color:transparent;
  color:#06121c;box-shadow:0 4px 18px rgba(34,211,238,.35)}
.tabline{color:var(--muted);font-size:.9rem;margin:10px 2px 0}
.tabline a{color:var(--a1);text-decoration:none}
.tools{display:flex;justify-content:flex-end;gap:8px;margin:14px 0 0;flex-wrap:wrap;align-items:center}
.tools input{background:var(--card);border:1px solid var(--border);border-radius:10px;
  color:var(--text);padding:10px 14px;font-size:.9rem;width:220px}
.tools input:focus{outline:none;border-color:var(--a1);box-shadow:0 0 0 3px rgba(34,211,238,.15)}
.tools select{background:var(--card);border:1px solid var(--border);border-radius:10px;
  color:var(--text);padding:10px 12px;font-size:.9rem;cursor:pointer}
.tools button.exp{background:var(--card2);border:1px solid var(--border);border-radius:10px;
  color:var(--text);padding:10px 14px;font-size:.85rem;font-weight:600;cursor:pointer}
.tools button.exp:hover{border-color:var(--a1);color:var(--a1)}
table{width:100%;border-collapse:collapse;font-size:.95rem}
th{position:sticky;top:0;background:var(--card2);text-align:left;padding:12px 10px;
  color:var(--muted);font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
  border-bottom:1px solid var(--border);white-space:nowrap;cursor:pointer;user-select:none;z-index:1}
th:hover{color:var(--text)}
td{padding:11px 10px;border-bottom:1px solid var(--border);vertical-align:middle}
tr.main:hover td{background:#142033}
.rankbadge{display:inline-block;min-width:32px;text-align:center;background:#1a2740;
  border:1px solid var(--border);border-radius:9px;padding:3px 9px;font-weight:700}
tr.main:nth-child(-n+3) .rankbadge{background:var(--grad);border-color:transparent;color:#06121c}
.modelbtn{background:none;border:0;color:var(--text);font-size:.95rem;font-weight:650;
  cursor:pointer;text-align:left;padding:0;font-family:inherit}
.modelbtn:hover{color:var(--a1)}
.modelbtn .org{display:block;font-weight:400;font-size:.8rem;color:var(--muted)}
td.num{font-variant-numeric:tabular-nums}
.firsts{color:var(--gold);font-weight:700}
tr.detail td{background:#0a111c;padding:0;border-bottom:1px solid var(--border)}
.chips{display:flex;flex-wrap:wrap;gap:8px;padding:14px 16px}
.chip{background:var(--card2);border:1px solid var(--border);border-radius:10px;
  padding:8px 13px;font-size:.85rem;color:var(--muted)}
.chip b{color:var(--text);font-size:1rem;margin-right:6px}
.chip a{color:var(--a1);text-decoration:none}
.srclist{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.src{background:var(--card2);border:1px solid var(--border);border-radius:10px;padding:14px 16px;
  transition:border-color .12s ease}
.src:hover{border-color:#33507a}
.src .nm{font-weight:700}
.src .nm a{color:var(--text);text-decoration:none}
.src .nm a:hover{color:var(--a1)}
.cat{display:inline-block;font-size:.72rem;background:#1a2740;border:1px solid var(--border);
  border-radius:999px;padding:1px 10px;margin-left:8px;color:var(--muted)}
.src p{font-size:.85rem;color:var(--muted);margin:6px 0}
.src .st{font-size:.78rem}
.st.live{color:var(--green)} .st.skip{color:var(--gold)}
ol.method{margin:8px 0;padding-left:22px;color:#c9d5e4}
ol.method li,ul.cav li{margin:6px 0}
ul.cav{margin:8px 0;padding-left:22px;color:var(--muted);font-size:.92rem}
ul.cav a,footer a{color:var(--a1);text-decoration:none}
footer{margin-top:30px;color:var(--muted);font-size:.85rem;text-align:center}
footer .brand{font-weight:700;color:var(--text)}
.hidden{display:none}
:focus-visible{outline:2px solid var(--a1);outline-offset:2px}
</style>
</head>
<body>
<div class="wrap">

<header class="hero">
<img class="logo" src="logo.svg" alt="MetaRank logo">
<div>
<p class="eyebrow">The leaderboard of leaderboards</p>
<h1>Meta<span class="rk">Rank</span></h1>
</div>
<div class="stats" id="stats"></div>
</header>
<p class="updated" id="updated"></p>

<div class="card">
<h2><span class="dot"></span>What is this?</h2>
<p>New to AI models and overwhelmed by a dozen different leaderboards? <b>MetaRank</b> fixes that.
We take the most respected public AI rankings, note where each model places on each one,
and average those placements into a single <b>meta-ranking</b>. The models at the top aren't
just winning one test &mdash; they're winning <i>everywhere</i>.</p>
</div>

<div class="card">
<h2><span class="dot"></span>How to read it</h2>
<div class="grid2">
<div class="def"><b>Average rank</b> &mdash; a model's mean placement across the sources it appears on. <b>Lower is better</b>: 1.5 beats 10.0.</div>
<div class="def"><b>Sources</b> &mdash; how many leaderboards the model appears on. More sources = more confidence.</div>
<div class="def"><b>#1sts</b> &mdash; how many leaderboards the model outright tops. The tiebreaker.</div>
<div class="def"><b>Click a model</b> for its per-source breakdown. <b>Click a column header</b> to sort. Use the search box or the source filter to narrow the table, and the export buttons to download it.</div>
<div class="def"><b>Pricing tab</b> &mdash; shows what the top models cost to run: input and output price per 1M tokens, live from OpenRouter. Sort by price to find the cheapest strong models.</div>
<div class="def"><b>Region filter</b> &mdash; narrow any tab to models from a region (USA, China, Europe, Canada, UK, Singapore, UAE). Region = the lab's headquarters country.</div>
<div class="def"><b>Open Weights / Self-Hosted tabs</b> &mdash; the top open models, and the subset you can realistically run yourself. Status comes from a curated list, not auto-detection.</div>
</div>
</div>

<div class="tabs" role="tablist" id="tabs"></div>
<p class="tabline" id="tabline"></p>

<div class="tools">
<select id="region" aria-label="Region filter">
<option value="">All regions</option>
<option value="USA">USA</option>
<option value="China">China</option>
<option value="Europe">Europe</option>
<option value="Canada">Canada</option>
<option value="UK">UK</option>
<option value="Singapore">Singapore</option>
<option value="UAE">UAE</option>
<option value="Other">Other</option>
</select>
<select id="minsrc" aria-label="Minimum sources">
<option value="0">All sources</option>
<option value="2">2+ sources</option>
<option value="3">3+ sources</option>
<option value="4">4+ sources</option>
</select>
<button class="exp" id="expCsv" type="button">Export CSV</button>
<button class="exp" id="expJson" type="button">Export JSON</button>
<input id="filter" type="search" placeholder="Filter models&hellip;" aria-label="Filter models">
</div>
<div class="card" style="padding:6px 14px;overflow-x:auto">
<table aria-label="Model rankings">
<thead id="thead"></thead>
<tbody id="rows"></tbody>
</table>
</div>

<div class="card">
<h2><span class="dot"></span>Sources</h2>
<div class="srclist" id="srclist"></div>
</div>

<div class="card">
<h2><span class="dot"></span>Methodology</h2>
<ol class="method">
<li><b>Collect.</b> We pull the current leaderboard from each source above &mdash; human-preference votes (LMArena), independent benchmark re-runs (Epoch AI, Artificial Analysis), fresh monthly questions (LiveBench), and real coding tasks (Aider).</li>
<li><b>Rank within each source.</b> Every model gets a rank (1st, 2nd, 3rd&hellip;) on each leaderboard it appears on.</li>
<li><b>Match models.</b> The same model is often named differently per site, so we normalize casing and vendor names &mdash; but <b>every distinct variant stays its own row</b> (e.g. GPT-5, GPT-5 (high) and GPT-5 (low) are ranked separately, no roll-ups). We keep each variant's <i>best</i> rank per source.</li>
<li><b>Average.</b> A model's <b>average rank</b> is the mean of its ranks across sources. Ties break on #1st-place finishes, then source count.</li>
<li><b>Filter.</b> The Overall tab needs a model on at least 2 sources; category tabs need at least 1. Top 60 shown per tab.</li>
</ol>
<ul class="cav">
<li>Different sources measure different things (human vibes vs. benchmarks vs. coding), so averaging is a rough consensus &mdash; not a precise score.</li>
<li>Some leaderboards refresh daily, others monthly. Each source's own date is shown above.</li>
<li><b>Open Weights / Self-Hosted tabs</b> are filtered from the Overall ranking using a <b>curated list</b> (<a href="https://github.com/goshitsarch-eng/metarank/blob/main/metarank/data/open_models.json">open_models.json</a>), not auto-detection. It reflects well-known openly-licensed families and which ones people commonly run locally.</li>
<li><b>Region filter:</b> each model's region is its lab's headquarters country, from a curated map (<a href="https://github.com/goshitsarch-eng/metarank/blob/main/metarank/data/model_origins.json">model_origins.json</a>) — USA, China, Europe, Canada, UK, Singapore, UAE, or Other.</li>
<li>Spot something wrong or missing in the curated lists? Corrections are welcome via GitHub pull request.</li>
<li>Refreshed daily by an automated pipeline; see the <a href="data.json">raw data</a>.</li>
</ul>
</div>

<footer>
<span class="brand">MetaRank</span> &mdash; the leaderboard of leaderboards &middot;
<a href="data.json">data.json</a> &middot; refreshed daily
</footer>
</div>

<script>
var PAYLOAD = %%PAYLOAD%%;
var tabs = PAYLOAD.tabs, order = ["overall","chat","coding","agents","pricing","open","selfhosted"];
var srcMeta = {}; PAYLOAD.source_directory.forEach(function(s){srcMeta[s.id]=s;});
var state = {tab:"overall", sortK:"pos", sortDir:1, filter:"", minSrc:0, region:""};
var lastRows = [];   // rows as last rendered (for export)
var lastIsPricing = false;

function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}

function isPricing(){ return state.tab==="pricing"; }
function isOpenTab(){ return state.tab==="open" || state.tab==="selfhosted"; }

function priceFmt(v){
  if(v==null) return "\u2014";
  return v < 0.01 ? "$"+v.toFixed(4) : "$"+v.toFixed(2);
}

// columns per tab type: [key, label]
function columns(){
  if(isPricing())
    return [["pos","#"],["name","Model"],["avg_rank","Avg rank"],["input_1m","Input $/1M"],["output_1m","Output $/1M"]];
  if(isOpenTab())
    return [["pos","#"],["name","Model"],["avg_rank","Avg rank"],["params","Params"],["n_sources","Sources"],["firsts","#1sts"]];
  return [["pos","#"],["name","Model"],["avg_rank","Avg rank"],["n_sources","Sources"],["firsts","#1sts"]];
}

function initTabs(){
  var el = document.getElementById("tabs");
  el.innerHTML = "";
  order.forEach(function(id){
    if(!tabs[id]) return;
    var b = document.createElement("button");
    b.textContent = tabs[id].label; b.setAttribute("role","tab");
    b.setAttribute("aria-selected", id===state.tab ? "true":"false");
    b.onclick = function(){ state.tab=id; state.sortK="pos"; state.sortDir=1;
      state.filter=""; document.getElementById("filter").value="";
      initTabs(); render(); };
    el.appendChild(b);
  });
}

function valOf(m,k){
  if(k==="pos") return m._pos;
  if(k==="name") return m.name.toLowerCase();
  if(k==="avg_rank") return m.avg_rank;
  if(k==="n_sources") return m.n_sources;
  if(k==="firsts") return m.placements["1"];
  if(k==="input_1m") return m.input_1m==null ? Infinity : m.input_1m;
  if(k==="output_1m") return m.output_1m==null ? Infinity : m.output_1m;
  if(k==="params") return m.params_b==null ? Infinity : m.params_b;
  return 0;
}

function cellFor(m, k){
  switch(k){
    case "pos": return '<td><span class="rankbadge">'+m._pos+"</span></td>";
    case "name": return '<td><button class="modelbtn">'+esc(m.name)+
      '<span class="org">'+esc(m.org||"")+"</span></button></td>";
    case "avg_rank": return '<td class="num">'+m.avg_rank.toFixed(2)+"</td>";
    case "n_sources": return '<td class="num">'+m.n_sources+"</td>";
    case "firsts": return '<td class="num firsts">'+m.placements["1"]+"</td>";
    case "input_1m": return '<td class="num">'+priceFmt(m.input_1m)+"</td>";
    case "output_1m": return '<td class="num">'+priceFmt(m.output_1m)+"</td>";
    case "params": return '<td class="num">'+
      (m.params_b==null ? "\u2014" : m.params_b+"B")+"</td>";
  }
  return "<td></td>";
}

function renderHead(){
  var tr = document.createElement("tr");
  columns().forEach(function(c){
    var th = document.createElement("th");
    th.setAttribute("data-k", c[0]);
    th.innerHTML = esc(c[1]) + (c[0]==="pos" ? "" : " \u21c5");
    th.onclick = function(){
      if(state.sortK===c[0]){ state.sortDir*=-1; } else { state.sortK=c[0]; state.sortDir=1; }
      render();
    };
    tr.appendChild(th);
  });
  var thead = document.getElementById("thead");
  thead.innerHTML = ""; thead.appendChild(tr);
}

function render(){
  var t = tabs[state.tab];
  lastIsPricing = isPricing();
  document.querySelectorAll("#tabs button").forEach(function(b){
    b.setAttribute("aria-selected", b.textContent===t.label ? "true":"false");
  });
  var srcNames = t.source_ids.map(function(id){
    var s=srcMeta[id]; if(!s) return "";
    return '<a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.name)+"</a>";
  }).join(", ");
  var line = esc(t.blurb)+" &middot; based on "+t.source_ids.length+" source"+(t.source_ids.length===1?"":"s")+": "+srcNames+
    " &middot; min "+t.min_sources+" source"+(t.min_sources===1?"":"s");
  if(lastIsPricing) line += ' &middot; prices live from <a href="https://openrouter.ai/models" target="_blank" rel="noopener">OpenRouter</a>';
  if(isOpenTab()) line += ' &middot; open-weight status from a <a href="https://github.com/goshitsarch-eng/metarank/blob/main/metarank/data/open_models.json" target="_blank" rel="noopener">curated list</a> &mdash; corrections welcome via pull request';
  document.getElementById("tabline").innerHTML = line;
  renderHead();
  var q = state.filter.trim().toLowerCase();
  var rows = t.models.map(function(m,i){ m._pos=i+1; return m; })
    .filter(function(m){
      if(m.n_sources < state.minSrc) return false;
      if(state.region && m.region !== state.region) return false;
      return !q || m.name.toLowerCase().indexOf(q)>-1 ||
        (m.org||"").toLowerCase().indexOf(q)>-1;
    });
  if(state.sortK!=="pos"){
    rows = rows.slice().sort(function(a,b){
      var x=valOf(a,state.sortK), y=valOf(b,state.sortK);
      return (x<y?-1:x>y?1:0)*state.sortDir;
    });
  }
  lastRows = rows;
  var ncol = columns().length;
  var tb = document.getElementById("rows"); tb.innerHTML="";
  if(!rows.length){
    tb.innerHTML='<tr><td colspan="'+ncol+'" style="text-align:center;color:var(--muted);padding:24px">No models match.</td></tr>';
    return;
  }
  rows.forEach(function(m){
    var tr = document.createElement("tr"); tr.className="main";
    tr.innerHTML = columns().map(function(c){ return cellFor(m, c[0]); }).join("");
    var det = document.createElement("tr"); det.className="detail hidden";
    var chips = t.source_ids.map(function(sid){
      var r = m.ranks[sid]; if(r==null) return "";
      var s = srcMeta[sid]; if(!s) return "";
      return '<span class="chip"><b>#'+r+"</b>"+
        '<a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.name)+"</a>"+
        (s.data_date ? " &middot; "+esc(s.data_date) : "")+"</span>";
    }).join("");
    det.innerHTML = '<td colspan="'+ncol+'"><div class="chips">'+chips+"</div></td>";
    tr.querySelector(".modelbtn").onclick = function(){ det.classList.toggle("hidden"); };
    tb.appendChild(tr); tb.appendChild(det);
  });
}

function download(name, text, type){
  var b = new Blob([text], {type: type});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = name;
  document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 800);
}
function csvEsc(v){
  v = String(v==null ? "" : v);
  return /[",\\n]/.test(v) ? '"'+v.replace(/"/g,'""')+'"' : v;
}
function colVal(m, k){
  if(k==="pos") return m._pos;
  if(k==="name") return m.name;
  if(k==="avg_rank") return m.avg_rank;
  if(k==="n_sources") return m.n_sources;
  if(k==="firsts") return m.placements["1"];
  if(k==="input_1m") return m.input_1m==null ? "" : m.input_1m;
  if(k==="output_1m") return m.output_1m==null ? "" : m.output_1m;
  if(k==="params") return m.params_b==null ? "" : m.params_b;
  return "";
}
function colHead(k){
  return {pos:"rank", name:"model", avg_rank:"avg_rank", n_sources:"n_sources",
          firsts:"firsts", input_1m:"input_usd_per_1m",
          output_1m:"output_usd_per_1m", params:"params_b"}[k] || k;
}
function exportCSV(){
  var cols = columns().map(function(c){ return c[0]; });
  var csv = cols.map(colHead).join(",")+"\\n" +
    lastRows.map(function(m){
      return cols.map(function(k){ return csvEsc(colVal(m, k)); }).join(",");
    }).join("\\n") + "\\n";
  download("metarank-"+state.tab+".csv", csv, "text/csv");
}
function exportJSON(){
  var data = lastRows.map(function(m){
    var o = {rank:m._pos, model:m.name, org:m.org||null, avg_rank:m.avg_rank,
             n_sources:m.n_sources, firsts:m.placements["1"], ranks:m.ranks,
             region:m.region||null};
    if(lastIsPricing){
      o.input_usd_per_1m = m.input_1m; o.output_usd_per_1m = m.output_1m;
    }
    if(m.open_weights || m.self_hostable || m.params_b!=null){
      o.open_weights = !!m.open_weights;
      o.self_hostable = !!m.self_hostable;
      o.params_b = m.params_b;
    }
    return o;
  });
  download("metarank-"+state.tab+".json",
           JSON.stringify({tab:state.tab, generated_at:PAYLOAD.generated_at, models:data}, null, 2),
           "application/json");
}
document.getElementById("filter").addEventListener("input", function(e){
  state.filter = e.target.value; render();
});
document.getElementById("minsrc").addEventListener("change", function(e){
  state.minSrc = parseInt(e.target.value, 10) || 0; render();
});
document.getElementById("region").addEventListener("change", function(e){
  state.region = e.target.value; render();
});
document.getElementById("expCsv").addEventListener("click", exportCSV);
document.getElementById("expJson").addEventListener("click", exportJSON);

(function(){
  var d = new Date(PAYLOAD.generated_at);
  document.getElementById("updated").textContent =
    "Last updated " + d.toUTCString().replace(" GMT"," UTC");
  var live = PAYLOAD.source_directory.filter(function(s){return s.live;}).length;
  var overall = tabs.overall ? tabs.overall.models : [];
  var top = overall.length ? overall[0].name : "\u2014";
  document.getElementById(\"stats\").innerHTML =
    \"<div class='stat'><div class='v'>\"+live+\"<span class='grad'>/\"+PAYLOAD.source_directory.length+\"</span></div><div class='k'>Sources live</div></div>\"+
    \"<div class='stat'><div class='v'>\"+overall.length+\"</div><div class='k'>Models ranked</div></div>\"+
    \"<div class='stat'><div class='v grad' style='font-size:1rem;line-height:1.9'>\"+esc(top)+\"</div><div class='k'>#1 right now</div></div>\";
  var sc = document.getElementById("srclist");
  PAYLOAD.source_directory.forEach(function(s){
    var div = document.createElement("div"); div.className="src";
    var st = s.live
      ? '<span class="st live">&#9679; live &middot; '+s.n_models+' models'+(s.data_date?" &middot; data "+esc(s.data_date):"")+"</span>"
      : '<span class="st skip">&#9679; skipped this run (needs API key)</span>';
    div.innerHTML = '<div class="nm"><a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.name)+"</a>"+
      '<span class="cat">'+esc(PAYLOAD.cat_labels[s.category]||s.category)+"</span></div>"+
      "<p>"+esc(s.what)+"</p>"+st;
    sc.appendChild(div);
  });
  initTabs(); render();
})();
</script>
</body>
</html>
"""

def latest_data():
    files = [f for f in glob.glob(os.path.join(ROOT, "data-*.json"))
             if re.search(r"data-\d{4}-\d{2}-\d{2}\.json$", f)]
    if not files:
        raise SystemExit("no data-YYYY-MM-DD.json found in repo root")
    return max(files)

def main():
    src_path = latest_data()
    with open(src_path) as fh:
        data = json.load(fh)
    fetched = {s["id"]: s for s in data.get("sources", [])}
    has_pricing = bool(data.get("pricing"))
    directory = []
    for k in KNOWN_SOURCES:
        f = fetched.get(k["id"], {})
        live = k["id"] in fetched or (k["id"] == "openrouter" and has_pricing)
        directory.append({
            "id": k["id"], "name": k["name"], "url": k["url"],
            "what": k["what"], "category": k["category"],
            "live": live,
            "data_date": f.get("data_date"),
            "n_models": f.get("n_models") if k["id"] != "openrouter"
                        else len(data.get("pricing", {})),
        })
    # per-tab category labels for the source cards
    payload = {
        "generated_at": data.get("generated_at"),
        "source_directory": directory,
        "cat_labels": CAT_LABEL,
        "tabs": data.get("tabs", {}),
    }

    docs = os.path.join(ROOT, "docs")
    os.makedirs(docs, exist_ok=True)

    # brand assets (rewritten each build so daily rebuilds keep the branding)
    with open(os.path.join(docs, "logo.svg"), "w") as fh:
        fh.write(LOGO_SVG)
    with open(os.path.join(docs, "favicon.svg"), "w") as fh:
        fh.write(FAVICON_SVG)

    # inject payload into template
    page = TEMPLATE.replace("%%PAYLOAD%%", json.dumps(payload))
    with open(os.path.join(docs, "index.html"), "w") as fh:
        fh.write(page)
    with open(os.path.join(docs, "data.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    print(f"built docs/index.html + docs/data.json + brand SVGs from {os.path.basename(src_path)}")

if __name__ == "__main__":
    main()
