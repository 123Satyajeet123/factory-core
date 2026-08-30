# How does a cell reach the browser? SETTLED 2026-08-30, by reading both vendors.

The kernel runs in its own interpreter and cannot import the BROWSER machine. A cell
that reaches the browser some other way bypasses the guard, the kept response bodies
and the witness — and an act nobody witnessed can never be promoted.

**Rejected: a second CDP client on the same endpoint.** Works, and was the previous
design. Two actuators, one unguarded, and the question has to be re-measured every
time either vendor moves.

**Settled: MCP, both vendors' own seams.**
- `rlm.mcp` is an MCP *client* — `stdio_client`, `ClientSession`, a server registry,
  `list_tools`, `call_tool`.
- `browser_use/mcp/server.py` shows the pattern is expected on the other side.

`browser/serve.py` is our server, exposing guarded acts; `kernel/tools.py` registers
it. A cell acts through the same `act.py` as every other rung, so the witness applies
by construction.

The vendor's own MCP server is deliberately not exposed: its `browser_click` accepts
`coordinate_x`/`coordinate_y`, the coordinate targeting already measured wrong on a
scaled display.

## Result — 2026-08-30, by execution

    door offers        ['candidates', 'click', 'fetched', 'go', 'write']
    same read: door 4 ms, direct 1 ms, wire 3 ms
    click through door ok=True  delivery=target_hit  detail=pressed via accessible
    covered target     ok=False delivery=intercepted detail=refused: covered DIV
    FAULTS  ways past the guard, or guarded acts that failed : 0

**The open item is answered, and the obvious way to answer it was wrong.** Timing a click
through the door gave 1,135 ms, and almost all of it is travel and rest -- our own pacing.
The wire is the difference between the same read taken through the door and taken directly:
**3 ms**. Quoting the 1,135 would have been a true number that answered a different
question.

**The guard survives the wire, which is the whole reason the door exists.** With an overlay
covering the target, a caller on the other side of MCP gets `intercepted` and nothing is
dispatched -- the same answer the driver gives itself. An act a model causes is guarded
because of where it came from, not because the model chose well.

**No tool takes a coordinate, a selector, an xpath or a node id.** The eval asserts this
against every tool's input schema rather than trusting the file, so adding an unguarded
argument later fails the suite.

**STREAMABLE HTTP, NOT STDIO, and that changed on evidence.** Over stdio the kernel spawns
the server, which would then have to attach its own client -- two sessions on one browser,
with the kept response bodies split across them. `rlm.mcp` supports `type: "http"` with a
`url` as well as stdio, so the door runs in the factory's own process over loopback with
one Browser, one session, one evidence channel.

**Not yet done:** the door is loopback-only and unauthenticated. A capability token is the
next thing it needs, and nothing else on this machine currently listens.
