
from pathlib import Path
import unittest

from dist.main import resolve_output_file_path


class TestResolvePath(unittest.TestCase):
    def test_file(self):
        img = Path("./example/single_color.jpg")
        out = Path("./example/single_color.png")

        actual = resolve_output_file_path(img, out)
        self.assertEqual(actual, out)
