"""What a person did, reported by the page itself.

LISTENERS ONLY, AND THAT DISTINCTION IS THE WHOLE SAFETY ARGUMENT. This adds
`addEventListener` calls and one global. It redefines no property, replaces no native
method, and leaves every `toString()` reading `[native code]`. The patches measured to cost
detection signals were the ones that lied about `navigator`; see `stealth.py`.

INSTALLED ONLY WHILE RECORDING, NEVER WHILE DRIVING. A person demonstrating is using their
own browser and the page is being driven by a hand. A replay injects nothing at all, which
is the state the stealth argument is about.

TIMING, NEVER CONTENT. Key events record when, and no key. A store of what was typed is a
password store and this project does not hold those.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

#: One global, one name, and nothing else touched. `capture: true` so a page that stops
#: propagation cannot blind the recorder.
WATCH = """
(() => {
  if (window.__factory_watch) return;
  const seen = { moves: [], keys: [], presses: [], releases: [] };
  window.__factory_watch = seen;
  addEventListener('mousemove', e => {
    seen.moves.push([e.clientX, e.clientY, performance.now()]);
    if (seen.moves.length > 20000) seen.moves.splice(0, 10000);
  }, true);
  addEventListener('keydown', () => seen.keys.push(performance.now()), true);
  addEventListener('mousedown', e => {
    const r = e.target && e.target.getBoundingClientRect
      ? e.target.getBoundingClientRect() : null;
    seen.presses.push([
      performance.now(),
      r && r.width ? (e.clientX - r.left) / r.width : null,
      r && r.height ? (e.clientY - r.top) / r.height : null,
    ]);
  }, true);
  addEventListener('mouseup', () => seen.releases.push(performance.now()), true);
})();
"""

DRAIN = """
(() => {
  const seen = window.__factory_watch;
  if (!seen) return null;
  const taken = { moves: seen.moves, keys: seen.keys,
                  presses: seen.presses, releases: seen.releases };
  seen.moves = []; seen.keys = []; seen.presses = []; seen.releases = [];
  return taken;
})()
"""


class Watched(BaseModel):
    """Raw timing, as the page reported it. Milliseconds, page-relative."""

    moves: list[tuple[float, float, float]] = Field(default_factory=list)
    keys: list[float] = Field(default_factory=list)
    #: when, and where in the target's box the press landed, as fractions.
    presses: list[tuple[float, float | None, float | None]] = Field(default_factory=list)
    releases: list[float] = Field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.moves or self.keys or self.presses)


async def watch(page: Any) -> None:
    """Start listening, and keep listening across navigations."""
    await page.add_init_script(WATCH)
    await page.evaluate(WATCH)


async def drain(page: Any) -> Watched:
    """Take what the page has collected and leave it empty."""
    got = await page.evaluate(DRAIN)
    return Watched(**got) if got else Watched()
