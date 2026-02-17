from flask import Flask, render_template, request, session, redirect, url_for
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

from flask_session import Session

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # replace later

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "./flask_sessions"


# ---------------------------------------------------------------------------
# Downstream clearing map
# ---------------------------------------------------------------------------
# Transition flag used to bridge the "Continue" action after Round 2:
#   ready_for_r3  — set by submit_r2, cleared by continue_after_r2

_ALL_FLAGS = [
    "ready_for_r3",
]

_ALL_ROUND3 = [
    "user_selected_frameworks", "done_round_3",
    "critique_round_3",
    "critique_response_r3_0", "critique_response_r3_1", "critique_response_r3_2",
    "acknowledgement_round_3",
]

_ALL_DOWNSTREAM = (
    _ALL_ROUND3 + _ALL_FLAGS + [
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ]
)

DOWNSTREAM_KEYS = {
    # ── Wipes everything ──────────────────────────────────────────────────
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
    ] + _ALL_DOWNSTREAM,

    # ── Wipes from context summary onwards ───────────────────────────────
    "update_summary": [
        "clarification_answers", "context_summary",
        "critique_round_1", "frameworks_used_round_1",
        "critique_response_r1_0", "critique_response_r1_1", "critique_response_r1_2",
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _ALL_DOWNSTREAM,

    # ── Wipes from critique round 1 onwards ──────────────────────────────
    "run_critique_1": [
        "critique_round_1", "frameworks_used_round_1",
        "critique_response_r1_0", "critique_response_r1_1", "critique_response_r1_2",
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _ALL_DOWNSTREAM,

    # ── Wipes from round 1 ack onwards ───────────────────────────────────
    "submit_r1": [
        "acknowledgement_round_1",
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _ALL_DOWNSTREAM,

    # ── Wipes from critique round 2 onwards ──────────────────────────────
    "run_critique_2": [
        "critique_round_2", "frameworks_used_round_2",
        "critique_response_r2_0", "critique_response_r2_1", "critique_response_r2_2",
        "acknowledgement_round_2",
    ] + _ALL_DOWNSTREAM,

    # ── Wipes from round 2 ack onwards ───────────────────────────────────
    "submit_r2": [
        "acknowledgement_round_2",
    ] + _ALL_DOWNSTREAM,

    # ── continue_after_r2: clears ready_for_r3 flag only ─────────────────
    "continue_after_r2": ["ready_for_r3"],

    # ── Wipes from round 3 onwards ───────────────────────────────────────
    "run_round_3":  _ALL_ROUND3 + ["ready_for_synthesis", "ready_for_mitigations",
                                    "ready_for_context_prompt",
                                    "critique_synthesis", "mitigation_improvement_output",
                                    "context_prompt"],
    "skip_round_3": _ALL_ROUND3 + ["ready_for_synthesis", "ready_for_mitigations",
                                    "ready_for_context_prompt",
                                    "critique_synthesis", "mitigation_improvement_output",
                                    "context_prompt"],

    # ── Wipes from round 3 ack onwards ───────────────────────────────────
    "submit_r3": [
        "acknowledgement_round_3",
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ],
    "run_synthesis": [
        "critique_synthesis", "mitigation_improvement_output", "context_prompt",
    ],
    "run_mitigations": [
        "mitigation_improvement_output", "context_prompt",
    ],
    "generate_context_prompt": [
        "context_prompt",
    ],
}


def clear_downstream(state, action: str) -> None:
    """Remove all state keys that are stale after re-running `action`."""
    for key in DOWNSTREAM_KEYS.get(action, []):
        state.pop(key, None)


# ---------------------------------------------------------------------------
# Step derivation
# ---------------------------------------------------------------------------
# Maps EXACTLY to the HTML {% if state.current_step >= N %} guards.
# No step is skipped. Every transition is accounted for.
#
# Internal flag drives the Round 2 → Round 3 "Continue" transition:
#   ready_for_r3  → step 6  (submit_r2 done, ack shown, waiting Continue)
#
# HTML guard reference:
#  >= 0  → step-1 (always visible)
#  >= 1  → step-2 clarification questions
#  >= 2  → step-2 context summary
#  >= 3  → step-3 critique round 1
#  >= 4  → step-3 ack + Run Critique Round 2 button
#  >= 5  → step-4 critique round 2
#  >= 6  → step-4 ack + Continue button
#  >= 7  → step-5 framework selector
#  >= 8  → step-5 critique round 3
#  >= 9  → step-5 ack + Continue to Aggregated Summary button
#  >= 10 → step-6 synthesis
#  >= 11 → step-7 mitigations
#  >= 12 → step-8 context prompt
#  >= 13 → step-9 thank you (never set by current flow, kept for future)

def derive_current_step(state) -> int:
    # ── Step 12: context prompt generated ───────────────────────────────
    if state.get("context_prompt"):
        return 12

    # ── Step 12: mitigations done → step-8 auto-appears ─────────────────
    if state.get("mitigation_improvement_output"):
        return 12

    # ── Step 11: synthesis done → step-7 auto-appears ───────────────────
    if state.get("critique_synthesis"):
        return 11

    # ── Step 10: round 3 ack OR skipped → synthesis section appears ─────
    # (ack box renders via {% if state.acknowledgement_round_3 %} guard,
    #  independent of step number, so returning 10 is safe)
    if state.get("acknowledgement_round_3") or state.get("done_round_3"):
        return 10

    # ── Step 8: round 3 output ready ────────────────────────────────────
    if state.get("critique_round_3"):
        return 8

    # ── Step 7: Continue clicked after R2 ack ───────────────────────────
    if state.get("acknowledgement_round_2"):
        return 7

    # ── Step 6: R2 responses submitted, ack shown, waiting Continue ─────
    if state.get("ready_for_r3"):
        return 6

    # ── Step 5: round 2 output ready ────────────────────────────────────
    if state.get("critique_round_2"):
        return 5

    # ── Step 4: round 1 ack shown ───────────────────────────────────────
    if state.get("acknowledgement_round_1"):
        return 4

    # ── Step 3: round 1 output ready ────────────────────────────────────
    if state.get("critique_round_1"):
        return 3

    # ── Step 2: context summary ready ───────────────────────────────────
    if state.get("context_summary"):
        return 2

    # ── Step 1: clarification questions ready ───────────────────────────
    if state.get("clarification_prompts"):
        return 1

    return 0


# ---------------------------------------------------------------------------
# Scroll helpers
# ---------------------------------------------------------------------------

def scroll_target_for(current_step: int) -> str:
    return {
        1:  "step-2-questions",
        2:  "step-2-summary",
        3:  "step-3-critique",
        4:  "step-3-ack",
        5:  "step-4-critique",
        6:  "step-4-ack",
        7:  "step-5-select",
        8:  "step-5-critique",
        9:  "step-5-ack",
        10: "step-6",
        11: "step-7",
        12: "step-8",
    }.get(current_step, "step-1")


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

Session(app)


# ---------------------------------------------------------------------------
# Main route
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    state = FlaskSessionState(session)
    message = None

    # ── GET ─────────────────────────────────────────────────────────────────
    # FIX: Do NOT check current_step (it's 0 on a fresh session, which is
    # falsy and would incorrectly reset a session that's genuinely at step 0).
    # Instead check for any real data key. If none exist, it's a fresh visit.
    if request.method == "GET":
        if not state.get("clarification_prompts") and not state.get("problem"):
            state.clear()
            state["current_step"] = 0
        else:
            # Rehydrate current_step from data in case server restarted
            state["current_step"] = derive_current_step(state)
        return render_template(
            "claude_index.html",
            state=dict(state._session),
            message=None,
            scroll_to=scroll_target_for(state.get("current_step", 0)),
        )

    # ── POST ────────────────────────────────────────────────────────────────
    action = request.form.get("action", "submit_idea")
    print(f"POST action={action!r}  current_step={state.get('current_step')}")

    # Ensure framework list is always available
    if "available_frameworks" not in state:
        all_frameworks = load_frameworks()
        state["available_frameworks"] = [fw["name"] for fw in all_frameworks]

    # Clear stale downstream data before running the action
    clear_downstream(state, action)

    # ── Route by action ─────────────────────────────────────────────────────

    # ------------------------------------------------------------------ #
    # SUBMIT IDEA → generate clarifying questions                         #
    # ------------------------------------------------------------------ #
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
                questions = extract_questions(state["clarification_output"])
                state["clarification_prompts"] = (
                    ["Correct the model's understanding (type '-' if none)"]
                    + questions
                )
                state["reframed_understanding"] = get_reframed_understanding(
                    state["clarification_output"]
                )

    # ------------------------------------------------------------------ #
    # UPDATE SUMMARY                                                       #
    # The HTML "Generate Context Summary" button sends action=update_summary.
    # This handler saves clarification answers AND generates the summary.  #
    # ------------------------------------------------------------------ #
    elif action == "update_summary":
        # Only save answers that were actually submitted in this form.
        # Never overwrite a previously saved answer with an empty string
        # from a different form that doesn't include the clarify fields.
        submitted_answers = {
            key: value
            for key, value in request.form.items()
            if key.startswith("clarify_answer_")
        }
        if submitted_answers:
            for key, value in submitted_answers.items():
                state[key] = value

        # Read answers from state (may include previously saved ones)
        answers = {k: state[k] for k in state.keys() if k.startswith("clarify_answer_")}

        if not all(v.strip() for v in answers.values()):
            message = "Please fill out every field. Use '-' if you have nothing to add."
        else:
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

    # ------------------------------------------------------------------ #
    # RUN CRITIQUE ROUND 1                                                #
    # Triggered by hidden input action="run_critique_1" in the summary    #
    # form. Also accepts any inline edit to context_summary.              #
    # ------------------------------------------------------------------ #
    elif action == "run_critique_1":
        updated_summary = request.form.get("context_summary", "").strip()
        if updated_summary:
            state["context_summary"] = updated_summary

        run_critique_round_1(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
        )

    # ------------------------------------------------------------------ #
    # SUBMIT ROUND 1 REFLECTIONS                                          #
    # ------------------------------------------------------------------ #
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
            submit_reflections_round_1(state=state, responses_snapshot=responses_snapshot)

    # ------------------------------------------------------------------ #
    # RUN CRITIQUE ROUND 2                                                #
    # ------------------------------------------------------------------ #
    elif action == "run_critique_2":
        run_critique_round_2(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
        )

    # ------------------------------------------------------------------ #
    # SUBMIT ROUND 2 REFLECTIONS                                          #
    # Sets ready_for_r3 so derive returns 6, showing the ack box +        #
    # Continue button (HTML guard: current_step >= 6).                    #
    # ------------------------------------------------------------------ #
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
            submit_reflections_round_2(state=state, responses_snapshot=responses_snapshot)
            state["ready_for_r3"] = True

    # ------------------------------------------------------------------ #
    # CONTINUE AFTER ROUND 2                                              #
    # Clears ready_for_r3 flag; acknowledgement_round_2 was already set   #
    # by submit_reflections_round_2, so derive now returns 7.             #
    # ------------------------------------------------------------------ #
    elif action == "continue_after_r2":
        # Safety net: ensure ack exists so derive returns 7 not 5
        if not state.get("acknowledgement_round_2"):
            state["acknowledgement_round_2"] = "—"

    # ------------------------------------------------------------------ #
    # RUN CRITIQUE ROUND 3                                                #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # SKIP CRITIQUE ROUND 3                                               #
    # done_round_3 makes derive return 10 directly (bypasses step 9).     #
    # ------------------------------------------------------------------ #
    elif action == "skip_round_3":
        state["done_round_3"] = True

    # ------------------------------------------------------------------ #
    # SUBMIT ROUND 3 REFLECTIONS                                          #
    # After this, derive returns 9 (ack box visible, Continue button).    #
    # ------------------------------------------------------------------ #
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
            submit_reflections_round_3(state=state, responses_snapshot=responses_snapshot)

    # ------------------------------------------------------------------ #
    # CONTINUE TO SYNTHESIS                                               #
    # Sets ready_for_synthesis → derive returns 10 → step-6 visible.     #
    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # RUN SYNTHESIS                                                       #
    # After this derive returns 11 — step-7 mitigations auto-appears.   #
    # ------------------------------------------------------------------ #
    elif action == "run_synthesis":
        run_critique_synthesis(state=state)

    # ------------------------------------------------------------------ #
    # RUN MITIGATIONS                                                     #
    # After this derive returns 12 — step-8 context prompt auto-appears. #
    # ------------------------------------------------------------------ #
    elif action == "run_mitigations":
        run_mitigation_generation(state=state)

    # ------------------------------------------------------------------ #
    # GENERATE CONTEXT PROMPT                                             #
    # ------------------------------------------------------------------ #
    elif action == "generate_context_prompt":
        run_context_prompt_generation(state=state)

    # ------------------------------------------------------------------ #
    # RESET                                                               #
    # ------------------------------------------------------------------ #
    elif action == "reset_app":
        state.clear()
        state["current_step"] = 0
        return render_template(
            "claude_index.html",
            state=dict(state._session),
            message=None,
            scroll_to="step-1",
        )

    # ── Derive step from what data actually exists in state ──────────────
    state["current_step"] = derive_current_step(state)
    scroll_to = scroll_target_for(state["current_step"])

    return render_template(
        "claude_index.html",
        state=dict(state._session),
        message=message,
        scroll_to=scroll_to,
    )


# ---------------------------------------------------------------------------
# Reset route (legacy redirect safety net)
# ---------------------------------------------------------------------------

@app.route("/reset", methods=["POST"])
def reset():
    state = FlaskSessionState(session)
    state.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)