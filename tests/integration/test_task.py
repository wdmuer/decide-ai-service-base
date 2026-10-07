import pytest
from decide_ai_service_base.sparql_config import GRAPHS
from decide_ai_service_base.task import Task

from . import tasks

EXT = "http://mu.semte.ch/vocabularies/ext/"
TASK = "http://redpencil.data.gift/vocabularies/tasks/"

ERROR_MESSAGES = """
SELECT ?message WHERE {
  GRAPH <%s> {
    ?error a <http://mu.semte.ch/vocabularies/ext/ErrorMessage> ;
           <http://purl.org/dc/terms/description> ?message
  }
}
"""


def test_from_uri_returns_the_class_registered_for_the_operation():
    tasks.seed("succeed")

    task = Task.from_uri("http://example.org/test/task/succeed")

    assert type(task) is tasks.SucceedingTask


def test_from_uri_rejects_an_operation_no_class_registers():
    tasks.seed("unknown_operation")

    with pytest.raises(RuntimeError, match="Unknown task type http://example.org/test/operation/unregistered"):
        Task.from_uri("http://example.org/test/task/unknown-operation")


def test_from_uri_rejects_a_task_that_does_not_exist():
    with pytest.raises(RuntimeError, match="Task with uri .* not found"):
        Task.from_uri("http://example.org/test/task/missing")


def test_a_succeeding_task_records_its_outcome():
    task_uri = "http://example.org/test/task/succeed"
    tasks.seed("succeed")

    tasks.run(task_uri)

    assert tasks.status(task_uri) == tasks.SUCCESS
    assert len(tasks.task_objects(task_uri, EXT + "startedAt")) == 1
    assert len(tasks.task_objects(task_uri, EXT + "endedAt")) == 1
    assert set(tasks.task_objects(task_uri, TASK + "resultsContainer")) == {tasks.RESULT_CONTAINER}


def test_a_failing_task_reraises_fails_and_logs_the_error():
    task_uri = "http://example.org/test/task/fail"
    tasks.seed("fail")

    with pytest.raises(RuntimeError, match="boom"):
        tasks.run(task_uri)

    assert tasks.status(task_uri) == tasks.FAILED
    rows = tasks.bindings(ERROR_MESSAGES % GRAPHS["data_containers"])
    assert {row["message"]["value"] for row in rows} == {
        f"Task {task_uri} failed: RuntimeError: boom"
    }
