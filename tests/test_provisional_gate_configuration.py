"""T042 (B1, D213): the provisional gate reads every Stryker config file name Stryker 10 looks for as configuration.

Stryker's `findConfigFile` tries `stryker.conf` and `stryker.config` with `.json`, `.js`, `.mjs` and `.cjs`; the wrapper
runs one of them, but a project can hold the others, and editing any of them is a change to the gate's own settings.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from typing import Any

from slipwai.assets import TOOLKIT_ROOT

sys.dont_write_bytecode = True


def provisional() -> Any:
    path = TOOLKIT_ROOT / "scripts/provisional.py"
    spec = importlib.util.spec_from_file_location("provisional_gate_configuration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GateConfigurationTest(unittest.TestCase):
    def test_every_stryker_config_file_name_is_gate_configuration(self) -> None:
        pattern = provisional().GATE_CONFIGURATION
        for stem in ("stryker.conf", "stryker.config"):
            for extension in ("json", "js", "mjs", "cjs"):
                with self.subTest(name=f"{stem}.{extension}"):
                    self.assertIsNotNone(pattern.fullmatch(f"{stem}.{extension}"))

    def test_hold_a_name_that_only_looks_like_one_is_not(self) -> None:
        pattern = provisional().GATE_CONFIGURATION
        for name in ("stryker.conf", "stryker.conf.json.bak", "mystryker.conf.json", "stryker.json",
                     "stryker.confs.js"):
            with self.subTest(name=name):
                self.assertIsNone(pattern.fullmatch(name))


if __name__ == "__main__":
    unittest.main()
