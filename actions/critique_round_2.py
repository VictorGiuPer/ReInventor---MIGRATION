# actions/critique_round_2.py

from core.utils import extract_framework_names, format_user_responses_to_critique
from steps.S06_critique_2 import critique_round_2
from steps.S07_user_reflect_2 import context_summary_2

def run_critique_round_2(
    *,
    state,
    abstraction_level: int,
):
    """
    Runs Critique Round 2 (LLM).
    """
    critique_output = critique_round_2(
        state["context_summary"],
        abstraction_level,
        state["frameworks_used_round_1"],
    )

    state["critique_round_2"] = critique_output
    state["frameworks_used_round_2"] = extract_framework_names(critique_output)

    return {"success": True}


def submit_reflections_round_2(
    *,
    state,
    responses_snapshot: dict,
):
    """
    Handles user reflections for Critique Round 2.
    """
    formatted = format_user_responses_to_critique(responses_snapshot)
    state["user_responses_round_2"] = formatted

    updated = context_summary_2(
        state["context_summary"],
        state["critique_round_2"],
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

    state["acknowledgement_round_2"] = acknowledgement_text
    state["context_summary"] = new_context

    return {"success": True}
