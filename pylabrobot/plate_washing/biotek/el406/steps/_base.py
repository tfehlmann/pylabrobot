"""Base mixin providing type stubs for EL406 step sub-mixins.

Sub-mixins inherit from this class so they can reference
``self._send_step_command`` and ``self.timeout`` without circular imports.
"""

from __future__ import annotations


class EL406StepsBaseMixin:
  """Type stubs consumed by the per-subsystem step mixins."""

  timeout: float

  async def _send_step_command(
    self,
    framed_message: bytes,
    timeout: float = ...,  # type: ignore[assignment]
  ) -> bytes:
    ...
