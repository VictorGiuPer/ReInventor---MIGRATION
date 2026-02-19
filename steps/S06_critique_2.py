from llm_client import client
from core.utils import load_frameworks, build_framework_list_text, filter_unused_frameworks

def critique_round_2(
    context_summary: str,
    abstraction_level: int,
    frameworks_used_round_1: list[str],
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
    - Select exactly three (3) frameworks from the remaining list that are meaningfully orthogonal to Round 1 — they should open new angles, not reframe the same risks.
    - Read the updated context carefully. If the user has genuinely resolved a Round 1 concern, do not re-raise it. If they addressed it poorly or introduced a new assumption in doing so, that is fair game.
    - Be direct and specific. Do not soften findings. Where something is a potentially fatal flaw, say so explicitly.
    - Focus ONLY on critique and DO NOT propose solutions or mitigations.
    - Use the **output instructions** included in the framework list to guide your critique output format
    
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
