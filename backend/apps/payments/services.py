import base64
import hashlib
import hmac
import logging

from django.conf import settings

log = logging.getLogger(__name__)


def validate_hmac(body: bytes, received_hmac: str) -> bool:
    """Validate CloudPayments webhook HMAC-SHA256 signature.

    CloudPayments sends Content-HMAC = base64(HMAC-SHA256(raw_body, api_secret)).
    Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.
    """
    secret = settings.CLOUDPAYMENTS_API_SECRET.encode("utf-8")
    expected = base64.b64encode(
        hmac.new(secret, body, hashlib.sha256).digest()
    ).decode("utf-8")
    return hmac.compare_digest(expected, received_hmac)
