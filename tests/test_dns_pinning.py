"""DNS-rebinding pinning: _pinned_dns filters getaddrinfo to validated IPs;
_validated_ips_for re-resolves and blocks private IPs."""
import socket
import unittest
from unittest.mock import patch

from tools.web_fetch import SsrFBlockedError, _pinned_dns, _validated_ips_for


def _fake_getaddrinfo(responses):
    """getaddrinfo stub returning one answer-list per call."""
    calls = {"n": 0}

    def fake(host, *args, **kwargs):
        idx = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))
                for ip in responses[idx]]

    return fake


class TestPinnedDns(unittest.TestCase):
    def test_pinned_dns_filters_rebinding_ip(self):
        # First resolution public (validated), second call rebinding to private.
        fake = _fake_getaddrinfo([["93.184.216.34"], ["93.184.216.34", "192.168.1.5"]])
        with patch("socket.getaddrinfo", fake):
            ips = _validated_ips_for("https://example.com/x", allow_private=False)
            self.assertEqual(ips, ["93.184.216.34"])
            with _pinned_dns("example.com", ips):
                infos = socket.getaddrinfo("example.com", 443)
                # The rebinding private IP must not survive the pin.
                self.assertEqual([i[4][0] for i in infos], ["93.184.216.34"])

    def test_pinned_dns_restores_original(self):
        original = socket.getaddrinfo
        with _pinned_dns("example.com", ["93.184.216.34"]):
            pass
        self.assertIs(socket.getaddrinfo, original)

    def test_validated_ips_for_blocks_private_rebinding(self):
        fake = _fake_getaddrinfo([["93.184.216.34", "10.0.0.7"]])
        with patch("socket.getaddrinfo", fake):
            with self.assertRaises(SsrFBlockedError):
                _validated_ips_for("https://example.com/x", allow_private=False)


if __name__ == "__main__":
    unittest.main()
