"""Testes do PANDORA PRESS-SUITE Ω, incluindo regressões das correções da integração."""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pandora_press import console, discovery, press  # noqa: E402

SITE = 'https://www.exemplo.com.br'


def new_db(td):
    db = press.connect(str(Path(td) / 't.db'))
    with db:
        db.execute('INSERT INTO authors VALUES (?,?,?,?,?)', ('a', 'Maria Silva', SITE, '', press.now()))
    return db


class PressSuiteTests(unittest.TestCase):
    def test_suite_selftest(self):
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'pandora_press_suite.py'), 'selftest'],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_discovery_provenance_not_published(self):
        with tempfile.TemporaryDirectory() as td:
            db = new_db(td)
            pages = {SITE + '/': '<title>Livro de Maria Silva</title><meta name="description" content="Livro publicado">'}
            discovery.discover(db, 'a', [SITE + '/'], fetcher=lambda u: pages[u], validator=lambda u: u)
            cid = db.execute('SELECT id FROM candidates').fetchone()[0]
            signal = json.loads(db.execute('SELECT payload_json FROM candidate_signals WHERE candidate_id=?', (cid,)).fetchone()[0])
            self.assertEqual(signal['identity_signal'], 'mention')
            press.approve_candidate(db, 'a', cid)
            self.assertNotIn('DISCOVERY', press.export_html(db, 'a'))
            self.assertNotIn('DISCOVERY', json.dumps(press.jsonld(db, 'a'), ensure_ascii=False))
            db.close()

    def test_jsonld_kind_wins_over_keywords(self):
        with tempfile.TemporaryDirectory() as td:
            db = new_db(td)
            ld = json.dumps({'@type': 'Book', 'name': 'X'})
            pages = {SITE + '/': '<title>Sistema editorial</title><script type="application/ld+json">' + ld + '</script>'}
            discovery.discover(db, 'a', [SITE + '/'], fetcher=lambda u: pages[u], validator=lambda u: u)
            self.assertEqual(db.execute('SELECT kind FROM candidates').fetchone()[0], 'book')
            db.close()

    def test_classify_whole_words(self):
        self.assertEqual(discovery.classify({'title': 'Os dois lados da busca', 'excerpt': '', 'url': ''}), 'other')
        self.assertEqual(discovery.classify({'title': 'Preprint com DOI', 'excerpt': '', 'url': ''}), 'paper')

    def test_www_variants_followed(self):
        with tempfile.TemporaryDirectory() as td:
            db = new_db(td)
            pages = {SITE + '/': '<title>Home de Maria Silva</title><a href="https://exemplo.com.br/livro">l</a>',
                     'https://exemplo.com.br/livro': '<title>Livro de Maria Silva</title>'}
            r = discovery.discover(db, 'a', [SITE + '/'], fetcher=lambda u: pages[u], validator=lambda u: u)
            self.assertEqual(r['visited'], 2)
            db.close()

    def test_exports_respect_status_and_event_role(self):
        with tempfile.TemporaryDirectory() as td:
            db = new_db(td)
            with db:
                press.save(db, 'a', {'title': 'Retratado', 'status': 'retracted'})
                press.save(db, 'a', {'title': 'Palestra', 'kind': 'talk', 'event_date': '2026-05-10', 'status': 'verified'})
                press.save(db, 'a', {'title': 'Pendente', 'status': 'pending', 'url': SITE + '/p'})
                press.save(db, 'a', {'title': 'Pendente 2', 'status': 'pending', 'url': SITE + '/p'})
            names = [n.get('name') for n in press.jsonld(db, 'a')['@graph']]
            self.assertNotIn('Retratado', names)
            self.assertNotIn('Retratado', press.export_html(db, 'a'))
            event = next(n for n in press.jsonld(db, 'a')['@graph'] if n['@type'] == 'Event')
            self.assertIn('performer', event); self.assertNotIn('creator', event)
            ids = [n['@id'] for n in press.jsonld(db, 'a')['@graph']]
            self.assertEqual(len(ids), len(set(ids)))
            only = [n.get('name') for n in press.jsonld(db, 'a', ('verified', 'corrected'))['@graph'][1:]]
            self.assertEqual(only, ['Palestra'])
            db.close()

    def test_console_rejects_foreign_host(self):
        with tempfile.TemporaryDirectory() as td:
            db = new_db(td); db.close()
            server = console.Console(('127.0.0.1', 0), str(Path(td) / 't.db'))
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True); t.start()
            try:
                ok = urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=5)
                self.assertEqual(ok.status, 200)
                req = urllib.request.Request(f'http://127.0.0.1:{port}/', headers={'Host': f'evil.example:{port}'})
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=5)
                self.assertEqual(ctx.exception.code, 403)
            finally:
                server.shutdown(); server.server_close()


if __name__ == '__main__':
    unittest.main()
