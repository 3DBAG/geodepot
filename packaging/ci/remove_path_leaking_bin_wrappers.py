#!/usr/bin/env python3
"""
Remove bin wrapper scripts that contain references to build-time paths.

This script ensures that binary wrapper scripts in the bundled environment
don't contain absolute paths that would make the bundle non-portable.

This is critical for creating self-contained bundles that can be moved to
different locations and still work correctly.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".bat",
    ".cmd",
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".ps1",
    ".rst",
    ".sh",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

TEXT_BASENAMES = {
    "geodepot",
}


def main(argv: list[str] | None = None) -> int:
    """
    Remove wrapper scripts that contain build-path references.

    Args:
        argv: Command line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 = success, 2 = usage error, 1 = other error)
    """
    args = sys.argv[1:] if argv is None else argv

    if len(args) != 2:
        print(
            "usage: remove_path_leaking_bin_wrappers.py <bundle-root> <prefix>",
            file=sys.stderr,
        )
        print(
            "  <bundle-root>  Path to the bundled environment root",
            file=sys.stderr,
        )
        print(
            "  <prefix>      Build prefix to search for and remove",
            file=sys.stderr,
        )
        return 2

    bundle_root = Path(args[0])
    prefix = args[1].encode()

    if not bundle_root.is_dir():
        print(f"Error: Bundle root is not a directory: {bundle_root}", file=sys.stderr)
        return 1

    # ========================================================================
    # Normalize the prefix for cross-platform matching
    # ========================================================================
    # On Windows, we need to check both forward slashes and backslashes
    # because the build prefix might be in either format, and the files might
    # use either format.
    if platform.system() == "Windows":
        # Convert forward slashes to backslashes
        windows_prefix = prefix.replace(b"/", b"\\")
        # Also keep the original in case it's already in backslash format
        prefixes_to_check = [prefix, windows_prefix]
        # Also add both directions in case the file has mixed separators
        if prefix != windows_prefix:
            prefixes_to_check.append(prefix.replace(b"\\", b"/"))
            prefixes_to_check.append(windows_prefix.replace(b"/", b"\\"))
    else:
        prefixes_to_check = [prefix]

    removed_count = 0

    # ========================================================================
    # Scan all files in the bundle
    # ========================================================================
    for path in bundle_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue

        # Only check text files (skip binaries, shared libraries, etc.)
        name = path.name.lower()
        is_text = name in TEXT_BASENAMES or path.suffix.lower() in TEXT_SUFFIXES

        if not is_text:
            continue

        try:
            content = path.read_bytes()

            # Check if any of the prefixes are in the file
            for check_prefix in prefixes_to_check:
                if check_prefix in content:
                    path.unlink()
                    print(f"Removed path-leaking wrapper: {path}")
                    removed_count += 1
                    break

        except OSError as e:
            # File might be locked or unreadable - just skip it
            print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            continue

    print(f"Total path-leaking wrappers removed: {removed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
