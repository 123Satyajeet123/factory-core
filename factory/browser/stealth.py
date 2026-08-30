"""Audits the page, and asserts the vendor settings the audit depends on. Read at rev b4bad86:
demo_mode is opt-in (session.py:540); python_highlights.py draws on the SCREENSHOT with PIL, not
into the DOM; browser-side highlighting is conditional at dom_watchdog.py:421 and there is a
_build_dom_tree_without_highlights path, so serialisation does not need it. Both highlight flags
off, checked rather than assumed. What reading cannot settle is whether an attached page is
indistinguishable from an unautomated one -- enabled CDP domains are their own question. That is
this module measuring, against a real fingerprinting page.
"""
