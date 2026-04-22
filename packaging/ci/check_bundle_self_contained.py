#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import os
import platform
import subprocess
from pathlib import Path


LINUX_SYSTEM_PREFIXES = ("/lib/", "/lib64/", "/usr/lib/", "/usr/lib64/")
MAC_SYSTEM_PREFIXES = ("/System/Library/", "/usr/lib/")
WINDOWS_SYSTEM_DLLS = {
    "advapi32.dll",
    "bcrypt.dll",
    "comdlg32.dll",
    "crypt32.dll",
    "gdi32.dll",
    "kernel32.dll",
    "mscoree.dll",
    "msvcp140.dll",
    "msvcrt.dll",
    "ntdll.dll",
    "ole32.dll",
    "oleaut32.dll",
    "rpcrt4.dll",
    "shell32.dll",
    "shlwapi.dll",
    "ucrtbase.dll",
    "user32.dll",
    "version.dll",
    "winmm.dll",
    "ws2_32.dll",
}
WINDOWS_SYSTEM_PATTERNS = (
    "api-ms-win-*.dll",
    "ext-ms-*.dll",
)
ELF_MAGIC = b"\x7fELF"
MACHO_MAGICS = {
    0xFEEDFACE,
    0xCEFAEDFE,
    0xFEEDFACF,
    0xCFFAEDFE,
    0xCAFEBABE,
    0xBEBAFECA,
}
PE_MAGIC = b"MZ"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that a Geodepot bundle only references bundled or system dependencies."
    )
    parser.add_argument("bundle", type=Path, help="Path to the extracted bundle root.")
    parser.add_argument(
        "--forbid-prefix",
        action="append",
        default=[],
        help="Additional string prefix to reject anywhere inside the bundle.",
    )
    return parser.parse_args()


def iter_regular_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and not path.is_symlink()]


def read_prefixes(args: argparse.Namespace) -> list[bytes]:
    prefixes = [prefix for prefix in args.forbid_prefix if prefix]
    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        prefixes.append(workspace)
    return [prefix.encode("utf-8") for prefix in prefixes if prefix]


def scan_forbidden_strings(files: list[Path], prefixes: list[bytes]) -> None:
    if not prefixes:
        return
    longest = max(len(prefix) for prefix in prefixes)
    for path in files:
        tail = b""
        try:
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    buffer = tail + chunk
                    for prefix in prefixes:
                        if prefix in buffer:
                            raise RuntimeError(
                                f"Bundle file {path} contains forbidden build prefix {prefix.decode('utf-8', 'ignore')!r}."
                            )
                    tail = buffer[-(longest - 1) :] if longest > 1 else b""
        except OSError as exc:
            raise RuntimeError(f"Failed to read {path}") from exc


def read_magic(path: Path, size: int = 4) -> bytes:
    with path.open("rb") as handle:
        return handle.read(size)


def is_elf(path: Path) -> bool:
    try:
        return read_magic(path, 4) == ELF_MAGIC
    except OSError:
        return False


def is_macho(path: Path) -> bool:
    try:
        magic = int.from_bytes(read_magic(path, 4), byteorder="big", signed=False)
    except OSError:
        return False
    return magic in MACHO_MAGICS


def is_pe(path: Path) -> bool:
    try:
        return read_magic(path, 2) == PE_MAGIC
    except OSError:
        return False


def basename(path: str) -> str:
    return Path(path).name.lower()


def bundle_library_dirs(bundle_root: Path) -> list[str]:
    candidates = (
        bundle_root / "env" / "lib",
        bundle_root / "env" / "lib64",
        bundle_root / "lib",
        bundle_root / "lib64",
        bundle_root / "_internal",
    )
    return [str(path) for path in candidates if path.is_dir()]


def audit_linux(files: list[Path], bundle_root: Path, bundle_names: set[str]) -> None:
    clean_env = os.environ.copy()
    library_dirs = bundle_library_dirs(bundle_root)
    if library_dirs:
        clean_env["LD_LIBRARY_PATH"] = ":".join(
            library_dirs + ([clean_env["LD_LIBRARY_PATH"]] if clean_env.get("LD_LIBRARY_PATH") else [])
        )
    for path in files:
        if not is_elf(path):
            continue
        result = subprocess.run(
            ["ldd", str(path)],
            capture_output=True,
            text=True,
            check=False,
            env=clean_env,
        )
        output = "\n".join(filter(None, [result.stdout, result.stderr]))
        if "not found" in output:
            raise RuntimeError(f"Bundle file {path} has unresolved shared libraries:\n{output}")
        for line in output.splitlines():
            if "=>" not in line:
                continue
            dep_name, resolved = [part.strip() for part in line.split("=>", 1)]
            if not dep_name:
                continue
            resolved_path = resolved.split("(", 1)[0].strip()
            if not resolved_path or resolved_path == "not found":
                raise RuntimeError(f"Bundle file {path} has unresolved dependency {dep_name}.")
            if resolved_path.startswith(tuple(LINUX_SYSTEM_PREFIXES)):
                if basename(dep_name) in bundle_names:
                    raise RuntimeError(
                        f"Bundle file {path} resolves bundled dependency {dep_name} to system path {resolved_path}."
                    )
                continue
            if not Path(resolved_path).is_relative_to(bundle_root):
                raise RuntimeError(
                    f"Bundle file {path} resolves dependency {dep_name} outside the bundle: {resolved_path}"
                )


def audit_macos(files: list[Path], bundle_root: Path, bundle_names: set[str]) -> None:
    for path in files:
        if not is_macho(path):
            continue
        result = subprocess.run(
            ["otool", "-L", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        output = "\n".join(filter(None, [result.stdout, result.stderr]))
        for line in output.splitlines()[1:]:
            dep_path = line.strip().split(" (", 1)[0].strip()
            if not dep_path:
                continue
            if dep_path.startswith("@"):
                continue
            if dep_path.startswith(MAC_SYSTEM_PREFIXES):
                continue
            if Path(dep_path).is_relative_to(bundle_root):
                continue
            if basename(dep_path) in bundle_names:
                raise RuntimeError(
                    f"Bundle file {path} resolves bundled dependency {dep_path} outside the bundle."
                )
            raise RuntimeError(
                f"Bundle file {path} resolves dependency outside the bundle: {dep_path}"
            )


def _read_u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little")


def _read_u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def _read_u64(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], "little")


def rva_to_offset(rva: int, sections: list[dict[str, int]]) -> int:
    for section in sections:
        start = section["virtual_address"]
        size = max(section["virtual_size"], section["raw_size"])
        if start <= rva < start + size:
            return section["raw_pointer"] + (rva - start)
    raise RuntimeError(f"Could not map RVA 0x{rva:x} to a file offset.")


def parse_pe_imports(path: Path) -> list[str]:
    data = path.read_bytes()
    if data[:2] != PE_MAGIC:
        return []
    e_lfanew = _read_u32(data, 0x3C)
    if data[e_lfanew : e_lfanew + 4] != b"PE\0\0":
        raise RuntimeError(f"{path} is not a valid PE file.")
    coff_offset = e_lfanew + 4
    number_of_sections = _read_u16(data, coff_offset + 2)
    size_of_optional_header = _read_u16(data, coff_offset + 16)
    optional_offset = coff_offset + 20
    magic = _read_u16(data, optional_offset)
    if magic == 0x10B:
        data_directory_offset = optional_offset + 96
    elif magic == 0x20B:
        data_directory_offset = optional_offset + 112
    else:
        raise RuntimeError(f"{path} has an unsupported PE optional header magic 0x{magic:x}.")
    import_rva = _read_u32(data, data_directory_offset + 8)
    if import_rva == 0:
        return []

    section_offset = optional_offset + size_of_optional_header
    sections: list[dict[str, int]] = []
    for index in range(number_of_sections):
        offset = section_offset + (index * 40)
        sections.append(
            {
                "virtual_size": _read_u32(data, offset + 8),
                "virtual_address": _read_u32(data, offset + 12),
                "raw_size": _read_u32(data, offset + 16),
                "raw_pointer": _read_u32(data, offset + 20),
            }
        )

    imports: list[str] = []
    descriptor_offset = rva_to_offset(import_rva, sections)
    while True:
        original_first_thunk = _read_u32(data, descriptor_offset)
        name_rva = _read_u32(data, descriptor_offset + 12)
        first_thunk = _read_u32(data, descriptor_offset + 16)
        if original_first_thunk == 0 and name_rva == 0 and first_thunk == 0:
            break
        name_offset = rva_to_offset(name_rva, sections)
        end = data.index(b"\0", name_offset)
        imports.append(data[name_offset:end].decode("ascii", "replace"))
        descriptor_offset += 20
    return imports


def audit_windows(files: list[Path], bundle_names: set[str]) -> None:
    for path in files:
        if path.suffix.lower() not in {".exe", ".dll", ".pyd"} and not is_pe(path):
            continue
        imports = parse_pe_imports(path)
        for dep in imports:
            dep_lower = dep.lower()
            if dep_lower in bundle_names:
                continue
            if dep_lower in WINDOWS_SYSTEM_DLLS:
                continue
            if any(fnmatch.fnmatch(dep_lower, pattern) for pattern in WINDOWS_SYSTEM_PATTERNS):
                continue
            raise RuntimeError(f"Bundle file {path} depends on missing DLL {dep}.")


def main() -> int:
    args = parse_args()
    bundle_root = args.bundle.resolve()
    if not bundle_root.is_dir():
        raise SystemExit(f"Bundle root {bundle_root} does not exist or is not a directory.")

    files = iter_regular_files(bundle_root)
    bundle_names = {path.name.lower() for path in files}
    prefixes = read_prefixes(args)
    scan_forbidden_strings(files, prefixes)

    system = platform.system()
    if system == "Linux":
        audit_linux(files, bundle_root, bundle_names)
    elif system == "Darwin":
        audit_macos(files, bundle_root, bundle_names)
    elif system == "Windows":
        audit_windows(files, bundle_names)
    else:
        raise SystemExit(f"Unsupported platform for bundle audit: {system}")

    print(f"Bundle {bundle_root} passed the dependency audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
