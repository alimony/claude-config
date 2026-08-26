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

# Pacing marker. Delta = usage% - calendar%, so > 0 means over-pacing (burning
# faster than the window elapses) and < 0 means banking. Sets PACE_COLOR,
# PACE_SYM and ABS for the caller. Shared by the weekly quota and the monthly
# spend limit — the read is the same, only the window differs.
pace_marker() {
    PACE=$1
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
}

# Weekly quota + pacing.
PACING=""
if [ -n "$WEEK_PCT" ] && [ -n "$WEEK_RESET" ]; then
    NOW=$(date +%s)
    WEEK_SECS=604800
    WEEK_START=$((WEEK_RESET - WEEK_SECS))
    ELAPSED=$((NOW - WEEK_START))
    CAL_PCT=$((ELAPSED * 100 / WEEK_SECS))
    pace_marker $((WEEK_PCT - CAL_PCT))

    if [ "$WEEK_PCT" -ge 90 ]; then WEEK_COLOR="$RED"
    elif [ "$WEEK_PCT" -ge 70 ]; then WEEK_COLOR="$YELLOW"
    else WEEK_COLOR="$GREEN"; fi

    PACING=" ${DIM}|${RESET} ${WEEK_COLOR}${WEEK_PCT}%w${RESET} ${PACE_COLOR}${PACE_SYM}${ABS}${RESET}"
    [ -n "$SESSION_PCT" ] && PACING="${PACING} ${DIM}·${RESET} ${CYAN}${SESSION_PCT}%s${RESET}"
fi

# Token-based / API / Enterprise billing has no rolling quota windows — the
# rate_limits field is sent only for Claude.ai Pro/Max subscribers. When it's
# absent, show month-to-date spend + this session's spend, the rough analogue
# of the weekly + session quota shown above.
#
# The month figure has two sources, in order of preference:
#
#  1. GET /api/oauth/usage — the actual figure, the same one /usage and the
#     desktop app show. Claude Code fetches it with the local OAuth token, but
#     it never reaches the status line: extra_usage is nested inside
#     rate_limits, and the payload attaches rate_limits only when a five-hour
#     or seven-day plan window exists. A spend-limit account has neither, so
#     the whole object is dropped. We therefore call the endpoint ourselves.
#
#  2. ccusage — a local estimate at list price, for when the OAuth token is
#     stale (a shell cannot refresh it; the next `claude` run does). It is
#     shown with a leading ~ so the two sources are never confused.
#
# Both are cached: neither the curl nor ccusage (~2s) belongs in the render
# path. Each is seeded synchronously only when it has no cache, and otherwise
# refreshed in the background while the cached value is displayed.
if [ -z "$PACING" ] && [ "$(echo "$input" | jq -r 'if .rate_limits then 1 else 0 end')" = "0" ]; then
    NOW=$(date +%s)

    # Calendar progress through the month, for the pacing marker. The spend
    # window carries no reset timestamp in the response, so we use the calendar
    # month — which is how the monthly limit is described. Deriving the end from
    # the next 1st keeps a DST month exact.
    MONTH_1ST="$(date +%Y-%m-01) 00:00:00"
    MONTH_START=$(date -j -f '%Y-%m-%d %H:%M:%S' "$MONTH_1ST" +%s 2>/dev/null)
    MONTH_END=$(date -j -v+1m -f '%Y-%m-%d %H:%M:%S' "$MONTH_1ST" +%s 2>/dev/null)
    MONTH_CAL_PCT=""
    [ -n "$MONTH_START" ] && [ -n "$MONTH_END" ] && [ "$MONTH_END" -gt "$MONTH_START" ] 2>/dev/null && \
        MONTH_CAL_PCT=$(( (NOW - MONTH_START) * 100 / (MONTH_END - MONTH_START) ))

    SPEND_CACHE="${HOME:-/Users/$USER}/.claude/statusline-spend"
    SPEND_LOCK="${HOME:-/Users/$USER}/.claude/statusline-spend.lock"
    SPEND_AGE=$((NOW - $(stat -f %m "$SPEND_CACHE" 2>/dev/null || echo 0)))

    # Emits "used|limit|percent" in major units, or nothing. A 401 from a stale
    # token yields nothing, which caches empty and falls through to ccusage.
    fetch_spend() {
        local tok
        tok=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null)
        [ -z "$tok" ] && return
        curl -sS --max-time 5 "https://api.anthropic.com/api/oauth/usage" -H "Authorization: Bearer $tok" -H "anthropic-beta: oauth-2025-04-20" -H "Accept: application/json" 2>/dev/null | jq -r '.spend | select(.enabled == true and .used != null and .limit != null) | "\(.used.amount_minor / pow(10; .used.exponent))|\(.limit.amount_minor / pow(10; .limit.exponent))|\(.percent)"' 2>/dev/null
    }

    if [ ! -f "$SPEND_CACHE" ]; then
        VAL=$(fetch_spend); printf '%s' "${VAL:-}" > "$SPEND_CACHE"
    elif [ "$SPEND_AGE" -gt 300 ]; then
        [ -d "$SPEND_LOCK" ] && [ $((NOW - $(stat -f %m "$SPEND_LOCK" 2>/dev/null || echo 0))) -gt 300 ] && rmdir "$SPEND_LOCK" 2>/dev/null
        if mkdir "$SPEND_LOCK" 2>/dev/null; then
            ( VAL=$(fetch_spend); printf '%s' "${VAL:-}" > "$SPEND_CACHE"; rmdir "$SPEND_LOCK" 2>/dev/null ) >/dev/null 2>&1 &
        fi
    fi
    SPEND_LINE=$(cat "$SPEND_CACHE" 2>/dev/null)

    ccusage_month() {
        local cc="ccusage"
        command -v ccusage >/dev/null 2>&1 || cc="npx --yes ccusage"
        $cc monthly --json 2>/dev/null | jq -r --arg m "$(date +%Y-%m)" \
            '(.monthly[] | select(.period == $m) | .totalCost) // empty' 2>/dev/null
    }

    MONTH_SPEND=""
    if [ -z "$SPEND_LINE" ]; then
        MONTH_CACHE="${HOME:-/Users/$USER}/.claude/statusline-ccusage-month"
        MONTH_LOCK="${HOME:-/Users/$USER}/.claude/statusline-ccusage-month.lock"
        AGE=$((NOW - $(stat -f %m "$MONTH_CACHE" 2>/dev/null || echo 0)))

        if [ ! -f "$MONTH_CACHE" ] || [ "$AGE" -gt 86400 ]; then
            VAL=$(ccusage_month); printf '%s' "${VAL:-}" > "$MONTH_CACHE"
        elif [ "$AGE" -gt 900 ]; then
            [ -d "$MONTH_LOCK" ] && [ $((NOW - $(stat -f %m "$MONTH_LOCK" 2>/dev/null || echo 0))) -gt 300 ] && rmdir "$MONTH_LOCK" 2>/dev/null
            if mkdir "$MONTH_LOCK" 2>/dev/null; then
                ( VAL=$(ccusage_month); printf '%s' "${VAL:-}" > "$MONTH_CACHE"; rmdir "$MONTH_LOCK" 2>/dev/null ) >/dev/null 2>&1 &
            fi
        fi
        MONTH_SPEND=$(cat "$MONTH_CACHE" 2>/dev/null)
    fi

    SESSION_COST=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')

    if [ -n "$SPEND_LINE" ]; then
        OLD_IFS=$IFS; IFS='|'; set -- $SPEND_LINE; IFS=$OLD_IFS
        SP_USED=$(printf '%.0f' "${1:-0}" 2>/dev/null || echo 0)
        SP_LIMIT=$(printf '%.0f' "${2:-0}" 2>/dev/null || echo 0)
        SP_PCT=$(printf '%.0f' "${3:-0}" 2>/dev/null || echo 0)
        if [ "$SP_PCT" -ge 100 ]; then SP_COLOR="$RED"
        elif [ "$SP_PCT" -ge 80 ]; then SP_COLOR="$YELLOW"
        else SP_COLOR="$GREEN"; fi
        PACING=" ${DIM}|${RESET} ${SP_COLOR}\$${SP_USED}${DIM}/${RESET}${SP_COLOR}\$${SP_LIMIT} ${SP_PCT}%${RESET}"
        if [ -n "$MONTH_CAL_PCT" ]; then
            pace_marker $((SP_PCT - MONTH_CAL_PCT))
            PACING="${PACING} ${PACE_COLOR}${PACE_SYM}${ABS}${RESET}"
        fi
    elif [ -n "$MONTH_SPEND" ]; then
        MO_FMT=$(printf '%.0f' "$MONTH_SPEND" 2>/dev/null || echo 0)
        # Optional monthly budget: put a dollar number in ~/.claude/monthly-budget
        # to show "~spend/budget pct%". NOTE: this is GROSS ccusage usage at list
        # price — it does NOT subtract any prepaid credit balance.
        BUDGET=$(cat "${HOME:-/Users/$USER}/.claude/monthly-budget" 2>/dev/null | tr -dc '0-9.')
        if [ -n "$BUDGET" ] && [ "${BUDGET%.*}" -gt 0 ] 2>/dev/null; then
            BUD_PCT=$(printf '%.0f' "$(echo "$MONTH_SPEND * 100 / $BUDGET" | bc -l 2>/dev/null)" 2>/dev/null || echo 0)
            if [ "$BUD_PCT" -ge 100 ]; then BUD_COLOR="$RED"
            elif [ "$BUD_PCT" -ge 80 ]; then BUD_COLOR="$YELLOW"
            else BUD_COLOR="$GREEN"; fi
            PACING=" ${DIM}|${RESET} ${BUD_COLOR}~\$${MO_FMT}${DIM}/${RESET}${BUD_COLOR}\$${BUDGET%.*} ${BUD_PCT}%${RESET}"
            if [ -n "$MONTH_CAL_PCT" ]; then
                pace_marker $((BUD_PCT - MONTH_CAL_PCT))
                PACING="${PACING} ${PACE_COLOR}${PACE_SYM}${ABS}${RESET}"
            fi
        else
            PACING=" ${DIM}|${RESET} ${MAGENTA}~\$${MO_FMT}${RESET}${DIM}mo${RESET}"
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
