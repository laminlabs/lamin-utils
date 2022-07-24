import os
import sys

from loguru import logger

if os.name == "nt":
    format = "{message}"
else:
    format = "{level.icon} {message}"

default_handler = dict(
    sink=sys.stdout,
    format=format,
)

logger.configure(handlers=[default_handler])
logger.level("SUCCESS", icon="✅")
logger.level("WARNING", icon="🔶")


# ANSI color code: https://gist.github.com/iansan5653/c4a0b9f5c30d74258c5f132084b78db9
ANSI_COLORS = dict(
    bold="\x1b[1m",
    black="\x1b[1;90m",
    red="\x1b[1;91m",
    green="\x1b[1;92m",
    yellow="\x1b[1;93m",
    blue="\x1b[1;94m",
    purple="\x1b[1;95m",
    cyan="\x1b[1;96m",
    white="\x1b[1;97m",
    reset="\x1b[0m",
)


class colors:
    """Coloring texts."""

    @staticmethod
    def bold(text):
        return f"{ANSI_COLORS['bold']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def black(text):
        return f"{ANSI_COLORS['black']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def red(text):
        return f"{ANSI_COLORS['red']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def green(text):
        return f"{ANSI_COLORS['green']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def yellow(text):
        return f"{ANSI_COLORS['yellow']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def blue(text):
        return f"{ANSI_COLORS['blue']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def purple(text):
        return f"{ANSI_COLORS['purple']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def cyan(text):
        return f"{ANSI_COLORS['cyan']}{text}{ANSI_COLORS['reset']}"

    @staticmethod
    def white(text):
        return f"{ANSI_COLORS['white']}{text}{ANSI_COLORS['reset']}"
