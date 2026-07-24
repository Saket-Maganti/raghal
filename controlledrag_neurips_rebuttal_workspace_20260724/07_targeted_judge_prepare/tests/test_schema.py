
import json, unittest
from pathlib import Path
from judge_schema import parse_judge_output
class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((Path(__file__).resolve().parents[1]/"synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json").read_text())
    def test_three_valid_cases(self):
        for key in ("valid_faithful","valid_unfaithful","valid_insufficient"):
            self.assertIsNotNone(parse_judge_output(self.cases[key])[0])
    def test_all_required_case_families_declared(self):
        self.assertEqual(len(self.cases),26)
    def test_seven_invalid_schema_cases(self):
        for key in ("malformed_json","markdown_fences","extra_keys","score_below","score_above","boolean_string","missing_key"):
            self.assertIsNone(parse_judge_output(self.cases[key])[0], key)
    def test_threshold_consistency(self):
        self.assertEqual(parse_judge_output('{"faithfulness_score": 80, "faithful": false, "insufficient_information": false}')[1],"threshold_inconsistency")
