# What happens on a page that we do not see happening?

Run 2026-08-30, on a fixture built to do ordinary things the machinery might not record.
Not a pass/fail suite: it prints what the page did beside what we kept, and the difference
is the finding.

**Why this is worth its own file.** Every other gate asks whether something we built works.
A gap here does not announce itself — the ledger looks complete, the run looks clean, and
the missing part leaves no evidence it was missing. That is the failure mode this project
keeps finding one level at a time, and this is the deliberate sweep for it.

## Result — by execution

    the page saw     : ['scroll', 'select:beta']
    we recorded      : 1 acts, kinds ['press']
        press  button 'plain'

    page errors      : NOT CAPTURED
    failed requests  : NOT CAPTURED
    dialogs          : NOT CAPTURED
    exchanges kept   : 3
    a control inside an iframe: no match

## Six blind spots, all of them silent

**B1 — `Doing` has three members and a person has more.** Scroll and a select happened; the
page recorded both and the ledger recorded neither. There is no SCROLL, no SELECT, no
keyboard navigation, no drag, no copy. A demonstration using any of them produces a shorter
ledger with nothing marking the hole, and the compiler induces a program confidently missing
those steps.

**B2 — nothing scrolls.** The guard refuses an off-viewport target (`outside`) instead of
bringing it into view, which is correct as a guard and useless as a capability. In this run
three clicks after a scroll failed for exactly that reason — and my eval had scrolled the
page itself, so the machinery was right and the test was naive.

**B3 — a control inside an iframe cannot be addressed.** `no match`.
`Accessibility.queryAXTree` runs against the main document. Spreadsheets, editors, payment
forms and consent walls are all frames.

**B4 — a page that throws looks fine.** No `pageerror` is collected, so a step that
"succeeded" while the page's own JavaScript failed is indistinguishable from one that worked.

**B5 — a request that fails at the network level leaves no trace.** `bodies` records
`Network.responseReceived`; a request that never gets a response is simply absent. A 404 IS
captured, because it has a status. A dropped connection is not.

**B6 — dialogs are invisible, and Playwright dismisses them by default.** A `confirm()` a
person clicked through in a demonstration is silently answered "cancel" on replay, and
neither the ledger nor the receipt says so.

## What is NOT wrong

The exchanges channel worked (3 kept), the guard refused correctly, and the recorder caught
what it has words for. Nothing here is a bug in something built; every one is something not
built, which is why none of them shows up as a failure.

## Ranked by how much damage they do quietly

1. **B6 dialogs** — changes behaviour, silently, on an act that already got a permit.
2. **B1 the vocabulary** — makes a ledger wrong rather than short, and the compiler cannot
   tell.
3. **B3 iframes** — a whole surface addressable by nothing.
4. **B2 scroll** — loud rather than silent: it refuses, and the refusal says `outside`.
5. **B4 / B5** — a witness with a contract would still refute, so they degrade diagnosis
   rather than correctness.

## Result — all six closed, 2026-08-30

    the page saw   : ['scroll', 'select:beta', 'scroll', 'dialog', 'fetch', 'throw']
    we recorded    : press, scroll, scroll, press, key, press, press
    page errors    : ['a page error']
    dialogs        : ['go on?']
    a control inside an iframe: one match

**B1** `Doing` now has scroll, select, key and answer, the recorder reports them, and the
harness performs them. A select is not typing: both raise `input`, and recording a pick as a
write replays it by typing an option's text into a control with no text.

**B2** `guard.press` scrolls a target into view before measuring. A no-op when it is already
visible, and the hit test still runs afterwards, so scrolling cannot smuggle a press onto
something that moved.

**B3** `Accessibility.queryAXTree` takes a node, not a frame id, and a frame's content
document has no node id registered until something pierces for it. `DOM.getDocument` with
`pierce` does, and every document is asked. Two dead ends on the way, both recorded: a
`frameId` argument the call rejects, and a `DOM.getFrameOwner` path whose node the query
could not find.

**B4** page errors are collected onto the act. **B5** so are failed requests -- and a 404 is
a RESPONSE, not a failure, so a fixture that 404s correctly produces none.

**B6, and the finding is sharper than the fix.** A dialog handler that only OBSERVES
suppresses the default dismissal and blocks the page forever: measured on an eval of ours
that hung a browser for seven minutes doing exactly that. And with a connection attached the
person cannot answer either -- whatever we do is the answer. So the driver dismisses, which
is the reversible choice, and records it loudly; `Doing.ANSWER` replays a demonstrated
answer for the next dialog only. A standing "always accept" is not consent, it is the guard
removed.

## Three of these were my eval's fault, not the machinery's

A select set by `dispatchEvent(new Event('change'))` raises no `input`, so the recorder
correctly saw nothing. Exchanges read after the acts had already drained them reported zero.
A 404 was called a failed request. Each looked like a blind spot and was a bad test.
