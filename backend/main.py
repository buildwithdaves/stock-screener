from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import math
import requests
import os
from datetime import datetime, timedelta

app = FastAPI(title="Stock & Options Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AV_KEY = os.environ.get("ALPHA_VANTAGE_KEY")
AV_BASE = "https://www.alphavantage.co/query"

YF_HEADERS = {
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


def av_get(params):
    params["apikey"] = AV_KEY
    r = requests.get(AV_BASE, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def yf_get(path, params=None):
    url = f"https://query1.finance.yahoo.com{path}"
    r = requests.get(url, headers=YF_HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        url = f"https://query2.finance.yahoo.com{path}"
        r = requests.get(url, headers=YF_HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    t = ticker.upper().strip()
    try:
        # Get quote from Alpha Vantage
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

        # Get company overview from Alpha Vantage
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

        # Get 1Y daily price history
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
