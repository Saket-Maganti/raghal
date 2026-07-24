
import unittest
from pathlib import Path
from render_prompts import normalized_symmetry, render_prompt
class PromptSymmetryTests(unittest.TestCase):
    def test_normalized_templates_match(self):
        self.assertTrue(normalized_symmetry(Path(__file__).resolve().parents[1]))
    def test_only_context_interface_shows_context(self):
        root=Path(__file__).resolve().parents[1]; row={"question":"Q","answer":"A","retrieved_context":"SECRET_CONTEXT"}
        self.assertNotIn("SECRET_CONTEXT", render_prompt(row,"answer_only",root))
        self.assertIn("SECRET_CONTEXT", render_prompt(row,"context_conditioned",root))
