"""
Type definitions for shared object management and cleanup handlers.

This module defines reusable type aliases and generic parameters used throughout
the sharedpotato library. It provides standard representations for value states,
cleanup strategies, and callable interfaces, helping to clarify the design and
intention of asynchronous shared resource management.

Generic parameters:
- T: the type of the shared object
- RCR: the return type of a resource cleanup handler
- MCR: the return type of a manager cleanup handler
- P: generic parameter specification for callables

Type aliases and protocols:
- RawValue: a possibly None or explicitly invalid shared object
- NullableValue: a shared object that may be None
- Seconds: time duration in seconds, optionally None
- ResourceCleanup: a Protocol that defines the callable interface for
  cleaning up a valid shared object.
- ManagerCleanup: a Protocol that defines the callable interface for
  cleaning up the manager instance that holds the shared object.

ja:
非同期共有オブジェクトの管理やクリーンアップ処理に関連する型定義モジュール。

このモジュールは、sharedpotato ライブラリ全体で使用される型エイリアスや
ジェネリック型パラメータ、プロトコルを定義します。値の状態表現、クリーンアップ戦略、
およびコール可能オブジェクトのインタフェースを標準化することで、
非同期リソース管理の設計と意図を明確に保つことを目的としています。

ジェネリック型パラメータ:
- T: 共有オブジェクトの型
- RCR: リソースクリーンアップ処理の戻り値型
- MCR: 管理インスタンスのクリーンアップ処理の戻り値型
- P: コール可能オブジェクトの可変長引数型

型エイリアスおよびプロトコル:
- RawValue: None または明示的な無効値を含む可能性のある共有オブジェクト
- NullableValue: None を許容する共有オブジェクト
- Seconds: 秒単位の時間指定（None 可）
- ResourceCleanup: 有効な共有オブジェクトに対するクリーンアップ関数を定義する Protocol
- ManagerCleanup: 共有オブジェクトを保持する管理インスタンスのクリーンアップ処理を定義する Protocol
"""

from typing import Generic, Protocol, TypeVar, ParamSpec
from typing import Optional, Union, Literal
from typing import Awaitable
from typing import runtime_checkable

from sentinels import _InvalidValue, INVALID
__all__ = [
    "T", "RCR", "MCR", "P",
    "RawValue",
    "NullableValue",
    "Seconds",
    "ResourceCleanup",
    "ManagerCleanup",
]

T = TypeVar('T', contravariant = True)
RCR = TypeVar('RCR', covariant = True)
MCR = TypeVar('MCR', covariant = True)
P = ParamSpec("P")


RawValue = Optional[Union[T, Literal[INVALID]]]

NullableValue = Optional[T]

Seconds = Optional[float]


class ResourceCleanup(Protocol, Generic[T, RCR]):
    """
    Callable interface for performing cleanup on a valid shared resource.
    
    ja:
    有効な共有リソースに対するクリーンアップ処理を行うための呼び出し可能インタフェース。
    """
    def __call__(self, valid_value: T) -> Union[MCR, Awaitable[MCR]]: ...


@runtime_checkable
class ManagerCleanup(Protocol, Generic[T, MCR]):
    """
    Callable interface for cleaning up the shared object manager.

    ja:
    共有オブジェクト管理インスタンスのクリーンアップ処理を行うための呼び出し可能インタフェース。
    """
    # raw_value corresponds to the expanded form of RawValue[T],
    # defined as: RawValue[T] = Optional[Union[T, Literal[INVALID]]]
    # It represents a possibly None or explicitly invalid shared object.
    # ja:
    # raw_value は RawValue[T] の明示展開であり、
    # RawValue[T] = Optional[Union[T, Literal[INVALID]]] に対応します。
    # None または特定の無効値 (INVALID) を含みうる共有オブジェクトを受け取ります。
    def __call__(self, raw_value: Optional[Union[T, _InvalidValue]]) -> Union[MCR, Awaitable[MCR]]: ...

