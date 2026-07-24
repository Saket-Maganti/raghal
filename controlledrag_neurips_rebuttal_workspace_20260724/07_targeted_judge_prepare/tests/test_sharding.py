
import unittest
from utils_hashing import deterministic_shard
class ShardingTests(unittest.TestCase):
    def test_determinism(self):
        self.assertEqual(deterministic_shard("row","answer_only"),deterministic_shard("row","answer_only"))
    def test_two_shards_only(self):
        self.assertTrue(all(deterministic_shard(str(i),"context_conditioned") in (0,1) for i in range(100)))
