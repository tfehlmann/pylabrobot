"""Tests for BioTek EL406 plate washer backend - Wash operations.

This module contains tests for wash-related step methods:
- wash (MANIFOLD_WASH 0xA4, 102-byte composite command)
"""

import unittest

# Import the backend module (mock is already installed by test_el406_mock import)
from pylabrobot.plate_washing.biotek.el406 import (
  BioTekEL406Backend,
  EL406PlateType,
  EL406StepType,
)


class TestEL406BackendWash(unittest.IsolatedAsyncioTestCase):
  """Test EL406 wash functionality (consolidated wash method)."""

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_wash_sends_command(self):
    """Wash should send correct command."""
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(cycles=1, dispense_volume=300.0)

    self.assertGreater(len(self.backend.dev.written_data), initial_count)

  async def test_wash_validates_cycles(self):
    """Wash should validate cycle count."""
    with self.assertRaises(ValueError):
      await self.backend.wash(cycles=0)  # Zero cycles

  async def test_wash_validates_buffer(self):
    """Wash should validate buffer selection."""
    with self.assertRaises(ValueError):
      await self.backend.wash(buffer="Z")

  async def test_wash_validates_dispense_flow_rate(self):
    """Wash should validate dispense flow rate range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(dispense_flow_rate=0)
    with self.assertRaises(ValueError):
      await self.backend.wash(dispense_flow_rate=10)

  async def test_wash_validates_travel_rate(self):
    """Wash should validate aspirate travel rate range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(aspirate_travel_rate=0)
    with self.assertRaises(ValueError):
      await self.backend.wash(aspirate_travel_rate=10)

  async def test_wash_validates_pre_dispense_flow_rate(self):
    """Wash should validate pre-dispense flow rate range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(pre_dispense_flow_rate=0)
    with self.assertRaises(ValueError):
      await self.backend.wash(pre_dispense_flow_rate=10)

  async def test_wash_validates_dispense_x(self):
    """Wash should validate dispense X offset range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(dispense_x=-200)

  async def test_wash_validates_dispense_y(self):
    """Wash should validate dispense Y offset range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(dispense_y=200)

  async def test_wash_with_all_params(self):
    """Wash should accept all original parameters."""
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(
      cycles=3,
      buffer="B",
      dispense_volume=200.0,
      dispense_flow_rate=5,
      dispense_x=10,
      dispense_y=-5,
      dispense_z=200,
      aspirate_travel_rate=5,
      aspirate_z=40,
      pre_dispense_flow_rate=7,
    )
    self.assertGreater(len(self.backend.dev.written_data), initial_count)

  async def test_wash_with_all_new_params(self):
    """Wash should accept all new parameters."""
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(
      cycles=3,
      buffer="B",
      dispense_volume=200.0,
      dispense_flow_rate=5,
      dispense_x=10,
      dispense_y=-5,
      dispense_z=200,
      aspirate_travel_rate=5,
      aspirate_z=40,
      pre_dispense_flow_rate=7,
      aspirate_delay_ms=1000,
      aspirate_x=15,
      aspirate_y=-10,
      final_aspirate=False,
      pre_dispense_volume=100.0,
      vacuum_delay_volume=50.0,
      soak_duration=30,
      shake_duration=10,
      shake_intensity="Fast",
    )
    self.assertGreater(len(self.backend.dev.written_data), initial_count)

  async def test_wash_validates_aspirate_delay_ms(self):
    """Wash should validate aspirate delay range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(aspirate_delay_ms=-1)
    with self.assertRaises(ValueError):
      await self.backend.wash(aspirate_delay_ms=70000)

  async def test_wash_validates_aspirate_x(self):
    """Wash should validate aspirate X offset range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(aspirate_x=-200)

  async def test_wash_validates_aspirate_y(self):
    """Wash should validate aspirate Y offset range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(aspirate_y=200)

  async def test_wash_validates_pre_dispense_volume(self):
    """Wash should validate pre-dispense volume (0 or 25-3000)."""
    with self.assertRaises(ValueError):
      await self.backend.wash(pre_dispense_volume=10.0)  # Below 25
    # 0 should be allowed (disabled)
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(pre_dispense_volume=0.0)
    self.assertGreater(len(self.backend.dev.written_data), initial_count)

  async def test_wash_validates_vacuum_delay_volume(self):
    """Wash should validate vacuum delay volume range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(vacuum_delay_volume=-1.0)
    with self.assertRaises(ValueError):
      await self.backend.wash(vacuum_delay_volume=4000.0)

  async def test_wash_validates_soak_duration(self):
    """Wash should validate soak duration range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(soak_duration=-1)
    with self.assertRaises(ValueError):
      await self.backend.wash(soak_duration=4000)

  async def test_wash_validates_shake_duration(self):
    """Wash should validate shake duration range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(shake_duration=-1)
    with self.assertRaises(ValueError):
      await self.backend.wash(shake_duration=4000)

  async def test_wash_validates_shake_intensity(self):
    """Wash should validate shake intensity string."""
    with self.assertRaises(ValueError):
      await self.backend.wash(shake_intensity="InvalidIntensity")


class TestWashCompositeCommandEncoding(unittest.TestCase):
  """Test 102-byte MANIFOLD_WASH composite command encoding.

  This tests _build_wash_composite_command() which produces the 102-byte
  payload for the MANIFOLD_WASH (0xA4) wire command.
  """

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_composite_command_length(self):
    """Composite wash command should be exactly 102 bytes."""
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(len(cmd), 102)

  def test_composite_command_header(self):
    """Header should encode prefix, sector mask, and cycles."""
    cmd = self.backend._build_wash_composite_command(cycles=5, sector_mask=0x03)
    self.assertEqual(cmd[0], 0x04)  # plate type (96-well)
    self.assertEqual(cmd[4], 0x03)  # sector mask low byte
    self.assertEqual(cmd[5], 0x00)  # sector mask high byte
    self.assertEqual(cmd[6], 5)  # wash cycles (bg.a8)

  def test_composite_command_dispense_sections(self):
    """Both dispense sections should encode buffer, volume, flow rate, Z, prime flow."""
    cmd = self.backend._build_wash_composite_command(
      buffer="B",
      dispense_volume=500.0,
      dispense_flow_rate=5,
      dispense_z=200,
      pre_dispense_flow_rate=7,
    )
    # Dispense section 1 starts at [7]
    self.assertEqual(cmd[7], 0x42)  # Buffer B
    self.assertEqual(cmd[8], 0xF4)  # 500 low byte
    self.assertEqual(cmd[9], 0x01)  # 500 high byte
    self.assertEqual(cmd[10], 5)  # flow rate
    self.assertEqual(cmd[17], 7)  # pre-dispense flow rate

    # Dispense section 2 starts at [68]
    self.assertEqual(cmd[68], 0x42)  # Buffer B
    self.assertEqual(cmd[69], 0xF4)  # 500 low byte
    self.assertEqual(cmd[70], 0x01)  # 500 high byte
    self.assertEqual(cmd[71], 5)  # flow rate
    self.assertEqual(cmd[78], 7)  # pre-dispense flow rate

  def test_composite_command_dispense_offsets(self):
    """Dispense sections should encode X/Y offsets."""
    cmd = self.backend._build_wash_composite_command(dispense_x=10, dispense_y=-5)
    # Dispense section 1: X at [11], Y at [12]
    self.assertEqual(cmd[11], 10)  # X offset
    self.assertEqual(cmd[12], 0xFB)  # Y=-5 two's complement
    # Dispense section 2: X at [72], Y at [73]
    self.assertEqual(cmd[72], 10)
    self.assertEqual(cmd[73], 0xFB)

  def test_composite_command_aspirate_sections(self):
    """Aspirate sections should encode travel rate and Z offsets.

    Wire Aspirate1 [29-48] = "final aspirate" with fixed Z=29.
    Wire Aspirate2 [49-67] = "primary aspirate" with user params.
    """
    cmd = self.backend._build_wash_composite_command(aspirate_travel_rate=5, aspirate_z=40)
    # Aspirate section 1 (final aspirate, mirrors primary Z)
    self.assertEqual(cmd[29], 5)  # travel rate (propagated)
    self.assertEqual(cmd[32], 0x28)  # Z low (40)
    self.assertEqual(cmd[33], 0x00)  # Z high
    self.assertEqual(cmd[37], 0x28)  # secondary Z low (mirrors primary)
    self.assertEqual(cmd[38], 0x00)  # secondary Z high

    # Aspirate section 2 (primary aspirate, user params)
    self.assertEqual(cmd[49], 0x00)  # leading padding
    self.assertEqual(cmd[50], 5)  # travel rate
    self.assertEqual(cmd[53], 0x28)  # Z low (40)
    self.assertEqual(cmd[58], 0x1D)  # secondary Z low (default 29, independent)

  def test_composite_command_final_section(self):
    """Final section should have shake intensity at [90]."""
    cmd = self.backend._build_wash_composite_command(aspirate_travel_rate=3)
    # Final section starts at [90]; [0] = shake intensity
    self.assertEqual(cmd[90], 3)  # shake intensity (default Medium=3)
    self.assertEqual(cmd[91], 0x00)  # reserved

  def test_composite_command_default_matches_reference(self):
    """Default parameters should produce bytes matching reference capture."""
    lhc_bytes = bytes(
      [
        0x04,
        0x00,
        0x01,
        0x00,
        0x0F,
        0x00,
        0x03,
        0x41,
        0x2C,
        0x01,
        0x07,
        0x00,
        0x00,
        0x79,
        0x00,
        0x00,
        0x00,
        0x09,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x41,
        0x2C,
        0x01,
        0x07,
        0x00,
        0x00,
        0x79,
        0x00,
        0x00,
        0x00,
        0x09,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
      ]
    )
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(cmd, lhc_bytes)

  def test_composite_command_final_aspirate_flag(self):
    """Header byte [2] should reflect final_aspirate flag."""
    cmd_on = self.backend._build_wash_composite_command(final_aspirate=True)
    self.assertEqual(cmd_on[2], 0x01)

    cmd_off = self.backend._build_wash_composite_command(final_aspirate=False)
    self.assertEqual(cmd_off[2], 0x00)

  def test_composite_command_pre_dispense_volume(self):
    """Pre-dispense volume should appear at dispense section offsets [8-9]."""
    cmd = self.backend._build_wash_composite_command(pre_dispense_volume=100.0)
    # Dispense1 [7-28]: pre_disp_vol at [7+8]=15, [7+9]=16
    self.assertEqual(cmd[15], 0x64)  # 100 low
    self.assertEqual(cmd[16], 0x00)  # 100 high
    # Dispense2 [68-89]: pre_disp_vol at [68+8]=76, [68+9]=77
    self.assertEqual(cmd[76], 0x64)
    self.assertEqual(cmd[77], 0x00)

  def test_composite_command_vacuum_delay_volume(self):
    """Vacuum delay volume should appear at dispense section offsets [11-12]."""
    cmd = self.backend._build_wash_composite_command(vacuum_delay_volume=200.0)
    # Dispense1: vac_delay at [7+11]=18, [7+12]=19
    self.assertEqual(cmd[18], 0xC8)  # 200 low
    self.assertEqual(cmd[19], 0x00)  # 200 high
    # Dispense2: vac_delay at [68+11]=79, [68+12]=80
    self.assertEqual(cmd[79], 0xC8)
    self.assertEqual(cmd[80], 0x00)

  def test_composite_command_aspirate_delay(self):
    """Aspirate delay encoding.

    Wire Aspirate1 uses fixed defaults (delay=0 always).
    Wire Aspirate2 layout: [2]=X, [3]=Y, no delay field.
    aspirate_delay_ms is accepted as parameter but not currently encoded.
    """
    cmd = self.backend._build_wash_composite_command(aspirate_delay_ms=1000)
    # Aspirate1 always has delay=0 (fixed defaults)
    self.assertEqual(cmd[30], 0x00)
    self.assertEqual(cmd[31], 0x00)

  def test_composite_command_aspirate_offsets(self):
    """Aspirate X/Y offsets appear in wire Aspirate2 only (primary aspirate).

    Wire Aspirate2 layout: [2]=X, [3]=Y.
    Wire Aspirate1 (final aspirate) uses fixed X=0, Y=0.
    """
    cmd = self.backend._build_wash_composite_command(aspirate_x=15, aspirate_y=-10)
    # Aspirate1 (final aspirate): X/Y fixed at 0
    self.assertEqual(cmd[34], 0x00)
    self.assertEqual(cmd[35], 0x00)
    # Aspirate2 (primary aspirate): X at [49+2]=51, Y at [49+3]=52
    self.assertEqual(cmd[51], 15)
    self.assertEqual(cmd[52], 0xF6)  # -10 two's complement

  def test_composite_command_shake_duration(self):
    """Shake duration should appear at wire [88-89] (bf section offset [1-2])."""
    cmd = self.backend._build_wash_composite_command(shake_duration=30)
    # Shake section [87-101]: shake_dur at [87+1]=88, [87+2]=89
    self.assertEqual(cmd[88], 30)
    self.assertEqual(cmd[89], 0x00)

  def test_composite_command_shake_intensity(self):
    """Shake intensity should appear at wire [90] (bf section offset [3])."""
    cmd_fast = self.backend._build_wash_composite_command(shake_duration=10, shake_intensity="Fast")
    self.assertEqual(cmd_fast[90], 0x04)

    cmd_slow = self.backend._build_wash_composite_command(shake_duration=10, shake_intensity="Slow")
    self.assertEqual(cmd_slow[90], 0x02)

    cmd_var = self.backend._build_wash_composite_command(
      shake_duration=10, shake_intensity="Variable"
    )
    self.assertEqual(cmd_var[90], 0x01)

  def test_composite_command_shake_intensity_default_when_disabled(self):
    """Shake intensity byte stays at default Medium (3) when shake_duration=0.

    The intensity field is inert when shake_duration=0."""
    cmd = self.backend._build_wash_composite_command(shake_duration=0, shake_intensity="Fast")
    self.assertEqual(cmd[90], 0x03)

  def test_composite_command_soak_duration(self):
    """Soak duration should appear at wire [92-93] (bf section offset [5-6])."""
    cmd = self.backend._build_wash_composite_command(soak_duration=90)
    # Shake section [87-101]: soak_dur at [87+5]=92, [87+6]=93
    self.assertEqual(cmd[92], 90)
    self.assertEqual(cmd[93], 0x00)

  def test_composite_command_soak_duration_large(self):
    """Large soak duration should encode correctly as 16-bit LE."""
    cmd = self.backend._build_wash_composite_command(soak_duration=3599)
    # 3599 = 0x0E0F -> low=0x0F, high=0x0E
    # Soak is at [92-93] after the fix
    self.assertEqual(cmd[92], 0x0F)
    self.assertEqual(cmd[93], 0x0E)

  def test_composite_command_all_new_params(self):
    """All new parameters set to non-default values should produce correct output."""
    cmd = self.backend._build_wash_composite_command(
      cycles=5,
      buffer="B",
      dispense_volume=500.0,
      dispense_flow_rate=5,
      dispense_x=10,
      dispense_y=-5,
      dispense_z=200,
      aspirate_travel_rate=5,
      aspirate_z=40,
      pre_dispense_flow_rate=7,
      aspirate_delay_ms=2000,
      aspirate_x=-20,
      aspirate_y=15,
      final_aspirate=False,
      pre_dispense_volume=150.0,
      vacuum_delay_volume=100.0,
      soak_duration=60,
      shake_duration=30,
      shake_intensity="Slow",
    )
    self.assertEqual(len(cmd), 102)
    # Header
    self.assertEqual(cmd[2], 0x00)  # final_aspirate=False
    self.assertEqual(cmd[4], 0x0F)  # sector_mask low byte (default)
    self.assertEqual(cmd[5], 0x00)  # sector_mask high byte
    self.assertEqual(cmd[6], 5)  # cycles
    # Dispense1 pre_dispense_volume=150 at [15-16]
    self.assertEqual(cmd[15], 150 & 0xFF)
    self.assertEqual(cmd[16], 0x00)
    # Dispense1 pre_dispense_flow_rate=7 at [17]
    self.assertEqual(cmd[17], 7)
    # Dispense1 vacuum_delay=100 at [18-19]
    self.assertEqual(cmd[18], 100)
    self.assertEqual(cmd[19], 0x00)
    # Aspirate1 (final aspirate) uses fixed defaults — delay/x/y not encoded
    self.assertEqual(cmd[30], 0x00)  # delay always 0
    self.assertEqual(cmd[31], 0x00)
    self.assertEqual(cmd[34], 0x00)  # X fixed 0
    self.assertEqual(cmd[35], 0x00)  # Y fixed 0
    # Aspirate2 (primary aspirate): x=-20 at [51], y=15 at [52]
    self.assertEqual(cmd[51], 0xEC)  # -20 two's complement
    self.assertEqual(cmd[52], 15)
    # bf section at [87-101]: shake=30 at [88-89], intensity=Slow at [90], soak=60 at [92-93]
    # (shake comes before soak)
    self.assertEqual(cmd[88], 30)  # shake duration
    self.assertEqual(cmd[89], 0x00)
    self.assertEqual(cmd[90], 0x02)  # Slow
    self.assertEqual(cmd[92], 60)  # soak duration
    self.assertEqual(cmd[93], 0x00)


class TestWashMoveHomeFirst(unittest.TestCase):
  """Test move_home_first parameter in 102-byte wash command."""

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_move_home_default_disabled(self):
    """move_home_first defaults to False, wire [87] = 0x00."""
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(cmd[87], 0x00)

  def test_move_home_enabled(self):
    """move_home_first=True sets wire [87] = 0x01."""
    cmd = self.backend._build_wash_composite_command(move_home_first=True)
    self.assertEqual(cmd[87], 0x01)

  def test_move_home_does_not_affect_other_bytes(self):
    """Enabling move_home_first should only change byte [87]."""
    cmd_off = self.backend._build_wash_composite_command(move_home_first=False)
    cmd_on = self.backend._build_wash_composite_command(move_home_first=True)
    # Only byte [87] should differ
    diffs = [i for i in range(102) if cmd_off[i] != cmd_on[i]]
    self.assertEqual(diffs, [87])

  def test_move_home_with_shake_and_soak(self):
    """move_home_first should coexist with shake/soak parameters."""
    cmd = self.backend._build_wash_composite_command(
      move_home_first=True, shake_duration=15, shake_intensity="Fast", soak_duration=45
    )
    self.assertEqual(cmd[87], 0x01)  # move_home
    # shake at [88-89], soak at [92-93]
    self.assertEqual(cmd[88], 15)  # shake low
    self.assertEqual(cmd[89], 0x00)  # shake high
    self.assertEqual(cmd[90], 0x04)  # Fast intensity
    self.assertEqual(cmd[92], 45)  # soak low
    self.assertEqual(cmd[93], 0x00)  # soak high


class TestWashSecondaryAspirate(unittest.TestCase):
  """Test secondary aspirate parameters in 102-byte wash command."""

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_secondary_aspirate_disabled_default(self):
    """When secondary_aspirate=False (default), Asp1 sec_z mirrors final_asp_z,
    Asp2 sec_z uses secondary_z default (29)."""
    cmd = self.backend._build_wash_composite_command(aspirate_z=40)
    # Asp1 (final aspirate): sec_z mirrors final_asp_z (= aspirate_z)
    self.assertEqual(cmd[37], 0x28)  # secondary Z = 40 (mirrors final_asp_z)
    self.assertEqual(cmd[38], 0x00)
    self.assertEqual(cmd[39], 0x00)  # secondary mode disabled
    # Asp2 (primary aspirate): sec_z = default 29, mode = 0
    self.assertEqual(cmd[58], 0x1D)  # secondary Z = 29 (default, independent)
    self.assertEqual(cmd[59], 0x00)
    self.assertEqual(cmd[55], 0x00)  # secondary mode at Asp2[6]

  def test_secondary_aspirate_enabled(self):
    """When secondary_aspirate=True, Asp2 gets secondary Z and mode.

    Asp1 sec_z mirrors final_asp_z (final_secondary_aspirate is off by default).
    Asp2 gets user's secondary_z and secondary mode enabled.
    """
    cmd = self.backend._build_wash_composite_command(
      aspirate_z=40, secondary_aspirate=True, secondary_z=100
    )
    # Asp1 (final aspirate): primary Z = aspirate_z, sec_z = final_asp_z (not secondary_z),
    # secondary mode stays off (final_secondary_aspirate=False)
    self.assertEqual(cmd[32], 0x28)  # primary Z = 40
    self.assertEqual(cmd[34], 0x00)  # final secondary mode at Asp1[5] = off
    self.assertEqual(cmd[37], 0x28)  # secondary Z = 40 (mirrors final_asp_z, not secondary_z)
    # Asp2 (primary aspirate): user params
    self.assertEqual(cmd[53], 0x28)  # primary Z = 40
    self.assertEqual(cmd[54], 0x00)
    self.assertEqual(cmd[55], 0x01)  # secondary mode at Asp2[6] = enabled
    self.assertEqual(cmd[58], 0x64)  # secondary Z = 100
    self.assertEqual(cmd[59], 0x00)

  def test_secondary_aspirate_default_preserves_reference(self):
    """Default output with secondary_aspirate=False must still match reference."""
    lhc_bytes = bytes(
      [
        0x04,
        0x00,
        0x01,
        0x00,
        0x0F,
        0x00,
        0x03,
        0x41,
        0x2C,
        0x01,
        0x07,
        0x00,
        0x00,
        0x79,
        0x00,
        0x00,
        0x00,
        0x09,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x1D,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x41,
        0x2C,
        0x01,
        0x07,
        0x00,
        0x00,
        0x79,
        0x00,
        0x00,
        0x00,
        0x09,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x03,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
      ]
    )
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(cmd, lhc_bytes)

  def test_secondary_aspirate_still_102_bytes(self):
    """Command is 102 bytes with secondary aspirate enabled."""
    cmd = self.backend._build_wash_composite_command(secondary_aspirate=True, secondary_z=50)
    self.assertEqual(len(cmd), 102)


class TestWashPreDispenseFlowRateEncoding(unittest.TestCase):
  """Test pre_dispense_flow_rate encoding in wash command."""

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_pre_dispense_flow_rate_encoding(self):
    """pre_dispense_flow_rate should encode at correct positions."""
    cmd = self.backend._build_wash_composite_command(pre_dispense_flow_rate=7)
    self.assertEqual(cmd[17], 7)  # Dispense1 [10]
    self.assertEqual(cmd[78], 7)  # Dispense2 [10]


class TestWashSecondaryXY(unittest.TestCase):
  """Test secondary aspirate X/Y parameters in 102-byte wash command."""

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_secondary_xy_default_zero(self):
    """Secondary X/Y should default to 0 and not affect baseline output."""
    cmd = self.backend._build_wash_composite_command()
    # Asp1 (final aspirate): always fixed 0
    self.assertEqual(cmd[40], 0x00)  # Asp1[11] = secondary X (fixed)
    self.assertEqual(cmd[41], 0x00)  # Asp1[12] = secondary Y (fixed)
    # Asp2 (primary aspirate): secondary X at [7], Y at [8]
    self.assertEqual(cmd[56], 0x00)  # Asp2[7] = secondary X
    self.assertEqual(cmd[57], 0x00)  # Asp2[8] = secondary Y

  def test_secondary_xy_encoded_when_enabled(self):
    """Secondary X/Y should be encoded in wire Aspirate2 when secondary_aspirate=True."""
    cmd = self.backend._build_wash_composite_command(
      secondary_aspirate=True, secondary_x=15, secondary_y=-10, secondary_z=50
    )
    # Asp1 (final aspirate): always fixed 0
    self.assertEqual(cmd[40], 0x00)
    self.assertEqual(cmd[41], 0x00)
    # Asp2 (primary aspirate): secondary X at [7]=56, Y at [8]=57
    self.assertEqual(cmd[56], 15)
    self.assertEqual(cmd[57], 0xF6)  # -10 two's complement

  def test_secondary_xy_zero_when_disabled(self):
    """Secondary X/Y should be 0 when secondary_aspirate=False, even if values set."""
    cmd = self.backend._build_wash_composite_command(
      secondary_aspirate=False, secondary_x=15, secondary_y=-10
    )
    self.assertEqual(cmd[40], 0x00)  # Asp1 (always fixed)
    self.assertEqual(cmd[41], 0x00)
    self.assertEqual(cmd[56], 0x00)  # Asp2 secondary X
    self.assertEqual(cmd[57], 0x00)  # Asp2 secondary Y

  def test_secondary_xy_still_102_bytes(self):
    """Command should still be 102 bytes with secondary X/Y."""
    cmd = self.backend._build_wash_composite_command(
      secondary_aspirate=True, secondary_x=30, secondary_y=-20, secondary_z=80
    )
    self.assertEqual(len(cmd), 102)

  def test_secondary_xy_preserves_baseline_when_default(self):
    """Default secondary X/Y should not change baseline bytes."""
    ref_hex = "040001000f0003412c01070000790000000900000000000000000000000300001d000000001d0000000000000000000000000300001d000000001d000000000000000000412c0107000079000000090000000000000000000000030000000000000000000000"
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(cmd, bytes.fromhex(ref_hex))


class TestWashBottomWash(unittest.TestCase):
  """Test bottom wash parameters in 102-byte wash command."""

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_bottom_wash_disabled_dispense1_mirrors_main(self):
    """When bottom_wash=False, Dispense1 should mirror main dispense volume/flow."""
    cmd = self.backend._build_wash_composite_command(dispense_volume=500.0, dispense_flow_rate=5)
    # Dispense1 [7-28]: vol at [8-9], flow at [10]
    self.assertEqual(cmd[8], 0xF4)  # 500 low
    self.assertEqual(cmd[9], 0x01)  # 500 high
    self.assertEqual(cmd[10], 5)  # flow rate
    # Dispense2 [68-89]: vol at [69-70], flow at [71]
    self.assertEqual(cmd[69], 0xF4)  # 500 low
    self.assertEqual(cmd[70], 0x01)  # 500 high
    self.assertEqual(cmd[71], 5)  # flow rate

  def test_bottom_wash_enabled_dispense1_uses_bottom_params(self):
    """When bottom_wash=True, Dispense1 should use bottom wash volume/flow."""
    cmd = self.backend._build_wash_composite_command(
      dispense_volume=300.0,
      dispense_flow_rate=7,
      bottom_wash=True,
      bottom_wash_volume=200.0,
      bottom_wash_flow_rate=5,
    )
    # Dispense1 [7-28]: bottom wash vol=200 at [8-9], flow=5 at [10]
    self.assertEqual(cmd[8], 0xC8)  # 200 low
    self.assertEqual(cmd[9], 0x00)  # 200 high
    self.assertEqual(cmd[10], 5)  # bottom wash flow rate
    # Dispense2 [68-89]: main vol=300 at [69-70], flow=7 at [71]
    self.assertEqual(cmd[69], 0x2C)  # 300 low
    self.assertEqual(cmd[70], 0x01)  # 300 high
    self.assertEqual(cmd[71], 7)  # main flow rate

  def test_bottom_wash_still_102_bytes(self):
    """Command should still be 102 bytes with bottom wash enabled."""
    cmd = self.backend._build_wash_composite_command(
      bottom_wash=True, bottom_wash_volume=200.0, bottom_wash_flow_rate=5
    )
    self.assertEqual(len(cmd), 102)


class TestWashBottomWashValidation(unittest.IsolatedAsyncioTestCase):
  """Test bottom wash parameter validation."""

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_bottom_wash_validates_volume(self):
    """Bottom wash should validate volume range (25-3000)."""
    with self.assertRaises(ValueError):
      await self.backend.wash(bottom_wash=True, bottom_wash_volume=10.0)
    with self.assertRaises(ValueError):
      await self.backend.wash(bottom_wash=True, bottom_wash_volume=0.0)

  async def test_bottom_wash_validates_flow_rate(self):
    """Bottom wash should validate flow rate range."""
    with self.assertRaises(ValueError):
      await self.backend.wash(bottom_wash=True, bottom_wash_volume=200.0, bottom_wash_flow_rate=0)

  async def test_bottom_wash_sends_command(self):
    """Bottom wash should send a command successfully."""
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(bottom_wash=True, bottom_wash_volume=200.0, bottom_wash_flow_rate=5)
    self.assertGreater(len(self.backend.dev.written_data), initial_count)


class TestWashPreDispenseBetweenCycles(unittest.TestCase):
  """Test pre-dispense between cycles parameters in 102-byte wash command."""

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_midcyc_disabled_dispense2_uses_main_pre_dispense(self):
    """When midcyc volume=0, Dispense2 pre-dispense mirrors main pre-dispense."""
    cmd = self.backend._build_wash_composite_command(
      pre_dispense_volume=100.0, pre_dispense_flow_rate=7
    )
    # Dispense1 pre-disp at [15-16], flow at [17]
    self.assertEqual(cmd[15], 100)
    self.assertEqual(cmd[16], 0x00)
    self.assertEqual(cmd[17], 7)
    # Dispense2 pre-disp at [76-77], flow at [78]
    self.assertEqual(cmd[76], 100)
    self.assertEqual(cmd[77], 0x00)
    self.assertEqual(cmd[78], 7)

  def test_midcyc_enabled_dispense2_uses_midcyc_values(self):
    """When midcyc volume>0, Dispense2 pre-dispense uses midcyc values."""
    cmd = self.backend._build_wash_composite_command(
      pre_dispense_volume=100.0,
      pre_dispense_flow_rate=7,
      pre_dispense_between_cycles_volume=50.0,
      pre_dispense_between_cycles_flow_rate=5,
    )
    # Dispense1 pre-disp: main values (100, flow 7)
    self.assertEqual(cmd[15], 100)
    self.assertEqual(cmd[16], 0x00)
    self.assertEqual(cmd[17], 7)
    # Dispense2 pre-disp: midcyc values (50, flow 5)
    self.assertEqual(cmd[76], 50)
    self.assertEqual(cmd[77], 0x00)
    self.assertEqual(cmd[78], 5)

  def test_midcyc_still_102_bytes(self):
    """Command should still be 102 bytes with midcyc enabled."""
    cmd = self.backend._build_wash_composite_command(pre_dispense_between_cycles_volume=50.0)
    self.assertEqual(len(cmd), 102)

  def test_midcyc_preserves_baseline_when_default(self):
    """Default midcyc parameters should not change baseline bytes."""
    ref_hex = "040001000f0003412c01070000790000000900000000000000000000000300001d000000001d0000000000000000000000000300001d000000001d000000000000000000412c0107000079000000090000000000000000000000030000000000000000000000"
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(cmd, bytes.fromhex(ref_hex))


class TestWashPreDispenseBetweenCyclesValidation(unittest.IsolatedAsyncioTestCase):
  """Test pre-dispense between cycles validation."""

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_midcyc_validates_volume(self):
    """Pre-dispense between cycles should validate volume (0 or 25-3000)."""
    with self.assertRaises(ValueError):
      await self.backend.wash(pre_dispense_between_cycles_volume=10.0)

  async def test_midcyc_validates_flow_rate(self):
    """Pre-dispense between cycles should validate flow rate."""
    with self.assertRaises(ValueError):
      await self.backend.wash(
        pre_dispense_between_cycles_volume=50.0, pre_dispense_between_cycles_flow_rate=0
      )

  async def test_midcyc_sends_command(self):
    """Pre-dispense between cycles should send a command successfully."""
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(
      pre_dispense_between_cycles_volume=50.0, pre_dispense_between_cycles_flow_rate=9
    )
    self.assertGreater(len(self.backend.dev.written_data), initial_count)


class TestWashCommandEncoding(unittest.TestCase):
  """Test 20-byte wash step command encoding (_build_wash_command).

  This tests the 20-byte M_WASH step type (0x06).
  NOT the 102-byte MANIFOLD_WASH composite command tested above.

  Protocol format for wash (M_WASH = 6):
    [0]   Step type: 0x06 (M_WASH)
    [1]   Number of cycles: byte
    [2]   Buffer valve: A=0, B=1, C=2, D=3
    [3]   Final aspirate: 0 or 1
    [4-5] Dispense volume: 2 bytes, little-endian, uL
    [6]   Dispense flow rate: 1-9
    [7]   Dispense offset X: signed byte
    [8]   Dispense offset Y: signed byte
    [9-10] Dispense offset Z: 2 bytes, little-endian
    [11]  Aspirate travel rate: 1-9
    [12-13] Aspirate delay: 2 bytes, little-endian, ms
    [14]  Aspirate offset X: signed byte
    [15]  Aspirate offset Y: signed byte
    [16-17] Aspirate offset Z: 2 bytes, little-endian
    [18]  Soak duration minutes: byte
    [19]  Soak duration seconds: byte
  """

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_wash_command_basic(self):
    """Basic wash: 1 cycle, 300 uL, buffer A, with final aspirate."""
    cmd = self.backend._build_wash_command(
      cycles=1,
      dispense_volume=300.0,
      soak_time=0.0,
      final_aspirate=True,
      buffer="A",
      dispense_flow_rate=7,
      dispense_offset_x=0,
      dispense_offset_y=0,
      dispense_offset_z=120,
      aspirate_travel_rate=3,
      aspirate_delay_ms=5000,
      aspirate_offset_x=0,
      aspirate_offset_y=0,
      aspirate_offset_z=29,
    )

    # Step type: M_WASH = 6
    self.assertEqual(cmd[0], EL406StepType.M_WASH)

    # Number of cycles: 1
    self.assertEqual(cmd[1], 1)

    # Buffer valve: A = 0
    self.assertEqual(cmd[2], 0)

    # Final aspirate: True = 1
    self.assertEqual(cmd[3], 1)

    # Dispense volume: 300 uL = 0x012C little-endian
    self.assertEqual(cmd[4], 0x2C)
    self.assertEqual(cmd[5], 0x01)

  def test_wash_command_multiple_cycles(self):
    """Wash with 3 cycles."""
    cmd = self.backend._build_wash_command(
      cycles=3,
      dispense_volume=300.0,
      soak_time=0.0,
      final_aspirate=True,
      buffer="B",
      dispense_flow_rate=7,
      dispense_offset_x=0,
      dispense_offset_y=0,
      dispense_offset_z=120,
      aspirate_travel_rate=3,
      aspirate_delay_ms=5000,
      aspirate_offset_x=0,
      aspirate_offset_y=0,
      aspirate_offset_z=29,
    )

    self.assertEqual(cmd[1], 3)

  def test_wash_command_with_soak_time(self):
    """Wash with 30 second soak time."""
    cmd = self.backend._build_wash_command(
      cycles=1,
      dispense_volume=300.0,
      soak_time=30.0,  # 30 seconds = 0 minutes, 30 seconds
      final_aspirate=True,
      buffer="A",
      dispense_flow_rate=7,
      dispense_offset_x=0,
      dispense_offset_y=0,
      dispense_offset_z=120,
      aspirate_travel_rate=3,
      aspirate_delay_ms=5000,
      aspirate_offset_x=0,
      aspirate_offset_y=0,
      aspirate_offset_z=29,
    )

    # Soak duration: 0 minutes, 30 seconds
    self.assertEqual(cmd[18], 0)  # Minutes
    self.assertEqual(cmd[19], 30)  # Seconds

  def test_wash_command_with_soak_time_over_minute(self):
    """Wash with 90 second soak time (1 minute 30 seconds)."""
    cmd = self.backend._build_wash_command(
      cycles=1,
      dispense_volume=300.0,
      soak_time=90.0,  # 90 seconds = 1 minute, 30 seconds
      final_aspirate=True,
      buffer="A",
      dispense_flow_rate=7,
      dispense_offset_x=0,
      dispense_offset_y=0,
      dispense_offset_z=120,
      aspirate_travel_rate=3,
      aspirate_delay_ms=5000,
      aspirate_offset_x=0,
      aspirate_offset_y=0,
      aspirate_offset_z=29,
    )

    # Soak duration: 1 minute, 30 seconds
    self.assertEqual(cmd[18], 1)  # Minutes
    self.assertEqual(cmd[19], 30)  # Seconds

  def test_wash_command_no_final_aspirate(self):
    """Wash without final aspirate."""
    cmd = self.backend._build_wash_command(
      cycles=1,
      dispense_volume=300.0,
      soak_time=0.0,
      final_aspirate=False,
      buffer="A",
      dispense_flow_rate=7,
      dispense_offset_x=0,
      dispense_offset_y=0,
      dispense_offset_z=120,
      aspirate_travel_rate=3,
      aspirate_delay_ms=5000,
      aspirate_offset_x=0,
      aspirate_offset_y=0,
      aspirate_offset_z=29,
    )

    # Final aspirate: False = 0
    self.assertEqual(cmd[3], 0)

  def test_wash_command_minimum_length(self):
    """Wash command should have at least 20 bytes."""
    cmd = self.backend._build_wash_command(
      cycles=1,
      dispense_volume=300.0,
      soak_time=0.0,
      final_aspirate=True,
      buffer="A",
      dispense_flow_rate=7,
      dispense_offset_x=0,
      dispense_offset_y=0,
      dispense_offset_z=120,
      aspirate_travel_rate=3,
      aspirate_delay_ms=5000,
      aspirate_offset_x=0,
      aspirate_offset_y=0,
      aspirate_offset_z=29,
    )
    self.assertGreaterEqual(len(cmd), 20)


class TestWashCaptureVectors(unittest.TestCase):
  """Byte-exact match against reference captures from real EL406 hardware.

  Each test builds a command with the same parameters as a LHC protocol and
  asserts exact match against the MANIFOLD_WASH bytes extracted from captures.
  """

  def setUp(self):
    self.backend = BioTekEL406Backend()

  def test_baseline_tobias_test1(self):
    """Baseline wash: 15 cycles, 300uL, flow 7, Z=121, travel 3, asp Z=29."""
    expected = bytes.fromhex(
      "040001000f0003412c01070000790000000900000000000000000000000300001d000000001d"
      "0000000000000000000000000300001d000000001d000000000000000000412c010700007900"
      "0000090000000000000000000000030000000000000000000000"
    )
    cmd = self.backend._build_wash_composite_command()
    self.assertEqual(cmd, expected)

  def test_aspirate_xyz_capture(self):
    """Aspirate with Z=28, X=5, Y=10."""
    expected = bytes.fromhex(
      "040001000f0003412c01070000790000000900000000000000000000000300001c000000001c"
      "00000000000000000000000003050a1c000000001d000000000000000000412c010700007900"
      "0000090000000000000000000000030000000000000000000000"
    )
    cmd = self.backend._build_wash_composite_command(aspirate_z=28, aspirate_x=5, aspirate_y=10)
    self.assertEqual(cmd, expected)

  def test_secondary_aspirate_capture(self):
    """Secondary aspirate enabled — mode byte at Asp2[6]."""
    expected = bytes.fromhex(
      "040001000f0003412c01070000790000000900000000000000000000000300001d000000001d"
      "0000000000000000000000000300001d000100001d000000000000000000412c010700007900"
      "0000090000000000000000000000030000000000000000000000"
    )
    cmd = self.backend._build_wash_composite_command(secondary_aspirate=True)
    self.assertEqual(cmd, expected)

  def test_final_secondary_aspirate_capture(self):
    """Final secondary aspirate — mode byte at Asp1[5], Z at Asp1[8-9].

    LHC wire capture from tobias-test4 Step 11: wash(cycles=2, buffer='A',
    final_secondary_aspirate=True, final_secondary_z=40).
    """
    expected = bytes.fromhex(
      "040001000f0002412c010700007900000009000000000000000000000003"
      "00001d000100002800000000000000000000000003"
      "00001d000000001d000000000000000000"
      "412c0107000079000000090000000000000000000000"
      "030000000000000000000000"
    )
    cmd = self.backend._build_wash_composite_command(
      cycles=2, buffer="A",
      final_secondary_aspirate=True, final_secondary_z=40
    )
    self.assertEqual(cmd, expected)

  def test_bottom_wash_capture(self):
    """Bottom wash: header[1]=1, Dispense1 vol=200, flow=5."""
    expected = bytes.fromhex(
      "040101000f000341c800050000790000000900000000000000000000000300001d000000001d"
      "0000000000000000000000000300001d000000001d000000000000000000412c010700007900"
      "0000090000000000000000000000030000000000000000000000"
    )
    cmd = self.backend._build_wash_composite_command(
      bottom_wash=True, bottom_wash_volume=200.0, bottom_wash_flow_rate=5
    )
    self.assertEqual(cmd, expected)

  def test_pre_dispense_between_cycles_capture(self):
    """Pre-dispense between cycles: Dispense2 pre-disp vol=50 at [76]."""
    expected = bytes.fromhex(
      "040001000f0003412c01070000790000000900000000000000000000000300001d000000001d"
      "0000000000000000000000000300001d000000001d000000000000000000412c010700007900"
      "3200090000000000000000000000030000000000000000000000"
    )
    cmd = self.backend._build_wash_composite_command(
      pre_dispense_between_cycles_volume=50.0, pre_dispense_between_cycles_flow_rate=9
    )
    self.assertEqual(cmd, expected)

  def test_aspirate_delay_capture(self):
    """Aspirate delay: aspirate_delay=1ms, final_aspirate_delay=2ms.

    384-well plate (prefix=0x01). Uses 384-well backend for full byte-exact match.
    Delay encoding: wire [48-49]=delay LE (spans Asp1[19] + Asp2[0]).
    Secondary Z = 22 (explicitly set, independent of aspirate_z).
    """
    capture_hex = (
      "010001000f0003"
      "4164000700007800000009000000000000000000020003000016000000001600000000000000"
      "000000010003000016000000001600000000000000000041640007000078000000090000"
      "000000000000000000030000000000000000000000"
    )
    expected = bytes.fromhex(capture_hex)
    backend_384 = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)
    cmd = backend_384._build_wash_composite_command(
      cycles=3,
      sector_mask=0x0F,
      buffer="A",
      dispense_volume=100.0,
      dispense_flow_rate=7,
      dispense_z=120,
      aspirate_travel_rate=3,
      aspirate_z=22,
      pre_dispense_flow_rate=9,
      aspirate_delay_ms=1,
      final_aspirate_delay_ms=2,
      secondary_z=22,
    )
    self.assertEqual(cmd, expected)

  def test_p384_sector_plate_format_capture(self):
    """384-well sector wash: 2 commands with different sector masks and formats.

    384-well plate (prefix=0x01). Uses 384-well backend with sector_mask
    and wash_format for full byte-exact match.
    All share: vol=100, flow=7, dispZ=120, aspZ=22, secZ=22, travelRate=3.
    """
    backend_384 = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)

    # Command 0: Plate format, sector_mask=0x0E (Q2+Q3+Q4), 1 cycle
    cap0 = bytes.fromhex(
      "010001000e00014164000700007800000009000000000000000000000003000016000000001600"
      "000000000000000000000003000016000000001600000000000000000041640007000078000000"
      "090000000000000000000000030000000000000000000000"
    )
    cmd0 = backend_384._build_wash_composite_command(
      cycles=1,
      sector_mask=0x0E,
      buffer="A",
      dispense_volume=100.0,
      dispense_flow_rate=7,
      dispense_z=120,
      aspirate_travel_rate=3,
      aspirate_z=22,
      pre_dispense_flow_rate=9,
      secondary_z=22,
    )
    self.assertEqual(cmd0, cap0)

    # Command 2: Sector format, sector_mask=0x0F, 1 cycle — byte [3]=0x01
    cap2 = bytes.fromhex(
      "010001010f00014164000700007800000009000000000000000000000003000016000000001600"
      "000000000000000000000003000016000000001600000000000000000041640007000078000000"
      "090000000000000000000000030000000000000000000000"
    )
    cmd2 = backend_384._build_wash_composite_command(
      cycles=1,
      sector_mask=0x0F,
      buffer="A",
      dispense_volume=100.0,
      dispense_flow_rate=7,
      dispense_z=120,
      aspirate_travel_rate=3,
      aspirate_z=22,
      pre_dispense_flow_rate=9,
      secondary_z=22,
      wash_format="Sector",
    )
    self.assertEqual(cmd2, cap2)


class TestWash384WellPlateSupport(unittest.TestCase):
  """Test 384-well plate support: plate_type prefix, wash_format, sector_mask."""

  def test_384_well_plate_type_byte(self):
    """384-well backend should produce byte [0] = 0x01."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[0], 0x01)

  def test_96_well_plate_type_byte(self):
    """96-well backend (default) should produce byte [0] = 0x04."""
    backend = BioTekEL406Backend()
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[0], 0x04)

  def test_wash_format_plate_default(self):
    """Default wash_format='Plate' should produce byte [3] = 0x00."""
    backend = BioTekEL406Backend()
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[3], 0x00)

  def test_wash_format_sector(self):
    """wash_format='Sector' should produce byte [3] = 0x01."""
    backend = BioTekEL406Backend()
    cmd = backend._build_wash_composite_command(wash_format="Sector")
    self.assertEqual(cmd[3], 0x01)

  def test_cycles_at_byte6(self):
    """cycles should be encoded at byte [6] (bg.a8)."""
    backend = BioTekEL406Backend()
    cmd = backend._build_wash_composite_command(cycles=5)
    self.assertEqual(cmd[6], 5)

  def test_cycles_default(self):
    """Default cycles=3 should produce byte [6] = 0x03."""
    backend = BioTekEL406Backend()
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[6], 3)

  def test_sector_mask_le_encoding(self):
    """Sector mask should be encoded as 16-bit LE at bytes [4-5] (bg.a7)."""
    backend = BioTekEL406Backend()
    cmd = backend._build_wash_composite_command(sector_mask=0x0E)
    self.assertEqual(cmd[4], 0x0E)
    self.assertEqual(cmd[5], 0x00)

  def test_384_well_full_combination(self):
    """384-well with Sector format and custom sector mask."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)
    cmd = backend._build_wash_composite_command(
      wash_format="Sector", cycles=1, sector_mask=0x0E, aspirate_travel_rate=3
    )
    self.assertEqual(cmd[0], 0x01)  # plate type
    self.assertEqual(cmd[3], 0x01)  # wash format = Sector
    self.assertEqual(cmd[4], 0x0E)  # sector mask low byte
    self.assertEqual(cmd[5], 0x00)  # sector mask high byte
    self.assertEqual(cmd[6], 1)  # wash cycles
    self.assertEqual(cmd[29], 3)  # Asp1 travel rate
    self.assertEqual(cmd[50], 3)  # Asp2 travel rate
    self.assertEqual(len(cmd), 102)


class TestWash384WellValidation(unittest.IsolatedAsyncioTestCase):
  """Test validation of 384-well parameters in wash() API."""

  async def asyncSetUp(self):
    self.backend = BioTekEL406Backend(timeout=0.5)
    await self.backend.setup()
    self.backend.dev.set_read_buffer(b"\x06" * 100)

  async def asyncTearDown(self):
    if self.backend.dev is not None:
      await self.backend.stop()

  async def test_wash_format_invalid(self):
    """wash() should reject invalid wash_format values."""
    with self.assertRaises(ValueError):
      await self.backend.wash(wash_format="Invalid")

  async def test_sectors_invalid(self):
    """wash() should reject out-of-range sector/quadrant values."""
    with self.assertRaises(ValueError):
      await self.backend.wash(sectors=[0])  # Must be 1-4
    with self.assertRaises(ValueError):
      await self.backend.wash(sectors=[5])  # Must be 1-4

  async def test_wash_with_384_params_sends_command(self):
    """wash() should accept and send command with 384-well params."""
    initial_count = len(self.backend.dev.written_data)
    await self.backend.wash(wash_format="Sector", sectors=[2, 3, 4], cycles=1)
    self.assertGreater(len(self.backend.dev.written_data), initial_count)


class TestWashPlateTypeDefaults(unittest.TestCase):
  """Test plate-type-aware defaults for wash parameters.

  Wash defaults are based on plate type:
  - dispense_volume: 300 uL for 96-well (well_count==96), 100 uL for others
  - dispense_z: plate-type-specific manifold dispense Z
  - aspirate_z: plate-type-specific manifold aspirate Z
  - secondary_z: same as aspirate_z default (independent of user-provided aspirate_z)
  """

  def test_96_well_defaults(self):
    """96-well plate should use 96-well defaults (300uL, dispZ=121, aspZ=29)."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_96_WELL)
    cmd = backend._build_wash_composite_command()
    # dispense_volume=300 -> 0x012C LE at Dispense1[1-2] = wire [8-9]
    self.assertEqual(cmd[8], 0x2C)
    self.assertEqual(cmd[9], 0x01)
    # dispense_z=121 -> 0x0079 LE at Dispense1[6-7] = wire [13-14]
    self.assertEqual(cmd[13], 0x79)
    self.assertEqual(cmd[14], 0x00)
    # aspirate_z=29 -> 0x001D at Asp2[4-5] = wire [53-54]
    self.assertEqual(cmd[53], 0x1D)
    self.assertEqual(cmd[54], 0x00)
    # secondary_z=29 at Asp2[9-10] = wire [58-59]
    self.assertEqual(cmd[58], 0x1D)
    self.assertEqual(cmd[59], 0x00)

  def test_384_well_defaults(self):
    """384-well plate should use 384-well defaults (100uL, dispZ=120, aspZ=22)."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)
    cmd = backend._build_wash_composite_command()
    # plate type prefix
    self.assertEqual(cmd[0], 0x01)
    # dispense_volume=100 -> 0x0064 LE at wire [8-9]
    self.assertEqual(cmd[8], 0x64)
    self.assertEqual(cmd[9], 0x00)
    # dispense_z=120 -> 0x0078 LE at wire [13-14]
    self.assertEqual(cmd[13], 0x78)
    self.assertEqual(cmd[14], 0x00)
    # aspirate_z=22 -> 0x0016 at wire [53-54]
    self.assertEqual(cmd[53], 0x16)
    self.assertEqual(cmd[54], 0x00)
    # secondary_z=22 at wire [58-59]
    self.assertEqual(cmd[58], 0x16)
    self.assertEqual(cmd[59], 0x00)
    # Dispense2 mirrors
    self.assertEqual(cmd[69], 0x64)  # vol low
    self.assertEqual(cmd[74], 0x78)  # disp_z low

  def test_384_pcr_defaults(self):
    """384 PCR plate should use its specific defaults (100uL, dispZ=83, aspZ=2)."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_PCR)
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[0], 0x02)  # plate type
    self.assertEqual(cmd[8], 0x64)  # vol=100 low
    self.assertEqual(cmd[13], 0x53)  # dispense_z=83
    self.assertEqual(cmd[53], 0x02)  # aspirate_z=2
    self.assertEqual(cmd[58], 0x02)  # secondary_z=2

  def test_1536_well_defaults(self):
    """1536-well plate: 100uL (1536 wells != 96), dispZ=94, aspZ=42."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_1536_WELL)
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[0], 0x00)  # plate type
    # dispense_volume=100 (1536 wells != 96)
    self.assertEqual(cmd[8], 0x64)
    self.assertEqual(cmd[9], 0x00)
    # dispense_z=94 -> 0x005E
    self.assertEqual(cmd[13], 0x5E)
    self.assertEqual(cmd[14], 0x00)
    # aspirate_z=42 -> 0x002A
    self.assertEqual(cmd[53], 0x2A)
    self.assertEqual(cmd[54], 0x00)

  def test_1536_flange_defaults(self):
    """1536 flange plate: 100uL (1536 wells != 96), dispZ=93, aspZ=13."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_1536_FLANGE)
    cmd = backend._build_wash_composite_command()
    self.assertEqual(cmd[0], 0x0E)  # plate type = 14
    # dispense_volume=100 (1536 wells != 96)
    self.assertEqual(cmd[8], 0x64)
    self.assertEqual(cmd[9], 0x00)
    # dispense_z=93 -> 0x005D
    self.assertEqual(cmd[13], 0x5D)
    self.assertEqual(cmd[14], 0x00)
    # aspirate_z=13 -> 0x000D
    self.assertEqual(cmd[53], 0x0D)
    self.assertEqual(cmd[54], 0x00)

  def test_explicit_values_override_plate_defaults(self):
    """Explicit parameter values should override plate-type defaults."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_384_WELL)
    cmd = backend._build_wash_composite_command(
      dispense_volume=500.0, dispense_z=200, aspirate_z=50, secondary_z=30
    )
    # dispense_volume=500 overrides 100
    self.assertEqual(cmd[8], 0xF4)  # 500 low
    self.assertEqual(cmd[9], 0x01)  # 500 high
    # dispense_z=200 overrides 120
    self.assertEqual(cmd[13], 0xC8)  # 200
    # aspirate_z=50 overrides 22
    self.assertEqual(cmd[53], 0x32)  # 50
    # secondary_z=30 overrides 22
    self.assertEqual(cmd[58], 0x1E)  # 30

  def test_secondary_z_independent_of_aspirate_z(self):
    """secondary_z default should be plate-type default, NOT user aspirate_z."""
    backend = BioTekEL406Backend(plate_type=EL406PlateType.PLATE_96_WELL)
    cmd = backend._build_wash_composite_command(aspirate_z=40)
    # aspirate_z=40 (user override)
    self.assertEqual(cmd[53], 0x28)  # aspirate_z = 40
    # secondary_z should still be 29 (plate-type default), NOT 40
    self.assertEqual(cmd[58], 0x1D)  # secondary_z = 29

  def test_all_plate_types_produce_102_bytes(self):
    """Every plate type should produce exactly 102 bytes with defaults."""
    for pt in EL406PlateType:
      backend = BioTekEL406Backend(plate_type=pt)
      cmd = backend._build_wash_composite_command()
      self.assertEqual(len(cmd), 102, f"Wrong length for {pt.name}")
      self.assertEqual(cmd[0], pt.value, f"Wrong prefix for {pt.name}")


if __name__ == "__main__":
  unittest.main()
