
import logging

verbose_logger = logging.getLogger(__name__)

def vlog_on_instance_created(obj, msg: str = "") -> None:
    """
    Use:
        Call when a new instance of a class is created.
    Example:
        vlog_on_instance_created(self, "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}] instance created. {msg}")

def vlog_on_instance_created_with_args(obj, *args, msg: str = "", **kwargs) -> None:
    """
    Use:
        Call when a new instance is created with constructor arguments.
    Example:
        vlog_on_instance_created_with_args(self, 1, 2, key="val", msg="optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        args_repr = ", ".join(repr(a) for a in args)
        kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}] instance created with args: {all_args}. {msg}")

def vlog_on_called(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call at the start of a method to trace its invocation.
    Example:
        vlog_on_called(self, "method_name", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} called. {msg}")

def vlog_on_lock_acquired(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call immediately after acquiring a lock.
    Example:
        vlog_on_lock_acquired(self, "method_name", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} lock acquired. {msg}")

def vlog_on_lock_released(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call immediately after releasing a lock.
    Example:
        vlog_on_lock_released(self, "method_name", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} lock released. {msg}")

def vlog_on_custom(obj, mn: str, message: str, msg: str = "") -> None:
    """
    Use:
        Call to log any custom debug-level message.
    Example:
        vlog_on_custom(self, "method_name", "message", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} {message} {msg}")

def vlog_on_custom_info(obj, mn: str, message: str, msg: str = "") -> None:
    """
    Use:
        Call to log a custom informational message.
    Example:
        vlog_on_custom_info(self, "method_name", "info message", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.INFO):
        verbose_logger.info(f"[{type(obj).__name__} id={id(obj)}].{mn} {message} {msg}")

def vlog_on_object_closed(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call when the object is detected to be closed.
    Example:
        vlog_on_object_closed(self, "method_name", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} object is closed. {msg}")

def vlog_on_cleanup_started(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call before starting a cleanup procedure.
    Example:
        vlog_on_cleanup_started(self, "cleanup", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} cleanup started. {msg}")

def vlog_on_cleanup_skipped(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call when cleanup is skipped due to prior conditions.
    Example:
        vlog_on_cleanup_skipped(self, "cleanup", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} cleanup skipped. {msg}")

def vlog_on_timeout(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call when a timeout condition is detected.
    Example:
        vlog_on_timeout(self, "operation", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} timeout occurred. {msg}")

def vlog_on_exception(obj, mn: str, exc: Exception, msg: str = "") -> None:
    """
    Use:
        Call when an exception is caught and needs to be logged.
    Example:
        vlog_on_exception(self, "method_name", exception_obj, "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} exception occurred: {exc}. {msg}")

def vlog_on_default_used(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call when a default value is substituted for a missing or invalid one.
    Example:
        vlog_on_default_used(self, "get", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} default value used. {msg}")

def vlog_on_wait_started(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call before an async wait or blocking operation begins.
    Example:
        vlog_on_wait_started(self, "get", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} wait started. {msg}")

def vlog_on_wait_finished(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call after an async wait or blocking operation completes.
    Example:
        vlog_on_wait_finished(self, "get", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} wait finished. {msg}")

def vlog_on_shield_started(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call before an asyncio shield.
    Example:
        vlog_on_shield_started(self, "method_name", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} shield started. {msg}")

def vlog_on_shield_finished(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call after an asyncio shield.
    Example:
        vlog_on_shield_finished(self, "method_name", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} shield finished. {msg}")

def vlog_on_task_created(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call after spawning an async task.
    Example:
        vlog_on_task_created(self, "cleanup", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} task created. {msg}")

def vlog_on_task_completed(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call after a task has completed execution.
    Example:
        vlog_on_task_completed(self, "cleanup", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} task completed. {msg}")

def vlog_on_accessor_used(obj, mn: str, accessor_method: str, msg: str = "") -> None:
    """
    Use:
        Call when a specific accessor method is used (e.g., without lock).
    Example:
        vlog_on_accessor_used(self, "set", "without_lock", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} accessor used: {accessor_method}. {msg}")

def vlog_on_invalid_value_detected(obj, mn: str, msg: str = "") -> None:
    """
    Use:
        Call when an invalid sentinel value is detected (e.g., INVALID_VALUE).
    Example:
        vlog_on_invalid_value_detected(self, "get", "optional message")
    """
    if verbose_logger.isEnabledFor(logging.DEBUG):
        verbose_logger.debug(f"[{type(obj).__name__} id={id(obj)}].{mn} invalid value detected. {msg}")
