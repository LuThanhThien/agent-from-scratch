from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from agent.tools.read_file import read_file


class ReadFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "repo"
        self.root.mkdir()
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(self.root)

    def test_read_utf8_file(self):
        """Return UTF-8 content and a normalized absolute path."""

        (self.root / "notes").mkdir()
        (self.root / "notes/example.txt").write_text("Hello world", encoding="utf-8")

        result = read_file("notes/../notes/example.txt")
        self.assertEqual(
            result,
            {
                "path": (self.root / "notes/example.txt").as_posix(),
                "content": "Hello world",
                "truncated": False,
            },
        )

    def test_truncation(self):
        """Truncate by character count and detect whether more content exists."""

        (self.root / "text.txt").write_text("hello", encoding="utf-8")
        for limit, content, truncated in (
            (3, "hel", True),
            (5, "hello", False),
        ):
            with self.subTest(limit=limit):
                result = read_file("text.txt", max_chars=limit)
                self.assertEqual(result["content"], content)
                self.assertEqual(result["truncated"], truncated)

    def test_empty_file(self):
        """Treat an empty file as a successful read."""

        (self.root / "empty.txt").touch()
        result = read_file("empty.txt")
        self.assertEqual(result["content"], "")
        self.assertFalse(result["truncated"])

    def test_default_limit(self):
        """Limit returned content to 10,000 characters by default."""

        (self.root / "large.txt").write_text("x" * 10_001, encoding="utf-8")
        result = read_file("large.txt")
        self.assertEqual(len(result["content"]), 10_000)
        self.assertTrue(result["truncated"])

    def test_missing_file(self):
        """Raise an error when the file does not exist."""

        with self.assertRaises(FileNotFoundError):
            read_file("missing.txt")

    def test_invalid_utf8(self):
        """Report undecodable content instead of returning corrupted text."""

        (self.root / "binary.bin").write_bytes(b"\xff\xfe")
        with self.assertRaises(UnicodeDecodeError):
            read_file("binary.bin")

    def test_invalid_input(self):
        """Reject empty paths, invalid limits, and non-string paths."""

        for arguments, error in (
            ({"path": ""}, ValueError),
            ({"path": " "}, ValueError),
            ({"path": "file.txt", "max_chars": 0}, ValueError),
            ({"path": "file.txt", "max_chars": -1}, ValueError),
            ({"path": "file.txt", "max_chars": True}, TypeError),
            ({"path": 123}, TypeError),
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(error):
                    read_file(**arguments)

    def test_directory(self):
        """Reject directories instead of trying to read them as files."""

        with self.assertRaisesRegex(ValueError, "regular file"):
            read_file(".")

    def test_absolute_and_relative_paths(self):
        """Read absolute paths and paths outside the current directory."""

        outside = Path(self.directory.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        self.assertEqual(read_file(str(outside))["content"], "outside")
        self.assertEqual(read_file("../outside.txt")["content"], "outside")

    def test_symlink_outside_repository(self):
        """Resolve symlinks to files outside the current directory."""

        outside = Path(self.directory.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (self.root / "link.txt").symlink_to(outside)
        result = read_file("link.txt")
        self.assertEqual(result["path"], outside.resolve().as_posix())
        self.assertEqual(result["content"], "outside")


class ReadFileRepositoryTests(unittest.TestCase):
    def test_read_repository_file(self):
        """Read a repository file using its absolute path."""
        file_path = Path(__file__).resolve().parents[2] / "agent/tools/read_file.py"
        result = read_file(str(file_path))
        self.assertEqual(result["path"], file_path.as_posix())


if __name__ == "__main__":
    unittest.main()
