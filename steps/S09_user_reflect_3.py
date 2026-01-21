from llm_client import client

def context_summary_3(context_summary: str, critique_text: str, user_feedback: str) -> str:
    """
    Calls the LLM with context, critique output, and user feedback,
    and returns the combined acknowledgement + updated context summary.
    """
    prompt = f"""
    You are the Context Updater in the Idea Hardener process.

    We have already generated an idea summary and three rounds of critique using selected frameworks.

    Here is the **previous context summary**:
    ---
    {context_summary}
    ---

    Here is the **critique output** from Round 3:
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
    - Write in a conversational tone.
    - Aim for roughly 6 sentences total.

    2. Generate an updated, structured context summary that consolidates:
    - Problem
    - Idea / Approach
    - Stakeholder / Audience
    - Constraints & non-negotiables
    - Clarifications
    - User feedback from Round 3

    ⚠️ Format your output exactly like this:

    ACKNOWLEDGEMENT:
    [Your short UI-visible message here]

    ---

    UPDATED CONTEXT SUMMARY:
    [The full new structured summary here — this will be saved and passed to the next step]
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # Replace with your deployment name
        messages=[
            {"role": "system", "content": "You are a clear and concise context summarization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content
