"""
Scenario orchestration helpers for seed-driven simulations.
"""

import json
import logging
import os
from datetime import datetime

from app.config import Config
from app.services.dhan_ingest import build_market_seed
from app.services.mock_seed import get_mock_seed
from app.services.scenario_library import fill_scenario_variable, get_scenario
from app.services.simulation_manager import SimulationManager


logger = logging.getLogger(__name__)


def _extract_seed_value(seed_text: str, label: str) -> str:
    for line in seed_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"- {label}:"):
            return stripped.split(":", 1)[1].strip()
    return ""


def _extract_numeric_prefix(value: str) -> str:
    cleaned = []
    for char in value:
        if char.isdigit() or char in {".", "-"}:
            cleaned.append(char)
        elif cleaned:
            break
    return "".join(cleaned)


def _build_seed(underlying: str, use_mock_seed: bool) -> str:
    if use_mock_seed:
        return get_mock_seed(underlying)

    try:
        return build_market_seed(underlying)
    except Exception:
        return get_mock_seed(underlying)


def run_simulation(
    scenario_id: str,
    n_agents: int = None,
    n_rounds: int = 40,
    custom_variable: str = None,
    underlying: str = "NIFTY",
    use_mock_seed: bool = None,
) -> dict:
    try:
        scenario = get_scenario(scenario_id)
        if n_agents is None:
            n_agents = scenario["default_agents"]

        if custom_variable:
            scenario["variable_injection"] = custom_variable

        if use_mock_seed is None:
            use_mock_seed = getattr(Config, "SEED_MODE", "document") == "mock"

        seed_text = _build_seed(underlying, use_mock_seed)
        if not seed_text:
            seed_text = get_mock_seed(underlying)

        pcr_line = _extract_seed_value(seed_text, "PCR")
        max_pain_line = _extract_seed_value(seed_text, "Max Pain Strike")
        pcr = _extract_numeric_prefix(pcr_line) or "0.0"
        max_pain = _extract_numeric_prefix(max_pain_line) or "0"

        injection_text = fill_scenario_variable(
            scenario,
            pcr=pcr,
            max_pain=max_pain,
            company="NIFTY",
            quarter="Q4",
            pct=8,
            user_defined_variable=custom_variable or "",
        )

        simulation_result = None

        # The existing OASIS stack is graph-first. The nearest synchronous entry point
        # we can safely invoke here without inventing a new interface is simulation creation.
        try:
            manager = SimulationManager()
            state = manager.create_simulation(
                project_id=f"scenario_{scenario_id}",
                graph_id="seed_only_graph",
                enable_twitter=True,
                enable_reddit=True,
            )
            simulation_result = state.to_simple_dict()
        except Exception as simulation_exc:
            logger.warning("Scenario simulation bootstrap failed: %s", simulation_exc)
            simulation_result = None

        return {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "injection_text": injection_text,
            "seed_summary": seed_text[:300],
            "n_agents": int(n_agents),
            "n_rounds": int(n_rounds),
            "underlying": underlying,
            "timestamp": datetime.now().isoformat(),
            "simulation_result": simulation_result,
            "status": "success",
            "error": None,
        }
    except Exception as exc:
        return {
            "scenario_id": scenario_id,
            "scenario_name": "",
            "injection_text": custom_variable or "",
            "seed_summary": "",
            "n_agents": n_agents,
            "n_rounds": n_rounds,
            "underlying": underlying,
            "timestamp": datetime.now().isoformat(),
            "simulation_result": None,
            "status": "failed",
            "error": str(exc),
        }
