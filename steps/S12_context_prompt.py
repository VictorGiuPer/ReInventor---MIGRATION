# steps/S12_context_prompt.py

def context_prompt(
    context_summary: str,
    critique_synthesis: str,
    mitigations: str,
) -> str:
    """
    Produces a copy-paste-ready context-setting prompt
    for use in any downstream LLM.
    """

    system_prompt = f"""
    You are an expert reasoning assistant.

    I previously worked through a structured critique
    process to stress-test an idea. You are now asked to help me
    continue working on that idea using the full context below.

    Your task:
    - Do NOT re-critique unless explicitly asked
    - Focus on constructive solution development

    AGGREGATED CRITIQUE SUMMARY
    {critique_synthesis}

    MITIGATIONS & IMPROVEMENTS
    {mitigations}

    INSTRUCTIONS
    Using the context above, help me continue productively.
    [ADD YOUR PRIORITIES, FOCUS TOPICS (MITIGATIONS) OR OTHER INSTRUCTIONS]
    """.strip()

    return system_prompt
