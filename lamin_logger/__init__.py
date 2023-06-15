"""Logging setup.

Import the package::

   import lamin_logger

This is the complete API reference:

.. autosummary::
   :toctree: .

   colors
"""

__version__ = "0.4.0"

from ._core import colors  # noqa
from ._logger import logger
from ._python_version import py_version_warning  # noqa
