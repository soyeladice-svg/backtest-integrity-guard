import io
import sys
import unittest
from contextlib import redirect_stdout

import backtest_integrity_guard
from backtest_integrity_guard import cli


class VersionTests(unittest.TestCase):
    def test_version_prints_package_version_and_exits_zero(self):
        old_argv = sys.argv
        sys.argv = ["btguard", "--version"]
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                with self.assertRaises(SystemExit) as ctx:
                    cli.main()
        finally:
            sys.argv = old_argv

        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(buf.getvalue().strip(), backtest_integrity_guard.__version__)


if __name__ == "__main__":
    unittest.main()
