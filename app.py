# =============================================================================
# Imports
# =============================================================================
import streamlit as st
import html

from core.utils import format_user_responses_to_critique, load_frameworks, extract_framework_names, get_reframed_understanding

from steps.S01_input import format_user_input
from steps.S02_clarify import clarification_prompt, generate_clarification
from steps.S03_user_response import extract_questions, context_summary_0
from steps.S04_critique_1 import critique_1
from steps.S05_user_reflect_1 import context_summary_1
from steps.S06_critique_2 import critique_round_2
from steps.S07_user_reflect_2 import context_summary_2
from steps.S08_critique_3 import critique_round_3
from steps.S09_user_reflect_3 import context_summary_3
from steps.S10_critique_synthesis import critique_synthesis
from steps.S11_mitigations import mitigation_improvement_suggestions

from ui.styles import apply_styles
from ui.layout import wrap_lines, label_height_em


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

    for key in list(st.session_state.keys()):
        if key not in allowed:
            del st.session_state[key]


# =============================================================================
# Sidebar – progress & navigation
# =============================================================================

def is_done(key: str) -> bool:
    return key in st.session_state and st.session_state[key] not in (None, "", {})

steps = [
    ("Step 0 — Submit Idea", "step-0", True),
    ("Step 1 — Clarify", "step-1", "formatted_input" in st.session_state),
    ("Step 2 — Critique 1", "step-2", "user_responses_round_1" in st.session_state),
    ("Step 3 — Critique 2", "step-3", "user_responses_round_2" in st.session_state),
    ("Step 4 — Critique 3", "step-4", "done_round_3" in st.session_state),
    ("Step 5 — Synthesis", "step-5", "critique_synthesis" in st.session_state),
    ("Step 6 — Mitigations", "step-6", "mitigation_improvement_output" in st.session_state),
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
    if not problem or not approach:
        st.warning("Please provide both problem and approach.")
    else:
        reset_to_layer(0)

        structured = format_user_input(
            problem, approach, stakeholder, constraints, abstraction
        )

        st.session_state["structured_input"] = structured
        st.session_state["formatted_input"] = structured["full_input"]

        prompt = clarification_prompt(structured["full_input"])

        with st.spinner("Generating clarifying questions..."):
            st.session_state["clarification_output"] = generate_clarification(prompt)

# Display clarification output once generated (no regeneration on reruns)
if "clarification_output" in st.session_state:
    st.markdown('<div id="step-1"></div>', unsafe_allow_html=True)
    st.header("1. Clarify the Idea")
    st.markdown("### Clarification Output")
    st.markdown(get_reframed_understanding(st.session_state["clarification_output"]))

# =============================================================================
# STEP 1.1 — User Answers Clarification Questions
# =============================================================================
if "clarification_output" in st.session_state:
    st.header("Your Clarification Responses")

    questions = extract_questions(st.session_state["clarification_output"])

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
            f"clarify_answer_{i}": st.session_state.get(f"clarify_answer_{i}", "")
            for i in range(len(clarification_prompts))
        }

        # VALIDATE using snapshot
        all_filled = all(v.strip() != "" for v in answers_snapshot.values())

        if not all_filled:
            st.warning("Please fill out every field. Use '-' if you have nothing to add.")
            st.stop()

        reset_to_layer(1)

        # WRITE layer-owned state
        st.session_state["clarification_answers"] = {
            "llm_understanding_correction": answers_snapshot["clarify_answer_0"],
            "clarifying_answers": {
                q: answers_snapshot[f"clarify_answer_{idx + 1}"]
                for idx, q in enumerate(questions)
            }
        }

        with st.spinner("Generating context summary..."):
            summary = context_summary_0(
                st.session_state["structured_input"],
                st.session_state["clarification_answers"]
            )

        st.session_state["context_summary"] = summary


if st.session_state.get("context_summary"):
    st.subheader("📘 Updated Context Summary")
    # User can edit this to correct phrasing or emphasis before critique begins
    updated = st.text_area(
        "Review or edit the summary below before continuing:",
        st.session_state["context_summary"],
        height=250
    )
    if updated != st.session_state["context_summary"]:
        reset_to_layer(2)
        st.session_state["context_summary"] = updated

    st.divider()


# =============================================================================
# STEP 2 — Critique Round 1
# =============================================================================
if "context_summary" in st.session_state:

    # --------------------------------------------------
    # TRIGGER: Run critique
    # --------------------------------------------------
    if st.button("Run Critique Round 1"):
        reset_to_layer(3)

        with st.spinner("Running critique round 1..."):
            critique_output = critique_1(
                st.session_state["context_summary"],
                st.session_state["structured_input"]["abstraction_level"]
            )

        st.session_state["critique_round_1"] = critique_output
        st.session_state["frameworks_used_round_1"] = extract_framework_names(critique_output)

    # --------------------------------------------------
    # DISPLAY CRITIQUE + FORM (STATE-DRIVEN)
    # --------------------------------------------------
    if "critique_round_1" in st.session_state:

        left, right = st.columns([1.2, 1], gap="large")

        with left:
            st.markdown("### Critique (Round 1)")
            st.markdown(st.session_state["critique_round_1"])

        with right:
            st.markdown("### Your Responses (Round 1)")
            st.markdown("Respond to each framework (type '-' if none).")

            frameworks = st.session_state.get("frameworks_used_round_1", [])

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
                    fw: st.session_state.get(f"critique_response_r1_{idx}", "")
                    for idx, fw in enumerate(frameworks)
                }

                if not all(v.strip() for v in responses_snapshot.values()):
                    st.warning("Please fill in all fields (use '-' if no response).")
                    st.stop()

                reset_to_layer(4)

                formatted = format_user_responses_to_critique(responses_snapshot)
                st.session_state["user_responses_round_1"] = formatted

                with st.spinner("Updating context summary..."):
                    updated = context_summary_1(
                        st.session_state["context_summary"],
                        st.session_state["critique_round_1"],
                        formatted
                    )

                new_context = updated.split("UPDATED CONTEXT SUMMARY:")[-1].strip()
                acknowledgement_text = (
                            updated
                            .split("ACKNOWLEDGEMENT:")[1]
                            .split("UPDATED CONTEXT SUMMARY:")[0]
                            .strip()
                        )
                
                st.session_state["acknowledgement_round_1"] = acknowledgement_text
                st.session_state["context_summary"] = new_context

                st.success("Your reflections have been recorded.")
                            
            # --------------------------------------------------
            # ACK / CONFIRMATION (SAFE ON RERUN)
            # --------------------------------------------------
            if "acknowledgement_round_1" in st.session_state:
                st.subheader("Context Update Acknowledgement (Round 1)")
                st.info(st.session_state["acknowledgement_round_1"])
        st.divider()



# =============================================================================
# STEP 3 — Critique Round 2
# =============================================================================
if "user_responses_round_1" in st.session_state:

    # --- Run critique only when button is clicked ---
    if st.button("Run Critique Round 2"):
        reset_to_layer(5)  # keep state up to reflections from round 1

        with st.spinner("Running critique round 2..."):
            critique_output = critique_round_2(
                st.session_state["context_summary"],
                st.session_state["structured_input"]["abstraction_level"],
                st.session_state["frameworks_used_round_1"]
            )

        st.session_state["critique_round_2"] = critique_output
        st.session_state["frameworks_used_round_2"] = extract_framework_names(critique_output)


    # --- Display critique if it exists ---
    if "critique_round_2" in st.session_state:

        left, right = st.columns([1.2, 1], gap="large")

        with left:
            st.markdown("### Critique (Round 2)")
            st.markdown(st.session_state["critique_round_2"])

        with right:
            st.markdown("### Your Responses (Round 2)")

            frameworks_used_round_2 = st.session_state.get("frameworks_used_round_2", [])

            with st.form("critique_response_form_round_2"):
                for idx, fw in enumerate(frameworks_used_round_2):
                    st.text_area(
                        f"💬 {fw}",
                        key=f"critique_response_r2_{idx}",
                        height=200
                    )

                submitted_r2 = st.form_submit_button("Submit Your Reflections (Round 2)")

            # --------------------------------------------------
            # HANDLE SUBMISSION (CORRECT ORDER)
            # --------------------------------------------------
            if submitted_r2:
                # SNAPSHOT widget values FIRST
                responses_snapshot = {
                    fw: st.session_state.get(f"critique_response_r2_{idx}", "")
                    for idx, fw in enumerate(frameworks_used_round_2)
                }

                # VALIDATE snapshot
                all_filled = all(v.strip() != "" for v in responses_snapshot.values())
                if not all_filled:
                    st.warning("Please complete all fields (use '-' if no response).")
                    st.stop()

    
                reset_to_layer(6)

                # WRITE layer-owned state
                formatted_response_r2 = format_user_responses_to_critique(responses_snapshot)
                st.session_state["user_responses_round_2"] = formatted_response_r2

                with st.spinner("Updating context summary after round 2..."):
                    updated_summary_r2 = context_summary_2(
                        st.session_state["context_summary"],
                        st.session_state["critique_round_2"],
                        st.session_state["user_responses_round_2"]["full_response_input"]
                    )

                if "UPDATED CONTEXT SUMMARY:" in updated_summary_r2 and "ACKNOWLEDGEMENT:" in updated_summary_r2:
                    acknowledgement_text_r2 = (
                        updated_summary_r2
                        .split("ACKNOWLEDGEMENT:")[1]
                        .split("UPDATED CONTEXT SUMMARY:")[0]
                        .strip()
                    )
                    new_context_r2 = (
                        updated_summary_r2
                        .split("UPDATED CONTEXT SUMMARY:")[1]
                        .strip()
                    )

                    st.session_state["acknowledgement_round_2"] = acknowledgement_text_r2

                    st.session_state["context_summary"] = new_context_r2

                    st.success("Reflections recorded and context updated (Round 2).")
                    
                else:
                    acknowledgement_text_r2 = "Format issue in LLM output."
                    new_context_r2 = updated_summary_r2.strip()

            if "acknowledgement_round_2" in st.session_state:
                st.subheader("Context Update Acknowledgement (Round 2)")
                st.info(st.session_state["acknowledgement_round_2"])
        st.divider()

# =============================================================================
# STEP 4 — Critique Round 3
# =============================================================================
if "user_responses_round_2" in st.session_state:
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
    with st.spinner("Running critique round 3..."):
        if submitted_frameworks:
            # SNAPSHOT
            selected_snapshot = list(selected_frameworks)

            # VALIDATE
            if len(selected_snapshot) < 1:
                st.warning("Please select at least one framework.")
                st.stop()
            if len(selected_snapshot) > 3:
                st.warning("Please select no more than 3 frameworks.")
                st.stop()

            # RESET
            reset_to_layer(7)  # keep state up to reflections from round 2

            # WRITE
            critique3 = critique_round_3(
                st.session_state["context_summary"],
                st.session_state["structured_input"]["abstraction_level"],
                selected_snapshot
            )

            st.session_state["critique_round_3"] = critique3
            st.session_state["user_selected_frameworks"] = selected_snapshot

    # --------------------------------------------------
    # SKIP FINAL CRITIQUE
    # --------------------------------------------------
    st.markdown("---")
    if not st.session_state.get("skipped_round_3", False):
        if st.button("🚀 Skip Final Critique – Go to Aggregated Summary"):
            reset_to_layer(7)
            st.session_state["done_round_3"] = True



# --------------------------------------------------
# DISPLAY CRITIQUE ROUND 3
# --------------------------------------------------
if "critique_round_3" in st.session_state:

    st.markdown('<div id="step-4"></div>', unsafe_allow_html=True)
    st.header("4. Critique Round 3")

    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown("### Critique Output (Round 3)")
        st.markdown(st.session_state["critique_round_3"])

    with right:
        st.markdown("### Your Responses (Round 3)")

        frameworks_used_round_3 = st.session_state.get("user_selected_frameworks", [])

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
                fw: st.session_state.get(f"critique_response_r3_{idx}", "")
                for idx, fw in enumerate(frameworks_used_round_3)
            }

            # VALIDATE
            if not all(v.strip() != "" for v in responses_snapshot.values()):
                st.warning("Please fill in all fields (use '-' if no response).")
                st.stop()


            reset_to_layer(8)

            # WRITE USER RESPONSES
            formatted_response_r3 = format_user_responses_to_critique(responses_snapshot)
            st.session_state["user_responses_round_3"] = formatted_response_r3

            # ✅ CONTEXT UPDATE — RUN ONCE, RIGHT HERE
            with st.spinner("Generating context summary..."):
                updated_summary_r3 = context_summary_3(
                    st.session_state["context_summary"],
                    st.session_state["critique_round_3"],
                    formatted_response_r3["full_response_input"]
                )

            if "UPDATED CONTEXT SUMMARY:" in updated_summary_r3 and "ACKNOWLEDGEMENT:" in updated_summary_r3:
                acknowledgement_text_r3 = (
                    updated_summary_r3
                    .split("ACKNOWLEDGEMENT:")[1]
                    .split("UPDATED CONTEXT SUMMARY:")[0]
                    .strip()
                )
                new_context_r3 = (
                    updated_summary_r3
                    .split("UPDATED CONTEXT SUMMARY:")[1]
                    .strip()
                )

                st.session_state["acknowledgement_round_3"] = acknowledgement_text_r3

                st.session_state["context_summary"] = new_context_r3

                st.session_state["done_round_3"] = True
            else:
                acknowledgement_text_r3 = "Format issue in LLM output."
                new_context_r3 = updated_summary_r3.strip()

        if "acknowledgement_round_3" in st.session_state:
            st.subheader("Context Update Acknowledgement (Round 3)")
            st.info(st.session_state["acknowledgement_round_3"])
    st.divider()

# =============================================================================
# STEP 5
# =============================================================================
if "done_round_3" in st.session_state:
    st.markdown('<div id="step-5"></div>', unsafe_allow_html=True)
    st.header("5. Aggregated Critique Summary & Criticality Ranking")

    st.markdown(
        "Now that you've reflected on all critique rounds, this step will "
        "summarize and prioritize the critique feedback."
    )

    # Explicit user trigger to avoid accidental regeneration
    if st.button("Generate Aggregated Critique Summary"):
        reset_to_layer(9)
        # Combine all critique outputs across rounds into one input
        all_critiques = ""
        for key in ["critique_round_1", "critique_round_2", "critique_round_3"]:
            if key in st.session_state:
                all_critiques += f"\n---\n{st.session_state[key]}"

        # Combine all user reflections into a single structured input
        all_user_reflections = ""
        for key in ["user_responses_round_1", "user_responses_round_2", "user_responses_round_3"]:
            if key in st.session_state:
                # Use the formatted string for reflections
                all_user_reflections += (
                    f"\n---\n{st.session_state[key]['full_response_input']}"
                )

        # Generate a consolidated critique with severity / criticality ranking
        with st.spinner("Synthesizing critique across rounds..."):
            aggregated_output = critique_synthesis(
                st.session_state["context_summary"],
                all_critiques,
                all_user_reflections,
            )

        st.session_state["critique_synthesis"] = aggregated_output

    # Display synthesis once generated
    if "critique_synthesis" in st.session_state:
        st.markdown("### 🧠 Aggregated Critique Summary (with Criticality)")
        st.markdown(st.session_state["critique_synthesis"])
    st.divider()
# ------------------------------------------------------------------------------------------------
# Step 11

if "critique_synthesis" in st.session_state:
    st.markdown('<div id="step-6"></div>', unsafe_allow_html=True)
    st.header("6. Mitigation & Improvement Ideas")

    # User-triggered to prevent unnecessary LLM calls
    if st.button("Generate Mitigations & Improvements"):
        reset_to_layer(10)
        # Prepare combined reflections
        all_user_reflections = ""
        for key in ["user_responses_round_1", "user_responses_round_2", "user_responses_round_3"]:
            if key in st.session_state:
                all_user_reflections += (
                    f"\n---\n{st.session_state[key]['full_response_input']}"
                )
        with st.spinner("Generating mitigations & improvements..."):
            mitigation_output = mitigation_improvement_suggestions(
                st.session_state["context_summary"],
                st.session_state["critique_synthesis"],
                all_user_reflections,
                st.session_state["structured_input"]["abstraction_level"],
            )
        st.session_state["mitigation_improvement_output"] = mitigation_output

    # Display mitigation ideas once generated
    if "mitigation_improvement_output" in st.session_state:
        st.markdown("### 🛠️ Mitigations & Improvement Ideas")
        st.markdown(st.session_state["mitigation_improvement_output"])
