"""BioTek EL406 plate washer backend.

This module provides the backend implementation for the BioTek EL406
plate washer, communicating via FTDI USB serial interface.

Protocol Details:
- Serial: 38400 baud, 8 data bits, 2 stop bits, no parity
- Flow control: disabled (no flow control)
- ACK byte: 0x06
- Commands are binary with little-endian encoding
- Read timeout: 15000ms, Write timeout: 5000ms

Binary Command Structure:
  [0]     Step type byte
  [1-2]   Volume (ushort, little-endian)
  [3]     Valve byte (A=0, B=1, etc)
  [4]     Flow rate
  [5]     Offset X (sbyte)
  [6-7]   Offset Z (short, little-endian)
  ... additional parameters
"""

from __future__ import annotations

import asyncio
import logging

try:
  from pylibftdi import Device

  USE_FTDI = True
except ImportError:
  USE_FTDI = False

from pylabrobot.plate_washing.backend import PlateWasherBackend

from .actions import EL406ActionsMixin
from .communication import EL406CommunicationMixin
from .constants import (
  DEFAULT_READ_TIMEOUT,
)
from .enums import EL406PlateType
from .errors import EL406CommunicationError
from .helpers import validate_plate_type
from .queries import EL406QueriesMixin
from .steps import EL406StepsMixin

logger = logging.getLogger("pylabrobot.plate_washing.biotek.el406")


class BioTekEL406Backend(
  EL406CommunicationMixin,
  EL406QueriesMixin,
  EL406ActionsMixin,
  EL406StepsMixin,
  PlateWasherBackend,
):
  """Backend for BioTek EL406 plate washer.

  Communicates with the EL406 via FTDI USB interface.

  Attributes:
    timeout: Default timeout for operations in seconds.
    plate_type: Currently configured plate type.

  Example:
    >>> backend = BioTekEL406Backend()
    >>> washer = PlateWasher(
    ...   name="el406",
    ...   size_x=200, size_y=200, size_z=100,
    ...   backend=backend
    ... )
    >>> await washer.setup()
    >>> await backend.peristaltic_prime(volume=300.0, flow_rate="High")
    >>> await washer.wash(cycles=3)
  """

  def __init__(
    self,
    timeout: float = DEFAULT_READ_TIMEOUT,
    plate_type: EL406PlateType = EL406PlateType.PLATE_96_WELL,
  ) -> None:
    """Initialize the EL406 backend.

    Args:
      timeout: Default timeout for operations in seconds.
      plate_type: Plate type to use for operations.
    """
    super().__init__()
    self.timeout = timeout
    self.plate_type = plate_type
    self.dev = None  # Will be set in setup()
    self._command_lock = asyncio.Lock()  # Protect against concurrent commands

  async def setup(self) -> None:
    """Set up communication with the EL406.

    Configures the FTDI USB interface with the correct parameters:
    - 38400 baud
    - 8 data bits, 2 stop bits, no parity (8N2)
    - No flow control (disabled)

    Raises:
      RuntimeError: If pylibftdi is not installed or communication fails.
    """
    logger.info("BioTekEL406Backend setting up")
    logger.info("  Timeout: %.1f seconds", self.timeout)
    logger.info("  Plate type: %s", self.plate_type.name if self.plate_type else "not set")

    if not USE_FTDI:
      raise RuntimeError(
        "pylibftdi is not installed. " "Run `pip install pylibftdi` to use the EL406 backend."
      )

    # Open FTDI device
    logger.debug("Opening FTDI device...")
    try:
      self.dev = Device(lazy_open=True)
      self.dev.open()
    except Exception as e:
      raise EL406CommunicationError(
        f"Failed to open FTDI device: {e}. Check USB connection and that no other program has the device open.",
        operation="open",
        original_error=e,
      ) from e
    logger.info("  FTDI device opened successfully")

    # Configure serial parameters
    logger.debug("Configuring serial parameters...")
    try:
      self.dev.baudrate = 38400
      self.dev.ftdi_fn.ftdi_set_line_property(8, 2, 0)  # 8 data bits, 2 stop bits, no parity
      logger.info("  Serial: 38400 baud, 8N2")

      # Flow control: NONE
      SIO_DISABLE_FLOW_CTRL = 0x0
      self.dev.ftdi_fn.ftdi_setflowctrl(SIO_DISABLE_FLOW_CTRL)
      logger.info("  Flow control: NONE")

      # Enable RTS and DTR
      self.dev.ftdi_fn.ftdi_setrts(1)
      self.dev.ftdi_fn.ftdi_setdtr(1)
      logger.debug("  RTS and DTR enabled")
    except Exception as e:
      self.dev.close()
      self.dev = None
      raise EL406CommunicationError(
        f"Failed to configure FTDI device: {e}",
        operation="configure",
        original_error=e,
      ) from e

    # Purge buffers
    logger.debug("Purging TX/RX buffers...")
    await self._purge_buffers()

    # Test communication
    logger.info("Testing communication with device...")
    try:
      await self._test_communication()
      logger.info("  Communication test: PASSED")
    except Exception as e:
      logger.error("  Communication test: FAILED - %s", e)
      raise

    logger.info("BioTekEL406Backend setup complete")

  async def stop(self) -> None:
    """Stop communication with the EL406."""
    logger.info("BioTekEL406Backend stopping")
    if self.dev is not None:
      self.dev.close()
      self.dev = None

  def set_plate_type(self, plate_type: EL406PlateType | int) -> None:
    """Set the current plate type."""
    validated_type = validate_plate_type(plate_type)
    self.plate_type = validated_type
    logger.info("Plate type set to: %s", self.plate_type.name)

  def get_plate_type(self) -> EL406PlateType:
    """Get the current plate type."""
    return self.plate_type

  def serialize(self) -> dict:
    """Serialize backend configuration."""
    return {
      **super().serialize(),
      "timeout": self.timeout,
      "plate_type": self.plate_type.value,
    }

