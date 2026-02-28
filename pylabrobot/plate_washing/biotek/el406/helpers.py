"""EL406 plate type defaults and helper functions."""

from __future__ import annotations

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
