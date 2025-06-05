"""
This module provides a lightweight interface and utility for acquiring exclusive asynchronous locks with timeout handling.

It defines a protocol for exclusive locks and provides a context manager that ensures lock acquisition and release within a specified timeout. It is designed to work with locks such as asyncio.Lock and asyncio.Condition that ensure mutual exclusion.

Counting locks such as asyncio.Semaphore, which allow multiple concurrent holders, are not supported. The caller must ensure the lock passed conforms to the expected behavior, as this module does not perform runtime validation.

ja:
このモジュールは、非同期環境において排他的ロックをタイムアウト付きで取得するための軽量なインターフェースおよびユーティリティを提供します。

排他ロックを定義するプロトコルと、それを一定時間内に取得し、使用後に適切に解放するコンテキストマネージャを提供します。

asyncio.Lock や asyncio.Condition のような排他制御を前提としたロックに対応しており、asyncio.Semaphore のような複数同時保有が可能なカウント型ロックには対応していません。

このモジュールではロックの動作を実行時に検証しないため、与えるロックが期待される仕様に従っていることを使用者が保証する必要があります。
"""

import asyncio
from typing import Protocol
from typing import Any, Optional
from contextlib import asynccontextmanager
import logging

from typedefs import TimeoutType
from exceptions import LockTimeout

from asyncvlog import vlog_on_lock_released

logger = logging.getLogger(__name__)

class ExclusiveLock(Protocol):
    """
    An interface for locks that provide exclusive access to a resource in asynchronous contexts.

    This protocol applies to locks that meet the following conditions:
    - The lock is acquired and released by a single task.
    - Multiple tasks do not hold the lock simultaneously.

    Suitable for locks like asyncio.Lock or asyncio.Condition that enforce mutual exclusion.
    Not suitable for counting locks like asyncio.Semaphore that allow multiple concurrent holders.

    This protocol does not include dynamic validation of a lock’s internal behavior,
    so users must ensure that the provided lock conforms to the intended constraints.

    ja:
    非同期コンテキストで排他的にリソースを制御するロックのインタフェースです。

    このプロトコルは以下の要件を満たすロックに適用されます：
    - 単一のタスクによってロックが取得および解放されること
    - 同時に複数のタスクがロックを保持することがないこと

    asyncio.Lock や asyncio.Condition など、1タスクずつ排他制御を行うロックに適しています。
    一方、asyncio.Semaphore のように複数タスクによる同時取得が可能なロック（カウント型ロック）は対象外です。

    このプロトコルではロックの内部構造や挙動を動的に検証する手段を提供しないため、
    使用者は与えるロックが本プロトコルの設計意図に沿ったものであることを保証する必要があります。
    """
    async def acquire(self): ...
    def release(self): ...
    def locked(self): ...


class _DefaultCallee:
    """
    Placeholder object used as the default value for the `callee` argument.
    This object is intended only for internal use within this module and should not be instantiated elsewhere.

    ja:
    `callee` 引数のデフォルト値として使用されるプレースホルダーオブジェクトです。
    このオブジェクトは本モジュール内部での使用を意図しており、
    他の場所でインスタンス化すべきではありません。
    """
    def __repr__(self):
        return "<DefaultCallee>"

DEFAULT_CALLEE = _DefaultCallee()


@asynccontextmanager
async def acquire_lock_with_timeout(
    exlock: ExclusiveLock,
    *,
    callee: Any = DEFAULT_CALLEE,
    mn: str = "<unknown>",
    after_set: Optional[asyncio.Event] = None,
    after_clear: Optional[asyncio.Event] = None,
    timeout: TimeoutType = None):
    """
    An async context manager that acquires a lock with timeout and optionally signals completion via events.

    - Attempts to acquire the given lock (exlock) within the specified timeout period.
    - If the block completes successfully:
        - `after_set` is set() if provided (e.g., to notify completion)
        - `after_clear` is cleared() if provided (e.g., to reset waiting conditions)
    - Does not change any event state at the start of processing.
    - Raises LockTimeout if acquisition times out.
    - Automatically releases the lock if it is still held after execution.

    This function assumes the provided lock follows the ExclusiveLock protocol.
    Locks such as asyncio.Semaphore that permit concurrent acquisition are not supported.
    The function cannot verify lock type internally, so callers are responsible for providing a compliant lock.

    ja:
    非同期ロックをタイムアウト付きで取得し、取得後の処理完了時にイベント通知を行うコンテキストマネージャです。

    - 指定したロック（exlock）を timeout 秒以内に取得します。
    - 正常に処理が完了した場合：
        - `after_set` が指定されていれば set() されます（例：完了通知）
        - `after_clear` が指定されていれば clear() されます（例：待機解除）
    - 処理の開始時にはイベントの状態変化は行いません。
    - タイムアウト時は LockTimeout を送出します。
    - 処理後にロックが保持されていれば自動で release されます。

    この関数は ExclusiveLock プロトコルに準拠したロックを前提としています。
    asyncio.Semaphore などの複数タスクによる同時取得が可能なロックには対応していません。
    ただし、関数内でロックの種類を検査する手段はないため、適切なロックを渡す責任は呼び出し側にあります。
    """
    done = False
    try:
        await asyncio.wait_for(exlock.acquire(), timeout=timeout)
        yield
        done = True
    except asyncio.TimeoutError as e:
        logger.warning(f"Lock acquisition timed out after {timeout} seconds")
        raise LockTimeout("Timeout acquring lock.") from e
    finally:
        if done:
            if after_set:
                after_set.set()
            if after_clear:
                after_clear.clear()
        if exlock.locked():
            exlock.release()
            vlog_on_lock_released(callee, mn)
    