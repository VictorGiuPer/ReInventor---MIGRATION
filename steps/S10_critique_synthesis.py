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

    The user has completed three rounds of critique across multiple frameworks and has reflected on each round. Your job is not to summarize what happened — the user lived it. Your job is to tell them what it all means: what the most important unresolved problems are, where their thinking has genuinely strengthened, and where they may be fooling themselves.

    Here is the FINAL consolidated context summary:
    ---
    {final_context_summary}
    ---

    Here are ALL critiques raised across the critique rounds:
    ---
    {all_critiques}
    ---

    Here are the user's reflections across all critique rounds:
    ---
    {all_user_reflections}
    ---

    ### Your task

    **1. Cross-cutting themes**
    Identify 2–3 concerns that appeared across multiple frameworks or rounds — the problems the critique kept circling back to from different angles. These are the load-bearing risks. Name them plainly and explain why they kept surfacing.

    **2. Resolved vs. unresolved**
    For each major concern raised across the rounds, make a direct assessment:
    - Has the user genuinely addressed it, or just acknowledged it?
    - If addressed, has their resolution introduced any new assumptions worth flagging?
    - If unresolved, say so plainly.

    **3. Blind spots that remain**
    If the critique rounds collectively missed something important — a pattern you can see by looking across all the material — name it. This is the one place where you may introduce a new observation, but only if it is clearly supported by what's already in the context.

    **4. Criticality ranking**
    List the top 3 unresolved concerns in order of criticality. For each:
    - One sentence stating the concern
    - Criticality: High / Medium / Low
    - One sentence on why it's ranked where it is

    ---

    ### Output format:

    🧠 **Critique Synthesis**

    **Cross-cutting themes:**
    [2–3 themes that kept surfacing, and why they matter]

    **What you've genuinely resolved:**
    [Honest assessment of what the user's reflections have actually strengthened]

    **What remains unresolved:**
    [Direct assessment of open problems — no softening]

    **Remaining blind spot:**
    [One observation the critique rounds didn't fully surface, if one exists. Skip this section if nothing meaningful to add.]

    **Top 3 concerns going into mitigation:**
    1. [Concern] — Criticality: High/Medium/Low — [Why]
    2. [Concern] — Criticality: High/Medium/Low — [Why]
    3. [Concern] — Criticality: High/Medium/Low — [Why]
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
