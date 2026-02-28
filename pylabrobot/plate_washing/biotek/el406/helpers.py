"""EL406 helper functions and encoding utilities.

This module contains encoding and validation helper functions used
across the BioTek EL406 plate washer backend modules.
"""

from __future__ import annotations

from typing import TypedDict

from .enums import EL406PlateType


def validate_plate_type(plate_type: EL406PlateType | int) -> EL406PlateType:
  if isinstance(plate_type, EL406PlateType):
    return plate_type

  if isinstance(plate_type, int):
    try:
      return EL406PlateType(plate_type)
    except ValueError:
      valid_values = [f"{pt.value} ({pt.name})" for pt in EL406PlateType]
      raise ValueError(
        f"Invalid plate type value: {plate_type}. Valid values are: {', '.join(valid_values)}"
      ) from None

  raise TypeError(
    f"Invalid plate type type: {type(plate_type).__name__}. Expected EL406PlateType or int."
  )


def syringe_to_byte(syringe: str) -> int:
  """Convert syringe letter to byte value.

  Args:
    syringe: Syringe identifier (A, B, Both).

  Returns:
    Byte value (A=0, B=1, Both=2).
  """
  syringe_upper = syringe.upper()
  if syringe_upper == "A":
    return 0
  if syringe_upper == "B":
    return 1
  if syringe_upper == "BOTH":
    return 2
  raise ValueError(f"Invalid syringe: {syringe}")


def encode_column_mask(columns: list[int] | None) -> bytes:
  """Encode list of column indices to 6-byte (48-bit) column mask.

  Each bit represents one column: 0 = skip, 1 = operate on column.

  Args:
    columns: List of column indices (0-47) to select, or None for all columns.
      If None, returns all 1s (all columns selected).
      If empty list, returns all 0s (no columns selected).

  Returns:
    6 bytes representing the 48-bit column mask in little-endian order.

  Raises:
    ValueError: If any column index is out of range (not 0-47).
  """
  if columns is None:
    return bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

  for col in columns:
    if col < 0 or col > 47:
      raise ValueError(f"Column index {col} out of range. Must be 0-47.")

  mask = [0] * 6
  for col in columns:
    byte_index = col // 8
    bit_index = col % 8
    mask[byte_index] |= 1 << bit_index

  return bytes(mask)


def cassette_to_byte(cassette: str) -> int:
  """Convert cassette type string to byte value.

  Cassette type (Any: 0, 1uL: 1, 5uL: 2, 10uL: 3).

  Args:
    cassette: Cassette type ("Any", "1uL", "5uL", "10uL").

  Returns:
    Byte value (0-3).

  Raises:
    ValueError: If cassette is invalid.
  """
  mapping = {"ANY": 0, "1UL": 1, "5UL": 2, "10UL": 3}
  key = cassette.upper()
  if key not in mapping:
    raise ValueError(f"Invalid cassette '{cassette}'. Must be one of: Any, 1uL, 5uL, 10uL")
  return mapping[key]


def encode_quadrant_mask_inverted(
  rows: list[int] | None,
  num_row_groups: int = 4,
) -> int:
  """Encode row/quadrant selection as inverted bitmask.

  The protocol uses INVERTED encoding for the quadrant/row mask byte:
  0 = selected, 1 = deselected. This is the opposite of the well mask.

  The number of valid row groups depends on the plate type:
  - 96-well: 1 row group (no row selection meaningful)
  - 384-well: 2 row groups (rows 1-2)
  - 1536-well: 4 row groups (rows 1-4)

  Bits beyond the num_row_groups are always 0 (unused row slots are
  treated as "selected").

  Args:
    rows: List of row numbers (1 to num_row_groups) to select, or None for all.
      If None, returns 0x00 (all selected in inverted encoding).
    num_row_groups: Number of valid row groups for this plate type (1, 2, or 4).

  Returns:
    Single byte with inverted bit encoding (only lower num_row_groups bits used).

  Raises:
    ValueError: If any row number is out of range.
  """
  if rows is None:
    return 0x00  # All selected (inverted: 0 = selected)

  # Start with only the valid bits set (all deselected for those row groups)
  # For 384-well (2 groups): max_mask = 0x03 (bits 0-1)
  # For 1536-well (4 groups): max_mask = 0x0F (bits 0-3)
  max_mask = (1 << num_row_groups) - 1
  mask = max_mask
  for row in rows:
    if row < 1 or row > num_row_groups:
      raise ValueError(f"Row number {row} out of range. Must be 1-{num_row_groups}.")
    mask &= ~(1 << (row - 1))  # Clear bit to select

  return mask & 0xFF


def columns_to_column_mask(columns: list[int] | None, plate_wells: int = 96) -> list[int] | None:
  """Convert 1-indexed column numbers to 0-indexed column indices.

  For a 96-well plate, columns 1-12 map to indices 0-11.
  For a 384-well plate, columns 1-24 map to indices 0-23.
  For a 1536-well plate, columns 1-48 map to indices 0-47.

  Args:
    columns: List of column numbers (1-based), or None for all columns.
    plate_wells: Plate format (96, 384, 1536). Determines max columns.

  Returns:
    List of 0-indexed column indices, or None if columns is None.

  Raises:
    ValueError: If column numbers are out of range.
  """
  if columns is None:
    return None

  max_cols = {96: 12, 384: 24, 1536: 48}.get(plate_wells, 48)
  indices = []
  for col in columns:
    if col < 1 or col > max_cols:
      raise ValueError(f"Column {col} out of range for {plate_wells}-well plate (1-{max_cols}).")
    indices.append(col - 1)
  return indices


def plate_type_max_columns(plate_type) -> int:
  """Return the maximum number of columns for a plate type."""
  return PLATE_TYPE_DEFAULTS[plate_type]["cols"]


def plate_type_max_rows(plate_type) -> int:
  """Return the maximum number of row groups for a plate type.

  96-well: 1 row group (no row selection).
  384-well: 2 row groups.
  1536-well: 4 row groups.
  """
  cols = PLATE_TYPE_DEFAULTS[plate_type]["cols"]
  return {12: 1, 24: 2, 48: 4}[cols]


def plate_type_well_count(plate_type) -> int:
  """Return the well count for a plate type (96, 384, or 1536)."""
  cols = PLATE_TYPE_DEFAULTS[plate_type]["cols"]
  return {12: 96, 24: 384, 48: 1536}[cols]


def plate_type_default_z(plate_type) -> int:
  """Return the default dispenser Z height for a plate type."""
  return PLATE_TYPE_DEFAULTS[plate_type]["dispenser_height"]


TRAVEL_RATE_TO_BYTE: dict[str, int] = {
  "1": 1,
  "2": 2,
  "3": 3,
  "4": 4,
  "5": 5,
  "1 CW": 7,
  "2 CW": 8,
  "3 CW": 9,
  "4 CW": 10,
  "6 CW": 6,
}
VALID_TRAVEL_RATES = set(TRAVEL_RATE_TO_BYTE)


def travel_rate_to_byte(rate: str) -> int:
  """Convert travel rate string to wire byte value.

  Args:
    rate: Travel rate string code.

  Returns:
    Byte value for wire encoding.

  Raises:
    ValueError: If rate is not a valid travel rate code.
  """
  if rate not in TRAVEL_RATE_TO_BYTE:
    valid = sorted(TRAVEL_RATE_TO_BYTE.keys())
    raise ValueError(
      f"Invalid travel rate '{rate}'. Must be one of: {', '.join(repr(r) for r in valid)}"
    )
  return TRAVEL_RATE_TO_BYTE[rate]


INTENSITY_TO_BYTE: dict[str, int] = {
  "Variable": 0x01,
  "Slow": 0x02,
  "Medium": 0x03,
  "Fast": 0x04,
}


# Plate type defaults for the EL406 instrument.
PLATE_TYPE_DEFAULTS: dict[EL406PlateType, dict[str, int]] = {
  EL406PlateType.PLATE_1536_WELL: {
    "dispenser_height": 250,
    "dispense_z": 94,
    "aspirate_z": 42,
    "rows": 32,
    "cols": 48,
  },
  EL406PlateType.PLATE_384_WELL: {
    "dispenser_height": 333,
    "dispense_z": 120,
    "aspirate_z": 22,
    "rows": 16,
    "cols": 24,
  },
  EL406PlateType.PLATE_384_PCR: {
    "dispenser_height": 230,
    "dispense_z": 83,
    "aspirate_z": 2,
    "rows": 16,
    "cols": 24,
  },
  EL406PlateType.PLATE_96_WELL: {
    "dispenser_height": 336,
    "dispense_z": 121,
    "aspirate_z": 29,
    "rows": 8,
    "cols": 12,
  },
  EL406PlateType.PLATE_1536_FLANGE: {
    "dispenser_height": 196,
    "dispense_z": 93,
    "aspirate_z": 13,
    "rows": 32,
    "cols": 48,
  },
}


class WashDefaults(TypedDict):
  dispense_volume: float
  dispense_z: int
  aspirate_z: int


def get_plate_type_wash_defaults(plate_type: EL406PlateType) -> WashDefaults:
  """Return wash defaults for a plate type.

  Returns dict with keys: dispense_volume, dispense_z, aspirate_z.
  Volume logic: 300 uL if well_count == 96, else 100 uL.
  Z values are plate-type-specific defaults for dispense and aspirate.
  """
  pt = PLATE_TYPE_DEFAULTS[plate_type]
  return {
    "dispense_volume": 300.0 if pt["cols"] == 12 else 100.0,
    "dispense_z": pt["dispense_z"],
    "aspirate_z": pt["aspirate_z"],
  }
