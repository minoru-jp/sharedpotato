"""
Custom exception classes used in the sharedpotato library.

This module defines exceptions that represent specific failure conditions
in asynchronous shared object management, such as accessing closed objects,
or timing out while acquiring locks or executing cleanup handlers.

Note:
    Some exceptions, such as `SharedObjectClosed`, are generally intended for
    internal use to signal object state, but depending on design choices,
    they may be allowed to propagate to user code.
    When that is the case, it will be explicitly documented at the API level.

ja:
sharedpotatoライブラリ内部で使用されるカスタム例外定義。

このモジュールでは、非同期共有オブジェクトの管理において発生しうる
特定の失敗状態を表現する例外を定義します。
例としては、クローズ済みオブジェクトへのアクセスや、ロック取得や
クリーンアップ処理のタイムアウトなどがあります。

注記：
    `SharedObjectClosed` のようないくつかの例外は、基本的には内部処理での
    状態通知に使用されることを想定していますが、設計上の方針によっては
    ユーザーコードまで伝播される場合もあります。
    その際には、該当する高レベルAPIのドキュメントにおいて明示されます。
"""


import asyncio

class SharedObjectClosed(Exception):
    """Raised when an operation is attempted on a closed shared object."""
    # クローズされた共有オブジェクトに操作しようとしたときに送出されます。
    pass

class LockTimeout(asyncio.TimeoutError):
    """Raised when lock acquisition exceeds the allowed timeout."""
    # ロックの取得が許容時間内に完了しなかった場合に送出されます。
    pass

class HandlerTimeout(asyncio.TimeoutError):
    """Raised when a handler or cleanup operation times out."""
    # ハンドラーやクリーンアップ処理が時間内に終了しなかった場合に送出されます。
    pass

