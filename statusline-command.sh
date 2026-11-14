#!/usr/bin/env bash
# Claude Code status line. Claude Code sends the session as JSON on stdin and
# shows what this prints. Line 1: model, directory and git. Line 2: context,
# tokens, and quota or spend with a pacing marker.

# Read every field in one jq call. Numbers the shell compares are floored here,
# and a missing field becomes an empty string.
eval "$(jq -r '
    def int: if type == "number" then floor else "" end;
    def str: if . == null then "" else tostring end;
    .context_window as $c | .rate_limits as $r |
    @sh "MODEL=\(.model.display_name | str)",
    @sh "DIR=\(.workspace.current_dir // .cwd | str)",
    @sh "PCT=\($c.used_percentage | int)",
    @sh "INPUT_TOKENS=\($c.total_input_tokens | int)",
    @sh "OUTPUT_TOKENS=\($c.total_output_tokens | int)",
    @sh "HAS_RESPONSE=\(if $c.current_usage then 1 else "" end)",
    @sh "HAS_LIMITS=\(if $r then 1 else "" end)",
    @sh "WEEK_PCT=\($r.seven_day.used_percentage | int)",
    @sh "WEEK_RESET=\($r.seven_day.resets_at | int)",
    @sh "SESSION_PCT=\($r.five_hour.used_percentage | int)",
    @sh "GW_PCT=\($r.spend_limit.used_percentage | int)",
    @sh "GW_RESET=\($r.spend_limit.resets_at | int)",
    @sh "GW_USED=\($r.spend_limit.used_usd | str)",
    @sh "GW_LIMIT=\($r.spend_limit.limit_usd | str)",
    @sh "GW_PERIOD=\($r.spend_limit.period | str)",
    @sh "SESSION_COST=\(.cost.total_cost_usd | str)"
' 2>/dev/null)"
PCT=${PCT:-0}
INPUT_TOKENS=${INPUT_TOKENS:-0}
OUTPUT_TOKENS=${OUTPUT_TOKENS:-0}
NOW=${EPOCHSECONDS:-$(date +%s)}

CYAN=$'\033[36m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
DIM=$'\033[2m'
MAGENTA=$'\033[35m'
RESET=$'\033[0m'

# HOME may not be set in the status line's shell
HOME_DIR=${HOME:-/Users/$USER}
case $DIR in
    "$HOME_DIR") SHORT_DIR="~" ;;
    "$HOME_DIR"/*) SHORT_DIR="~${DIR#"$HOME_DIR"}" ;;
    *) SHORT_DIR=$DIR ;;
esac

# Git state, cached for 5 seconds per directory to keep large repos fast. One
# `git status` gives the branch and all three counts. --no-optional-locks keeps
# it from taking index.lock, which would make a commit Claude runs fail.
GIT_CACHE="${TMPDIR:-/tmp}"
GIT_CACHE="${GIT_CACHE%/}/claude-statusline-git${DIR//\//%}"
GIT_LINE=""
[ -f "$GIT_CACHE" ] && IFS= read -r GIT_LINE < "$GIT_CACHE"
CACHED_AT=${GIT_LINE%%|*}
case $CACHED_AT in ''|*[!0-9]*) CACHED_AT=0 ;; esac
if [ $((NOW - CACHED_AT)) -gt 5 ]; then
    GIT_LINE="$NOW|$(git -C "$DIR" --no-optional-locks status --porcelain=v2 --branch --untracked-files=all 2>/dev/null | awk '
        /^# branch\.oid / { oid = substr($3, 1, 7) }
        /^# branch\.head / { head = $3 }
        /^[12u] / { if (substr($2, 1, 1) != ".") s++; if (substr($2, 2, 1) != ".") m++ }
        /^\? / { u++ }
        END { if (head == "") exit; if (head == "(detached)") head = oid; printf "%s|%d|%d|%d", head, s, m, u }')"
    printf '%s\n' "$GIT_LINE" 2>/dev/null > "$GIT_CACHE"
fi
IFS='|' read -r _ BRANCH STAGED MODIFIED UNTRACKED <<< "$GIT_LINE"

GIT_INFO=""
if [ -n "$BRANCH" ]; then
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

FILLED=$((PCT / 10))
[ "$FILLED" -gt 10 ] && FILLED=10
printf -v FULL '%*s' "$FILLED" ''
printf -v EMPTY '%*s' $((10 - FILLED)) ''
BAR="${FULL// /█}${EMPTY// /░}"

# Token counts as 12.5K or 1.2M, truncated like `bc` with scale=1. Sets the
# variable named in $1.
fmt_tokens() {
    local n=$2
    if [ "$n" -ge 1000000 ]; then printf -v "$1" '%d.%dM' $((n / 1000000)) $((n % 1000000 / 100000))
    elif [ "$n" -ge 1000 ]; then printf -v "$1" '%d.%dK' $((n / 1000)) $((n % 1000 / 100))
    else printf -v "$1" '%d' "$n"; fi
}
fmt_tokens IN_FMT "$INPUT_TOKENS"
fmt_tokens OUT_FMT "$OUTPUT_TOKENS"

# Pacing marker. Delta = usage% - calendar%, so > 0 means over-pacing (burning
# faster than the window elapses) and < 0 means banking. Sets PACE_COLOR,
# PACE_SYM and ABS. Every window uses it: the weekly quota and each spend limit.
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

# Calendar math in UTC with no `date` call (Howard Hinnant's algorithms).
# days_from_civil Y M D sets DAYS, the days since 1970-01-01.
days_from_civil() {
    local y=$1 m=$2 d=$3 era yoe doy
    [ "$m" -le 2 ] && y=$((y - 1))
    era=$((y / 400)); yoe=$((y - era * 400))
    doy=$(( (153 * (m > 2 ? m - 3 : m + 9) + 2) / 5 + d - 1 ))
    DAYS=$(( era * 146097 + yoe * 365 + yoe / 4 - yoe / 100 + doy - 719468 ))
}
# civil_from_days N sets Y, M and D for the day N days after 1970-01-01.
civil_from_days() {
    local z=$(($1 + 719468)) era doe yoe doy mp
    era=$((z / 146097)); doe=$((z - era * 146097))
    yoe=$(( (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365 ))
    doy=$(( doe - (365 * yoe + yoe / 4 - yoe / 100) ))
    mp=$(( (5 * doy + 2) / 153 ))
    D=$(( doy - (153 * mp + 2) / 5 + 1 ))
    M=$(( mp < 10 ? mp + 3 : mp - 9 ))
    Y=$(( yoe + era * 400 + (M <= 2) ))
}

# Calendar percent of a window that ends at $1 and lasts one period $2 (daily,
# weekly, monthly). A month is the calendar month before the reset, at the same
# time of day. Sets CAL_PCT, or empty for an unknown period.
window_cal_pct() {
    local end=$1 start dim
    case $2 in
        daily) start=$((end - 86400)) ;;
        weekly) start=$((end - 604800)) ;;
        monthly)
            civil_from_days $((end / 86400))
            local y=$Y m=$((M - 1)) d=$D
            [ "$m" -eq 0 ] && { y=$((y - 1)); m=12; }
            days_from_civil "$Y" "$M" 1; dim=$DAYS
            days_from_civil "$y" "$m" 1; dim=$((dim - DAYS))
            [ "$d" -gt "$dim" ] && d=$dim
            days_from_civil "$y" "$m" "$d"
            start=$((DAYS * 86400 + end % 86400)) ;;
        *) CAL_PCT=""; return ;;
    esac
    CAL_PCT=$(( (NOW - start) * 100 / (end - start) ))
    [ "$CAL_PCT" -lt 0 ] && CAL_PCT=0
    [ "$CAL_PCT" -gt 100 ] && CAL_PCT=100
}

# Spend segment: "$used/$limit pct%", or "pct%$" without amounts, then a pacing
# marker when the calendar percent is known. $1 is "~" for an estimate.
spend_segment() {
    local mark=$1 used=$2 limit=$3 pct=$4 cal=$5 color=$GREEN
    [ "$pct" -ge 80 ] && color=$YELLOW
    [ "$pct" -ge 100 ] && color=$RED
    if [ -n "$used" ]; then
        PACING=" ${DIM}|${RESET} ${color}${mark}\$${used}${DIM}/${RESET}${color}\$${limit} ${pct}%${RESET}"
    else
        PACING=" ${DIM}|${RESET} ${color}${pct}%\$${RESET}"
    fi
    if [ -n "$cal" ]; then
        pace_marker $((pct - cal))
        PACING="${PACING} ${PACE_COLOR}${PACE_SYM}${ABS}${RESET}"
    fi
}

# This session's spend, for token-based billing
session_cost() {
    [ -n "$SESSION_COST" ] || return
    local s; printf -v s '%.2f' "$SESSION_COST" 2>/dev/null || s='0.00'
    if [ -n "$PACING" ]; then
        PACING="${PACING} ${DIM}·${RESET} ${CYAN}\$${s}${RESET}${DIM}s${RESET}"
    else
        PACING=" ${DIM}|${RESET} ${CYAN}\$${s}${RESET}${DIM}s${RESET}"
    fi
}

PACING=""
if [ -n "$WEEK_PCT" ] && [ -n "$WEEK_RESET" ]; then
    # Subscription: weekly quota with pacing, then the five-hour session quota
    pace_marker $((WEEK_PCT - (NOW - (WEEK_RESET - 604800)) * 100 / 604800))

    if [ "$WEEK_PCT" -ge 90 ]; then WEEK_COLOR="$RED"
    elif [ "$WEEK_PCT" -ge 70 ]; then WEEK_COLOR="$YELLOW"
    else WEEK_COLOR="$GREEN"; fi

    PACING=" ${DIM}|${RESET} ${WEEK_COLOR}${WEEK_PCT}%w${RESET} ${PACE_COLOR}${PACE_SYM}${ABS}${RESET}"
    [ -n "$SESSION_PCT" ] && PACING="${PACING} ${DIM}·${RESET} ${CYAN}${SESSION_PCT}%s${RESET}"
elif [ -n "$SESSION_PCT" ]; then
    # Subscription with only the five-hour window reported
    PACING=" ${DIM}|${RESET} ${CYAN}${SESSION_PCT}%s${RESET}"
elif [ -n "$GW_PCT" ] && [ -n "$GW_RESET" ]; then
    # Claude gateway spend limit: the gateway's own meter, no network call
    GW_USED_FMT=""; GW_LIMIT_FMT=""
    if [ -n "$GW_USED" ] && [ -n "$GW_LIMIT" ]; then
        printf -v GW_USED_FMT '%.0f' "$GW_USED" 2>/dev/null
        printf -v GW_LIMIT_FMT '%.0f' "$GW_LIMIT" 2>/dev/null
    fi
    window_cal_pct "$GW_RESET" "$GW_PERIOD"
    spend_segment "" "$GW_USED_FMT" "$GW_LIMIT_FMT" "$GW_PCT" "$CAL_PCT"
    session_cost
elif [ -z "$HAS_LIMITS" ] && [ -n "$HAS_RESPONSE" ]; then
    # Token-based billing (API, Enterprise, a spend-limit account): no rate-limit
    # windows. Show month-to-date spend and this session's spend. Waits for the
    # first API response, because a subscription's rate limits arrive only with
    # it, and before then every account looks like this one.
    #
    # The month figure has two sources, in order of preference:
    #
    #  1. GET /api/oauth/usage – the actual figure, the same one /usage shows.
    #     Claude Code never passes it to the status line: it attaches rate_limits
    #     only when a five-hour or seven-day window exists, and a spend-limit
    #     account has neither. So we call the endpoint ourselves.
    #
    #  2. An installed ccusage – a local estimate at list price, for when the
    #     OAuth token is stale (a shell cannot refresh it; the next `claude` run
    #     does). Shown with a leading ~, so the two are never confused.
    #
    # Both are cached and refreshed in the background while the cached value
    # shows. Each is fetched in the foreground only when it has no cache.
    CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME_DIR/.claude}"

    # The limit resets at 00:00 UTC on the 1st: the usage panel shows that same
    # instant in local time. Local time would be wrong near the boundary for a
    # user behind UTC.
    civil_from_days $((NOW / 86400))
    days_from_civil "$Y" "$M" 1; MONTH_START=$((DAYS * 86400))
    if [ "$M" -eq 12 ]; then days_from_civil $((Y + 1)) 1 1; else days_from_civil "$Y" $((M + 1)) 1; fi
    MONTH_END=$((DAYS * 86400))
    MONTH_CAL_PCT=$(( (NOW - MONTH_START) * 100 / (MONTH_END - MONTH_START) ))

    age_of() { AGE=$((NOW - $(stat -f %m "$1" 2>/dev/null || echo 0))); }

    # Runs fetch function $1 into cache $2: in the foreground when there is no
    # cache or it is older than $4 seconds, in the background (one at a time)
    # when it is older than $3 seconds.
    refresh() {
        local fetch=$1 cache=$2 lock="$2.lock" val
        age_of "$cache"
        if [ ! -f "$cache" ] || [ "$AGE" -gt "$4" ]; then
            val=$($fetch); printf '%s' "$val" > "$cache"
        elif [ "$AGE" -gt "$3" ]; then
            age_of "$lock"
            [ -d "$lock" ] && [ "$AGE" -gt 300 ] && rmdir "$lock" 2>/dev/null
            if mkdir "$lock" 2>/dev/null; then
                ( val=$($fetch); printf '%s' "$val" > "$cache"; rmdir "$lock" 2>/dev/null ) >/dev/null 2>&1 &
            fi
        fi
    }

    # Prints "used|limit|percent" in major units, or nothing. A 401 from a stale
    # token prints nothing, which caches empty and falls through to ccusage.
    fetch_spend() {
        # A second account runs with CLAUDE_CONFIG_DIR set, and Claude Code then
        # suffixes its Keychain entry with the first 8 hex digits of the dir's
        # SHA-256
        local svc="Claude Code-credentials" tok
        [ -n "${CLAUDE_CONFIG_DIR:-}" ] && svc="$svc-$(printf '%s' "$CLAUDE_CONFIG_DIR" | shasum -a 256 | cut -c1-8)"
        tok=$(security find-generic-password -s "$svc" -w 2>/dev/null | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null)
        [ -z "$tok" ] && return
        curl -sS --max-time 5 "https://api.anthropic.com/api/oauth/usage" -H "Authorization: Bearer $tok" -H "anthropic-beta: oauth-2025-04-20" -H "Accept: application/json" 2>/dev/null | jq -r '.spend | select(.enabled == true and .used != null and .limit != null) | "\(.used.amount_minor / pow(10; .used.exponent))|\(.limit.amount_minor / pow(10; .limit.exponent))|\(.percent)"' 2>/dev/null
    }

    # ccusage reports by local date, so the month here is local. It is never
    # downloaded during a render: without an installed ccusage there is no
    # estimate.
    ccusage_month() {
        command -v ccusage >/dev/null 2>&1 || return
        ccusage monthly --json 2>/dev/null | jq -r --arg m "$(date +%Y-%m)" \
            '(.monthly[] | select(.period == $m) | .totalCost) // empty' 2>/dev/null
    }

    SPEND_LINE=""
    refresh fetch_spend "$CONFIG_DIR/statusline-spend" 300 999999999
    [ -f "$CONFIG_DIR/statusline-spend" ] && IFS= read -r SPEND_LINE < "$CONFIG_DIR/statusline-spend"

    if [ -n "$SPEND_LINE" ]; then
        IFS='|' read -r SP_USED SP_LIMIT SP_PCT <<< "$SPEND_LINE"
        printf -v SP_USED '%.0f' "${SP_USED:-0}" 2>/dev/null || SP_USED=0
        printf -v SP_LIMIT '%.0f' "${SP_LIMIT:-0}" 2>/dev/null || SP_LIMIT=0
        printf -v SP_PCT '%.0f' "${SP_PCT:-0}" 2>/dev/null || SP_PCT=0
        spend_segment "" "$SP_USED" "$SP_LIMIT" "$SP_PCT" "$MONTH_CAL_PCT"
    else
        MONTH_SPEND=""
        refresh ccusage_month "$CONFIG_DIR/statusline-ccusage-month" 900 86400
        [ -f "$CONFIG_DIR/statusline-ccusage-month" ] && IFS= read -r MONTH_SPEND < "$CONFIG_DIR/statusline-ccusage-month"

        if [ -n "$MONTH_SPEND" ]; then
            printf -v MO_FMT '%.0f' "$MONTH_SPEND" 2>/dev/null || MO_FMT=0
            # Optional monthly budget: put a dollar number in $CONFIG_DIR/monthly-budget
            # to show "~spend/budget pct%". This is GROSS ccusage usage at list
            # price: it does not subtract any prepaid credit balance.
            BUDGET=""
            [ -f "$CONFIG_DIR/monthly-budget" ] && IFS= read -r BUDGET < "$CONFIG_DIR/monthly-budget"
            BUDGET=${BUDGET//[^0-9.]/}
            if [ -n "$BUDGET" ] && [ "${BUDGET%.*}" -gt 0 ] 2>/dev/null; then
                printf -v BUD_PCT '%.0f' "$(echo "$MONTH_SPEND * 100 / $BUDGET" | bc -l 2>/dev/null)" 2>/dev/null || BUD_PCT=0
                spend_segment "~" "$MO_FMT" "${BUDGET%.*}" "$BUD_PCT" "$MONTH_CAL_PCT"
            else
                PACING=" ${DIM}|${RESET} ${MAGENTA}~\$${MO_FMT}${RESET}${DIM}mo${RESET}"
            fi
        fi
    fi
    session_cost
fi

# Line 1: model, directory, git
printf '%s\n' "${CYAN}${MODEL}${RESET} ${SHORT_DIR}${GIT_INFO}"

# Line 2: context bar, token counts, quota or spend (no trailing newline, to
# avoid an empty third line)
printf '%s' "${BAR_COLOR}${BAR}${RESET} ${PCT}% ${DIM}|${RESET} ${CYAN}${IN_FMT}${RESET}${DIM} in${RESET} ${GREEN}${OUT_FMT}${RESET}${DIM} out${RESET}${PACING}"
