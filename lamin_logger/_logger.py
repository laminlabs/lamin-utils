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
import logging
import platform
from datetime import datetime, timedelta, timezone
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from typing import Optional

VERBOSITY_TO_LOGLEVEL = {
    "error": "ERROR",
    "warning": "WARNING",
    "info": "INFO",
    "hint": "HINT",
    "debug": "DEBUG",
}
for v, level in enumerate(list(VERBOSITY_TO_LOGLEVEL.values())):
    VERBOSITY_TO_LOGLEVEL[v] = level  # type: ignore


class Settings:
    @property
    def versbosity(self) -> int:
        return 1


HINT = (INFO + DEBUG) // 2
logging.addLevelName(HINT, "HINT")


class RootLogger(logging.RootLogger):
    def __init__(self, level, settings=None):
        super().__init__(level)
        self.propagate = False
        if settings is None:
            settings = Settings()
        self.settings = settings
        RootLogger.manager = logging.Manager(self)

    def log(  # type: ignore
        self,
        level: int,
        msg: str,
        *,
        extra: Optional[dict] = None,
        time: datetime = None,
        deep: Optional[str] = None,
    ) -> datetime:
        """Log message with level and return current time.

        Args:
            level: Logging level.
            msg: Message to display.
            time: A time in the past. If this is passed, the time difference from then
                to now is appended to `msg` as ` (HH:MM:SS)`.
                If `msg` contains `{time_passed}`, the time difference is instead
                inserted at that position.
            deep: If the current verbosity is higher than the log function’s level,
                this gets displayed as well
            extra: Additional values you can specify in `msg` like `{time_passed}`.
        """
        now = datetime.now(timezone.utc)
        time_passed: timedelta = None if time is None else now - time  # type: ignore
        extra = {
            **(extra or {}),
            "deep": deep if self.settings.verbosity.level < level else None,
            "time_passed": time_passed,
        }
        super().log(level, msg, extra=extra)
        return now

    def critical(self, msg, *, time=None, deep=None, extra=None) -> datetime:  # type: ignore  # noqa
        return self.log(CRITICAL, msg, time=time, deep=deep, extra=extra)

    def error(self, msg, *, time=None, deep=None, extra=None) -> datetime:  # type: ignore  # noqa
        return self.log(ERROR, msg, time=time, deep=deep, extra=extra)

    def warning(self, msg, *, time=None, deep=None, extra=None) -> datetime:  # type: ignore  # noqa
        return self.log(WARNING, msg, time=time, deep=deep, extra=extra)

    def info(self, msg, *, time=None, deep=None, extra=None) -> datetime:  # type: ignore  # noqa
        return self.log(INFO, msg, time=time, deep=deep, extra=extra)

    def hint(self, msg, *, time=None, deep=None, extra=None) -> datetime:  # type: ignore  # noqa
        return self.log(HINT, msg, time=time, deep=deep, extra=extra)

    def debug(self, msg, *, time=None, deep=None, extra=None) -> datetime:  # type: ignore  # noqa
        return self.log(DEBUG, msg, time=time, deep=deep, extra=extra)


def _set_log_file(settings):
    file = settings.logfile
    name = settings.logpath
    root = settings._root_logger
    h = logging.StreamHandler(file) if name is None else logging.FileHandler(name)
    h.setFormatter(_LogFormatter())
    h.setLevel(root.level)
    if len(root.handlers) == 1:
        root.removeHandler(root.handlers[0])
    elif len(root.handlers) > 1:
        raise RuntimeError("Lamin's root logger somehow got more than one handler")
    root.addHandler(h)


def set_log_level(settings, level: int):
    root = settings._root_logger
    root.setLevel(level)
    (h,) = root.handlers  # may only be 1
    h.setLevel(level)


icons = {
    40: "❌",  # hint
    30: "🔶",  # warning
    25: "✅",  # success
    15: "💡",  # hint
}


class _LogFormatter(logging.Formatter):
    def __init__(
        self, fmt="{levelname}: {message}", datefmt="%Y-%m-%d %H:%M", style="{"
    ):
        super().__init__(fmt, datefmt, style)

    def base_format(self, record: logging.LogRecord):
        if platform.system() == "Windows":
            return f"{record.levelname}:" + " {message}"
        else:
            return f"{icons[record.levelno]}" + " {message}"

    def format(self, record: logging.LogRecord):
        format_orig = self._style._fmt
        self._style._fmt = self.base_format(record)
        if record.time_passed:  # type: ignore
            # strip microseconds
            if record.time_passed.microseconds:  # type: ignore
                record.time_passed = timedelta(  # type: ignore
                    seconds=int(record.time_passed.total_seconds())  # type: ignore
                )
            if "{time_passed}" in record.msg:
                record.msg = record.msg.replace(
                    "{time_passed}", str(record.time_passed)  # type: ignore
                )
            else:
                self._style._fmt += " ({time_passed})"
        if record.deep:  # type: ignore
            record.msg = f"{record.msg}: {record.deep}"  # type: ignore
        result = logging.Formatter.format(self, record)
        self._style._fmt = format_orig
        return result
