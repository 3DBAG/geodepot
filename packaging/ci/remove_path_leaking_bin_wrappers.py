from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: remove_path_leaking_bin_wrappers.py <bin-dir> <prefix>", file=sys.stderr)
        return 2

    bin_dir = Path(args[0])
    prefix = args[1].encode()

    if not bin_dir.is_dir():
        return 0

    for path in bin_dir.iterdir():
        if path.is_dir():
            continue
        try:
            if prefix in path.read_bytes():
                path.unlink()
        except OSError:
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
