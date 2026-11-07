from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def read_file(path: str, max_chars: int = 10_000) -> dict:
    """Read a UTF-8 file relative to the repository, up to max_chars characters."""

    # Validate input
    if not path.strip():
        raise ValueError("path must not be empty")
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")

    # Resolve path
    file_path = Path(path)
    if file_path.is_absolute():
        raise ValueError("path must be relative to the repository")

    file_path = (_ROOT / file_path).resolve()
    if not file_path.is_relative_to(_ROOT):
        raise PermissionError("path must stay within the repository")
    if file_path.exists() and not file_path.is_file():
        raise ValueError("path must refer to a regular file")

    # Read bounded content
    with file_path.open(encoding="utf-8") as file:
        content = file.read(max_chars + 1)

    # File result
    return {
        "path": file_path.relative_to(_ROOT).as_posix(),
        "content": content[:max_chars],
        "truncated": len(content) > max_chars,
    }
