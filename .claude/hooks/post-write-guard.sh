#!/usr/bin/env bash
# Тонкая обёртка: страж целиком в post-write-guard.py (ADR-0034).
# Гейты ADR-0006/ADR-0013 независимо от инструмента записи — bash-путь PreToolUse не видит.
[ -n "$CLAUDE_PROJECT_DIR" ] || exit 0
exec python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/post-write-guard.py"
