#!/usr/bin/env bash
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CONDA_PREFIX="${SCRIPT_DIR}/env"
ACTIVATE_DIR="${CONDA_PREFIX}/etc/conda/activate.d"

: "${PDAL_DRIVER_PATH:=}"
: "${_CONDA_SET_PDAL_PYTHON_DRIVER_PATH:=}"

export CONDA_PREFIX
export CONDA_SHLVL=1
export PATH="${CONDA_PREFIX}/bin:${PATH}"

case "$(uname -s)" in
    Darwin)
        export DYLD_LIBRARY_PATH="${CONDA_PREFIX}/lib${DYLD_LIBRARY_PATH:+:${DYLD_LIBRARY_PATH}}"
        export DYLD_FALLBACK_LIBRARY_PATH="${CONDA_PREFIX}/lib${DYLD_FALLBACK_LIBRARY_PATH:+:${DYLD_FALLBACK_LIBRARY_PATH}}"
        ;;
    *)
        export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
        ;;
esac

if [ -d "${ACTIVATE_DIR}" ]; then
    for hook in "${ACTIVATE_DIR}"/*.sh; do
        if [ -f "${hook}" ]; then
            . "${hook}"
        fi
    done
fi

exec "${CONDA_PREFIX}/bin/python" -m geodepot "$@"
