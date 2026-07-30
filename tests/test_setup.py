import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch


def _load_setup_module(setup_path="setup.py"):
    """Load setup.py while suppressing setuptools and I/O side effects."""
    spec = importlib.util.spec_from_file_location(
        "setup_under_test",
        os.path.abspath(setup_path),
    )
    module = importlib.util.module_from_spec(spec)
    mock_setuptools = MagicMock()
    mock_setuptools.Command = MagicMock()
    mock_setuptools.find_packages = list
    mock_setuptools.setup = lambda **kwargs: None
    sys.modules["setuptools"] = mock_setuptools

    with patch("builtins.print"):
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = ""
            with patch("os.listdir", return_value=[]):
                spec.loader.exec_module(module)

    return module


class TestGetAllFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.setup = _load_setup_module()
        self.setup._ROOT = self.tmp

    def test_recursively_lists_relative_paths(self):
        os.makedirs(os.path.join(self.tmp, "a", "b"))
        with open(os.path.join(self.tmp, "a", "b", "file.txt"), "w") as f:
            f.write("x")
        with open(os.path.join(self.tmp, "root.txt"), "w") as f:
            f.write("y")

        result = sorted(self.setup.get_all_files(self.tmp))
        self.assertEqual(result, ["a/b/file.txt", "root.txt"])

    def test_empty_directory_returns_empty_list(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        self.assertEqual(self.setup.get_all_files(empty), [])

    def test_nonexistent_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.setup.get_all_files(os.path.join(self.tmp, "nope"))


class TestRead(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.setup = _load_setup_module()

    def test_returns_file_content(self):
        fpath = os.path.join(self.tmp, "readme.md")
        with open(fpath, "w") as f:
            f.write("description")
        self.assertEqual(self.setup.read(fpath), "description")

    def test_raises_on_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            self.setup.read(os.path.join(self.tmp, "missing.md"))


if __name__ == "__main__":
    unittest.main()
