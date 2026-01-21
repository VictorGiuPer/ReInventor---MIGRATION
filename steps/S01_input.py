def format_user_input(problem: str, approach: str, stakeholder: str, constraints: str, abstraction_level: int) -> dict:
    # Normalize constraints input into a clean list (one per line, no blanks)
    constraints_list = [c.strip() for c in constraints.split("\n") if c.strip()]

    # Build a single formatted text block for LLM consumption
    full_input = (
        f"Problem:\n{problem.strip()}\n\n"
        f"Proposed Approach:\n{approach.strip()}\n\n"
        f"Primary Stakeholder:\n{stakeholder.strip()}\n\n"
        f"Constraints & Non-Negotiables:\n" + "\n".join(f"- {c}" for c in constraints_list) + "\n\n"
        f"Critique Abstraction Level: {abstraction_level}"
    )

    # Return both structured fields (for programmatic use) and the formatted text block (for prompt injection)
    return {
        "problem": problem.strip(),
        "approach": approach.strip(),
        "stakeholder": stakeholder.strip(),
        "constraints": constraints_list,
        "abstraction_level": abstraction_level,
        "full_input": full_input
    }
