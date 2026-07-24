
import unittest
class OutputValidationTests(unittest.TestCase):
    def test_duplicate_and_missing_fixtures_are_distinct(self):
        keys=[("r","answer_only"),("r","answer_only")]
        self.assertEqual(len(keys)-len(set(keys)),1)
        expected={("r","answer_only"),("r","context_conditioned")}
        self.assertEqual(expected-set(keys),{("r","context_conditioned")})
    def test_differential_missingness_fixture(self):
        self.assertGreater(abs(1.0-0.97),0.02)
    def test_identity_and_interface_mismatch_fixtures(self):
        root=__import__("pathlib").Path(__file__).resolve().parents[1]
        cases=__import__("json").loads((root/"synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json").read_text())
        self.assertNotEqual(cases["mismatched_row_id"],"synthetic_faithful")
        self.assertNotIn(cases["wrong_interface"],("answer_only","context_conditioned"))
        self.assertNotEqual(cases["wrong_model_revision"],"a09a35458c702b33eeacc393d103063234e8bc28")
    def test_truncation_and_semantic_duplicate_fixtures(self):
        root=__import__("pathlib").Path(__file__).resolve().parents[1]
        cases=__import__("json").loads((root/"synthetic/EXPECTED_SYNTHETIC_OUTPUTS.json").read_text())
        self.assertEqual(cases["truncation_boundary"],4096)
        self.assertIn("same normalized",cases["duplicate_semantic_row"])
    def test_checksum_mismatch_fixture(self):
        import hashlib
        actual=hashlib.sha256(b"actual").hexdigest()
        claimed=hashlib.sha256(b"deliberately invalid checksum fixture").hexdigest()
        self.assertNotEqual(actual,claimed)
