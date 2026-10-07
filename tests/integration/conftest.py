import os
import time

import pytest
import requests
from decide_ai_service_base.sparql_config import GRAPHS
from helpers import update

ENDPOINT = os.environ["MU_SPARQL_ENDPOINT"]


@pytest.fixture(scope="session", autouse=True)
def virtuoso():
    deadline = time.monotonic() + 180
    while True:
        try:
            requests.post(
                ENDPOINT, data={"query": "ASK { ?s ?p ?o }"}, timeout=10
            ).raise_for_status()
            return
        except requests.RequestException:
            if time.monotonic() > deadline:
                raise
            time.sleep(2)


# Task pickup and recovery act on every task in the jobs graph, so tests must start empty.
@pytest.fixture(autouse=True)
def empty_graphs(virtuoso):
    for graph in GRAPHS.values():
        update(f"CLEAR SILENT GRAPH <{graph}>", sudo=True)
