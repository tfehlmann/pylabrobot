"""Pytest conftest for BioTek EL406 tests.

Sets up the mock FTDI device before any test modules are imported.

We use importlib to load mock_tests directly (bypassing el406/__init__.py)
because __init__.py imports backend.py which imports the real pylibftdi.
The mock must be installed BEFORE those imports happen.
"""

import importlib
import pathlib

_mock_tests_path = pathlib.Path(__file__).parent / "el406" / "mock_tests.py"
_spec = importlib.util.spec_from_file_location(
  "pylabrobot.plate_washing.biotek.el406.mock_tests", _mock_tests_path
)
_mock_tests = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mock_tests)

# setup_mock() is called at module level in mock_tests,
# so executing the module above ensures the mock is installed
# before any test file imports the backend.
