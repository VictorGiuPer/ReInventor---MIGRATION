from steps.S01_input import format_user_input
from steps.S02_clarify import clarification_prompt, generate_clarification

def run_clarification(
    *,
    state,
    problem: str,
    approach: str,
    stakeholder: str,
    constraints: str,
    abstraction: int,
):
    """
    Executes Step 1: Generate clarifying questions.
    Mutates state in-place.
    """

    if not problem or not approach:
        return {"error": "Please provide both problem and approach."}

    # Reset state to step 0
    state.clear_except({"problem", "approach", "stakeholder", "constraints", "abstraction"})

    structured = format_user_input(
        problem, approach, stakeholder, constraints, abstraction
    )

    state["structured_input"] = structured
    state["formatted_input"] = structured["full_input"]

    prompt = clarification_prompt(structured["full_input"])
    state["clarification_output"] = generate_clarification(prompt)

    return {"success": True}