"""EL406 query methods.

This module contains the mixin class for query operations on the
BioTek EL406 plate washer.
"""

from __future__ import annotations

import logging

from .constants import (
  GET_PERISTALTIC_INSTALLED_COMMAND_HIGH,
  GET_PERISTALTIC_INSTALLED_COMMAND_LOW,
  GET_SENSOR_ENABLED_COMMAND,
  GET_SERIAL_NUMBER_COMMAND_HIGH,
  GET_SERIAL_NUMBER_COMMAND_LOW,
  GET_SYRINGE_BOX_INFO_COMMAND,
  GET_SYRINGE_MANIFOLD_COMMAND,
  GET_WASHER_MANIFOLD_COMMAND,
  LONG_READ_TIMEOUT,
  RUN_SELF_CHECK_COMMAND,
)
from .enums import (
  EL406Sensor,
  EL406SyringeManifold,
  EL406WasherManifold,
)

logger = logging.getLogger("pylabrobot.plate_washing.biotek.el406")


class EL406QueriesMixin:
  """Mixin providing query methods for the EL406.

  This mixin provides:
  - Manifold queries (washer, syringe)
  - Serial number query
  - Sensor status query
  - Syringe box info query
  - Peristaltic pump installation query
  - Instrument settings query
  - Self-check query

  Requires:
    self._send_framed_query: Async method for sending framed queries
  """

  async def get_washer_manifold(self) -> EL406WasherManifold:
    """Query the installed washer manifold type."""
    logger.info("Querying washer manifold type")
    response_data = await self._send_framed_query(GET_WASHER_MANIFOLD_COMMAND)
    logger.debug("Washer manifold response data: %s", response_data.hex())
    manifold_byte = response_data[2] if len(response_data) > 2 else response_data[0]

    try:
      manifold = EL406WasherManifold(manifold_byte)
    except ValueError:
      logger.warning("Unknown washer manifold type: %d (0x%02X)", manifold_byte, manifold_byte)
      raise ValueError(
        f"Unknown washer manifold type: {manifold_byte} (0x{manifold_byte:02X}). "
        f"Valid types: {[m.name for m in EL406WasherManifold]}"
      ) from None

    logger.info("Washer manifold installed: %s (0x%02X)", manifold.name, manifold.value)
    return manifold

  async def get_syringe_manifold(self) -> EL406SyringeManifold:
    """Query the installed syringe manifold type."""
    logger.info("Querying syringe manifold type")
    response_data = await self._send_framed_query(GET_SYRINGE_MANIFOLD_COMMAND)
    logger.debug("Syringe manifold response data: %s", response_data.hex())
    manifold_byte = response_data[2] if len(response_data) > 2 else response_data[0]

    try:
      manifold = EL406SyringeManifold(manifold_byte)
    except ValueError:
      logger.warning("Unknown syringe manifold type: %d (0x%02X)", manifold_byte, manifold_byte)
      raise ValueError(
        f"Unknown syringe manifold type: {manifold_byte} (0x{manifold_byte:02X}). "
        f"Valid types: {[m.name for m in EL406SyringeManifold]}"
      ) from None

    logger.info("Syringe manifold installed: %s (0x%02X)", manifold.name, manifold.value)
    return manifold

  async def get_serial_number(self) -> str:
    """Query the product serial number."""
    logger.info("Querying product serial number")
    command_code = (GET_SERIAL_NUMBER_COMMAND_HIGH << 8) | GET_SERIAL_NUMBER_COMMAND_LOW
    response_data = await self._send_framed_query(command_code)
    serial_number = response_data[2:].decode("ascii", errors="ignore").strip().rstrip("\x00")
    logger.info("Product serial number: %s", serial_number)
    return serial_number

  async def get_sensor_enabled(self, sensor: EL406Sensor) -> bool:
    """Query whether a specific sensor is enabled."""
    logger.info("Querying sensor enabled status: %s", sensor.name)
    response_data = await self._send_framed_query(GET_SENSOR_ENABLED_COMMAND, bytes([sensor.value]))
    logger.debug("Sensor enabled response data: %s", response_data.hex())
    enabled_byte = response_data[2] if len(response_data) > 2 else response_data[0]
    enabled = bool(enabled_byte)
    logger.info("Sensor %s enabled: %s", sensor.name, enabled)
    return enabled

  async def get_syringe_box_info(self) -> dict:
    """Get syringe box information."""
    logger.info("Querying syringe box info")
    response_data = await self._send_framed_query(GET_SYRINGE_BOX_INFO_COMMAND)
    logger.debug("Syringe box info response data: %s", response_data.hex())

    box_type = response_data[2] if len(response_data) > 2 else response_data[0]
    box_size = (
      response_data[3]
      if len(response_data) > 3
      else (response_data[1] if len(response_data) > 1 else 0)
    )
    installed = box_type != 0

    info = {
      "box_type": box_type,
      "box_size": box_size,
      "installed": installed,
    }

    logger.info("Syringe box info: %s", info)
    return info

  async def get_peristaltic_installed(self, selector: int) -> bool:
    """Check if a peristaltic pump is installed."""
    if selector < 0 or selector > 1:
      raise ValueError(f"Invalid selector {selector}. Must be 0 (primary) or 1 (secondary).")

    logger.info("Querying peristaltic pump installed: selector=%d", selector)
    command_code = (
      GET_PERISTALTIC_INSTALLED_COMMAND_HIGH << 8
    ) | GET_PERISTALTIC_INSTALLED_COMMAND_LOW
    response_data = await self._send_framed_query(command_code, bytes([selector]))
    logger.debug("Peristaltic installed response data: %s", response_data.hex())

    installed_byte = response_data[2] if len(response_data) > 2 else response_data[0]
    installed = bool(installed_byte)

    logger.info("Peristaltic pump %d installed: %s", selector, installed)
    return installed

  async def get_instrument_settings(self) -> dict:
    """Get current instrument hardware configuration."""
    logger.info("Querying instrument settings from hardware")

    washer_manifold = await self.get_washer_manifold()
    syringe_manifold = await self.get_syringe_manifold()
    syringe_box = await self.get_syringe_box_info()
    peristaltic_1 = await self.get_peristaltic_installed(0)
    peristaltic_2 = await self.get_peristaltic_installed(1)

    settings = {
      "washer_manifold": washer_manifold,
      "syringe_manifold": syringe_manifold,
      "syringe_box": syringe_box,
      "peristaltic_pump_1": peristaltic_1,
      "peristaltic_pump_2": peristaltic_2,
    }

    logger.info("Instrument settings: %s", settings)
    return settings

  async def run_self_check(self) -> dict:
    """Run instrument self-check diagnostics."""
    logger.info("Running instrument self-check")
    response_data = await self._send_framed_query(RUN_SELF_CHECK_COMMAND, timeout=LONG_READ_TIMEOUT)
    logger.debug("Self-check response data: %s", response_data.hex())
    error_code = response_data[2] if len(response_data) > 2 else response_data[0]
    success = error_code == 0

    result = {
      "success": success,
      "error_code": error_code,
      "message": "Self-check passed"
      if success
      else f"Self-check failed (error code: {error_code})",
    }

    logger.info("Self-check result: %s", result["message"])
    return result

