"""PlateWasher frontend class.

This module provides the user-facing API for plate washers.
"""

from __future__ import annotations

from pylabrobot.machines.machine import Machine, need_setup_finished
from pylabrobot.plate_washing.backend import PlateWasherBackend
from pylabrobot.resources import Resource


class PlateWasher(Resource, Machine):
  """Frontend class for plate washers.

  Plate washers are devices that automate the washing of microplates.
  This class provides a high-level API for controlling plate washers,
  with the actual hardware communication handled by backend classes.

  Example:
    >>> from pylabrobot.plate_washing import PlateWasher
    >>> from pylabrobot.plate_washing.biotek import BioTekEL406Backend
    >>> washer = PlateWasher(
    ...   name="washer",
    ...   size_x=200, size_y=200, size_z=100,
    ...   backend=BioTekEL406Backend()
    ... )
    >>> await washer.setup()
    >>> await washer.prime(buffer="A", volume=1000)
    >>> await washer.wash(cycles=3, dispense_volume=300)
    >>> await washer.stop()
  """

  def __init__(
    self,
    name: str,
    size_x: float,
    size_y: float,
    size_z: float,
    backend: PlateWasherBackend,
    category: str | None = None,
    model: str | None = None,
  ) -> None:
    """Initialize a PlateWasher.

    Args:
      name: Unique name for this plate washer.
      size_x: Width of the washer in millimeters.
      size_y: Depth of the washer in millimeters.
      size_z: Height of the washer in millimeters.
      backend: Backend implementation for hardware communication.
      category: Optional category string.
      model: Optional model string.
    """
    Resource.__init__(
      self,
      name=name,
      size_x=size_x,
      size_y=size_y,
      size_z=size_z,
      category=category,
      model=model,
    )
    Machine.__init__(self, backend=backend)
    self.backend: PlateWasherBackend = backend

  @need_setup_finished
  async def aspirate(
    self,
    volume: float | None = None,
    flow_rate: int | None = None,
  ) -> None:
    """Aspirate liquid from all wells.

    Args:
      volume: Volume to aspirate in microliters. If None, aspirate
        until wells are empty.
      flow_rate: Aspiration flow rate (device-specific scale).
    """
    await self.backend.aspirate(volume=volume, flow_rate=flow_rate)

  @need_setup_finished
  async def dispense(
    self,
    volume: float,
    buffer: str = "A",
    flow_rate: int = 5,
  ) -> None:
    """Dispense liquid to all wells.

    Args:
      volume: Volume to dispense in microliters.
      buffer: Buffer valve selection (A, B, C, D, etc.).
      flow_rate: Dispense flow rate (device-specific scale).
    """
    await self.backend.dispense(volume=volume, buffer=buffer, flow_rate=flow_rate)

  @need_setup_finished
  async def wash(
    self,
    cycles: int = 1,
    dispense_volume: float = 300.0,
    soak_time: float = 0.0,
    final_aspirate: bool = True,
    buffer: str = "A",
  ) -> None:
    """Perform wash cycles.

    A wash cycle consists of:
    1. Dispense buffer to all wells
    2. Optional soak (wait)
    3. Aspirate liquid from all wells

    Args:
      cycles: Number of wash cycles to perform.
      dispense_volume: Volume to dispense per cycle in microliters.
      soak_time: Time to soak between dispense and aspirate in seconds.
      final_aspirate: Whether to perform a final aspirate after last cycle.
      buffer: Buffer valve selection (A, B, C, D, etc.).
    """
    await self.backend.wash(
      cycles=cycles,
      dispense_volume=dispense_volume,
      soak_time=soak_time,
      final_aspirate=final_aspirate,
      buffer=buffer,
    )

  @need_setup_finished
  async def prime(
    self,
    buffer: str = "A",
    volume: float = 1000.0,
  ) -> None:
    """Prime the fluid lines.

    Priming fills the tubing with buffer to remove air bubbles.

    Args:
      buffer: Buffer valve to prime (A, B, C, D, etc.).
      volume: Volume to prime in microliters.
    """
    await self.backend.prime(buffer=buffer, volume=volume)

  @need_setup_finished
  async def shake(
    self,
    duration: float,
    intensity: str = "medium",
    shake_type: str = "linear",
  ) -> None:
    """Shake the plate.

    Note: Not all plate washers support shaking.

    Args:
      duration: Shake duration in seconds.
      intensity: Shake intensity (low, medium, high, or variable).
      shake_type: Type of shaking motion (linear, orbital, x-axis, y-axis).

    Raises:
      NotImplementedError: If the washer does not support shaking.
    """
    await self.backend.shake(
      duration=duration,
      intensity=intensity,
      shake_type=shake_type,
    )
