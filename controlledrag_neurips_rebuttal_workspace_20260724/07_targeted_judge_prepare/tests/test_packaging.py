
import tempfile, unittest, zipfile
from pathlib import Path
from package_kaggle_outputs import package
class PackagingTests(unittest.TestCase):
    def test_output_zip_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT"; root.mkdir()
            (root/"RUN_RECEIPT.json").write_text("{}")
            z=Path(d)/"out.zip"; result=package(root,z)
            self.assertTrue(z.exists()); self.assertEqual(result["files"],2)
            with zipfile.ZipFile(z) as a:
                self.assertIn("CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT/SHA256SUMS.txt",a.namelist())
