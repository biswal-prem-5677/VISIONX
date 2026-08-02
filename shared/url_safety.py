"""
VisionX — Outbound URL Safety
=================================
Validation for user-supplied outbound URLs (webhooks, IoT devices, API calls).

Why this exists
---------------
Webhook and IoT actions take a URL straight from user configuration and POST to
it from inside the server. Without validation that is a textbook **SSRF**: a
customer (or anyone who can create a rule) points a webhook at
``http://169.254.169.254/latest/meta-data/iam/security-credentials/`` and the
server fetches cloud instance credentials on their behalf, or sweeps the
private network the server sits in.

Tracked as ENGINEERING_REVIEW.md §8.2 A10 / R18, EXECUTION_TRACKER.md DEF-013.

Policy
------
* Scheme must be ``http`` or ``https``.
* Host must resolve, and **no** resolved address may be loopback, private,
  link-local, multicast, reserved, or unspecified.
* An explicit allowlist (``VISIONX_WEBHOOK_ALLOWED_HOSTS``) short-circuits the
  check for operators who deliberately target an internal endpoint.
* Resolution failure is a **rejection**, not a pass. Fail closed.

Note the residual DNS-rebinding window: we validate the addresses resolved at
check time, and ``requests`` resolves again when it connects. Closing that fully
requires pinning the connection to the validated IP; it is out of scope here and
recorded in the tracker.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

from loguru import logger

ALLOWED_SCHEMES = frozenset({"http", "https"})


class UnsafeURLError(ValueError):
    """Raised when an outbound URL fails the SSRF policy."""


def _allowlisted_hosts() -> frozenset[str]:
    """Hosts an operator has explicitly opted into, comma-separated."""
    raw = os.getenv("VISIONX_WEBHOOK_ALLOWED_HOSTS", "")
    return frozenset(h.strip().lower() for h in raw.split(",") if h.strip())


def _is_blocked_address(addr: str) -> bool:
    """Whether an IP literal falls in a range we refuse to contact."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return True  # not parseable → refuse

    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_outbound_url(url: str) -> str:
    """
    Validate a user-supplied outbound URL against the SSRF policy.

    Args:
        url: The URL to validate.

    Returns:
        The URL, unchanged, when it is safe to request.

    Raises:
        UnsafeURLError: if the URL is malformed, uses a disallowed scheme, or
            resolves to a non-public address.
    """
    if not url or not url.strip():
        raise UnsafeURLError("URL is empty")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(
            f"Scheme '{parsed.scheme}' is not allowed (expected http or https)"
        )

    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    if host.lower() in _allowlisted_hosts():
        return url

    try:
        resolved = socket.getaddrinfo(host, parsed.port or 0, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise UnsafeURLError(f"Host '{host}' does not resolve: {e}") from e

    addresses = {info[4][0] for info in resolved}
    if not addresses:
        raise UnsafeURLError(f"Host '{host}' resolved to no addresses")

    for addr in addresses:
        if _is_blocked_address(addr):
            raise UnsafeURLError(
                f"Host '{host}' resolves to a non-public address ({addr}). "
                f"Set VISIONX_WEBHOOK_ALLOWED_HOSTS to override deliberately."
            )

    return url


def is_safe_outbound_url(url: str) -> bool:
    """Non-raising form of :func:`validate_outbound_url`."""
    try:
        validate_outbound_url(url)
        return True
    except UnsafeURLError as e:
        logger.warning(f"Rejected outbound URL: {e}")
        return False
