# Raise warnings for python versions that are not tested
import platform

from packaging import version

from ._core import logger

py_version = version.parse(platform.python_version())


def py_version_warning():
    if (py_version >= version.parse("3.11.0")) or (py_version < version.parse("3.7.0")):
        logger.warning(
            "Python versions < 3.7.0 or >= 3.11.0 are currently not tested, use at your"
            " own risk."
        )
