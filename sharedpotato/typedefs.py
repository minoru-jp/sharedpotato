
from typing import TypeVar, ParamSpec
from typing import Any, Optional, Union
from typing import Callable, Coroutine, Awaitable

from sentinels import _InvalidValue

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec("P")



RawValue = Optional[Union[T, _InvalidValue]]

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
