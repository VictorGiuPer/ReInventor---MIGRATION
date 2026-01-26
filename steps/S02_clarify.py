from llm_client import client

print(client)

def clarification_prompt(formatted_input: str) -> str:
    # Construct the system-guided prompt that forces the model
    # to clarify and restate the idea without offering critique

    return f"""
    ROLE: You are the Clarifier in the Idea Hardener process. Your only job is to ensure you fully understand the user’s idea before any critique happens.
    CONTEXT: The user has submitted an early-stage idea. Your job is to carefully reframe it, decompose it, and uncover missing elements by asking precise clarifying questions.
    
    USER INPUT: 
    ---
    {formatted_input}
    ---
    
    INSTRUCTIONS: 
    1. Rephrase the idea in a more holistic and structured way. Summarize it logically.
    2. Decompose it into parts: problem, proposed solution, personas, assumptions.
    3. Identify what’s **missing or ambiguous** (e.g. constraints, stakeholders, logic gaps).
    4. Ask 5 **clarifying questions** to resolve these gaps.
        - Be **targeted** and **specific**.
        - DO NOT include suggestions or critique.
        - Questions should reflect genuine curiosity and logical gaps.

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
    - Your role is to **set the stage** for later critique by ensuring clarity now.
    - Assume this is the **user’s first time** articulating the idea."""

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