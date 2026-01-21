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

    We have already generated an initial idea summary and a first round of critique using selected frameworks.

    Here is the **previous context summary**:
    ---
    {context_summary}
    ---

    Here is the **critique output** from Round 1:
    ---
    {critique_text}
    ---

    Here is the **user’s responses to that critique**:
    ---
    {user_feedback}
    ---
    IF THE USER INPUT IS NONSENSE/GIBERISH/WITHOUT ESSENCE BRIEFLY CALL IT OUT IN THE ACKNOWLEDGEMENT MESSAGE MENTIONING THAT IT WITHOUT PROPER INPUT THE PROCESS WONT WORK.

    Your task has two parts:

    1. Acknowledge the user's reflections directly by speaking to them in second person.
    - Do NOT describe the user in third person.
    - Use phrases like “you said”, “you think”, or “you suggested”.
    - Write in a conversational tone, as if responding directly to the user.
    - Aim for exactly 6 sentences total, roughly 2 sentences per critique.    
    2. Generate an updated, structured context summary that consolidates:
    - Problem
    - Idea / Approach
    - Stakeholder / Audience
    - Constraints & non‑negotiables
    - User’s reflections from the critique round 1

    ⚠️ Format your output like this:

    ACKNOWLEDGEMENT:
    [Your short UI-visible message here]

    ---

    UPDATED CONTEXT SUMMARY:
    [The full new structured summary here — this will be saved and passed to the next round of critique]
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
