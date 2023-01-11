# Raise warnings for python versions that are not tested
import platform
from pathlib import Path
from typing import Optional

import yaml  # type: ignore
from packaging import version

from ._core import logger

py_version = version.parse(platform.python_version())


def py_version_warning(pkg_filepath: Optional[str]):
    if pkg_filepath is not None:
        with open(
            Path(pkg_filepath).parent.parent / ".github/workflows/build.yml", "r"
        ) as f:
            versions = (
                yaml.safe_load(f)
                .get("jobs")
                .get("build")
                .get("strategy")
                .get("matrix")
                .get("python-version")
            )
        min_v = versions[0]
        max_v = versions[-1]
    else:
        min_v = "3.7"
        max_v = "3.11"

    max_v_plus_1 = (
        ".".join(max_v.split(".")[:-1]) + "." + str(int(max_v.split(".")[-1]) + 1)
    )

    if py_version >= version.parse(max_v_plus_1) or py_version < version.parse(min_v):
        logger.warning(
            f"Python versions < {min_v} or >= {max_v_plus_1} are currently not tested,"
            " use at your own risk."
        )
