"""
Telegram bot helpers for IndiaFish.
"""

import logging
import threading
import time
from datetime import datetime

import schedule
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater

from app.config import Config
from app.services.fo_signal_generator import process_simulation_output
from app.services.scenario_library import list_scenarios
from app.services.scenario_runner import run_simulation


logger = logging.getLogger(__name__)

_COMMON_SCENARIOS = [
    "rbi_rate_cut_50bps",
    "rbi_rate_hold_hawkish",
    "union_budget_cgt_hike",
    "union_budget_cgt_removal",
    "weekly_expiry_thursday",
    "monthly_expiry_squeeze",
    "fii_massive_selloff",
    "geopolitical_escalation",
]


def _md_escape(text: str) -> str:
    escaped = str(text or "")
    for char in ("\\", "`", "*", "_", "["):
        escaped = escaped.replace(char, "\\" + char)
    return escaped


def _format_number_token(value: str) -> str:
    value = str(value or "").strip()
    return f"`{_md_escape(value)}`" if value else "`0`"


def _extract_between(report_markdown: str, start_marker: str, end_marker: str = "") -> list:
    lines = report_markdown.splitlines()
    collected = []
    inside = False
    for line in lines:
        if line.strip() == start_marker:
            inside = True
            continue
        if inside and end_marker and line.strip() == end_marker:
            break
        if inside:
            collected.append(line)
    return collected


def _parse_table_block(lines: list) -> dict:
    parsed = {}
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] != "Metric":
            parsed[parts[0]] = parts[1]
    return parsed


def _extract_title_parts(report_markdown: str) -> tuple:
    for line in report_markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("**") and "| Underlying:" in stripped:
            clean = stripped.replace("**", "")
            parts = [part.strip() for part in clean.split("|")]
            scenario_name = parts[0] if parts else "Unknown scenario"
            timestamp = parts[1] if len(parts) > 1 else ""
            return scenario_name, timestamp
    return "Unknown scenario", ""


def _extract_consensus(report_markdown: str) -> str:
    for line in report_markdown.splitlines():
        if line.strip().startswith("> "):
            return line.strip()[2:].strip()
    return "Consensus unavailable."


def _extract_footer_line(report_markdown: str) -> str:
    for line in report_markdown.splitlines():
        stripped = line.strip().strip("*")
        if stripped.startswith("IndiaFish swarm simulation"):
            return stripped
    return "IndiaFish swarm simulation."


def _split_message(text: str, max_len: int = 4000) -> list:
    if len(text) <= max_len:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > max_len:
        split_at = remaining.rfind("\n", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def format_report_for_telegram(report_markdown: str) -> str:
    if not report_markdown:
        return "IndiaFish Signal Report\n\nNo report content available."

    scenario_name, timestamp = _extract_title_parts(report_markdown)
    consensus = _extract_consensus(report_markdown)
    footer_line = _extract_footer_line(report_markdown)

    bias_table = _parse_table_block(
        _extract_between(report_markdown, "## Nifty Directional Bias", "## Max Pain Analysis")
    )
    max_pain_table = _parse_table_block(
        _extract_between(report_markdown, "## Max Pain Analysis", "## IV / Volatility Signal")
    )
    iv_table = _parse_table_block(
        _extract_between(report_markdown, "## IV / Volatility Signal", "## Simulation Consensus")
    )

    bias_indicator = bias_table.get("Bias", "NEUTRAL")
    lines = [
        "IndiaFish Signal Report",
        f"{_md_escape(scenario_name)} | {_md_escape(timestamp.split('T')[0] if 'T' in timestamp else timestamp)}",
        "",
        _md_escape(bias_indicator),
        "",
        f"Scenario: {_md_escape(_extract_between(report_markdown, '## Market Scenario', '## Nifty Directional Bias')[0] if _extract_between(report_markdown, '## Market Scenario', '## Nifty Directional Bias') else 'Unavailable')}",
        "",
        "*NIFTY BIAS*",
        f"Bear: {_format_number_token(bias_table.get('Bear %', '33%'))} | Bull: {_format_number_token(bias_table.get('Bull %', '34%'))} | Neutral: {_format_number_token(bias_table.get('Neutral %', '33%'))}",
        f"Confidence: {_md_escape(bias_table.get('Confidence', 'Low'))}",
        "",
        "*MAX PAIN*",
        f"Strike: {_format_number_token(max_pain_table.get('Max Pain Strike', '24000'))} | Distance: {_format_number_token(max_pain_table.get('Distance', '0 pts (0%)'))}",
        f"Pinning: {_md_escape(max_pain_table.get('Pinning Probability', 'Low (<40%)'))}",
        f"Pull: {_md_escape(max_pain_table.get('Direction', 'At max pain'))}",
        "",
        f"*IV SIGNAL: {_md_escape(iv_table.get('IV Direction', 'NEUTRAL'))}*",
        f"Current IV: {_format_number_token(iv_table.get('Current IV', '13.5%'))}",
        f"Implication: {_md_escape(iv_table.get('Implication', 'No clear IV edge'))}",
        "",
        f"Consensus: {_md_escape(consensus)}",
        "",
        _md_escape(footer_line),
        "Not financial advice.",
    ]

    formatted = "\n".join(lines)
    if len(formatted) > 4000:
        return formatted[:4000].rstrip() + "\n... (truncated)"
    return formatted


def _get_bot():
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set — bot will not start")
        return None
    try:
        return telegram.Bot(token=Config.TELEGRAM_BOT_TOKEN)
    except Exception as exc:
        logger.error("Failed to initialize Telegram bot: %s", exc)
        return None


def send_message(chat_id, text, parse_mode=None):
    bot = _get_bot()
    if not bot:
        return False
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return True
    except Exception as exc:
        logger.error("Failed to send Telegram message to %s: %s", chat_id, exc)
        return False


def send_report(chat_id: str, processed: dict):
    report_markdown = (processed or {}).get("report_markdown", "")
    signals = (processed or {}).get("signals", {})
    meta = (processed or {}).get("meta", {})
    formatted_report = format_report_for_telegram(report_markdown)
    consensus = _extract_consensus(report_markdown)
    bias_indicator = ((signals.get("bias") or {}).get("bias") or "NEUTRAL").strip()
    scenario_name = meta.get("scenario_name") or "IndiaFish scenario"
    timestamp = meta.get("timestamp") or datetime.now().isoformat()
    first_message = "\n".join(
        [
            _md_escape(bias_indicator),
            f"{_md_escape(scenario_name)} | {_md_escape(timestamp.split('T')[0] if 'T' in timestamp else timestamp)}",
            "",
            _md_escape(consensus),
        ]
    )

    success = send_message(chat_id, first_message, parse_mode=ParseMode.MARKDOWN)
    for chunk in _split_message(formatted_report):
        chunk_success = send_message(chat_id, chunk, parse_mode=ParseMode.MARKDOWN)
        success = success and chunk_success
        time.sleep(0.2)
    return success


def _is_allowed(update):
    if not Config.TELEGRAM_ALLOWED_USERS:
        return True
    chat_id = str(update.effective_chat.id)
    if chat_id in Config.TELEGRAM_ALLOWED_USERS:
        return True
    if update.effective_message:
        update.effective_message.reply_text("Access restricted. Contact admin.")
    return False


def start_handler(update, context):
    if not _is_allowed(update):
        return
    message = (
        "Welcome to IndiaFish — Indian F&O Swarm Simulator.\n\n"
        "I simulate how 300-500 market participants react to events\n"
        "before they happen.\n\n"
        "Commands:\n"
        "/sim — Run a simulation (choose scenario)\n"
        "/morning — Today's morning market brief\n"
        "/scenarios — List all available scenarios\n"
        "/status — Check system status\n"
        "/help — Show this message"
    )
    update.effective_message.reply_text(message)


def scenarios_handler(update, context):
    if not _is_allowed(update):
        return
    scenarios = list_scenarios()
    lines = []
    for idx, scenario in enumerate(scenarios, start=1):
        lines.append(f"{idx}. {scenario['name']} ({scenario['urgency']})")
    lines.append("")
    lines.append("Use /sim to run any scenario.")
    update.effective_message.reply_text("\n".join(lines))


def sim_handler(update, context):
    if not _is_allowed(update):
        return
    scenario_lookup = {item["id"]: item["name"] for item in list_scenarios()}
    buttons = []
    for scenario_id in _COMMON_SCENARIOS:
        buttons.append(
            [
                InlineKeyboardButton(
                    scenario_lookup.get(scenario_id, scenario_id),
                    callback_data=scenario_id,
                )
            ]
        )
    update.effective_message.reply_text(
        "Choose a simulation scenario:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


def sim_callback_handler(update, context):
    if not _is_allowed(update):
        return

    query = update.callback_query
    query.answer()
    scenario_id = query.data
    scenario_lookup = {item["id"]: item["name"] for item in list_scenarios()}
    scenario_name = scenario_lookup.get(scenario_id, scenario_id)
    query.message.reply_text(
        f"Running simulation for: {scenario_name}... this takes 30-60 seconds"
    )

    result = run_simulation(
        scenario_id,
        n_agents=200,
        n_rounds=20,
        use_mock_seed=True,
    )
    processed = process_simulation_output(result)
    send_report(str(update.effective_chat.id), processed)


def _pick_morning_scenario():
    now = datetime.now()
    if now.weekday() == 3:
        return "weekly_expiry_thursday", None
    if now.weekday() == 1 and now.day <= 7:
        return "rbi_rate_hold_hawkish", None

    try:
        from app.services.dhan_ingest import get_fii_dii_flows

        fii_data = get_fii_dii_flows()
        if fii_data.get("fii_net_cr", 0) < -3000:
            return "fii_massive_selloff", None
    except Exception:
        pass

    return "custom", "Summarise today's market conditions and likely Nifty direction"


def morning_handler(update, context):
    if not _is_allowed(update):
        return
    scenario_id, custom_variable = _pick_morning_scenario()
    update.effective_message.reply_text("Running morning brief... this takes 30-60 seconds")
    result = run_simulation(
        scenario_id,
        n_agents=200,
        n_rounds=20,
        custom_variable=custom_variable,
        use_mock_seed=(Config.SEED_MODE == "mock"),
    )
    processed = process_simulation_output(result)
    send_report(str(update.effective_chat.id), processed)


def status_handler(update, context):
    if not _is_allowed(update):
        return

    dhan_status = "Mock"
    try:
        from app.services.dhan_ingest import get_option_chain

        dhan_status = "Connected" if get_option_chain("NIFTY") else "Mock"
    except Exception:
        dhan_status = "Mock"

    now_ist = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    message = "\n".join(
        [
            "System: Online",
            f"Seed mode: {Config.SEED_MODE}",
            f"Dhan API: {dhan_status}",
            f"LLM: {Config.LLM_MODEL_NAME}",
            "Bot: Running",
            f"Time: {now_ist}",
        ]
    )
    update.effective_message.reply_text(message)


def _fallback_message_handler(update, context):
    if not _is_allowed(update):
        return
    update.effective_message.reply_text("Use /help to see available commands.")


def start_bot() -> None:
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set — bot will not start")
        return

    updater = Updater(token=Config.TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_handler))
    dp.add_handler(CommandHandler("help", start_handler))
    dp.add_handler(CommandHandler("scenarios", scenarios_handler))
    dp.add_handler(CommandHandler("sim", sim_handler))
    dp.add_handler(CommandHandler("morning", morning_handler))
    dp.add_handler(CommandHandler("status", status_handler))
    dp.add_handler(CallbackQueryHandler(sim_callback_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, _fallback_message_handler))
    updater.start_polling()
    updater.idle()


def start_bot_thread() -> threading.Thread:
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    return thread
