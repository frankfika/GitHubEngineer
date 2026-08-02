#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_BUNDLE="${1:-$ROOT_DIR/src-tauri/target/release/bundle/macos/GitHub Engineer.app}"
DMG_PATH="${2:-}"
DESKTOP_BINARY="$APP_BUNDLE/Contents/MacOS/github-engineer-desktop"
BACKEND_BINARY="$APP_BUNDLE/Contents/MacOS/github-engineer-backend"

if [[ ! -d "$APP_BUNDLE" ]]; then
  echo "Missing macOS app bundle: $APP_BUNDLE" >&2
  exit 1
fi
for binary in "$DESKTOP_BINARY" "$BACKEND_BINARY"; do
  if [[ ! -x "$binary" ]]; then
    echo "Unified bundle is missing executable: $binary" >&2
    exit 1
  fi
done

desktop_archs="$(lipo -archs "$DESKTOP_BINARY")"
backend_archs="$(lipo -archs "$BACKEND_BINARY")"
if [[ "$desktop_archs" != "$backend_archs" ]]; then
  echo "Frontend/backend architecture mismatch: $desktop_archs vs $backend_archs" >&2
  exit 1
fi

# PyInstaller must freeze Python and project dependencies into the backend.
# A distributable bundle may link macOS system libraries, but never a Homebrew,
# virtualenv, or source-tree library that will be absent on the user's machine.
non_system_dependencies="$(
  otool -L "$BACKEND_BINARY" \
    | tail -n +2 \
    | awk '{print $1}' \
    | grep -Ev '^(/usr/lib/|/System/Library/)' \
    || true
)"
if [[ -n "$non_system_dependencies" ]]; then
  echo "Packaged backend has non-system runtime dependencies:" >&2
  echo "$non_system_dependencies" >&2
  exit 1
fi

codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"

if [[ -z "$DMG_PATH" ]]; then
  DMG_PATH="$(find "$ROOT_DIR/src-tauri/target/release/bundle/dmg" -name '*.dmg' -type f -print -quit)"
fi
if [[ -z "$DMG_PATH" || ! -f "$DMG_PATH" ]]; then
  echo "Missing DMG installer for unified app bundle." >&2
  exit 1
fi
hdiutil verify "$DMG_PATH"

mount_dir="$(mktemp -d /tmp/github-engineer-dmg.XXXXXX)"
cleanup_mount() {
  hdiutil detach "$mount_dir" >/dev/null 2>&1 || true
  rmdir "$mount_dir" >/dev/null 2>&1 || true
}
trap cleanup_mount EXIT
hdiutil attach -readonly -nobrowse -mountpoint "$mount_dir" "$DMG_PATH" >/dev/null
DMG_APP="$mount_dir/GitHub Engineer.app"
for relative_binary in \
  "Contents/MacOS/github-engineer-desktop" \
  "Contents/MacOS/github-engineer-backend"; do
  if [[ ! -x "$DMG_APP/$relative_binary" ]]; then
    echo "DMG is missing unified bundle executable: $relative_binary" >&2
    exit 1
  fi
  if ! cmp -s "$APP_BUNDLE/$relative_binary" "$DMG_APP/$relative_binary"; then
    echo "DMG contains a stale or mismatched executable: $relative_binary" >&2
    exit 1
  fi
done
cleanup_mount
trap - EXIT

echo "Unified desktop bundle verified."
echo "frontend: $DESKTOP_BINARY ($desktop_archs)"
echo "backend:  $BACKEND_BINARY ($backend_archs, embedded Python runtime)"
echo "installer: $DMG_PATH (contains the same frontend and backend)"
