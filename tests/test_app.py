import unittest
from unittest.mock import patch

import app


class FlaskEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_homepage_returns_success(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Ms. Sunny", response.data)

    def test_question_endpoint_returns_initial_question(self):
        response = self.client.get("/question")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["current_letter"], "C")
        self.assertIn("question", data)
        self.assertTrue(data["choices"])

    def test_answer_rejects_missing_json(self):
        response = self.client.post("/answer", data="", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_answer_rejects_blank_answer(self):
        response = self.client.post("/answer", json={"answer": "   "})
        self.assertEqual(response.status_code, 400)

    def test_answer_rejects_non_string_answer(self):
        response = self.client.post("/answer", json={"answer": 123})
        self.assertEqual(response.status_code, 400)

    def test_answer_rejects_non_object_json(self):
        response = self.client.post("/answer", json=["cat"])
        self.assertEqual(response.status_code, 400)

    def test_answer_returns_agent_result(self):
        result = {
            "is_correct": True,
            "explanation": "Great job!",
            "next_question": "Next question?",
            "learning_gaps": [],
            "reasoning_logs": [],
            "choices": [],
            "current_letter": "D",
        }
        with patch.object(app, "run_agents", return_value=result):
            response = self.client.post(
                "/answer",
                json={"question": "Which word starts with C?", "answer": "cat"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["is_correct"])

    def test_model_configuration_error_returns_service_unavailable(self):
        with patch.object(app, "run_agents", side_effect=ValueError("missing API key")):
            response = self.client.post("/answer", json={"answer": "cat"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("missing API key", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
