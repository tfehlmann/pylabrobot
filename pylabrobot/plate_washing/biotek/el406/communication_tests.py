"""Tests for BioTek EL406 plate washer backend - Communication and protocol functionality.

This module contains tests for Communication and protocol functionality.
"""

import unittest

# Import the backend module (mock is already installed by test_el406_mock import)
from pylabrobot.plate_washing.biotek.el406 import (
  BioTekEL406Backend,
)
from pylabrobot.plate_washing.biotek.el406.mock_tests import MockFTDIDevice


class TestEL406BackendCommunication(unittest.IsolatedAsyncioTestCase):
  """Test EL406 low-level communication."""

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    # Set up ACK responses for all tests
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_send_command_waits_for_ack(self):
    """Send command should wait for ACK (0x06) response."""
    self.backend.dev.set_read_buffer(b"\x06")
    response = await self.backend._send_command(b"test")

    self.assertEqual(response, b"\x06")
    self.assertEqual(self.backend.dev.written_data[-1], b"test")

  async def test_send_command_timeout_on_no_ack(self):
    """Send command should timeout if no ACK received."""
    self.backend.timeout = 0.1
    self.backend.dev.set_read_buffer(b"")  # No response

    with self.assertRaises(TimeoutError):
      await self.backend._send_command(b"test")


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


class TestGetComPort(unittest.IsolatedAsyncioTestCase):
  """Test get_com_port functionality.

  get_com_port returns the device identifier or port information.
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  def test_get_com_port_returns_string(self):
    """get_com_port should return a string identifier."""
    result = self.backend.get_com_port()
    self.assertIsInstance(result, str)

  def test_get_com_port_returns_device_id_when_connected(self):
    """get_com_port should return device identifier when connected."""
    result = self.backend.get_com_port()
    # Should return something indicating FTDI device
    self.assertIn("FTDI", result)

  def test_get_com_port_returns_none_or_empty_when_not_connected(self):
    """get_com_port should return empty/None when not connected."""
    backend = BioTekEL406Backend()
    # Not setup - no device
    result = backend.get_com_port()
    self.assertEqual(result, "")


class TestTestPort(unittest.IsolatedAsyncioTestCase):
  """Test test_port functionality.

  test_port sends a test communication command on a specific port.
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_test_port_returns_bool(self):
    """test_port should return a boolean."""
    result = await self.backend.test_port("/dev/ttyUSB0")
    self.assertIsInstance(result, bool)

  async def test_test_port_returns_true_on_success(self):
    """test_port should return True when communication succeeds."""
    self.backend.dev.set_read_buffer(b"\x06")
    result = await self.backend.test_port("test_port")
    self.assertTrue(result)

  async def test_test_port_returns_false_on_timeout(self):
    """test_port should return False when communication times out."""
    self.backend.dev.set_read_buffer(b"")  # No response
    result = await self.backend.test_port("test_port")
    self.assertFalse(result)

  async def test_test_port_sends_test_comm_command(self):
    """test_port should send the test communication command (0x73) in framed message."""
    self.backend.dev.set_read_buffer(b"\x06")
    await self.backend.test_port("test_port")

    last_command = self.backend.dev.written_data[-1]
    # Command byte is at position 2 in framed message
    self.assertEqual(last_command[2], 0x73)


# =============================================================================
# INSTRUMENT CONTROL TESTS (TDD - Written FIRST)
#
# These tests cover:
# 3. validate_step(step_type, definition) - Validate step before execution
# 4. run_self_check() - Run instrument self-check
# 5. auto_prime() - Auto-prime all devices
# 6. auto_prime_device(device: int) - Auto-prime specific device
# =============================================================================
