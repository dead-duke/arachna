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
    if url.startswith("https://"):
        return url
    if not url.startswith("http://"):
        raise ValueError(f"only http:// and https:// URLs are allowed. Got: {url}")
    parsed = urlparse(url)
    hostname = parsed.hostname
    if hostname is None:
        raise ValueError(f"Cannot parse hostname from URL: {url}")
    if _is_local_host(hostname):
        return url
    raise ValueError(f"only https:// or local URLs are allowed. Got: {url}")
