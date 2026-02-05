"""Abstract base class for plate washer backends.

Plate washers are devices that automate the washing of microplates,
typically used in ELISA, cell-based assays, and other applications.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod

from pylabrobot.machines.backend import MachineBackend


class PlateWasherBackend(MachineBackend, metaclass=ABCMeta):
  """Abstract base class for plate washer backends.

  Plate washers typically support the following operations:
  - Aspirate: Remove liquid from wells
  - Dispense: Add liquid to wells from buffer reservoirs
  - Wash: Combined dispense and aspirate cycles
  - Prime: Fill tubing with buffer
  - Shake: Agitate the plate (optional, not all washers support)

  Subclasses must implement the abstract methods for specific hardware.
  """

  @abstractmethod
  async def setup(self) -> None:
    """Set up the plate washer.

    This should establish connection to the device and configure
    communication parameters.
    """

  @abstractmethod
  async def stop(self) -> None:
    """Stop the plate washer and close connections.

    This should safely close all connections and ensure the device
    is in a safe state.
    """

  @abstractmethod
  async def aspirate(
    self,
    volume: float | None = None,
    flow_rate: int | None = None,
  ) -> None:
    """Aspirate liquid from all wells.

    Args:
      volume: Volume to aspirate in microliters. If None, aspirate
        until wells are empty (device-dependent behavior).
      flow_rate: Aspiration flow rate on device-specific scale (typically 1-9).
    """

  @abstractmethod
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
      flow_rate: Dispense flow rate on device-specific scale (typically 1-9).
    """

  @abstractmethod
  async def wash(
    self,
    cycles: int = 1,
    dispense_volume: float = 300.0,
    soak_time: float = 0.0,
    final_aspirate: bool = True,
    buffer: str = "A",
  ) -> None:
    """Perform a wash cycle (dispense + optional soak + aspirate).

    Args:
      cycles: Number of wash cycles to perform.
      dispense_volume: Volume to dispense per cycle in microliters.
      soak_time: Time to soak between dispense and aspirate in seconds.
      final_aspirate: Whether to perform a final aspirate after last cycle.
      buffer: Buffer valve selection (A, B, C, D, etc.).
    """

  @abstractmethod
  async def prime(
    self,
    buffer: str = "A",
    volume: float = 1000.0,
  ) -> None:
    """Prime the fluid lines.

    Priming fills the tubing with buffer to remove air bubbles
    and ensure consistent dispensing.

    Args:
      buffer: Buffer valve to prime (A, B, C, D, etc.).
      volume: Volume to prime in microliters.
    """

  async def shake(
    self,
    duration: float,
    intensity: str = "medium",
    shake_type: str = "linear",
  ) -> None:
    """Shake the plate.

    This is an optional method - not all plate washers support shaking.
    The default implementation raises NotImplementedError.

    Args:
      duration: Shake duration in seconds.
      intensity: Shake intensity (low, medium, high, or variable).
      shake_type: Type of shaking motion (linear, orbital, x-axis, y-axis).

    Raises:
      NotImplementedError: If the washer does not support shaking.
    """
    raise NotImplementedError("This washer does not support shaking")
