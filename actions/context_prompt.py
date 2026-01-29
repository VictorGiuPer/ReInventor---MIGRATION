# actions/context_prompt.py

from steps.S12_context_prompt import context_prompt


def run_context_prompt_generation(*, state):
    """
    Generates a context-setting prompt for external LLM use.
    """

    prompt = context_prompt(
        context_summary=state["context_summary"],
        critique_synthesis=state["critique_synthesis"],
        mitigations=state["mitigation_improvement_output"],
    )

    state["context_prompt"] = prompt
    return {"success": True}
