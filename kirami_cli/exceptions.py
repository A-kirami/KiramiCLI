class ModuleLoadFailed(RuntimeError):
    """Raised when a module fails to load."""


class PythonInterpreterError(RuntimeError):
    """Raised when the Python version is not supported."""


class PipNotInstalledError(RuntimeError):
    """Raised when pip is not installed."""


class KiramiBotNotInstalledError(RuntimeError):
    """Raised when KiramiBot is not installed."""


class ProjectNotFoundError(RuntimeError):
    """Raised when project root directory not found"""
