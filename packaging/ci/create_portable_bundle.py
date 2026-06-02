#!/usr/bin/env python3
"""
Create a self-contained portable bundle from a pixi environment.

This script copies a pixi environment to a portable location and cleans up
any path references that would make it non-portable. The resulting bundle
can be distributed and run on any system without requiring pixi, conda,
or any other external tools to be installed.

Usage:
    python packaging/ci/create_portable_bundle.py <src_env> <dest_dir> [--build-prefix PREFIX]

Example:
    python packaging/ci/create_portable_bundle.py .pixi/envs/default dist/geodepot
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def get_pixi_environment_path(environment_name: str = "default") -> Path | None:
    """
    Get the path to a pixi environment using pixi info command.

    Args:
        environment_name: Name of the pixi environment (default: "default")

    Returns:
        Path to the environment, or None if not found
    """
    try:
        result = subprocess.run(
            ["pixi", "info", f"--environment={environment_name}", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        import json

        data = json.loads(result.stdout)
        for env in data.get("environments_info", []):
            if env.get("name") == environment_name:
                prefix = env.get("prefix")
                if prefix:
                    return Path(prefix)
        return None
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        FileNotFoundError,
    ) as e:
        print(f"Warning: Could not get pixi environment path: {e}", file=sys.stderr)
        return None


def create_portable_bundle(
    src_env: Path | str | None,
    dest: Path | str,
    build_prefix: str = "",
    clean_activation_scripts: bool = True,
    remove_path_leaking: bool = True,
) -> int:
    """
    Create a portable bundle by copying environment and cleaning up paths.

    Args:
        src_env: Source pixi environment path (if None, will try to get from pixi)
        dest: Destination bundle directory
        build_prefix: Build prefix to remove from scripts (for path leaking cleanup)
        clean_activation_scripts: Whether to remove conda activation scripts
        remove_path_leaking: Whether to remove path-leaking bin wrappers

    Returns:
        Exit code (0 = success, 1 = error)
    """
    src_env = Path(src_env) if src_env else None
    dest = Path(dest)

    # If src_env is not provided, try to get it from pixi
    if src_env is None or not src_env.exists():
        src_env = get_pixi_environment_path("default")
        if src_env is None:
            print("Error: Could not determine source environment path", file=sys.stderr)
            print(
                "Please provide --src-env or ensure pixi is available", file=sys.stderr
            )
            return 1

    # Create destination directory
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(
            f"Error: Could not create destination directory {dest}: {e}",
            file=sys.stderr,
        )
        return 1

    dest_env = dest / "env"

    # Copy the environment
    print(f"Copying environment from {src_env} to {dest_env}")
    try:
        if dest_env.exists():
            shutil.rmtree(dest_env)
        shutil.copytree(src_env, dest_env)
    except OSError as e:
        print(f"Error: Could not copy environment: {e}", file=sys.stderr)
        return 1

    # Clean up conda activation scripts that may contain build-path references
    if clean_activation_scripts:
        print("Cleaning up conda activation scripts...")
        for pattern in ["etc/conda/activate.d", "etc/conda/deactivate.d"]:
            for path in dest_env.glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"  Removed: {path.relative_to(dest_env)}")

    # Remove path-leaking bin wrappers
    if remove_path_leaking and build_prefix:
        print("Removing path-leaking bin wrappers...")
        from packaging.ci.remove_path_leaking_bin_wrappers import (
            main as remove_path_leaking_main,
        )

        # Call the cleanup script
        old_argv = sys.argv
        try:
            sys.argv = [
                "remove_path_leaking_bin_wrappers.py",
                str(dest_env),
                build_prefix,
            ]
            result = remove_path_leaking_main()
            if result != 0:
                print(
                    f"Warning: remove_path_leaking_bin_wrappers.py returned {result}",
                    file=sys.stderr,
                )
        finally:
            sys.argv = old_argv

    print(f"Portable bundle created at {dest}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a self-contained portable bundle from a pixi environment"
    )
    parser.add_argument(
        "dest",
        type=Path,
        help="Destination bundle directory",
    )
    parser.add_argument(
        "--src-env",
        type=Path,
        default=None,
        help="Source pixi environment path (default: auto-detect from pixi)",
    )
    parser.add_argument(
        "--build-prefix",
        default="",
        help="Build prefix to remove from scripts",
    )
    parser.add_argument(
        "--no-clean-activation",
        action="store_false",
        dest="clean_activation",
        help="Do not remove conda activation scripts",
    )
    parser.add_argument(
        "--no-remove-path-leaking",
        action="store_false",
        dest="remove_path_leaking",
        help="Do not remove path-leaking bin wrappers",
    )
    args = parser.parse_args()

    return create_portable_bundle(
        src_env=args.src_env,
        dest=args.dest,
        build_prefix=args.build_prefix,
        clean_activation_scripts=args.clean_activation,
        remove_path_leaking=args.remove_path_leaking,
    )


if __name__ == "__main__":
    sys.exit(main())
