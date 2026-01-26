# =============================================================================
# Imports
# =============================================================================
import streamlit as st
import html

from state.session_state import SessionState

# Actions
from actions.clarify import run_clarification
from actions.critique_round_1 import run_critique_round_1, submit_reflections_round_1
from actions.critique_round_2 import run_critique_round_2, submit_reflections_round_2
from actions.critique_round_3 import run_critique_round_3, submit_reflections_round_3
from actions.synthesis import run_critique_synthesis
from actions.mitigation import run_mitigation_generation

from steps.S03_user_response import extract_questions, context_summary_0

from core.utils import load_frameworks, get_reframed_understanding

from ui.styles import apply_styles
from ui.layout import wrap_lines, label_height_em

state = SessionState(st.session_state)

# =============================================================================
# App configuration & global styles
# =============================================================================
st.set_page_config(
    page_title="Reinventor",
    page_icon="reinventor.png",
    initial_sidebar_state="expanded",
    layout="wide"
)

apply_styles()


st.image(
    "reinventor.png",
    width=120,
)
st.title("ReInventor")
st.caption("Stress-test your idea through structured critique rounds, then synthesize mitigations.")
st.caption("Remember: YOU are in driver seat, I am just your tool.")

st.divider()


# =============================================================================
# Helper Functions
# =============================================================================

STEP_STATE_KEYS = {
    # ---------------------------------------------------------------------
    # L0 — STEP 0: Raw Idea Input

    0: {
        "problem",
        "approach",
        "stakeholder",
        "constraints",
        "abstraction",
    },

    # ---------------------------------------------------------------------
    # L1 — STEP 1: Generate Clarifying Questions
    1: {
        "structured_input",
        "formatted_input",
        "clarification_output",
    },

    # ---------------------------------------------------------------------
    # L2 — STEP 1.1: User Answers Clarification Questions
    2: {
        "clarification_answers",
        *{f"clarify_answer_{i}" for i in range(6)},
        "context_summary",
    },

    # ---------------------------------------------------------------------
    # L3 — STEP 1.2: User Manually Edits Context Summary
    3: {
        "context_summary",
    },

    # ---------------------------------------------------------------------
    # L4 — STEP 2: Critique Round 1 (LLM)
    4: {
        "critique_round_1",
        "frameworks_used_round_1",
    },

    # ---------------------------------------------------------------------
    # L5 — STEP 2.1: User Reflections on Critique Round 1
    5: {
        *{f"critique_response_r1_{i}" for i in range(10)},
        "user_responses_round_1",
        "context_summary",
        "acknowledgement_round_1",
    },

    # ---------------------------------------------------------------------
    # L6 — STEP 3: Critique Round 2 (LLM)
    6: {
        "critique_round_2",
        "frameworks_used_round_2",
    },

    # ---------------------------------------------------------------------
    # L7 — STEP 3.1: User Reflections on Critique Round 2
    # Action: User responds to second critique → context updated again
    7: {
        *{f"critique_response_r2_{i}" for i in range(10)},
        "user_responses_round_2",
        "context_summary",
        "acknowledgement_round_2",
    },

    # ---------------------------------------------------------------------
    # L8 — STEP 4: Critique Round 3 (Optional, LLM)
    8: {
        "user_selected_frameworks",
        "critique_round_3",
    },

    # ---------------------------------------------------------------------
    # L9 — STEP 4.1: User Reflections on Critique Round 3
    9: {
        *{f"critique_response_r3_{i}" for i in range(5)},
        "user_responses_round_3",
        "context_summary",
        "done_round_3",
        "acknowledgement_round_3",
    },

    # ---------------------------------------------------------------------
    # L10 — STEP 5: Aggregated Critique Synthesis
    10: {
        "critique_synthesis",
    },

    # ---------------------------------------------------------------------
    # L11 — STEP 6: Mitigations & Improvement Ideas
    11: {
        "mitigation_improvement_output",
    },

    # ---------------------------------------------------------------------
    # L12 — STEP 4 (Branch): Skip Final Critique
    12: {
        "skipped_round_3",
    },
}

GLOBAL_STATE_KEYS = set()

def allowed_keys_up_to(step: int) -> set[str]:
    allowed = set()
    for s in range(step + 1):
        allowed |= STEP_STATE_KEYS.get(s, set())
    return allowed

def reset_to_layer(step: int) -> None:
    allowed = allowed_keys_up_to(step) | GLOBAL_STATE_KEYS
    state.clear_except(allowed)



# =============================================================================
# Sidebar – progress & navigation
# =============================================================================

def is_done(key: str) -> bool:
    return key in state and state[key] not in (None, "", {})

steps = [
    ("Step 0 — Submit Idea", "step-0", True),
    ("Step 1 — Clarify", "step-1", "formatted_input" in state),
    ("Step 2 — Critique 1", "step-2", "user_responses_round_1" in state),
    ("Step 3 — Critique 2", "step-3", "user_responses_round_2" in state),
    ("Step 4 — Critique 3", "step-4", "done_round_3" in state),
    ("Step 5 — Synthesis", "step-5", "critique_synthesis" in state),
    ("Step 6 — Mitigations", "step-6", "mitigation_improvement_output" in state),
]

done_count = sum(1 for _, _, done in steps if done)
progress = done_count / len(steps)

with st.sidebar:
    st.markdown("## Steps")
    st.progress(progress, text=f"Progress: {done_count}/{len(steps)}")

    for label, anchor, done in steps:
        icon = "✅" if done else "⬜"
        # links jump to anchors on the page
        st.markdown(f"{icon} <a href='#{anchor}'>{label}</a>", unsafe_allow_html=True)


# =============================================================================
# STEP 0 — Submit Idea
# =============================================================================

st.markdown('<div id="step-0"></div>', unsafe_allow_html=True)
st.header("Submit Your Idea")

c1, c2 = st.columns(2, gap="large")
with c1:
    problem = st.text_area("Problem", height=220)
with c2:
    approach = st.text_area("Proposed Approach", height=220)

c3, c4 = st.columns(2, gap="large")
with c3:
    stakeholder = st.text_input("Primary stakeholder")
    abstraction = st.slider("Critique abstraction level", 0, 10, 5)

with c4:
    constraints = st.text_area("Constraints / non-negotiables", height=120)

# =============================================================================
# STEP 1 — Clarification
# =============================================================================

if st.button("Generate Clarifying Questions"):
    result = run_clarification(
        state=state,
        problem=problem,
        approach=approach,
        stakeholder=stakeholder,
        constraints=constraints,
        abstraction=abstraction,
    )

    if "error" in result:
        st.warning(result["error"])

# Display clarification output once generated (no regeneration on reruns)
if "clarification_output" in state:
    st.markdown('<div id="step-1"></div>', unsafe_allow_html=True)
    st.header("1. Clarify the Idea")
    st.markdown("### Clarification Output")
    st.markdown(get_reframed_understanding(state["clarification_output"]))

# =============================================================================
# STEP 1.1 — User Answers Clarification Questions
# =============================================================================
if "clarification_output" in state:
    st.header("Your Clarification Responses")

    questions = extract_questions(state["clarification_output"])

    # Build a unified list of 6 prompts
    clarification_prompts = [
        "Correct the model's understanding (type '-' if none)"
    ] + questions

    with st.form("clarification_form"):
        left_col, right_col = st.columns(2, gap="large")

        answers = {}

        # Split into 2 columns of 3 prompts each
        left_prompts = clarification_prompts[:3]
        right_prompts = clarification_prompts[3:6]

        for row in range(3):
            lp = left_prompts[row] if row < len(left_prompts) else ""
            rp = right_prompts[row] if row < len(right_prompts) else ""

            # Wrap both prompts
            lp_lines = wrap_lines(lp, width=52)
            rp_lines = wrap_lines(rp, width=52)

            # Max lines in this row determines BOTH label heights
            max_lines = max(len(lp_lines), len(rp_lines))
            h_em = label_height_em(max_lines)

            # Render row: left + right
            lc, rc = st.columns(2, gap="large")

            with lc:
                safe_lp = html.escape(lp, quote=True)
                lp_text = html.escape("\n".join(lp_lines), quote=True)
                st.markdown(
                    f'<div class="fixed-label" style="height:{h_em}em" title="{safe_lp}">{lp_text}</div>',
                    unsafe_allow_html=True
                )
                answers[lp] = st.text_area(
                    " ",
                    key=f"clarify_answer_{row}",
                    height=140,
                    label_visibility="collapsed",
                )

            with rc:
                safe_rp = html.escape(rp, quote=True)
                rp_text = html.escape("\n".join(rp_lines), quote=True)
                st.markdown(
                    f'<div class="fixed-label" style="height:{h_em}em" title="{safe_rp}">{rp_text}</div>',
                    unsafe_allow_html=True
                )
                answers[rp] = st.text_area(
                    " ",
                    key=f"clarify_answer_{row+3}",
                    height=140,
                    label_visibility="collapsed",
                )



        submitted = st.form_submit_button("Generate Context Summary")

    if submitted:
        # SNAPSHOT widget values FIRST
        answers_snapshot = {
            f"clarify_answer_{i}": state.get(f"clarify_answer_{i}", "")
            for i in range(len(clarification_prompts))
        }

        # VALIDATE using snapshot
        all_filled = all(v.strip() != "" for v in answers_snapshot.values())

        if not all_filled:
            st.warning("Please fill out every field. Use '-' if you have nothing to add.")
            st.stop()

        reset_to_layer(1)

        # WRITE layer-owned state
        state["clarification_answers"] = {
            "llm_understanding_correction": answers_snapshot["clarify_answer_0"],
            "clarifying_answers": {
                q: answers_snapshot[f"clarify_answer_{idx + 1}"]
                for idx, q in enumerate(questions)
            }
        }

        with st.spinner("Generating context summary..."):
            summary = context_summary_0(
                state["structured_input"],
                state["clarification_answers"]
            )

        state["context_summary"] = summary


if state.get("context_summary"):
    st.subheader("📘 Updated Context Summary")
    # User can edit this to correct phrasing or emphasis before critique begins
    updated = st.text_area(
        "Review or edit the summary below before continuing:",
        state["context_summary"],
        height=250
    )
    if updated != state["context_summary"]:
        reset_to_layer(2)
        state["context_summary"] = updated

    st.divider()


# =============================================================================
# STEP 2 — Critique Round 1
# =============================================================================
if "context_summary" in state:

    if st.button("Run Critique Round 1"):
        run_critique_round_1(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
        )

    # --------------------------------------------------
    # DISPLAY CRITIQUE + FORM (STATE-DRIVEN)
    # --------------------------------------------------
    if "critique_round_1" in state:

        left, right = st.columns([1.2, 1], gap="large")

        with left:
            st.markdown("### Critique (Round 1)")
            st.markdown(state["critique_round_1"])

        with right:
            st.markdown("### Your Responses (Round 1)")
            st.markdown("Respond to each framework (type '-' if none).")

            frameworks = state.get("frameworks_used_round_1", [])

            with st.form("critique_response_form_round_1"):
                for idx, fw in enumerate(frameworks):
                    st.text_area(
                        f"💬 {fw}",
                        key=f"critique_response_r1_{idx}",
                        height=200
                    )

                submitted_r1 = st.form_submit_button("Submit Your Reflections")


            # --------------------------------------------------
            # HANDLE SUBMISSION (RUNS ON RERUN)
            # --------------------------------------------------
            if submitted_r1:
                responses_snapshot = {
                    fw: state.get(f"critique_response_r1_{idx}", "")
                    for idx, fw in enumerate(frameworks)
                }

                if not all(v.strip() for v in responses_snapshot.values()):
                    st.warning("Please fill in all fields (use '-' if no response).")
                    st.stop()

                submit_reflections_round_1(
                    state=state,
                    responses_snapshot=responses_snapshot,
                )

                st.success("Your reflections have been recorded.")

                            
            # --------------------------------------------------
            # ACK / CONFIRMATION (SAFE ON RERUN)
            # --------------------------------------------------
            if "acknowledgement_round_1" in state:
                st.subheader("Context Update Acknowledgement (Round 1)")
                st.info(state["acknowledgement_round_1"])
        st.divider()

# =============================================================================
# STEP 3 — Critique Round 2
# =============================================================================
if "user_responses_round_1" in state:

    # --- Run critique only when button is clicked ---
    if st.button("Run Critique Round 2"):
        run_critique_round_2(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
        )

    # --- Display critique if it exists ---
    if "critique_round_2" in state:

        left, right = st.columns([1.2, 1], gap="large")

        with left:
            st.markdown("### Critique (Round 2)")
            st.markdown(state["critique_round_2"])

        with right:
            st.markdown("### Your Responses (Round 2)")

            frameworks_used_round_2 = state.get("frameworks_used_round_2", [])

            with st.form("critique_response_form_round_2"):
                for idx, fw in enumerate(frameworks_used_round_2):
                    st.text_area(
                        f"💬 {fw}",
                        key=f"critique_response_r2_{idx}",
                        height=200
                    )

                submitted_r2 = st.form_submit_button("Submit Your Reflections (Round 2)")

            # --------------------------------------------------
            # HANDLE SUBMISSION (THIN UI LAYER)
            # --------------------------------------------------
            if submitted_r2:
                responses_snapshot = {
                    fw: state.get(f"critique_response_r2_{idx}", "")
                    for idx, fw in enumerate(frameworks_used_round_2)
                }

                if not all(v.strip() for v in responses_snapshot.values()):
                    st.warning("Please complete all fields (use '-' if no response).")
                    st.stop()

                submit_reflections_round_2(
                    state=state,
                    responses_snapshot=responses_snapshot,
                )

                st.success("Reflections recorded and context updated (Round 2).")

            if "acknowledgement_round_2" in state:
                st.subheader("Context Update Acknowledgement (Round 2)")
                st.info(state["acknowledgement_round_2"])

        st.divider()

# =============================================================================
# STEP 4 — Critique Round 3
# =============================================================================
if "user_responses_round_2" in state:
    st.header("4. Optional — Critique Round 3")
    st.markdown("Select frameworks for a final optional critique round:")

    # Load available frameworks
    all_frameworks = load_frameworks()
    available_framework_names = [fw["name"] for fw in all_frameworks]

    # --------------------------------------------------
    # FRAMEWORK SELECTION (SNAPSHOT → VALIDATE → RESET)
    # --------------------------------------------------
    with st.form("framework_selection_round_3"):
        selected_frameworks = st.multiselect(
            "Choose 1 to 3 frameworks for critique:",
            available_framework_names
        )
        submitted_frameworks = st.form_submit_button("Run Critique Round 3")
    
    if submitted_frameworks:
        selected_snapshot = list(selected_frameworks)

        if len(selected_snapshot) < 1:
            st.warning("Please select at least one framework.")
            st.stop()
        if len(selected_snapshot) > 3:
            st.warning("Please select no more than 3 frameworks.")
            st.stop()

        run_critique_round_3(
            state=state,
            abstraction_level=state["structured_input"]["abstraction_level"],
            selected_frameworks=selected_snapshot,
        )
        
    # --------------------------------------------------
    # SKIP FINAL CRITIQUE
    # --------------------------------------------------
    st.markdown("---")
    if not state.get("skipped_round_3", False):
        if st.button("🚀 Skip Final Critique – Go to Aggregated Summary"):
            reset_to_layer(7)
            state["done_round_3"] = True


# --------------------------------------------------
# DISPLAY CRITIQUE ROUND 3
# --------------------------------------------------
if "critique_round_3" in state:

    st.markdown('<div id="step-4"></div>', unsafe_allow_html=True)
    st.header("4. Critique Round 3")

    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown("### Critique Output (Round 3)")
        st.markdown(state["critique_round_3"])

    with right:
        st.markdown("### Your Responses (Round 3)")

        frameworks_used_round_3 = state.get("user_selected_frameworks", [])

        with st.form("critique_response_form_round_3"):
            for idx, fw in enumerate(frameworks_used_round_3):
                st.text_area(
                    f"💬 {fw}",
                    key=f"critique_response_r3_{idx}",
                    height=200
                )

            submitted_r3 = st.form_submit_button("Submit Reflections (Round 3)")

        # --------------------------------------------------
        # HANDLE SUBMISSION (CORRECT ORDER)
        # --------------------------------------------------
        if submitted_r3:
            # SNAPSHOT
            responses_snapshot = {
                fw: state.get(f"critique_response_r3_{idx}", "")
                for idx, fw in enumerate(frameworks_used_round_3)
            }

            # VALIDATE
            if not all(v.strip() != "" for v in responses_snapshot.values()):
                st.warning("Please fill in all fields (use '-' if no response).")
                st.stop()

            submit_reflections_round_3(
                state=state,
                responses_snapshot=responses_snapshot,
            )

            st.success("Reflections recorded and context updated (Round 3).")


        if "acknowledgement_round_3" in state:
            st.subheader("Context Update Acknowledgement (Round 3)")
            st.info(state["acknowledgement_round_3"])
    st.divider()

# =============================================================================
# STEP 5
# =============================================================================
if "done_round_3" in state:
    st.markdown('<div id="step-5"></div>', unsafe_allow_html=True)
    st.header("5. Aggregated Critique Summary & Criticality Ranking")

    st.markdown(
        "Now that you've reflected on all critique rounds, this step will "
        "summarize and prioritize the critique feedback."
    )

    if st.button("Generate Aggregated Critique Summary"):
        run_critique_synthesis(state=state)

    if "critique_synthesis" in state:
        st.markdown("### 🧠 Aggregated Critique Summary (with Criticality)")
        st.markdown(state["critique_synthesis"])

    st.divider()
# ------------------------------------------------------------------------------------------------
# Step 11

if "critique_synthesis" in state:
    st.markdown('<div id="step-6"></div>', unsafe_allow_html=True)
    st.header("6. Mitigation & Improvement Ideas")

    if st.button("Generate Mitigations & Improvements"):
        run_mitigation_generation(state=state)

    if "mitigation_improvement_output" in state:
        st.markdown("### 🛠️ Mitigations & Improvement Ideas")
        st.markdown(state["mitigation_improvement_output"])