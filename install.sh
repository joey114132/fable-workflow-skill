#!/usr/bin/env bash
set -euo pipefail

# Install the fable-workflow skill into a skills directory.
# Usage: ./install.sh <skills-dir>
#   e.g. ./install.sh ~/my-project/.claude/skills

target="${1:-}"
if [[ -z "${target}" ]]; then
  echo "Usage: ./install.sh <skills-dir>" >&2
  echo "  e.g. ./install.sh ~/my-project/.claude/skills" >&2
  exit 2
fi

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${target%/}/fable-workflow"

mkdir -p "${dest}"
cp "${repo}/SKILL.md" "${repo}/prompts.md" "${dest}/"

echo "Installed fable-workflow -> ${dest}"
