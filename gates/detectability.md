# Where do we measure detectability, and where do we never measure it?

## The rule, first, because it is the part that matters

**Never calibrate against a site we intend to use.** Tuning against a live commercial
target teaches that target what we look like, burns the account, and produces a number
that is about one vendor's current rules rather than about our driving. Every measurement
below runs against a detector built to be measured against.

A pass on any of these means "our driving has the shape these tests look for". It never
means undetectable, and no result here may be quoted as if it did.

## Targets, verified 2026-08-30 by request and by the GitHub API

**Vendored, and the gate that actually runs:**

| target | what it measures | licence | signal |
|---|---|---|---|
| **BotD** `fingerprintjs/BotD` | a typed automation verdict, computed in the page, no server | MIT | 1,457 stars, pushed 2026-08-11, npm v2.0.0 |
| **CreepJS** `abrahamjuliot/creepjs` | fingerprint entropy, and internal-consistency "lies" | MIT | 2,490 stars, pushed 2026-06-11 |

**BotD is the primary because it is a library rather than a page.** It returns a verdict we
can assert on, offline, with no third party's uptime in the loop. CreepJS is the deeper
audit and is read rather than asserted: it tests *consistency*, which is exactly what this
project's "inject nothing" claim rests on.

**Hosted, read and never shipped:**

| target | status | fronted by | why |
|---|---|---|---|
| `nowsecure.nl` | 200 | Cloudflare (`cf-ray` present) | a real Cloudflare challenge |
| `bot.sannysoft.com` | 200 | Cloudflare | the classic fingerprint table |
| `browserscan.net/bot-detection` | 200 | — | second opinion |
| `deviceandbrowserinfo.com/are_you_a_bot` | 200 | nginx | second opinion |
| `rebrowser-bot-detector` | hosted | — | CDP-specific leaks. **No licence stated**, so never vendored |
| `arh.antoinevastel.com/bots/areyouheadless` | **502, dead** | nginx | do not bother |

`niespodd/browser-fingerprinting` (5,129 stars, pushed 2026-07-27) is the reference for
which protection catches what. Read, never imported.

**Cloudflare is testable after all, and my earlier claim that it was not is withdrawn.**
`nowsecure.nl` sits behind a real Cloudflare challenge and answers 200 to a plain request.
It is somebody else's site, so it is used sparingly and never tuned against — the rule at
the top applies to it exactly as it applies to Apollo.

## What is measured

Both channels, because they fail differently:

- **the browser** — what a page can tell about the binary, the profile and the attach.
  Compare a browser we drive against the same browser opened and left alone. Any signal
  present in one and not the other is ours and is a finding.
- **the driving** — pointer paths, dwell, inter-act rhythm, and landing points. Measured
  from the page's own event stream, which is the same channel a detector reads.

## What would make this dishonest

Reporting the first channel and calling it stealth. A perfect fingerprint with a pointer
that jumps to pixel centres and clicks in the same millisecond is a solved fingerprint and
an unsolved problem.

## Result

(filled in by execution — not by reasoning)
