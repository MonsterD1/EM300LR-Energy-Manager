"""Fixtures for EM300 LR tests."""

import json

import pytest

HOST = "192.168.0.23"
START = {
    "serial": "72102414",
    "app_version": "2.04",
    "auth_mode": "none",
    "authentication": True,
}
DATA = {
    "serial": "72102414",
    **{f"1-0:{c}.4.0*255": 0.0 for c in (3, 4, 9, 10, 13, 14)},
    **{f"1-0:{c}.8.0*255": 1.0 for c in (3, 4, 9, 10)},
    "1-0:1.4.0*255": 0,
    "1-0:2.4.0*255": 2302.9,
    "1-0:1.8.0*255": 11653931.3,
    "1-0:2.8.0*255": 49067315.3,
    **{
        f"1-0:{b + o}.{k}.0*255": 1.0
        for b in (20, 40, 60)
        for o in (1, 2, 3, 4, 9, 10)
        for k in (4, 8)
    },
    **{f"1-0:{b + o}.4.0*255": 1.0 for b in (20, 40, 60) for o in (11, 12, 13)},
    "status": 0,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def em300_mock(aioclient_mock):
    """Device that answers like firmware 2.04 (JSON as text/html, trailing '#')."""
    aioclient_mock.get(f"http://{HOST}/start.php", text=json.dumps(START))
    aioclient_mock.get(
        f"http://{HOST}/mum-webservice/data.php", text=json.dumps(DATA) + "#"
    )
    return aioclient_mock
