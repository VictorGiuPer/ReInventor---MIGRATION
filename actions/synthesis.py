# actions/synthesis.py

from steps.S10_critique_synthesis import critique_synthesis


def run_critique_synthesis(*, state):
    """
    Generates the aggregated critique summary with criticality ranking.
    """

    # Combine all critique outputs
    all_critiques = ""
    for key in ["critique_round_1", "critique_round_2", "critique_round_3"]:
        if key in state:
            all_critiques += f"\n---\n{state[key]}"

    # Combine all user reflections
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

    aggregated_output = critique_synthesis(
        state["context_summary"],
        all_critiques,
        all_user_reflections,
    )

    state["critique_synthesis"] = aggregated_output

    return {"success": True}
