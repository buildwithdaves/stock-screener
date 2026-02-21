from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import math
import requests
from datetime import datetime, timedelta

app = FastAPI(title="Stock & Options Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

YF_BASE = "https://query1.finance.yahoo.com"
YF_BASE2 = "https://query2.finance.yahoo.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://finance.yahoo.com",
    "Referer": "https://finance.yahoo.com",
}


def safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else round(f, 4)
    except:
        return None


def yf_get(path, params=None, use_base2=False):
    base = YF_BASE2 if use_base2 else YF_BASE
    url = f"{base}{path}"
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError:
        alt = YF_BASE if use_base2 else YF_BASE2
        r = requests.get(f"{alt}{path}", headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()


@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    t = ticker.upper().strip()
    try:
        data = yf_get("/v10/finance/quoteSummary/" + t, params={
            "modules": "price,summaryDetail,defaultKeyStatistics,assetProfile"
        })

        result = data.get("quoteSummary", {}).get("result")
        if not result:
            raise HTTPException(status_code=404, detail="Ticker not found")

        price = result[0].get("price", {})
        summary = result[0].get("summaryDetail", {})
        stats = result[0].get("defaultKeyStatistics", {})
        profile = result[0].get("assetProfile", {})

        current_price = safe_float(price.get("regularMarketPrice", {}).get("raw"))
        if not current_price:
            raise HTTPException(status_code=404, detail="Could not retrieve price data")

        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=365)).timestamp())
        hist_data = yf_get("/v8/finance/chart/" + t, params={
            "period1": start,
            "period2": end,
            "interval": "1d"
        })

        price_history = []
        chart = hist_data.get("chart", {}).get("result", [{}])[0]
        timestamps = chart.get("timestamp", [])
        closes = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        opens = chart.get("indicators", {}).get("quote", [{}])[0].get("open", [])
        highs = chart.get("indicators", {}).get("quote", [{}])[0].get("high", [])
        lows = chart.get("indicators", {}).get("quote", [{}])[0].get("low", [])
        volumes = chart.get("indicators", {}).get("quote", [{}])[0].get("volume", [])

        for i, ts in enumerate(timestamps):
            try:
                price_history.append({
                    "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                    "open": safe_float(opens[i]) if i < len(opens) else None,
                    "high": safe_float(highs[i]) if i < len(highs) else None,
                    "low": safe_float(lows[i]) if i < len(lows) else None,
                    "close": safe_float(closes[i]) if i < len(closes) else None,
                    "volume": int(volumes[i]) if i < len(volumes) and volumes[i] else None,
                })
            except:
                continue

        def raw(d, key):
            return safe_float(d.get(key, {}).get("raw")) if isinstance(d.get(key), dict) else safe_float(d.get(key))

        return {
            "ticker": t,
            "name": price.get("longName") or price.get("shortName") or t,
            "current_price": current_price,
            "previous_close": raw(price, "regularMarketPreviousClose"),
            "open": raw(price, "regularMarketOpen"),
            "day_high": raw(price, "regularMarketDayHigh"),
            "day_low": raw(price, "regularMarketDayLow"),
            "week_52_high": raw(summary, "fiftyTwoWeekHigh"),
            "week_52_low": raw(summary, "fiftyTwoWeekLow"),
            "market_cap": raw(price, "marketCap"),
            "pe_ratio": raw(summary, "trailingPE"),
            "forward_pe": raw(summary, "forwardPE"),
            "eps": raw(stats, "trailingEps"),
            "dividend_yield": raw(summary, "dividendYield"),
            "beta": raw(summary, "beta"),
            "volume": raw(price, "regularMarketVolume"),
            "avg_volume": raw(summary, "averageVolume"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "description": (profile.get("longBusinessSummary") or "")[:500],
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
        params = {"getAllData": "true"}
        if expiration:
            try:
                params["date"] = int(datetime.strptime(expiration, "%Y-%m-%d").timestamp())
            except:
                pass

        data = yf_get(f"/v7/finance/options/{t}", params=params)

        result = data.get("optionChain", {}).get("result")
        if not result:
            raise HTTPException(status_code=404, detail="No options data available")

        chain_data = result[0]
        current_price = safe_float(chain_data.get("quote", {}).get("regularMarketPrice"))
        if not current_price:
            raise HTTPException(status_code=400, detail="Could not determine current price")

        exp_timestamps = chain_data.get("expirationDates", [])
        expirations = [datetime.fromtimestamp(ts).strftime("%Y-%m-%d") for ts in exp_timestamps]

        options = chain_data.get("options", [{}])[0]
        calls_raw = options.get("calls", [])
        puts_raw = options.get("puts", [])

        selected_exp = expiration if expiration in expirations else (expirations[0] if expirations else "")

        def process_chain(raw_options, option_type):
            results = []
            for opt in raw_options:
                try:
                    strike = safe_float(opt.get("strike"))
                    bid = safe_float(opt.get("bid"))
                    ask = safe_float(opt.get("ask"))
                    last = safe_float(opt.get("lastPrice"))
                    mid_premium = round((bid + ask) / 2, 4) if (bid and ask) else (last or 0)

                    if not strike or not mid_premium:
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

                    iv = safe_float(opt.get("impliedVolatility"))
                    volume = int(opt.get("volume", 0) or 0)
                    open_interest = int(opt.get("openInterest", 0) or 0)
                    unusual_volume = volume > (open_interest * 0.5) if open_interest > 0 and volume > 100 else False

                    exp_ts = opt.get("expiration")
                    exp_str = datetime.fromtimestamp(exp_ts).strftime("%Y-%m-%d") if exp_ts else selected_exp

                    results.append({
                        "contract_name": opt.get("contractSymbol", ""),
                        "type": option_type,
                        "strike": strike,
                        "expiration": exp_str,
                        "bid": bid,
                        "ask": ask,
                        "last_price": last,
                        "mid_premium": mid_premium,
                        "cost_per_contract": round(mid_premium * 100, 2),
                        "volume": volume,
                        "open_interest": open_interest,
                        "implied_volatility": round(iv * 100, 2) if iv else None,
                        "in_the_money": bool(opt.get("inTheMoney", False)),
                        "breakeven": breakeven,
                        "pct_to_breakeven": pct_to_breakeven,
                        "unusual_volume": unusual_volume,
                        "scenarios": scenarios
                    })
                except Exception:
                    continue
            return results

        return {
            "ticker": t,
            "current_price": current_price,
            "expirations": expirations,
            "selected_expiration": selected_exp,
            "calls": process_chain(calls_raw, "call"),
            "puts": process_chain(puts_raw, "put")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
