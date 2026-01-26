# actions/critique_round_3.py

from core.utils import format_user_responses_to_critique
from steps.S08_critique_3 import critique_round_3
from steps.S09_user_reflect_3 import context_summary_3


def run_critique_round_3(
    *,
    state,
    abstraction_level: int,
    selected_frameworks: list[str],
):
    """
    Runs optional Critique Round 3.
    """
    critique_output = critique_round_3(
        state["context_summary"],
        abstraction_level,
        selected_frameworks,
    )

    state["critique_round_3"] = critique_output
    state["user_selected_frameworks"] = selected_frameworks

    return {"success": True}


def submit_reflections_round_3(
    *,
    state,
    responses_snapshot: dict,
):
    """
    Handles user reflections for Critique Round 3.
    """
    formatted = format_user_responses_to_critique(responses_snapshot)
    state["user_responses_round_3"] = formatted

    updated = context_summary_3(
        state["context_summary"],
        state["critique_round_3"],
        formatted["full_response_input"],
    )

    acknowledgement_text = (
        updated
        .split("ACKNOWLEDGEMENT:")[1]
        .split("UPDATED CONTEXT SUMMARY:")[0]
        .strip()
    )

    new_context = (
        updated
        .split("UPDATED CONTEXT SUMMARY:")[1]
        .strip()
    )

    state["acknowledgement_round_3"] = acknowledgement_text
    state["context_summary"] = new_context
    state["done_round_3"] = True

    return {"success": True}
