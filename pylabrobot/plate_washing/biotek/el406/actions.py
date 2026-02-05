"""EL406 action and control methods.

This module contains the mixin class for action/control operations on the
BioTek EL406 plate washer (reset, home, pause, resume, etc.).
"""

from __future__ import annotations

import logging

from .constants import (
  ABORT_COMMAND,
  AUTO_PRIME_DEVICE_COMMAND,
  END_OF_BATCH_COMMAND,
  HOME_VERIFY_MOTORS_COMMAND,
  LONG_READ_TIMEOUT,
  PAUSE_COMMAND,
  RESET_COMMAND,
  RESUME_COMMAND,
  SET_WASHER_MANIFOLD_COMMAND,
  VACUUM_PUMP_CONTROL_COMMAND,
)
from .enums import (
  EL406Motor,
  EL406MotorHomeType,
  EL406StepType,
  EL406WasherManifold,
)
from .protocol import build_framed_message

logger = logging.getLogger("pylabrobot.plate_washing.biotek.el406")


class EL406ActionsMixin:
  """Mixin providing action/control methods for the EL406.

  This mixin provides:
  - Abort, pause, resume operations
  - Reset instrument
  - Home/verify motors
  - Vacuum pump control
  - End-of-batch operations
  - Auto-prime operations
  - Set washer manifold

  Requires:
    self._send_framed_command: Async method for sending framed commands
    self._send_action_command: Async method for sending action commands
  """

  async def abort(
    self,
    step_type: EL406StepType | None = None,
  ) -> None:
    """Abort a running operation.

    Args:
      step_type: Optional step type to abort. If None, aborts current operation.

    Raises:
      RuntimeError: If device not initialized.
      TimeoutError: If timeout waiting for ACK response.
    """
    logger.info(
      "Aborting %s",
      f"step type {step_type.name}" if step_type is not None else "current operation",
    )

    step_type_value = step_type.value if step_type is not None else 0
    data = bytes([step_type_value])
    framed_command = build_framed_message(ABORT_COMMAND, data)
    await self._send_framed_command(framed_command)

  async def pause(self) -> None:
    """Pause a running operation."""
    logger.info("Pausing operation")
    framed_command = build_framed_message(PAUSE_COMMAND)
    await self._send_framed_command(framed_command)

  async def resume(self) -> None:
    """Resume a paused operation."""
    logger.info("Resuming operation")
    framed_command = build_framed_message(RESUME_COMMAND)
    await self._send_framed_command(framed_command)

  async def reset(self) -> None:
    """Reset the instrument to a known state."""
    logger.info("Resetting instrument")
    framed_command = build_framed_message(RESET_COMMAND)
    await self._send_action_command(framed_command, timeout=LONG_READ_TIMEOUT)
    logger.info("Instrument reset complete")

  async def perform_end_of_batch(self) -> None:
    """Perform end-of-batch activities - sends completion marker.

    NOTE: This command (140) is just a completion marker and does NOT:
    - Stop the pump
    - Home the syringes

    For a complete cleanup after a protocol, use cleanup_after_protocol() instead,
    or manually call:
    1. set_vacuum_pump(False) - to stop the pump
    2. home_motors() - to return syringes to home position
    """
    logger.info("Performing end-of-batch activities (completion marker)")
    framed_command = build_framed_message(END_OF_BATCH_COMMAND)
    await self._send_action_command(framed_command, timeout=60.0)
    logger.info("End-of-batch marker sent")

  async def cleanup_after_protocol(self) -> None:
    """Complete cleanup after running a protocol.

    This method performs the full cleanup sequence that the original BioTek
    software does after all protocol steps complete:
    1. Stop the vacuum/peristaltic pump
    2. Home the syringes (XYZ motors)
    3. Send end-of-batch completion marker

    This is the recommended way to end a protocol run.

    Example:
      >>> # Run protocol steps
      >>> await backend.syringe_prime("A", 1000, 5, 2)
      >>> await backend.syringe_prime("B", 1000, 5, 2)
      >>> # Then cleanup
      >>> await backend.cleanup_after_protocol()
    """
    logger.info("Starting post-protocol cleanup")

    # Step 1: Stop the pump
    logger.info("  Stopping vacuum pump...")
    await self.set_vacuum_pump(False)

    # Step 2: Home syringes
    logger.info("  Homing motors...")
    await self.home_motors(EL406MotorHomeType.HOME_XYZ_MOTORS)

    # Step 3: Send end-of-batch marker
    logger.info("  Sending end-of-batch marker...")
    await self.perform_end_of_batch()

    logger.info("Post-protocol cleanup complete")

  async def set_vacuum_pump(self, enabled: bool) -> None:
    """Control the vacuum/peristaltic pump on or off.

    This sends command 299 (LeaveVacuumPumpOn) to control the pump state.
    CRITICAL: After syringe_prime or other pump operations, you MUST call
    this with enabled=False to stop the pump.

    Args:
      enabled: True to turn pump ON, False to turn pump OFF.

    Raises:
      RuntimeError: If device not initialized.
      TimeoutError: If timeout waiting for response.

    Example:
      >>> # After syringe prime, stop the pump
      >>> await backend.syringe_prime("A", 1000, 5, 2)
      >>> await backend.set_vacuum_pump(False)  # STOP THE PUMP
      >>> await backend.home_motors(EL406MotorHomeType.HOME_XYZ_MOTORS)
    """
    state_str = "ON" if enabled else "OFF"
    logger.info("Setting vacuum pump: %s", state_str)

    # Command 299 with 2-byte parameter (little-endian short): 1=on, 0=off
    state_value = 1 if enabled else 0
    data = bytes([state_value & 0xFF, (state_value >> 8) & 0xFF])  # Low byte, high byte
    framed_command = build_framed_message(VACUUM_PUMP_CONTROL_COMMAND, data)
    await self._send_framed_command(framed_command)
    logger.info("Vacuum pump set to %s", state_str)

  async def home_motors(
    self,
    home_type: EL406MotorHomeType,
    motor: EL406Motor | None = None,
  ) -> None:
    """Home or verify motor positions."""
    logger.info(
      "Home/verify motors: type=%s, motor=%s",
      home_type.name,
      motor.name if motor is not None else "default(0)",
    )

    motor_num = motor.value if motor is not None else 0
    data = bytes([home_type.value, motor_num])
    framed_command = build_framed_message(HOME_VERIFY_MOTORS_COMMAND, data)
    await self._send_action_command(framed_command, timeout=120.0)
    logger.info("Motors homed")

  async def set_washer_manifold(self, manifold: EL406WasherManifold) -> None:
    """Set the washer manifold type."""
    logger.info("Setting washer manifold to: %s", manifold.name)
    data = bytes([manifold.value])
    framed_command = build_framed_message(SET_WASHER_MANIFOLD_COMMAND, data)
    await self._send_framed_command(framed_command)
    logger.info("Washer manifold set to: %s", manifold.name)

  async def auto_prime(self) -> None:
    """Auto-prime all fluid devices."""
    logger.info("Auto-priming all devices")
    for device in [1, 2, 3]:
      await self.auto_prime_device(device)
    logger.info("Auto-prime complete")

  async def auto_prime_device(self, device: int) -> None:
    """Auto-prime a specific fluid device."""
    if device < 0 or device > 3:
      raise ValueError(f"Invalid device number {device}. Must be 0-3.")

    logger.info("Auto-priming device %d", device)
    data = bytes([device & 0xFF])
    framed_command = build_framed_message(AUTO_PRIME_DEVICE_COMMAND, data)
    await self._send_action_command(framed_command, timeout=LONG_READ_TIMEOUT)
    logger.info("Device %d primed", device)

  # =========================================================================
  # COMMAND BUILDER METHODS
  # =========================================================================

  def _build_abort_command(
    self,
    step_type: EL406StepType | None = None,
  ) -> bytes:
    """Build abort command bytes.

    Protocol format for abort:
      [0]   Command byte: 0x89 (137)
      [1]   Step type: byte (0 = abort current operation)

    Args:
      step_type: Step type to abort. If None, uses 0 (current operation).

    Returns:
      Command bytes.
    """
    step_type_value = step_type.value if step_type is not None else 0
    return bytes([ABORT_COMMAND, step_type_value])

  def _build_pause_command(self) -> bytes:
    """Build pause command bytes.

    Protocol format for pause:
      [0]   Command byte: 0x8A (138)

    Returns:
      Command bytes.
    """
    return bytes([PAUSE_COMMAND])

  def _build_resume_command(self) -> bytes:
    """Build resume command bytes.

    Protocol format for resume:
      [0]   Command byte: 0x8B (139)

    Returns:
      Command bytes.
    """
    return bytes([RESUME_COMMAND])

  def _build_reset_command(self) -> bytes:
    """Build reset command bytes.

    Protocol format for reset:
      [0]   Command byte: 0x70 (112)

    Returns:
      Command bytes.
    """
    return bytes([RESET_COMMAND])

  def _build_home_motors_command(
    self,
    home_type: EL406MotorHomeType,
    motor: EL406Motor | None = None,
  ) -> bytes:
    """Build home/verify motors command bytes.

    Protocol format for HomeVerifyMotors (from n.cs class al):
      [0]   Command byte: 200 (0xC8) - HOME_VERIFY_MOTORS_COMMAND
      [1]   Home type: 1-6 from EL406MotorHomeType
      [2]   Motor number: 0-11 from EL406Motor (default 0)

    Args:
      home_type: Type of homing operation.
      motor: Specific motor to operate on. Defaults to motor 0 if not specified.

    Returns:
      Command bytes.
    """
    motor_num = motor.value if motor is not None else 0

    return bytes(
      [
        HOME_VERIFY_MOTORS_COMMAND,
        home_type.value,
        motor_num,
      ]
    )

  def _build_run_self_check_command(self) -> bytes:
    """Build run self-check command bytes.

    Protocol format for self-check (may need verification with hardware):
      [0]   Command byte: RUN_SELF_CHECK_COMMAND

    Returns:
      Command bytes.
    """
    from .constants import RUN_SELF_CHECK_COMMAND

    return bytes([RUN_SELF_CHECK_COMMAND])

  def _build_auto_prime_device_command(self, device: int) -> bytes:
    """Build auto-prime device command bytes.

    Protocol format for auto-prime device (may need verification with hardware):
      [0]   Command byte: AUTO_PRIME_DEVICE_COMMAND
      [1]   Device number: byte

    Args:
      device: Device number to prime.

    Returns:
      Command bytes.
    """
    return bytes([AUTO_PRIME_DEVICE_COMMAND, device & 0xFF])

  def _build_set_washer_manifold_command(self, manifold: EL406WasherManifold) -> bytes:
    """Build set washer manifold command bytes.

    Protocol format for set washer manifold:
      [0]   Command byte: 0xD9 (217) - SET_WASHER_MANIFOLD_COMMAND
      [1]   Manifold type: byte from EL406WasherManifold enum

    Args:
      manifold: Manifold type to set.

    Returns:
      Command bytes.
    """
    return bytes([SET_WASHER_MANIFOLD_COMMAND, manifold.value])
