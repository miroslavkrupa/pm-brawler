#!/usr/bin/env bash
# Builds the WebGL version and publishes it to GitHub Pages (the gh-pages branch),
# which serves it at https://miroslavkrupa.github.io/pm-brawler/
#
# Usage: Tools/publish_web.sh             build with Unity, then publish
#        Tools/publish_web.sh --no-build  publish the existing Builds/WebGL
#
# Close the project in the Unity Editor first: batch builds can't run while it's open.
# Set UNITY=/path/to/Unity to use an editor other than the one in ProjectVersion.txt.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BUILD_DIR="Builds/WebGL"

if [[ "${1:-}" != "--no-build" ]]; then
  VERSION=$(sed -n 's/^m_EditorVersion: //p' ProjectSettings/ProjectVersion.txt)
  UNITY="${UNITY:-/Applications/Unity/Hub/Editor/$VERSION/Unity.app/Contents/MacOS/Unity}"
  if [[ ! -x "$UNITY" ]]; then
    echo "Unity $VERSION not found at $UNITY (install it in Unity Hub or set UNITY=...)" >&2
    exit 1
  fi
  if [[ -f Temp/UnityLockfile ]] && lsof Temp/UnityLockfile >/dev/null 2>&1; then
    echo "The project is open in Unity. Close it and run this again." >&2
    exit 1
  fi
  LOG="$(mktemp -t pm-brawler-webgl)"
  echo "Building WebGL with Unity $VERSION (takes a few minutes)..."
  if ! "$UNITY" -batchmode -quit -projectPath "$ROOT" -buildTarget WebGL \
      -executeMethod PMBrawler.Editor.ProjectSetup.BuildWebGL -logFile "$LOG"; then
    echo "Build failed. Log: $LOG" >&2
    exit 1
  fi
fi

if [[ ! -f "$BUILD_DIR/index.html" ]]; then
  echo "No build found in $BUILD_DIR." >&2
  exit 1
fi

SOURCE=$(git rev-parse --short HEAD)
if [[ -n "$(git status --porcelain -- Assets Packages ProjectSettings)" ]]; then   # what goes into the build
  echo "Note: you have uncommitted changes; they are in the build but not in commit $SOURCE."
  SOURCE="$SOURCE+local changes"
fi

# check out gh-pages in a throwaway worktree, swap its contents for the new build, push
WORKTREE=$(mktemp -d)
trap 'git worktree remove --force "$WORKTREE" >/dev/null 2>&1 || true' EXIT
git fetch -q origin gh-pages
git worktree add -q -B gh-pages "$WORKTREE" origin/gh-pages
git -C "$WORKTREE" rm -rq --ignore-unmatch .
cp -R "$BUILD_DIR"/. "$WORKTREE"/
touch "$WORKTREE/.nojekyll"   # serve files as-is, no Jekyll processing
git -C "$WORKTREE" add -A

if git -C "$WORKTREE" diff --cached --quiet; then
  echo "The published version is already up to date."
  exit 0
fi

git -C "$WORKTREE" commit -q -m "Publish WebGL build of $SOURCE"
git -C "$WORKTREE" push -q origin gh-pages
echo "Published. GitHub Pages updates in a minute or two: https://miroslavkrupa.github.io/pm-brawler/"
