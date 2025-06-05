from typing import Generic, TypeVar, Any, Callable, Awaitable, Optional, Union, TypeAlias
from sharedobj import AsyncSharedObject, CleanupTasks, InvalidValue

T = TypeVar('T')

SetRawAccessor: TypeAlias = AsyncSharedObject[set[T]]._ObjectRawRef

class AsyncSharedSet(Generic[T]):
    class Query(Generic[T]):
        def __init__(self, parent: 'AsyncSharedSet[T]'):
            self._parent = parent
        async def contains(self, obj: T) -> bool:
            return await self._parent.contains(obj)
        async def size(self) -> int:
            return await self._parent.size()
        async def snapshot(self) -> set[T]:
            return await self._parent.copy()

    class Setter(Generic[T]):
        def __init__(self, parent: 'AsyncSharedSet[T]'):
            self._parent = parent
        async def add(self, obj: T) -> None:
            await self._parent.add(obj)

    class Deleter(Generic[T]):
        def __init__(self, parent: 'AsyncSharedSet[T]'):
            self._parent = parent
        async def discard(self, obj: T) -> None:
            await self._parent.discard(obj)
        async def clear(self) -> None:
            await self._parent.clear()

    class Updater(Generic[T]):
        def __init__(self, parent: 'AsyncSharedSet[T]'):
            self._parent = parent
        async def add(self, obj: T) -> None:
            await self._parent.add(obj)
        async def discard(self, obj: T) -> None:
            await self._parent.discard(obj)
        async def clear(self) -> None:
            await self._parent.clear()

    class Scanner(Generic[T]):
        def __init__(self, parent: 'AsyncSharedSet[T]'):
            self._parent = parent
        async def scan(self) -> list[T]:
            return list(await self._parent.copy())
        def __aiter__(self):
            return self._parent.__aiter__()

    def __init__(self, timeout: float = 1):
        self._shared_set = AsyncSharedObject[set[T]](set(), timeout=timeout)
        cls = type(self)
        self._item_query = cls.Query(self)
        self._item_scanner = cls.Scanner(self)
        self._item_setter = cls.Setter(self)
        self._item_deleter = cls.Deleter(self)
        self._item_updater = cls.Updater(self)
        self._item_cleanup_tasks = CleanupTasks()

    def _add_without_lock(self, acc: SetRawAccessor, obj: T) -> None:
        acc.get().add(obj)

    def _discard_without_lock(self, acc: SetRawAccessor, obj: T) -> None:
        set_ = acc.get()
        if obj in set_:
            self._item_cleanup_tasks.cleanup(obj)
            acc.get().discard(obj)

    def _contains_without_lock(self, acc: SetRawAccessor, obj: T) -> bool:
        return obj in acc.get()

    def _size_without_lock(self, acc: SetRawAccessor) -> int:
        return len(acc.get())

    def _clear_without_lock(self, acc: SetRawAccessor) -> None:
        set_ = acc.get()
        for item in set_:
            self._item_cleanup_tasks.cleanup(item)
        acc.get().clear()

    def _copy_without_lock(self, acc: SetRawAccessor) -> set[T]:
        return set(acc.get())

    async def add(self, obj: T) -> None:
        await self._shared_set._lock_and_do(self._add_without_lock, obj)

    async def discard(self, obj: T) -> None:
        await self._shared_set._lock_and_do(self._discard_without_lock, obj)

    async def contains(self, obj: T) -> bool:
        return await self._shared_set._lock_and_do(self._contains_without_lock, obj)

    async def size(self) -> int:
        return await self._shared_set._lock_and_do(self._size_without_lock)

    async def clear(self) -> None:
        await self._shared_set._lock_and_do(self._clear_without_lock)

    async def copy(self) -> set[T]:
        return await self._shared_set._lock_and_do(self._copy_without_lock)

    def set_close_handler(self, handler: Callable[[SetRawAccessor], Any]) -> None:
        self._shared_set.set_close_handler(handler)
    
    @property
    def cleanup_prop(self):
        return self._item_cleanup_tasks.prop

    @property
    def query(self) -> 'AsyncSharedSet.Query[T]':
        return self._item_query
    @property
    def scanner(self) -> 'AsyncSharedSet.Scanner[T]':
        return self._item_scanner
    @property
    def setter(self) -> 'AsyncSharedSet.Setter[T]':
        return self._item_setter
    @property
    def deleter(self) -> 'AsyncSharedSet.Deleter[T]':
        return self._item_deleter
    @property
    def updater(self) -> 'AsyncSharedSet.Updater[T]':
        return self._item_updater

    def __aiter__(self):
        return self._aiter()

    async def _aiter(self):
        # イテレーションはsnapshotで安定した内容を渡す
        items = await self.copy()
        for item in items:
            yield item

    async def close(self) -> None:
        return await self._shared_set.close()

    async def closed(self) -> bool:
        return await self._shared_set.closed()

    async def lock_and_do(self, func: Callable, *args, lock_timeout: Optional[float] = None, handler_timeout: Optional[float] = None, **kwargs) -> Any:
        return await self._shared_set._lock_and_do(func, *args, lock_timeout=lock_timeout, handler_timeout=handler_timeout, **kwargs)

