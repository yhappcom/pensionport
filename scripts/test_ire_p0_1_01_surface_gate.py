"""P101 static CLI exposure scope: never certify broader deployments."""
import tempfile
import unittest
from pathlib import Path
from scripts.ire_p0_1_01_surface_gate import ROOT,CORE,validate
class P101SurfaceTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.r=Path(t.name)
        for path in CORE:
            p=self.r/path;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes((ROOT/path).read_bytes())
    def test_core_positive(self):
        self.assertEqual(validate(ROOT),[])
        self.assertEqual(validate(self.r),[])
    def test_direct_legacy_cli_detected(self):
        p=self.r/CORE[1]
        p.write_text(p.read_text()+"\nif __name__ == '__main__':\n    pass\n")
        self.assertTrue(any("DIRECT_CLI" in x for x in validate(self.r)))
    def test_web_framework_detected(self):
        p=self.r/CORE[4]
        p.write_text(p.read_text()+"\nimport fastapi\n")
        self.assertTrue(any("SERVICE_FRAMEWORK" in x for x in validate(self.r)))
    def test_public_api_export_cannot_multiply(self):
        p=self.r/next(x for x in CORE if x.endswith("/v243_canonical_e1_e5_route.py"))
        p.write_text(p.read_text().replace(
            '__all__ = ("run_canonical_research_route",)',
            '__all__ = ("run_canonical_research_route","legacy_publish")'))
        self.assertTrue(any("SINGLE_OFFICIAL" in x for x in validate(self.r)))
    def test_e4_seal_readback_not_optional(self):
        p=self.r/next(x for x in CORE if x.endswith("/v243_canonical_e1_e5_route.py"))
        p.write_text(p.read_text().replace("verify_e4_certificate(","no_verification("))
        self.assertTrue(any("READBACK_GATE" in x for x in validate(self.r)))
    def test_external_app_config_requires_reaudit(self):
        (self.r/"Dockerfile").write_text("FROM scratch\n")
        self.assertTrue(any("DEPLOYMENT_CONFIG" in x for x in validate(self.r)))
    def test_unprotected_python_import_still_exists(self):
        self.assertIn("PrivateKnowledgeStore",(self.r/CORE[1]).read_text())
        self.assertEqual(validate(self.r),[])
if __name__=="__main__":
    unittest.main()
