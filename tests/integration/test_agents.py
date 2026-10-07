import pytest
from decide_ai_service_base import util
from decide_ai_service_base.sparql_config import GRAPHS
from decide_ai_service_base.util import get_agent_uri, write_agent_info

from . import tasks

SERVICE_BASE = "http://lblod.data.gift/id/components/test-service/v1.0.0"
SUBCOMPONENT = "http://lblod.data.gift/id/components/test-subcomponent/v1.0.0"

AGENTS = """
SELECT ?agent ?base WHERE {
  GRAPH <%s> {
    ?agent a <https://w3id.org/tcs#InstancePipelineComponent> ;
           <http://www.w3.org/ns/prov#specializationOf> ?base
  }
}
"""

CONFIGS = """
SELECT ?config WHERE {
  GRAPH <%s> { ?config a <http://mu.semte.ch/vocabularies/ext/AgentConfig> }
}
"""

AI_CALL = """
SELECT ?call ?predicate ?object WHERE {
  GRAPH <%s> {
    <http://example.org/test/task/ai-call> <http://mu.semte.ch/vocabularies/ext/performedAICall> ?call .
    ?call a <http://mu.semte.ch/vocabularies/ext/AICall> ;
          ?predicate ?object
  }
}
"""


@pytest.fixture(autouse=True)
def unregistered_agents(monkeypatch):
    monkeypatch.setattr(util.app.state, "config_uri", None)
    monkeypatch.setattr(util.app.state, "agent_uris", {})


def agents():
    rows = tasks.bindings(AGENTS % GRAPHS["jobs"])
    return {(row["agent"]["value"], row["base"]["value"]) for row in rows}


def test_registering_the_agent_twice_stores_one_agent_and_one_config():
    write_agent_info(SERVICE_BASE)
    write_agent_info(SERVICE_BASE)

    stored = agents()
    assert len(stored) == 1
    agent_uri, base = next(iter(stored))
    assert base == SERVICE_BASE
    assert len(tasks.bindings(CONFIGS % GRAPHS["jobs"])) == 1
    assert get_agent_uri() == agent_uri


def test_a_full_subcomponent_uri_becomes_the_specialized_component():
    write_agent_info(SERVICE_BASE, SUBCOMPONENT)

    stored = agents()
    assert len(stored) == 1
    agent_uri, base = next(iter(stored))
    assert base == SUBCOMPONENT
    assert get_agent_uri(SUBCOMPONENT) == agent_uri


def test_record_ai_call_links_the_call_to_the_task():
    task = tasks.SucceedingTask("http://example.org/test/task/ai-call")
    model = "http://example.org/test/model/example"

    task.record_ai_call("http://example.org/llm", model, 10, 20, duration=1.5)

    rows = tasks.bindings(AI_CALL % GRAPHS["jobs"])
    assert len({row["call"]["value"] for row in rows}) == 1
    ext = "http://mu.semte.ch/vocabularies/ext/"
    values = {
        row["predicate"]["value"].removeprefix(ext): row["object"]["value"]
        for row in rows
        if row["predicate"]["value"].startswith(ext)
    }
    assert values.keys() == {"endpoint", "aiModel", "tokenIn", "tokenOut", "duration"}
    assert values["endpoint"] == "http://example.org/llm"
    assert values["aiModel"] == model
    assert int(values["tokenIn"]) == 10
    assert int(values["tokenOut"]) == 20
    assert float(values["duration"]) == 1.5
