#!/bin/sh
# Run the complete fixed synthetic suite into a NEW directory.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -n "${GPSMAP_PYTHON:-}" ]; then
    runner_python="$GPSMAP_PYTHON"
elif [ -x .venv/bin/python ]; then
    runner_python="$(pwd)/.venv/bin/python"
elif [ -x ../数据核查/2026-11-01/.venv/bin/python ]; then
    runner_python="$(pwd)/../数据核查/2026-11-01/.venv/bin/python"
else
    runner_python=python3
fi
if [ "$#" -ne 1 ]; then
    echo 'Usage: ./run.sh <new-output-directory>' >&2
    exit 2
fi
case "$1" in
    /*) result_root="$1" ;;
    *) result_root="$(pwd)/$1" ;;
esac
if [ -e "$result_root" ]; then
    echo "Output already exists; preserving it: $result_root" >&2
    exit 2
fi
"$runner_python" -c 'import numpy, shapely, pyproj, pyogrio, matplotlib'
"$runner_python" -m gpsmap generate --output "$result_root/datasets" --fengtai-map data/maps/fengtai_map.json
"$runner_python" -m gpsmap run --datasets "$result_root/datasets" --output "$result_root/results"
