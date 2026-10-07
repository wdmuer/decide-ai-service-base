"""Seed tasks and run them the way a service does."""
import pathlib
from collections import defaultdict

from decide_ai_service_base.sparql_config import GRAPHS, JOB_STATUSES
from decide_ai_service_base.task import Task
from helpers import query, update
from rdflib import Graph

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

SUCCESS = JOB_STATUSES["success"]
FAILED = JOB_STATUSES["failed"]

RESULT_CONTAINER = "http://example.org/test/container/result"

# The graph the library's queries read each fixture subject from.
GRAPH_BY_SUBJECT_PREFIX = {
    "http://example.org/test/task/": "jobs",
    "http://example.org/test/job/": "jobs",
    "http://example.org/test/container/": "jobs",
    "http://example.org/test/agent/": "jobs",
    "http://example.org/test/expression/": "expressions",
    "http://example.org/test/work/": "expressions",
    "http://example.org/test/activity/": "ai",
    "http://example.org/test/codelist/": "ai",
}

INSERT_INTO_GRAPH = "INSERT DATA { GRAPH <%s> { %s } }"

TASK_OBJECTS = """
SELECT ?object WHERE {
  GRAPH <%s> { <%s> <%s> ?object }
}
"""


class SucceedingTask(Task):
    __task_type__ = "http://example.org/test/operation/succeed"

    def process(self):
        self.results_container_uris.append(RESULT_CONTAINER)


class FailingTask(Task):
    __task_type__ = "http://example.org/test/operation/fail"

    def process(self):
        raise RuntimeError("boom")


def bindings(sparql: str) -> list[dict]:
    return query(sparql, sudo=True)["results"]["bindings"]


def _graph_for(subject: str) -> str:
    for prefix, key in GRAPH_BY_SUBJECT_PREFIX.items():
        if subject.startswith(prefix):
            return key
    raise ValueError(f"no graph for fixture subject {subject}")


def seed(fixture_name: str) -> None:
    buckets = defaultdict(Graph)
    for triple in Graph().parse(FIXTURES / f"{fixture_name}.ttl"):
        buckets[_graph_for(str(triple[0]))].add(triple)

    for key, data in buckets.items():
        update(INSERT_INTO_GRAPH % (GRAPHS[key], data.serialize(format="nt")), sudo=True)


def run(task_uri: str) -> None:
    Task.from_uri(task_uri).execute()


def task_objects(task_uri: str, predicate: str) -> list[str]:
    rows = bindings(TASK_OBJECTS % (GRAPHS["jobs"], task_uri, predicate))
    return [row["object"]["value"] for row in rows]


def status(task_uri: str) -> str:
    rows = task_objects(task_uri, "http://www.w3.org/ns/adms#status")
    assert len(rows) == 1, f"expected one status for {task_uri}, got {len(rows)}"
    return rows[0]
