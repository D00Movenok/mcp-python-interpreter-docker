from __future__ import annotations


class PythonInterpreterError(Exception):
    """Base exception for interpreter errors."""


class InvalidInputError(PythonInterpreterError):
    """Raised when tool input is invalid."""


class PackageInstallError(PythonInterpreterError):
    """Raised when package installation fails."""
