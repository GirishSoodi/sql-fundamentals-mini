import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import fittrack


class TestCommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "fittrack.db")
        patcher = mock.patch.object(fittrack, "DB_PATH", self.db)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp)

    def cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = fittrack.main(list(args))
        return code, out.getvalue()

    def test_run_before_build_explains_what_to_do(self):
        code, out = self.cli("run", "list_clients")
        self.assertEqual(code, 1)
        self.assertIn("python fittrack.py build", out)

    def test_build_twice_starts_fresh(self):
        self.cli("build")
        self.cli("run", "add_client", "name=Eva", "email=eva@example.com",
                 "join_date=2026-04-01")
        code, out = self.cli("build")
        self.assertEqual(code, 0)
        self.assertIn("4 clients, 8 sessions", out)

    def test_run_report_prints_table(self):
        self.cli("build")
        code, out = self.cli("run", "summary_report")
        self.assertEqual(code, 0)
        self.assertIn("Dev Patel", out)
        self.assertIn("(4 rows)", out)

    def test_missing_parameter_is_an_error(self):
        self.cli("build")
        code, out = self.cli("run", "add_client", "name=Eva")
        self.assertEqual(code, 1)
        self.assertIn("Error:", out)


if __name__ == "__main__":
    unittest.main()

