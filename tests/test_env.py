import os
import tempfile
import unittest
from pathlib import Path

from polign_curator.env import load_project_env
from polign_curator.cli import _short_answer


class EnvTests(unittest.TestCase):
    def test_loads_values_without_overriding_existing_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("DEMO_NEW=value\nDEMO_EXISTING=from-file\n", encoding="utf-8")
            os.environ["DEMO_EXISTING"] = "from-shell"
            os.environ.pop("DEMO_NEW", None)
            try:
                self.assertTrue(load_project_env(path))
                self.assertEqual("value", os.environ["DEMO_NEW"])
                self.assertEqual("from-shell", os.environ["DEMO_EXISTING"])
            finally:
                os.environ.pop("DEMO_NEW", None)
                os.environ.pop("DEMO_EXISTING", None)

    def test_short_answer_keeps_the_final_summary(self):
        answer = "Long evidence.\n\n**In short**\n- Pick Monet."
        self.assertEqual("**In short**\n- Pick Monet.", _short_answer(answer))


if __name__ == "__main__":
    unittest.main()
