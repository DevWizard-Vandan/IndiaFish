"""
Scenario definitions for IndiaFish simulations.
"""

from copy import deepcopy


SCENARIO_LIBRARY = {
    "rbi_rate_cut_50bps": {
        "id": "rbi_rate_cut_50bps",
        "name": "RBI surprise rate cut",
        "description": "A surprise RBI easing decision shocks traders during market hours.",
        "variable_injection": "RBI Governor announces surprise 50bps repo rate cut effective immediately, citing slowing growth and benign inflation. Markets were expecting a hold.",
        "affected_segments": ["banks", "real_estate", "rate_sensitives", "bond_yields", "INR"],
        "historical_reference": "RBI emergency cut March 2020",
        "urgency": "live_event",
        "default_agents": 500,
    },
    "rbi_rate_hold_hawkish": {
        "id": "rbi_rate_hold_hawkish",
        "name": "RBI hold with hawkish tone",
        "description": "The RBI stays on hold but warns inflation will keep policy tight for longer.",
        "variable_injection": "RBI holds repo rate but signals no cuts for rest of year, warning that inflation remains sticky and policy must stay restrictive.",
        "affected_segments": ["banks", "bond_yields", "rate_sensitives"],
        "historical_reference": "RBI hold Oct 2023",
        "urgency": "live_event",
        "default_agents": 300,
    },
    "union_budget_cgt_hike": {
        "id": "union_budget_cgt_hike",
        "name": "Budget capital gains tax hike",
        "description": "A surprise Union Budget tax change hits equity sentiment instantly.",
        "variable_injection": "Finance Minister raises STCG to 20% and LTCG to 15%, effective immediately, catching both traders and long-term investors off guard.",
        "affected_segments": ["equity_flows", "FII", "retail_sentiment", "all_sectors"],
        "historical_reference": "Budget July 2024 CGT changes",
        "urgency": "live_event",
        "default_agents": 500,
    },
    "union_budget_cgt_removal": {
        "id": "union_budget_cgt_removal",
        "name": "Budget removes capital gains tax",
        "description": "A pro-market Budget rumor triggers aggressive bullish positioning ahead of confirmation.",
        "variable_injection": "Finance Minister announces complete removal of LTCG tax on equities to boost investment, triggering a sharp pre-event surge in risk appetite.",
        "affected_segments": ["equity_flows", "FII", "retail_sentiment", "small_midcap"],
        "historical_reference": "Pre-budget speculation 2024",
        "urgency": "pre_event",
        "default_agents": 500,
    },
    "weekly_expiry_thursday": {
        "id": "weekly_expiry_thursday",
        "name": "Weekly Nifty expiry day",
        "description": "Weekly expiry mechanics dominate intraday behavior in index options.",
        "variable_injection": "Today is weekly Nifty expiry Thursday. Max pain at {max_pain}. PCR at {pcr}.",
        "affected_segments": ["nifty_options", "banknifty_options", "OTM_strikes", "theta_decay"],
        "historical_reference": "Every Thursday NSE expiry",
        "urgency": "live_event",
        "default_agents": 300,
    },
    "monthly_expiry_squeeze": {
        "id": "monthly_expiry_squeeze",
        "name": "Monthly expiry last Thursday",
        "description": "Monthly expiry positioning creates rollovers, squeezes, and sharp intraday traps.",
        "variable_injection": "Monthly series expiry today. Large OI buildup at key strikes. Rollover in progress.",
        "affected_segments": ["all_fo_segments", "index_futures", "stock_futures"],
        "historical_reference": "Monthly expiry dynamics NSE",
        "urgency": "live_event",
        "default_agents": 500,
    },
    "large_corp_results_miss": {
        "id": "large_corp_results_miss",
        "name": "Large cap misses estimates",
        "description": "A heavyweight company disappoints on earnings and drags the broader tape with it.",
        "variable_injection": "{company} {quarter} results: PAT down {pct}% vs estimates, revenue miss, management cautious on outlook.",
        "affected_segments": ["stock_specific", "sector_peers", "index_weight"],
        "historical_reference": "TCS Q2 FY24 miss",
        "urgency": "live_event",
        "default_agents": 200,
    },
    "large_corp_results_beat": {
        "id": "large_corp_results_beat",
        "name": "Large cap beats estimates",
        "description": "A heavyweight earnings beat sparks optimism across the stock and its peers.",
        "variable_injection": "{company} {quarter} results: PAT up {pct}% above estimates, strong guidance, buyback announced.",
        "affected_segments": ["stock_specific", "sector_peers", "index_weight"],
        "historical_reference": "Reliance Q2 FY24 beat",
        "urgency": "live_event",
        "default_agents": 200,
    },
    "fii_massive_selloff": {
        "id": "fii_massive_selloff",
        "name": "FII single-day massive selloff",
        "description": "A brutal foreign outflow day shakes index sentiment and currency confidence.",
        "variable_injection": "FII net sold Rs. 8,500 Cr in cash market today, the largest single-day outflow in 6 months. DII is absorbing part of the damage but sentiment is cracking.",
        "affected_segments": ["large_cap", "index_futures", "INR", "sentiment"],
        "historical_reference": "FII selloff Oct 2023",
        "urgency": "live_event",
        "default_agents": 500,
    },
    "geopolitical_escalation": {
        "id": "geopolitical_escalation",
        "name": "India-Pakistan border escalation",
        "description": "A sudden security escalation triggers defense bids and broad risk-off fear.",
        "variable_injection": "Ceasefire violations reported at LoC, Indian Army on high alert. Government convenes emergency security meeting as traders brace for geopolitical risk.",
        "affected_segments": ["defense_stocks", "INR", "gold", "PSU_banks", "sentiment"],
        "historical_reference": "Pulwama Feb 2019",
        "urgency": "live_event",
        "default_agents": 500,
    },
    "rupee_sharp_fall": {
        "id": "rupee_sharp_fall",
        "name": "Rupee sharp depreciation",
        "description": "A sudden INR slide changes sector leadership and raises macro alarms intraday.",
        "variable_injection": "USDINR crosses 88, RBI intervenes but INR is still down 1.2% intraday. Import-heavy sectors are immediately under pressure.",
        "affected_segments": ["IT_exporters", "pharma", "importers", "oil_companies", "FII_flows"],
        "historical_reference": "INR 83+ Sept 2023",
        "urgency": "live_event",
        "default_agents": 300,
    },
    "us_fed_rate_hike": {
        "id": "us_fed_rate_hike",
        "name": "US Fed surprise rate hike",
        "description": "A global rates shock spills into Indian risk assets and the rupee.",
        "variable_injection": "US Federal Reserve raises rates by 25bps and signals more hikes ahead. Global risk-off is triggered and US 10Y yield spikes sharply.",
        "affected_segments": ["FII_flows", "IT_sector", "INR", "global_risk_sentiment"],
        "historical_reference": "Fed hike cycle 2022-23",
        "urgency": "live_event",
        "default_agents": 500,
    },
    "crude_oil_spike": {
        "id": "crude_oil_spike",
        "name": "Crude oil spike above $100",
        "description": "A crude spike revives inflation and current account fears for India.",
        "variable_injection": "Brent crude crosses $100 per barrel on OPEC+ supply cut. India macro risk rises immediately as CAD widening fears return.",
        "affected_segments": ["oil_marketing_cos", "aviation", "paint_sector", "INR", "inflation"],
        "historical_reference": "Crude spike Russia-Ukraine 2022",
        "urgency": "live_event",
        "default_agents": 300,
    },
    "custom": {
        "id": "custom",
        "name": "Custom scenario",
        "description": "A user-defined market shock can be injected into the simulation.",
        "variable_injection": "{user_defined_variable}",
        "affected_segments": [],
        "historical_reference": "User defined",
        "urgency": "live_event",
        "default_agents": 300,
    },
}


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def get_scenario(scenario_id: str) -> dict:
    if scenario_id not in SCENARIO_LIBRARY:
        raise ValueError(f"Unknown scenario_id: {scenario_id}")
    return deepcopy(SCENARIO_LIBRARY[scenario_id])


def list_scenarios() -> list:
    return [
        {
            "id": scenario["id"],
            "name": scenario["name"],
            "description": scenario["description"],
            "urgency": scenario["urgency"],
        }
        for scenario in SCENARIO_LIBRARY.values()
    ]


def fill_scenario_variable(scenario: dict, **kwargs) -> str:
    template = scenario.get("variable_injection", "")
    return template.format_map(_SafeFormatDict(kwargs))
