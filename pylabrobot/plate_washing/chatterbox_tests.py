"""Tests for PlateWasherChatterboxBackend.

Following TDD methodology: These tests verify the chatterbox backend
correctly simulates plate washer operations.
"""

import io
import sys
import unittest

from pylabrobot.plate_washing import PlateWasher, PlateWasherChatterboxBackend


class TestChatterboxBackendSetup(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend setup and teardown."""

  async def test_setup_prints_message(self):
    """Setup should print a message."""
    backend = PlateWasherChatterboxBackend()
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await backend.setup()
    finally:
      sys.stdout = sys.__stdout__

    self.assertIn("Setting up plate washer", captured.getvalue())

  async def test_stop_prints_message(self):
    """Stop should print a message."""
    backend = PlateWasherChatterboxBackend()
    await backend.setup()

    captured = io.StringIO()
    sys.stdout = captured
    try:
      await backend.stop()
    finally:
      sys.stdout = sys.__stdout__

    self.assertIn("Stopping plate washer", captured.getvalue())


class TestChatterboxBackendAspirate(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend aspirate functionality."""

  async def asyncSetUp(self):
    self.backend = PlateWasherChatterboxBackend()
    await self.backend.setup()

  async def asyncTearDown(self):
    await self.backend.stop()

  async def test_aspirate_prints_volume(self):
    """Aspirate should print the volume."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.aspirate(volume=100.0)
    finally:
      sys.stdout = sys.__stdout__

    self.assertIn("100", captured.getvalue())
    self.assertIn("uL", captured.getvalue())

  async def test_aspirate_all_prints_all(self):
    """Aspirate without volume should indicate all."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.aspirate()
    finally:
      sys.stdout = sys.__stdout__

    self.assertIn("all", captured.getvalue())

  async def test_aspirate_with_flow_rate_prints_flow_rate(self):
    """Aspirate should print the flow rate when provided."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.aspirate(flow_rate=5)
    finally:
      sys.stdout = sys.__stdout__

    self.assertIn("flow rate", captured.getvalue())
    self.assertIn("5", captured.getvalue())


class TestChatterboxBackendDispense(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend dispense functionality."""

  async def asyncSetUp(self):
    self.backend = PlateWasherChatterboxBackend()
    await self.backend.setup()

  async def asyncTearDown(self):
    await self.backend.stop()

  async def test_dispense_prints_volume_and_buffer(self):
    """Dispense should print volume and buffer."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.dispense(volume=300.0, buffer="B", flow_rate=5)
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("300", output)
    self.assertIn("B", output)
    self.assertIn("flow rate", output)


class TestChatterboxBackendWash(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend wash functionality."""

  async def asyncSetUp(self):
    self.backend = PlateWasherChatterboxBackend()
    await self.backend.setup()

  async def asyncTearDown(self):
    await self.backend.stop()

  async def test_wash_prints_cycles_and_volume(self):
    """Wash should print cycles and volume."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.wash(cycles=3, dispense_volume=250.0)
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("3", output)
    self.assertIn("250", output)

  async def test_wash_with_soak_prints_soak_time(self):
    """Wash with soak time should print soak duration."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.wash(cycles=1, soak_time=30.0)
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("soak", output)
    self.assertIn("30", output)

  async def test_wash_no_final_aspirate_prints_message(self):
    """Wash without final aspirate should indicate that."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.wash(cycles=1, final_aspirate=False)
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("no final aspirate", output)


class TestChatterboxBackendPrime(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend prime functionality."""

  async def asyncSetUp(self):
    self.backend = PlateWasherChatterboxBackend()
    await self.backend.setup()

  async def asyncTearDown(self):
    await self.backend.stop()

  async def test_prime_prints_buffer_and_volume(self):
    """Prime should print buffer and volume."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.prime(buffer="C", volume=500.0)
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("C", output)
    self.assertIn("500", output)


class TestChatterboxBackendShake(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend shake functionality."""

  async def asyncSetUp(self):
    self.backend = PlateWasherChatterboxBackend()
    await self.backend.setup()

  async def asyncTearDown(self):
    await self.backend.stop()

  async def test_shake_prints_duration_and_intensity(self):
    """Shake should print duration and intensity."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.shake(duration=10.0, intensity="high")
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("10", output)
    self.assertIn("high", output)

  async def test_shake_prints_shake_type(self):
    """Shake should print shake type."""
    captured = io.StringIO()
    sys.stdout = captured
    try:
      await self.backend.shake(duration=5.0, shake_type="orbital")
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("orbital", output)


class TestChatterboxWithPlateWasher(unittest.IsolatedAsyncioTestCase):
  """Test chatterbox backend integration with PlateWasher frontend."""

  async def test_full_wash_cycle(self):
    """Test a complete wash cycle through the frontend."""
    backend = PlateWasherChatterboxBackend()
    washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=backend,
    )

    captured = io.StringIO()
    sys.stdout = captured
    try:
      await washer.setup()
      await washer.prime(buffer="A", volume=1000.0)
      await washer.wash(cycles=3, dispense_volume=300.0)
      await washer.stop()
    finally:
      sys.stdout = sys.__stdout__

    output = captured.getvalue()
    self.assertIn("Setting up", output)
    self.assertIn("Priming", output)
    self.assertIn("Washing", output)
    self.assertIn("Stopping", output)


if __name__ == "__main__":
  unittest.main()
