#!/usr/bin/env sh
set -eu

REPO="${GEODEPOT_REPO:-3DBAG/geodepot}"
API_BASE="${GEODEPOT_GITHUB_API:-https://api.github.com}"
DOWNLOAD_BASE="${GEODEPOT_GITHUB_DOWNLOAD:-https://github.com/${REPO}/releases/download}"

VERSION="latest"
INSTALL_ROOT="${GEODEPOT_INSTALL_DIR:-${HOME}/.local/share/geodepot}"
BIN_DIR="${GEODEPOT_BIN_DIR:-${HOME}/.local/bin}"
NO_WRAPPER=0

usage() {
    cat <<'EOF'
Install Geodepot from a GitHub release bundle.

Usage:
  geodepot-install.sh [--version <tag>] [--install-dir <path>] [--bin-dir <path>] [--no-wrapper]

Options:
  --version <tag>      Install a specific release tag instead of the latest release.
  --install-dir <path> Installation root. Default: ~/.local/share/geodepot
  --bin-dir <path>     Wrapper location. Default: ~/.local/bin
  --no-wrapper         Do not install the PATH wrapper script.
  --help               Show this help.
EOF
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1" >&2
        exit 1
    fi
}

log() {
    printf '%s\n' "$*" >&2
}

sha256_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
        return
    fi

    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
        return
    fi

    echo "Could not find sha256sum or shasum for checksum verification." >&2
    exit 1
}

resolve_tag() {
    if [ "$VERSION" != "latest" ]; then
        printf '%s\n' "$VERSION"
        return
    fi

    release_json=$(mktemp)
    if ! curl -fsSL -H "Accept: application/vnd.github+json" "${API_BASE}/repos/${REPO}/releases/latest" -o "$release_json"; then
        rm -f "$release_json"
        exit 1
    fi

    tag_name=$(awk -F'"' '/"tag_name":/ {print $4; exit}' "$release_json")
    rm -f "$release_json"

    if [ -z "$tag_name" ]; then
        echo "Could not resolve the latest release tag from GitHub." >&2
        exit 1
    fi

    printf '%s\n' "$tag_name"
}

resolve_platform() {
    case "$(uname -s)" in
        Linux) printf '%s\n' "linux" ;;
        Darwin) printf '%s\n' "macos" ;;
        *)
            echo "Unsupported operating system: $(uname -s)" >&2
            exit 1
            ;;
    esac
}

resolve_arch() {
    case "$(uname -m)" in
        x86_64|amd64) printf '%s\n' "x86_64" ;;
        arm64|aarch64) printf '%s\n' "arm64" ;;
        *)
            echo "Unsupported architecture: $(uname -m)" >&2
            exit 1
            ;;
    esac
}

asset_candidates() {
    platform="$1"
    arch="$2"

    case "${platform}:${arch}" in
        linux:x86_64)
            printf '%s\n' "geodepot-linux-x86_64.zip" "geodepot-ubuntu-x86_64.zip" "geodepot-ubuntu.zip"
            ;;
        linux:arm64)
            printf '%s\n' "geodepot-linux-arm64.zip"
            ;;
        macos:x86_64)
            printf '%s\n' "geodepot-macos-x86_64.zip" "geodepot-macos.zip"
            ;;
        macos:arm64)
            printf '%s\n' "geodepot-macos-arm64.zip" "geodepot-macos.zip"
            ;;
        *)
            return 1
            ;;
    esac
}

asset_exists() {
    curl -fsIL "$1" >/dev/null 2>&1
}

resolve_asset() {
    tag="$1"
    platform="$2"
    arch="$3"

    for asset in $(asset_candidates "$platform" "$arch"); do
        if asset_exists "${DOWNLOAD_BASE}/${tag}/${asset}"; then
            printf '%s\n' "$asset"
            return 0
        fi
    done

    echo "Could not find a release bundle for ${platform}/${arch} at tag ${tag}." >&2
    exit 1
}

while [ $# -gt 0 ]; do
    case "$1" in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --install-dir)
            INSTALL_ROOT="$2"
            shift 2
            ;;
        --bin-dir)
            BIN_DIR="$2"
            shift 2
            ;;
        --no-wrapper)
            NO_WRAPPER=1
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

require_cmd curl
require_cmd unzip

log "Starting Geodepot installation."
log "Detecting platform and release bundle."
platform=$(resolve_platform)
arch=$(resolve_arch)

if [ "$VERSION" = "latest" ]; then
    log "Resolving latest release tag from GitHub."
else
    log "Installing requested version: ${VERSION}."
fi

tag=$(resolve_tag)
asset=$(resolve_asset "$tag" "$platform" "$arch")
checksum_asset="${asset}.sha256sum"

log "Using release ${tag} for ${platform}/${arch}."
log "Selected bundle ${asset}."

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT HUP INT TERM

archive_path="${tmpdir}/${asset}"
checksum_path="${tmpdir}/${checksum_asset}"

log "Downloading bundle and checksum."
curl -fsSL -o "$archive_path" "${DOWNLOAD_BASE}/${tag}/${asset}"
curl -fsSL -o "$checksum_path" "${DOWNLOAD_BASE}/${tag}/${checksum_asset}"

log "Verifying checksum."
expected_hash=$(awk '{print $1}' "$checksum_path")
actual_hash=$(sha256_file "$archive_path")

if [ "$expected_hash" != "$actual_hash" ]; then
    echo "Checksum verification failed for ${asset}." >&2
    exit 1
fi

release_dir="${INSTALL_ROOT}/releases/${tag}"
bundle_dir="${release_dir}/geodepot"
current_dir="${INSTALL_ROOT}/current"

log "Installing into ${bundle_dir}."
mkdir -p "${INSTALL_ROOT}/releases"
rm -rf "$release_dir"
mkdir -p "$release_dir"
log "Extracting bundle."
unzip -q "$archive_path" -d "$release_dir"

if [ ! -f "${bundle_dir}/geodepot" ]; then
    echo "Unexpected bundle layout in ${asset}." >&2
    exit 1
fi

log "Updating current symlink."
rm -rf "$current_dir"
ln -s "$bundle_dir" "$current_dir"

if [ "$NO_WRAPPER" -eq 0 ]; then
    log "Installing wrapper in ${BIN_DIR}."
    mkdir -p "$BIN_DIR"
    cat > "${BIN_DIR}/geodepot" <<EOF
#!/usr/bin/env sh
exec "${current_dir}/geodepot" "\$@"
EOF
    chmod 755 "${BIN_DIR}/geodepot"
fi

echo "Installed Geodepot ${tag} to ${bundle_dir}"

if [ "$NO_WRAPPER" -eq 0 ]; then
    echo "Installed launcher wrapper to ${BIN_DIR}/geodepot"
    case ":${PATH}:" in
        *:"${BIN_DIR}":*)
            ;;
        *)
            echo "Add ${BIN_DIR} to PATH to run 'geodepot' from any shell."
            ;;
    esac
else
    echo "Run ${bundle_dir}/geodepot to start Geodepot."
fi
