"""Testes do motor PANDORA SITEMAP & LLMS AUDIT Ω."""
import importlib.util
import json
import subprocess
import sys
import tempfile
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

    def test_fetch_failures_are_measured_in_mixed_sample(self):
        audit = engine.Audit('https://example.org', None, headings=False)
        pages = {
            'https://example.org/': {'url': 'https://example.org/', 'captured': True,
                                    'status': 200, 'redirects': []},
            'https://example.org/a/': {'url': 'https://example.org/a/', 'captured': True,
                                      'status': None, 'error': 'timeout'},
            'https://example.org/b/': {'url': 'https://example.org/b/', 'captured': False,
                                      'status': None},
        }
        audit.page_checks({}, pages)
        _, dims = audit.score(pages, {})
        self.assertTrue(dims['url_health']['measured'])
        self.assertEqual(dims['url_health']['checked'], 2)
        self.assertEqual(dims['url_health']['score'], 125)
        self.assertEqual([i['code'] for i in audit.issues], ['URL_FETCH_ERROR'])

    def test_missing_snapshot_pages_remain_unmeasured(self):
        audit = engine.Audit('https://example.org', None, headings=False)
        pages = {'https://example.org/': {'captured': False, 'status': None}}
        audit.orphans = None
        _, dims = audit.score(pages, {})
        self.assertFalse(dims['url_health']['measured'])
        self.assertIsNone(dims['url_health']['score'])

    def test_verify_rejects_all_unavailable_pages_offline(self):
        base = 'https://example.org'
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[1]) as directory:
            snap = Path(directory)
            resources = {
                '/robots.txt': 'User-agent: *\nDisallow:\nSitemap: ' + base + '/sitemap.xml\n',
                '/sitemap.xml': '<urlset><url><loc>' + base + '/</loc></url>'
                                '<url><loc>' + base + '/a/</loc></url></urlset>',
                '/llms.txt': '# Site\n\n> Resumo.\n\n## Páginas\n'
                             '- [Início](' + base + '/): Página inicial\n'
                             '- [Artigo](' + base + '/a/): Artigo completo\n',
                '/llms-full.txt': '# Site\n\nTexto integral.',
            }
            manifest = {}
            for index, (path, body) in enumerate(resources.items()):
                name = f'resource{index}'
                (snap / name).write_text(body, encoding='utf-8')
                manifest[base + path] = {'status': 200, 'file': name}
            for status in (None, 503):
                with self.subTest(status=status):
                    manifest[base + '/'] = {'status': status}
                    manifest[base + '/a/'] = {'status': status}
                    (snap / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), 'verify', base, '--snapshot', str(snap),
                         '--no-headings', '--min-score', '800', '--json', str(snap / 'report.json')],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                    report = json.loads((snap / 'report.json').read_text(encoding='utf-8'))
                    self.assertLess(report['score'], 800)
                    self.assertEqual(report['dimensions']['url_health']['score'], 0)
                    self.assertEqual(report['dimensions']['url_health']['checked'], 2)
                    code = 'URL_FETCH_ERROR' if status is None else 'URL_ERROR_STATUS'
                    self.assertEqual(sum(i['code'] == code for i in report['issues']), 2)


if __name__ == '__main__':
    unittest.main()
