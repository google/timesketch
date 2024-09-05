"""DFIQ Analyzer module."""

import os
import importlib
import inspect
import logging
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager as analyzer_manager

import timesketch.lib.analyzers.dfiq_plugins.manager

logger = logging.getLogger("timesketch.lib.analyzers.dfiq_plugins")

# Dynamically load DFIQ Analyzers
DFIQ_ANALYZER_PATH = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(DFIQ_ANALYZER_PATH):
    if filename.endswith(".py") and not filename.startswith("__"):
        module_name = filename[:-3]  # Remove .py extension
        if module_name == "manager":
            continue
        module_path = f"timesketch.lib.analyzers.dfiq_plugins.{module_name}"
        try:
            module = importlib.import_module(module_path)
            for name, obj in inspect.getmembers(module):
                if name not in [
                    "interface",
                    "logger",
                    "logging",
                    "manager",
                ] and not name.startswith("__"):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, interface.BaseAnalyzer)
                        and hasattr(obj, "IS_DFIQ_ANALYZER")
                        and obj.IS_DFIQ_ANALYZER
                    ):
                        analyzer_manager.AnalysisManager.register_analyzer(obj)
                        logger.info("Registered DFIQ analyzer: %s", obj.NAME)
                    else:
                        logger.error(
                            'Skipped loading "%s" as analyzer, since it did '
                            "not meet the requirements.",
                            str(module_path),
                        )
        except ImportError as error:
            logger.error(
                "Failed to import dfiq analyzer module: %s, %s",
                str(module_path),
                str(error),
            )
