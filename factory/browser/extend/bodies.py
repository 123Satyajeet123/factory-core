"""Subclass BaseWatchdog (browser/watchdog_base.py) with LISTENS_TO/EMITS, attached via
attach_to_session. Their BrowserStateSummary carries a count of in-flight requests, never the
payload; Network.getResponseBody exists only inside har_recording_watchdog.py, not as a channel
anything reads. getResponseBody issued from inside a CDP event handler on the same connection
deadlocks: record in the handler, fetch on drain.
"""
