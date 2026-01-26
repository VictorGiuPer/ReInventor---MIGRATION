# actions/critique_round_1.py

from core.utils import extract_framework_names
from steps.S04_critique_1 import critique_1
from steps.S05_user_reflect_1 import context_summary_1
from core.utils import format_user_responses_to_critique

def run_critique_round_1(
    *,
    state,
    abstraction_level: int,
):
    """
    Runs Critique Round 1 (LLM).
    """
    state.clear_except(
        {
            "structured_input",
            "formatted_input",
            "context_summary",
        }
    )

    critique_output = critique_1(
        state["context_summary"],
        abstraction_level,
    )

    state["critique_round_1"] = critique_output
    state["frameworks_used_round_1"] = extract_framework_names(critique_output)

    return {"success": True}


def submit_reflections_round_1(
    *,
    state,
    responses_snapshot: dict,
):
    """
    Handles user reflections for Critique Round 1.
    """
    formatted = format_user_responses_to_critique(responses_snapshot)
    state["user_responses_round_1"] = formatted

    updated = context_summary_1(
        state["context_summary"],
        state["critique_round_1"],
        formatted,
    )

    new_context = updated.split("UPDATED CONTEXT SUMMARY:")[-1].strip()
    acknowledgement_text = (
        updated
        .split("ACKNOWLEDGEMENT:")[1]
        .split("UPDATED CONTEXT SUMMARY:")[0]
        .strip()
    )

    state["acknowledgement_round_1"] = acknowledgement_text
    state["context_summary"] = new_context

    return {"success": True}
