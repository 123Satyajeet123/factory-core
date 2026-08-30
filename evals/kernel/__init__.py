"""Isolation, top-level await, surviving task, interrupt, hung cell.

K1 and K2 are the ones that matter: a cell that can read a key or import this package has
no isolation, whatever the other three do. See gates/kernel-isolation.md.
"""
