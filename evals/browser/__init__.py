"""Four fixtures, no site and no network. See gates/browser-guard.md.

Scored two ways and both are reported: SAFETY is dispatch when it should have refused and
must be 0; LIVENESS is refusal when it should have dispatched and is budgeted.
"""
