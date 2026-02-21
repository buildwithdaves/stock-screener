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
    fon
