from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from agent.tools._base import execute_tool
from agent.tools.read_file import read_file


class ReadFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "repo"
        self.root.mkdir()
        self.patch = patch("agent.tools.read_file._ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_read_utf8_file(self):
        """Return UTF-8 content and a normalized repository-relative path."""

        (self.root / "notes").mkdir()
        (self.root / "notes/example.txt").write_text("Hello world", encoding="utf-8")

        result = execute_tool(read_file, {"path": "notes/../notes/example.txt"})
        self.assertEqual(
            result,
            {
                "ok": True,
                "data": {
                    "path": "notes/example.txt",
                    "content": "Hello world",
                    "truncated": False,
                },
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
        result = execute_tool(read_file, {"path": "empty.txt"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["content"], "")
        self.assertFalse(result["data"]["truncated"])

    def test_default_limit(self):
        """Limit returned content to 10,000 characters by default."""

        (self.root / "large.txt").write_text("x" * 10_001, encoding="utf-8")
        result = read_file("large.txt")
        self.assertEqual(len(result["content"]), 10_000)
        self.assertTrue(result["truncated"])

    def test_missing_file(self):
        """Report missing files through the shared error wrapper."""

        result = execute_tool(read_file, {"path": "missing.txt"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["type"], "FileNotFoundError")

    def test_invalid_utf8(self):
        """Report undecodable content instead of returning corrupted text."""

        (self.root / "binary.bin").write_bytes(b"\xff\xfe")
        result = execute_tool(read_file, {"path": "binary.bin"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["type"], "UnicodeDecodeError")

    def test_invalid_input(self):
        """Reject empty paths, invalid limits, and non-string paths."""

        for arguments in (
            {"path": ""},
            {"path": " "},
            {"path": "file.txt", "max_chars": 0},
            {"path": "file.txt", "max_chars": -1},
            {"path": "file.txt", "max_chars": True},
            {"path": 123},
        ):
            with self.subTest(arguments=arguments):
                self.assertFalse(execute_tool(read_file, arguments)["ok"])

    def test_directory(self):
        """Reject directories instead of trying to read them as files."""

        with self.assertRaisesRegex(ValueError, "regular file"):
            read_file(".")

    def test_paths_outside_repository(self):
        """Reject absolute paths and traversal outside the repository."""

        outside = Path(self.directory.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_file(str(outside))
        with self.assertRaises(PermissionError):
            read_file("../outside.txt")

    def test_symlink_outside_repository(self):
        """Resolve symlinks before enforcing the repository boundary."""

        outside = Path(self.directory.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (self.root / "link.txt").symlink_to(outside)
        with self.assertRaises(PermissionError):
            read_file("link.txt")


if __name__ == "__main__":
    unittest.main()
