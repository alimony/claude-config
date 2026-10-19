#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
MAIN_DIR="$HOME/.claude"
# A second account runs with CLAUDE_CONFIG_DIR set; install into that dir when it is
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$MAIN_DIR}"

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

# State a second config dir links back to the main one, so sessions, memory,
# prompt history, and plugins are shared across accounts
SHARED_DIRS=(
    "projects"
    "file-history"
    "plans"
    "todos"
    "tasks"
    "plugins"
)
SHARED_FILES=(
    "history.jsonl"
)

# .claude.json keys a second config dir is seeded with: project trust and UI
# state, but no account, user ID, or cached server data
SEED_KEYS='["projects", "hasCompletedOnboarding", "lastOnboardingVersion", "lastReleaseNotesSeen", "installMethod", "autoUpdates", "autoUpdatesProtectedForNative", "githubRepoPaths", "copyOnSelect", "optionAsMetaKeyInstalled", "hasUsedBackslashReturn", "hasCompletedClaudeInChromeOnboarding", "claudeInChromeDefaultEnabled", "diffSidebarOpen", "showSpinnerTree", "leftArrowOpensAgents", "lspRecommendationDisabled", "effortCalloutDismissed", "effortCalloutV2Dismissed"]'

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

# Link shared state and seed .claude.json, only for a second config dir
if [ "$CLAUDE_DIR" != "$MAIN_DIR" ]; then
    for dir in "${SHARED_DIRS[@]}"; do
        [ -d "$MAIN_DIR/$dir" ] || run mkdir -p "$MAIN_DIR/$dir"
        link_item "$MAIN_DIR/$dir" "$CLAUDE_DIR/$dir"
    done
    for file in "${SHARED_FILES[@]}"; do
        [ -f "$MAIN_DIR/$file" ] || run touch "$MAIN_DIR/$file"
        link_item "$MAIN_DIR/$file" "$CLAUDE_DIR/$file"
    done

    if [ -e "$CLAUDE_DIR/.claude.json" ]; then
        say "  ok  $CLAUDE_DIR/.claude.json (exists)"
    elif [ -f "$HOME/.claude.json" ]; then
        echo "  seed  $CLAUDE_DIR/.claude.json"
        if ! $CHECK; then
            jq --argjson keys "$SEED_KEYS" 'with_entries(select(.key as $k | $keys | index($k)))' \
                "$HOME/.claude.json" > "$CLAUDE_DIR/.claude.json"
            chmod 600 "$CLAUDE_DIR/.claude.json"
        fi
        DRIFT=true
    fi
fi

if $CHECK; then
    $DRIFT || exit 0
    echo "Run $REPO_DIR/install.sh to make these changes, then restart Claude Code."
    exit 1
fi

echo ""
echo "Done. Restart Claude Code to pick up changes."
