#!/usr/bin/env bash
input=$(cat)

# Extract fields
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
OUTPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')

# Colors
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
DIM='\033[2m'
MAGENTA='\033[35m'
RESET='\033[0m'

# Shorten directory (sed is more reliable than bash parameter expansion here
# because HOME may not be set in the statusline shell context)
SHORT_DIR=$(echo "$DIR" | sed "s|^${HOME:-/Users/$USER}|~|")

# Git info (cached for performance)
CACHE_FILE="/tmp/claude-statusline-git-cache"
CACHE_MAX_AGE=5

cache_is_stale() {
    [ ! -f "$CACHE_FILE" ] || \
    [ $(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0))) -gt $CACHE_MAX_AGE ]
}

GIT_INFO=""
if git -C "$DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    if cache_is_stale; then
        BRANCH=$(git -C "$DIR" symbolic-ref --quiet --short HEAD 2>/dev/null || \
                 git -C "$DIR" rev-parse --short HEAD 2>/dev/null || echo "?")
        STAGED=$(git -C "$DIR" diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
        MODIFIED=$(git -C "$DIR" diff --numstat 2>/dev/null | wc -l | tr -d ' ')
        UNTRACKED=$(git -C "$DIR" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
        echo "$BRANCH|$STAGED|$MODIFIED|$UNTRACKED" > "$CACHE_FILE"
    fi
    IFS='|' read -r BRANCH STAGED MODIFIED UNTRACKED < "$CACHE_FILE"

    STATUS=""
    [ "$STAGED" -gt 0 ] 2>/dev/null && STATUS="${GREEN}+${STAGED}${RESET}"
    [ "$MODIFIED" -gt 0 ] 2>/dev/null && STATUS="${STATUS}${YELLOW}~${MODIFIED}${RESET}"
    [ "$UNTRACKED" -gt 0 ] 2>/dev/null && STATUS="${STATUS}${RED}?${UNTRACKED}${RESET}"
    [ -n "$STATUS" ] && STATUS=" $STATUS"

    GIT_INFO=" ${DIM}on${RESET} ${MAGENTA}${BRANCH}${RESET}${STATUS}"
fi

# Context bar with color thresholds
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

BAR_WIDTH=10
FILLED=$((PCT * BAR_WIDTH / 100))
EMPTY=$((BAR_WIDTH - FILLED))
BAR=""
[ "$FILLED" -gt 0 ] && BAR=$(printf "%${FILLED}s" | tr ' ' '█')
[ "$EMPTY" -gt 0 ] && BAR="${BAR}$(printf "%${EMPTY}s" | tr ' ' '░')"

# Format token counts (e.g., 12.5K, 1.2M)
fmt_tokens() {
    local n=$1
    if [ "$n" -ge 1000000 ]; then
        printf '%s' "$(echo "scale=1; $n / 1000000" | bc)M"
    elif [ "$n" -ge 1000 ]; then
        printf '%s' "$(echo "scale=1; $n / 1000" | bc)K"
    else
        printf '%s' "$n"
    fi
}
IN_FMT=$(fmt_tokens "$INPUT_TOKENS")
OUT_FMT=$(fmt_tokens "$OUTPUT_TOKENS")

# Line 1: model, directory, git
printf '%b\n' "${CYAN}${MODEL}${RESET} ${SHORT_DIR}${GIT_INFO}"

# Line 2: context bar, token counts (no trailing newline to avoid empty third line)
printf '%b' "${BAR_COLOR}${BAR}${RESET} ${PCT}% ${DIM}|${RESET} ${CYAN}${IN_FMT}${RESET}${DIM} in${RESET} ${GREEN}${OUT_FMT}${RESET}${DIM} out${RESET}"
