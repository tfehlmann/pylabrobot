"""Tests for BioTek EL406 plate washer backend - Setup, serialization, and enum.

This module contains tests for Setup, serialization, and enum.
"""

import unittest

# Import the backend module (mock is already installed by test_el406_mock import)
from pylabrobot.plate_washing.biotek.el406 import (
  BioTekEL406Backend,
  EL406CommunicationError,
  EL406PlateType,
  EL406StepType,
  EL406SyringeManifold,
  EL406WasherManifold,
)


class TestEL406BackendSetup(unittest.IsolatedAsyncioTestCase):
  """Test EL406 backend setup and teardown."""

  async def test_setup_configures_serial_parameters(self):
    """Setup should configure 38400 baud, 8N2, XON/XOFF."""
    backend = BioTekEL406Backend(timeout=0.5)  # Short timeout for tests
    await backend.setup()

    self.assertEqual(backend.dev.baudrate, 38400)
    self.assertEqual(backend.dev.line_property, (8, 2, 0))  # 8 data, 2 stop, no parity
    self.assertTrue(backend.dev.opened)
    # No flow control
    self.assertEqual(backend.dev.flow_control, 0x0)

  async def test_stop_closes_device(self):
    """Stop should close the FTDI device."""
    backend = BioTekEL406Backend(timeout=0.5)
    await backend.setup()

    self.assertTrue(backend.dev.opened)
    await backend.stop()

    self.assertIsNone(backend.dev)


class TestEL406PlateTypes(unittest.TestCase):
  """Test EL406 plate type enumeration."""

  def test_plate_type_96_well(self):
    """96-well plate type should have correct value."""
    self.assertEqual(EL406PlateType.PLATE_96_WELL.value, 4)

  def test_plate_type_384_well(self):
    """384-well plate type should have correct value."""
    self.assertEqual(EL406PlateType.PLATE_384_WELL.value, 1)

  def test_plate_type_1536_well(self):
    """1536-well plate type should have correct value."""
    self.assertEqual(EL406PlateType.PLATE_1536_WELL.value, 0)

  def test_plate_type_1536_flange(self):
    """1536 flange plate type should have correct value."""
    self.assertEqual(EL406PlateType.PLATE_1536_FLANGE.value, 14)


class TestEL406WasherManifold(unittest.TestCase):
  """Test EL406 washer manifold enumeration."""

  def test_manifold_96_tube_dual(self):
    """96-tube dual manifold should have correct value."""
    self.assertEqual(EL406WasherManifold.TUBE_96_DUAL.value, 0)

  def test_manifold_not_installed(self):
    """Not installed manifold should have value 255."""
    self.assertEqual(EL406WasherManifold.NOT_INSTALLED.value, 255)


class TestEL406StepType(unittest.TestCase):
  """Test EL406 step type enumeration."""

  def test_step_type_prime(self):
    """Prime step should have value 2."""
    self.assertEqual(EL406StepType.P_PRIME.value, 2)

  def test_step_type_wash(self):
    """Wash step should have value 6."""
    self.assertEqual(EL406StepType.M_WASH.value, 6)

  def test_step_type_aspirate(self):
    """Aspirate step should have value 7."""
    self.assertEqual(EL406StepType.M_ASPIRATE.value, 7)


class TestEL406CommunicationError(unittest.TestCase):
  """Test EL406CommunicationError exception class."""

  def test_exception_can_be_raised_and_caught(self):
    """EL406CommunicationError should be catchable as Exception."""
    with self.assertRaises(EL406CommunicationError):
      raise EL406CommunicationError("Test error")

  def test_exception_message(self):
    """EL406CommunicationError should preserve message."""
    error = EL406CommunicationError("Device disconnected")
    self.assertEqual(str(error), "Device disconnected")

  def test_exception_operation_attribute(self):
    """EL406CommunicationError should store operation attribute."""
    error = EL406CommunicationError("Failed to write", operation="write")
    self.assertEqual(error.operation, "write")

  def test_exception_original_error_attribute(self):
    """EL406CommunicationError should store original error."""
    original = OSError("USB disconnect")
    error = EL406CommunicationError("FTDI error", operation="read", original_error=original)
    self.assertIs(error.original_error, original)

  def test_exception_defaults(self):
    """EL406CommunicationError should have sensible defaults."""
    error = EL406CommunicationError("Test")
    self.assertEqual(error.operation, "")
    self.assertIsNone(error.original_error)


class TestEL406BackendSerialization(unittest.TestCase):
  """Test EL406 backend serialization."""

  def test_serialize(self):
    """Backend should serialize correctly."""
    backend = BioTekEL406Backend(timeout=30.0)
    serialized = backend.serialize()

    self.assertEqual(serialized["type"], "BioTekEL406Backend")
    self.assertEqual(serialized["timeout"], 30.0)

  def test_init_without_ftdi_available(self):
    """Backend should be instantiable without FTDI library."""
    # This test verifies the backend can be created for serialization
    # even when pylibftdi is not installed
    backend = BioTekEL406Backend()
    self.assertIsNone(backend.dev)


class TestEL406SyringeManifold(unittest.TestCase):
  """Test EL406 syringe manifold enumeration."""

  def test_syringe_manifold_not_installed(self):
    """Not installed syringe manifold should have value 0."""
    self.assertEqual(EL406SyringeManifold.NOT_INSTALLED.value, 0)

  def test_syringe_manifold_tube_16(self):
    """16-Tube syringe manifold should have value 1."""
    self.assertEqual(EL406SyringeManifold.TUBE_16.value, 1)

  def test_syringe_manifold_tube_32_large_bore(self):
    """32-Tube Large Bore syringe manifold should have value 2."""
    self.assertEqual(EL406SyringeManifold.TUBE_32_LARGE_BORE.value, 2)

  def test_syringe_manifold_tube_32_small_bore(self):
    """32-Tube Small Bore syringe manifold should have value 3."""
    self.assertEqual(EL406SyringeManifold.TUBE_32_SMALL_BORE.value, 3)

  def test_syringe_manifold_tube_16_7(self):
    """16-Tube 7 syringe manifold should have value 4."""
    self.assertEqual(EL406SyringeManifold.TUBE_16_7.value, 4)

  def test_syringe_manifold_tube_8(self):
    """8-Tube syringe manifold should have value 5."""
    self.assertEqual(EL406SyringeManifold.TUBE_8.value, 5)

  def test_syringe_manifold_plate_6_well(self):
    """6-Well Plate syringe manifold should have value 6."""
    self.assertEqual(EL406SyringeManifold.PLATE_6_WELL.value, 6)

  def test_syringe_manifold_plate_12_well(self):
    """12-Well Plate syringe manifold should have value 7."""
    self.assertEqual(EL406SyringeManifold.PLATE_12_WELL.value, 7)

  def test_syringe_manifold_plate_24_well(self):
    """24-Well Plate syringe manifold should have value 8."""
    self.assertEqual(EL406SyringeManifold.PLATE_24_WELL.value, 8)

  def test_syringe_manifold_plate_48_well(self):
    """48-Well Plate syringe manifold should have value 9."""
    self.assertEqual(EL406SyringeManifold.PLATE_48_WELL.value, 9)


class TestEL406Sensor(unittest.TestCase):
  """Test EL406 sensor enumeration."""

  def test_sensor_enum_exists(self):
    """EL406Sensor enum should be importable."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertTrue(hasattr(EL406Sensor, "VACUUM"))

  def test_sensor_vacuum_value(self):
    """Vacuum sensor should have value 0."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertEqual(EL406Sensor.VACUUM.value, 0)

  def test_sensor_waste_value(self):
    """Waste sensor should have value 1."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertEqual(EL406Sensor.WASTE.value, 1)

  def test_sensor_fluid_value(self):
    """Fluid sensor should have value 2."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertEqual(EL406Sensor.FLUID.value, 2)

  def test_sensor_flow_value(self):
    """Flow sensor should have value 3."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertEqual(EL406Sensor.FLOW.value, 3)

  def test_sensor_filter_vac_value(self):
    """Filter vacuum sensor should have value 4."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertEqual(EL406Sensor.FILTER_VAC.value, 4)

  def test_sensor_plate_value(self):
    """Plate presence sensor should have value 5."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Sensor

    self.assertEqual(EL406Sensor.PLATE.value, 5)


class TestEL406Motor(unittest.TestCase):
  """Test EL406 motor enumeration."""

  def test_motor_enum_exists(self):
    """EL406Motor enum should exist in the module."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertTrue(hasattr(EL406Motor, "CARRIER_X"))

  def test_motor_carrier_x(self):
    """CARRIER_X motor should have value 0."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.CARRIER_X.value, 0)

  def test_motor_carrier_y(self):
    """CARRIER_Y motor should have value 1."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.CARRIER_Y.value, 1)

  def test_motor_disp_head_z(self):
    """DISP_HEAD_Z motor should have value 2."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.DISP_HEAD_Z.value, 2)

  def test_motor_wash_head_z(self):
    """WASH_HEAD_Z motor should have value 3."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.WASH_HEAD_Z.value, 3)

  def test_motor_syringe_a(self):
    """SYRINGE_A motor should have value 4."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.SYRINGE_A.value, 4)

  def test_motor_syringe_b(self):
    """SYRINGE_B motor should have value 5."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.SYRINGE_B.value, 5)

  def test_motor_peri_pump_primary(self):
    """PERI_PUMP_PRIMARY motor should have value 6."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.PERI_PUMP_PRIMARY.value, 6)

  def test_motor_peri_pump_secondary(self):
    """PERI_PUMP_SECONDARY motor should have value 7."""
    from pylabrobot.plate_washing.biotek.el406 import EL406Motor

    self.assertEqual(EL406Motor.PERI_PUMP_SECONDARY.value, 7)


class TestEL406MotorHomeType(unittest.TestCase):
  """Test EL406 motor home type enumeration."""

  def test_motor_home_type_enum_exists(self):
    """EL406MotorHomeType enum should exist in the module."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertTrue(hasattr(EL406MotorHomeType, "INIT_ALL_MOTORS"))

  def test_init_all_motors(self):
    """INIT_ALL_MOTORS should have value 1."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertEqual(EL406MotorHomeType.INIT_ALL_MOTORS.value, 1)

  def test_init_peri_pump(self):
    """INIT_PERI_PUMP should have value 2."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertEqual(EL406MotorHomeType.INIT_PERI_PUMP.value, 2)

  def test_home_motor(self):
    """HOME_MOTOR should have value 3."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertEqual(EL406MotorHomeType.HOME_MOTOR.value, 3)

  def test_home_xyz_motors(self):
    """HOME_XYZ_MOTORS should have value 4."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertEqual(EL406MotorHomeType.HOME_XYZ_MOTORS.value, 4)

  def test_verify_motor(self):
    """VERIFY_MOTOR should have value 5."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertEqual(EL406MotorHomeType.VERIFY_MOTOR.value, 5)

  def test_verify_xyz_motors(self):
    """VERIFY_XYZ_MOTORS should have value 6."""
    from pylabrobot.plate_washing.biotek.el406 import EL406MotorHomeType

    self.assertEqual(EL406MotorHomeType.VERIFY_XYZ_MOTORS.value, 6)


class TestPlateTypeConfiguration(unittest.TestCase):
  """Test plate type configuration without async context.

  These tests verify the plate type configuration functionality
  in a synchronous context.
  """

  def test_default_plate_type_is_96_well(self):
    """Default plate type should be 96-well."""
    backend = BioTekEL406Backend()

    self.assertEqual(backend.plate_type, EL406PlateType.PLATE_96_WELL)

  def test_init_with_custom_plate_type(self):
    """Backend should accept custom plate type in __init__."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)

    self.assertEqual(backend.plate_type, EL406PlateType.PLATE_384_WELL)

  def test_set_plate_type_method(self):
    """set_plate_type should update the plate_type property."""
    backend = BioTekEL406Backend()
    backend.set_plate_type(EL406PlateType.PLATE_1536_WELL)

    self.assertEqual(backend.plate_type, EL406PlateType.PLATE_1536_WELL)

  def test_get_plate_type_method(self):
    """get_plate_type should return the current plate type."""
    backend = BioTekEL406Backend()

    result = backend.get_plate_type()

    self.assertEqual(result, EL406PlateType.PLATE_96_WELL)

  def test_set_and_get_plate_type_round_trip(self):
    """set_plate_type and get_plate_type should work together."""
    backend = BioTekEL406Backend()

    for plate_type in EL406PlateType:
      backend.set_plate_type(plate_type)
      result = backend.get_plate_type()
      self.assertEqual(result, plate_type)

  def test_serialize_includes_plate_type(self):
    """Backend serialization should include plate_type."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)

    serialized = backend.serialize()

    self.assertEqual(serialized["plate_type"], EL406PlateType.PLATE_384_WELL.value)

  def test_validate_plate_type_raises_for_invalid(self):
    """validate_plate_type should raise ValueError for invalid input."""
    from pylabrobot.plate_washing.biotek.el406.helpers import validate_plate_type

    # Invalid integer should raise
    with self.assertRaises(ValueError):
      validate_plate_type(999)

    # Invalid type should raise
    with self.assertRaises((ValueError, TypeError)):
      validate_plate_type("invalid")


class TestPlateTypeValidation(unittest.TestCase):
  """Test plate type validation.

  These tests verify the validate_plate_type function works correctly.
  """

  def test_validate_plate_type_accepts_enum(self):
    """validate_plate_type should accept EL406PlateType enum values."""
    from pylabrobot.plate_washing.biotek.el406.helpers import validate_plate_type

    for plate_type in EL406PlateType:
      # Should not raise
      validate_plate_type(plate_type)

  def test_validate_plate_type_accepts_int_values(self):
    """validate_plate_type should accept valid integer values."""
    from pylabrobot.plate_washing.biotek.el406.helpers import validate_plate_type

    # Valid values: 0 (1536), 1 (384), 2 (384 PCR), 4 (96), 14 (1536 flange)
    for value in [0, 1, 2, 4, 14]:
      result = validate_plate_type(value)
      self.assertIsInstance(result, EL406PlateType)

  def test_validate_plate_type_raises_for_invalid_int(self):
    """validate_plate_type should raise ValueError for invalid integers."""
    from pylabrobot.plate_washing.biotek.el406.helpers import validate_plate_type

    with self.assertRaises(ValueError):
      validate_plate_type(-1)

    with self.assertRaises(ValueError):
      validate_plate_type(3)  # Not a supported EL406 plate type

    with self.assertRaises(ValueError):
      validate_plate_type(100)

  def test_validate_plate_type_raises_for_invalid_type(self):
    """validate_plate_type should raise for invalid types."""
    from pylabrobot.plate_washing.biotek.el406.helpers import validate_plate_type

    with self.assertRaises((ValueError, TypeError)):
      validate_plate_type("96-well")

    with self.assertRaises((ValueError, TypeError)):
      validate_plate_type(None)

    with self.assertRaises((ValueError, TypeError)):
      validate_plate_type([1, 2, 3])


class TestEL406BackendSetPlateType(unittest.IsolatedAsyncioTestCase):
  """Test EL406 set plate type functionality.

  The set_plate_type operation configures the plate type for subsequent operations.
  This is a local configuration setting that does NOT send a command to the device.
  The plate type is stored as a local property and does not communicate
  with the device.
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_set_plate_type_updates_backend_property(self):
    """set_plate_type should update the backend plate_type property."""
    self.backend.set_plate_type(EL406PlateType.PLATE_384_WELL)

    self.assertEqual(self.backend.plate_type, EL406PlateType.PLATE_384_WELL)

  async def test_set_plate_type_96_well(self):
    """set_plate_type should accept 96-well plate type."""
    self.backend.set_plate_type(EL406PlateType.PLATE_96_WELL)

    self.assertEqual(self.backend.plate_type, EL406PlateType.PLATE_96_WELL)

  async def test_set_plate_type_1536_well(self):
    """set_plate_type should accept 1536-well plate type."""
    self.backend.set_plate_type(EL406PlateType.PLATE_1536_WELL)

    self.assertEqual(self.backend.plate_type, EL406PlateType.PLATE_1536_WELL)

  async def test_set_plate_type_all_types(self):
    """set_plate_type should accept all valid plate types."""
    for plate_type in EL406PlateType:
      self.backend.set_plate_type(plate_type)
      self.assertEqual(self.backend.plate_type, plate_type)

  async def test_set_plate_type_does_not_send_command(self):
    """set_plate_type should NOT send any command to the device."""
    initial_count = len(self.backend.dev.written_data)

    self.backend.set_plate_type(EL406PlateType.PLATE_384_WELL)

    # No command should be sent - this is a local configuration
    self.assertEqual(len(self.backend.dev.written_data), initial_count)

  async def test_set_plate_type_works_without_device_initialized(self):
    """set_plate_type should work even if device is not initialized."""
    backend = BioTekEL406Backend()
    # Note: no setup() called

    # Should not raise - this is a local configuration
    backend.set_plate_type(EL406PlateType.PLATE_384_WELL)

    self.assertEqual(backend.plate_type, EL406PlateType.PLATE_384_WELL)


class TestEL406BackendGetPlateType(unittest.IsolatedAsyncioTestCase):
  """Test EL406 get plate type functionality.

  The get_plate_type operation returns the currently configured plate type.
  This is a local configuration query that does NOT communicate with the device.
  """

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_get_plate_type_returns_enum(self):
    """get_plate_type should return an EL406PlateType enum value."""
    result = self.backend.get_plate_type()

    self.assertIsInstance(result, EL406PlateType)

  async def test_get_plate_type_returns_default_96_well(self):
    """get_plate_type should return 96-well as default."""
    # Default plate type is 96-well
    result = self.backend.get_plate_type()

    self.assertEqual(result, EL406PlateType.PLATE_96_WELL)

  async def test_get_plate_type_returns_set_value(self):
    """get_plate_type should return the value set by set_plate_type."""
    self.backend.set_plate_type(EL406PlateType.PLATE_384_WELL)

    result = self.backend.get_plate_type()

    self.assertEqual(result, EL406PlateType.PLATE_384_WELL)

  async def test_get_plate_type_does_not_send_command(self):
    """get_plate_type should NOT send any command to the device."""
    initial_count = len(self.backend.dev.written_data)

    self.backend.get_plate_type()

    # No command should be sent - this is a local configuration query
    self.assertEqual(len(self.backend.dev.written_data), initial_count)

  async def test_get_plate_type_works_without_device_initialized(self):
    """get_plate_type should work even if device is not initialized."""
    backend = BioTekEL406Backend()
    # Note: no setup() called

    # Should not raise - this is a local configuration query
    result = backend.get_plate_type()

    self.assertEqual(result, EL406PlateType.PLATE_96_WELL)

  async def test_get_plate_type_reflects_init_parameter(self):
    """get_plate_type should reflect the plate_type passed to __init__."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)

    result = backend.get_plate_type()

    self.assertEqual(result, EL406PlateType.PLATE_384_WELL)
