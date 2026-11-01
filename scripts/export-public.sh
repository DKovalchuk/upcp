#!/usr/bin/env bash
# Export a release branch of this repository to the public GitHub mirror
# with a scrubbed full history (TASK-0167).
#
# Pipeline:  mirror clone -> filter-repo replace-text (deterministic)
#           -> gitleaks gate (baseline) -> push <branch>
#
# The local checkout and the upstream GitLab history are never rewritten;
# every export re-applies the same replacement rules, so successive exports
# stay fast-forward for the same upstream history.
#
# Usage:
#   scripts/export-public.sh --to <git-url> [options]
#
# Options:
#   --to <url>       target git url (required), e.g.
#                    https://github.com/DKovalchuk/upcp.git
#   --source <url>   source git url (default: origin of this checkout)
#   --branch <name>  branch to export (default: main)
#   --dry-run        run the whole pipeline, push with --dry-run
#   --keep           keep the temporary workdir (debugging)
#
# Environment:
#   GITHUB_PUB_TOKEN  if set, embedded in --to https url for authentication
#                     (masked CI variable; never echoed)
#
# Requires in PATH: git, git-filter-repo, gitleaks.
set -euo pipefail

die() {
  echo "ERROR: $*" >&2
  exit 1
}

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
}

TARGET=""
SOURCE=""
BRANCH="main"
DRY_RUN=0
KEEP=0

while [ $# -gt 0 ]; do
  case "$1" in
    --to) TARGET="${2:?--to requires a value}"; shift 2 ;;
    --source) SOURCE="${2:?--source requires a value}"; shift 2 ;;
    --branch) BRANCH="${2:?--branch requires a value}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --keep) KEEP=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (see --help)" ;;
  esac
done

[ -n "$TARGET" ] || die "--to is required (see --help)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
REPLACE_TEXT="$SCRIPT_DIR/export-replace-text.txt"
BASELINE="$SCRIPT_DIR/export-gitleaks-baseline.txt"

for tool in git git-filter-repo gitleaks; do
  command -v "$tool" >/dev/null 2>&1 || die "missing tool: $tool"
done
[ -f "$REPLACE_TEXT" ] || die "missing replacement rules: $REPLACE_TEXT"
[ -f "$BASELINE" ] || die "missing gitleaks baseline: $BASELINE"

if [ -z "$SOURCE" ]; then
  SOURCE="$(git -C "$REPO_ROOT" remote get-url origin)"
fi

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/upcp-export.XXXXXX")"
cleanup() {
  if [ "$KEEP" -eq 1 ]; then
    echo "==> workdir kept: $WORKDIR"
  else
    rm -rf "$WORKDIR"
  fi
}
trap cleanup EXIT

echo "==> [1/5] mirror clone: $(printf '%s' "$SOURCE" | sed 's|://[^@]*@|://***@|')"
git clone --quiet --mirror "$SOURCE" "$WORKDIR/upcp.git"
cd "$WORKDIR/upcp.git"

echo "==> [2/5] scrub history (filter-repo replace-text, deterministic)"
git filter-repo --quiet --force --replace-text "$REPLACE_TEXT"

echo "==> [3/5] gitleaks gate (baseline: $(basename "$BASELINE"))"
if ! gitleaks git . --log-opts=--all \
    --baseline-path "$BASELINE" --no-banner --redact; then
  die "gitleaks found findings outside the baseline — refusing to push"
fi

echo "==> [4/5] resolve push url"
PUSH_URL="$TARGET"
if [ -n "${GITHUB_PUB_TOKEN:-}" ]; then
  case "$TARGET" in
    https://*)
      creds="$(printf '%s' "${GITHUB_PUB_TOKEN}" | sed 's/[\/&]/\\&/g')"
      PUSH_URL="$(printf '%s' "$TARGET" | sed "s|^https://|https://x-access-token:${creds}@|")"
      ;;
    *) die "GITHUB_PUB_TOKEN is set but --to is not an https url" ;;
  esac
fi

echo "==> [5/5] push branch '$BRANCH'"
if [ "$DRY_RUN" -eq 1 ]; then
  git push --dry-run --force "$PUSH_URL" \
    "refs/heads/$BRANCH:refs/heads/$BRANCH"
  echo "==> dry-run complete (nothing pushed)"
else
  git push --force "$PUSH_URL" "refs/heads/$BRANCH:refs/heads/$BRANCH"
  echo "==> exported '$BRANCH' to target"
fi
