from unittest.mock import patch

import pytest

from services.real_time_performance_architecture import L3APILayer
from models.market_data import MarketData


@pytest.mark.asyncio
async def test_l3_live_data_upstox_mapping(monkeypatch):
    # Enable feature flag and token
    monkeypatch.setenv('UPSTOX_LIVE_DATA_ENABLED', 'true')
    monkeypatch.setenv('UPSTOX_ACCESS_TOKEN', 'test_token')
    monkeypatch.setenv('UPSTOX_BASE_URL', 'https://api.upstox.com/v2')

    layer = L3APILayer(websocket_pool=None)

    symbols = ['RELIANCE', 'TCS']

    class MockResponse:
        def __init__(self, status: int, payload: dict):
            self.status = status
            self._payload = payload
        async def json(self):
            return self._payload
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class MockSession:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        def get(self, url, headers=None):
            payload = {
                'data': {
                    'NSE_EQ|RELIANCE': {'ltp': 2510.5},
                    'NSE_EQ|TCS': {'ltp': 3921.0},
                }
            }
            return MockResponse(200, payload)

    with patch('services.real_time_performance_architecture.aiohttp.ClientSession', return_value=MockSession()):
        data = await layer._fetch_upstox_ltp(symbols)

    assert isinstance(data, dict)
    assert 'RELIANCE' in data and 'TCS' in data
    assert isinstance(data['RELIANCE'], MarketData)
    assert data['RELIANCE'].last_price == 2510.5
    assert data['RELIANCE'].source == 'UPSTOX'
    assert data['TCS'].last_price == 3921.0
