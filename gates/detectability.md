# Where do we measure detectability, and where do we never measure it?

## The rule, first, because it is the part that matters

**Never calibrate against a site we intend to use.** Tuning against a live commercial
target teaches that target what we look like, burns the account, and produces a number
that is about one vendor's current rules rather than about our driving. Every measurement
below runs against a detector built to be measured against.

A pass on any of these means "our driving has the shape these tests look for". It never
means undetectable, and no result here may be quoted as if it did.

## Targets, verified 2026-08-30 via the GitHub API

| target | what it measures | licence | signal |
|---|---|---|---|
| **CreepJS** `abrahamjuliot/creepjs` | fingerprint entropy, and internal-consistency "lies" — a claimed property that does not match observed behaviour | MIT | 2,490 stars, pushed 2026-06-11 |
| **rebrowser-bot-detector** `rebrowser/rebrowser-bot-detector` | runtime leaks specific to CDP-driven browsers — the class our attach could produce | **NONE stated** | 158 stars, pushed 2024-10-25 |
| `bot.sannysoft.com` | the classic headless battery | hosted | — |

**CreepJS is the primary and can be vendored.** MIT, current, and it tests the thing this
project's stealth argument rests on: consistency. Our claim is that we inject nothing, so
there is nothing to be inconsistent about; that claim is exactly what CreepJS is built to
falsify.

**rebrowser-bot-detector states no licence, so it is not vendored.** No licence means no
grant to copy or redistribute. It is used at its hosted address, read and never shipped.
Its value is that it targets CDP leaks specifically rather than headless-ness.

**Cloudflare cannot be self-hosted.** A challenge only exists on a protected origin. If a
Cloudflare measurement is wanted it needs a page we control behind our own Cloudflare
account — a real one, deliberately provisioned — and not somebody else's login wall.

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
