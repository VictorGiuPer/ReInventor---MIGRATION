from llm_client import client

def critique_synthesis(
    final_context_summary: str,
    all_critiques: str,
    all_user_reflections: str,
    ) -> str:
    """
    Generates a concise synthesis per critique framework,
    including criticality and contextual importance.
    """

    prompt = f"""
    You are the Synthesis Engine in the Idea Hardener workflow.

    The user has completed:
    - An initial idea articulation
    - Clarification questions
    - Three rounds of critique using different frameworks
    - Multiple rounds of reflection and context updates

    Your role now is NOT to introduce new critique or reorganize ideas.
    Your role is to **compress and prioritize the existing critique** so the user can clearly see what matters most.

    ---

    Here is the FINAL consolidated context summary:
    ---
    {final_context_summary}
    ---

    Here are ALL critiques raised across the critique rounds:
    ---
    {all_critiques}
    ---

    Here are the user’s reflections across all critique rounds:
    ---
    {all_user_reflections}
    ---

    ### Your task

    For **each critique framework that was used**, do the following:

    1. Write **one concise sentence** that synthesizes the *core concern* raised by that framework  
    - This should be a summary, not a repetition
    - No more than one sentence

    2. Assign a **Criticality level**:
    - **High** — would significantly block or derail the idea if unaddressed
    - **Medium** — important to address but not blocking
    - **Low** — useful improvement but non-essential

    3. Briefly explain how the users comments already consider or do not consider this critique and if possible build on top of the users ideas.

    ---

    ### Output format (use exactly this structure):

    🧠 **Critique Synthesis & Priority Overview**

    **[Framework Name]**
    - **Synthesis:** One-sentence summary of the core concern.
    - **Criticality:** High | Medium | Low
    - **Why this matters:** 2–3 sentences of contextual justification.

    (Repeat for each framework used.)

    ---

    Rules:
    - Do NOT introduce new critiques.
    - Do NOT cluster or merge frameworks.
    - Do NOT propose solutions or next steps.
    - Be decisive and prioritization-oriented.
    - Assume the user is already familiar with the details.

    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # adjust to your deployment
        messages=[
            {"role": "system", "content": "You are a concise prioritization and synthesis assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content
