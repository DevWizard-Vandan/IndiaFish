"""
Hardcoded development seed for IndiaFish market testing.
"""

from datetime import datetime


def get_mock_seed(underlying: str = "NIFTY") -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    seed_lines = [
        "---",
        "## Market Snapshot",
        f"- Underlying: {underlying} (MOCK DATA)",
        "- Spot (approx): 24187.00",
        f"- Date: {today}",
        "- Market Hours: 09:15-15:30 IST (MOCK DATA)",
        "",
        "## Option Chain Summary",
        "### Top 5 CE Strikes by OI",
        "| Strike | OI | OI Change % | IV | LTP |",
        "|---|---|---|---|---|",
        "| 24200 | 184,500 | 11.80% | 12.90 | 116.40 |",
        "| 24300 | 173,200 | 9.60% | 13.20 | 78.55 |",
        "| 24500 | 161,900 | 14.10% | 14.40 | 29.85 |",
        "| 24400 | 149,700 | 8.30% | 13.80 | 49.20 |",
        "| 24600 | 137,400 | 6.70% | 15.10 | 18.40 |",
        "",
        "### Top 5 PE Strikes by OI",
        "| Strike | OI | OI Change % | IV | LTP |",
        "|---|---|---|---|---|",
        "| 24000 | 196,800 | 13.40% | 13.10 | 62.75 |",
        "| 23900 | 181,300 | 10.90% | 13.60 | 47.90 |",
        "| 23800 | 169,100 | 7.50% | 14.20 | 35.65 |",
        "| 24100 | 154,600 | 12.20% | 12.80 | 84.35 |",
        "| 23700 | 141,900 | 5.80% | 14.90 | 26.40 |",
        "",
        "### Fresh OI Build-up (>20% change)",
        "- 24100 PE: OI 154,600, change 22.40%, IV 12.80, LTP 84.35 (MOCK DATA)",
        "- 24500 CE: OI 161,900, change 21.10%, IV 14.40, LTP 29.85 (MOCK DATA)",
        "",
        "## Key Levels",
        "- Max Pain Strike: 24000",
        "- Strong CE Resistance (highest OI): 24200",
        "- Strong PE Support (highest OI): 24000",
        "",
        "## Sentiment Indicators",
        "- PCR: 0.94 — Neutral (MOCK DATA)",
        "- FII Net Flow Today: ₹-2,340 Cr",
        "- DII Net Flow Today: ₹1,890 Cr",
        "",
        "## Expiry Context",
        "- Days to nearest expiry: 3",
        "- Expiry type: Weekly",
        "---",
    ]
    return "\n".join(seed_lines)
