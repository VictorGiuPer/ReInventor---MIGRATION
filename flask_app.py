"""
ReInventor Flask Application
=============================
Main routing and state management for the 8-step idea critique workflow.

Architecture:
- User submits idea → clarify → 3 rounds of critique → synthesis → mitigations → context prompt
- State management via Flask sessions (filesystem-backed)
- Step progression determined by data presence (derive_current_step)
- Downstream state clearing prevents stale data from affecting re-runs
"""

import os

from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session

from state.flask_session_state import FlaskSessionState
from core.utils import extract_questions, get_reframed_understanding, load_frameworks

from steps.S03_user_response import context_summary_0

from actions.clarify import run_clarification
from actions.critique_round_1 import run_critique_round_1, submit_reflections_round_1
from actions.critique_round_2 import run_critique_round_2, submit_reflections_round_2
from actions.critique_round_3 import run_critique_round_3, submit_reflections_round_3
from actions.synthesis import run_critique_synthesis
from actions.mitigation import run_mitigation_generation
from actions.context_prompt import run_context_prompt_generation


# =============================================================================
# Flask App Configuration
# =============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = os.environ.get("SESSION_FILE_DIR", "./flask_sessions")

Session(app)


# =============================================================================
# State Management — Downstream Clearing
# =============================================================================
# When a user re-runs an earlier step, all data generated AFTER that step
# becomes stale and must be cleared. The DOWNSTREAM_KEYS map defines what
# gets wiped for each action.
#
# Example: re-running "submit_idea" wipes everything (clarification → context
# → all three critique rounds → synthesis → mitigations → context prompt).
#
# Principle: Every action clears only the data it produces + everything downstream.
# =============================================================================

# Round 3 data
_ROUND3_DATA = [
    "user_selected_frameworks", "done_round_3", "critique_round_3",
    "critique_response_r3_0", "critique_response_r3_1", "critique_response_r3_2",
    "acknowledgement_round_3",
]

# Everything downstream of Round 3
_DOWNSTREAM_OF_R3 = _ROUND3_DATA + [
    "critique_synthesis", "mitigation_improvement_output", "context_prompt",
]

DOWNSTREAM_KEYS = {
    # Step 1: Submit idea → wipes everything
    "submit_idea": [
        "clarification_output", "clarification_prompts", "reframed_understanding",
        "structured_input",
        "clarify_answer_0", "clarify_answer_1", "clarify_answer_2",
        "clarify_answer_3", "clarify_answer_4", "clarify_answer_5",
        "clarification_answers", "context_summary",
        "critique_round_1", "frameworks_used_round_1",
        "critique_response_r1_0", "critique_response_r1_1", "critique_response_r1_2",
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _DOWNSTREAM_OF_R3,

    # Step 2a: Generate context summary → wipes from summary onwards
    "update_summary": [
        "clarification_answers", "context_summary",
        "critique_round_1", "frameworks_used_round_1",
        "critique_response_r1_0", "critique_response_r1_1", "critique_response_r1_2",
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _DOWNSTREAM_OF_R3,

    # Step 3: Critique Round 1 → wipes R1 onwards
    "run_critique_1": [
        "critique_round_1", "frameworks_used_round_1",
        "critique_response_r1_0", "critique_response_r1_1", "critique_response_r1_2",
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _DOWNSTREAM_OF_R3,

    "submit_r1": [
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _DOWNSTREAM_OF_R3,

    # Step 5: Critique Round 2 → wipes R2 onwards
    "run_critique_2": [
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _DOWNSTREAM_OF_R3,

    "submit_r2": [
        "acknowledgement_round_2",
    ] + _DOWNSTREAM_OF_R3,

    # Step 7: Critique Round 3 (optional)
    "run_round_3": _ROUND3_DATA + [
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ],

    "skip_round_3": _ROUND3_DATA + [
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ],

    "submit_r3": [
        "acknowledgement_round_3",
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ],

    # Step 10: Synthesis
    "run_synthesis": [
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ],

    # Step 11: Mitigations
    "run_mitigations": [
        "mitigation_improvement_output", "context_prompt",
    ],

    # Step 12: Context prompt
    "generate_context_prompt": [
        "context_prompt",
    ],
}


def clear_downstream(state, action: str) -> None:
    """
    Clear all stale state data that becomes invalid after re-running `action`.
    
    Example: If user re-runs "submit_idea", all clarification, critique, and
    synthesis data is wiped because it was based on the old idea inputs.
    """
    for key in DOWNSTREAM_KEYS.get(action, []):
        state.pop(key, None)


# =============================================================================
# Step Derivation — Single Source of Truth
# =============================================================================
# The current step is derived from what data exists in the session, NOT stored
# as a separate variable. This prevents state desync issues.
#
# Step progression is automatic: when an action completes and writes its output,
# derive_current_step() returns the next step number, which triggers the next
# section to appear via HTML guards (e.g., {% if state.current_step >= 5 %}).
# =============================================================================

def derive_current_step(state) -> int:
    """
    Determine current step by checking which data exists.
    
    Returns:
        0:  Initial state (submit idea form)
        1:  Clarification questions generated
        2:  Context summary generated
        3:  Critique Round 1 output ready
        4:  Round 1 acknowledgement ready
        5:  Critique Round 2 output ready
        6:  Round 2 acknowledgement ready (transitions to Round 3 selector)
        7:  Round 3 selector shown
        8:  Critique Round 3 output ready
        10: Synthesis section (ack/skip Round 3 complete)
        11: Mitigations section
        12: Context prompt section
    """
    # Working backwards from final step to initial
    if state.get("context_prompt"):
        return 12
    
    if state.get("mitigation_improvement_output"):
        return 12  # Auto-show context prompt section
    
    if state.get("critique_synthesis"):
        return 11  # Auto-show mitigations section
    
    # Round 3 complete OR skipped → show synthesis
    if state.get("acknowledgement_round_3") or state.get("done_round_3"):
        return 10
    
    if state.get("critique_round_3"):
        return 8
    
    if state.get("acknowledgement_round_2"):
        return 7  # Show Round 3 selector
    
    if state.get("critique_round_2"):
        return 5
    
    if state.get("acknowledgement_round_1"):
        return 4
    
    if state.get("critique_round_1"):
        return 3
    
    if state.get("context_summary"):
        return 2
    
    if state.get("clarification_prompts"):
        return 1
    
    return 0


# =============================================================================
# Scroll Management
# =============================================================================
# After each action, the page auto-scrolls to the newly generated section.
# This prevents users from having to manually hunt for new content.
# =============================================================================

def scroll_target_for(current_step: int) -> str:
    """Map step number to HTML element ID for smooth scrolling."""
    return {
        1:  "step-2-questions",   # Clarification questions
        2:  "step-2-summary",      # Context summary
        3:  "step-3-critique",     # Critique Round 1
        4:  "step-3-ack",          # Round 1 acknowledgement
        5:  "step-4-critique",     # Critique Round 2
        6:  "step-4-ack",          # Round 2 acknowledgement
        7:  "step-5-select",       # Round 3 framework selector
        8:  "step-5-critique",     # Critique Round 3
        10: "step-6",              # Synthesis
        11: "step-7",              # Mitigations
        12: "step-8",              # Context prompt
    }.get(current_step, "step-1")


# =============================================================================
# Routes
# =============================================================================

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route — handles both initial page load and all form submissions.
    
    GET:  Load page with current state (rehydrate step from data if server restarted)
    POST: Process action, update state, re-render with new step
    """
    state = FlaskSessionState(session)
    message = None

    # ── GET: Initial page load ───────────────────────────────────────────
    if request.method == "GET":
        # Fresh session check: no data exists
        if not state.get("clarification_prompts") and not state.get("problem"):
            state.clear()
            state["current_step"] = 0
        else:
            # Rehydrate step from data (handles server restart)
            state["current_step"] = derive_current_step(state)
        
        return render_template(
            "index.html",
            state=dict(state._session),
            message=None,
            scroll_to=scroll_target_for(state.get("current_step", 0)),
        )

    # ── POST: Handle action ──────────────────────────────────────────────
    action = request.form.get("action", "submit_idea")

    # Ensure framework list is always available for Round 3
    if "available_frameworks" not in state:
        all_frameworks = load_frameworks()
        state["available_frameworks"] = [
            {"name": fw["name"], "tooltip": fw["tooltip"]}
            for fw in all_frameworks
        ]

    # Clear stale downstream data BEFORE running action
    clear_downstream(state, action)

    # ═════════════════════════════════════════════════════════════════════
    # Action Routing
    # ═════════════════════════════════════════════════════════════════════

    # ── Step 1: Submit Idea ──────────────────────────────────────────────
    if action == "submit_idea":
        state["problem"]     = request.form.get("problem", "")
        state["approach"]    = request.form.get("approach", "")
        state["stakeholder"] = request.form.get("stakeholder", "")
        state["constraints"] = request.form.get("constraints", "")
        state["abstraction"] = int(request.form.get("abstraction", 5))

        if not state["problem"] or not state["approach"]:
            message = "Please provide both a problem and an approach."
        else:
            result = run_clarification(
                state=state,
                problem=state["problem"],
                approach=state["approach"],
                stakeholder=state["stakeholder"],
                constraints=state["constraints"],
                abstraction=state["abstraction"],
            )
            if "error" in result:
                message = result["error"]
            else:
                # Extract clarification questions from LLM output
                questions = extract_questions(state["clarification_output"])
                state["clarification_prompts"] = (
                    ["Correct the model's understanding (type '-' if none)"]
                    + questions
                )
                state["reframed_understanding"] = get_reframed_understanding(
                    state["clarification_output"]
                )

    # ── Step 2: Generate Context Summary ─────────────────────────────────
    elif action == "update_summary":
        # Save clarification answers (only fields submitted in this form)
        submitted_answers = {
            key: value
            for key, value in request.form.items()
            if key.startswith("clarify_answer_")
        }
        if submitted_answers:
            for key, value in submitted_answers.items():
                state[key] = value

        # Validate all answers filled
        answers = {k: state[k] for k in state.keys() if k.startswith("clarify_answer_")}
        if not all(v.strip() for v in answers.values()):
            message = "Please fill out every field. Use '-' if you have nothing to add."
        else:
            # Package answers and generate summary
            prompts = state["clarification_prompts"]
            state["clarification_answers"] = {
                "llm_understanding_correction": state["clarify_answer_0"],
                "clarifying_answers": {
                    prompts[i + 1]: state[f"clarify_answer_{i + 1}"]
                    for i in range(len(prompts) - 1)
                },
            }
            summary = context_summary_0(
                state["structured_input"],
                state["clarification_answers"],
            )
            state["context_summary"] = summary

    # ── Step 3: Run Critique Round 1 ─────────────────────────────────────
    elif action == "run_critique_1":
        # Allow inline editing of context summary
        updated_summary = request.form.get("context_summary", "").strip()
        if updated_summary:
            state["context_summary"] = updated_summary

        run_critique_round_1(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
        )

    # ── Step 4: Submit Round 1 Reflections ───────────────────────────────
    elif action == "submit_r1":
        responses_snapshot = {}
        frameworks = state.get("frameworks_used_round_1", [])
        
        for idx, fw in enumerate(frameworks):
            key = f"critique_response_r1_{idx}"
            state[key] = request.form.get(key, "")
            responses_snapshot[fw] = state[key]

        if not all(v.strip() for v in responses_snapshot.values()):
            message = "Please fill in all fields (use '-' if no response)."
        else:
            submit_reflections_round_1(
                state=state,
                responses_snapshot=responses_snapshot
            )

    # ── Step 5: Run Critique Round 2 ─────────────────────────────────────
    elif action == "run_critique_2":
        run_critique_round_2(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
        )

    # ── Step 6: Submit Round 2 Reflections ───────────────────────────────
    elif action == "submit_r2":
        responses_snapshot = {}
        frameworks = state.get("frameworks_used_round_2", [])
        
        for idx, fw in enumerate(frameworks):
            key = f"critique_response_r2_{idx}"
            state[key] = request.form.get(key, "")
            responses_snapshot[fw] = state[key]

        if not all(v.strip() for v in responses_snapshot.values()):
            message = "Please fill in all fields (use '-' if no response)."
        else:
            submit_reflections_round_2(
                state=state,
                responses_snapshot=responses_snapshot
            )

    # ── Step 7: Run Critique Round 3 (Optional) ──────────────────────────
    elif action == "run_round_3":
        selected_frameworks = request.form.getlist("selected_frameworks")
        state["user_selected_frameworks"] = selected_frameworks

        if len(selected_frameworks) < 1:
            message = "Please select at least one framework."
        elif len(selected_frameworks) > 3:
            message = "Please select no more than 3 frameworks."
        else:
            run_critique_round_3(
                state=state,
                abstraction_level=state["structured_input"]["abstraction_level"],
                selected_frameworks=selected_frameworks,
            )

    # ── Step 7: Skip Round 3 ─────────────────────────────────────────────
    elif action == "skip_round_3":
        state["done_round_3"] = True
        # derive_current_step will return 10, showing synthesis section

    # ── Step 8: Submit Round 3 Reflections ───────────────────────────────
    elif action == "submit_r3":
        responses_snapshot = {}
        frameworks = state.get("user_selected_frameworks", [])
        
        for idx, fw in enumerate(frameworks):
            key = f"critique_response_r3_{idx}"
            state[key] = request.form.get(key, "")
            responses_snapshot[fw] = state[key]

        if not all(v.strip() for v in responses_snapshot.values()):
            message = "Please fill in all fields (use '-' if no response)."
        else:
            submit_reflections_round_3(
                state=state,
                responses_snapshot=responses_snapshot
            )

    # ── Step 10: Generate Aggregated Critique Summary ────────────────────
    elif action == "run_synthesis":
        run_critique_synthesis(state=state)

    # ── Step 11: Generate Mitigations & Improvements ─────────────────────
    elif action == "run_mitigations":
        run_mitigation_generation(state=state)

    # ── Step 12: Generate Context Prompt ─────────────────────────────────
    elif action == "generate_context_prompt":
        run_context_prompt_generation(state=state)

    # ── Reset App ────────────────────────────────────────────────────────
    elif action == "reset_app":
        state.clear()
        state["current_step"] = 0
        return render_template(
            "index.html",
            state=dict(state._session),
            message=None,
            scroll_to="step-1",
        )

    # ── Derive new step from updated state ───────────────────────────────
    state["current_step"] = derive_current_step(state)
    scroll_to = scroll_target_for(state["current_step"])

    return render_template(
        "index.html",
        state=dict(state._session),
        message=message,
        scroll_to=scroll_to,
    )


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True)