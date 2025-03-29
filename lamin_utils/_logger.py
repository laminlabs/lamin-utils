# Parts of this class are from the Scanpy equivalent, see license below

# BSD 3-Clause License

# Copyright (c) 2017 F. Alexander Wolf, P. Angerer, Theis Lab
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""Logging and Profiling."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

HINT, SAVE, SUCCESS, PRINT, IMPORTANT = 15, 21, 25, 41, 31
for name in ["HINT", "SAVE", "SUCCESS", "PRINT", "IMPORTANT"]:
    logging.addLevelName(globals()[name], name)

LEVEL_TO_ICONS = {
    logging.ERROR: "[red]✗[/]",
    logging.CRITICAL: "[red]✗[/]",
    IMPORTANT: "[green]→[/]",
    logging.WARNING: "[yellow]![/]",
    SUCCESS: "[green]✓[/]",
    SAVE: "[green]✓[/]",
    logging.INFO: "[blue]•[/]",
    HINT: "[cyan]•[/]",
    logging.DEBUG: "[grey50]•[/]",
}


class RootLogger(logging.RootLogger):
    def __init__(self, level="INFO"):
        super().__init__(level)
        self.propagate = False
        self._verbosity = 1
        self.indent = ""
        self.handler = RichHandler(
            console=Console(),
            show_time=False,
            show_path=False,
            show_level=False,
            markup=True,
        )
        self.addHandler(self.handler)

    def _log_wrapper(
        self,
        level: int,
        msg: Any,
        *args: Any,
        time: datetime | None = None,
        deep: str | None = None,
        **kwargs: Any,
    ) -> datetime:
        now = datetime.now(timezone.utc)
        icon = LEVEL_TO_ICONS.get(level, "")
        msg = f"{icon} {self.indent}{msg}" if icon else f"{self.indent}{msg}"

        if time:
            diff = now - time
            msg = f"{msg} ({diff})"
        if deep and self._verbosity >= level:
            msg = f"{msg}: {deep}"

        super().log(level, msg, *args, **kwargs)
        return now

    def critical(self, msg, *args, **kwargs):
        return self._log_wrapper(logging.CRITICAL, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self._log_wrapper(logging.ERROR, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return self._log_wrapper(logging.WARNING, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return self._log_wrapper(logging.INFO, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        return self._log_wrapper(logging.DEBUG, msg, *args, **kwargs)

    def important(self, msg, *args, **kwargs):
        return self._log_wrapper(IMPORTANT, msg, *args, **kwargs)

    def success(self, msg, *args, **kwargs):
        return self._log_wrapper(SUCCESS, msg, *args, **kwargs)

    def save(self, msg, *args, **kwargs):
        return self._log_wrapper(SAVE, msg, *args, **kwargs)

    def hint(self, msg, *args, **kwargs):
        return self._log_wrapper(HINT, msg, *args, **kwargs)

    def print(self, msg, *args, **kwargs):
        return self._log_wrapper(PRINT, msg, *args, **kwargs)

    def download(self, msg, *args, **kwargs):
        return self.save(msg, *args, **kwargs)

    def set_verbosity(self, level: int) -> None:
        if level not in {0, 1, 2, 3, 4, 5}:
            raise ValueError("verbosity must be between 0 and 5")
        self._verbosity = level
        level_map = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: SUCCESS,
            3: logging.INFO,
            4: HINT,
            5: logging.DEBUG,
        }
        self.setLevel(level_map[level])

    def mute(self):
        class Muted:
            def __init__(self, logger):
                self.logger = logger
                self.prev_level = None

            def __enter__(self):
                self.prev_level = self.logger._verbosity
                self.logger.set_verbosity(0)

            def __exit__(self, *_):
                self.logger.set_verbosity(self.prev_level)

        return Muted(self)


logger = RootLogger()
