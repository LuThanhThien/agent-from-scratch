from pathlib import Path


def read_file(path: str, max_chars: int = 10_000) -> dict:
    """Read a UTF-8 file.

    Args:
        path: Path to the file.
        max_chars: Maximum number of characters to read from the file.

    Returns:
        A dictionary containing the path, the file content,
        and whether the content was truncated.
    """

    # Validate input
    if type(path) is not str:
        raise TypeError("path must be str")
    if type(max_chars) is not int:
        raise TypeError("max_chars must be int")
    if not path.strip():
        raise ValueError("path must not be empty")
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")

    # Resolve path
    file_path = Path(path).resolve().absolute()

    if file_path.exists() and not file_path.is_file():
        raise ValueError("path must refer to a regular file")

    # Read bounded content
    with file_path.open(encoding="utf-8") as file:
        content = file.read(max_chars + 1)

    # File result
    return {
        "path": file_path.as_posix(),
        "content": content[:max_chars],
        "truncated": len(content) > max_chars,
    }
