"""THE ONLY VENDOR-SEAM FILE IN THIS TREE. Subclasses browser_use BaseWatchdog
(browser/watchdog_base.py:15) with LISTENS_TO/EMITS, attached via attach_to_session. Their
BrowserStateSummary carries a count of in-flight requests, never the payload;
Network.getResponseBody exists only inside har_recording_watchdog.py. Issued from inside a CDP
event handler on the same connection it deadlocks: record in the handler, fetch on drain.
"""
