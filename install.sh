#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

# Files to symlink: source (relative to repo) -> target (relative to ~/.claude/)
FILES=(
    "CLAUDE.md"
    "settings.json"
    "statusline-command.sh"
)

# Directories to symlink (when they have content)
DIRS=(
    "commands"
    "skills"
    "agents"
)

echo "Installing Claude config from $REPO_DIR"
echo "Target: $CLAUDE_DIR"
echo ""

mkdir -p "$CLAUDE_DIR"

link_item() {
    local src="$1"
    local dest="$2"

    if [ -L "$dest" ]; then
        local current_target
        current_target="$(readlink "$dest")"
        if [ "$current_target" = "$src" ]; then
            echo "  ok  $dest (already linked)"
            return
        fi
        echo "  update  $dest (repointing symlink)"
        rm "$dest"
    elif [ -e "$dest" ]; then
        echo "  backup  $dest -> ${dest}.bak"
        mv "$dest" "${dest}.bak"
    else
        echo "  new  $dest"
    fi

    ln -s "$src" "$dest"
}

# Link files
for file in "${FILES[@]}"; do
    src="$REPO_DIR/$file"
    dest="$CLAUDE_DIR/$file"
    if [ -f "$src" ]; then
        link_item "$src" "$dest"
    else
        echo "  skip  $file (not in repo)"
    fi
done

# Link directories (only if they exist in repo and have content)
for dir in "${DIRS[@]}"; do
    src="$REPO_DIR/$dir"
    dest="$CLAUDE_DIR/$dir"
    if [ -d "$src" ] && [ "$(ls -A "$src" 2>/dev/null)" ]; then
        link_item "$src" "$dest"
    fi
done

echo ""
echo "Done. Restart Claude Code to pick up changes."
