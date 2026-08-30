from __future__ import annotations


class Failed(RuntimeError):
    pass


class BrowserFailed(Failed):
    pass


class KernelFailed(Failed):
    pass


class CapabilityFailed(Failed):
    pass


class StoreFailed(Failed):
    pass
