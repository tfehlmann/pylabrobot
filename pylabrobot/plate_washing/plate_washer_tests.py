"""Tests for PlateWasher frontend.

Following TDD methodology: These tests are written FIRST, before implementation.
"""

import unittest

from pylabrobot.plate_washing.backend import PlateWasherBackend
from pylabrobot.plate_washing.plate_washer import PlateWasher


class MockPlateWasherBackend(PlateWasherBackend):
  """A mock backend for testing the PlateWasher frontend."""

  def __init__(self):
    super().__init__()
    self.setup_called = False
    self.stop_called = False
    self.aspirate_calls: list[dict] = []
    self.dispense_calls: list[dict] = []
    self.wash_calls: list[dict] = []
    self.prime_calls: list[dict] = []
    self.shake_calls: list[dict] = []

  async def setup(self) -> None:
    self.setup_called = True

  async def stop(self) -> None:
    self.stop_called = True

  async def aspirate(
    self,
    volume: float | None = None,
    flow_rate: int | None = None,
  ) -> None:
    self.aspirate_calls.append({"volume": volume, "flow_rate": flow_rate})

  async def dispense(
    self,
    volume: float,
    buffer: str = "A",
    flow_rate: int = 5,
  ) -> None:
    self.dispense_calls.append(
      {
        "volume": volume,
        "buffer": buffer,
        "flow_rate": flow_rate,
      }
    )

  async def wash(
    self,
    cycles: int = 1,
    dispense_volume: float = 300.0,
    soak_time: float = 0.0,
    final_aspirate: bool = True,
    buffer: str = "A",
  ) -> None:
    self.wash_calls.append(
      {
        "cycles": cycles,
        "dispense_volume": dispense_volume,
        "soak_time": soak_time,
        "final_aspirate": final_aspirate,
        "buffer": buffer,
      }
    )

  async def prime(
    self,
    buffer: str = "A",
    volume: float = 1000.0,
  ) -> None:
    self.prime_calls.append({"buffer": buffer, "volume": volume})

  async def shake(
    self,
    duration: float,
    intensity: str = "medium",
    shake_type: str = "linear",
  ) -> None:
    self.shake_calls.append(
      {
        "duration": duration,
        "intensity": intensity,
        "shake_type": shake_type,
      }
    )


class TestPlateWasherSetup(unittest.IsolatedAsyncioTestCase):
  """Test PlateWasher setup and teardown."""

  def setUp(self) -> None:
    self.backend = MockPlateWasherBackend()
    self.washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=self.backend,
    )

  async def test_setup_calls_backend_setup(self):
    """Setup should call backend.setup()."""
    await self.washer.setup()
    self.assertTrue(self.backend.setup_called)

  async def test_setup_finished_after_setup(self):
    """setup_finished should be True after setup()."""
    self.assertFalse(self.washer.setup_finished)
    await self.washer.setup()
    self.assertTrue(self.washer.setup_finished)

  async def test_stop_calls_backend_stop(self):
    """Stop should call backend.stop()."""
    await self.washer.setup()
    await self.washer.stop()
    self.assertTrue(self.backend.stop_called)

  async def test_context_manager(self):
    """PlateWasher should work as async context manager."""
    async with self.washer:
      self.assertTrue(self.backend.setup_called)
    self.assertTrue(self.backend.stop_called)


class TestPlateWasherAspirate(unittest.IsolatedAsyncioTestCase):
  """Test PlateWasher aspirate functionality."""

  async def asyncSetUp(self) -> None:
    self.backend = MockPlateWasherBackend()
    self.washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=self.backend,
    )
    await self.washer.setup()

  async def asyncTearDown(self) -> None:
    await self.washer.stop()

  async def test_aspirate_requires_setup(self):
    """Aspirate should raise if setup not called."""
    new_washer = PlateWasher(
      name="new_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=MockPlateWasherBackend(),
    )
    with self.assertRaises(RuntimeError):
      await new_washer.aspirate()

  async def test_aspirate_default_params(self):
    """Aspirate with default parameters."""
    await self.washer.aspirate()
    self.assertEqual(len(self.backend.aspirate_calls), 1)
    self.assertEqual(self.backend.aspirate_calls[0]["volume"], None)
    self.assertEqual(self.backend.aspirate_calls[0]["flow_rate"], None)

  async def test_aspirate_with_volume(self):
    """Aspirate with specific volume."""
    await self.washer.aspirate(volume=100.0)
    self.assertEqual(self.backend.aspirate_calls[0]["volume"], 100.0)

  async def test_aspirate_with_flow_rate(self):
    """Aspirate with specific flow rate."""
    await self.washer.aspirate(flow_rate=5)
    self.assertEqual(self.backend.aspirate_calls[0]["flow_rate"], 5)


class TestPlateWasherDispense(unittest.IsolatedAsyncioTestCase):
  """Test PlateWasher dispense functionality."""

  async def asyncSetUp(self) -> None:
    self.backend = MockPlateWasherBackend()
    self.washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=self.backend,
    )
    await self.washer.setup()

  async def asyncTearDown(self) -> None:
    await self.washer.stop()

  async def test_dispense_requires_setup(self):
    """Dispense should raise if setup not called."""
    new_washer = PlateWasher(
      name="new_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=MockPlateWasherBackend(),
    )
    with self.assertRaises(RuntimeError):
      await new_washer.dispense(volume=100.0)

  async def test_dispense_with_volume(self):
    """Dispense with specific volume."""
    await self.washer.dispense(volume=300.0)
    self.assertEqual(len(self.backend.dispense_calls), 1)
    self.assertEqual(self.backend.dispense_calls[0]["volume"], 300.0)
    self.assertEqual(self.backend.dispense_calls[0]["buffer"], "A")
    self.assertEqual(self.backend.dispense_calls[0]["flow_rate"], 5)

  async def test_dispense_with_buffer(self):
    """Dispense from specific buffer."""
    await self.washer.dispense(volume=200.0, buffer="B")
    self.assertEqual(self.backend.dispense_calls[0]["buffer"], "B")

  async def test_dispense_with_flow_rate(self):
    """Dispense with specific flow rate."""
    await self.washer.dispense(volume=200.0, flow_rate=9)
    self.assertEqual(self.backend.dispense_calls[0]["flow_rate"], 9)


class TestPlateWasherWash(unittest.IsolatedAsyncioTestCase):
  """Test PlateWasher wash functionality."""

  async def asyncSetUp(self) -> None:
    self.backend = MockPlateWasherBackend()
    self.washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=self.backend,
    )
    await self.washer.setup()

  async def asyncTearDown(self) -> None:
    await self.washer.stop()

  async def test_wash_requires_setup(self):
    """Wash should raise if setup not called."""
    new_washer = PlateWasher(
      name="new_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=MockPlateWasherBackend(),
    )
    with self.assertRaises(RuntimeError):
      await new_washer.wash()

  async def test_wash_default_params(self):
    """Wash with default parameters."""
    await self.washer.wash()
    self.assertEqual(len(self.backend.wash_calls), 1)
    self.assertEqual(self.backend.wash_calls[0]["cycles"], 1)
    self.assertEqual(self.backend.wash_calls[0]["dispense_volume"], 300.0)
    self.assertEqual(self.backend.wash_calls[0]["soak_time"], 0.0)
    self.assertEqual(self.backend.wash_calls[0]["final_aspirate"], True)

  async def test_wash_multiple_cycles(self):
    """Wash with multiple cycles."""
    await self.washer.wash(cycles=3)
    self.assertEqual(self.backend.wash_calls[0]["cycles"], 3)

  async def test_wash_with_soak(self):
    """Wash with soak time."""
    await self.washer.wash(soak_time=30.0)
    self.assertEqual(self.backend.wash_calls[0]["soak_time"], 30.0)

  async def test_wash_no_final_aspirate(self):
    """Wash without final aspirate."""
    await self.washer.wash(final_aspirate=False)
    self.assertEqual(self.backend.wash_calls[0]["final_aspirate"], False)


class TestPlateWasherPrime(unittest.IsolatedAsyncioTestCase):
  """Test PlateWasher prime functionality."""

  async def asyncSetUp(self) -> None:
    self.backend = MockPlateWasherBackend()
    self.washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=self.backend,
    )
    await self.washer.setup()

  async def asyncTearDown(self) -> None:
    await self.washer.stop()

  async def test_prime_requires_setup(self):
    """Prime should raise if setup not called."""
    new_washer = PlateWasher(
      name="new_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=MockPlateWasherBackend(),
    )
    with self.assertRaises(RuntimeError):
      await new_washer.prime()

  async def test_prime_default_params(self):
    """Prime with default parameters."""
    await self.washer.prime()
    self.assertEqual(len(self.backend.prime_calls), 1)
    self.assertEqual(self.backend.prime_calls[0]["buffer"], "A")
    self.assertEqual(self.backend.prime_calls[0]["volume"], 1000.0)

  async def test_prime_specific_buffer(self):
    """Prime specific buffer."""
    await self.washer.prime(buffer="B")
    self.assertEqual(self.backend.prime_calls[0]["buffer"], "B")

  async def test_prime_specific_volume(self):
    """Prime with specific volume."""
    await self.washer.prime(volume=500.0)
    self.assertEqual(self.backend.prime_calls[0]["volume"], 500.0)


class TestPlateWasherShake(unittest.IsolatedAsyncioTestCase):
  """Test PlateWasher shake functionality."""

  async def asyncSetUp(self) -> None:
    self.backend = MockPlateWasherBackend()
    self.washer = PlateWasher(
      name="test_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=self.backend,
    )
    await self.washer.setup()

  async def asyncTearDown(self) -> None:
    await self.washer.stop()

  async def test_shake_requires_setup(self):
    """Shake should raise if setup not called."""
    new_washer = PlateWasher(
      name="new_washer",
      size_x=200.0,
      size_y=200.0,
      size_z=100.0,
      backend=MockPlateWasherBackend(),
    )
    with self.assertRaises(RuntimeError):
      await new_washer.shake(duration=5.0)

  async def test_shake_with_duration(self):
    """Shake for specific duration."""
    await self.washer.shake(duration=10.0)
    self.assertEqual(len(self.backend.shake_calls), 1)
    self.assertEqual(self.backend.shake_calls[0]["duration"], 10.0)
    self.assertEqual(self.backend.shake_calls[0]["intensity"], "medium")

  async def test_shake_with_intensity(self):
    """Shake with specific intensity."""
    await self.washer.shake(duration=5.0, intensity="high")
    self.assertEqual(self.backend.shake_calls[0]["intensity"], "high")


class TestPlateWasherSerialization(unittest.TestCase):
  """Test PlateWasher serialization."""

  def test_backend_serialization(self):
    """Backend should serialize correctly."""
    backend = MockPlateWasherBackend()
    serialized = backend.serialize()
    self.assertEqual(serialized["type"], "MockPlateWasherBackend")


if __name__ == "__main__":
  unittest.main()
