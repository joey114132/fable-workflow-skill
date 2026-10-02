#!/usr/bin/env bash
set -euo pipefail

# Install the fable-workflow skill into a skills directory.
# Usage: ./install.sh <skills-dir>
#   e.g. ./install.sh ~/my-project/.claude/skills
#
# Copies SKILL.md, every reference .md file it points to, and scripts/goals.py.
# The hooks (hooks/) are not copied: they only run when the repo is installed as
# a Claude Code plugin, where ${CLAUDE_PLUGIN_ROOT} is set. A manual install gets
# the method and the completion-gate script, run by its installed path.

target="${1:-}"
if [[ -z "${target}" ]]; then
  echo "Usage: ./install.sh <skills-dir>" >&2
  echo "  e.g. ./install.sh ~/my-project/.claude/skills" >&2
  echo "Hooks are plugin-only and are not copied." >&2
  exit 2
fi

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${target%/}/fable-workflow"

mkdir -p "${dest}/scripts"
cp "${repo}/SKILL.md" "${repo}/prompts.md" "${repo}/standing-orders.md" \
   "${repo}/loop-engineering.md" "${repo}/completion-gate.md" "${dest}/"
cp "${repo}/scripts/goals.py" "${dest}/scripts/"

echo "Installed fable-workflow -> ${dest}"
echo "Hooks not installed (plugin installs only)."
