#!/usr/bin/env bash
# Hypomnemata — enforce ADR-0036 п.7: задача, взятая в юнит, обязана назвать рабочий продукт.
# PreToolUse Write: у карточки 10-governance/6-tasks/T-*.md с заполненным `unit:`
# требует непустого, не-плейсхолдерного `artifact:`. Иначе блок (exit 2).
# Задача без `unit:` проходит молча: рабочий продукт у неё желателен, не обязателен.
# Правки (Edit) пропускаем — полного содержимого у них нет.
# see 80-kernel/stele/ADR-0013-wp-card-self-contained.md · ADR-0036-task-as-atomic-card.md

input=$(cat)
path=$(printf '%s' "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
[ -z "$path" ] && exit 0
rel=${path#"$CLAUDE_PROJECT_DIR"/}

# только карточки задач
case "$rel" in
  10-governance/6-tasks/[Tt]-*.md) ;;
  *) exit 0 ;;
esac

# полное содержимое есть только у Write; у Edit/MultiEdit его нет — пропускаем (гейт на создание)
content=$(printf '%s' "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('content',''))" 2>/dev/null)
[ -z "$content" ] && exit 0

printf '%s' "$content" | python3 "$CLAUDE_PROJECT_DIR/80-kernel/scripts/task-artifact-check.py"
exit $?
