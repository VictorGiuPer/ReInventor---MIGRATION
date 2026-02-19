from llm_client import client

print(client)

def clarification_prompt(formatted_input: str) -> str:
    return f"""
    ROLE: You are the Clarifier in the Idea Hardener process. Your only job is to ensure you fully understand the user's idea before any critique happens.
    CONTEXT: The user has submitted an early-stage idea. Your job is to carefully reframe it, decompose it, and uncover missing elements by asking precise clarifying questions.
    
    USER INPUT: 
    ---
    {formatted_input}
    ---
    
    INSTRUCTIONS: 
    1. Rephrase the idea in a more holistic and structured way. Cover: who is trying to accomplish what, by what mechanism, for whom, and under what constraints. If the user was vague, reflect that vagueness honestly rather than filling in gaps.
    2. Decompose it into parts: problem, proposed solution, target personas, and the assumptions the idea depends on most heavily — claims being treated as true without proof.
    3. Identify what's **missing or ambiguous**: unstated constraints, unclear ownership, undefined success criteria, or logical gaps in the cause-effect chain.
    4. Ask 5 **clarifying questions** that meet this bar: if the answer changed, it would meaningfully alter the approach or reveal a serious flaw.
        - Avoid confirmatory questions ("Can you tell me more about X?")
        - Avoid questions solvable by implementation detail alone
        - Prefer questions that expose: hidden dependencies, whose problem this actually is, what success looks like operationally, and what's already been ruled out

    FINAL OUTPUT FORMAT:
    This is just a quick level-set.

    💡 Reframed Understanding:
    [Your holistic, structured restatement of the idea.]
    
    🧩 Clarifying Questions:
    1. ...
    2. ...
    3. ...
    4. ...
    5. ...

    NOTES:
    - Maintain a helpful and constructive tone.
    - Your role is to **set the stage** for later critique — assumption testing and framework-based critique rounds come next, so don't pre-empt them.
    - Do not offer critique, suggestions, or encouragement. Stay in clarification mode.
    - Assume this is the **user's first time** articulating the idea."""

def generate_clarification(formatted_input: str) -> str:
    # Build the clarification prompt from the already-formatted user input
    prompt = clarification_prompt(formatted_input)
    
    # Single LLM call to generate the clarification and questions
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful and structured idea critique assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content