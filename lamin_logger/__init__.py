"""Logging setup.

Import the package::

   import lamin_logger

This is the complete API reference:

.. autosummary::
   :toctree: .

   colors
"""

__version__ = "0.1.5"

from . import _configure_external  # noqa
from ._core import colors, logger  # noqa
from ._python_version import py_version_warning  # noqa
