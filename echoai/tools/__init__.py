"""Load individual tools on demand without importing unrelated dependencies.

The CLI registers tools explicitly. Importing a task browser must not eagerly
import every Selenium, PDF, or execution tool.
"""

from importlib import import_module


def __getattr__(name):
    if name.startswith("_"):
        raise AttributeError(name)
    try:
        module = import_module(f".{name}", __name__)
    except ModuleNotFoundError as error:
        if error.name == f"{__name__}.{name}":
            raise AttributeError(name) from error
        raise
    value = getattr(module, name, module)
    globals()[name] = value
    return value
