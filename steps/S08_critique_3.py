from llm_client import client
from core.utils import load_frameworks

def critique_round_3(context_summary: str, abstraction_level: int, frameworks_selected: list[str]) -> str:
    """
    Critique using user‑selected frameworks.
    """

    all_frameworks = load_frameworks()

    # Extract only the descriptions of frameworks explicitly selected by the user
    selected_descriptions = []
    for fw in all_frameworks:
        if fw["name"] in frameworks_selected:
            selected_descriptions.append(
                f"{fw['name']}: {fw['description']}"
            )

    # Build a readable framework definition block for the LLM
    selected_text = "\n".join(selected_descriptions)

    # Construct the third critique prompt:
    prompt = f"""
    You are the Critique Engine in the Idea Hardener workflow.

    Here is the UPDATED user's idea context:
    ---
    {context_summary}
    ---

    Critique Abstraction Level: {abstraction_level}

    The user has chosen the following frameworks for critique:
    {selected_text}

    Your task:
    - Critique only through the selected frameworks — no additions, no extras.
    - This is the final round. Prioritize depth over breadth. Surface the risks that the previous rounds may have circled around but not fully confronted.
    - Read the updated context carefully. Do not re-raise issues the user has genuinely resolved. If they addressed something poorly or introduced new assumptions in doing so, that is fair game.
    - Be direct and specific. Do not soften findings. Where something is a potentially fatal flaw, say so explicitly.
    - Focus ONLY on critique and DO NOT propose solutions or mitigations.
    - Use the **output instructions** included in the framework list to guide your critique output format


    Output Format:

    🔍 **Critique Round 3**

    ###Framework Name 1
    [Framework 1 output structure]

    ###Framework Name 2
    [Framework 2 output structure]

    ###Framework Name 3
    [Framework 3 output structure]
    """

    # Single LLM call to generate the optional, user-directed critique
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # or your actual deployment
        messages=[
            {"role": "system", "content": "You are a structured and rigorous critique assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    # Return only the model's generated critique text
    return response.choices[0].message.content
