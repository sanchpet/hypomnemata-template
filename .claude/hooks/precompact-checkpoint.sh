#!/usr/bin/env bash
# PreCompact Checkpoint Hook (Hypomnemata)
# Перед сжатием контекста напоминает сохранить checkpoint в .claude/checkpoint.md
# (gitignored). Read-only для агента — возвращает напоминание через additionalContext.
# see 80-kernel/stele/ADR-0009-claude-machinery-in-dotclaude.md
cat <<'JSON'
{"additionalContext": "⚠️ PRECOMPACT: контекст будет сжат. Прочитай .claude/checkpoint.md если он есть, и запиши в него: (1) над какой задачей работаешь, (2) что осталось сделать, (3) какой ОРЗ-ритуал/скилл выполняешь и на каком шаге, (4) незавершённые шаги, включая верификацию (/verify)."}
JSON
exit 0
