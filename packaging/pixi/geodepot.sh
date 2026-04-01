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

if [ -d "${ACTIVATE_DIR}" ]; then
    for hook in "${ACTIVATE_DIR}"/*.sh; do
        if [ -f "${hook}" ]; then
            . "${hook}"
        fi
    done
fi

exec "${CONDA_PREFIX}/bin/geodepot" "$@"
