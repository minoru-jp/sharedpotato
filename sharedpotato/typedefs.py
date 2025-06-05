
from typing import TypeVar, ParamSpec
from typing import Any, Optional, Union
from typing import Callable, Coroutine, Awaitable


T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec("P")

class InvalidValue:
    def __repr__(self):
        return "<INVALID_VALUE>"

INVALID: InvalidValue = InvalidValue()

class _UndefinedValue:
    def __repr__(self):
        return "<UNDEFINED_VLAUE>"

_UNDEFINED: _UndefinedValue = _UndefinedValue()

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

DEFAULT_CALLEE: _DefaultCallee = _DefaultCallee()

RawValue = Optional[Union[T, InvalidValue]]

OptionalValue = Optional[T]

ValidValue = T

TimeoutType = Optional[float]

ResourceCleanup = Union[
    Callable[[ValidValue[T]]]
]

ManagerCleanup = Union[
    Callable[[RawValue[T]], Any],
    Callable[[RawValue[T]], Awaitable[Any]],
]
