import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_init_does_not_require_osgeo(tmp_path):
    """`geodepot init` should still work when osgeo cannot be imported."""
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    code = textwrap.dedent(
        """
        import importlib.abc
        import sys


        class BlockOsgeo(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path, target=None):
                if fullname == "osgeo" or fullname.startswith("osgeo."):
                    raise ModuleNotFoundError("blocked osgeo import for test")
                return None


        sys.meta_path.insert(0, BlockOsgeo())

        from click.testing import CliRunner
        from geodepot.cli import geodepot_grp

        result = CliRunner().invoke(geodepot_grp, ["init"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / ".geodepot").exists()
