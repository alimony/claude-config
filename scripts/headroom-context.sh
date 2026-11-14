#!/usr/bin/env bash
# SessionStart hook: adds the Headroom instructions to the session while Claude
# Code sends its requests to a local proxy. `headroom wrap claude` points one of
# these variables at 127.0.0.1 (port 8787 unless --port changes it). Without a
# local proxy, the session gets nothing.
for url in "${ANTHROPIC_BASE_URL:-}" "${ANTHROPIC_VERTEX_BASE_URL:-}" "${ANTHROPIC_FOUNDRY_BASE_URL:-}"; do
    case $url in
        http://127.0.0.1:*|http://localhost:*)
            jq -n --rawfile ctx "${BASH_SOURCE[0]%/*}/headroom-context.md" \
                '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
            exit 0
            ;;
    esac
done
