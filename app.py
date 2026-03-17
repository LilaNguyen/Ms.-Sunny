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
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    question = data.get("question", INITIAL_QUESTION)
    student_answer = data.get("answer", "").strip()
    current_letter = data.get("current_letter")

    if not student_answer:
        return jsonify({"error": "No answer provided"}), 400

    try:
        result = run_agents(
            question=question,
            student_answer=student_answer,
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
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 503
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
