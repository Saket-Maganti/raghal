
import ast, unittest
from pathlib import Path
class NoRealInferenceTests(unittest.TestCase):
    def test_model_imports_are_below_authorization(self):
        text=(Path(__file__).resolve().parents[1]/"src/run_judge_distributed.py").read_text()
        self.assertLess(text.index("require_authorization(args.authorize_real_inference)"),text.index("from transformers import"))
    def test_no_auto_device_map_or_api_clients(self):
        root=Path(__file__).resolve().parents[1]
        checked=list((root/"src").glob("*.py"))+list((root/"notebooks").glob("*.ipynb"))
        texts="\\n".join(p.read_text(errors="ignore") for p in checked)
        self.assertNotIn('device_map="auto"',texts)
        for forbidden in ("openai.ChatCompletion","anthropic.Anthropic","groq.Groq","FreeLLMAPI"):
            self.assertNotIn(forbidden,texts)
    def test_default_notebook_gate_false(self):
        text=(Path(__file__).resolve().parents[1]/"notebooks/CONTROLLEDRAG_TARGETED_MODERN_JUDGE_T4X2.ipynb").read_text()
        self.assertIn("AUTHORIZE_REAL_INFERENCE = False",text)
    def test_no_weight_files_downloaded_into_bundle(self):
        root=Path(__file__).resolve().parents[1]
        weight_suffixes={".safetensors",".bin",".pt",".pth",".ckpt"}
        self.assertFalse([p for p in root.rglob("*") if p.is_file() and p.suffix in weight_suffixes])
