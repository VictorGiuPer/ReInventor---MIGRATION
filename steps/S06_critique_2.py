from llm_client import client
from core.utils import load_frameworks, build_framework_list_text, filter_unused_frameworks

def critique_round_2(
    context_summary: str,
    abstraction_level: int,
    frameworks_used_round_1: list[str]
) -> str:
    """
    Full orchestration for Critique Round 2 using new, orthogonal frameworks.
    """

    # Load the full framework library
    all_frameworks = load_frameworks()

    # Remove previously used frameworks
    unused_frameworks = filter_unused_frameworks(
        all_frameworks,
        frameworks_used_round_1
    )

    # Convert remaining frameworks into a readable list for the LLM
    framework_list = build_framework_list_text(unused_frameworks)

    # Construct the second-round critique prompt
    prompt = f"""
    You are the Critique Engine in the Idea Hardener workflow.

    Here is the UPDATED user's idea context:
    ---
    {context_summary}
    ---

    Critique Abstraction Level: {abstraction_level}

    The following critique frameworks were already used in Round 1.
    You MUST NOT use them again and must choose orthogonal alternatives.

    Used frameworks (DO NOT select):
    {", ".join(frameworks_used_round_1)}

    Below is the remaining available critique frameworks:
    {framework_list}

    Your task:
    - Select exactly three (3) frameworks from the remaining list.
    - Ensure they are meaningfully different from those used in Round 1.
    - For each selected framework:
        - Use the **output instructions** included in the framework list to guide your critique output format
        - Focus ONLY on critique (risks, assumptions, blind spots, constraints).
        - DO NOT propose solutions or mitigations at this step.
    - Avoid repeating critique already covered in Round 1.

    Output Format:
    (important information should be outlined with **...**)

    ###Framework Name 1
    [Framework 1 output structure]

    ###Framework Name 2
    [Framework 2 output structure]

    ###Framework Name 3
    [Framework 3 output structure]
    """

    # Single LLM call to generate the second structured critique pass
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a structured and rigorous critique assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    # Return only the model's generated critique text
    return response.choices[0].message.content
