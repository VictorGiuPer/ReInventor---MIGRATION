import json
from pathlib import Path
import re

# Path to the canonical framework definitions used across critique rounds
FRAMEWORKS_PATH = Path("frameworks/frameworks.json")

def load_frameworks() -> list[dict]:
    # Load the full library of critique frameworks from disk.
    with open(FRAMEWORKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    
def build_framework_list_text(frameworks: list[dict]) -> str:
    """
    Turn frameworks JSON into a text block the LLM can read,
    including output format expectations for each framework.
    """
    blocks = []
    for fw in frameworks:
        name = fw["name"]
        desc = fw["description"]
        instr = fw.get("output_instructions", "")
        blocks.append(
            f"{name}:\n"
            f"{desc}\n"
            f"How to apply (output instructions): {instr}"
        )
    return "\n\n".join(blocks)


def filter_unused_frameworks(all_frameworks: list[dict], used_framework_names: list[str]) -> list[dict]:
    # Remove frameworks that have already been used in prior critique rounds.
    return [
        fw for fw in all_frameworks
        if fw["name"] not in used_framework_names
    ]

def format_user_responses_to_critique(responses: dict) -> dict:
    """
    Format user answers to each critique category for future LLM use.
    """
    formatted = "\n".join(
        [f"💡 **{framework}**\n{answer.strip()}" for framework, answer in responses.items()]
    )

    return {
        "framework_responses": responses,
        "full_response_input": formatted
    }

def extract_framework_names(critique_output: str) -> list:
    """
    Extracts framework names from the critique output.
    Filters out irrelevant headers like 'Critique Round'.
    """
    # Match headers like "### Framework Name"
    matches = re.findall(r"^###\s+(.*)", critique_output, re.MULTILINE)
    
    # Remove common non-framework headers
    excluded = {"Critique Round", "Critique Round 1", "Critique Round 2", "Critique Output"}
    frameworks = [m.strip() for m in matches if m.strip() not in excluded]

    # Return unique list preserving order
    seen = set()
    unique_frameworks = []
    for fw in frameworks:
        if fw not in seen:
            seen.add(fw)
            unique_frameworks.append(fw)

    return unique_frameworks

def get_reframed_understanding(clarification_output: str) -> str:
    # Split on the questions header and keep only the understanding part
    return clarification_output.split("🧩 Clarifying Questions:", 1)[0].strip()


def extract_questions(clarification_output: str) -> list:
    """
    Extract clarifying questions from the LLM's output.
    Simple parser based on markdown-style list (e.g. "1. Question").
    """
    # Extract numbered clarification questions (assumes "1. Question" format)
    lines = clarification_output.split("\n")
    questions = [line.strip()[3:] for line in lines if line.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. "))]
    return questions
