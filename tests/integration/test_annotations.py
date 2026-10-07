import pytest
from decide_ai_service_base.annotation.linking import LinkingAnnotation
from decide_ai_service_base.annotation.ner import NERAnnotation
from decide_ai_service_base.annotation.relation_extraction import RelationExtractionAnnotation
from decide_ai_service_base.sparql_config import GRAPHS

from . import tasks

AGENT = "http://example.org/test/agent/annotator"
AGENT_TYPE = "http://xmlns.com/foaf/0.1/Agent"
CLASS = "http://example.org/test/class/Person"

ANNOTATIONS_OF_SOURCE = """
SELECT ?annotation WHERE {
  GRAPH <%s> {
    ?annotation a <http://www.w3.org/ns/oa#Annotation> ;
                <http://www.w3.org/ns/oa#hasTarget> ?target .
    ?target <http://www.w3.org/ns/oa#hasSource> <%s> .
  }
}
"""

ANNOTATIONS_OF_TARGET = """
SELECT ?annotation WHERE {
  GRAPH <%s> {
    ?annotation a <http://www.w3.org/ns/oa#Annotation> ;
                <http://www.w3.org/ns/oa#hasTarget> <%s> .
  }
}
"""


@pytest.fixture(autouse=True)
def agent():
    tasks.seed("annotation_agent")


def stored_for_source(source: str) -> list[str]:
    rows = tasks.bindings(ANNOTATIONS_OF_SOURCE % (GRAPHS["ai"], source))
    return [row["annotation"]["value"] for row in rows]


def stored_for_target(target: str) -> list[str]:
    rows = tasks.bindings(ANNOTATIONS_OF_TARGET % (GRAPHS["ai"], target))
    return [row["annotation"]["value"] for row in rows]


def test_ner_without_a_text_position_is_stored_once():
    source = "http://example.org/test/expression/ner-plain"
    annotation = NERAnnotation(
        "http://example.org/test/activity/ner-plain", source, CLASS, None, None, AGENT, AGENT_TYPE
    )

    annotation.add_to_triplestore_if_not_exists()
    annotation.add_to_triplestore_if_not_exists()

    assert len(stored_for_source(source)) == 1
    [read] = NERAnnotation.create_from_uri(source)
    assert read.class_uri == CLASS
    assert read.agent == AGENT
    assert read.agent_type == AGENT_TYPE
    assert (read.start, read.end) == (None, None)


def test_ner_with_a_text_position_is_read_back_with_its_position():
    source = "http://example.org/test/expression/ner-positioned"
    annotation = NERAnnotation(
        "http://example.org/test/activity/ner-positioned", source, CLASS, 3, 9, AGENT, AGENT_TYPE
    )

    annotation.add_to_triplestore_if_not_exists()

    [read] = NERAnnotation.create_from_uri(source)
    assert read.class_uri == CLASS
    assert read.agent == AGENT
    assert (read.start, read.end) == (3, 9)


def test_relation_extraction_is_read_back_with_subject_predicate_and_object():
    source = "http://example.org/test/expression/relation"
    subject = "http://example.org/test/expression/relation-subject"
    annotation = RelationExtractionAnnotation(
        subject,
        "<http://data.europa.eu/eli/ontology#title>",
        '"Titel"',
        "http://example.org/test/activity/relation",
        source,
        0,
        5,
        AGENT,
        AGENT_TYPE,
    )

    annotation.add_to_triplestore_if_not_exists()

    [read] = RelationExtractionAnnotation.create_from_uri(source)
    assert read.subject == subject
    assert read.predicate == "http://data.europa.eu/eli/ontology#title"
    assert read.object == "Titel"
    assert (read.start, read.end) == (0, 5)


def test_linking_for_an_activity_in_a_codelist_job_is_stored_once():
    tasks.seed("annotation_codelist")
    source = "http://example.org/test/expression/linking"
    annotation = LinkingAnnotation(
        "http://example.org/test/activity/linking", source, CLASS, AGENT, AGENT_TYPE
    )

    annotation.add_to_triplestore_if_not_exists()
    annotation.add_to_triplestore_if_not_exists()

    assert len(stored_for_target(source)) == 1
    [read] = LinkingAnnotation.create_from_uri(source)
    assert read.class_uri == CLASS
    assert read.agent == AGENT
    assert read.agent_type == AGENT_TYPE
