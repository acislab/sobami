import logging
from typing import Iterator, Tuple, Iterable

import requests


def check_ok(url: str):
    try:
        logging.info(f"Pinging {url}")
        result = requests.get(url)
        result.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.warning("Failed health check: " + url, exc_info=e)
        return False

def check_all(agents: Iterable[str]) -> Iterator[Tuple[str, bool]]:
    yield "ichatbio.org", check_ok("https://ichatbio.org")

    for agent in agents:
        url = f"http://icb-agents.acis.ufl.edu/{agent}/.well-known/agent.json"
        yield agent, check_ok(url)