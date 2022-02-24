
from pathlib import Path
import unittest

from dist.main import resolve_output_file_path


class TestResolvePath(unittest.TestCase):
    def test_case_normal_image(self):
        img = Path("./example/single_color.jpg")
        out = "./example/single_color.png"
        expected = Path("./example/single_color.png")

        actual = resolve_output_file_path(img, out)
        self.assertEqual(actual, expected)

    def test_case_stem(self):
        img = Path("./example/single_color.jpg")
        out = "./example/${stem}.png"

        expected = Path("./example/single_color.png")

        actual = resolve_output_file_path(img, out)
        self.assertEqual(actual, expected)

    def test_case_dir(self):
        img = Path("./example/single_color.jpg")
        out = "${dir}/single_color.png"

        expected = Path("./example/single_color.png")

        actual = resolve_output_file_path(img, out)
        self.assertEqual(actual, expected)

    def test_case_dir_and_stem(self):
        img = Path("./example/single_color.jpg")
        out = "${dir}/${stem}.png"

        expected = Path("./example/single_color.png")

        actual = resolve_output_file_path(img, out)
        self.assertEqual(actual, expected)
