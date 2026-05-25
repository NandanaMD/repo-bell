from __future__ import annotations

import hashlib
import hmac
import unittest

from app.webhook.signature import is_valid_signature


class SignatureValidationTests(unittest.TestCase):
    def test_valid_signature(self) -> None:
        secret = "my-secret"
        payload = b'{"hello":"world"}'
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        header = f"sha256={digest}"

        self.assertTrue(is_valid_signature(secret, payload, header))

    def test_invalid_signature(self) -> None:
        self.assertFalse(is_valid_signature("secret", b"payload", "sha256=bad"))

    def test_secret_disabled_accepts_any_signature(self) -> None:
        self.assertTrue(is_valid_signature("", b"payload", ""))


if __name__ == "__main__":
    unittest.main()
