# pylint: skip-file
import unittest
from pathlib import Path

from src.main import get_img_inputs_from_user_inputs
from src.cliparser import parse


class TestIterateImgInputs(unittest.TestCase):
    def test_single_wild_input(self):
        input_pattern = "example/*.png"
        args = ["-i", input_pattern, "-o", "example/${stem}.ico"]
        namespace = parse(args)
        img_inputs = namespace.inputs

        expected = set(Path.cwd().glob(input_pattern))
        actual = set(get_img_inputs_from_user_inputs(img_inputs))

        self.assertEqual(actual, expected)
