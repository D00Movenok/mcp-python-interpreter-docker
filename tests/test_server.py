from __future__ import annotations

import asyncio

import server
from server import create_app, health_check


def test_http_and_sse_routes_are_registered() -> None:
    app = create_app()
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/mcp" in paths
    assert "/sse" in paths
    assert "/messages" in paths
    assert "/health" in paths


def test_health_is_unhealthy_until_startup_packages_are_ready() -> None:
    server._startup_packages_ready = False
    server._startup_package_error = None

    response = asyncio.run(health_check(None))

    assert response.status_code == 503
    assert b'"packages_ready":false' in response.body


def test_health_is_ok_after_startup_packages_are_ready() -> None:
    server._startup_packages_ready = True
    server._startup_package_result = {"packages": ["example-package"]}

    response = asyncio.run(health_check(None))

    assert response.status_code == 200
    assert b'"packages_ready":true' in response.body
    assert b'"startup_package_count":1' in response.body
