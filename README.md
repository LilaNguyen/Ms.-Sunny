# Ms. Sunny — AI Classroom Assistant

Ms. Sunny is a prototype AI reading and phonics tutor built for young learners. It uses a LangGraph workflow to assess a student's answer, retrieve relevant curriculum material, generate a child-friendly explanation, and provide another practice question.

## How it works

The Python backend defines four specialized agents in `agents.py`:

1. **Assessment Agent** — asks NVIDIA Nemotron to evaluate the student's answer and identify possible learning gaps, with a rule-based fallback.
2. **Retrieval Agent** — searches the local `curriculum.json` knowledge base for a matching phonics concept.
3. **Lesson Generator Agent** — passes the retrieved concept into a Nemotron prompt to generate a short, encouraging explanation.
4. **Reinforcement Agent** — prepares the next practice question and response data.

LangGraph routes the workflow based on the assessment result. Incorrect answers continue through retrieval, lesson generation, and reinforcement; correct answers follow a shorter path to the next question.

## Retrieval approach

The curriculum is stored locally in `curriculum.json` and includes phonics concepts, example words, rules, practice questions, blends, and sight words. The current retriever in `rag.py` uses keyword and rule-based matching against this structured content. It is a lightweight retrieval-augmented generation (RAG) implementation; it does **not** use vector embeddings or a vector database. When no match is found, it selects a fallback phonics concept.

## Technology

- Python and Flask
- LangGraph for workflow orchestration and state transitions
- NVIDIA Nemotron via the OpenAI-compatible NVIDIA API
- HTML, CSS, and JavaScript for the Flask-served interface
- React, Vite, and TypeScript files are also present under `artifacts/ms-sunny/` for the Replit frontend

## Run the Flask app locally

Requirements: Python 3.11+ and an NVIDIA API key.

1. Clone the repository and enter its directory.
2. Install the Python project dependencies (for example, with `uv sync` or `pip install -e .`).
3. Set the API key in your shell. Do not commit secrets:

   ```bash
   export NVIDIA_API_KEY="your_key_here"
   ```

4. Start the Flask app:

   ```bash
   python app.py
   ```

5. Open [http://localhost:5000](http://localhost:5000).

The Flask app serves the interface in `templates/index.html` and exposes `GET /question` and `POST /answer`. The app can start without an API key; model calls require `NVIDIA_API_KEY` or `NEMOTRON_API_KEY`, and the assessment agent falls back to a simple rule-based check if the model call fails. The frontend expects the backend to be available when submitting answers. The separate Vite frontend under `artifacts/ms-sunny/` uses a development proxy to a Flask server on port 8000 and requires `PORT` and `BASE_PATH` environment variables for Vite configuration.

## Project structure

```text
.
├── app.py                  # Flask application and HTTP endpoints
├── agents.py               # LangGraph state, agents, and routing
├── rag.py                  # Curriculum loading and rule-based retrieval
├── curriculum.json         # Local phonics knowledge base
├── nemotron_api.py         # Lazy-initialized NVIDIA Nemotron API client
├── templates/index.html    # Flask UI
├── static/                 # Flask UI styles and browser logic
└── artifacts/ms-sunny/     # React/Vite frontend in the Replit workspace
```

## Run the tests

The Python unit tests use the standard-library `unittest` runner and mock the model client so they do not need a live NVIDIA API key.

```bash
python -m pip install flask flask-cors langgraph openai
python -m unittest discover -s tests -v
```

A GitHub Actions workflow runs the same test suite on pushes to `main` and `portfolio-polish`, and on pull requests targeting `main`.

## Scope and limitations

This is a hackathon prototype, not a validated educational assessment tool. Answer evaluation and retrieval can make mistakes; manual testing during development does not establish measured accuracy or learning outcomes. The curriculum is a small, hand-authored knowledge base rather than a comprehensive reading curriculum.
