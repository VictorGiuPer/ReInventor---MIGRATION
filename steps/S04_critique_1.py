from llm_client import client
from core.utils import load_frameworks, build_framework_list_text

def critique_1(context_summary: str, abstraction_level: int) -> str:
    """
    Full orchestration for Critique Round 1 using real LLM + dynamic framework selection.
    """
    # Load the full framework library available for critique
    frameworks = load_frameworks()

     # Convert framework definitions into a readable text block for the LLM
    framework_list = build_framework_list_text(frameworks)

    # Construct the critique prompt
    prompt = f"""
    You are the Critique Engine in the Idea Hardener workflow.

    Here is the user's idea context:
    ---
    {context_summary}
    ---

    Critique Abstraction Level: {abstraction_level}
    Calibrate the depth and angle of your critique to this level:
    - Level 0–3 (Practical): Focus on execution risks — specific resource gaps, named actors, near-term blockers, and operational failure modes.
    - Level 4–6 (Balanced): Balance structural concerns with concrete execution risks.
    - Level 7–10 (Abstract): Focus on structural and conceptual risks — incentive dynamics, logical dependencies, systemic assumptions, and model-level flaws.

    Below is a list of possible critique frameworks. Select exactly three (3) that will surface the most distinct and non-obvious risks for this specific idea — not the most generic or broadly applicable ones.

    Frameworks:
    {framework_list}
    
    Your task:
    Select 3 frameworks and critique the idea through each one.
    - Be direct and specific. Do not soften findings. A real risk should be stated as a real risk.
    - Where something is a potentially fatal flaw, say so explicitly.
    - Focus ONLY on critique and DO NOT propose solutions or mitigations.
    - Use the **output instructions** included in the framework list to guide your critique output format

    Output Format:
    (important information should be outlined with **...**, to make them stand out in markdown)

    ###Framework Name 1
    [Framework 1 output structure]

    ###Framework Name 2
    [Framework 2 output structure]

    ###Framework Name 3
    [Framework 3 output structure]

    """

    # Single LLM call to generate the first structured critique pass
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a structured and rigorous critique assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content
