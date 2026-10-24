# Ms. Sunny — Workspace Notes

## Overview

This repository contains a Python Flask application for an AI reading and phonics tutor, plus a React/Vite frontend and additional Replit workspace packages. The core AI workflow is implemented in Python and orchestrated with LangGraph.

## Core application

- `app.py`: Flask HTTP API and Flask-served fallback interface
- `agents.py`: four agent functions and LangGraph routing
- `rag.py`: keyword/rule-based retrieval from `curriculum.json`
- `curriculum.json`: local phonics, blend, and sight-word content
- `nemotron_api.py`: NVIDIA Nemotron client
- `templates/` and `static/`: Flask HTML/CSS/JavaScript interface
- `artifacts/ms-sunny/`: React/Vite frontend used in the Replit workspace

## Agent workflow

1. **Assessment Agent** evaluates a student's answer and identifies possible learning gaps.
2. **Retrieval Agent** searches the local curriculum for a relevant concept.
3. **Lesson Generator Agent** uses the retrieved concept in a Nemotron prompt to generate a child-friendly explanation.
4. **Reinforcement Agent** creates follow-up practice content.

The graph routes correct answers to the next-question path. Incorrect answers continue through retrieval, lesson generation, and reinforcement.

## Retrieval notes

The current retriever matches query text against curriculum fields such as letters, example words, sounds, blends, and sight words. It uses keyword/rule-based matching, not embedding similarity or a vector database. Unmatched queries fall back to a randomly selected phonics concept.

## Environment

- Python 3.11+
- `NVIDIA_API_KEY` is required for Nemotron calls. Set it in the environment or Replit Secrets; never commit the key.
- The Flask backend can be started with `python app.py`.
- The Vite frontend proxies `/answer` and `/question` to a Flask backend at `http://localhost:8000`. Its Vite config requires `PORT` and `BASE_PATH`.

Some other workspace packages and generated files are present in this repository; they are not part of the core Python agent workflow.
