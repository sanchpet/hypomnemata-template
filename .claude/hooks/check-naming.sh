#!/usr/bin/env bash
# Базовый хук Hypomnemata — enforce ADR-0006 (имена файлов).
# PreToolUse на Write|Edit|MultiEdit: блокирует создание/правку файла
# с пробелами, кириллицей или произвольным верхним регистром в имени.
# Разрешено: опциональный ЗАГЛАВНЫЙ инвентарный префикс (T-001-/DIR-1-/DIS-1-/
# P01-/ADR-0014-) + строчная смысловая часть. Инв.номер читается отдельно от имени.
# Человекочитаемость — через aliases во frontmatter, не через имя файла.
#
# Два интерфейса, одно правило (как у task-artifact-check.py):
#   • пути аргументами — проверяет каждый, печатает все нарушения (батч для
#     PostToolUse-стража post-write-guard.sh, где путей много, а python дорог);
#   • JSON хука на stdin — прежнее поведение PreToolUse (блок на первом же).
# Правило живёт здесь в единственном экземпляре: две копии разъедутся (ADR-0034).
# see 80-kernel/stele/ADR-0006-naming-convention.md, ADR-0034-enforcement-independent-of-tool.md

# Возвращает 0, если имя годное; иначе печатает причину в stderr и возвращает 1.
check_one() {
  local rel=$1 base

  # dot-зона и сторонние конфиги — не наши имена, пропускаем
  case "$rel" in
    .obsidian/*|.git/*|.repos/*|.resources/*|.principles/*) return 0 ;;
    # Вложения выведены из-под правила (ADR-0006): блобы адресуются ссылкой,
    # имя у них служебное, а порождают его Obsidian и Excalidraw жёстко — настройки нет.
    80-kernel/attachments/*) return 0 ;;
  esac

  base=$(basename "$rel")

  # uppercase tooling-токены — исключения ADR-0006
  case "$base" in
    README.md|LICENSE|CLAUDE.md|MEMORY.md|SKILL.md) return 0 ;;
  esac

  # опциональный заглавный инвентарный префикс + строчная смысловая часть
  if ! printf '%s' "$base" | grep -qE '^([A-Z]+-?[0-9]+-)?[a-z0-9._-]+$'; then
    echo "ADR-0006: имя — строчная латиница без пробелов/кириллицы; допускается лишь ЗАГЛАВНЫЙ инвентарный префикс (T-001-, DIR-1-, P01-, ADR-0014-). Получено: '$base'. Человекочитаемость — через aliases." >&2
    return 1
  fi
  return 0
}

# --- батч по аргументам ---
if [ $# -gt 0 ]; then
  rc=0
  for p in "$@"; do
    [ -n "$p" ] || continue
    check_one "${p#"$CLAUDE_PROJECT_DIR"/}" || rc=2
  done
  exit $rc
fi

# --- одиночная проверка из JSON хука ---
input=$(cat)
path=$(printf '%s' "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
[ -z "$path" ] && exit 0

check_one "${path#"$CLAUDE_PROJECT_DIR"/}" || exit 2
exit 0
