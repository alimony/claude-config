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
    "skills"
    "agents"
)

# --check reports what a run would change, changes nothing, and exits 1 if anything differs
CHECK=false
if [ "${1:-}" = "--check" ]; then
    CHECK=true
fi
DRIFT=false

# Progress output, which --check leaves out
say() {
    $CHECK || echo "$@"
}

# A change under ~/.claude, which --check records instead of making
run() {
    if $CHECK; then
        DRIFT=true
    else
        "$@"
    fi
}

say "Installing Claude config from $REPO_DIR"
say "Target: $CLAUDE_DIR"
say ""

$CHECK || mkdir -p "$CLAUDE_DIR"

link_item() {
    local src="$1"
    local dest="$2"

    if [ -L "$dest" ]; then
        local current_target
        current_target="$(readlink "$dest")"
        if [ "$current_target" = "$src" ]; then
            say "  ok  $dest (already linked)"
            return
        fi
        echo "  update  $dest (repointing symlink)"
        run rm "$dest"
    elif [ -e "$dest" ]; then
        echo "  backup  $dest -> ${dest}.bak"
        run mv "$dest" "${dest}.bak"
    else
        echo "  new  $dest"
    fi

    run ln -s "$src" "$dest"
}

# Link files
for file in "${FILES[@]}"; do
    src="$REPO_DIR/$file"
    dest="$CLAUDE_DIR/$file"
    if [ -f "$src" ]; then
        link_item "$src" "$dest"
    else
        say "  skip  $file (not in repo)"
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

if $CHECK; then
    $DRIFT || exit 0
    echo "Run $REPO_DIR/install.sh to make these changes, then restart Claude Code."
    exit 1
fi

echo ""
echo "Done. Restart Claude Code to pick up changes."
