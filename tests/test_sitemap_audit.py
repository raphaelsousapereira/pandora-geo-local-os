"""Testes do motor PANDORA SITEMAP & LLMS AUDIT Ω."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'pandora_sitemap_audit.py'
spec = importlib.util.spec_from_file_location('pandora_sitemap_audit', SCRIPT)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


class SitemapAuditTests(unittest.TestCase):
    def test_builtin_selftest(self):
        r = subprocess.run([sys.executable, str(SCRIPT), 'selftest'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_parse_llms(self):
        p = engine.parse_llms('# Site\n\n> Resumo.\n\n## Páginas\n- [A](https://x/a/): nota\n- [B](https://x/b/)\n')
        self.assertEqual(p['h1'], 'Site')
        self.assertEqual(p['summary'], 'Resumo.')
        self.assertEqual([l['notes'] for l in p['links']], ['nota', ''])

    def test_parse_sitemap_namespace_agnostic(self):
        kind, entries = engine.parse_sitemap(
            b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            b'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"><url><loc>https://x/</loc>'
            b'<lastmod>2026-01-01</lastmod><image:image><image:loc>https://x/i.png</image:loc></image:image></url></urlset>')
        self.assertEqual(kind, 'urlset')
        self.assertEqual(entries[0]['images'], 1)

    def test_heading_engine_integration(self):
        self.assertIsNotNone(engine.load_heading_engine())


if __name__ == '__main__':
    unittest.main()
