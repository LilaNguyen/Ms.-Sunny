import re
from typing import TypedDict, List, Optional, Annotated
import json
import operator
from langgraph.graph import StateGraph, END
from nemotron_api import call_nemotron
from rag import retrieve_concept, load_curriculum, generate_choices_for_letter

LETTER_SEQUENCE = list("ABCDEFGHIJKLMNOPRSTW")


class AgentState(TypedDict):
    question: str
    student_answer: str
    is_correct: Optional[bool]
    learning_gaps: List[str]
    retrieved_concept: Optional[dict]
    explanation: Optional[str]
    next_question: Optional[str]
    choices: List[dict]
    current_letter: Optional[str]
    reasoning_logs: Annotated[List[dict], operator.add]
    plan: Optional[str]


def log_step(agent_name: str, thought: str, action: str, observation: str, plan: str) -> dict:
    return {
        "agent": agent_name,
        "THOUGHT": thought,
        "ACTION": action,
        "OBSERVATION": observation,
        "PLAN": plan,
    }


def extract_letter_from_question(question: str) -> Optional[str]:
    """Try to extract a single letter being studied from a question string."""
    match = re.search(r"\bletter\s+([A-Z])\b", question, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b([A-Z])\b", question)
    if match:
        return match.group(1).upper()
    return None


def next_letter_after(letter: Optional[str]) -> str:
    """Return the next letter in the teaching sequence."""
    if letter and letter.upper() in LETTER_SEQUENCE:
        idx = LETTER_SEQUENCE.index(letter.upper())
        return LETTER_SEQUENCE[(idx + 1) % len(LETTER_SEQUENCE)]
    return "B"


def _rule_based_assessment(question: str, student_answer: str, current_letter: Optional[str]) -> dict:
    """Fallback: check if the answer word starts with the target letter."""
    letter = current_letter or extract_letter_from_question(question)
    if letter:
        words = student_answer.lower().split()
        is_correct = any(w.startswith(letter.lower()) for w in words)
        if is_correct:
            return {"is_correct": True, "learning_gaps": [], "feedback": f"Yes! {student_answer.capitalize()} starts with the letter {letter}. Great job!"}
        else:
            return {"is_correct": False, "learning_gaps": [f"letter {letter} recognition"], "feedback": f"Not quite — look for a word that starts with the letter {letter}!"}
    return {"is_correct": False, "learning_gaps": ["letter recognition"], "feedback": "Let's keep practicing!"}


def assessment_agent(state: AgentState) -> AgentState:
    question = state["question"]
    student_answer = state["student_answer"]
    current_letter = state.get("current_letter")

    thought = (
        f"A student answered '{student_answer}' to the question '{question}'. "
        "I need to figure out if this is correct and what they might be struggling with."
    )
    action = "Calling Nemotron model to assess the student's answer."

    system_prompt = (
        "You are a phonics teacher grading a student answer. "
        "Output ONLY a single JSON object — no extra text, no markdown, no explanation.\n"
        'Format: {"is_correct": true, "learning_gaps": [], "feedback": "Great job!"}\n'
        'If wrong: {"is_correct": false, "learning_gaps": ["letter X recognition"], "feedback": "Try again!"}'
    )
    user_prompt = (
        f"Question: {question}\n"
        f"Student answer: {student_answer}\n"
        "Output JSON only."
    )

    result = None
    try:
        response = call_nemotron(system_prompt, user_prompt, temperature=0.3)
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            parsed = json.loads(response[start:end])
            if "is_correct" in parsed:
                result = parsed
    except Exception:
        pass

    if result is None:
        result = _rule_based_assessment(question, student_answer, current_letter)

    is_correct = bool(result.get("is_correct", False))
    learning_gaps = result.get("learning_gaps", [])
    feedback = result.get("feedback", "Good try!")

    observation = f"Answer is {'correct' if is_correct else 'incorrect'}. Learning gaps found: {learning_gaps}."
    plan = (
        "Answer is correct — generate a new progressive question."
        if is_correct
        else "Need to retrieve the right curriculum concept, explain it, and create a new practice question."
    )

    log = log_step("Assessment Agent", thought, action, observation, plan)

    return {
        "is_correct": is_correct,
        "learning_gaps": learning_gaps,
        "explanation": feedback if is_correct else None,
        "reasoning_logs": [log],
        "plan": plan,
    }


def retrieval_agent(state: AgentState) -> AgentState:
    question = state["question"]
    learning_gaps = state.get("learning_gaps", [])
    student_answer = state.get("student_answer", "")
    current_letter = state.get("current_letter")

    # Filter out synthetic/error gap strings that aren't real phonics gaps
    real_gaps = [g for g in learning_gaps if not any(skip in g.lower() for skip in ("unable", "unclear", "assess"))]

    # Build search query: prefer current_letter as anchor when gaps are clean
    if current_letter and not real_gaps:
        search_query = f"letter {current_letter} {question}"
    else:
        search_query = " ".join(real_gaps) + " " + question + " " + student_answer

    thought = (
        f"The student has gaps: {learning_gaps}. "
        "I need to find the right lesson from our curriculum knowledge base."
    )
    action = f"Searching curriculum for: '{search_query[:80]}'"

    result = retrieve_concept(search_query)

    concept = result.get("concept", {})
    current_letter = result.get("current_letter")
    choices = result.get("choices", [])

    if result["found"]:
        concept_name = concept.get("letter") or concept.get("blend") or concept.get("word", "")
        observation = f"Found concept '{concept_name}' (type: {result['type']}). Generated {len(choices)} multiple-choice options."
    else:
        observation = f"No exact match. Using fallback concept for letter '{current_letter}'. Generated {len(choices)} choices."

    plan = "Pass the concept to Lesson Generator to create a kid-friendly explanation and multiple-choice question."

    log = log_step("Retrieval Agent (RAG)", thought, action, observation, plan)

    return {
        "retrieved_concept": result,
        "choices": choices,
        "current_letter": current_letter,
        "reasoning_logs": [log],
        "plan": plan,
    }


def lesson_generator_agent(state: AgentState) -> AgentState:
    retrieved = state.get("retrieved_concept", {})
    concept = retrieved.get("concept", {})
    learning_gaps = state.get("learning_gaps", [])
    question = state["question"]
    student_answer = state["student_answer"]
    current_letter = state.get("current_letter")

    thought = (
        "I have the curriculum concept. I need to explain it to a 7-year-old "
        "using simple words, a fun example, and lots of encouragement."
    )
    action = "Calling Nemotron to generate a kid-friendly explanation."

    concept_text = json.dumps(concept, indent=2) if concept else "general phonics"

    system_prompt = (
        "You are Ms. Sunny, a warm and fun teacher for 7-year-old children. "
        "Explain reading and phonics using very simple language and short sentences. "
        "Use relatable examples like animals, toys, and food. "
        "End with one encouraging sentence. Max 3 sentences total."
    )
    user_prompt = (
        f"Student tried: '{question}' — answered: '{student_answer}'\n"
        f"Learning gaps: {learning_gaps}\n"
        f"Curriculum concept:\n{concept_text}\n\n"
        "Explain this simply and encouragingly!"
    )

    try:
        explanation = call_nemotron(system_prompt, user_prompt, temperature=0.7)
    except Exception:
        desc = concept.get("description", "") if concept else ""
        examples = concept.get("examples", []) if concept else []
        explanation = (
            f"{desc} Think of words like: {', '.join(examples[:3])}! You are doing great!"
        ) if desc else "Let's keep learning together — you're doing amazing!"

    letter_note = f" (letter {current_letter})" if current_letter else ""
    observation = f"Generated explanation{letter_note} ({len(explanation)} chars)."
    plan = "Send to Reinforcement Agent to create a new multiple-choice question."

    log = log_step("Lesson Generator Agent", thought, action, observation, plan)

    return {
        "explanation": explanation,
        "reasoning_logs": [log],
        "plan": plan,
    }


def reinforcement_agent(state: AgentState) -> AgentState:
    retrieved = state.get("retrieved_concept", {})
    concept = retrieved.get("concept", {})
    learning_gaps = state.get("learning_gaps", [])
    question = state["question"]
    current_letter = state.get("current_letter")

    thought = (
        f"Student struggled with: {learning_gaps}. "
        "I'll create a fresh multiple-choice question on the same concept."
    )
    action = "Calling Nemotron to generate a new practice question."

    concept_text = json.dumps(concept, indent=2) if concept else ""

    system_prompt = (
        "You are a creative teacher for 7-year-old students. "
        "Create ONE short, fun question asking the student to identify a word "
        "that starts with a given letter. "
        "Format: 'Which of these words starts with the letter X?' "
        "Only return the question itself."
    )
    user_prompt = (
        f"Student needs more practice with: {learning_gaps}\n"
        f"Previous question: '{question}'\n"
        f"Concept:\n{concept_text}\n"
        f"Current letter being studied: {current_letter or 'unknown'}\n"
        "Create a new multiple-choice phonics question!"
    )

    try:
        next_question = call_nemotron(system_prompt, user_prompt, temperature=0.8)
        next_question = next_question.strip().strip('"')
    except Exception:
        letter = current_letter or "C"
        if concept and "practice_question" in concept:
            next_question = concept["practice_question"]
        else:
            next_question = f"Which of these words starts with the letter {letter}?"

    observation = f"Generated question: '{next_question[:60]}...'"
    plan = "Workflow complete. Return results with choices to the student."

    log = log_step("Reinforcement Agent", thought, action, observation, plan)

    return {
        "next_question": next_question,
        "reasoning_logs": [log],
        "plan": plan,
    }


def should_continue_after_assessment(state: AgentState) -> str:
    return "end_correct" if state.get("is_correct") else "retrieve"


def generate_correct_next_question(state: AgentState) -> AgentState:
    question = state["question"]
    current_letter = state.get("current_letter") or extract_letter_from_question(question)
    next_letter = next_letter_after(current_letter)

    thought = (
        "The student answered correctly! I'll advance them to the next letter "
        f"and create a new multiple-choice question for letter '{next_letter}'."
    )
    action = f"Generating question for letter '{next_letter}' + building new choices."

    system_prompt = (
        "You are Ms. Sunny, a fun teacher for 7-year-old students. "
        "A student just answered a phonics question correctly! "
        "Create ONE short question asking them to identify a word that starts with a given letter. "
        "Format: 'Which of these words starts with the letter X?' "
        "Only return the question itself."
    )
    user_prompt = (
        f"Student just got this right: '{question}'\n"
        f"Now teach them letter '{next_letter}'. Create a new question!"
    )

    try:
        next_question = call_nemotron(system_prompt, user_prompt, temperature=0.8)
        next_question = next_question.strip().strip('"')
    except Exception:
        next_question = f"Which of these words starts with the letter {next_letter}?"

    curriculum = load_curriculum()
    choices = generate_choices_for_letter(next_letter, curriculum)

    observation = f"Generated question for letter '{next_letter}' with {len(choices)} choices."
    plan = "Workflow complete. Student gets next letter challenge."

    log = log_step("Lesson Generator Agent", thought, action, observation, plan)

    return {
        "next_question": next_question,
        "choices": choices,
        "current_letter": next_letter,
        "reasoning_logs": [log],
        "plan": plan,
    }


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("assessment", assessment_agent)
    workflow.add_node("retrieval", retrieval_agent)
    workflow.add_node("lesson_generator", lesson_generator_agent)
    workflow.add_node("reinforcement", reinforcement_agent)
    workflow.add_node("correct_question", generate_correct_next_question)

    workflow.set_entry_point("assessment")
    workflow.add_conditional_edges(
        "assessment",
        should_continue_after_assessment,
        {"retrieve": "retrieval", "end_correct": "correct_question"},
    )
    workflow.add_edge("retrieval", "lesson_generator")
    workflow.add_edge("lesson_generator", "reinforcement")
    workflow.add_edge("reinforcement", END)
    workflow.add_edge("correct_question", END)

    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_agents(question: str, student_answer: str, current_letter: Optional[str] = None) -> dict:
    graph = get_graph()

    initial_state: AgentState = {
        "question": question,
        "student_answer": student_answer,
        "is_correct": None,
        "learning_gaps": [],
        "retrieved_concept": None,
        "explanation": None,
        "next_question": None,
        "choices": [],
        "current_letter": current_letter or extract_letter_from_question(question),
        "reasoning_logs": [],
        "plan": None,
    }

    result = graph.invoke(initial_state)

    return {
        "is_correct": result.get("is_correct", False),
        "explanation": result.get("explanation", ""),
        "next_question": result.get("next_question", ""),
        "learning_gaps": result.get("learning_gaps", []),
        "reasoning_logs": result.get("reasoning_logs", []),
        "choices": result.get("choices", []),
        "current_letter": result.get("current_letter"),
    }
