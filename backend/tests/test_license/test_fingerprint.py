"""Tests for license/fingerprint.py"""

from unittest.mock import patch

from license.fingerprint import get_machine_id


class TestGetMachineId:
    def test_returns_32_hex_chars(self):
        mid = get_machine_id()
        assert isinstance(mid, str)
        assert len(mid) == 32
        assert all(c in "0123456789abcdef" for c in mid)

    def test_deterministic(self):
        """Same machine always produces the same ID."""
        assert get_machine_id() == get_machine_id()

    def test_different_hostname_gives_different_id(self):
        import platform
        original = platform.node()
        id1 = get_machine_id()
        with patch("platform.node", return_value="different-host-xyz"):
            id2 = get_machine_id()
        assert id1 != id2

    def test_does_not_crash_on_subprocess_failure(self):
        """Even if system_profiler / reg fails, fingerprint still returns a value."""
        with patch("license.fingerprint._safe_run", return_value=""):
            mid = get_machine_id()
            assert isinstance(mid, str)
            assert len(mid) == 32
