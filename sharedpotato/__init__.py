"""
sharedpotato package

A lightweight utility library for managing shared asynchronous objects.

Modules:
    - asyncvlog: Verbose logging helpers
    - sharedobj: AsyncSharedObject core implementation

This file makes the package importable as `import sharedpotato`.
"""

__version__ = "0.1.0"

from .sharedobj import AsyncSharedObject, SharedObjectClosed, LockTimeout, HandlerTimeout
from . import asyncvlog as vlog
