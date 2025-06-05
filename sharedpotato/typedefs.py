"""
Type definitions for shared object management and cleanup handlers.

This module defines reusable type aliases and generic parameters used throughout
the sharedpotato library. It provides standard representations for value states,
cleanup strategies, and callable interfaces, helping to clarify the design and
intention of asynchronous shared resource management.

Generic parameters:
- T: the type of the shared object
- R: generic return value type
- P: generic parameter specification for callables

Type aliases:
- RawValue: a possibly invalid or None-containing shared object
- NullableValue: a shared object that may be None
- Seconds: time duration in seconds, optionally None
- ResourceCleanup: a cleanup function for valid shared objects
- ManagerCleanup: a handler for cleaning up the instance that manages shared objects


ja:
非同期共有オブジェクトの管理やクリーンアップ処理に関連する型定義モジュール。

このモジュールは、sharedpotato ライブラリ全体で使用される型エイリアスや
ジェネリック型パラメータを定義します。値の状態表現、クリーンアップ戦略、
コール可能オブジェクトのインタフェースを標準化することで、
非同期リソース管理の設計と意図を明確に保つことを目的としています。

ジェネリック型パラメータ:
- T: 共有オブジェクトの型
- R: 一般的な戻り値型
- P: コール可能オブジェクトの可変長引数を表す型

型エイリアス:
- RawValue: 無効値や None を含む可能性のある共有オブジェクト
- NullableValue: None を許容する共有オブジェクト
- Seconds: 秒単位の時間指定（None 可）
- ResourceCleanup: 有効な共有オブジェクトに対するクリーンアップ関数
- ManagerCleanup: 共有オブジェクトを管理するインスタンス自体のクリーンアップを行うハンドラー
"""


from typing import TypeVar, ParamSpec
from typing import Any, Optional, Union, Literal
from typing import Callable, Awaitable

from sentinels import INVALID

__all__ = [
    "T", "R", "P",
    "RawValue",
    "NullableValue",
    "Seconds",
    "ResourceCleanup",
    "ManagerCleanup",
]

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec("P")


RawValue = Optional[Union[T, Literal[INVALID]]]

NullableValue = Optional[T]

Seconds = Optional[float]

ResourceCleanup = Callable[[T], R]

ManagerCleanup = Union[
    Callable[[RawValue], Any],
    Callable[[RawValue], Awaitable[Any]],
]


