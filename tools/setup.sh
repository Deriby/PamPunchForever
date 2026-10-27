#!/usr/bin/env bash
set -euo pipefail
# Run from any directory; retained assets require no Blender or Python packages.
PAM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PAM_TOOLS="${PAM_TOOLS_DIR:-/workspace/tools}/godot-4.4.1"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/workspace/.runtime/data}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/workspace/.runtime/config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/workspace/.runtime/cache}"
mkdir -p "$PAM_TOOLS" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
PAM_BASE=https://github.com/godotengine/godot-builds/releases/download/4.4.1-stable
PAM_ARCHIVE=Godot_v4.4.1-stable_linux.x86_64.zip
if [ ! -f "$PAM_TOOLS/$PAM_ARCHIVE" ]; then
 curl -fL --retry 2 "$PAM_BASE/$PAM_ARCHIVE" -o "$PAM_TOOLS/$PAM_ARCHIVE"
fi
if [ ! -f "$PAM_TOOLS/SHA512-SUMS.txt" ]; then
 curl -fL --retry 2 "$PAM_BASE/SHA512-SUMS.txt" -o "$PAM_TOOLS/SHA512-SUMS.txt"
fi
(cd "$PAM_TOOLS" && awk '$2 == "Godot_v4.4.1-stable_linux.x86_64.zip"' SHA512-SUMS.txt | sha512sum -c -)
unzip -oq "$PAM_TOOLS/$PAM_ARCHIVE" -d "$PAM_TOOLS"
chmod +x "$PAM_TOOLS/Godot_v4.4.1-stable_linux.x86_64"
"$PAM_TOOLS/Godot_v4.4.1-stable_linux.x86_64" --headless --path "$PAM_ROOT" --editor --import
"$PAM_TOOLS/Godot_v4.4.1-stable_linux.x86_64" --headless --fixed-fps 120 --path "$PAM_ROOT" --script tests/integration.gd
