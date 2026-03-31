"""
F&O signal generation helpers for IndiaFish scenario simulations.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple


_REPORT_CONTEXT: Dict[str, Any] = {"n_rounds": 0}

_BULLISH_KEYWORDS = [
    "buy",
    "call",
    "bullish",
    "long",
    "upside",
    "rally",
    "breakout",
    "support holds",
    "accumulate",
    "positive",
]
_BEARISH_KEYWORDS = [
    "sell",
    "put",
    "bearish",
    "short",
    "downside",
    "fall",
    "breakdown",
    "resistance",
    "exit",
    "negative",
    "crash",
]
_NEUTRAL_KEYWORDS = [
    "sideways",
    "range",
    "wait",
    "hold",
    "unclear",
    "uncertain",
    "neutral",
    "consolidat",
]
_VOL_EXPAND_KEYWORDS = [
    "volatile",
    "big move",
    "iv buy",
    "vix spike",
    "uncertainty",
    "event risk",
    "gap up",
    "gap down",
    "explosion",
]
_VOL_CRUSH_KEYWORDS = [
    "calm",
    "range bound",
    "theta",
    "sell premium",
    "iv crush",
    "time decay",
    "no movement",
    "pinned",
    "stable",
]
_PERSONA_WEIGHTS = {
    "fii_algo_desk": 3.0,
    "hni_options_seller": 2.5,
    "technical_trader": 2.0,
    "domestic_mf_manager": 1.5,
    "retail_fomo_trader": 0.5,
    "news_driven_punter": 0.5,
    "operator_manipulator": 0.0,
    "sebi_circuit_watcher": 0.0,
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "-"):
        return default
    if isinstance(value, str):
        cleaned = (
            value.replace(",", "")
            .replace("%", "")
            .replace("₹", "")
            .replace("Cr", "")
            .strip()
        )
        if not cleaned:
            return default
        value = cleaned
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(_safe_float(value, default)))
    except (TypeError, ValueError):
        return default


def _extract_numeric_fragment(text: str) -> float:
    if not text:
        return 0.0
    chars: List[str] = []
    started = False
    for char in str(text):
        if char.isdigit() or char in {".", "-"}:
            chars.append(char)
            started = True
        elif started:
            break
    return _safe_float("".join(chars), 0.0)


def _iter_agent_entries(payload: Any, inherited_persona: Optional[str] = None) -> Iterable[Tuple[str, Optional[str]]]:
    if isinstance(payload, dict):
        persona = (
            payload.get("type")
            or payload.get("persona_type")
            or payload.get("agent_type")
            or inherited_persona
        )

        candidate_texts = [
            payload.get("content"),
            payload.get("text"),
            payload.get("message"),
            payload.get("response"),
            payload.get("opinion"),
            payload.get("summary"),
            payload.get("stance"),
            payload.get("analysis"),
        ]
        for text in candidate_texts:
            if isinstance(text, str) and text.strip():
                yield text, persona

        for key in ("agent_opinions", "agent_states", "messages", "rounds", "final_state", "responses", "agents"):
            nested = payload.get(key)
            if nested is not None:
                yield from _iter_agent_entries(nested, persona)

        for value in payload.values():
            if isinstance(value, (dict, list)):
                yield from _iter_agent_entries(value, persona)

    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_agent_entries(item, inherited_persona)


def _score_text(text: str, keywords: List[str]) -> int:
    lowered = text.lower()
    score = 0
    for keyword in keywords:
        if keyword in lowered:
            score += 1
    return score


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.6:
        return "High"
    if confidence >= 0.3:
        return "Medium"
    return "Low"


def _get_weight(persona_type: Optional[str]) -> float:
    if not persona_type:
        return 1.0
    return _PERSONA_WEIGHTS.get(str(persona_type).strip(), 1.0)


def _default_bias() -> dict:
    bull_pct = 34.0
    bear_pct = 33.0
    neutral_pct = 33.0
    confidence = abs(bull_pct - bear_pct) / 100
    return {
        "bull_pct": bull_pct,
        "bear_pct": bear_pct,
        "neutral_pct": neutral_pct,
        "bias": "NEUTRAL",
        "confidence": round(confidence, 2),
        "confidence_label": _confidence_label(confidence),
        "agents_counted": 0,
        "data_quality": "low",
    }


def compute_nifty_bias(simulation_result: dict) -> dict:
    if not isinstance(simulation_result, dict) or not simulation_result:
        return _default_bias()

    bull_weighted = 0.0
    bear_weighted = 0.0
    neutral_weighted = 0.0
    agents_counted = 0

    for text, persona_type in _iter_agent_entries(simulation_result):
        weight = _get_weight(persona_type)
        if weight <= 0:
            continue

        bull_score = _score_text(text, _BULLISH_KEYWORDS)
        bear_score = _score_text(text, _BEARISH_KEYWORDS)
        neutral_score = _score_text(text, _NEUTRAL_KEYWORDS)

        if bull_score == 0 and bear_score == 0 and neutral_score == 0:
            continue

        agents_counted += 1
        if bull_score >= bear_score and bull_score >= neutral_score and bull_score > 0:
            bull_weighted += weight
        elif bear_score >= bull_score and bear_score >= neutral_score and bear_score > 0:
            bear_weighted += weight
        else:
            neutral_weighted += weight

    total_weighted = bull_weighted + bear_weighted + neutral_weighted
    if total_weighted <= 0:
        return _default_bias()

    bull_pct = round(bull_weighted / total_weighted * 100, 1)
    bear_pct = round(bear_weighted / total_weighted * 100, 1)
    neutral_pct = round(100 - bull_pct - bear_pct, 1)

    if bull_pct > 55:
        bias = "BULL"
    elif bear_pct > 55:
        bias = "BEAR"
    elif bull_pct > bear_pct and bull_pct > 45:
        bias = "BULL-LEANING"
    elif bear_pct > bull_pct and bear_pct > 45:
        bias = "BEAR-LEANING"
    else:
        bias = "NEUTRAL"

    confidence = abs(bull_pct - bear_pct) / 100
    if agents_counted >= 20:
        data_quality = "high"
    elif agents_counted >= 5:
        data_quality = "medium"
    else:
        data_quality = "low"

    return {
        "bull_pct": bull_pct,
        "bear_pct": bear_pct,
        "neutral_pct": neutral_pct,
        "bias": bias,
        "confidence": round(confidence, 2),
        "confidence_label": _confidence_label(confidence),
        "agents_counted": agents_counted,
        "data_quality": data_quality,
    }


def _compute_chain_max_pain(chain_data: dict) -> int:
    losses: Dict[int, float] = {}
    for candidate_strike in chain_data:
        total_loss = 0.0
        for strike, legs in chain_data.items():
            total_loss += max(0, strike - candidate_strike) * _safe_float(legs.get("CE", {}).get("oi"))
            total_loss += max(0, candidate_strike - strike) * _safe_float(legs.get("PE", {}).get("oi"))
        losses[candidate_strike] = total_loss
    return min(losses, key=losses.get) if losses else 0


def _compute_chain_spot(chain_data: dict) -> float:
    if not chain_data:
        return 0.0
    atm_strike = min(
        chain_data,
        key=lambda strike: abs(
            _safe_float(chain_data[strike].get("CE", {}).get("ltp"))
            - _safe_float(chain_data[strike].get("PE", {}).get("ltp"))
        ),
    )
    ce_ltp = _safe_float(chain_data[atm_strike].get("CE", {}).get("ltp"))
    pe_ltp = _safe_float(chain_data[atm_strike].get("PE", {}).get("ltp"))
    return round(max(0.0, atm_strike + ce_ltp - pe_ltp), 2)


def _top_oi_strike(chain_data: dict, leg: str) -> int:
    if not chain_data:
        return 0
    return max(
        chain_data.items(),
        key=lambda item: _safe_float(item[1].get(leg, {}).get("oi")),
    )[0]


def compute_max_pain_signal(chain_data: dict) -> dict:
    if not isinstance(chain_data, dict) or not chain_data:
        spot = 24187.0
        max_pain = 24000
        top_ce_strike = 24300
        top_pe_strike = 24000
    else:
        spot = _compute_chain_spot(chain_data)
        max_pain = _compute_chain_max_pain(chain_data)
        top_ce_strike = _top_oi_strike(chain_data, "CE")
        top_pe_strike = _top_oi_strike(chain_data, "PE")

    distance_points = round(abs(spot - max_pain), 2)
    distance_pct = round(distance_points / spot * 100, 2) if spot else 0.0

    if distance_pct < 0.5:
        pinning_probability = "Very High (>80%)"
    elif distance_pct < 1.0:
        pinning_probability = "High (60-80%)"
    elif distance_pct < 1.5:
        pinning_probability = "Medium (40-60%)"
    else:
        pinning_probability = "Low (<40%)"

    if spot > max_pain:
        direction_to_pain = "Bearish pull — price may drift down toward max pain"
    elif spot < max_pain:
        direction_to_pain = "Bullish pull — price may drift up toward max pain"
    else:
        direction_to_pain = "At max pain — pinning likely"

    return {
        "spot": round(spot, 2),
        "max_pain_strike": int(max_pain),
        "distance_points": distance_points,
        "distance_pct": distance_pct,
        "pinning_probability": pinning_probability,
        "direction_to_pain": direction_to_pain,
        "top_ce_resistance": int(top_ce_strike),
        "top_pe_support": int(top_pe_strike),
    }


def _atm_iv_from_chain(chain_data: dict) -> float:
    if not isinstance(chain_data, dict) or not chain_data:
        return 13.5

    atm_strike = min(
        chain_data,
        key=lambda strike: abs(
            _safe_float(chain_data[strike].get("CE", {}).get("ltp"))
            - _safe_float(chain_data[strike].get("PE", {}).get("ltp"))
        ),
    )
    ce_iv = _safe_float(chain_data[atm_strike].get("CE", {}).get("iv"))
    pe_iv = _safe_float(chain_data[atm_strike].get("PE", {}).get("iv"))
    if ce_iv and pe_iv:
        return round((ce_iv + pe_iv) / 2, 2)
    return round(ce_iv or pe_iv or 13.5, 2)


def compute_iv_signal(simulation_result: dict, chain_data: dict) -> dict:
    expand_votes = 0
    crush_votes = 0

    if isinstance(simulation_result, dict):
        for text, _persona_type in _iter_agent_entries(simulation_result):
            expand_votes += _score_text(text, _VOL_EXPAND_KEYWORDS)
            crush_votes += _score_text(text, _VOL_CRUSH_KEYWORDS)

    current_iv = _atm_iv_from_chain(chain_data)

    if expand_votes > crush_votes * 1.5:
        iv_direction = "EXPAND"
    elif crush_votes > expand_votes * 1.5:
        iv_direction = "CRUSH"
    else:
        iv_direction = "NEUTRAL"

    signal_strength = abs(expand_votes - crush_votes) / max(expand_votes + crush_votes, 1)

    if iv_direction == "EXPAND":
        trade_implication = "Consider long straddle / strangle or buy options outright"
    elif iv_direction == "CRUSH":
        trade_implication = "Consider short straddle / iron condor or sell premium"
    else:
        trade_implication = "No clear IV edge — avoid pure vol plays"

    return {
        "iv_direction": iv_direction,
        "current_iv": round(current_iv, 2),
        "signal_strength": round(signal_strength, 2),
        "expand_votes": int(expand_votes),
        "crush_votes": int(crush_votes),
        "trade_implication": trade_implication,
    }


def _one_line_summary(bias: dict, max_pain: dict, iv_signal: dict) -> str:
    bias_text = f"{bias.get('bias', 'NEUTRAL').title()} with {bias.get('bull_pct', 0)}% bullish vs {bias.get('bear_pct', 0)}% bearish sentiment"
    pain_text = (
        f"max pain at {max_pain.get('max_pain_strike', 0)} suggests {max_pain.get('pinning_probability', 'unknown').lower()} pinning"
    )
    iv_text = {
        "EXPAND": "IV expansion likely — option buying may work better than premium selling",
        "CRUSH": "IV crush likely — premium selling structures look more favorable",
        "NEUTRAL": "IV is balanced — avoid taking a pure volatility bet",
    }.get(iv_signal.get("iv_direction"), "IV edge is unclear")
    return f"{bias_text} — {pain_text}, and {iv_text}."


def generate_fo_report(
    scenario_id: str,
    scenario_name: str,
    injection_text: str,
    bias: dict,
    max_pain: dict,
    iv_signal: dict,
    seed_summary: str = "",
    timestamp: str = "",
    n_agents: int = 200,
    n_rounds: int = 20,
) -> str:
    report_timestamp = timestamp or ""
    one_line_summary = _one_line_summary(bias, max_pain, iv_signal)
    n_agents = _safe_int(n_agents, 200)
    n_rounds = _safe_int(n_rounds, 20)
    agents_counted = _safe_int(bias.get("agents_counted"), 0)

    return "\n".join(
        [
            "---",
            "# IndiaFish F&O Signal Report",
            f"**{scenario_name or scenario_id or 'Unknown Scenario'}** | {report_timestamp} | Underlying: NIFTY",
            "",
            "## Market Scenario",
            injection_text or "No scenario injection provided.",
            "",
            "## Nifty Directional Bias",
            "| Metric | Value |",
            "|---|---|",
            f"| Bias | {bias.get('bias', 'NEUTRAL')} |",
            f"| Bull % | {bias.get('bull_pct', 34.0)}% |",
            f"| Bear % | {bias.get('bear_pct', 33.0)}% |",
            f"| Neutral % | {bias.get('neutral_pct', 33.0)}% |",
            f"| Confidence | {bias.get('confidence_label', 'Low')} ({bias.get('confidence', 0):.0%}) |",
            f"| Agents simulated | {agents_counted} |",
            "",
            "## Max Pain Analysis",
            "| Metric | Value |",
            "|---|---|",
            f"| Spot (approx) | {max_pain.get('spot', 0):.2f} |",
            f"| Max Pain Strike | {max_pain.get('max_pain_strike', 0)} |",
            f"| Distance | {max_pain.get('distance_points', 0)} pts ({max_pain.get('distance_pct', 0)}%) |",
            f"| Pinning Probability | {max_pain.get('pinning_probability', 'Low (<40%)')} |",
            f"| Direction | {max_pain.get('direction_to_pain', 'At max pain — pinning likely')} |",
            f"| CE Resistance | {max_pain.get('top_ce_resistance', 0)} |",
            f"| PE Support | {max_pain.get('top_pe_support', 0)} |",
            "",
            "## IV / Volatility Signal",
            "| Metric | Value |",
            "|---|---|",
            f"| IV Direction | {iv_signal.get('iv_direction', 'NEUTRAL')} |",
            f"| Current IV | {iv_signal.get('current_iv', 13.5)}% |",
            f"| Signal Strength | {iv_signal.get('signal_strength', 0):.0%} |",
            f"| Implication | {iv_signal.get('trade_implication', 'No clear IV edge — avoid pure vol plays')} |",
            "",
            "## Simulation Consensus",
            f"> {one_line_summary}",
            "",
            "---",
            f"*IndiaFish swarm simulation — {n_agents} agents, {n_rounds} rounds.*",
            "*Not financial advice. For research purposes only.*",
            "---",
        ]
    )


def process_simulation_output(simulation_result_dict: dict) -> dict:
    simulation_result_dict = simulation_result_dict if isinstance(simulation_result_dict, dict) else {}

    scenario_id = simulation_result_dict.get("scenario_id", "")
    scenario_name = simulation_result_dict.get("scenario_name", "")
    injection_text = simulation_result_dict.get("injection_text", "")
    simulation_result = simulation_result_dict.get("simulation_result") or {}
    seed_summary = simulation_result_dict.get("seed_summary", "")
    timestamp = simulation_result_dict.get("timestamp", "")
    n_agents = _safe_int(simulation_result_dict.get("n_agents"), 200)
    n_rounds = _safe_int(simulation_result_dict.get("n_rounds"), 20)

    try:
        from app.services.dhan_ingest import get_option_chain

        chain_data = get_option_chain("NIFTY")
    except Exception:
        chain_data = {}

    bias = compute_nifty_bias(simulation_result)
    max_pain_data = compute_max_pain_signal(chain_data)
    iv_signal = compute_iv_signal(simulation_result, chain_data)

    report_md = generate_fo_report(
        scenario_id,
        scenario_name,
        injection_text,
        bias,
        max_pain_data,
        iv_signal,
        seed_summary,
        timestamp,
        n_agents=n_agents,
        n_rounds=n_rounds,
    )

    return {
        "report_markdown": report_md,
        "signals": {
            "bias": bias,
            "max_pain": max_pain_data,
            "iv": iv_signal,
        },
        "meta": {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "timestamp": timestamp,
            "n_agents": n_agents,
            "n_rounds": n_rounds,
        },
    }
