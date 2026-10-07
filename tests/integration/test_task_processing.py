from threading import Lock

from decide_ai_service_base.util import (TaskProcessor,
                                         fail_busy_and_scheduled_tasks,
                                         get_one_open_task)

from . import tasks

TASK = "http://example.org/test/task/"


def test_get_one_open_task_returns_the_scheduled_task_with_a_registered_operation():
    tasks.seed("busy")
    tasks.seed("unknown_operation")
    tasks.seed("succeed")

    assert get_one_open_task() == TASK + "succeed"


def test_get_one_open_task_ignores_busy_and_unregistered_tasks():
    tasks.seed("busy")
    tasks.seed("unknown_operation")

    assert get_one_open_task() is None


def test_task_processor_runs_every_open_task_even_when_one_fails():
    tasks.seed("fail")
    tasks.seed("succeed")
    tasks.seed("succeed_other")

    TaskProcessor(Lock())()

    assert tasks.status(TASK + "fail") == tasks.FAILED
    assert tasks.status(TASK + "succeed") == tasks.SUCCESS
    assert tasks.status(TASK + "succeed-other") == tasks.SUCCESS


def test_fail_busy_and_scheduled_tasks_fails_a_busy_task():
    tasks.seed("busy")

    fail_busy_and_scheduled_tasks()

    assert tasks.status(TASK + "busy") == tasks.FAILED
