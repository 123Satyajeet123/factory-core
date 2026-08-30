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

**Open:** the round-trip cost of one act over stdio. Measure once the wire exists.
