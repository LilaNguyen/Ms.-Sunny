import json
import os
import random
from typing import Optional

CURRICULUM_PATH = os.path.join(os.path.dirname(__file__), "curriculum.json")

_curriculum: Optional[dict] = None

WORD_EMOJIS: dict[str, str] = {
    "apple": "🍎", "ant": "🐜", "alligator": "🐊", "axe": "🪓",
    "ball": "⚽", "bear": "🐻", "bus": "🚌", "book": "📚",
    "cat": "🐱", "cup": "🥤", "car": "🚗", "cot": "🛏️",
    "dog": "🐕", "duck": "🦆", "door": "🚪", "drum": "🥁",
    "egg": "🥚", "elephant": "🐘", "end": "🏁", "edge": "🔪",
    "fish": "🐟", "frog": "🐸", "fan": "🌀", "fire": "🔥",
    "goat": "🐐", "game": "🎮", "gift": "🎁", "green": "💚",
    "hat": "🎩", "house": "🏠", "hand": "🤚", "hop": "🐇",
    "igloo": "🏔️", "inch": "📏", "insect": "🐛", "itch": "🤔",
    "jump": "🦘", "jar": "🫙", "jet": "✈️", "jelly": "🍇",
    "kite": "🪁", "king": "👑", "kid": "🧒", "kick": "🦵",
    "lion": "🦁", "lamp": "💡", "leaf": "🍃", "lemon": "🍋",
    "moon": "🌙", "monkey": "🐒", "map": "🗺️", "milk": "🥛",
    "nest": "🪺", "nose": "👃", "nut": "🥜", "night": "🌙",
    "octopus": "🐙", "ox": "🐂", "on": "💡", "odd": "🤔",
    "pig": "🐷", "pizza": "🍕", "pop": "🎈", "pet": "🐾",
    "queen": "👸", "quack": "🦆", "quiz": "❓", "quick": "⚡",
    "rabbit": "🐰", "red": "🔴", "run": "🏃", "ring": "💍",
    "sun": "☀️", "snake": "🐍", "sand": "🏖️", "sock": "🧦",
    "tiger": "🐯", "top": "🪀", "tent": "⛺", "tree": "🌳",
    "umbrella": "☂️", "up": "⬆️", "under": "⬇️", "ugly": "😬",
    "van": "🚐", "vine": "🌿", "vest": "🦺", "volcano": "🌋",
    "whale": "🐋", "water": "💧", "wind": "💨", "worm": "🪱",
    "fox": "🦊", "box": "📦", "wax": "🕯️", "six": "6️⃣",
    "yellow": "💛", "yak": "🦙", "yard": "🌿", "yell": "📢",
    "zebra": "🦓", "zoo": "🦁", "zip": "🤐", "zero": "0️⃣",
    "ship": "🚢", "shoe": "👟", "shell": "🐚", "shop": "🛒",
    "chair": "🪑", "cheese": "🧀", "chicken": "🐔", "child": "🧒",
    "think": "💭", "three": "3️⃣", "there": "👉", "the": "📖",
    "blue": "💙", "black": "🖤", "blink": "👁️", "blow": "💨",
    "and": "➕", "is": "⭐", "in": "📍", "it": "💡",
}


def load_curriculum() -> dict:
    global _curriculum
    if _curriculum is None:
        with open(CURRICULUM_PATH, "r") as f:
            _curriculum = json.load(f)
    return _curriculum


def generate_choices_for_letter(letter: str, curriculum: dict, n: int = 4) -> list[dict]:
    """Return n multiple-choice word cards (one starts with `letter`, rest are distractors)."""
    correct_words: list[str] = []
    distractor_words: list[str] = []

    for phonics in curriculum.get("phonics", []):
        examples = phonics.get("examples", [])
        if phonics["letter"].upper() == letter.upper():
            correct_words.extend(examples)
        else:
            distractor_words.extend(examples)

    if not correct_words:
        return []

    correct = random.choice(correct_words)
    random.shuffle(distractor_words)
    chosen_distractors = distractor_words[: n - 1]

    all_words = [correct] + chosen_distractors
    random.shuffle(all_words)

    return [
        {"word": w, "emoji": WORD_EMOJIS.get(w.lower(), "📝")}
        for w in all_words
    ]


def retrieve_concept(query: str) -> dict:
    curriculum = load_curriculum()
    query_lower = query.lower()

    for phonics in curriculum.get("phonics", []):
        letter = phonics["letter"].lower()
        examples = [e.lower() for e in phonics["examples"]]
        if (
            f"letter {letter}" in query_lower
            or any(f" {ex} " in f" {query_lower} " for ex in examples)
            or phonics["sound"].lower() in query_lower
        ):
            choices = generate_choices_for_letter(phonics["letter"], curriculum)
            return {
                "type": "phonics",
                "concept": phonics,
                "found": True,
                "choices": choices,
                "current_letter": phonics["letter"].upper(),
            }

    for blend in curriculum.get("blends", []):
        blend_lower = blend["blend"].lower()
        examples = [e.lower() for e in blend["examples"]]
        if (
            blend_lower in query_lower
            or any(ex in query_lower for ex in examples)
            or blend["sound"].lower() in query_lower
        ):
            return {
                "type": "blend",
                "concept": blend,
                "found": True,
                "choices": [],
                "current_letter": None,
            }

    for sight in curriculum.get("sight_words", []):
        word_lower = sight["word"].lower()
        if word_lower in query_lower.split():
            return {
                "type": "sight_word",
                "concept": sight,
                "found": True,
                "choices": [],
                "current_letter": None,
            }

    if curriculum["phonics"]:
        fallback = random.choice(curriculum["phonics"])
        choices = generate_choices_for_letter(fallback["letter"], curriculum)
        return {
            "type": "phonics",
            "concept": fallback,
            "found": False,
            "choices": choices,
            "current_letter": fallback["letter"].upper(),
            "note": "Could not find a specific match; returning a general phonics lesson.",
        }

    return {"type": None, "concept": None, "found": False, "choices": [], "current_letter": None}
