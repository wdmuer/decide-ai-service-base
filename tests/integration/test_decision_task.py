from decide_ai_service_base.task import DecisionTask

from . import tasks


class ExampleDecisionTask(DecisionTask):
    __task_type__ = "http://example.org/test/operation/decision"

    def process(self):
        pass


def test_fetch_data_returns_each_text_of_the_input_expression_once():
    tasks.seed("decision_input")

    data = ExampleDecisionTask("http://example.org/test/task/decision").fetch_data()

    assert data == "\n".join(
        [
            "The council approves the budget.",
            "Budget 2026",
            "Article 12 of the municipal decree",
        ]
    )


def test_fetch_work_uri_returns_the_work_the_expression_realizes():
    tasks.seed("decision_input")

    task = ExampleDecisionTask("http://example.org/test/task/decision")

    assert task.fetch_work_uri() == "http://example.org/test/work/decision"


def test_fetch_work_uri_returns_none_without_a_realized_work():
    tasks.seed("decision_input_without_work")

    task = ExampleDecisionTask("http://example.org/test/task/decision-without-work")

    assert task.fetch_work_uri() is None
