#!/usr/bin/env bash
set -euo pipefail
PAM_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# Optional visual review in a cloud task; Xorg with dummy_drv is already installed.
# Use the current display if supplied; otherwise create a dedicated temporary one.
if [ -z "${DISPLAY:-}" ]; then
 PAM_SCREEN="${PAM_REVIEW_SCREEN:-:97}"
 PAM_LOG="$(mktemp /tmp/pam-xorg-XXXXXX.log)"
 Xorg "$PAM_SCREEN" -config "$PAM_ROOT/tools/xorg-dummy.conf" -logfile "$PAM_LOG" -noreset -nolisten tcp > /tmp/pam-xorg-console.log 2>&1 &
 PAM_XORG_PID=$!
 trap 'kill "$PAM_XORG_PID" 2>/dev/null || true; wait "$PAM_XORG_PID" 2>/dev/null || true' EXIT
 export DISPLAY="$PAM_SCREEN"
 # Bounded readiness polling; never stop or reuse an unknown X server.
 for i in {1..30}; do
  kill -0 "$PAM_XORG_PID" 2>/dev/null || { cat "$PAM_LOG"; exit 1; }
  [ -S "/tmp/.X11-unix/X${PAM_SCREEN#:}" ] && break
  sleep 0.1
 done
fi
export LP_NUM_THREADS="${LP_NUM_THREADS:-4}"
"$PAM_ROOT/tools/godot.sh" --audio-driver Dummy --script "${PAM_REVIEW_SCRIPT:-tests/capture.gd}"
