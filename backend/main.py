from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from datetime import datetime
import math

app = FastAPI(title="Stock & Options Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except:
        return None


@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        hist = stock.history(period="1y")

        if hist.empty:
            raise HTTPException(status_code=404, detail="Ticker not found")

        price_data = []
        for date, row in hist.iterrows():
            price_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": safe_float(row["Open"]),
                "high": safe_float(row["High"]),
                "low": safe_float(row["Low"]),
                "close": safe_float(row["Close"]),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None
            })

        current_price = safe_float(
    info.get("currentPrice") or 
    info.get("regularMarketPrice") or 
    info.get("navPrice") or
    (hist["Close"].iloc[-1] if not hist.empty else None)
)

if not current_price:
    raise HTTPException(status_code=404, detail="Could not retrieve price data")
```

Also update the `requirements.txt` to use the latest yfinance:
```
fastapi==0.111.0
uvicorn==0.30.1
yfinance==0.2.44
pandas==2.2.2
numpy<2.0
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", ticker.upper()),
            "current_price": current_price,
            "previous_close": safe_float(info.get("previousClose")),
            "open": safe_float(info.get("open")),
            "day_high": safe_float(info.get("dayHigh")),
            "day_low": safe_float(info.get("dayLow")),
            "week_52_high": safe_float(info.get("fiftyTwoWeekHigh")),
            "week_52_low": safe_float(info.get("fiftyTwoWeekLow")),
            "market_cap": info.get("marketCap"),
            "pe_ratio": safe_float(info.get("trailingPE")),
            "forward_pe": safe_float(info.get("forwardPE")),
            "eps": safe_float(info.get("trailingEps")),
            "dividend_yield": safe_float(info.get("dividendYield")),
            "beta": safe_float(info.get("beta")),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": info.get("longBusinessSummary", "")[:500],
            "price_history": price_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/options/{ticker}")
def get_options(ticker: str, expiration: str = None):
    try:
        stock = yf.Ticker(ticker.upper())
        expirations = stock.options

        if not expirations:
            raise HTTPException(status_code=404, detail="No options data available")

        info = stock.info
        current_price = safe_float(
            info.get("currentPrice") or
            info.get("regularMarketPrice") or
            stock.history(period="1d")["Close"].iloc[-1]
        )

        selected_exp = expiration if expiration in expirations else expirations[0]
        chain = stock.option_chain(selected_exp)

        def process_chain(df, option_type):
            results = []
            for _, row in df.iterrows():
                strike = safe_float(row.get("strike"))
                premium = safe_float(row.get("lastPrice")) or safe_float(row.get("ask")) or 0
                bid = safe_float(row.get("bid"))
                ask = safe_float(row.get("ask"))
                mid_premium = round((bid + ask) / 2, 4) if bid and ask else premium

                if not strike or not current_price:
                    continue

                if option_type == "call":
                    breakeven = round(strike + mid_premium, 2)
                    pct_to_breakeven = round(((breakeven - current_price) / current_price) * 100, 2)
                else:
                    breakeven = round(strike - mid_premium, 2)
                    pct_to_breakeven = round(((current_price - breakeven) / current_price) * 100, 2)

                scenarios = {}
                multipliers = {
                    "-50%": -0.50, "-25%": -0.25, "-10%": -0.10,
                    "+10%": 0.10, "+25%": 0.25, "+50%": 0.50,
                    "+75%": 0.75, "+100%": 1.00
                }
                for label, pct in multipliers.items():
                    scenario_price = current_price * (1 + pct)
                    if option_type == "call":
                        intrinsic = max(0, scenario_price - strike)
                    else:
                        intrinsic = max(0, strike - scenario_price)
                    pnl_per_share = round(intrinsic - mid_premium, 2)
                    pnl_per_contract = round(pnl_per_share * 100, 2)
                    pct_return = round((pnl_per_share / mid_premium) * 100, 1) if mid_premium > 0 else None
                    scenarios[label] = {
                        "scenario_price": round(scenario_price, 2),
                        "pnl_per_share": pnl_per_share,
                        "pnl_per_contract": pnl_per_contract,
                        "pct_return": pct_return,
                        "profitable": pnl_per_share > 0
                    }

                iv = safe_float(row.get("impliedVolatility"))
                volume = int(row["volume"]) if pd.notna(row.get("volume")) else 0
                open_interest = int(row["openInterest"]) if pd.notna(row.get("openInterest")) else 0
                unusual_volume = volume > (open_interest * 0.5) if open_interest > 0 and volume > 100 else False

                results.append({
                    "contract_name": row.get("contractSymbol", ""),
                    "type": option_type,
                    "strike": strike,
                    "expiration": selected_exp,
                    "bid": bid,
                    "ask": ask,
                    "last_price": premium,
                    "mid_premium": mid_premium,
                    "cost_per_contract": round(mid_premium * 100, 2),
                    "volume": volume,
                    "open_interest": open_interest,
                    "implied_volatility": round(iv * 100, 2) if iv else None,
                    "in_the_money": bool(row.get("inTheMoney", False)),
                    "breakeven": breakeven,
                    "pct_to_breakeven": pct_to_breakeven,
                    "unusual_volume": unusual_volume,
                    "scenarios": scenarios
                })
            return results

        calls = process_chain(chain.calls, "call")
        puts = process_chain(chain.puts, "put")

        return {
            "ticker": ticker.upper(),
            "current_price": current_price,
            "expirations": list(expirations),
            "selected_expiration": selected_exp,
            "calls": calls,
            "puts": puts
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
