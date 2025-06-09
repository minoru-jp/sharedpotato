
import logging

from vlog import get_vlog_factory


verbose_logger = logging.getLogger(__name__)
vlog_factory = get_vlog_factory(verbose_logger)

vlog_on_instance_created = vlog_factory("instance created.")
vlog_on_called = vlog_factory("called")
vlog_on_lock_acquired = vlog_factory("lock acquired")
vlog_on_lock_released = vlog_factory("lock released")
vlog_on_custom = vlog_factory("")
vlog_on_object_closed = vlog_factory("object is closed")
vlog_on_cleanup_started = vlog_factory("cleanup started")
vlog_on_cleanup_skipped = vlog_factory("cleanup skipped")
vlog_on_timeout = vlog_factory("timeout occurred")
vlog_on_exception = vlog_factory("exception occurred")
vlog_on_default_used = vlog_factory("default value used")
vlog_on_wait_started = vlog_factory("wait started")
vlog_on_wait_finished = vlog_factory("wait finished")
vlog_on_shield_started = vlog_factory("shield started")
vlog_on_shield_finished = vlog_factory("shield finished")
vlog_on_task_created = vlog_factory("task created")
vlog_on_task_completed = vlog_factory("task completed")
vlog_on_no_handler = vlog_factory("no handler found", level=logging.INFO)

