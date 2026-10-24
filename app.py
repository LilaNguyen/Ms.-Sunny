import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from agents import run_agents
from rag import load_curriculum, generate_choices_for_letter

app = Flask(__name__)
CORS(app)

INITIAL_LETTER = "C"
INITIAL_QUESTION = "Which of these words starts with the letter C?"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/question", methods=["GET"])
def get_initial_question():
    curriculum = load_curriculum()
    choices = generate_choices_for_letter(INITIAL_LETTER, curriculum)
    return jsonify({
        "question": INITIAL_QUESTION,
        "current_letter": INITIAL_LETTER,
        "choices": choices,
    })


@app.route("/answer", methods=["POST"])
def answer():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    question = data.get("question", INITIAL_QUESTION)
    student_answer = data.get("answer", "")
    current_letter = data.get("current_letter")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Question must be a non-empty string"}), 400
    if not isinstance(student_answer, str) or not student_answer.strip():
        return jsonify({"error": "Answer must be a non-empty string"}), 400
    if current_letter is not None and not isinstance(current_letter, str):
        return jsonify({"error": "current_letter must be a string"}), 400

    try:
        result = run_agents(
            question=question.strip(),
            student_answer=student_answer.strip(),
            current_letter=current_letter,
        )
        return jsonify({
            "is_correct": result["is_correct"],
            "explanation": result["explanation"],
            "next_question": result["next_question"],
            "learning_gaps": result["learning_gaps"],
            "reasoning_logs": result["reasoning_logs"],
            "choices": result["choices"],
            "current_letter": result["current_letter"],
        })
    except ValueError as exc:
        # Missing model credentials are surfaced as a configuration response.
        app.logger.warning("Unable to process answer due to configuration: %s", exc)
        return jsonify({"error": str(exc)}), 503
    except Exception:
        # Keep internal exception details in server logs, not in API responses.
        app.logger.exception("Unexpected error while processing student answer")
        return jsonify({"error": "An unexpected error occurred while processing the answer."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
