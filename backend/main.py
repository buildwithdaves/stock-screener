from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import math
import requests
import os
from datetime import datetime

app = FastAPI(title="Stock & Options Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AV_KEY = os.environ.get("ALPHA_VANTAGE_KEY")
MD_KEY = os.environ.get("MARKET_DATA_KEY")
AV_BASE = "https://www.alphavantage.co/query"
MD_BASE = "https://api.marketdata.app/v1"


def safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except:
        return None


def av_get(params):
    params["apikey"] = AV_KEY
    r = requests.get(AV_BASE, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    t = ticker.upper().strip()
    try:
        quote_data = av_get({"function": "GLOBAL_QUOTE", "symbol": t})
        quote = quote_data.get("Global Quote", {})

        if not quote or not quote.get("05. price"):
            raise HTTPException(status_code=404, detail="Ticker not found")

        current_price = safe_float(quote.get("05. price"))
        previous_close = safe_float(quote.get("08. previous close"))
        open_price = safe_float(quote.get("02. open"))
        day_high = safe_float(quote.get("03. high"))
        day_low = safe_float(quote.get("04. low"))
        volume = safe_float(quote.get("06. volume"))

        overview_data = av_get({"function": "OVERVIEW", "symbol": t})
        name = overview_data.get("Name") or t
        sector = overview_data.get("Sector")
        industry = overview_data.get("Industry")
        description = (overview_data.get("Description") or "")[:500]
        market_cap = safe_float(overview_data.get("MarketCapitalization"))
        pe_ratio = safe_float(overview_data.get("TrailingPE"))
        forward_pe = safe_float(overview_data.get("ForwardPE"))
        eps = safe_float(overview_data.get("EPS"))
        beta = safe_float(overview_data.get("Beta"))
        week_52_high = safe_float(overview_data.get("52WeekHigh"))
        week_52_low = safe_float(overview_data.get("52WeekLow"))
        dividend_yield = safe_float(overview_data.get("DividendYield"))
        avg_volume = safe_float(overview_data.get("10DayAverageTradingVolume"))

        hist_data = av_get({"function": "TIME_SERIES_DAILY", "symbol": t, "outputsize": "compact"})
        time_series = hist_data.get("Time Series (Daily)", {})

        price_history = []
        for date_str, values in sorted(time_series.items()):
            price_history.append({
                "date": date_str,
                "open": safe_float(values.get("1. open")),
                "high": safe_float(values.get("2. high")),
                "low": safe_float(values.get("3. low")),
                "close": safe_float(values.get("4. close")),
                "volume": int(float(values.get("5. volume", 0)))
            })

        return {
            "ticker": t,
            "name": name,
            "current_price": current_price,
            "previous_close": previous_close,
            "open": open_price,
            "day_high": day_high,
            "day_low": day_low,
            "week_52_high": week_52_high,
            "week_52_low": week_52_low,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "forward_pe": forward_pe,
            "eps": eps,
            "dividend_yield": dividend_yield,
            "beta": beta,
            "volume": volume,
            "avg_volume": avg_volume,
            "sector": sector,
            "industry": industry,
            "description": description,
            "price_history": price_history
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/options/{ticker}")
def get_options(ticker: str, expiration: str = None):
    t = ticker.upper().strip()
    try:
        # Get current price
        quote_data = av_get({"function": "GLOBAL_QUOTE", "symbol": t})
        quote = quote_data.get("Global Quote", {})
        current_price = safe_float(quote.get("05. price"))

        if not current_price:
            raise HTTPException(status_code=400, detail="Could not determine current price")

        # Fetch options from Market Data App
        params = {"side": "all", "token": MD_KEY}
        if expiration:
            params["expiration"] = expiration

        r = requests.get(f"{MD_BASE}/options/chain/{t}/", params=params, timeout=15)
        data = r.json()

        print(f"MD response: s={data.get('s')} keys={list(data.keys())}")

        if data.get("s") == "error":
            raise HTTPException(status_code=404, detail=data.get("errmsg", "No options data"))

        if data.get("s") != "ok":
            raise HTTPException(status_code=404, detail="No options data available")

        all_expirations = sorted(set(data.get("expiration", [])))
        selected_exp = expiration or (all_expirations[0] if all_expirations else None)

        calls = []
        puts = []

        for i, symbol in enumerate(data.get("optionSymbol", [])):
            try:
                opt_type = data.get("side", [])[i]
                exp = data.get("expiration", [])[i]

                if selected_exp and exp != selected_exp:
                    continue

                strike = safe_float(data.get("strike", [])[i])
                bid = safe_float(data.get("bid", [])[i])
                ask = safe_float(data.get("ask", [])[i])
                last = safe_float(data.get("last", [])[i])
                mid_premium = round((bid + ask) / 2, 4) if (bid and ask) else (last or 0)

                if not strike or not mid_premium:
                    continue

                if opt_type == "call":
                    breakeven = round(strike + mid_premium, 2)
                    pct_to_breakeven = round(((breakeven - current_price) / current_price) * 100, 2)
                else:
                    breakeven = round(strike - mid_premium, 2)
                    pct_to_breakeven = round(((current_price - breakeven) / current_price) * 100, 2)

                in_the_money = (
                    (opt_type == "call" and current_price > strike) or
                    (opt_type == "put" and current_price < strike)
                )

                scenarios = {}
                multipliers = {
                    "-50%": -0.50, "-25%": -0.25, "-10%": -0.10,
                    "+10%": 0.10, "+25%": 0.25, "+50%": 0.50,
                    "+75%": 0.75, "+100%": 1.00
                }
                for label, pct in multipliers.items():
                    scenario_price = current_price * (1 + pct)
                    intrinsic = max(0, scenario_price - strike) if opt_type == "call" else max(0, strike - scenario_price)
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

                iv_list = data.get("iv", [])
                vol_list = data.get("volume", [])
                oi_list = data.get("openInterest", [])

                iv = safe_float(iv_list[i]) if i < len(iv_list) else None
                volume = int(vol_list[i] or 0) if i < len(vol_list) else 0
                open_interest = int(oi_list[i] or 0) if i < len(oi_list) else 0
                unusual_volume = volume > (open_interest * 0.5) if open_interest > 0 and volume > 100 else False

                option = {
                    "contract_name": symbol,
                    "type": opt_type,
                    "strike": strike,
                    "expiration": exp,
                    "bid": bid,
                    "ask": ask,
                    "last_price": last,
                    "mid_premium": mid_premium,
                    "cost_per_contract": round(mid_premium * 100, 2),
                    "volume": volume,
                    "open_interest": open_interest,
                    "implied_volatility": round(iv * 100, 2) if iv else None,
                    "in_the_money": in_the_money,
                    "breakeven": breakeven,
                    "pct_to_breakeven": pct_to_breakeven,
                    "unusual_volume": unusual_volume,
                    "scenarios": scenarios
                }

                if opt_type == "call":
                    calls.append(option)
                else:
                    puts.append(option)

            except Exception:
                continue

        return {
            "ticker": t,
            "current_price": current_price,
            "expirations": all_expirations,
            "selected_expiration": selected_exp,
            "calls": sorted(calls, key=lambda x: x["strike"]),
            "puts": sorted(puts, key=lambda x: x["strike"])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
