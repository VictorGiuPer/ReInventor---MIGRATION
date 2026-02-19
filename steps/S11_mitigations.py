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
    You are the Mitigation Engine in the Idea Hardener workflow.

    The user has completed three rounds of critique and a synthesis that identified their most important unresolved concerns. Your job is to turn those concerns into concrete, prioritized actions — not a generic improvement list, but specific moves this person can make given their context, constraints, and stakeholders.

    Here is the **final consolidated context summary**:
    ---
    {final_context_summary}
    ---

    Here is the **critique synthesis**, including the top ranked concerns:
    ---
    {critique_synthesis}
    ---

    Here are the user's **reflections across all critique rounds**:
    ---
    {all_user_reflections}
    ---

    Abstraction Level: {abstraction_level}
    Calibrate accordingly: strategic level means focus on positioning, sequencing, and structural decisions. Tactical level means focus on concrete steps, resources, and near-term actions.

    ### Your task

    Work through the top concerns from the synthesis in order of criticality. For each:

    1. **Restate the concern in one sentence** — grounded in this specific idea, not generic
    2. **Recommend 2–3 mitigation actions** — concrete moves that reduce the risk or address the gap. Scale depth to criticality: High concerns get more specific actions, Low concerns get leaner ones.
    3. **Flag any trade-off** — if mitigating this concern creates tension with another part of the idea or with the user's constraints, name it explicitly.

    After addressing individual concerns, add one closing section:

    **What to do first** — given everything, what is the single highest-leverage action the user should take before anything else, and why.

    Rules:
    - Stay grounded in the user's actual context, constraints, and stakeholders — no generic advice.
    - Do not re-raise concerns the synthesis marked as resolved.
    - Do not introduce new critique.
    - If the user's own reflections already pointed toward a good mitigation, build on it rather than replacing it.
    - Be direct. Recommended actions should be specific enough that the user knows what to do Monday morning.

    ### Output format:

    **Mitigations**

    **[Concern 1 — Criticality: High/Medium/Low]**
    [One sentence restating the concern]
    - [Action 1]
    - [Action 2]
    - [Action 3 if warranted]
    ⚠️ Trade-off: [If applicable]

    **[Concern 2 — Criticality: High/Medium/Low]**
    [One sentence restating the concern]
    - [Action 1]
    - [Action 2]
    ⚠️ Trade-off: [If applicable]

    (Continue for remaining concerns)

    ---

    **What to do first:**
    [Single highest-leverage action and the reasoning behind it]
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
