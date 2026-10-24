import unittest
from unittest.mock import patch

import agents


class RuleBasedAssessmentTests(unittest.TestCase):
    def test_next_letter_advances_through_full_alphabet(self):
        self.assertEqual(agents.next_letter_after("P"), "Q")
        self.assertEqual(agents.next_letter_after("Z"), "A")

    def test_accepts_word_starting_with_target_letter(self):
        result = agents._rule_based_assessment(
            "Which word starts with the letter C?", "cat", "C"
        )
        self.assertTrue(result["is_correct"])
        self.assertEqual(result["learning_gaps"], [])

    def test_rejects_word_not_starting_with_target_letter(self):
        result = agents._rule_based_assessment(
            "Which word starts with the letter C?", "dog", "C"
        )
        self.assertFalse(result["is_correct"])
        self.assertTrue(result["learning_gaps"])

    def test_assessment_uses_rule_fallback_when_model_fails(self):
        state = {
            "question": "Which word starts with the letter C?",
            "student_answer": "cat",
            "current_letter": "C",
            "learning_gaps": [],
            "reasoning_logs": [],
        }
        with patch.object(agents, "call_nemotron", side_effect=RuntimeError("offline")):
            result = agents.assessment_agent(state)
        self.assertTrue(result["is_correct"])
        self.assertEqual(result["learning_gaps"], [])


if __name__ == "__main__":
    unittest.main()
