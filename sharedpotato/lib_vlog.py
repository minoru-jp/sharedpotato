
import logging

from vlog import get_vlog_factory


_verbose_logger = logging.getLogger(__name__)
vlog_factory = get_vlog_factory(_verbose_logger)

#--About instantiation and calling--
vlog_on_instance_created = vlog_factory("instance created.")
vlog_on_called = vlog_factory("called")
vlog_on_no_handler = vlog_factory("no handler found", level=logging.INFO)

#--About lock--
vlog_on_lock_acquired = vlog_factory("lock acquired")
vlog_on_lock_released = vlog_factory("lock released")

#--About synchronous--
vlog_on_wait_started = vlog_factory("wait started")
vlog_on_wait_finished = vlog_factory("wait finished")
vlog_on_timeout = vlog_factory("timeout occurred")
vlog_on_shield_started = vlog_factory("shield started")
vlog_on_shield_finished = vlog_factory("shield finished")

#--About task--
vlog_on_task_created = vlog_factory("task created")

#--About Error--
vlog_on_exception = vlog_factory("unexpected exception occurred", level=logging.INFO)


#--Copy and paste for import all--
# vlog_on_instance_created,
# vlog_on_called,
# vlog_on_no_handler,
# vlog_on_lock_acquired,
# vlog_on_lock_released,
# vlog_on_wait_started,
# vlog_on_wait_finished,
# vlog_on_timeout,
# vlog_on_shield_started,
# vlog_on_shield_finished,
# vlog_on_task_created,
# vlog_on_exception,

#vlog_on_object_closed = sharedpotato_vlog_factory("object is closed")
#vlog_on_cleanup_started = sharedpotato_vlog_factory("cleanup started")
#vlog_on_cleanup_skipped = sharedpotato_vlog_factory("cleanup skipped")


