#!/usr/bin/env bash
# Claude Code → WakaTime heartbeat (Hypomnemata)
# Учёт времени работы агента по проекту. События: UserPromptSubmit, PostToolUse, Stop.
# Неблокирующий, тихий; деградирует мягко (нет wakatime-cli → exit 0).

INPUT=$(cat)
read -r CWD EVENT TOOL < <(printf '%s' "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('cwd','') or '', d.get('hook_event_name','') or '-', d.get('tool_name','') or '-')
" 2>/dev/null)

# Проект из git-remote или имени папки
if [ -n "$CWD" ] && [ -d "$CWD" ]; then
  PROJECT=$(cd "$CWD" && git config --local remote.origin.url 2>/dev/null | sed 's#.*/\([^.]*\)#\1#;s#\.git$##')
  PROJECT=${PROJECT:-$(basename "$CWD")}
else
  PROJECT="hypomnemata"
fi

# Категория по событию/инструменту
CATEGORY="ai coding"
if [ "$EVENT" = "PostToolUse" ]; then
  case "$TOOL" in
    WebSearch|WebFetch) CATEGORY="researching" ;;
    Read|Grep|Glob)     CATEGORY="code reviewing" ;;
    Edit|Write|MultiEdit) CATEGORY="coding" ;;
  esac
fi

CLI="$HOME/.wakatime/wakatime-cli"
[ -x "$CLI" ] || exit 0

("$CLI" \
  --entity-type app \
  --entity "Claude Code" \
  --category "$CATEGORY" \
  --project "$PROJECT" \
  --plugin "claude-code-hypomnemata/0.1.0" \
  --write \
  >/dev/null 2>&1 &)

exit 0
