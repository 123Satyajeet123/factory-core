"""Our profile, persistent, launched by us. Nothing here is browser_use BrowserProfile.

WE LAUNCH, THEY NEVER DO. browser_use/browser/profile.py:428 adds --enable-automation and
:193 --disable-blink-features=AutomationControlled, then masks the result in JS -- the
approach measured to cost signals rather than save them.
"""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path

from factory.core.errors import BrowserFailed

#: Real binaries, in the order a person is most likely to already be signed in to.
#: `families.py` replaces this ordering with a measured one; this is the fallback.
BINARIES = (
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def executable() -> str:
    for path in BINARIES:
        if Path(path).exists():
            return path
    raise BrowserFailed(f"no browser found; looked in {BINARIES}")


def taken(port: int) -> bool:
    """Whether something already listens there.

    A debugging port held by another browser -- a stale one from a sibling project is the
    ordinary case -- makes `launch` succeed and the attach time out fifteen seconds later
    with "never opened its debugging port", which blames the wrong thing.
    """
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


def launch(profile: Path, port: int) -> subprocess.Popen[bytes]:
    """A debuggable browser on a persistent profile, and no automation flags.

    The flag list is deliberately short. Every switch here is one a person's own browser
    would also have; nothing announces that this session is driven.
    """
    if taken(port):
        raise BrowserFailed(
            f"port {port} already has a listener; another browser is using this debugging "
            f"port and this one would never be reachable")
    profile.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        [executable(),
         f"--remote-debugging-port={port}",
         f"--user-data-dir={profile}",
         "--no-first-run",
         "--no-default-browser-check"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
