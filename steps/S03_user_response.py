from llm_client import client

def context_prompt(user_inputs: dict, clarification_answers: dict) -> str:
    # Construct a prompt that consolidates all known context
    return f"""
    You are the Summarizer in the Idea Hardener process.
    Here's the structured context provided by the user so far:

    Problem:
    {user_inputs['problem']}

    Idea / Approach:
    {user_inputs['approach']}

    Stakeholder:
    {user_inputs['stakeholder']}

    Constraints & Non-Negotiables:
    {', '.join(user_inputs['constraints'])}

    Clarification Answers:
    {clarification_answers}
    
    Abstraction Level:
    {user_inputs["abstraction_level"]}

    Your task:
    1. Produce a concise, logically structured summary that captures:
        - The problem being tackled
        - The proposed idea
        - The relevant stakeholder(s)
        - Any constraints or boundaries
        - Key clarifications just added. If the clarification answers were gibberish, one-word, or otherwise unhelpful, include one plain sentence in the summary noting this.

    2. Write in an assertive tone. This summary will become the base memory for the next steps in the critique process.

    Output format:
    ---
    **Updated Idea Summary:**
    [Your 6-8 sentence structured summary]
    ---
    """

def context_summary_0(user_inputs: dict, clarification_answers: str) -> str:
    # Build the consolidation prompt from structured inputs and clarifications
    prompt = context_prompt(user_inputs, clarification_answers)

    # Single LLM call to generate the updated working context
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # Replace with your actual model ID
        messages=[
            {"role": "system", "content": "You are a helpful and structured idea critique assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


