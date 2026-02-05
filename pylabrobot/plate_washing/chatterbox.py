"""Chatterbox backend for plate washer simulation and testing.

This backend prints operations to stdout for debugging and testing
without requiring actual hardware.
"""

from __future__ import annotations

import logging

from pylabrobot.plate_washing.backend import PlateWasherBackend

logger = logging.getLogger(__name__)


class PlateWasherChatterboxBackend(PlateWasherBackend):
  """A simulation backend that logs all operations.

  This backend is useful for:
  - Testing without hardware
  - Debugging protocol logic
  - Demonstrating the API

  Example:
    >>> from pylabrobot.plate_washing import PlateWasher, PlateWasherChatterboxBackend
    >>> washer = PlateWasher(
    ...   name="sim_washer",
    ...   size_x=200, size_y=200, size_z=100,
    ...   backend=PlateWasherChatterboxBackend()
    ... )
    >>> await washer.setup()
    Setting up plate washer.
    >>> await washer.wash(cycles=2)
    Washing plate: 2 cycles, 300.0 uL, buffer A
  """

  def __init__(self) -> None:
    """Initialize the chatterbox backend."""
    super().__init__()

  async def setup(self) -> None:
    """Set up the simulated plate washer."""
    logger.info("Setting up plate washer.")
    print("Setting up plate washer.")

  async def stop(self) -> None:
    """Stop the simulated plate washer."""
    logger.info("Stopping plate washer.")
    print("Stopping plate washer.")

  async def aspirate(
    self,
    volume: float | None = None,
    flow_rate: int | None = None,
  ) -> None:
    """Simulate aspirating from all wells."""
    vol_str = f"{volume} uL" if volume is not None else "all"
    rate_str = f", flow rate {flow_rate}" if flow_rate is not None else ""
    msg = f"Aspirating {vol_str}{rate_str}."
    logger.info(msg)
    print(msg)

  async def dispense(
    self,
    volume: float,
    buffer: str = "A",
    flow_rate: int = 5,
  ) -> None:
    """Simulate dispensing to all wells."""
    msg = f"Dispensing {volume} uL from buffer {buffer}, flow rate {flow_rate}."
    logger.info(msg)
    print(msg)

  async def wash(
    self,
    cycles: int = 1,
    dispense_volume: float = 300.0,
    soak_time: float = 0.0,
    final_aspirate: bool = True,
    buffer: str = "A",
  ) -> None:
    """Simulate wash cycles."""
    msg = f"Washing plate: {cycles} cycles, {dispense_volume} uL, buffer {buffer}"
    if soak_time > 0:
      msg += f", soak {soak_time}s"
    if not final_aspirate:
      msg += ", no final aspirate"
    msg += "."
    logger.info(msg)
    print(msg)

  async def prime(
    self,
    buffer: str = "A",
    volume: float = 1000.0,
  ) -> None:
    """Simulate priming fluid lines."""
    msg = f"Priming buffer {buffer} with {volume} uL."
    logger.info(msg)
    print(msg)

  async def shake(
    self,
    duration: float,
    intensity: str = "medium",
    shake_type: str = "linear",
  ) -> None:
    """Simulate shaking the plate."""
    msg = f"Shaking plate: {duration}s, {intensity} intensity, {shake_type} motion."
    logger.info(msg)
    print(msg)
