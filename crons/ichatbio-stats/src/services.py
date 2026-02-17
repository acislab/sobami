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

def check_all(services: Iterable[str]) -> Iterator[Tuple[str, bool]]:
    for service in services:
        parts = service.split(" ")
        name = " ".join(parts[:-1])
        url = parts[-1]
        yield name, check_ok(url)
