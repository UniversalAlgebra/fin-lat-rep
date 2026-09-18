"""
File: scripts/python/finlatrep/test_con_table.py

Description: Tests for the pure parts of the Jython second engine.

  scripts/jython/con_table.py runs under Jython, but it is written so that
  everything except the UACalc import is ordinary Python that either
  interpreter can load.  That lets its argument and classpath handling be
  tested here, from Python 3, without a JVM.  What cannot be tested without
  one is the UACalc call itself; docs/CHECKING-AN-ALGEBRA.md shows that run.
"""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

CON_TABLE = Path(__file__).resolve().parents[2] / "jython" / "con_table.py"


def _load() -> types.ModuleType:
    """Load the Jython script as a module, by path."""
    spec = importlib.util.spec_from_file_location("con_table", CON_TABLE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load()
        self._path = list(sys.path)

    def tearDown(self) -> None:
        sys.path[:] = self._path

    def test_the_script_is_where_the_documentation_says(self) -> None:
        self.assertTrue(CON_TABLE.is_file(), f"not found: {CON_TABLE}")

    def test_jars_are_put_on_sys_path(self) -> None:
        self.module.add_jars_to_path(["/tmp/uacalc.jar", "/tmp/LatDraw.jar"])
        self.assertIn("/tmp/uacalc.jar", sys.path)
        self.assertIn("/tmp/LatDraw.jar", sys.path)

    def test_empty_entries_are_skipped(self) -> None:
        """A trailing colon in UACALC_JARS must not put '' on sys.path."""
        before = len(sys.path)
        self.module.add_jars_to_path(["", ""])
        self.assertEqual(len(sys.path), before)

    def test_a_jar_is_not_added_twice(self) -> None:
        self.module.add_jars_to_path(["/tmp/uacalc.jar"])
        before = len(sys.path)
        self.module.add_jars_to_path(["/tmp/uacalc.jar"])
        self.assertEqual(len(sys.path), before)

    def test_wrong_argument_count_is_refused(self) -> None:
        self.assertEqual(self.module.main(["con_table.py"]), 2)

    def test_missing_uacalc_jars_is_refused_with_an_exit_code(self) -> None:
        """Not an exception: the caller gets a message and a status."""
        import os

        saved = os.environ.pop("UACALC_JARS", None)
        try:
            self.assertEqual(self.module.main(["con_table.py", "x.ua"]), 2)
        finally:
            if saved is not None:
                os.environ["UACALC_JARS"] = saved


if __name__ == "__main__":
    unittest.main()
