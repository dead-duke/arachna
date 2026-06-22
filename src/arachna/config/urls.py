"""URL validation for security-sensitive operations.

https:// is always allowed.
http:// is allowed only for hosts resolving to private/loopback IPs.
All other URLs raise ValueError.
"""

import ipaddress
import socket
from urllib.parse import urlparse


def _is_local_host(hostname: str) -> bool:
    """Check if hostname resolves to a loopback or private network address."""
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return True
    try:
        info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _, _, _, _, sockaddr in info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_loopback or ip.is_private:
                return True
    except (OSError, ValueError):
        pass
    return False


def validate_remote_url(url: str) -> str:
    """Validate URL for remote operations. Returns the URL if valid.

    Allows:
    - https:// URLs (always)
    - http:// URLs only for hosts resolving to private/loopback IPs

    Raises ValueError for any other URL scheme or non-local http://.
    """
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return url
    if parsed.scheme != "http":
        raise ValueError(f"Only https:// URLs are allowed. Got: {url}")
    if parsed.hostname is None:
        raise ValueError(f"Cannot parse hostname from URL: {url}")
    if _is_local_host(parsed.hostname):
        return url
    raise ValueError(f"URL must use https:// (or http:// for local hosts only). Got: {url}")
