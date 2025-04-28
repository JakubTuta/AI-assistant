import importlib
import os
import sys
from pathlib import Path


def discover_services():
    """Automatically import all service modules in this package."""
    current_dir = Path(__file__).parent

    for filename in os.listdir(current_dir):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue

        module_name = filename[:-3]

        full_module_name = f"{__name__}.{module_name}"
        importlib.import_module(full_module_name)


discover_services()
