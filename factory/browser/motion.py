"""Pointer path geometry, asked of ghost-cursor over one long-lived process.

WHY NOT OURS. Measured in gates/pointer-motion.md: our quadratic with equal parameter
steps put the velocity peak at 100% of the path, so the pointer accelerated into its
target. A hand decelerates onto it.

WHY NO FALLBACK. A fallback would be a second motion model, silently worse, chosen exactly
when nobody is looking. If node is missing this raises and says so.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import threading
from pathlib import Path

HERE = Path(__file__).parent
SERVER = HERE / "motion.js"


class Paths:
    """One node process, shared. Not per move."""

    _lock = threading.Lock()
    _shared: Paths | None = None

    def __init__(self) -> None:
        if not (HERE.parents[1] / "node_modules" / "ghost-cursor").exists():
            raise RuntimeError("ghost-cursor is not installed; run `npm install`")
        self._next = 0
        self._process = subprocess.Popen(
            ["node", str(SERVER)], cwd=HERE.parents[1],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    @classmethod
    def shared(cls) -> Paths:
        with cls._lock:
            if cls._shared is None or cls._shared._process.poll() is not None:
                cls._shared = cls()
            return cls._shared

    def between(self, start: tuple[float, float],
                end: tuple[float, float]) -> list[tuple[float, float]]:
        """Blocking. Callers on an event loop must go through `between_async`."""
        with self._lock:
            self._next += 1
            asked = {"id": self._next, "from": list(start), "to": list(end)}
            assert self._process.stdin and self._process.stdout
            self._process.stdin.write(json.dumps(asked) + "\n")
            self._process.stdin.flush()
            answer = json.loads(self._process.stdout.readline())
        if "error" in answer:
            raise RuntimeError(f"path generation failed: {answer['error']}")
        return [(x, y) for x, y in answer["points"]]

    def close(self) -> None:
        self._process.terminate()


def between(start: tuple[float, float],
            end: tuple[float, float]) -> list[tuple[float, float]]:
    return Paths.shared().between(start, end)


async def between_async(start: tuple[float, float],
                        end: tuple[float, float]) -> list[tuple[float, float]]:
    """The same, off the event loop.

    A blocking readline on the loop stops every other coroutine, including whatever would
    have timed it out, so the whole run stalls with nothing to show for it.
    """
    return await asyncio.to_thread(between, start, end)
