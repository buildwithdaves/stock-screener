# AlphaLens Terminal 📈

A Bloomberg-style stock screener with full options chain analysis, breakeven calculations, and payout scenarios.

## Features

- **Stock Overview** — Price chart (1Y), key metrics, fundamentals
- **Options Chain** — Full calls/puts chain with bid/ask/mid/IV/volume/OI
- **Breakeven Analysis** — Breakeven price and % move required per strike
- **Payout Scenarios** — P&L per contract at -50%, -25%, -10%, +10%, +25%, +50%, +75%, +100%
- **Smart Flags** — ITM highlighting, unusual volume detection (HOT)
- **Toggle** — Switch between $/contract and % return views

---

## Project Structure

```
stock-screener/
├── backend/         ← FastAPI + yfinance (deploy to Render)
│   ├── main.py
│   ├── requirements.txt
│   └── render.yaml
└── frontend/        ← React (deploy to Vercel)
    ├── src/
    │   ├── App.js
    │   └── index.js
    ├── public/
    │   └── index.html
    ├── package.json
    └── vercel.json
```

---

## Deployment Guide

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - AlphaLens Terminal"
git remote add origin https://github.com/Buildwithdaves/stock-screener.git
git push -u origin main
```

### Step 2 — Deploy Backend to Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Set **Root Directory** to `backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Choose the **Free** tier
7. Deploy → copy your URL (e.g. `https://stock-screener-api.onrender.com`)

### Step 3 — Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add Environment Variable:
   - Key: `REACT_APP_API_URL`
   - Value: your Render backend URL from Step 2
5. Deploy → your app is live!

### Step 4 — Every future update

```bash
git add .
git commit -m "Your update message"
git push
```
Vercel and Render will auto-redeploy on every push. ✅

---

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# Runs at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm start
# Runs at http://localhost:3000
# Proxy → localhost:8000 for API calls
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /stock/{ticker}` | Stock data + 1Y price history |
| `GET /options/{ticker}` | Options chain (all expirations) |
| `GET /options/{ticker}?expiration=2025-03-21` | Specific expiration |
| `GET /health` | Health check |

---

## Notes

- Data sourced from Yahoo Finance via `yfinance` — free, no API key required
- Options scenarios use mid-price (bid+ask)/2 for calculations
- "HOT" flag = volume > 50% of open interest (unusual activity signal)
- Scenarios assume held to expiration — does not model theta decay

---

*Built with FastAPI + React + Recharts*
