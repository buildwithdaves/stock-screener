import React, { useState, useCallback, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine
} from "recharts";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const SCENARIOS = ["-50%", "-25%", "-10%", "+10%", "+25%", "+50%", "+75%", "+100%"];

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Barlow+Condensed:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #050a0e;
    --surface: #0a1520;
    --surface2: #0f1e2d;
    --border: #1a3048;
    --border2: #0d2035;
    --green: #00e676;
    --green-dim: #00c853;
    --green-glow: rgba(0,230,118,0.15);
    --red: #ff1744;
    --red-dim: #d50000;
    --red-glow: rgba(255,23,68,0.12);
    --cyan: #00b8d4;
    --amber: #ffab00;
    --text: #c8dde8;
    --text-dim: #5a7a90;
    --text-bright: #e8f4fa;
    --mono: 'Space Mono', monospace;
    --sans: 'Barlow Condensed', sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    min-height: 100vh;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.03) 2px,
      rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
  }

  .app { max-width: 1600px; margin: 0 auto; padding: 0 20px 60px; }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 0 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
  }
  .header-logo {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--green);
    letter-spacing: 4px;
    text-transform: uppercase;
  }
  .header-logo span { color: var(--text-dim); }
  .header-time {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 1px;
  }

  .search-row {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
    align-items: center;
  }
  .search-input-wrap {
    position: relative;
    flex: 0 0 300px;
  }
  .search-prefix {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    font-family: var(--mono);
    color: var(--green);
    font-size: 13px;
    pointer-events: none;
  }
  .search-input {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-bright);
    font-family: var(--mono);
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 3px;
    padding: 12px 14px 12px 34px;
    text-transform: uppercase;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .search-input:focus {
    border-color: var(--green);
    box-shadow: 0 0 0 3px var(--green-glow), inset 0 0 20px rgba(0,230,118,0.03);
  }
  .search-btn {
    background: var(--green);
    color: #000;
    border: none;
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 13px 24px;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.2s, transform 0.1s;
  }
  .search-btn:hover { background: var(--green-dim); }
  .search-btn:active { transform: scale(0.97); }
  .search-btn:disabled { background: var(--border); color: var(--text-dim); cursor: not-allowed; }
  .quick-tickers {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .quick-pill {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 1px;
    padding: 6px 12px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .quick-pill:hover { border-color: var(--cyan); color: var(--cyan); }

  .error-bar {
    background: rgba(255,23,68,0.1);
    border: 1px solid var(--red);
    color: var(--red);
    font-family: var(--mono);
    font-size: 11px;
    padding: 10px 16px;
    margin-bottom: 20px;
  }

  .stock-overview {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 20px;
    margin-bottom: 24px;
  }
  @media (max-width: 900px) { .stock-overview { grid-template-columns: 1fr; } }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 20px;
  }

  .stock-header { margin-bottom: 16px; }
  .stock-ticker {
    font-family: var(--mono);
    font-size: 28px;
    font-weight: 700;
    color: var(--text-bright);
    letter-spacing: 2px;
  }
  .stock-name {
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text-dim);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 2px;
  }
  .stock-sector {
    display: inline-block;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--cyan);
    border: 1px solid var(--cyan);
    padding: 2px 8px;
    margin-top: 6px;
    letter-spacing: 1px;
  }
  .price-row {
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin: 12px 0;
  }
  .price-main {
    font-family: var(--mono);
    font-size: 42px;
    font-weight: 700;
    color: var(--text-bright);
    letter-spacing: -1px;
  }
  .price-change {
    font-family: var(--mono);
    font-size: 16px;
    font-weight: 700;
  }
  .pos { color: var(--green); }
  .neg { color: var(--red); }
  .neu { color: var(--text-dim); }

  .chart-wrap { height: 200px; margin-top: 8px; }
  .chart-tooltip {
    background: var(--surface2);
    border: 1px solid var(--border);
    padding: 8px 12px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px;
  }
  .stat-row {
    background: var(--surface2);
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .stat-label {
    font-family: var(--mono);
    font-size: 9px;
    color: var(--text-dim);
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }
  .stat-value {
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 700;
    color: var(--text-bright);
  }

  .options-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .section-title {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--green);
  }
  .section-title-dim {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 16px;
  }

  .tab-group { display: flex; gap: 2px; }
  .tab-btn {
    background: var(--surface2);
    border: 1px solid var(--border2);
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 2px;
    padding: 8px 18px;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
  }
  .tab-btn.active-call { background: rgba(0,230,118,0.12); border-color: var(--green); color: var(--green); }
  .tab-btn.active-put { background: rgba(255,23,68,0.12); border-color: var(--red); color: var(--red); }
  .tab-btn:not(.active-call):not(.active-put):hover { border-color: var(--border); color: var(--text); }

  .exp-select {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: var(--mono);
    font-size: 11px;
    padding: 8px 12px;
    outline: none;
    cursor: pointer;
  }
  .exp-select:focus { border-color: var(--green); }

  .pnl-toggle {
    display: flex;
    gap: 2px;
    margin-left: auto;
  }
  .toggle-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 1px;
    padding: 6px 12px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .toggle-btn.active { background: var(--surface2); border-color: var(--amber); color: var(--amber); }

  .table-wrap { overflow-x: auto; }
  table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--mono);
    font-size: 11px;
  }
  thead th {
    background: var(--surface2);
    border-bottom: 2px solid var(--border);
    padding: 10px 8px;
    text-align: right;
    color: var(--text-dim);
    font-size: 9px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    white-space: nowrap;
    position: sticky;
    top: 0;
  }
  thead th:first-child, thead th:nth-child(2), thead th:nth-child(3) { text-align: left; }
  tbody tr {
    border-bottom: 1px solid var(--border2);
    transition: background 0.1s;
  }
  tbody tr:hover { background: rgba(255,255,255,0.02); }
  tbody tr.itm { background: rgba(0,230,118,0.04); }
  tbody tr.unusual { border-left: 2px solid var(--amber); }
  td {
    padding: 9px 8px;
    text-align: right;
    color: var(--text);
    white-space: nowrap;
  }
  td:first-child { text-align: left; }
  td:nth-child(2) { text-align: left; }
  td:nth-child(3) { text-align: left; }

  .strike-cell { font-weight: 700; color: var(--text-bright); font-size: 13px; }
  .itm-badge {
    display: inline-block;
    background: rgba(0,230,118,0.15);
    color: var(--green);
    font-size: 8px;
    padding: 1px 5px;
    letter-spacing: 1px;
    margin-left: 4px;
  }
  .unusual-badge {
    display: inline-block;
    background: rgba(255,171,0,0.15);
    color: var(--amber);
    font-size: 8px;
    padding: 1px 5px;
    letter-spacing: 1px;
    margin-left: 4px;
  }
  .breakeven-cell { color: var(--cyan); }
  .pct-cell { color: var(--amber); }

  .scenario-pos { color: var(--green); font-weight: 700; }
  .scenario-neg { color: var(--red); }
  .scenario-zero { color: var(--text-dim); }

  .atm-divider td {
    border-top: 2px dashed var(--amber) !important;
    padding-top: 10px;
  }

  .loading-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px;
    gap: 16px;
  }
  .loading-bar {
    width: 200px;
    height: 2px;
    background: var(--border);
    position: relative;
    overflow: hidden;
  }
  .loading-bar::after {
    content: '';
    position: absolute;
    left: -50%;
    top: 0;
    width: 50%;
    height: 100%;
    background: var(--green);
    animation: loading 1s ease-in-out infinite;
  }
  @keyframes loading {
    0% { left: -50%; }
    100% { left: 100%; }
  }
  .loading-text {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 3px;
    text-transform: uppercase;
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 100px 40px;
    gap: 12px;
    border: 1px dashed var(--border);
  }
  .empty-state-title {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 4px;
    color: var(--text-dim);
    text-transform: uppercase;
  }
  .empty-state-sub {
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text-dim);
  }
  .term-cursor {
    display: inline-block;
    width: 8px;
    height: 14px;
    background: var(--green);
    vertical-align: middle;
    animation: blink 1s step-end infinite;
    margin-left: 4px;
  }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

  .divider { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
`;

const fmt = (v, dec = 2) => v == null ? "—" : Number(v).toFixed(dec);
const fmtUSD = (v) => v == null ? "—" : "$" + Number(v).toFixed(2);
const fmtBig = (v) => {
  if (v == null) return "—";
  if (v >= 1e12) return "$" + (v / 1e12).toFixed(2) + "T";
  if (v >= 1e9) return "$" + (v / 1e9).toFixed(2) + "B";
  if (v >= 1e6) return "$" + (v / 1e6).toFixed(2) + "M";
  return "$" + v.toLocaleString();
};
const fmtVol = (v) => {
  if (v == null) return "—";
  if (v >= 1e6) return (v / 1e6).toFixed(1) + "M";
  if (v >= 1e3) return (v / 1e3).toFixed(0) + "K";
  return v.toString();
};

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span>
      {time.toLocaleTimeString("en-US", { hour12: false })}
      &nbsp;&nbsp;
      {time.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }).toUpperCase()}
    </span>
  );
}

function PriceChart({ data, currentPrice }) {
  if (!data || !data.length) return null;
  const startPrice = data[0].close;
  const isUp = currentPrice >= startPrice;
  const color = isUp ? "#00e676" : "#ff1744";

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <div>{payload[0].payload.date}</div>
        <div style={{ color }}>${fmt(payload[0].value)}</div>
      </div>
    );
  };

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.15} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" hide />
          <YAxis hide domain={["auto", "auto"]} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={startPrice} stroke="#1a3048" strokeDasharray="3 3" />
          <Area
            type="monotone" dataKey="close"
            stroke={color} strokeWidth={1.5}
            fill="url(#priceGrad)" dot={false}
            activeDot={{ r: 3, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function ScenarioCell({ scenario, mode }) {
  if (!scenario) return <td className="scenario-zero">—</td>;
  const val = mode === "pct" ? scenario.pct_return : scenario.pnl_per_contract;
  if (val == null) return <td className="scenario-zero">—</td>;
  const cls = val > 0 ? "scenario-pos" : val < 0 ? "scenario-neg" : "scenario-zero";
  const display = mode === "pct"
    ? (val > 0 ? "+" : "") + val.toFixed(0) + "%"
    : (val > 0 ? "+$" : "-$") + Math.abs(val).toFixed(0);
  return <td className={cls}>{display}</td>;
}

function OptionsTable({ options, type, mode }) {
  if (!options || !options.length) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "var(--text-dim)", fontFamily: "var(--mono)", fontSize: "11px" }}>
        NO OPTIONS DATA AVAILABLE
      </div>
    );
  }

  const sortedOptions = [...options].sort((a, b) => a.strike - b.strike);
  let atmIdx = -1;
  if (type === "call") {
    atmIdx = sortedOptions.findIndex((o, i) =>
      i > 0 && sortedOptions[i - 1].in_the_money && !o.in_the_money
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Strike</th>
            <th>Breakeven</th>
            <th>% to BE</th>
            <th>Bid</th>
            <th>Ask</th>
            <th>Mid</th>
            <th>Cost/Ct</th>
            <th>Vol</th>
            <th>OI</th>
            <th>IV%</th>
            {SCENARIOS.map(s => <th key={s}>{s}</th>)}
          </tr>
        </thead>
        <tbody>
          {sortedOptions.map((opt, i) => {
            const isAtm = i === atmIdx;
            return (
              <tr
                key={opt.contract_name}
                className={[
                  opt.in_the_money ? "itm" : "",
                  opt.unusual_volume ? "unusual" : "",
                  isAtm ? "atm-divider" : ""
                ].join(" ")}
              >
                <td>
                  <span className="strike-cell">${fmt(opt.strike, 0)}</span>
                  {opt.in_the_money && <span className="itm-badge">ITM</span>}
                  {opt.unusual_volume && <span className="unusual-badge">HOT</span>}
                </td>
                <td className="breakeven-cell">${fmt(opt.breakeven)}</td>
                <td className="pct-cell">
                  {opt.pct_to_breakeven != null
                    ? (opt.pct_to_breakeven > 0 ? "+" : "") + opt.pct_to_breakeven.toFixed(1) + "%"
                    : "—"}
                </td>
                <td>{opt.bid != null ? "$" + fmt(opt.bid) : "—"}</td>
                <td>{opt.ask != null ? "$" + fmt(opt.ask) : "—"}</td>
                <td style={{ color: "var(--text-bright)", fontWeight: 700 }}>
                  ${fmt(opt.mid_premium)}
                </td>
                <td>${fmt(opt.cost_per_contract, 0)}</td>
                <td style={{ color: opt.unusual_volume ? "var(--amber)" : "inherit" }}>
                  {fmtVol(opt.volume)}
                </td>
                <td>{fmtVol(opt.open_interest)}</td>
                <td>{opt.implied_volatility != null ? opt.implied_volatility + "%" : "—"}</td>
                {SCENARIOS.map(s => (
                  <ScenarioCell key={s} scenario={opt.scenarios?.[s]} mode={mode} />
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [optLoading, setOptLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [optionsData, setOptionsData] = useState(null);
  const [optionType, setOptionType] = useState("call");
  const [pnlMode, setPnlMode] = useState("dollar");
  const [selectedExp, setSelectedExp] = useState(null);

  const fetchOptions = useCallback(async (t, exp) => {
    setOptLoading(true);
    try {
      const url = exp
        ? `${API_BASE}/options/${t}?expiration=${exp}`
        : `${API_BASE}/options/${t}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error((await res.json()).detail || "Options fetch failed");
      const data = await res.json();
      setOptionsData(data);
      setSelectedExp(data.selected_expiration);
    } catch (e) {
      console.warn("Options error:", e.message);
    } finally {
      setOptLoading(false);
    }
  }, []);

  const search = useCallback(async (sym) => {
    const t = (sym || ticker).toUpperCase().trim();
    if (!t) return;
    setLoading(true);
    setError(null);
    setOptionsData(null);
    setSelectedExp(null);
    try {
      const res = await fetch(`${API_BASE}/stock/${t}`);
      if (!res.ok) throw new Error((await res.json()).detail || "Ticker not found");
      const data = await res.json();
      setStockData(data);
      setTicker(t);
      await fetchOptions(t, null);
    } catch (e) {
      setError(e.message);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  }, [ticker, fetchOptions]);

  const handleExpChange = (exp) => {
    setSelectedExp(exp);
    fetchOptions(stockData.ticker, exp);
  };

  const priceChange = stockData
    ? stockData.current_price - (stockData.previous_close || stockData.current_price)
    : 0;
  const pricePct = stockData?.previous_close
    ? (priceChange / stockData.previous_close) * 100
    : 0;

  return (
    <>
      <style>{styles}</style>
      <div className="app">
        <div className="header">
          <div className="header-logo">
            ▸ ALPHA<span>LENS</span> TERMINAL
          </div>
          <div className="header-time"><Clock /></div>
        </div>

        <div className="search-row">
          <div className="search-input-wrap">
            <span className="search-prefix">$</span>
            <input
              className="search-input"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === "Enter" && search()}
              placeholder="AAPL"
              maxLength={10}
            />
          </div>
          <button className="search-btn" onClick={() => search()} disabled={loading}>
            {loading ? "LOADING..." : "SCAN ▸"}
          </button>
          <div className="quick-tickers">
            {["AAPL", "TSLA", "NVDA", "SPY", "MSFT", "AMZN", "META"].map(t => (
              <button key={t} className="quick-pill" onClick={() => { setTicker(t); search(t); }}>
                {t}
              </button>
            ))}
          </div>
        </div>

        {error && <div className="error-bar">⚠ ERROR: {error.toUpperCase()}</div>}

        {loading && (
          <div className="loading-wrap">
            <div className="loading-bar" />
            <div className="loading-text">Fetching market data</div>
          </div>
        )}

        {!loading && stockData && (
          <>
            <div className="stock-overview">
              <div className="card">
                <div className="stock-header">
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                    <div>
                      <div className="stock-ticker">{stockData.ticker}</div>
                      <div className="stock-name">{stockData.name}</div>
                      {stockData.sector && <div className="stock-sector">{stockData.sector}</div>}
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontFamily: "var(--mono)", fontSize: "10px", color: "var(--text-dim)", letterSpacing: "1px" }}>
                        INDUSTRY
                      </div>
                      <div style={{ fontFamily: "var(--mono)", fontSize: "11px", color: "var(--text)", maxWidth: "200px", textAlign: "right" }}>
                        {stockData.industry || "—"}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="price-row">
                  <div className="price-main">${fmt(stockData.current_price)}</div>
                  <div className={`price-change ${priceChange >= 0 ? "pos" : "neg"}`}>
                    {priceChange >= 0 ? "▲" : "▼"} {Math.abs(priceChange).toFixed(2)} ({pricePct >= 0 ? "+" : ""}{pricePct.toFixed(2)}%)
                  </div>
                </div>
                <PriceChart data={stockData.price_history} currentPrice={stockData.current_price} />
              </div>

              <div className="card">
                <div className="section-title-dim">KEY METRICS</div>
                <div className="stats-grid">
                  {[
                    ["PREV CLOSE", fmtUSD(stockData.previous_close)],
                    ["OPEN", fmtUSD(stockData.open)],
                    ["DAY HIGH", fmtUSD(stockData.day_high)],
                    ["DAY LOW", fmtUSD(stockData.day_low)],
                    ["52W HIGH", fmtUSD(stockData.week_52_high)],
                    ["52W LOW", fmtUSD(stockData.week_52_low)],
                    ["MKT CAP", fmtBig(stockData.market_cap)],
                    ["P/E (TTM)", fmt(stockData.pe_ratio)],
                    ["FWD P/E", fmt(stockData.forward_pe)],
                    ["EPS (TTM)", fmtUSD(stockData.eps)],
                    ["BETA", fmt(stockData.beta)],
                    ["DIV YIELD", stockData.dividend_yield ? (stockData.dividend_yield * 100).toFixed(2) + "%" : "—"],
                    ["VOLUME", fmtVol(stockData.volume)],
                    ["AVG VOL", fmtVol(stockData.avg_volume)],
                  ].map(([label, val]) => (
                    <div className="stat-row" key={label}>
                      <div className="stat-label">{label}</div>
                      <div className="stat-value">{val}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <hr className="divider" />

            <div className="options-header">
              <div className="section-title">▸ OPTIONS CHAIN</div>
              <div className="tab-group">
                <button
                  className={`tab-btn ${optionType === "call" ? "active-call" : ""}`}
                  onClick={() => setOptionType("call")}
                >CALLS</button>
                <button
                  className={`tab-btn ${optionType === "put" ? "active-put" : ""}`}
                  onClick={() => setOptionType("put")}
                >PUTS</button>
              </div>
              {optionsData?.expirations && (
                <select
                  className="exp-select"
                  value={selectedExp || ""}
                  onChange={e => handleExpChange(e.target.value)}
                >
                  {optionsData.expirations.map(exp => (
                    <option key={exp} value={exp}>{exp}</option>
                  ))}
                </select>
              )}
              <div className="pnl-toggle">
                <button
                  className={`toggle-btn ${pnlMode === "dollar" ? "active" : ""}`}
                  onClick={() => setPnlMode("dollar")}
                >$/CT</button>
                <button
                  className={`toggle-btn ${pnlMode === "pct" ? "active" : ""}`}
                  onClick={() => setPnlMode("pct")}
                >% RET</button>
              </div>
            </div>

            <div style={{ display: "flex", gap: "20px", marginBottom: "12px", flexWrap: "wrap" }}>
              {[
                ["var(--green)", "ITM = In The Money"],
                ["var(--amber)", "HOT = Unusual Volume"],
                ["var(--amber)", "--- = ATM Divider"],
                ["var(--cyan)", "Breakeven Price"],
              ].map(([color, label]) => (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{ width: "8px", height: "8px", background: color }} />
                  <span style={{ fontFamily: "var(--mono)", fontSize: "9px", color: "var(--text-dim)", letterSpacing: "1px" }}>
                    {label}
                  </span>
                </div>
              ))}
            </div>

            <div className="card" style={{ padding: 0 }}>
              {optLoading ? (
                <div className="loading-wrap">
                  <div className="loading-bar" />
                  <div className="loading-text">Loading options chain</div>
                </div>
              ) : optionsData ? (
                <OptionsTable
                  options={optionType === "call" ? optionsData.calls : optionsData.puts}
                  type={optionType}
                  mode={pnlMode}
                />
              ) : (
                <div style={{ padding: "40px", textAlign: "center", color: "var(--text-dim)", fontFamily: "var(--mono)", fontSize: "11px" }}>
                  NO OPTIONS DATA
                </div>
              )}
            </div>

            <div style={{ marginTop: "12px", fontFamily: "var(--mono)", fontSize: "9px", color: "var(--text-dim)", lineHeight: "1.6", letterSpacing: "0.5px" }}>
              SCENARIOS SHOW P&L {pnlMode === "dollar" ? "PER CONTRACT (100 SHARES)" : "AS % RETURN ON PREMIUM"} IF HELD TO EXPIRATION.
              MID PREMIUM USED FOR CALCULATIONS. DOES NOT ACCOUNT FOR THETA DECAY OR EARLY ASSIGNMENT.
            </div>
          </>
        )}

        {!loading && !stockData && !error && (
          <div className="empty-state">
            <div className="empty-state-title">
              ENTER TICKER SYMBOL<span className="term-cursor" />
            </div>
            <div className="empty-state-sub">
              Search for any stock to view price data, key metrics, and full options chain with payout analysis
            </div>
          </div>
        )}
      </div>
    </>
  );
}
