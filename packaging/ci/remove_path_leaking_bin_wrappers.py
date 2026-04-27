from __future__ import annotations

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
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(
            "usage: remove_path_leaking_bin_wrappers.py <bundle-root> <prefix>",
            file=sys.stderr,
        )
        return 2

    bundle_root = Path(args[0])
    prefix = args[1].encode()

    if not bundle_root.is_dir():
        return 0

    for path in bundle_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue

        # ONLY check files we know are text or match our allowlist
        # Do NOT unlink .so, .pyd, or .dll files!
        name = path.name.lower()
        is_text = name in TEXT_BASENAMES or path.suffix.lower() in TEXT_SUFFIXES

        if not is_text:
            continue  # Skip binary auditing to avoid deleting shared libs

        try:
            if prefix in path.read_bytes():
                path.unlink()
                print(f"Removed path-leaking wrapper: {path}")
        except OSError:
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
