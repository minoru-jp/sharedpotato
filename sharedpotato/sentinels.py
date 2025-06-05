"""
Sentinel values for internal state management and default argument representation.

This module defines immutable singleton objects used to represent special values such as
"invalid", "undefined", or "anonymous". These sentinels are used across internal logic,
default argument markers, and type annotations.

Public sentinels:
    - INVALID   : Indicates an explicitly invalid value; may appear in type hints.
    - ANONYMOUS : Default marker for unspecified `callee` arguments.

Private sentinel:
    - _UNDEFINED: Internal-only marker for parameters that are not set, even as `None`.
                  This value is not intended to appear in type annotations or be accessed externally.

All sentinels are identity-comparable using the `is` operator and should be compared accordingly.

ja:
状態管理およびデフォルト引数のための内部用番兵値定義モジュール。

このモジュールでは、「無効」「未定義」「匿名」といった特殊な状態を表すための
不変かつ一意なシングルトンオブジェクト（番兵値）を定義します。
これらは内部処理や引数の既定値、また型アノテーションにも使用されます。

公開される番兵値:
    - INVALID   : 明示的な「無効値」を表す定数。型定義にも登場することがあります。
    - ANONYMOUS : `callee` 引数が指定されなかった場合に使用される既定値。

非公開の番兵値:
    - _UNDEFINED: `None` とも区別される「未設定」を表す内部専用の定数。
                  型アノテーションには現れず、外部からアクセスされることを想定していません。

いずれの番兵値も `is` 演算子によって同一性比較されることを前提とし、そのように扱うべきです。
"""

class _InvalidValue:
    """
    Internal marker representing an explicitly invalid value.
    Used only within this module. Do not instantiate or use externally.
    """
    #明示的な「無効値」を示す内部用マーカー。
    #本モジュール内でのみ使用されます。外部での生成や使用は避けてください。
    __slots__ = ()
    def __repr__(self):
        return "<INVALID>"

# Sentinel representing an explicitly invalid value; intended for internal use.
INVALID: _InvalidValue = _InvalidValue()

class _UndefinedValue:
    """
    Internal marker for an unset value, distinct from None.
    Used only within this module. Do not instantiate or use externally.
    """
    #None とは異なる「未設定」を示す内部用マーカー。
    #本モジュール内でのみ使用されます。外部での生成や使用は避けてください。
    __slots__ = ()
    def __repr__(self):
        return "<UNDEFINED>"

# Sentinel representing an explicitly unset value (not None); intended for internal use.
_UNDEFINED: _UndefinedValue = _UndefinedValue()

class _Anonymous:
    """
    Default placeholder for the `callee` argument.
    For internal use within this module only. Do not instantiate or use externally.
    """
    #`callee` 引数のデフォルト用プレースホルダー。
    #このモジュール内でのみ使用されることを想定しています。外部での生成や使用は避けてください。
    __slots__ = ()
    def __repr__(self):
        return "<ANONYMOUS>"

# Sentinel representing an unspecified callee; intended for internal use.
ANONYMOUS: _Anonymous = _Anonymous()
