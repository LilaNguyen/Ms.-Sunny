import os
import unittest
from unittest.mock import patch

import nemotron_api


class NemotronClientTests(unittest.TestCase):
    def setUp(self):
        nemotron_api._client = None
        nemotron_api._client_api_key = None

    def tearDown(self):
        nemotron_api._client = None
        nemotron_api._client_api_key = None

    def test_missing_api_key_raises_only_when_client_requested(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "NVIDIA_API_KEY"):
                nemotron_api.get_client()

    def test_supports_nvidia_api_key(self):
        fake_client = object()
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}, clear=True):
            with patch.object(nemotron_api, "OpenAI", return_value=fake_client) as factory:
                self.assertIs(nemotron_api.get_client(), fake_client)
                factory.assert_called_once_with(
                    base_url=nemotron_api.BASE_URL, api_key="test-key"
                )

    def test_supports_legacy_nemotron_api_key(self):
        fake_client = object()
        with patch.dict(os.environ, {"NEMOTRON_API_KEY": "legacy-key"}, clear=True):
            with patch.object(nemotron_api, "OpenAI", return_value=fake_client):
                self.assertIs(nemotron_api.get_client(), fake_client)


if __name__ == "__main__":
    unittest.main()
