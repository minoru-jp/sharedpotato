
import asyncio

class SharedObjectClosed(Exception):
    pass

class LockTimeout(asyncio.TimeoutError):
    pass

class HandlerTimeout(asyncio.TimeoutError):
    pass

