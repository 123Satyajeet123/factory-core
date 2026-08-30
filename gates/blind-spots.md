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

## Result

The sweep is the result. Each of B1–B6 needs its own gate before it needs code, and B6
should be first because it is the only one that changes what happens rather than what is
known about it.
