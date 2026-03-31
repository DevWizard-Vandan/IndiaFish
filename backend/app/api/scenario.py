"""
Scenario API routes.
"""

from flask import jsonify, request

from . import scenario_bp
from ..services.fo_signal_generator import process_simulation_output
from ..services.scenario_library import list_scenarios
from ..services.scenario_runner import run_simulation


@scenario_bp.route("/scenarios", methods=["GET"])
def get_scenarios():
    return jsonify(list_scenarios())


@scenario_bp.route("/simulate", methods=["POST"])
def simulate_scenario():
    body = request.get_json() or {}
    scenario_id = body.get("scenario_id")

    if not scenario_id:
        return jsonify({"error": "scenario_id required"}), 400

    result = run_simulation(
        scenario_id=scenario_id,
        n_agents=body.get("n_agents"),
        n_rounds=body.get("n_rounds", 40),
        custom_variable=body.get("custom_variable"),
        underlying=body.get("underlying", "NIFTY"),
    )

    if result.get("status") == "success":
        processed = process_simulation_output(result)
        result["fo_signals"] = processed["signals"]
        result["report_markdown"] = processed["report_markdown"]

    return jsonify(result)
