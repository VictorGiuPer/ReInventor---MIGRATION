from llm_client import client

def mitigation_improvement_suggestions(
    final_context_summary: str,
    critique_synthesis: str,
    all_user_reflections: str,
    abstraction_level: int
) -> str:
    """
    Calls the LLM to generate mitigation strategies and improvement ideas.
    """
    prompt = f"""
    You are the Mitigation & Improvement Engine in the Idea Hardener workflow.

    The user has completed:
    - The initial idea articulation
    - Clarification questions
    - Three rounds of critique
    - Reflections after each critique round
    - A concise synthesis of critique themes with criticality rankings

    Here is the **final consolidated context summary**:
    ---
    {final_context_summary}
    ---

    Here is the **critique synthesis output** with criticality levels:
    ---
    {critique_synthesis}
    ---

    Here are the user's **reflections across all critique rounds**:
    ---
    {all_user_reflections}
    ---

    Critique Abstraction Level: {abstraction_level}

    Your task is to produce **practical, grounded, and realistic recommendations** for each critique insight.

    For each critique, do the following:

    1) Provide 2 mitigation strategies — realistic steps the user can take to reduce the identified risk or limitation.
    2) Provide 2 idea improvement suggestions — ways to strengthen or pivot the idea while remaining true to the original intent.
    3) Frame recommendations with:
    - The stakeholder in mind
    - The constraints & non‑negotiables
    - The abstraction level (practical vs conceptual focus)

    Important:
    - Align all recommendations with the user’s context.
    - Do NOT repeat critique points; focus on actionable ideas.
    - Outputs should be clear, concise, and logically grounded.

    Output format:

    **Mitigations & Improvement Ideas**

    **[Framework / Critique]**
    **Criticality:** High | Medium | Low

    1) Mitigation Strategies:
    - ...
    - ...

    2) Idea Improvement Suggestion:
    - ...
    - ...
    """
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a structured and practical mitigation recommender."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.55
    )
    return response.choices[0].message.content
