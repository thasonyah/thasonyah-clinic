import asyncio

import httpx

from app.main import app


def test_health_contract():
    async def check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.get("/api/v1/healthz")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            ready = await c.get("/api/v1/readyz")
            assert ready.status_code == 200
            assert ready.json() == {"status": "ready"}

    asyncio.run(check())
