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

from typing import Protocol, Callable, Any, Awaitable, TypeVar, Generic, Optional, Union

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


class CleanupTasks(Generic[T]):

    class Property(Generic[T]):
        def __init__(self, parent: 'CleanupTasks[T]'):
            self._parent = parent
        
        @property
        def cleanup_handler(self) -> Optional[Callable[[T], Any]]:
            return self._parent.cleanup_handler
        
        @cleanup_handler.setter
        def cleanup_handler(self, handler: Callable[[T], Any]) -> None:
            self._parent.cleanup_handler = handler
        
        @property
        def runs_in_task(self) -> bool:
            return self._parent.runs_in_task

        @runs_in_task.setter
        def runs_in_task(self, flag: bool) -> None:
            self._parent.runs_in_task = flag
        
        def update_cleanup_interval(self, interval: int) -> None:
            return self._parent.update_cleanup_interval(interval)


    def __init__(self, cleanup_interval: int = 100):
        self.__pending_cleanup_tasks: set[asyncio.Task[T]] = set()
        self.__cleanup_handler: Optional[Callable[[T], Any]] = None
        self.__cleanup_task_runs_in_task: bool = False
        self.__cleanup_interval: int = cleanup_interval
        self.__clear_count: int = 0
        self.__prop: CleanupTasks[T].Property[T] = type(self).Property(self)
        vlog_on_instance_created_with_args(self, cleanup_interval)

    @property
    def cleanup_handler(self) -> Optional[Callable[[T], Any]]:
        return self.__cleanup_handler

    @cleanup_handler.setter
    def cleanup_handler(self, handler: Callable[[T], Any]) -> None:
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
    def prop(self) -> Property[T]:
        return self.__prop

    async def cleanup(self, obj: T, timeout: Optional[float] = None, resumes: bool = True) -> None:
        MN = "cleanup"
        vlog_on_called(self, MN)
        self.__clear_count += 1
        if self.__clear_count >= self.__cleanup_interval:
            vlog_on_custom_info(self, MN, "cleanup interval reached, collecting done tasks")
            self._collect_done_tasks()
            self.__clear_count = 0
        try:
            if self.cleanup_handler is not None:
                result = self.cleanup_handler(obj)
                if inspect.isawaitable(result):
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


@asynccontextmanager
async def acquire_lock_with_timeout(obj, mn: str, lock: asyncio.Lock, timeout: Optional[float]):
    try:
        await asyncio.wait_for(lock.acquire(), timeout=timeout)
        yield
    except asyncio.TimeoutError as e:
        logger.warning(f"Lock acquisition timed out after {timeout} seconds")
        raise LockTimeout("ロック取得タイムアウト") from e
    finally:
        if lock.locked():
            lock.release()
            vlog_on_lock_released(obj, mn)


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

# 無効値を表す番兵オブジェクト
class InvalidValue:
    '''
    無効値を表す。値オブジェクトはAsyncSharedObject.INVALID_VALUEから参照する
    AsyncSharedObject以外はこのクラスをインスタンス化しないこと
    Genericの型指定のみに使用する
    '''
    def __repr__(self):
        return "<INVALID_VALUE>"



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
    class Getter(Generic[T]):
        def __init__(self, parent: 'AsyncSharedObject[T]'):
            self._parent = parent

        async def get(self) -> T:
            return await self._parent.get()

    class Setter(Generic[T]):
        def __init__(self, parent: 'AsyncSharedObject[T]'):
            self._parent = parent

        async def set(self, obj: T) -> None:
            await self._parent.set(obj)

        async def get(self) -> T:
            return await self._parent.get()

    class Deleter(Generic[T]):
        def __init__(self, parent: 'AsyncSharedObject[T]'):
            self._parent = parent

        async def clear(self) -> T:
            return await self._parent.clear()

    class Updater(Generic[T]):
        def __init__(self, parent: 'AsyncSharedObject[T]'):
            self._parent = parent

        async def set(self, obj: T) -> None:
            await self._parent.set(obj)

        async def clear(self) -> None:
            await self._parent.clear()

        async def get(self) -> T:
            return await self._parent.get()

    class WithoutLockAccessor(Generic[T]):
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

    INVALID_VALUE = InvalidValue()

    def __init__(
        self,
        obj: Union[T, InvalidValue] = INVALID_VALUE,
        default: Union[T, InvalidValue] = INVALID_VALUE,
        timeout: float = 1
    ):
        self._lock = asyncio.Lock()
        self._obj_is_enabled = asyncio.Event()
        self._default: Union[T, InvalidValue] = default
        self._obj: Union[T, InvalidValue] = self._select_initial_value(obj, default)
        self._closed: bool = False
        self._default_timeout = timeout

        cls = type(self)
        self._obj_getter: AsyncSharedObject.Getter[T] = cls.Getter(self)
        self._obj_setter: AsyncSharedObject.Setter[T] = cls.Setter(self)
        self._obj_deleter: AsyncSharedObject.Deleter[T] = cls.Deleter(self)
        self._obj_updater: AsyncSharedObject.Updater[T] = cls.Updater(self)
        self._without_lock_accessor: AsyncSharedObject.WithoutLockAccessor[T] = cls.WithoutLockAccessor(self)
        self._obj_cleanup_tasks = CleanupTasks[T]()
        vlog_on_instance_created_with_args(self, obj, default, timeout)

    @classmethod
    def _select_initial_value(
        cls,
        obj: Union[T, InvalidValue],
        default: Union[T, InvalidValue]
    ) -> Union[T, InvalidValue]:
        if obj is not cls.INVALID_VALUE:
            return obj
        elif default is not cls.INVALID_VALUE:
            return default
        else:
            return cls.INVALID_VALUE

    async def set(self, obj: T, lock_timeout: Optional[float] = None) -> Union[T, InvalidValue]:
        MN = 'set'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            old_obj = self._set_without_lock(obj)
            return await self._obj_cleanup_tasks.cleanup(old_obj)


    async def clear(self, lock_timeout: Optional[float] = None) -> T:
        MN = 'clear'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            old_obj = self._clear_without_lock()
            return await self._obj_cleanup_tasks.cleanup(old_obj)


    async def get(self, lock_timeout: Optional[float] = None) -> T:
        MN = 'get'
        vlog_on_called(self, MN)
        # 1回目のロック（クローズチェック）
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN, 'pre-wait')
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
        # イベントwait（ロック解放中に他コルーチンが値をセットできるようにする
        vlog_on_wait_started(self, MN, 'wait event self._obj_is_enabled')
        await self._obj_is_enabled.wait()
        # 2回目のロック（値の取得）
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN, 'post-wait')
            return self._get_without_wait()


    async def peek(self, lock_timeout: Optional[float] = None) -> Union[T, InvalidValue]:
        MN = 'peek'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            return self._obj

  
    def _set_without_lock(self, obj: T) -> Union[T, InvalidValue]:
        old_obj = self._obj
        self._obj = obj
        self._obj_is_enabled.set()
        return old_obj

    def _clear_without_lock(self) -> Union[T, InvalidValue]:
        old_obj = self._obj
        self._obj = self._default
        self._obj_is_enabled.clear()
        return old_obj

    def _get_without_wait(self) -> T:
        return self._obj

  
    async def close(self, lock_timeout: Optional[float] = None) -> WithoutLockAccessor[T]:
        MN = 'close'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            self._closed = True
            self._obj = self.INVALID_VALUE
            if hasattr(self, "_close_handler") and self._close_handler:
                result = self._close_handler(self._without_lock_accessor)
                if inspect.isawaitable(result):
                    vlog_on_wait_started(self, MN, "awaiting close handler result.")
                    await result
                    vlog_on_wait_finished(self, MN, "awaiting close handler result.")
            else:
                #no close handler set
                pass
            return self._without_lock_accessor

    def set_close_handler(self, handler: Callable[[WithoutLockAccessor[T]], Any]) -> None:
        self._close_handler = handler
    
    async def wait_cleanup_all(
            self,
            all_timeout: Optional[float] = None,
            per_task_timeout: Optional[float] = None):
        await self._obj_cleanup_tasks.wait_all(all_timeout, per_task_timeout)
  
    @property
    def cleanup_prop(self) -> CleanupTasks[T].Property:
        return self._obj_cleanup_tasks.prop
    
    @property
    def getter(self) -> Getter[T]:
        return self._obj_getter

    @property
    def setter(self) -> Setter[T]:
        return self._obj_setter

    @property
    def deleter(self) -> Deleter[T]:
        return self._obj_deleter

    @property
    def updater(self) -> Updater[T]:
        return self._obj_updater

    async def closed(self, lock_timeout: Optional[float] = None) -> bool:
        MN = 'closed'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            return self._closed

    def _close_without_lock(self) -> None:
        self._closed = True

    async def valid(self, lock_timeout: Optional[float] = None) -> bool:
        return (await self.peek(lock_timeout=lock_timeout)) is not self.INVALID_VALUE

    async def _lock_and_do(
        self,
        handler: Callable[["AsyncSharedObject.WithoutLockAccessor[T]"], Union[R, Awaitable[R]]],
        *args,
        lock_timeout: Optional[float] = None,
        handler_timeout: Optional[float] = None,
        **kwargs
    ) -> R:
        MN = '_lock_and_do'
        vlog_on_called(self, MN)
        async with acquire_lock_with_timeout(self, MN, self._lock, lock_timeout):
            vlog_on_lock_acquired(self, MN)
            if self._closed:
                vlog_on_object_closed(self, MN)
                raise SharedObjectClosed()
            result = handler(self._without_lock_accessor, *args, **kwargs)
            if inspect.isawaitable(result):
                try:
                    vlog_on_wait_started(self, MN, "awaiting handler result.")
                    r = await asyncio.wait_for(result, timeout=handler_timeout)
                    vlog_on_wait_finished(self, MN, "awaiting handler result.")
                    return r
                except asyncio.TimeoutError as e:
                    logger.warning("Handler execution timed out after %s seconds", handler_timeout)
                    raise HandlerTimeout("ハンドラ処理タイムアウト") from e
            return result


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # キャンセルされてもクローズ処理だけは完遂させる
        MN = '__aexit__'
        vlog_on_shield_started(self, MN, "await asyncio.shield(self.close())")
        await asyncio.shield(self.close())
        vlog_on_shield_finished(self, MN, "await asyncio.shield(self.close())")


