"""Testes do motor PANDORA COMPETITOR Ω."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'pandora_competitor_omega.py'
spec = importlib.util.spec_from_file_location('pandora_competitor_omega', SCRIPT)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


class CompetitorOmegaTests(unittest.TestCase):
    def test_builtin_selftest(self):
        r = subprocess.run([sys.executable, str(SCRIPT), 'selftest'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_config_is_valid(self):
        import json
        cfg = json.loads((SCRIPT.parents[1] / 'config' / 'competitors.json').read_text(encoding='utf-8'))
        sites, domains, limit, delay = engine.validate_config(cfg)
        self.assertEqual(len(domains), len(set(domains)))

    def test_nonce_does_not_create_change(self):
        a = engine.extract('<title>T</title><script>n="a"</script><p>x</p>', 'https://e.org/')
        b = engine.extract('<title>T</title><script>n="b"</script><p>x</p>', 'https://e.org/')
        self.assertEqual(engine.content_hash(a), engine.content_hash(b))


if __name__ == '__main__':
    unittest.main()
