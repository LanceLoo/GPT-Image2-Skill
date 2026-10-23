"""OpenCode provider contracts: fake configs, mock HTTP, no real credentials."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from openai import OpenAI

from gpt_image_cli import cli
from test_cli import PNG, httpx


class OpenCodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'opencode.jsonc'

    def write_config(self, options=None, modern=False):
        self.config.write_text(json.dumps({
            'providers' if modern else 'provider': {
                'example-images': {'settings' if modern else 'options': options or {
                    'baseURL': 'http://images.invalid/v1', 'apiKey': 'fake-image-key',
                }},
            },
        }), encoding='utf-8')

    def test_jsonc_and_environment_reference(self):
        self.config.write_text('''{
            // A URL containing // must remain intact.
            "provider": {"example-images": {"options": {
                "baseURL": "http://images.invalid/v1/",
                "apiKey": "{env:TEST_IMAGE_KEY}", /* trailing comma */
            }}},
        }''', encoding='utf-8-sig')
        with patch.dict(os.environ, {'TEST_IMAGE_KEY': 'fake-env-key'}):
            self.assertEqual(cli.resolve_opencode_provider('example-images', self.config),
                             ('http://images.invalid/v1', 'fake-env-key'))

    def test_modern_settings(self):
        self.write_config(modern=True)
        self.assertEqual(cli.resolve_opencode_provider('example-images', self.config)[1], 'fake-image-key')

    def test_other_modern_providers_do_not_hide_legacy_provider(self):
        for modern in ({}, {'other-provider': {'settings': {}}}):
            self.write_config()
            config = json.loads(self.config.read_text(encoding='utf-8'))
            config['providers'] = modern
            self.config.write_text(json.dumps(config), encoding='utf-8')
            self.assertEqual(cli.resolve_opencode_provider('example-images', self.config),
                             ('http://images.invalid/v1', 'fake-image-key'))

    def test_missing_provider_error_identifies_file_without_contents(self):
        self.config.write_text('{"providers": {"other": {"apiKey": "fake-secret"}}}', encoding='utf-8')
        with self.assertRaises(ValueError) as error:
            cli.resolve_opencode_provider('example-images', self.config)
        self.assertIn(repr(str(self.config.resolve())), str(error.exception))
        self.assertIn('example-images', str(error.exception))
        self.assertNotIn('fake-secret', str(error.exception))

    def test_global_discovery_and_ambiguity(self):
        self.write_config()
        folder = self.root / 'opencode'
        folder.mkdir()
        (folder / 'opencode.jsonc').write_bytes(self.config.read_bytes())
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.root)}):
            self.assertEqual(cli.resolve_opencode_provider('example-images', None)[1], 'fake-image-key')
            (folder / 'opencode.json').write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError):
                cli.resolve_opencode_provider('example-images', None)

    def test_invalid_config_does_not_leak_source(self):
        for text in ('{"apiKey": "fake-secret" oops}', '[]', '{}'):
            self.config.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError) as error:
                cli.resolve_opencode_provider('example-images', self.config)
            self.assertNotIn('fake-secret', str(error.exception))

    def test_missing_settings_do_not_fall_back(self):
        for options in ({'apiKey': 'fake-secret'}, {'baseURL': 'http://images.invalid/v1'},
                        {'baseURL': 'file:///example', 'apiKey': 'fake-secret'},
                        {'baseURL': 'http://images.invalid/v1', 'apiKey': '{env:MISSING_IMAGE_KEY}'},
                        {'baseURL': 'http://images.invalid/v1', 'apiKey': '{file:secret}'}):
            self.write_config(options)
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'unrelated-key'}, clear=True), \
                    patch.object(cli, 'OpenAI') as constructor, \
                    patch.object(sys, 'argv', ['gpt-image', '-p', 'test', '--opencode-provider',
                                              'example-images', '--opencode-config', str(self.config)]), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(), 2)
                constructor.assert_not_called()

    def test_real_sdk_route_auth_and_output(self):
        self.write_config()
        output = self.root / '中文图片' / 'image.png'
        requests = []

        def respond(request):
            requests.append(request)
            return httpx.Response(200, json={'data': [{'b64_json': base64.b64encode(PNG).decode()}]})

        def client_factory(**kwargs):
            return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond)))

        argv = ['gpt-image', '--opencode-provider', 'example-images', '--opencode-config', str(self.config),
                '--model', 'gpt-image-2', '-p', '一只橘猫', '-f', str(output)]
        with patch.object(sys, 'argv', argv), patch.object(cli, 'OpenAI', side_effect=client_factory), \
                patch.object(cli, '_load_env_chain') as dotenv, \
                patch.dict(os.environ, {'OPENAI_API_KEY': 'wrong-key', 'OPENAI_BASE_URL': 'https://wrong.invalid/v1'}), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(cli.main(), 0)
        dotenv.assert_not_called()
        self.assertEqual(len(requests), 1)
        self.assertEqual(str(requests[0].url), 'http://images.invalid/v1/images/generations')
        self.assertEqual(requests[0].headers['authorization'], 'Bearer fake-image-key')
        self.assertEqual(json.loads(requests[0].content)['model'], 'gpt-image-2')
        self.assertEqual(output.read_bytes(), PNG)
        self.assertIn(str(output), stdout.getvalue())

    def test_gateway_error_body_is_not_printed_or_retried(self):
        self.write_config()
        calls = []

        def respond(request):
            calls.append(request)
            return httpx.Response(403, json={'error': {'message': 'echo fake-image-key'}})

        def client_factory(**kwargs):
            return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond)))

        with patch.object(sys, 'argv', ['gpt-image', '-p', 'test', '--opencode-provider', 'example-images',
                                       '--opencode-config', str(self.config)]), \
                patch.object(cli, 'OpenAI', side_effect=client_factory), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(cli.main(), 1)
        self.assertEqual(len(calls), 1)
        self.assertIn('403', stderr.getvalue())
        self.assertNotIn('fake-image-key', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
