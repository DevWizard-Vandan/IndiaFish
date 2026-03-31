"""
Dhan market data ingestion helpers for IndiaFish seed generation.
"""

import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger("mirofish.dhan_ingest")

try:
    import dhanhq  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - optional runtime dependency check
    dhanhq = None


OPTION_CHAIN_URL = "https://api.dhan.co/v2/optionchain"
INTRADAY_URL = "https://api.dhan.co/v2/charts/intraday"
NSE_HOME_URL = "https://www.nseindia.com"
NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
EMPTY_OHLCV = ["datetime", "open", "high", "low", "close", "volume"]
_LAST_OPTION_CHAIN_META: Dict[str, Any] = {}


def _empty_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_OHLCV)


def _to_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "-"):
        return default
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("%", "").strip()
        if not cleaned:
            return default
        value = cleaned
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    return int(round(_to_float(value, default)))


def _extract_leg(raw_leg: Dict[str, Any]) -> Dict[str, float]:
    oi = _to_float(
        raw_leg.get("oi", raw_leg.get("openInterest", raw_leg.get("open_interest", 0)))
    )
    prev_oi = _to_float(
        raw_leg.get("prev_oi", raw_leg.get("previousOi", raw_leg.get("previous_oi", 0)))
    )
    oi_change_pct = raw_leg.get("oi_change_pct")
    if oi_change_pct in (None, "", "-") and prev_oi > 0:
        oi_change_pct = ((oi - prev_oi) / prev_oi) * 100

    return {
        "ltp": _to_float(raw_leg.get("ltp", raw_leg.get("last_price", raw_leg.get("lastPrice", 0)))),
        "oi": oi,
        "prev_oi": prev_oi,
        "oi_change_pct": _to_float(oi_change_pct),
        "iv": _to_float(raw_leg.get("iv", raw_leg.get("impliedVolatility", raw_leg.get("implied_volatility", 0)))),
        "delta": _to_float(raw_leg.get("delta")),
        "theta": _to_float(raw_leg.get("theta")),
        "gamma": _to_float(raw_leg.get("gamma")),
        "vega": _to_float(raw_leg.get("vega")),
        "volume": _to_float(raw_leg.get("volume", raw_leg.get("tradedVolume", 0))),
        "bid": _to_float(raw_leg.get("bid", raw_leg.get("bestBidPrice", raw_leg.get("bid_price", 0)))),
        "ask": _to_float(raw_leg.get("ask", raw_leg.get("bestAskPrice", raw_leg.get("ask_price", 0)))),
    }


def _iter_option_rows(payload: Any) -> Iterable[Tuple[Any, Dict[str, Any]]]:
    if isinstance(payload, dict):
        for key in ("oc", "optionChain", "data", "records"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                yield from _iter_option_rows(nested)
            elif isinstance(nested, list):
                yield from _iter_option_rows(nested)

        for strike, leg_payload in payload.items():
            if strike in {"oc", "optionChain", "data", "records"}:
                continue
            if isinstance(leg_payload, dict) and any(
                leg_key in leg_payload for leg_key in ("CE", "PE", "ce", "pe", "callOptions", "putOptions")
            ):
                yield strike, leg_payload

    elif isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            strike = item.get("strikePrice", item.get("strike", item.get("StrikePrice")))
            if strike is None:
                continue
            yield strike, item


def _extract_option_meta(response_json: Dict[str, Any]) -> None:
    global _LAST_OPTION_CHAIN_META

    candidate_sources: List[Dict[str, Any]] = [response_json]
    for key in ("data", "records"):
        nested = response_json.get(key)
        if isinstance(nested, dict):
            candidate_sources.append(nested)

    meta: Dict[str, Any] = {}
    for source in candidate_sources:
        for key, value in source.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("expiry", "date", "spot", "underlying", "ltp")):
                meta[key] = value

    _LAST_OPTION_CHAIN_META = meta


def _find_expiry_date(meta: Dict[str, Any]) -> Optional[datetime]:
    for key, value in meta.items():
        if "expiry" not in str(key).lower():
            continue
        for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y", "%Y/%m/%d", "%d %b %Y"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
    return None


def get_option_chain(underlying: str = "NIFTY", expiry_offset: int = 0) -> dict:
    try:
        headers = {
            "access-token": Config.DHAN_ACCESS_TOKEN or "",
            "client-id": Config.DHAN_CLIENT_ID or "",
            "Content-Type": "application/json",
        }
        body = {"UnderlyingScip": underlying, "ExpiryCode": expiry_offset}

        response = requests.post(OPTION_CHAIN_URL, json=body, headers=headers, timeout=15)
        time.sleep(3)
        if response.status_code in (401, 403):
            logger.warning(
                "Dhan option chain auth failed with %s. DHAN_ACCESS_TOKEN may be expired or invalid.",
                response.status_code,
            )
        response.raise_for_status()

        response_json = response.json()
        _extract_option_meta(response_json)

        chain: Dict[int, Dict[str, Dict[str, float]]] = {}
        for strike_value, row in _iter_option_rows(response_json):
            strike = _to_int(strike_value, default=-1)
            if strike < 0:
                continue

            ce_raw = row.get("CE", row.get("ce", row.get("callOptions", {}))) or {}
            pe_raw = row.get("PE", row.get("pe", row.get("putOptions", {}))) or {}
            chain[strike] = {"CE": _extract_leg(ce_raw), "PE": _extract_leg(pe_raw)}

        return dict(sorted(chain.items()))
    except Exception as exc:
        logger.warning(f"Failed to fetch option chain for {underlying}: {exc}")
        return {}


def get_pcr_and_max_pain(chain: dict) -> dict:
    if not chain:
        return {"pcr": 0.0, "max_pain_strike": 0, "spot": 0.0}

    total_ce_oi = sum(_to_float(legs.get("CE", {}).get("oi")) for legs in chain.values())
    total_pe_oi = sum(_to_float(legs.get("PE", {}).get("oi")) for legs in chain.values())
    pcr = total_pe_oi / total_ce_oi if total_ce_oi else 0.0

    candidate_losses: Dict[int, float] = {}
    for candidate_strike in chain:
        total_loss = 0.0
        for strike, legs in chain.items():
            total_loss += max(0, strike - candidate_strike) * _to_float(legs.get("CE", {}).get("oi"))
            total_loss += max(0, candidate_strike - strike) * _to_float(legs.get("PE", {}).get("oi"))
        candidate_losses[candidate_strike] = total_loss

    max_pain_strike = min(candidate_losses, key=candidate_losses.get) if candidate_losses else 0

    spot = 0.0
    for key, value in _LAST_OPTION_CHAIN_META.items():
        lowered = str(key).lower()
        if "spot" in lowered or ("underlying" in lowered and "value" in lowered):
            spot = _to_float(value)
            if spot:
                break

    if not spot:
        atm_strike = min(
            chain,
            key=lambda strike: abs(
                _to_float(chain[strike].get("CE", {}).get("ltp"))
                - _to_float(chain[strike].get("PE", {}).get("ltp"))
            ),
        )
        ce_ltp = _to_float(chain[atm_strike].get("CE", {}).get("ltp"))
        pe_ltp = _to_float(chain[atm_strike].get("PE", {}).get("ltp"))
        spot = max(0.0, atm_strike + ce_ltp - pe_ltp)

    return {"pcr": round(pcr, 4), "max_pain_strike": int(max_pain_strike), "spot": round(spot, 2)}


def _find_today_bucket(payload: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, list):
        return None

    today_strings = {
        datetime.now().strftime("%d-%b-%Y"),
        datetime.now().strftime("%d %b %Y"),
        datetime.now().strftime("%Y-%m-%d"),
        datetime.now().strftime("%d-%m-%Y"),
    }

    fallback = None
    for item in payload:
        if not isinstance(item, dict):
            continue

        date_value = str(
            item.get("date")
            or item.get("tradeDate")
            or item.get("tradedDate")
            or item.get("businessDate")
            or ""
        )
        if date_value:
            normalized = date_value.strip()
            if normalized in today_strings:
                return item
            fallback = item
        elif fallback is None:
            fallback = item

    return fallback


def _extract_party_values(row: Dict[str, Any], party: str) -> Tuple[float, float, float]:
    lower_party = party.lower()
    buy = sell = net = 0.0

    for key, value in row.items():
        lowered = str(key).lower()
        if lower_party not in lowered:
            continue
        if "buy" in lowered:
            buy = _to_float(value)
        elif "sell" in lowered:
            sell = _to_float(value)
        elif "net" in lowered:
            net = _to_float(value)

    if not any((buy, sell, net)):
        category = str(row.get("category", row.get("clientType", ""))).lower()
        if lower_party in category:
            buy = _to_float(row.get("buyValue", row.get("buy", 0)))
            sell = _to_float(row.get("sellValue", row.get("sell", 0)))
            net = _to_float(row.get("netValue", row.get("net", buy - sell)))
        elif party.upper() in {"FII", "DII"} and category == "":
            buy = _to_float(row.get(f"{lower_party}Buy", 0))
            sell = _to_float(row.get(f"{lower_party}Sell", 0))
            net = _to_float(row.get(f"{lower_party}Net", buy - sell))

    if not net and (buy or sell):
        net = buy - sell

    return buy, sell, net


def get_fii_dii_flows() -> dict:
    try:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.nseindia.com/",
            }
        )
        session.get(NSE_HOME_URL, timeout=15)
        response = session.get(NSE_FII_DII_URL, timeout=15)
        response.raise_for_status()

        payload = response.json()
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("rows", payload))

        today_row = _find_today_bucket(payload)
        if not today_row:
            raise ValueError("Unable to find FII/DII row")

        fii_buy, fii_sell, fii_net = _extract_party_values(today_row, "FII")
        dii_buy, dii_sell, dii_net = _extract_party_values(today_row, "DII")

        if not any((fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net)) and isinstance(payload, list):
            for row in payload:
                category = str(row.get("category", row.get("clientType", ""))).upper()
                if "FII" in category:
                    fii_buy, fii_sell, fii_net = _extract_party_values(row, "FII")
                elif "DII" in category:
                    dii_buy, dii_sell, dii_net = _extract_party_values(row, "DII")

        return {
            "fii_net_cr": round(fii_net, 2),
            "dii_net_cr": round(dii_net, 2),
            "fii_buy": round(fii_buy, 2),
            "fii_sell": round(fii_sell, 2),
            "dii_buy": round(dii_buy, 2),
            "dii_sell": round(dii_sell, 2),
        }
    except Exception as exc:
        logger.warning(f"Failed to fetch NSE FII/DII data: {exc}")
        return {"fii_net_cr": 0, "dii_net_cr": 0, "error": "unavailable"}


def _normalize_intraday_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    data = payload.get("data", payload)
    timestamps = data.get("start_Time", data.get("start_time", data.get("datetime", [])))
    frame = pd.DataFrame(
        {
            "datetime": pd.to_datetime(timestamps, errors="coerce"),
            "open": pd.to_numeric(data.get("open", []), errors="coerce"),
            "high": pd.to_numeric(data.get("high", []), errors="coerce"),
            "low": pd.to_numeric(data.get("low", []), errors="coerce"),
            "close": pd.to_numeric(data.get("close", []), errors="coerce"),
            "volume": pd.to_numeric(data.get("volume", []), errors="coerce"),
        }
    )
    return frame.dropna(subset=["datetime"]).reset_index(drop=True)


def get_historical_ohlcv(symbol: str, from_date: str, to_date: str, interval: int = 5) -> pd.DataFrame:
    headers = {
        "access-token": Config.DHAN_ACCESS_TOKEN or "",
        "client-id": Config.DHAN_CLIENT_ID or "",
        "Content-Type": "application/json",
    }
    body = {
        "securityId": symbol,
        "exchangeSegment": "NSE_EQ",
        "instrument": "INDEX",
        "interval": str(interval),
        "fromDate": from_date,
        "toDate": to_date,
    }

    try:
        response = requests.post(INTRADAY_URL, json=body, headers=headers, timeout=20)
        response.raise_for_status()
        frame = _normalize_intraday_payload(response.json())
        if not frame.empty:
            return frame[EMPTY_OHLCV]
    except Exception as exc:
        logger.warning(f"Dhan intraday fetch failed for {symbol}: {exc}")

    try:
        yf_frame = yf.download(
            f"{symbol}.NS",
            start=from_date,
            end=to_date,
            interval=f"{interval}m",
            progress=False,
            auto_adjust=False,
        )
        if yf_frame.empty:
            return _empty_ohlcv_frame()

        yf_frame = yf_frame.reset_index()
        datetime_col = "Datetime" if "Datetime" in yf_frame.columns else "Date"
        yf_frame = yf_frame.rename(
            columns={
                datetime_col: "datetime",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        return yf_frame[EMPTY_OHLCV]
    except Exception as exc:
        logger.warning(f"yfinance fallback failed for {symbol}: {exc}")
        return _empty_ohlcv_frame()


def _top_oi_rows(chain: dict, leg: str) -> List[Tuple[int, Dict[str, float]]]:
    return sorted(
        ((strike, legs.get(leg, {})) for strike, legs in chain.items()),
        key=lambda item: _to_float(item[1].get("oi")),
        reverse=True,
    )[:5]


def _fresh_buildup_lines(chain: dict) -> List[str]:
    lines = []
    for strike, legs in sorted(chain.items()):
        for leg_name in ("CE", "PE"):
            leg = legs.get(leg_name, {})
            if abs(_to_float(leg.get("oi_change_pct"))) > 20:
                lines.append(
                    f"- {strike} {leg_name}: OI {int(_to_float(leg.get('oi'))):,}, "
                    f"change {leg.get('oi_change_pct', 0):.2f}%, IV {leg.get('iv', 0):.2f}, LTP {leg.get('ltp', 0):.2f}"
                )
    return lines


def _format_oi_table(rows: List[Tuple[int, Dict[str, float]]]) -> str:
    lines = ["| Strike | OI | OI Change % | IV | LTP |", "|---|---|---|---|---|"]
    for strike, leg in rows:
        lines.append(
            f"| {strike} | {int(_to_float(leg.get('oi'))):,} | {leg.get('oi_change_pct', 0):.2f}% | "
            f"{leg.get('iv', 0):.2f} | {leg.get('ltp', 0):.2f} |"
        )
    if len(lines) == 2:
        lines.append("| N/A | 0 | 0.00% | 0.00 | 0.00 |")
    return "\n".join(lines)


def _expiry_context() -> Tuple[str, str]:
    expiry_dt = _find_expiry_date(_LAST_OPTION_CHAIN_META)
    if not expiry_dt:
        return "Unknown", "Unknown"

    days = max((expiry_dt.date() - datetime.now().date()).days, 0)
    expiry_type = "Monthly" if expiry_dt.day >= 24 else "Weekly"
    return str(days), expiry_type


def build_market_seed(underlying: str = "NIFTY") -> str:
    if getattr(Config, "SEED_MODE", "document") == "mock":
        from .mock_seed import get_mock_seed

        return get_mock_seed(underlying)

    chain = get_option_chain(underlying)
    pcr_data = get_pcr_and_max_pain(chain)
    fii_data = get_fii_dii_flows()
    today = datetime.now().strftime("%Y-%m-%d")

    top_ce_rows = _top_oi_rows(chain, "CE")
    top_pe_rows = _top_oi_rows(chain, "PE")
    fresh_buildup = _fresh_buildup_lines(chain)

    strongest_ce = top_ce_rows[0][0] if top_ce_rows else "N/A"
    strongest_pe = top_pe_rows[0][0] if top_pe_rows else "N/A"

    pcr = pcr_data.get("pcr", 0.0)
    if pcr > 1.3:
        sentiment = "Bullish"
    elif pcr < 0.8:
        sentiment = "Bearish"
    else:
        sentiment = "Neutral"

    days_to_expiry, expiry_type = _expiry_context()

    seed_lines = [
        "---",
        "## Market Snapshot",
        f"- Underlying: {underlying}",
        f"- Spot (approx): {pcr_data.get('spot', 0.0):.2f}",
        f"- Date: {today}",
        "- Market Hours: 09:15–15:30 IST",
        "",
        "## Option Chain Summary",
        "### Top 5 CE Strikes by OI",
        _format_oi_table(top_ce_rows),
        "",
        "### Top 5 PE Strikes by OI",
        _format_oi_table(top_pe_rows),
        "",
        "### Fresh OI Build-up (>20% change)",
        "\n".join(fresh_buildup) if fresh_buildup else "- None above threshold",
        "",
        "## Key Levels",
        f"- Max Pain Strike: {pcr_data.get('max_pain_strike', 0)}",
        f"- Strong CE Resistance (highest OI): {strongest_ce}",
        f"- Strong PE Support (highest OI): {strongest_pe}",
        "",
        "## Sentiment Indicators",
        f"- PCR: {pcr:.2f} — {sentiment}",
        f"- FII Net Flow Today: ₹{fii_data.get('fii_net_cr', 0):,.0f} Cr",
        f"- DII Net Flow Today: ₹{fii_data.get('dii_net_cr', 0):,.0f} Cr",
        "",
        "## Expiry Context",
        f"- Days to nearest expiry: {days_to_expiry}",
        f"- Expiry type: {expiry_type}",
        "---",
    ]
    return "\n".join(seed_lines)
