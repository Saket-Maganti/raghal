
import unittest
import numpy as np
class StatisticsTests(unittest.TestCase):
    def test_bootstrap_determinism(self):
        x=np.array([1.,2.,3.])
        def run():
            rng=np.random.default_rng(20260724)
            return [x[rng.integers(0,3,3)].mean() for _ in range(20)]
        self.assertEqual(run(),run())
    def test_material_threshold(self):
        self.assertTrue(abs(-7.0)>=5.0); self.assertFalse(abs(4.99)>=5.0)
