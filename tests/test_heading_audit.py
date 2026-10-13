"""Testes do motor PANDORA HEADING AUDIT Ω (camada 7.1 — HTML textual)."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'pandora_heading_audit.py'
spec = importlib.util.spec_from_file_location('pandora_heading_audit', SCRIPT)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


class HeadingAuditTests(unittest.TestCase):
    def test_builtin_selftests(self):
        for cmd in ('selftest', 'selftest-v4'):
            r = subprocess.run([sys.executable, str(SCRIPT), cmd], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_perfect_page_scores_1000(self):
        r = engine.analyze('x', '<html lang="pt-BR"><title>Clínica</title><main><h1>Clínica</h1><h2>Serviços</h2></main></html>')
        self.assertEqual(r['score'], 1000)

    def test_missing_h1_flagged(self):
        r = engine.analyze('x', '<html lang="pt"><title>X</title><h2>Sem H1</h2></html>')
        codes = {i['code'] for i in r['issues']}
        self.assertIn('MISSING_H1', codes)
        self.assertLess(r['score'], 1000)

    def test_audit_cli_writes_reports(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / 'site'
            site.mkdir()
            (site / 'index.html').write_text('<html lang="pt"><title>A</title><main><h1>A</h1></main></html>', encoding='utf-8')
            out = Path(d) / 'report.json'
            r = subprocess.run([sys.executable, str(SCRIPT), 'audit', str(site), '--json', str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            report = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(report['version'], engine.VERSION)
            self.assertEqual(len(report['pages']), 1)


if __name__ == '__main__':
    unittest.main()
