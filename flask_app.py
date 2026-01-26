from flask import Flask, render_template, request, session, redirect, url_for
from state.flask_session_state import FlaskSessionState
from core.utils import extract_questions, get_reframed_understanding
from steps.S03_user_response import context_summary_0


from actions.clarify import run_clarification
from actions.critique_round_1 import run_critique_round_1, submit_reflections_round_1
from actions.critique_round_2 import run_critique_round_2, submit_reflections_round_2

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # replace later


@app.route("/", methods=["GET", "POST"])
def index():
    state = FlaskSessionState(session)
    message = None

    if request.method == "GET":
        state.clear()
        state["current_step"] = 0
        state["current_step"] = 0

    if request.method == "POST":
        step = state.get("current_step", 0)

        # STEP 0 → generate clarification questions
        if step == 0:
            # 1. Store inputs FIRST
            state["problem"] = request.form.get("problem", "")
            state["approach"] = request.form.get("approach", "")
            state["stakeholder"] = request.form.get("stakeholder", "")
            state["constraints"] = request.form.get("constraints", "")
            state["abstraction"] = int(request.form.get("abstraction", 5))

            # 2. Validate
            if not state["problem"] or not state["approach"]:
                message = "Please provide both problem and approach."
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
                    # ✅ BUILD PROMPTS HERE
                    questions = extract_questions(state["clarification_output"])
                    state["clarification_prompts"] = (
                        ["Correct the model's understanding (type '-' if none)"]
                        + questions
                    )

                    state["reframed_understanding"] = get_reframed_understanding(
                        state["clarification_output"]
                    )

                    state["current_step"] = 1


        # STEP 1 → submit clarification answers
        elif step == 1:
            # Store answers FIRST
            for key, value in request.form.items():
                if key.startswith("clarify_answer_"):
                    state[key] = value

            # Validate
            answers = {
                k: state[k] for k in state.keys()
                if k.startswith("clarify_answer_")
            }

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

                # Generate context summary ONCE
                summary = context_summary_0(
                    state["structured_input"],
                    state["clarification_answers"]
                )

                state["context_summary"] = summary
                state["current_step"] = 2


        elif step == 2:
            action = request.form.get("action")

            # Always store edited summary first (important!)
            updated_summary = request.form.get("context_summary", "").strip()
            state["context_summary"] = updated_summary

            if not updated_summary:
                message = "Context summary cannot be empty."
                return render_template("index.html", state=dict(state._session), message=message)

            if action == "update_summary":
                # Stay on step 2
                state["current_step"] = 2

            elif action == "run_critique_1":
                run_critique_round_1(
                    state=state,
                    abstraction_level=state["structured_input"]["abstraction_level"],
                )
                state["current_step"] = 3


        elif step == 3:
            # Store responses FIRST
            responses_snapshot = {}

            frameworks = state.get("frameworks_used_round_1", [])
            for idx, fw in enumerate(frameworks):
                key = f"critique_response_r1_{idx}"
                state[key] = request.form.get(key, "")
                responses_snapshot[fw] = state[key]

            # Validate
            if not all(v.strip() for v in responses_snapshot.values()):
                message = "Please fill in all fields (use '-' if no response)."
            else:
                submit_reflections_round_1(
                    state=state,
                    responses_snapshot=responses_snapshot,
                )
                state["current_step"] = 4

        elif step == 4:
            # user clicked "Run Critique Round 2"
            run_critique_round_2(
                state=state,
                abstraction_level=state["structured_input"]["abstraction_level"],
            )
            state["current_step"] = 5



    return render_template(
        "index.html",
        state=dict(state._session),
        message=message,
    )


@app.route("/reset", methods=["POST"])
def reset():
    state = FlaskSessionState(session)
    state.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
