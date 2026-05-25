from __future__ import annotations

import hashlib
import hmac


def is_valid_signature(secret: str, payload: bytes, signature_header: str) -> bool:
    if not secret:
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    sent_signature = signature_header.split("=", maxsplit=1)[1].strip()
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sent_signature)
