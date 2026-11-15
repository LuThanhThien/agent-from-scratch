from pathlib import Path


def list_files(path: str = ".", max_files: int = 100) -> dict:
    """List files directly inside a directory.

    Args:
        path: Path to the directory.
        max_files: Maximum number of files to return.

    Returns:
        A dictionary containing the directory path, file names, and whether
        the list was truncated.
    """

    # Validate input
    if not path.strip():
        raise ValueError("path must not be empty")
    if max_files <= 0:
        raise ValueError("max_files must be greater than zero")

    # List files
    directory = Path(path).resolve()
    files = sorted(entry.name for entry in directory.iterdir() if entry.is_file())

    return {
        "path": directory.as_posix(),
        "files": files[:max_files],
        "truncated": len(files) > max_files,
    }
