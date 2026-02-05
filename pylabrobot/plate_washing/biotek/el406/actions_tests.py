"""Tests for BioTek EL406 plate washer backend - Action methods.

This module contains tests for Action methods.
"""

import unittest

from pylabrobot.plate_washing.biotek.el406 import (
  BioTekEL406Backend,
  EL406Motor,
  EL406MotorHomeType,
  EL406StepType,
  EL406WasherManifold,
)
from pylabrobot.plate_washing.biotek.el406.mock_tests import MockFTDI


class TestEL406BackendAbort(unittest.IsolatedAsyncioTestCase):
  """Test EL406 abort functionality.

  The abort operation cancels a running step.
  - Command byte: 137 (0x89)
  - Accepts a step type parameter (can be 0 for current operation)
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_abort_sends_command(self):
    """Abort should send abort command to device."""
    initial_count = len(self.backend.io.written_data)
    await self.backend.abort()

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_abort_command_byte(self):
    """Abort command should be 137 (0x89) in framed message."""
    await self.backend.abort()

    # Abort sends header + data, so header is at -2
    last_header = self.backend.io.written_data[-2]
    # Command byte is at position 2 in framed message
    self.assertEqual(last_header[2], 0x89)

  async def test_abort_with_step_type(self):
    """Abort should accept optional step type parameter."""
    await self.backend.abort(step_type=EL406StepType.M_WASH)

    # Abort sends header + data, so header is at -2
    last_header = self.backend.io.written_data[-2]
    self.assertEqual(last_header[2], 0x89)

  async def test_abort_without_step_type_uses_zero(self):
    """Abort without step_type should default to 0 (abort current)."""
    await self.backend.abort()

    # Abort sends header + data separately
    last_header = self.backend.io.written_data[-2]
    last_data = self.backend.io.written_data[-1]
    self.assertEqual(last_header[2], 0x89)
    self.assertEqual(last_data[0], 0)  # Default step type = 0

  async def test_abort_raises_when_device_not_initialized(self):
    """Abort should raise RuntimeError if device not initialized."""
    backend = BioTekEL406Backend()
    # Note: no setup() called
    with self.assertRaises(RuntimeError):
      await backend.abort()


class TestEL406BackendPause(unittest.IsolatedAsyncioTestCase):
  """Test EL406 pause functionality.

  The pause operation temporarily halts a running step.
  - Command byte: 138 (0x8A)
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_pause_sends_command(self):
    """Pause should send pause command to device."""
    initial_count = len(self.backend.io.written_data)
    await self.backend.pause()

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_pause_command_byte(self):
    """Pause command should be 138 (0x8A) in framed message."""
    await self.backend.pause()

    # Get the last command sent
    last_command = self.backend.io.written_data[-1]
    # Command byte is at position 2 in framed message
    self.assertEqual(last_command[2], 0x8A)

  async def test_pause_raises_when_device_not_initialized(self):
    """Pause should raise RuntimeError if device not initialized."""
    backend = BioTekEL406Backend()
    # Note: no setup() called
    with self.assertRaises(RuntimeError):
      await backend.pause()

  async def test_pause_raises_on_timeout(self):
    """Pause should raise TimeoutError when device does not respond."""
    self.backend.io.set_read_buffer(b"")  # No ACK response
    with self.assertRaises(TimeoutError):
      await self.backend.pause()

  async def test_pause_resume_sequence(self):
    """Pause followed by resume should work correctly."""
    await self.backend.pause()
    # Verify pause command was sent (command byte at position 2 in framed message)
    pause_cmd = self.backend.io.written_data[-1]
    self.assertEqual(pause_cmd[2], 0x8A)

    await self.backend.resume()
    # Verify resume command was sent after pause (command byte at position 2)
    resume_cmd = self.backend.io.written_data[-1]
    self.assertEqual(resume_cmd[2], 0x8B)


class TestEL406BackendResume(unittest.IsolatedAsyncioTestCase):
  """Test EL406 resume functionality.

  The resume operation continues a paused step.
  - Command byte: 139 (0x8B)
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_resume_sends_command(self):
    """Resume should send resume command to device."""
    initial_count = len(self.backend.io.written_data)
    await self.backend.resume()

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_resume_command_byte(self):
    """Resume command should be 139 (0x8B) in framed message."""
    await self.backend.resume()

    # Get the last command sent
    last_command = self.backend.io.written_data[-1]
    # Command byte is at position 2 in framed message
    self.assertEqual(last_command[2], 0x8B)

  async def test_resume_raises_when_device_not_initialized(self):
    """Resume should raise RuntimeError if device not initialized."""
    backend = BioTekEL406Backend()
    # Note: no setup() called
    with self.assertRaises(RuntimeError):
      await backend.resume()

  async def test_resume_raises_on_timeout(self):
    """Resume should raise TimeoutError when device does not respond."""
    self.backend.io.set_read_buffer(b"")  # No ACK response
    with self.assertRaises(TimeoutError):
      await self.backend.resume()


class TestEL406BackendReset(unittest.IsolatedAsyncioTestCase):
  """Test EL406 reset functionality.

  The reset operation resets the instrument to a known state.
  - Command byte: 112 (0x70)
  - Timeout: 30000ms (30 seconds)
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_reset_sends_command(self):
    """Reset should send reset command to device."""
    initial_count = len(self.backend.io.written_data)
    await self.backend.reset()

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_reset_command_byte(self):
    """Reset command should be 112 (0x70) in framed message."""
    await self.backend.reset()

    # Get the last command sent
    last_command = self.backend.io.written_data[-1]
    # Command byte is at position 2 in framed message
    self.assertEqual(last_command[2], 0x70)

  async def test_reset_raises_when_device_not_initialized(self):
    """Reset should raise RuntimeError if device not initialized."""
    backend = BioTekEL406Backend()
    # Note: no setup() called
    with self.assertRaises(RuntimeError):
      await backend.reset()

  async def test_reset_raises_on_timeout(self):
    """Reset should raise TimeoutError when device does not respond."""
    self.backend.io.set_read_buffer(b"")  # No ACK response
    with self.assertRaises(TimeoutError):
      await self.backend.reset()


class TestEL406BackendHomeMotors(unittest.IsolatedAsyncioTestCase):
  """Test EL406 motor homing functionality.

  The home_motors operation homes and/or verifies motor positions.
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_home_motors_sends_command(self):
    """home_motors should send a command to the device."""


    initial_count = len(self.backend.io.written_data)
    await self.backend.home_motors(
      home_type=EL406MotorHomeType.HOME_MOTOR,
      motor=EL406Motor.CARRIER_X,
    )

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_home_motors_home_all(self):
    """home_motors should work with HOME_XYZ_MOTORS to home all xyz motors."""


    initial_count = len(self.backend.io.written_data)
    await self.backend.home_motors(home_type=EL406MotorHomeType.HOME_XYZ_MOTORS)

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_home_motors_init_all(self):
    """home_motors should work with INIT_ALL_MOTORS."""


    initial_count = len(self.backend.io.written_data)
    await self.backend.home_motors(home_type=EL406MotorHomeType.INIT_ALL_MOTORS)

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_home_motors_verify_motor(self):
    """home_motors should work with VERIFY_MOTOR for specific motor."""


    initial_count = len(self.backend.io.written_data)
    await self.backend.home_motors(
      home_type=EL406MotorHomeType.VERIFY_MOTOR,
      motor=EL406Motor.SYRINGE_A,
    )

    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_home_motors_raises_when_device_not_initialized(self):
    """home_motors should raise RuntimeError if device not initialized."""


    backend = BioTekEL406Backend()
    # Note: no setup() called

    with self.assertRaises(RuntimeError):
      await backend.home_motors(home_type=EL406MotorHomeType.HOME_XYZ_MOTORS)


class TestRunSelfCheck(unittest.IsolatedAsyncioTestCase):
  """Test run_self_check functionality.

  run_self_check runs instrument self-diagnostics.
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_run_self_check_returns_dict(self):
    """run_self_check should return a dictionary with results."""
    self.backend.io.set_read_buffer(b"\x00\x06")  # Success
    result = await self.backend.run_self_check()
    self.assertIsInstance(result, dict)

  async def test_run_self_check_has_success_key(self):
    """run_self_check result should have a success key."""
    self.backend.io.set_read_buffer(b"\x00\x06")
    result = await self.backend.run_self_check()
    self.assertIn("success", result)

  async def test_run_self_check_success_on_valid_response(self):
    """run_self_check should report success when device responds OK."""
    self.backend.io.set_read_buffer(b"\x00\x06")
    result = await self.backend.run_self_check()
    self.assertTrue(result["success"])

  async def test_run_self_check_failure_on_error_response(self):
    """run_self_check should report failure on error response."""
    self.backend.io.set_read_buffer(b"\x01\x06")  # Error code 1
    result = await self.backend.run_self_check()
    self.assertFalse(result["success"])

  async def test_run_self_check_sends_command(self):
    """run_self_check should send a command to the device."""
    initial_count = len(self.backend.io.written_data)
    self.backend.io.set_read_buffer(b"\x00\x06")
    await self.backend.run_self_check()
    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_run_self_check_raises_when_device_not_initialized(self):
    """run_self_check should raise RuntimeError if device not initialized."""
    backend = BioTekEL406Backend()
    with self.assertRaises(RuntimeError):
      await backend.run_self_check()



class TestSetWasherManifold(unittest.IsolatedAsyncioTestCase):
  """Test set_washer_manifold functionality.

  set_washer_manifold configures the washer manifold type.
  Command byte: 0xD9 (217)
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    self.backend.io = MockFTDI()
    await self.backend.setup()
    self.backend.io.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.io is not None:
      await self.backend.stop()

  async def test_set_washer_manifold_sends_command(self):
    """set_washer_manifold should send a command to the device."""
    initial_count = len(self.backend.io.written_data)
    await self.backend.set_washer_manifold(EL406WasherManifold.TUBE_96_DUAL)
    self.assertGreater(len(self.backend.io.written_data), initial_count)

  async def test_set_washer_manifold_sends_correct_command_byte(self):
    """set_washer_manifold should send command byte 0xD9 (217) in framed message."""
    await self.backend.set_washer_manifold(EL406WasherManifold.TUBE_96_DUAL)
    # Command sends header + data, so header is at -2
    last_header = self.backend.io.written_data[-2]
    # Command byte is at position 2 in framed message
    self.assertEqual(last_header[2], 0xD9)

  async def test_set_washer_manifold_includes_manifold_type(self):
    """set_washer_manifold should include manifold type in command data."""
    await self.backend.set_washer_manifold(EL406WasherManifold.TUBE_192)
    # Command sends header + data separately
    last_data = self.backend.io.written_data[-1]
    # Data payload contains the manifold type
    self.assertEqual(last_data[0], EL406WasherManifold.TUBE_192.value)

  async def test_set_washer_manifold_accepts_all_types(self):
    """set_washer_manifold should accept all manifold types."""
    for manifold in EL406WasherManifold:
      self.backend.io.set_read_buffer(b"\x06" * 100)
      # Should not raise
      await self.backend.set_washer_manifold(manifold)

  async def test_set_washer_manifold_raises_when_device_not_initialized(self):
    """set_washer_manifold should raise RuntimeError if device not initialized."""
    backend = BioTekEL406Backend()
    with self.assertRaises(RuntimeError):
      await backend.set_washer_manifold(EL406WasherManifold.TUBE_96_DUAL)


