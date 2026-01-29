from flask import Flask, render_template, request, session, redirect, url_for
from state.flask_session_state import FlaskSessionState
from core.utils import extract_questions, get_reframed_understanding, load_frameworks
from steps.S03_user_response import context_summary_0


from actions.clarify import run_clarification
from actions.critique_round_1 import run_critique_round_1, submit_reflections_round_1
from actions.critique_round_2 import run_critique_round_2, submit_reflections_round_2
from actions.critique_round_3 import run_critique_round_3, submit_reflections_round_3
from actions.synthesis import run_critique_synthesis

from flask_session import Session

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # replace later

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "./flask_sessions"

Session(app)

@app.route("/", methods=["GET", "POST"])
def index():
    state = FlaskSessionState(session)
    message = None

    if request.method == "GET":
        state.clear()
        state["current_step"] = 0
        
    if "available_frameworks" not in state:
        all_frameworks = load_frameworks()
        state["available_frameworks"] = [fw["name"] for fw in all_frameworks]


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
            action = request.form.get("action")

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
                return render_template(
                    "index.html",
                    state=dict(state._session),
                    message=message,
                )

            if action == "submit_r1":
                submit_reflections_round_1(
                    state=state,
                    responses_snapshot=responses_snapshot,
                )
                state["current_step"] = 4


        elif step == 4:
            run_critique_round_2(
                state=state,
                abstraction_level=state["structured_input"]["abstraction_level"],
            )
            state["current_step"] = 5


        elif step == 5:
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
                    responses_snapshot=responses_snapshot,
                )
                state["current_step"] = 6

        elif step == 6:
            action = request.form.get("action")

            if action == "continue_after_r2":
                state["current_step"] = 7
                return render_template(
                    "index.html",
                    state=dict(state._session),
                    message=None,
                )


        elif step == 7:
            action = request.form.get("action")

            # -----------------------------
            # SKIP FINAL CRITIQUE
            # -----------------------------
            if action == "skip_round_3":
                state["done_round_3"] = True
                state["current_step"] = 10
                return render_template(
                    "index.html",
                    state=dict(state._session),
                    message=None,
                )

            # -----------------------------
            # RUN CRITIQUE ROUND 3
            # -----------------------------
            elif action == "run_round_3":
                selected_frameworks = request.form.getlist("selected_frameworks")

                # SNAPSHOT — persist selection so UI keeps it
                state["user_selected_frameworks"] = selected_frameworks

                # VALIDATION
                if len(selected_frameworks) < 1:
                    message = "Please select at least one framework."
                    return render_template(
                        "index.html",
                        state=dict(state._session),
                        message=message,
                    )

                if len(selected_frameworks) > 3:
                    message = "Please select no more than 3 frameworks."
                    return render_template(
                        "index.html",
                        state=dict(state._session),
                        message=message,
                    )

                # RUN
                run_critique_round_3(
                    state=state,
                    abstraction_level=state["structured_input"]["abstraction_level"],
                    selected_frameworks=selected_frameworks,
                )

                state["current_step"] = 8
            
        elif step == 8:
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
                    responses_snapshot=responses_snapshot,
                )
                state["current_step"] = 9






        elif step == 10:
            action = request.form.get("action")

            if action == "run_synthesis":
                run_critique_synthesis(state=state)
                state["current_step"] = 10


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
