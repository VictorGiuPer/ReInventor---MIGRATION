from llm_client import client

def extract_questions(clarification_output: str) -> list:
    """
    Extract clarifying questions from the LLM's output.
    Simple parser based on markdown-style list (e.g. "1. Question").
    """
    # Extract numbered clarification questions (assumes "1. Question" format)
    lines = clarification_output.split("\n")
    questions = [line.strip()[3:] for line in lines if line.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. "))]
    return questions


def context_prompt(user_inputs: dict, clarification_answers: dict) -> str:
    # Construct a prompt that consolidates all known context
    return f"""
    You are the Summarizer in the Idea Hardener process.
    Here’s the structured context provided by the user so far:

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
        - Key clarifications just added

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


