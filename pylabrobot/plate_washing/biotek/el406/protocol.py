"""EL406 protocol framing utilities.

This module contains the protocol framing functions for building
properly formatted messages for the BioTek EL406 plate washer.
"""

from __future__ import annotations

from pylabrobot.io.binary import Writer


def build_framed_message(command: int, data: bytes = b"") -> bytes:
  """Build a properly framed EL406 message.

  Protocol structure:
    [0]: 0x01 (start marker)
    [1]: 0x02 (version marker)
    [2-3]: command (little-endian short)
    [4]: 0x01 (constant)
    [5-6]: reserved (ushort, typically 0)
    [7-8]: data length (ushort, little-endian)
    [9-10]: checksum (ushort, little-endian)
    ... followed by data bytes

  Checksum is two's complement of sum of header bytes 0-8 + all data bytes.

  Args:
    command: 16-bit command code
    data: Optional data bytes

  Returns:
    Complete framed message with header and checksum
  """
  # Build header bytes 0-8 (checksum placeholder filled after)
  header_prefix = (
    Writer()
    .u8(0x01)      # [0] Start marker
    .u8(0x02)    # [1] Version marker
    .u16(command)              # [2-3] Command (LE)
    .u8(0x01)          # [4] Constant
    .u16(0x0000)               # [5-6] Reserved
    .u16(len(data))            # [7-8] Data length (LE)
    .finish()
  )  # fmt: skip

  # Checksum: two's complement of sum of header bytes 0-8 + all data bytes
  checksum_sum = sum(header_prefix) + sum(data)
  checksum = (0xFFFF - checksum_sum + 1) & 0xFFFF

  return header_prefix + Writer().u16(checksum).finish() + data
