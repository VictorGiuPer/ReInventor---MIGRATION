from llm_client import client

def context_summary_1(context_summary: str, critique_text: str, user_feedback: str) -> str:
    """
    Calls the LLM with context, critique, and user feedback,
    and returns the updated context summary.
    """
    # Build a prompt that both acknowledges the user's reflections
    # and updates the working context for the next critique round
    prompt = f"""
        You are the Context Updater in the Idea Hardener process.

    We have completed Round 1 of critique. Your job is to acknowledge the user's reflections and produce an updated context summary that will carry forward into the next step.

    Here is the **previous context summary** (contains all context accumulated so far):
    ---
    {context_summary}
    ---

    Here is the **critique output** from Round 1:
    ---
    {critique_text}
    ---

    Here is the **user's response to that critique**:
    ---
    {user_feedback}
    ---

    Your task has two parts:

    **Part 1 — Acknowledgement**
    Write a short response directly to the user (second person only — "you said", "you think", "you suggested"). Aim for 5–6 sentences covering the most substantive points they raised.
    - If their response was vague, one-word, or gibberish, note it plainly within the acknowledgement: e.g. "Your responses this round didn't give much to work with — the process works best when you engage with the critique directly."
    - Do not describe the user in third person.

    **Part 2 — Updated Context Summary**
    Produce a structured summary that consolidates everything known so far. This is passed as working memory to all subsequent steps, so it must be complete and self-contained — do not assume the next step has access to earlier summaries.

    Include:
    - Problem
    - Idea / Approach
    - Stakeholder / Audience
    - Constraints & Non-Negotiables
    - Key reflections and position updates from ALL critique rounds so far (not just Round 1)
    - Any unresolved tensions or open questions surfaced through critique that the user has not yet addressed

    ⚠️ Output format:

    ACKNOWLEDGEMENT:
    [5–6 sentences directly to the user]

    ---

    UPDATED CONTEXT SUMMARY:
    [Full structured summary — self-contained, cumulative, complete]
    """

    # Single LLM call that performs acknowledgement + context consolidation
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # Replace with your deployment
        messages=[
            {"role": "system", "content": "You are a clear and concise context summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    # Return only the model's generated critique text
    return response.choices[0].message.content
