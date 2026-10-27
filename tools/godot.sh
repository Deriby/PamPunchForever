#!/usr/bin/env bash
set -euo pipefail
PAM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/workspace/.runtime/data}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/workspace/.runtime/config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/workspace/.runtime/cache}"
mkdir -p "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
exec "${PAM_GODOT:-/workspace/tools/godot-4.4.1/Godot_v4.4.1-stable_linux.x86_64}" --path "$PAM_ROOT" "$@"
