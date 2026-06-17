#!/usr/bin/env bash
input=$(cat)

# Extract fields
MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
OUTPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
WEEK_PCT=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' | cut -d. -f1)
WEEK_RESET=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
SESSION_PCT=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' | cut -d. -f1)

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

# Weekly quota + pacing. Delta = usage% - calendar%.
# > 0 = over-pacing (burning faster than time); < 0 = under-pacing (banking).
PACING=""
if [ -n "$WEEK_PCT" ] && [ -n "$WEEK_RESET" ]; then
    NOW=$(date +%s)
    WEEK_SECS=604800
    WEEK_START=$((WEEK_RESET - WEEK_SECS))
    ELAPSED=$((NOW - WEEK_START))
    CAL_PCT=$((ELAPSED * 100 / WEEK_SECS))
    PACE=$((WEEK_PCT - CAL_PCT))
    ABS=$PACE; [ "$PACE" -lt 0 ] && ABS=$((-PACE))

    if [ "$PACE" -ge 10 ]; then
        PACE_COLOR="$RED"; PACE_SYM="▲"
    elif [ "$PACE" -ge 3 ]; then
        PACE_COLOR="$YELLOW"; PACE_SYM="△"
    elif [ "$PACE" -le -10 ]; then
        PACE_COLOR="$GREEN"; PACE_SYM="▼"
    elif [ "$PACE" -le -3 ]; then
        PACE_COLOR="$CYAN"; PACE_SYM="▽"
    else
        PACE_COLOR="$DIM"; PACE_SYM="•"
    fi

    if [ "$WEEK_PCT" -ge 90 ]; then WEEK_COLOR="$RED"
    elif [ "$WEEK_PCT" -ge 70 ]; then WEEK_COLOR="$YELLOW"
    else WEEK_COLOR="$GREEN"; fi

    PACING=" ${DIM}|${RESET} ${WEEK_COLOR}${WEEK_PCT}%w${RESET} ${PACE_COLOR}${PACE_SYM}${ABS}${RESET}"
    [ -n "$SESSION_PCT" ] && PACING="${PACING} ${DIM}·${RESET} ${CYAN}${SESSION_PCT}%s${RESET}"
fi

# Token-based / API / Enterprise billing has no rolling quota windows — the
# rate_limits field is sent only for Claude.ai Pro/Max subscribers. When it's
# absent, show month-to-date Claude Code spend (via ccusage) + this session's
# spend, the rough analogue of the weekly + session quota shown above.
#
# ccusage parses the local logs (~2s) — too slow for the render path — so it is
# seeded synchronously only when there is no cache yet (or it is a day stale),
# and otherwise refreshed in the background while the cached value is displayed.
# If ccusage is unavailable, the month segment is simply omitted.
if [ -z "$PACING" ] && [ "$(echo "$input" | jq -r 'if .rate_limits then 1 else 0 end')" = "0" ]; then
    MONTH_CACHE="/tmp/claude-statusline-ccusage-month"
    MONTH_LOCK="/tmp/claude-statusline-ccusage-month.lock"
    NOW=$(date +%s)
    AGE=$((NOW - $(stat -f %m "$MONTH_CACHE" 2>/dev/null || echo 0)))

    ccusage_month() {
        local cc="ccusage"
        command -v ccusage >/dev/null 2>&1 || cc="npx --yes ccusage"
        $cc monthly --json 2>/dev/null | jq -r --arg m "$(date +%Y-%m)" \
            '(.monthly[] | select(.period == $m) | .totalCost) // empty' 2>/dev/null
    }

    if [ ! -f "$MONTH_CACHE" ] || [ "$AGE" -gt 86400 ]; then
        VAL=$(ccusage_month); printf '%s' "${VAL:-}" > "$MONTH_CACHE"
    elif [ "$AGE" -gt 900 ]; then
        [ -d "$MONTH_LOCK" ] && [ $((NOW - $(stat -f %m "$MONTH_LOCK" 2>/dev/null || echo 0))) -gt 300 ] && rmdir "$MONTH_LOCK" 2>/dev/null
        if mkdir "$MONTH_LOCK" 2>/dev/null; then
            ( VAL=$(ccusage_month); printf '%s' "${VAL:-}" > "$MONTH_CACHE"; rmdir "$MONTH_LOCK" 2>/dev/null ) >/dev/null 2>&1 &
        fi
    fi
    MONTH_SPEND=$(cat "$MONTH_CACHE" 2>/dev/null)

    SESSION_COST=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')

    if [ -n "$MONTH_SPEND" ]; then
        MO_FMT=$(printf '%.0f' "$MONTH_SPEND" 2>/dev/null || echo 0)
        # Optional monthly budget: put a dollar number in ~/.claude/monthly-budget
        # to show "spend/budget pct%". NOTE: this is GROSS ccusage usage at list
        # price — it does NOT subtract any prepaid credit balance.
        BUDGET=$(cat "${HOME:-/Users/$USER}/.claude/monthly-budget" 2>/dev/null | tr -dc '0-9.')
        if [ -n "$BUDGET" ] && [ "${BUDGET%.*}" -gt 0 ] 2>/dev/null; then
            BUD_PCT=$(printf '%.0f' "$(echo "$MONTH_SPEND * 100 / $BUDGET" | bc -l 2>/dev/null)" 2>/dev/null || echo 0)
            if [ "$BUD_PCT" -ge 100 ]; then BUD_COLOR="$RED"
            elif [ "$BUD_PCT" -ge 80 ]; then BUD_COLOR="$YELLOW"
            else BUD_COLOR="$GREEN"; fi
            PACING=" ${DIM}|${RESET} ${BUD_COLOR}\$${MO_FMT}${DIM}/${RESET}${BUD_COLOR}\$${BUDGET%.*} ${BUD_PCT}%${RESET}"
        else
            PACING=" ${DIM}|${RESET} ${MAGENTA}\$${MO_FMT}${RESET}${DIM}mo${RESET}"
        fi
    fi
    if [ -n "$SESSION_COST" ]; then
        S_FMT=$(printf '%.2f' "$SESSION_COST" 2>/dev/null || echo '0.00')
        if [ -n "$PACING" ]; then
            PACING="${PACING} ${DIM}·${RESET} ${CYAN}\$${S_FMT}${RESET}${DIM}s${RESET}"
        else
            PACING=" ${DIM}|${RESET} ${CYAN}\$${S_FMT}${RESET}${DIM}s${RESET}"
        fi
    fi
fi

# Line 1: model, directory, git
printf '%b\n' "${CYAN}${MODEL}${RESET} ${SHORT_DIR}${GIT_INFO}"

# Line 2: context bar, token counts, weekly quota + pacing (no trailing newline to avoid empty third line)
printf '%b' "${BAR_COLOR}${BAR}${RESET} ${PCT}% ${DIM}|${RESET} ${CYAN}${IN_FMT}${RESET}${DIM} in${RESET} ${GREEN}${OUT_FMT}${RESET}${DIM} out${RESET}${PACING}"
