
import json, unittest
from pathlib import Path
from utils_hashing import semantic_digest

class InputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.rows = [json.loads(x) for x in (root/"synthetic/synthetic_rows.jsonl").read_text().splitlines()]
    def test_synthetic_rows_have_unique_ids(self):
        self.assertEqual(len(self.rows), len({r["experiment_row_id"] for r in self.rows}))
    def test_semantic_digest_deterministic(self):
        row={"question":" Q ","retrieved_context":"C","answer":"A","system":"baseline"}
        self.assertEqual(semantic_digest(row), semantic_digest(row))
    def test_paired_and_unpaired_system_fixtures(self):
        pairs={}
        for row in self.rows: pairs.setdefault(row["pair_id"],set()).add(row["system"])
        self.assertEqual(pairs["synthetic_pair_1"],{"baseline","hcpc_v1"})
        self.assertEqual(pairs["synthetic_pair_2"],{"baseline"})
    def test_two_human_slice_fixtures_remain_separate(self):
        slices={r["human_slice"] for r in self.rows if r["human_label_available"]}
        self.assertEqual(slices,{"typical","disagreement_targeted"})
