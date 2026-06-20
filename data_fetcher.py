import requests
from datetime import datetime, timezone

BINANCE_INTERVAL = {"15min": "15m", "1h": "1h"}


def get_binance_klines(binance_symbol: str, interval: str, limit: int = 300):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": binance_symbol,
            "interval": BINANCE_INTERVAL.get(interval, interval),
            "limit": limit,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
        return [
            {
                "time": float(c[0]) / 1000.0,
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
            }
            for c in raw
        ]
    except Exception as e:
        print(f"[data_fetcher] Binance klines error: {e}")
        return None


def get_binance_price(binance_symbol: str):
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        resp = requests.get(url, params={"symbol": binance_symbol}, timeout=10)
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception as e:
        print(f"[data_fetcher] Binance price error: {e}")
        return None


def get_twelvedata_klines(td_symbol: str, interval: str, api_key: str, outputsize: int = 300):
    try:
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": td_symbol,
            "interval": interval,
            "outputsize": outputsize,
            "timezone": "UTC",
            "apikey": api_key,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "error" or "values" not in data:
            print(f"[data_fetcher] Twelve Data error: {data}")
            return None
        values = list(reversed(data["values"]))
        result = []
        for v in values:
            try:
                t = datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                t = datetime.strptime(v["datetime"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
            result.append({
                "time": t,
                "open": float(v["open"]),
                "high": float(v["high"]),
                "low": float(v["low"]),
                "close": float(v["close"]),
            })
        return result
    except Exception as e:
        print(f"[data_fetcher] Twelve Data klines error: {e}")
        return None


def get_twelvedata_price(td_symbol: str, api_key: str):
    try:
        url = "https://api.twelvedata.com/price"
        resp = requests.get(url, params={"symbol": td_symbol, "apikey": api_key}, timeout=10)
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception as e:
        print(f"[data_fetcher] Twelve Data price error: {e}")
        return None


def fetch_candles(symbol_cfg: dict, interval: str, api_key: str, limit: int = 300):
    if symbol_cfg["type"] == "binance":
        result = get_binance_klines(symbol_cfg["binance_symbol"], interval, limit)
        if result is not None:
            return result
        fallback_symbol = symbol_cfg.get("td_fallback_symbol")
        if fallback_symbol:
            print("[data_fetcher] Binance ব্যর্থ, Twelve Data fallback ব্যবহার হচ্ছে...")
            return get_twelvedata_klines(fallback_symbol, interval, api_key, limit)
        return None
    elif symbol_cfg["type"] == "twelvedata":
        return get_twelvedata_klines(symbol_cfg["td_symbol"], interval, api_key, limit)
    return None


def fetch_price(symbol_cfg: dict, api_key: str):
    if symbol_cfg["type"] == "binance":
        result = get_binance_price(symbol_cfg["binance_symbol"])
        if result is not None:
            return result
        fallback_symbol = symbol_cfg.get("td_fallback_symbol")
        if fallback_symbol:
            return get_twelvedata_price(fallback_symbol, api_key)
        return None
    elif symbol_cfg["type"] == "twelvedata":
        return get_twelvedata_price(symbol_cfg["td_symbol"], api_key)
    return None
