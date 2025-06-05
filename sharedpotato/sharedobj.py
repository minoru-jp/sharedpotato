"""
coroforge: Utilities for shared object management in asynchronous programming (asyncio)

This module provides classes and helpers for safely managing shared objects in Python asyncio environments.
- AsyncSharedObject: Supports exclusive locking, lazy initialization, event-based notification, timeout control, and close handlers.
- acquire_lock_with_timeout: An async context manager for lock acquisition with timeout.

Suitable for safely sharing and synchronizing resources between coroutines.

jp:
coroforge: 非同期プログラミング向けの共有オブジェクト管理ユーティリティ

本モジュールは、Pythonのasyncio環境下で安全に共有オブジェクトを管理するためのクラス群を提供します。
- AsyncSharedObject: 排他制御、値の初期化遅延、イベントによる通知、タイムアウト、クローズ時のハンドラ呼び出しなどをサポート。
- acquire_lock_with_timeout: タイムアウト付きのロック取得を行う非同期コンテキストマネージャ。

主にコルーチン間で安全にリソース共有・排他制御が必要な用途に利用できます。

Copyright (c) 2024 minoru_jp
"""

import asyncio
import inspect
from contextlib import asynccontextmanager

from typing import Protocol, Callable, Any, Awaitable, TypeVar, Generic, Optional, Union, Coroutine, TypeGuard, ParamSpec, Concatenate

import logging

from asyncvlog import (
    vlog_on_instance_created,
    vlog_on_instance_created_with_args,
    vlog_on_called,
    vlog_on_lock_acquired,
    vlog_on_lock_released,
    vlog_on_custom,
    vlog_on_custom_info,
    vlog_on_object_closed,
    vlog_on_cleanup_started,
    vlog_on_cleanup_skipped,
    vlog_on_timeout,
    vlog_on_exception,
    vlog_on_default_used,
    vlog_on_wait_started,
    vlog_on_wait_finished,
    vlog_on_shield_started,
    vlog_on_shield_finished,
    vlog_on_task_created,
    vlog_on_task_completed,
    vlog_on_accessor_used,
    vlog_on_invalid_value_detected,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec("P")

class _CTProperty(Generic[T]):
    def __init__(self, parent: 'CleanupTasks[T]'):
        self._parent = parent
    
    @property
    def cleanup_handler(self) -> MaybeCoroutineOrCallableOrNone[T, R]:
        return self._parent.handler
    
    @cleanup_handler.setter
    def cleanup_handler(self, handler: Callable[[T], Any]) -> None:
        self._parent.handler = handler
    
    @property
    def runs_in_task(self) -> bool:
        return self._parent.runs_in_task

    @runs_in_task.setter
    def runs_in_task(self, flag: bool) -> None:
        self._parent.runs_in_task = flag
    
    def update_cleanup_interval(self, interval: int) -> None:
        return self._parent.update_cleanup_interval(interval)



class CleanupTasks(Generic[T]):

    def __init__(self, cleanup_interval: int = 100):
        self.__pending_cleanup_tasks: set[asyncio.Task[T]] = set()
        self.__cleanup_handler: MaybeCoroutineOrCallableOrNone[T, Any] = None
        self.__cleanup_task_runs_in_task: bool = False
        self.__cleanup_interval: int = cleanup_interval
        self.__clear_count: int = 0
        self.__prop: _CTProperty[T] = _CTProperty(self)
        vlog_on_instance_created_with_args(self, cleanup_interval)

    @property
    def handler(self) -> MaybeCoroutineOrCallableOrNone[T, R]:
        return self.__cleanup_handler

    @handler.setter
    def handler(self, handler: Callable[[T], Any]) -> None:
        self.__cleanup_handler = handler

    @property
    def runs_in_task(self) -> bool:
        return self.__cleanup_task_runs_in_task

    @runs_in_task.setter
    def runs_in_task(self, flag: bool) -> None:
        self.__cleanup_task_runs_in_task = flag

    @property
    def cleanup_interval(self) -> int:
        return self.__cleanup_interval
    
    @cleanup_interval.setter
    def cleanup_interval(self, interval: int) -> None:
        if interval < 1:
            raise ValueError("cleanup_interval must be >= 1")
        self.__cleanup_interval = interval

    def update_cleanup_interval(self, interval: int) -> None:
        if interval < 1:
            raise ValueError("cleanup_interval must be >= 1")
        # 設定値変更時に整理・カウントリセット
        self._collect_done_tasks()
        self.__clear_count = 0
        self.__cleanup_interval = interval
    
    @property
    def prop(self) -> _CTProperty[T]:
        return self.__prop

    async def cleanup(self, obj: ValidValue[T], timeout: TimeoutType = None, resumes: bool = True) -> None:
        MN = "cleanup"
        vlog_on_called(self, MN)
        self.__clear_count += 1
        if self.__clear_count >= self.__cleanup_interval:
            vlog_on_custom_info(self, MN, "cleanup interval reached, collecting done tasks")
            self._collect_done_tasks()
            self.__clear_count = 0
        try:
            if self.handler is not None:
                if isinstance(self.handler, Callable):
                    result = self.handler(obj)
                if inspect.iscoroutine(result):
                    if self.runs_in_task:
                        vlog_on_task_created(self, MN, "cleanup handler is awaitable, running in task")
                        task = asyncio.create_task(result)
                        self.__pending_cleanup_tasks.add(task)
                    else:
                        try:
                            vlog_on_wait_started(self, MN, "awaiting cleanup handler with timeout")
                            await asyncio.wait_for(result, timeout)
                            vlog_on_wait_finished(self, MN, "awaiting cleanup handler with timeout")
                        except TimeoutError:
                            logger.warning("cleanup handler timed out, resumes=%s", resumes)
                            if resumes:
                                task = asyncio.create_task(result)
                                self.__pending_cleanup_tasks.add(task)
                            else:
                                logger.debug("cleanup handler timed out and resumes is False; skipping re-execution")
                else:
                    pass
            else:
                logger.debug("no cleanup handler set; skipping cleanup")
        except Exception as e:
            logger.exception(f"exception occurred during cleanup: {e}")

    async def wait_all(
        self,
        all_timeout: Optional[float] = None,
        per_task_timeout: Optional[float] = None
    ) -> None:
        MN = 'wait_all'
        vlog_on_called(self, MN)
        self._collect_done_tasks()
        try:
            tasks = self.__pending_cleanup_tasks
            if per_task_timeout is not None:
                tasks = {asyncio.wait_for(t, timeout=per_task_timeout) for t in tasks}
            vlog_on_wait_started(self, MN, "wait for all cleanup tasks")
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=all_timeout
            )
            vlog_on_wait_finished(self, MN, "wait for all cleanup tasks")
            for r in results:
                if isinstance(r, Exception):
                    logger.warning(f"Cleanup handler raised exception: {r}")
            self.__pending_cleanup_tasks.clear()
        except asyncio.TimeoutError:
            logger.warning("wait_all timed out")
            self._collect_done_tasks()
            for t in self.__pending_cleanup_tasks:
                t.cancel()
            self.__pending_cleanup_tasks.clear()
        except Exception as e:
            logger.exception(f"Unexpected exception occurred in wait_all: {e}")
        
    def _collect_done_tasks(self) -> None:
        self.__pending_cleanup_tasks = {t for t in self.__pending_cleanup_tasks if not t.done()}

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
    

# 共有オブジェクトが既にクローズされている場合に投げる例外
class SharedObjectClosed(Exception):
    pass

# ロック取得タイムアウト例外
class LockTimeout(asyncio.TimeoutError):
    """ロック取得のタイムアウト時に投げられる例外"""
    pass

# ハンドラ処理のタイムアウト例外
class HandlerTimeout(asyncio.TimeoutError):
    """ハンドラ処理のタイムアウト時に投げられる例外"""
    pass





class _ObjectGetter(Generic[T]):
    def __init__(self, parent: 'AsyncSharedObject[T]'):
        self._parent = parent

    async def get(self) -> T:
        return await self._parent.get()

class _ObjectSetter(Generic[T]):
    def __init__(self, parent: 'AsyncSharedObject[T]'):
        self._parent = parent

    async def set(self, obj: T) -> None:
        await self._parent.set(obj)

    async def get(self) -> T:
        return await self._parent.get()

class _ObjectDeleter(Generic[T]):
    def __init__(self, parent: 'AsyncSharedObject[T]'):
        self._parent = parent

    async def clear(self) -> T:
        return await self._parent.clear()

class _ObjectUpdater(Generic[T]):
    def __init__(self, parent: 'AsyncSharedObject[T]'):
        self._parent = parent

    async def set(self, obj: T) -> None:
        await self._parent.set(obj)

    async def clear(self) -> None:
        await self._parent.clear()

    async def get(self) -> T:
        return await self._parent.get()

class _ObjectRawRef(Generic[T]):
    def __init__(self, parent: 'AsyncSharedObject[T]'):
        self._parent = parent

    def set(self, obj: T) -> None:
        self._parent._set_without_lock(obj)

    def clear(self) -> None:
        self._parent._clear_without_lock()

    def get(self) -> T:
        return self._parent._get_without_wait()

    def close(self) -> None:
        self._parent._close_without_lock()

    def closed(self) -> bool:
        return self._parent._closed


class AsyncSharedObject(Generic[T]):
    """
    A generic class for safe, asynchronous value sharing and synchronization.

    AsyncSharedObject enables multiple coroutines to safely share, update, or clear a value under Python's asyncio.
    It internally supports exclusive locking, event synchronization, timeout handling, close handler invocation, and more.

    Main features:
      - set/get/clear for updating, retrieving, or clearing the shared value
      - Lock-based mutual exclusion and event-based initialization waiting
      - Timeout-enabled lock acquisition and event waiting
      - Explicit handling of closed state and INVALID_VALUE sentinels
      - Registration and invocation of a close handler on close()
      - Support for async with context manager (auto-close)

    Notes:
      - peek() only acquires a lock; value validity is checked by is-comparison with INVALID_VALUE
      - get() will wait until the value is set (event-based wait)
      - All operations after close() raise SharedObjectClosed
      - Timeout errors may occur during lock acquisition or event waiting
    
    jp:
    非同期で安全に値を共有・排他制御するためのジェネリッククラス。

    AsyncSharedObject は、Python の asyncio 環境下で、
    1つの値を複数のコルーチン間で安全に共有・更新・削除するためのクラスです。
    内部で排他ロック・イベント同期・タイムアウト・クローズ時のハンドラ呼び出しなどをサポートします。

    主な機能:
      - set/get/clear による値の設定・取得・クリア
      - 排他制御付きのロック、イベントによる初期化待ち
      - タイムアウト付きロック取得・イベント待機
      - クローズ状態・無効値(INVALID_VALUE)の明確化
      - クローズ時ハンドラの登録と自動呼び出し
      - async with による自動クローズ対応

    注意:
      - peek() はロック取得のみで、値の有効性はINVALID_VALUEとのis比較で判定
      - get()は値が未設定なら初期化まで待機する（イベント待ち）
      - クローズ後は全ての操作でSharedObjectClosed例外が発生
      - ロック取得・イベント待機でタイムアウト例外が発生
    
    Example(With context manager):
        async def cleanup_handler(obj):
        print(f"Value at close: {obj}")

        async def main():
            async with AsyncSharedObject[int]() as shared:
                shared.set_close_handler(cleanup_handler)
                await shared.set(1)
                value = await shared.get()
                print(f"Value obtained: {value}")
            # cleanup_handler is called here
        
    Example(without context manger):
        async def main():
            shared = AsyncSharedObject[int]()
            await shared.set(1)
            value = await shared.get()
            print(f"Value obtained: {value}")

            # Custom cleanup handling at close (without set_close_handler)
            closed_value = await shared.close()
            print(f"Value at close: {closed_value}")
    """


    INVALID_VALUE = InvalidValue()
    _UNDEFINED_VALUE = object()

    def __init__(
        self,
        obj: Union[T, InvalidValue] = INVALID_VALUE,
        default: Union[T, InvalidValue] = INVALID_VALUE,
        timeout: TimeoutType = 1
    ):
        self._lock: asyncio.Lock = asyncio.Lock()
        self._cond: asyncio.Condition = asyncio.Condition(self._lock)
        self._updated: asyncio.Event = asyncio.Event()
        #self._obj_is_enabled = asyncio.Event()
        self._default: Union[T, InvalidValue] = default
        self._obj: RawValue[T] = self._select_initial_value(obj, default)
        self._closed: bool = False
        self._default_timeout: TimeoutType = timeout

        self._obj_getter: _ObjectGetter[T] = _ObjectGetter(self)
        self._obj_setter: _ObjectSetter[T] = _ObjectSetter(self)
        self._obj_deleter: _ObjectDeleter[T] = _ObjectDeleter(self)
        self._obj_updater: _ObjectUpdater[T] = _ObjectUpdater(self)
        self._without_lock_accessor: _ObjectRawRef[T] = _ObjectRawRef(self)
        self._obj_cleanup_tasks = CleanupTasks[T]()
        vlog_on_instance_created_with_args(self, obj, default, timeout)

    @classmethod
    def _select_initial_value(
        cls,
        obj: RawValue,
        default: RawValue
    ) -> RawValue:
        if obj is not cls.INVALID_VALUE:
            return obj
        elif default is not cls.INVALID_VALUE:
            return default
        else:
            return cls.INVALID_VALUE

    async def set(self, obj: T, timeout: TimeoutType = None) -> None:
        MN = 'set'
        vlog_on_called(self, MN)
        old_obj = self.INVALID_VALUE
        async with acquire_lock_with_timeout(
            self, MN, self._cond, self._updated, timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            old_obj = self._set_without_lock(obj)
            self._cond.notify_all()
        if self.is_valid_value(old_obj):
            await self._obj_cleanup_tasks.cleanup(old_obj)


    async def clear(self, timeout: TimeoutType = None) -> None:
        MN = 'clear'
        vlog_on_called(self, MN)
        self._updated.clear()
        UNDEFINED = self._UNDEFINED_VALUE
        old_obj = UNDEFINED
        async with acquire_lock_with_timeout(
            self, MN, self._cond, complete = self._updated, timeout = timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            old_obj = self._clear_without_lock()
            self._cond.notify_all()
        if old_obj is not UNDEFINED:
            if self.is_valid_value(old_obj):
                await self._obj_cleanup_tasks.cleanup(old_obj)
        else:
            raise RuntimeError("Old object is missing")

    @classmethod
    def is_valid_value(cls, value: RawValue[T]) -> TypeGuard[ValidValue[T]]:
        return value is not None and value is not cls.INVALID_VALUE
    
    @classmethod
    def is_optional_value(cls, value: RawValue[T]) -> TypeGuard[OptionalValue[T]]:
        return value is not cls.INVALID_VALUE
    
    async def get(self, timeout: TimeoutType = None) -> OptionalValue[T]:
        MN = 'get'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._cond, timeout):
            vlog_on_lock_acquired(self, MN) #TODO: vlogのRENAME
            value = self._obj
            while not self.is_optional_value(value):
                if self._closed:
                    vlog_on_object_closed(self, MN)
                    raise SharedObjectClosed()
                vlog_on_wait_started(self, MN)
                await self._cond.wait()
                vlog_on_wait_finished(self, MN)
                value = self._obj
            return value

    
    async def peek(self, timeout: TimeoutType = None) -> RawValue[T]:
        MN = 'peek'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._cond, timeout):
            vlog_on_lock_acquired(self, MN) #TODO: vlogのRENAME
            return self._obj

  
    def _set_without_lock(self, obj: T) -> RawValue[T]:
        old_obj = self._obj
        self._obj = obj
        return old_obj

    def _clear_without_lock(self) -> RawValue[T]:
        old_obj = self._obj
        self._obj = self._default
        return old_obj

    def _get_without_wait(self) -> RawValue[T]:
        return self._obj

  
    async def close(self, timeout: TimeoutType = None) -> None:
        MN = 'close'
        vlog_on_called(self, MN)
        self._close = True
        try:
            await self._updated.wait()
        except Exception:
            pass

        async with acquire_lock_with_timeout(self, MN, self._cond, timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            self._closed = True
            final_value = self._obj
            self._obj = self.INVALID_VALUE
            self._cond.notify_all() # notifies shared object is closed
        #TODO: vlog_cleanup_started(...)
        if hasattr(self, "_close_handler") and self._close_handler:
            result = self._close_handler(final_value)
            if inspect.iscoroutine(result):
                vlog_on_wait_started(self, MN, "awaiting close handler result.")
                await result
                vlog_on_wait_finished(self, MN, "awaiting close handler result.")
        else:
            #no close handler set
            pass

    def set_close_handler(self, handler: Callable[[_ObjectRawRef[T]], Any]) -> None:
        self._close_handler = handler
    
    async def wait_cleanup_all(
            self,
            all_timeout: Optional[float] = None,
            per_task_timeout: Optional[float] = None):
        await self._obj_cleanup_tasks.wait_all(all_timeout, per_task_timeout)
  
    @property
    def cleanup(self) -> _CTProperty[T]:
        return self._obj_cleanup_tasks.prop
    
    @property
    def getter(self) -> _ObjectGetter[T]:
        return self._obj_getter

    @property
    def setter(self) -> _ObjectSetter[T]:
        return self._obj_setter

    @property
    def deleter(self) -> _ObjectDeleter[T]:
        return self._obj_deleter

    @property
    def updater(self) -> _ObjectUpdater[T]:
        return self._obj_updater

    async def closed(self, timeout: Optional[float] = None) -> bool:
        MN = 'closed'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._cond, timeout):
            vlog_on_lock_acquired(self, MN)
            return self._closed

    def _close_without_lock(self) -> None:
        self._closed = True

    async def valid(self, timeout: Optional[float] = None) -> bool:
        return self.is_valid_value(await self.peek(timeout=timeout))

    async def _lock_and_do(
        self,
        handler: Callable[Concatenate[_ObjectRawRef[T], P], Any],
        *args,
        lock_timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        MN = '_lock_and_do'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._cond, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            return handler(self._without_lock_accessor, *args, **kwargs)

    async def _lock_and_async(
        self,
        handler: Callable[Concatenate[_ObjectRawRef[T], P], Any],
        *args,
        lock_timeout: Optional[float] = None,
        handler_timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        MN = '_lock_and_do'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._cond, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            result = handler(self._without_lock_accessor, *args, **kwargs)
            if inspect.iscoroutine(result):
                try:
                    vlog_on_wait_started(self, MN, "awaiting handler result.")
                    awaited_result = await asyncio.wait_for(result, timeout=handler_timeout)
                    vlog_on_wait_finished(self, MN, "awaiting handler result.")
                    return awaited_result
                except asyncio.TimeoutError as e:
                    logger.warning("Handler execution timed out after %s seconds", handler_timeout)
                    raise HandlerTimeout("ハンドラ処理タイムアウト") from e
            else:
                return result


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # キャンセルされてもクローズ処理だけは完遂させる
        MN = '__aexit__'
        vlog_on_shield_started(self, MN, "await asyncio.shield(self.close())")
        await asyncio.shield(self.close())
        vlog_on_shield_finished(self, MN, "await asyncio.shield(self.close())")


