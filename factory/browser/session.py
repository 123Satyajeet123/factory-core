"""BrowserSession(cdp_url=...) against the browser already running. WE NEVER USE THEIR LAUNCH PATH:
browser_use/browser/profile.py:428 adds --enable-automation and :193 --disable-blink-
features=AutomationControlled, and masks the result in JS -- the approach measured here to cost
signals rather than save them. Attaching means their flag list never applies.
"""
