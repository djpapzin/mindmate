"""Offline regression tests for coherent Render service exports."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'pull_render_env.py'
spec = importlib.util.spec_from_file_location('pull_render_env', SCRIPT)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def config(label, **optional):
    return {'TELEGRAM_BOT_TOKEN': f'{label}-token',
            'MINDMATE_OPENROUTER_API_KEY': f'{label}-router', **optional}


class RenderExportTests(unittest.TestCase):
    def run_export(self, responses, services=None, inherited=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / '.env'
            output.write_text('existing configuration\n')
            args = [str(SCRIPT), '--out', str(output)]
            for service in services or []:
                args += ['--service-id', service]
            logs = io.StringIO()
            env = {'RENDER_API_KEY': 'dummy-api-key', **(inherited or {})}
            with patch.dict(os.environ, env, clear=True), patch.object(sys, 'argv', args), \
                    patch.object(exporter, 'fetch_env_vars', side_effect=responses) as fetch, \
                    contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
                result = exporter.main()
            return result, output.read_text(), fetch.call_args_list, logs.getvalue(), output.stat().st_mode & 0o777

    def test_first_complete_service_wins_without_querying_staging(self):
        result, text, calls, _, mode = self.run_export([config('prod', DATABASE_URL='prod-db')])
        self.assertEqual(result, 0)
        self.assertIn('DATABASE_URL=prod-db\n', text)
        self.assertEqual([call.args[1] for call in calls], [exporter.DEFAULT_SERVICE_IDS[0]])
        self.assertEqual(mode, 0o600)

    def test_incomplete_production_is_discarded_as_a_whole(self):
        result, text, calls, _, _ = self.run_export([
            {'TELEGRAM_BOT_TOKEN': 'prod-token', 'DATABASE_URL': 'prod-db', 'REDIS_URL': 'prod-redis'},
            config('stage', NEON_MINDMATE_DB_URL='stage-db')])
        self.assertEqual(result, 0)
        self.assertIn('TELEGRAM_BOT_TOKEN=stage-token\n', text)
        self.assertIn('NEON_MINDMATE_DB_URL=stage-db\n', text)
        self.assertNotIn('prod', text)
        self.assertNotIn('\nDATABASE_URL=', text)
        self.assertNotIn('\nREDIS_URL=', text)
        self.assertEqual(len(calls), 2)

    def test_complementary_incomplete_services_cannot_form_valid_config(self):
        result, text, _, _, _ = self.run_export([
            {'TELEGRAM_BOT_TOKEN': 'prod-token'},
            {'MINDMATE_OPENROUTER_API_KEY': 'stage-router', 'DATABASE_URL': 'stage-db'}])
        self.assertEqual(result, 1)
        self.assertEqual(text, 'existing configuration\n')

    def test_missing_or_blank_required_values_preserve_output(self):
        for key in exporter.REQUIRED_KEYS:
            for value in (None, '', '  '):
                with self.subTest(key=key, value=value):
                    candidate = config('prod')
                    if value is None:
                        del candidate[key]
                    else:
                        candidate[key] = value
                    result, text, calls, _, _ = self.run_export([candidate], ['prod-only'])
                    self.assertEqual(result, 1)
                    self.assertEqual(text, 'existing configuration\n')
                    self.assertEqual(len(calls), 1)

    def test_explicit_service_order_is_respected(self):
        result, text, calls, _, _ = self.run_export([{}, config('chosen')], ['custom-a', 'custom-b'])
        self.assertEqual(result, 0)
        self.assertEqual([call.args[1] for call in calls], ['custom-a', 'custom-b'])
        self.assertIn('TELEGRAM_BOT_TOKEN=chosen-token\n', text)

    def test_fetch_failure_falls_back_without_leaking_exception(self):
        result, _, calls, logs, _ = self.run_export([
            RuntimeError('sensitive-response-value'), config('stage')])
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 2)
        self.assertNotIn('sensitive-response-value', logs)
        self.assertNotIn('stage-token', logs)
        self.assertNotIn('dummy-api-key', logs)

    def test_all_fetch_failures_preserve_output(self):
        result, text, _, _, _ = self.run_export([RuntimeError(), RuntimeError()])
        self.assertEqual(result, 1)
        self.assertEqual(text, 'existing configuration\n')

    def test_inherited_environment_is_neither_exported_nor_modified(self):
        inherited = {'DATABASE_URL': 'unrelated-db', 'REDIS_URL': 'unrelated-redis',
                     'TELEGRAM_BOT_TOKEN': 'unrelated-token', 'RENDER_EXTERNAL_URL': 'https://example.invalid'}
        before = dict(os.environ)
        result, text, _, _, _ = self.run_export([config('prod')], inherited=inherited)
        self.assertEqual(result, 0)
        self.assertNotIn('unrelated', text)
        self.assertNotIn('\nRENDER_EXTERNAL_URL=', text)
        self.assertEqual(dict(os.environ), before)

    def test_fetch_filters_other_secrets_and_webhook_url(self):
        response = Mock(status_code=200)
        values = config('prod', DATABASE_URL='prod-db', RENDER_EXTERNAL_URL='https://example.invalid',
                        RENDER_API_KEY='should-not-export')
        response.json.return_value = [{'envVar': {'key': k, 'value': v}} for k, v in values.items()]
        with patch.object(exporter.requests, 'get', return_value=response):
            fetched = exporter.fetch_env_vars('dummy-key', 'prod')
        self.assertEqual(fetched, config('prod', DATABASE_URL='prod-db'))


if __name__ == '__main__':
    unittest.main()
