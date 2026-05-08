from __future__ import annotations

import os
import sys
import time
from typing import TextIO


RED = "\033[31m"
RESET = "\033[0m"


def supports_color(stream: TextIO) -> bool:
    return (
        hasattr(stream, "isatty")
        and stream.isatty()
        and os.environ.get("NO_COLOR") is None
    )


def red(text: str, stream: TextIO | None = None) -> str:
    stream = stream or sys.stderr
    if supports_color(stream):
        return f"{RED}{text}{RESET}"
    return text


def print_error(message: str, stream: TextIO | None = None) -> None:
    stream = stream or sys.stderr
    print(red(f"ERROR {message}", stream), file=stream)


class ProgressBar:
    def __init__(
        self,
        label: str,
        stream: TextIO | None = None,
        width: int = 18,
        interval_seconds: float = 0.5,
        enabled: bool | None = None,
    ):
        self.label = label
        self.stream = stream or sys.stderr
        self.width = width
        self.interval_seconds = interval_seconds
        if enabled is None:
            enabled = hasattr(self.stream, "isatty") and self.stream.isatty()
        self.enabled = enabled
        self._started_at = time.monotonic()
        self._next_update = 0.0

    def update(self, message: str) -> None:
        if not self.enabled:
            return

        now = time.monotonic()
        if now < self._next_update:
            return

        elapsed = int(now - self._started_at)
        position = int((now - self._started_at) / self.interval_seconds) % self.width
        bar = "=" * position + ">" + "." * (self.width - position - 1)
        minutes, seconds = divmod(elapsed, 60)
        self.stream.write(
            f"\r{self.label} [{bar}] {minutes:02d}:{seconds:02d} {message}"
        )
        self.stream.flush()
        self._next_update = now + self.interval_seconds

    def finish(self, message: str) -> None:
        if not self.enabled:
            return

        elapsed = int(time.monotonic() - self._started_at)
        minutes, seconds = divmod(elapsed, 60)
        self.stream.write(
            "\r"
            + " " * (self.width + len(self.label) + len(message) + 16)
            + "\r"
            + f"{self.label} [{'=' * self.width}] {minutes:02d}:{seconds:02d} {message}\n"
        )
        self.stream.flush()

    def clear(self) -> None:
        if not self.enabled:
            return

        self.stream.write("\r" + " " * 100 + "\r")
        self.stream.flush()
