
class _InvalidValue:
    def __repr__(self):
        return "<INVALID_VALUE>"

INVALID: _InvalidValue = _InvalidValue()

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
