"""EL406 shake/soak step methods.

Provides the shake operation and its command builder.
"""

from __future__ import annotations

import logging
from typing import Literal

from ..constants import (
  SHAKE_SOAK_COMMAND,
)
from ..helpers import (
  validate_intensity,
)
from ..protocol import build_framed_message
from ._base import EL406StepsBaseMixin

logger = logging.getLogger("pylabrobot.plate_washing.biotek.el406")


class EL406ShakeStepsMixin(EL406StepsBaseMixin):
  """Mixin for shake/soak step operations."""

  MAX_SHAKE_DURATION = 3599  # 59:59 max (mm:ss format, mm max=59)
  MAX_SOAK_DURATION = 3599  # 59:59 max (mm:ss format, mm max=59)
  AUTO_HOME_THRESHOLD = 60  # GUI forces move-home when total > 60s

  async def shake(
    self,
    duration: int = 0,
    intensity: Literal["Variable", "Slow", "Medium", "Fast"] = "Medium",
    soak_duration: int = 0,
    move_home_first: bool = True,
  ) -> None:
    """Shake the plate with optional soak period.

    Durations are in whole seconds (GUI uses mm:ss picker, max 59:59 each).
    A duration of 0 disables shake. A soak_duration of 0 disables soak.

    Note: The GUI forces move_home_first=True when total time exceeds 60s
    to prevent manifold drip contamination. Our default of True matches this.

    Args:
      duration: Shake duration in seconds (0-3599). 0 to disable shake.
      intensity: Shake intensity - "Variable", "Slow" (3.5 Hz),
                 "Medium" (5 Hz), or "Fast" (8 Hz).
      soak_duration: Soak duration in seconds after shaking (0-3599). 0 to disable.
      move_home_first: Move carrier to home position before shaking (default True).

    Raises:
      ValueError: If parameters are invalid.
    """
    if duration < 0 or duration > self.MAX_SHAKE_DURATION:
      raise ValueError(f"Invalid duration {duration}. Must be 0-{self.MAX_SHAKE_DURATION}.")
    if soak_duration < 0 or soak_duration > self.MAX_SOAK_DURATION:
      raise ValueError(
        f"Invalid soak_duration {soak_duration}. Must be 0-{self.MAX_SOAK_DURATION}."
      )
    if duration == 0 and soak_duration == 0:
      raise ValueError("At least one of duration or soak_duration must be > 0.")
    validate_intensity(intensity)

    shake_enabled = duration > 0

    logger.info(
      "Shake: %ds, %s intensity, move_home=%s, soak=%ds",
      duration,
      intensity,
      move_home_first,
      soak_duration,
    )

    data = self._build_shake_command(
      shake_duration=duration,
      soak_duration=soak_duration,
      intensity=intensity,
      shake_enabled=shake_enabled,
      move_home_first=move_home_first,
    )
    framed_command = build_framed_message(SHAKE_SOAK_COMMAND, data)
    total_timeout = duration + soak_duration + self.timeout
    await self._send_step_command(framed_command, timeout=total_timeout)

  # =========================================================================
  # COMMAND BUILDERS
  # =========================================================================

  def _build_shake_command(
    self,
    shake_duration: int = 0,
    soak_duration: int = 0,
    intensity: str = "medium",
    shake_enabled: bool = True,
    move_home_first: bool = True,
  ) -> bytes:
    """Build shake command bytes.

    Protocol format for shake/soak (12 bytes wire format):

    Field mapping:
      - move_home_first (bool) - combined with shake_enabled for byte[1]
      - shake_enabled (bool) - combined with move_home_first for byte[1]
      - shake duration ("mm:ss") -> bytes[2-3]: shake duration (16-bit LE total seconds)
      - frequency -> byte[4]: (Slow=0x02, Medium=0x03, Fast=0x04)
      - soak duration ("mm:ss") -> bytes[6-7]: soak duration (16-bit LE total seconds)

    Example encodings (wire format with plate type prefix, 0x04=96-well):
      shake=30s, medium:              04 01 1e 00 03 00 00 00 00 00 00 00
      shake=60s, slow:                04 01 3c 00 02 00 00 00 00 00 00 00
      shake=30s, fast:                04 01 1e 00 04 00 00 00 00 00 00 00
      shake=30s + soak=30s:           04 01 1e 00 03 00 1e 00 00 00 00 00
      shake_enabled=False:            04 00 00 00 03 00 00 00 00 00 00 00

    Byte structure (12 bytes):
      [0]      Plate type (EL406PlateType enum value, e.g. 0x04=96-well)
      [1]      (move_home_first AND shake_enabled): 0x00 or 0x01
      [2-3]    Shake duration in TOTAL SECONDS (16-bit little-endian)
      [4]      Frequency/intensity: 0x01=Variable, 0x02=Slow, 0x03=Medium, 0x04=Fast
      [5]      Reserved: always 0x00
      [6-7]    Soak duration in TOTAL SECONDS (16-bit little-endian)
      [8-11]   Padding/reserved: 4 bytes (0x00)

    Args:
      shake_duration: Shake duration in seconds (encoded in bytes[2-3] only if shake_enabled=True).
      soak_duration: Soak duration in seconds (encoded in bytes[6-7]).
      intensity: Shake intensity - "Variable" (0x01), "Slow" (0x02), "Medium" (0x03), "Fast" (0x04).
      shake_enabled: Whether shake is enabled. When False, shake_duration is NOT encoded (bytes[2-3]=0x0000).
      move_home_first: Move carrier to home position before shaking (default True).
                       byte[1] = 1 only if BOTH move_home_first AND shake_enabled are true.

    Returns:
      Command bytes (12 bytes).
    """
    # Shake duration as 16-bit little-endian total seconds
    # Only encode if shake_enabled=True (sets to 0 when disabled)
    if shake_enabled:
      shake_total_seconds = int(shake_duration)
    else:
      shake_total_seconds = 0
    shake_low = shake_total_seconds & 0xFF
    shake_high = (shake_total_seconds >> 8) & 0xFF

    # Soak duration as 16-bit little-endian total seconds
    soak_total_seconds = int(soak_duration)
    soak_low = soak_total_seconds & 0xFF
    soak_high = (soak_total_seconds >> 8) & 0xFF

    # Map intensity to byte value
    intensity_map = {"Slow": 0x02, "Medium": 0x03, "Fast": 0x04, "Variable": 0x01}
    intensity_byte = intensity_map.get(intensity, 0x03)

    # byte[1] = move_home_first (independent of shake_enabled)
    # Note: soak-only with move_home_first=True sends 0x01
    byte0 = 0x01 if move_home_first else 0x00

    return bytes(
      [
        self.plate_type.value,  # byte[0]: Plate type prefix
        byte0,  # byte[1]: (move_home_first AND shake_enabled)
        shake_low,  # byte[2]: Shake duration (low byte)
        shake_high,  # byte[3]: Shake duration (high byte)
        intensity_byte,  # byte[4]: Frequency/intensity
        0,  # byte[5]: Reserved
        soak_low,  # byte[6]: Soak duration (low byte)
        soak_high,  # byte[7]: Soak duration (high byte)
        0,
        0,
        0,
        0,  # bytes[8-11]: Padding/reserved
      ]
    )
