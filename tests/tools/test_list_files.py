from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agent.tools import list_files


class ListFilesTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_list_files(self):
        """Return sorted file names without including directories."""
        (self.root / "b.txt").touch()
        (self.root / "a.txt").touch()
        (self.root / "folder").mkdir()

        self.assertEqual(
            list_files(str(self.root)),
            {
                "path": self.root.resolve().as_posix(),
                "files": ["a.txt", "b.txt"],
                "truncated": False,
            },
        )

    def test_limit(self):
        """Limit the file list and indicate when entries are omitted."""
        (self.root / "a.txt").touch()
        (self.root / "b.txt").touch()

        result = list_files(str(self.root), max_files=1)
        self.assertEqual(result["files"], ["a.txt"])
        self.assertTrue(result["truncated"])

        self.assertFalse(list_files(str(self.root), max_files=2)["truncated"])

    def test_empty_directory(self):
        """Return an empty list for a directory without files."""
        result = list_files(str(self.root))
        self.assertEqual(result["files"], [])
        self.assertFalse(result["truncated"])

    def test_invalid_input(self):
        """Reject invalid paths and limits."""
        with self.assertRaises(ValueError):
            list_files("")
        with self.assertRaises(ValueError):
            list_files(str(self.root), max_files=0)
        with self.assertRaises(FileNotFoundError):
            list_files(str(self.root / "missing"))


if __name__ == "__main__":
    unittest.main()
