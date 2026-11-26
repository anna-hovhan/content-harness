import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import test_check_repetition as rep  # noqa: E402

P1 = "Shared context decides who owns each note and how current every team note stays across the company today."
P2 = "A team note stays current only when shared context names its owner and the company checks how current it is."
OTHER = "The prototype ships with a test suite and continuous integration, and nobody outside the author has run it yet."


class Repetition(unittest.TestCase):
    def test_flags_restated_point(self):
        self.assertTrue(any("overlap" in m for m in rep.check(f"{P1}\n\n{P2}\n")))

    def test_distinct_paragraphs_pass(self):
        self.assertEqual(rep.check(f"{P1}\n\n{OTHER}\n"), [])

    def test_flags_many_code_terms(self):
        text = " ".join(f"`t{i}`" for i in range(7))
        self.assertTrue(any("backticked" in m for m in rep.check(text)))


if __name__ == "__main__":
    unittest.main()
