"""Mock FTDI device for EL406 testing.

This module provides the MockFTDIDevice class and setup_mock() function
for testing the BioTek EL406 plate washer backend without actual hardware.

Usage:
  from .mock_tests import MockFTDIDevice, setup_mock

  # Call setup_mock() once at module level (or it's already called on import)
"""

import sys
from unittest.mock import MagicMock


class MockFTDIDevice:
  """Mock FTDI device for testing without hardware."""

  # ACK byte constant for convenience
  ACK = b"\x06"

  def __init__(self, lazy_open: bool = False):
    self.baudrate: int | None = None
    self.opened = False
    self.written_data: list = []
    # Pre-populate with proper response frames so setup() works fast
    # Default: multiple ACK + header frames (header has 0 data length)
    self.read_buffer: bytes = self._default_response_buffer()
    self.line_property: tuple | None = None
    self.flow_control: int | None = None
    self.dtr: bool | None = None
    self.rts: bool | None = None
    self.ftdi_fn = self  # Self-reference for ftdi_fn calls

  @staticmethod
  def _default_response_buffer() -> bytes:
    """Create default buffer with proper response frames."""
    # Each response: ACK + 11-byte header (with 0 data length)
    header = bytes([0x01, 0x02, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    single_response = b"\x06" + header
    return single_response * 20  # 20 responses should be enough

  def open(self):
    self.opened = True

  def close(self):
    self.opened = False

  def write(self, data: bytes):
    self.written_data.append(data)
    return len(data)

  def read(self, size: int) -> bytes:
    result = self.read_buffer[:size]
    self.read_buffer = self.read_buffer[size:]
    return result

  def set_read_buffer(self, data: bytes):
    """Set the read buffer with automatic framing detection.

    Automatically converts legacy test data formats to proper framed responses:
    1. ACK-only buffers: Convert to ACK+header frames
    2. Data ending with ACK (e.g., bytes([value, 0x06])): Wrap as query response
    3. Already framed data (starts with 0x06, 0x01, 0x02): Pass through as-is

    This allows existing tests written for the old protocol to work with
    the new framed protocol without manual updates.
    """
    if not data:
      self.read_buffer = data
      return

    # Check if already a properly framed response (ACK + header starting with 0x01, 0x02)
    if len(data) >= 12 and data[0] == 0x06 and data[1] == 0x01 and data[2] == 0x02:
      self.read_buffer = data
      return

    # Case 1: All ACKs - convert to ACK+header frames
    if all(b == 0x06 for b in data):
      header = bytes([0x01, 0x02, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
      single_response = b"\x06" + header
      count = len(data)
      self.read_buffer = single_response * count
      return

    # Case 2: Data ending with ACK (legacy format) - wrap as query response
    # Pattern: bytes([value1, value2, ..., 0x06])
    if data[-1] == 0x06:
      # Extract the actual data (everything except trailing ACK)
      actual_data = data[:-1]
      # Build proper framed response with 2-byte prefix
      prefixed_data = bytes([0x01, 0x00]) + actual_data
      data_len = len(prefixed_data)
      header = bytes(
        [
          0x01,
          0x02,
          0x00,
          0x00,
          0x01,
          0x00,
          0x00,
          data_len & 0xFF,
          (data_len >> 8) & 0xFF,
          0x00,
          0x00,
        ]
      )
      self.read_buffer = b"\x06" + header + prefixed_data
      return

    # Default: pass through as-is (for timeout tests with empty buffer, etc.)
    self.read_buffer = data

  # FTDI-specific methods
  def ftdi_set_line_property(self, bits: int, stop_bits: int, parity: int):
    self.line_property = (bits, stop_bits, parity)

  def ftdi_setflowctrl(self, flow_ctrl: int):
    self.flow_control = flow_ctrl

  def ftdi_setrts(self, state: int):
    self.rts = bool(state)

  def ftdi_setdtr(self, state: int):
    self.dtr = bool(state)

  def ftdi_usb_purge_rx_buffer(self):
    # Don't clear buffer in tests - we need to simulate device responses
    pass

  def ftdi_usb_purge_tx_buffer(self):
    pass

  @staticmethod
  def build_completion_frame(data: bytes = b"") -> bytes:
    """Build a mock completion frame for action commands.

    Action commands expect:
    1. ACK (0x06)
    2. 11-byte header (bytes 7-8 = data length, little-endian)
    3. Data bytes

    Args:
      data: Optional data bytes to include in frame.

    Returns:
      Complete response bytes (ACK + header + data).
    """
    data_len = len(data)
    # Build 11-byte header: [start, version, 0, 0, const, 0, 0, len_low, len_high, 0, 0]
    header = bytes(
      [
        0x01,  # Start marker
        0x02,  # Version marker
        0x00,  # Reserved
        0x00,  # Reserved
        0x01,  # Constant
        0x00,  # Reserved
        0x00,  # Reserved
        data_len & 0xFF,  # Data length low byte
        (data_len >> 8) & 0xFF,  # Data length high byte
        0x00,  # Reserved
        0x00,  # Reserved
      ]
    )
    return b"\x06" + header + data

  def set_action_response(self, data: bytes = b"", count: int = 1):
    """Set up mock responses for action commands.

    Args:
      data: Data bytes to include in each completion frame.
      count: Number of action responses to queue.
    """
    response = self.build_completion_frame(data)
    self.read_buffer = response * count

  def set_query_response(self, data: bytes, count: int = 1):
    """Set up mock responses for query commands.

    This wraps the data in a proper framed response format:
    ACK + 11-byte header + 2-byte prefix + data

    The 2-byte prefix matches the real device response format:
    - Byte 0: Status (0x01)
    - Byte 1: Reserved (0x00)

    The implementation extracts data starting at byte 2, so we need
    to include this prefix.

    Args:
      data: Data bytes to include in each response.
      count: Number of responses to queue.
    """
    # Include 2-byte prefix that real device sends
    prefixed_data = bytes([0x01, 0x00]) + data
    response = self.build_completion_frame(prefixed_data)
    self.read_buffer = response * count


def setup_mock():
  """Install the mock pylibftdi module and clear el406 modules.

  This must be called before importing any el406 modules.
  """
  # Install mock BEFORE any imports that might trigger el406 import
  mock_pylibftdi = MagicMock()
  mock_pylibftdi.Device = MockFTDIDevice
  sys.modules["pylibftdi"] = mock_pylibftdi

  # Force reload of all el406 submodules to pick up our mock
  # Note: Do NOT clear "pylabrobot.plate_washing.biotek" or
  # "pylabrobot.plate_washing.biotek.el406" as those are package entries
  # needed for test module imports to resolve
  modules_to_clear = [
    "pylabrobot.plate_washing.biotek.el406.backend",
    "pylabrobot.plate_washing.biotek.el406.communication",
    "pylabrobot.plate_washing.biotek.el406.queries",
    "pylabrobot.plate_washing.biotek.el406.actions",
    "pylabrobot.plate_washing.biotek.el406.steps",
    "pylabrobot.plate_washing.biotek.el406.helpers",
  ]
  for mod in modules_to_clear:
    if mod in sys.modules:
      del sys.modules[mod]


# Call setup_mock() at module level so it runs on import
setup_mock()
