"""Testes do motor PANDORA ADS Ω."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'pandora_ads_omega.py'
spec = importlib.util.spec_from_file_location('pandora_ads_omega', SCRIPT)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


class AdsOmegaTests(unittest.TestCase):
    def test_builtin_selftest(self):
        r = subprocess.run([sys.executable, str(SCRIPT), 'selftest'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_example_config_runs(self):
        cfg_path = ROOT / 'examples' / 'ads' / 'config.json'
        report = engine.AdsAudit(json.loads(cfg_path.read_text(encoding='utf-8')), cfg_path.parent).run()
        self.assertEqual(report['mode'], 'read_only')
        self.assertGreater(len(report['findings']), 5)

    def test_negative_broad_does_not_match_variants(self):
        self.assertFalse(engine.negative_blocks('grátis', 'Ampla', 'curso gratuito'))
        self.assertTrue(engine.negative_blocks('grátis', 'Ampla', 'curso grátis online'))


if __name__ == '__main__':
    unittest.main()
