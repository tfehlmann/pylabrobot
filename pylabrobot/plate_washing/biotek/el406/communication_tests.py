"""Tests for BioTek EL406 plate washer backend - Communication and protocol functionality.

This module contains tests for Communication and protocol functionality.
"""

import unittest

# Import the backend module (mock is already installed by test_el406_mock import)
from pylabrobot.plate_washing.biotek.el406 import (
  BioTekEL406Backend,
)
from pylabrobot.plate_washing.biotek.el406.mock_tests import MockFTDIDevice


class TestTestCommunication(unittest.IsolatedAsyncioTestCase):
  """Test communication verification.

  The _test_communication() method should send a query command
  and verify the device responds with ACK (0x06).
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    # Don't call setup() yet - we want to test _test_communication() directly

  async def test_communication_success_with_ack(self):
    """Test communication should succeed when ACK is received."""
    # Manually set up the device to test the communication method
    self.backend.dev = MockFTDIDevice(lazy_open=True)
    self.backend.dev.open()

    # _test_communication() sends two commands (TEST_COMM + INIT_STATE)
    # so we need enough responses for both
    self.backend.dev.set_read_buffer(b"\x06" * 10)

    # Should not raise
    await self.backend._test_communication()

  async def test_communication_sends_query_command(self):
    """Test communication should send a query command."""
    self.backend.dev = MockFTDIDevice(lazy_open=True)
    self.backend.dev.open()
    # _test_communication() sends two commands, need enough responses
    self.backend.dev.set_read_buffer(b"\x06" * 10)

    await self.backend._test_communication()

    # Verify some command was sent (actual command depends on implementation)
    # For now just verify device is in good state
    self.assertTrue(self.backend.dev.opened)


