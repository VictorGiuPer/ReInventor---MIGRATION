# actions/mitigation.py

from steps.S11_mitigations import mitigation_improvement_suggestions


def run_mitigation_generation(*, state):
    """
    Generates mitigation and improvement suggestions.
    """

    all_user_reflections = ""
    for key in [
        "user_responses_round_1",
        "user_responses_round_2",
        "user_responses_round_3",
    ]:
        if key in state:
            all_user_reflections += (
                f"\n---\n{state[key]['full_response_input']}"
            )

    mitigation_output = mitigation_improvement_suggestions(
        state["context_summary"],
        state["critique_synthesis"],
        all_user_reflections,
        state["structured_input"]["abstraction_level"],
    )

    state["mitigation_improvement_output"] = mitigation_output

    return {"success": True}
