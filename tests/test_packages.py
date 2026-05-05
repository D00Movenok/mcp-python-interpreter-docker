from __future__ import annotations

import asyncio

import pytest

import packages as package_helpers
from models import InvalidInputError
from packages import list_installed_packages, packages_from_env


def test_packages_from_env_uses_shell_splitting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTHON_PACKAGES", "numpy 'git+https://example.test/repo.git'")

    assert packages_from_env() == ["numpy", "git+https://example.test/repo.git"]


def test_packages_from_env_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTHON_PACKAGES", raising=False)

    assert packages_from_env() == []


def test_install_packages_rejects_empty_list() -> None:
    with pytest.raises(InvalidInputError):
        asyncio.run(package_helpers.install_packages([]))


def test_list_installed_packages_returns_structured_result() -> None:
    result = asyncio.run(list_installed_packages(max_results=1))

    assert result["count"] >= 1
    assert isinstance(result["packages"], list)
    assert len(result["packages"]) == 1
    assert "name" in result["packages"][0]
