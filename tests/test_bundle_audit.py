from __future__ import annotations

import runpy
from pathlib import Path

import pytest


MODULE = runpy.run_path(
    Path(__file__).resolve().parents[1]
    / "packaging"
    / "ci"
    / "check_bundle_self_contained.py"
)


def test_windows_system_dll_path_detects_system32_dependency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    windows_root = tmp_path / "Windows"
    system32 = windows_root / "System32"
    system32.mkdir(parents=True)
    dll_path = system32 / "psapi.dll"
    dll_path.write_bytes(b"")
    monkeypatch.setenv("WINDIR", str(windows_root))

    resolved = MODULE["windows_system_dll_path"]("psapi.dll")

    assert resolved == dll_path


def test_audit_windows_accepts_system_dependency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    windows_root = tmp_path / "Windows"
    system32 = windows_root / "System32"
    system32.mkdir(parents=True)
    (system32 / "psapi.dll").write_bytes(b"")
    (system32 / "kernel32.dll").write_bytes(b"")
    monkeypatch.setenv("WINDIR", str(windows_root))

    bundle_file = tmp_path / "libomp.dll"
    bundle_file.write_bytes(b"MZ")

    audit_windows = MODULE["audit_windows"]
    monkeypatch.setitem(audit_windows.__globals__, "is_pe", lambda path: True)
    monkeypatch.setitem(
        audit_windows.__globals__,
        "parse_pe_imports",
        lambda path: ["PSAPI.DLL", "KERNEL32.DLL"],
    )

    audit_windows([bundle_file], set())
