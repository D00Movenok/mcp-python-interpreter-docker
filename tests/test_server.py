from __future__ import annotations

from server import create_app


def test_http_and_sse_routes_are_registered() -> None:
    app = create_app()
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/mcp" in paths
    assert "/sse" in paths
    assert "/messages" in paths
