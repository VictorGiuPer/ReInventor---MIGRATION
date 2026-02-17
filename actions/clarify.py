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
    Writes structured_input, formatted_input, and clarification_output into state.

    NOTE: State cleanup (clearing downstream keys) is handled entirely by
    clear_downstream() in app.py before this function is called.
    This function must NOT call state.clear() or state.clear_except() —
    doing so would wipe keys that app.py manages (e.g. available_frameworks)
    and fight with the downstream clearing logic.
    """

    if not problem or not approach:
        return {"error": "Please provide both problem and approach."}

    structured = format_user_input(
        problem, approach, stakeholder, constraints, abstraction
    )

    state["structured_input"] = structured
    state["formatted_input"] = structured["full_input"]

    prompt = clarification_prompt(structured["full_input"])
    state["clarification_output"] = generate_clarification(prompt)

    return {"success": True}