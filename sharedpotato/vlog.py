"""
Verbose log function generator for structured debug logging.

This module provides a factory that creates reusable logging functions (called VlogFunctions)
designed for **verbose-level tracing** of object lifecycle, method calls, and runtime events.
Each generated function includes context such as class name, object ID, method name,
and a user-defined label or message.

The term "Vlog" stands for "Verbose Log", emphasizing its purpose as a fine-grained,
developer-focused diagnostic tool. Templates can be customized with prefixes, suffixes,
or full format strings, and the log level is adjustable (default: DEBUG).

Usage example:
    template = "[{cls} id={id}].{mn} >> {label} {msg}"
    vlog = vlog_factory(label="called", template=template)
    vlog(obj, "method_name", "processing started")

Format placeholders:
    - {cls}   : Class name of the target object
    - {id}    : Object ID (from id())
    - {mn}    : Method name
    - {label} : User-defined label (e.g., "called", "created")
    - {msg}   : Runtime message to log

Error handling:
    If the format string contains invalid keys or malformed syntax,
    the system logs a diagnostic error message at DEBUG level (not raised).

ja:
詳細なデバッグログ（Verbose Log）のための関数生成モジュール。

このモジュールは、再利用可能なログ関数（VlogFunction）を生成するファクトリを提供します。
Vlog は “Verbose Log” の略で、オブジェクトのライフサイクルやメソッド呼び出し、
ランタイムイベントを**詳細に追跡するためのログ**として設計されています。

生成される関数は、クラス名・オブジェクトID・メソッド名・任意のラベルやメッセージを
一貫した形式で出力します。プレフィックスやサフィックス、完全なテンプレートを
指定することで、柔軟な出力フォーマットが可能です。
ログレベルも任意に設定できます（デフォルト: DEBUG）。

テンプレート構文で使用可能な変数:
    - {cls}   : 対象オブジェクトのクラス名
    - {id}    : 対象オブジェクトの ID（id() の結果）
    - {mn}    : メソッド名
    - {label} : ログラベル（例: "called", "created" など）
    - {msg}   : 実行時に渡されるメッセージ

テンプレートエラー処理:
    プレースホルダの欠落やフォーマット構文ミスがあった場合でも例外は送出されず、
    DEBUG レベルで内部エラーとして記録されます。
"""

import logging

from typing import Protocol, Optional
from typing import Any

LOG_CONTEXT = "[{cls} id={id}].{mn}"

class VlogFunction(Protocol):
    """
    A callable that logs a message with object context.

    Arguments:
        obj: The target instance.
        mn: The method name where logging occurs.
        msg: Optional log message.
        level: Logging level (default: DEBUG).

    ja:
    オブジェクトの文脈を含めてログを出力する呼び出し可能オブジェクト。

    引数:
        obj: 対象のインスタンス。
        mn: ログ出力元のメソッド名。
        msg: 任意のメッセージ。
        level: ログ出力レベル（デフォルトは DEBUG）。
    """
    def __call__(
            self,
            obj: Any,
            mn: str,
            msg: str = "",
            level: int = logging.DEBUG
            ) -> None: ...

class VlogFactory(Protocol):
    """
    A callable that creates a contextual logging function.

    Arguments:
        label: Label to include in the log (e.g. "called", "timeout").
        prefix: Format prefix before the label.
        suffix: Format suffix after the label.
        template: Full format string. Overrides prefix/suffix if provided.

    ja:
    文脈付きログ関数を生成する呼び出し可能オブジェクト。

    引数:
        label: ログに含めるラベル（例: "called", "timeout"）。
        prefix: ラベルの前に出力されるフォーマット文字列。
        suffix: ラベルの後に出力されるフォーマット文字列。
        template: フォーマット全体を直接指定する場合に使用。
                  指定された場合は prefix/suffix を無視します。
    """
    def __call__(
            self,
            label: str,
            prefix: str = LOG_CONTEXT,
            suffix: str = " {msg}",
            template: Optional[str] = None
            ) -> VlogFunction: ...

def get_vlog_factory(logger: logging.Logger) -> VlogFactory:
    """
    Returns a factory for creating contextual logging functions using the given logger.

    Arguments:
        logger: The logger to use for all generated functions.

    ja:
    指定されたロガーを用いて文脈付きログ関数を生成するファクトリを返します。

    引数:
        logger: 生成されたログ関数で使用されるロガー。
    """
    def vlog_factory(
            label: str,
            prefix: str = LOG_CONTEXT,
            suffix: str = " {msg}",
            template: Optional[str] = None) -> VlogFunction:
        """
        Creates a logging function that outputs contextual messages with a given label.

        If `template` is provided, it overrides `prefix`, `suffix`, and `label`.

        The format string (from `template`, or assembled from `prefix`, `label`, and `suffix`)
        can include the following placeholders:
            - {cls}   : Class name of the target object
            - {id}    : Object ID (from id())
            - {mn}    : Method name
            - {label} : User-defined label
            - {msg}   : Runtime log message content

        Arguments:
            label: The label to embed in the log output.
            prefix: Format string prepended before the label (default: LOG_CONTEXT).
            suffix: Format string appended after the label. Typically includes `{msg}`.
            template: Full format string. If given, it is used directly instead of combining prefix, label, and suffix.

        ja:
        指定されたラベルを含む文脈付きログ関数を生成します。

        `template` が指定された場合は、`prefix`、`suffix`、`label` は無視されます。

        テンプレート文字列（`template` または `prefix` + `label` + `suffix`）で
        使用できるプレースホルダは以下のとおりです：
            - {cls}   : 対象オブジェクトのクラス名
            - {id}    : 対象オブジェクトの ID（`id()` の結果）
            - {mn}    : メソッド名
            - {label} : ログに埋め込まれるラベル
            - {msg}   : 実行時に渡されるメッセージ

        引数:
            label: ログ出力に埋め込まれるラベル。
            prefix: ラベルの前に挿入されるフォーマット文字列（デフォルト: LOG_CONTEXT）。
            suffix: ラベルの後に追加されるフォーマット文字列。
                    通常は `{msg}` を含めて出力の末尾構造を定義します。
            template: フォーマット全体を直接指定する場合に使用されます。
                    指定された場合は、他の3つの引数は無視されます。
        """
        templ:str = prefix + " >>" + " {label} " + suffix \
                    if template is None else str(template)
        key_error_msg: Optional[str] = None
        value_error_msg: Optional[str] = None
        def vlog_function(
                obj,
                mn: str,
                msg: str = "",
                level: int = logging.DEBUG) -> None:
            """
            Function generated by the vlog factory to emit verbose log messages.

            ja:
            vlogファクトリによって生成され、実際にログ出力を行う関数です。
            """
            nonlocal key_error_msg
            nonlocal value_error_msg
            if logger.isEnabledFor(level):
                try:
                    formatted = templ.format(
                        cls = type(obj).__name__,
                        id = id(obj),
                        mn = mn,
                        label = label,
                        msg = msg
                    )
                    logger.log(level, formatted)
                except KeyError as e:
                    if not key_error_msg:
                        key_error_msg =\
                            f"{__name__} VLOG KEY ERROR: " +\
                            f"key={e.args[0]} "+\
                            f"label={label} template={templ}"
                    logger.debug(key_error_msg)
                except ValueError as e:
                    if not value_error_msg:
                        value_error_msg =\
                            f"{__name__} VLOG VALUE ERROR: " +\
                            f"template={templ} "+\
                            f"label={label}"
                    logger.debug(value_error_msg)
                
        return vlog_function
    return vlog_factory


def example_usage() -> None:
    """
    Demonstrates both normal and error-producing usage of vlog functions.
    All logs (normal and exceptions) are sent through the same logger.
    """
    # Setup a logger (output to stderr by default)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Create a vlog factory tied to this logger
    vlog_factory = get_vlog_factory(logger)

    # Normal usage with standard template
    vlog_on_created = vlog_factory("created")
    vlog_on_called = vlog_factory("called")
    vlog_on_fail = vlog_factory("failed", suffix="!!{msg}")

    # Log normal lifecycle events
    class Example:
        def __init__(self):
            vlog_on_created(self, "init", "instance initialized")

        def start(self):
            vlog_on_called(self, "start")

        def fail(self):
            vlog_on_fail(self, "fail", "operation failed")

    ex = Example()
    ex.start()
    ex.fail()

    # Error: missing placeholder causes KeyError
    vlog_keyerror = vlog_factory(
        label="invalid_key",
        template="[INVALID {cls} {unknown}] {msg}"  # {unknown} is not a valid key
    )
    vlog_keyerror(ex, "key_error", "This should trigger KeyError")

    # Error: malformed template causes ValueError
    vlog_valueerror = vlog_factory(
        label="invalid_format",
        template="Malformed template {cls!}"  # Invalid format specifier
    )
    vlog_valueerror(ex, "value_error", "This should trigger ValueError")


if __name__ == "__main__":
    # Call the usage example when run directly
    example_usage()
