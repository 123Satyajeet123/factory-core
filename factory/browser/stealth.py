"""Audits the page, and asserts the vendor settings the audit depends on. browser_use
highlight_elements defaults TRUE (profile.py:686) and injects overlays on every interaction;
dom_highlight_elements likewise. Both off, checked rather than assumed. Injects nothing of its
own -- what makes this clean is a real binary, a persistent profile and a plain CDP attach.
"""
