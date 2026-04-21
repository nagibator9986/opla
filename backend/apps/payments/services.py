import base64
import hashlib
import hmac
import logging
from urllib.parse import parse_qs

from django.conf import settings

log = logging.getLogger(__name__)


def validate_hmac(body: bytes, received_hmac: str) -> bool:
    """Validate CloudPayments webhook HMAC-SHA256 signature.

    CloudPayments sends Content-HMAC = base64(HMAC-SHA256(raw_body, api_secret)).
    Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.
    """
    if not received_hmac or not settings.CLOUDPAYMENTS_API_SECRET:
        return False
    secret = settings.CLOUDPAYMENTS_API_SECRET.encode("utf-8")
    expected = base64.b64encode(
        hmac.new(secret, body, hashlib.sha256).digest()
    ).decode("utf-8")
    return hmac.compare_digest(expected, received_hmac)


def parse_webhook_body(body: bytes) -> dict[str, str]:
    """Parse CloudPayments webhook body directly from raw bytes.

    We avoid request.POST because DRF/Django request pipelines can reset the
    stream after HMAC has been computed on request.body, which would cause the
    HMAC check and parsed payload to disagree. Parsing the same bytes used for
    HMAC verification eliminates that drift.
    """
    try:
        payload = body.decode("utf-8")
    except UnicodeDecodeError:
        return {}
    parsed = parse_qs(payload, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in parsed.items()}
