import unittest
from unittest.mock import patch

import rag


class CurriculumRetrievalTests(unittest.TestCase):
    def setUp(self):
        rag._curriculum = None

    def test_load_curriculum_contains_phonics(self):
        curriculum = rag.load_curriculum()
        self.assertIn("phonics", curriculum)
        self.assertTrue(curriculum["phonics"])

    def test_retrieves_letter_when_query_mentions_it(self):
        result = rag.retrieve_concept("letter C cat")
        self.assertTrue(result["found"])
        self.assertEqual(result["type"], "phonics")
        self.assertEqual(result["concept"]["letter"], "C")

    def test_retrieves_blend_from_example(self):
        curriculum = rag.load_curriculum()
        if not curriculum.get("blends"):
            self.skipTest("Curriculum has no blends")
        blend = curriculum["blends"][0]
        result = rag.retrieve_concept(blend["examples"][0])
        self.assertTrue(result["found"])
        self.assertEqual(result["type"], "blend")

    def test_unknown_query_uses_documented_fallback(self):
        result = rag.retrieve_concept("an unrelated sentence with no curriculum term")
        self.assertFalse(result["found"])
        self.assertEqual(result["type"], "phonics")
        self.assertIn("concept", result)


if __name__ == "__main__":
    unittest.main()
