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

    def test_negative_conflicts_respect_level_and_ad_group(self):
        keyword = {'keyword': 'curso grátis', 'campaign': 'Cursos', 'ad_group': 'Online'}
        cases = [
            ({'campaign': 'Cursos', 'ad_group': 'Presencial'}, False),
            ({'campaign': 'Cursos', 'ad_group': 'Online'}, True),
            ({'campaign': 'Outra', 'ad_group': 'Online'}, False),
            ({'campaign': 'Cursos', 'ad_group': 'Presencial', 'level': 'Ad group'}, False),
            ({'campaign': 'Cursos', 'ad_group': 'Online', 'level': 'Grupo de anúncios'}, True),
            ({'campaign': 'Cursos', 'level': 'ad_group'}, False),
            ({'campaign': 'Cursos', 'ad_group': 'Presencial', 'level': 'Campaign'}, True),
            ({'campaign': 'Outra', 'level': 'Campanha'}, False),
            ({'campaign': 'Cursos'}, True),
            ({}, True),
            ({'campaign': 'Outra', 'ad_group': 'Presencial', 'level': 'Account'}, True),
            ({'level': 'Conta'}, True),
        ]
        for scope, expected in cases:
            with self.subTest(scope=scope):
                audit = engine.AdsAudit({})
                audit.data = {'negatives': [{'negative': 'grátis', 'match_type': 'Ampla', **scope}],
                              'keywords': [keyword]}
                audit.gear_negative_conflicts()
                self.assertEqual(bool(audit.findings), expected)
                if expected:
                    self.assertEqual(audit.findings[0].evidence[0].get('ad_group'), 'Online')

    def test_group_negative_does_not_assume_missing_keyword_scope(self):
        for missing in ('campaign', 'ad_group'):
            with self.subTest(missing=missing):
                audit = engine.AdsAudit({})
                keyword = {'keyword': 'curso grátis', 'campaign': 'Cursos', 'ad_group': 'Online'}
                del keyword[missing]
                audit.data = {'negatives': [{'negative': 'grátis', 'campaign': 'Cursos',
                                            'ad_group': 'Online', 'level': 'Ad group'}],
                              'keywords': [keyword]}
                audit.gear_negative_conflicts()
                self.assertEqual(audit.findings, [])

    def test_auction_falls_back_to_own_account_label(self):
        for label in ('Você', 'You', 'Sua conta'):
            for domain in ('', 'absent.example'):
                with self.subTest(label=label, domain=domain):
                    audit = engine.AdsAudit({'own_domain': domain})
                    audit.data = {'auction': [
                        {'domain': label, 'impression_share': '10%', 'position_above': '90%'},
                        {'domain': 'rival.example', 'impression_share': '50%', 'position_above': '0%'},
                    ]}
                    audit.gear_auction()
                    self.assertEqual(len(audit.findings), 1)
                    self.assertEqual([r['domain'] for r in audit.findings[0].evidence], ['rival.example'])

    def test_auction_preserves_configured_domain_or_account_name(self):
        for own_name in ('my.example', 'Minha empresa'):
            with self.subTest(own_name=own_name):
                audit = engine.AdsAudit({'own_domain': own_name})
                audit.data = {'auction': [
                    {'domain': 'Você', 'impression_share': '50%', 'position_above': '0%'},
                    {'domain': own_name, 'impression_share': '10%', 'position_above': '90%'},
                ]}
                audit.gear_auction()
                self.assertEqual([r['domain'] for r in audit.findings[0].evidence], ['Você'])

    def test_auction_without_own_account_uses_position_above_only(self):
        audit = engine.AdsAudit({})
        audit.data = {'auction': [
            {'domain': 'rival.example', 'impression_share': '90%', 'position_above': '0%'},
        ]}
        audit.gear_auction()
        self.assertEqual(audit.findings, [])


if __name__ == '__main__':
    unittest.main()
