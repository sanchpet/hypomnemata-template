#!/usr/bin/env bash
# Hypomnemata — ADR-0033/ADR-0036: у новой карточки задачи обязана появиться работа в приборе учёта.
# Опционален: нужен Super Productivity с подключённым MCP. Без него — убрать из settings.json.
# PostToolUse на пишущих тулах: если в 10-governance/6-tasks/ появилась карточка,
# которой ещё нет в git, — печатает модели напоминание завести работу через MCP.
# Кратность 1:N (ADR-0036 п.5): в приборе живут работы, у задачи их может быть несколько.
#
# Карточку ищем НЕ по аргументам тула, а спрашивая git, что в каталоге задач не под версией
# (`ls-files --others`). Первая редакция хука разбирала tool_input.file_path и потому
# видела только Write/Edit — а карточки в этом vault заводятся `cat > файл <<'EOF'`,
# где пути в аргументах нет вовсе. Хук промолчал на двух реальных заведениях подряд.
# Опрос git от инструмента не зависит: heredoc, sed -i, python, Write — всё равно.
# Он же снимает ложные срабатывания на чтении: grep/cat/ls файла не создают.
#
# Хук САМ в Super Productivity не ходит и его протокола не знает: он только триггер.
# Работу заводит модель вызовом mcp__super-productivity__create_task — отсюда нулевое
# сцепление с чужим форматом (INV-18 build-vs-adopt) и никакого холодного старта npx.
#
# Канал до модели — JSON `hookSpecificOutput.additionalContext`. Он проверен пробой
# (Claude Code 2.1.260): голый stdout при exit 0 до модели НЕ доходит, exit 2 доходит,
# но как «blocking error» — а напоминание не должно ронять сессию. Любой отказ → тихий exit 0.
# see 80-kernel/stele/ADR-0033-wp-mirrored-in-time-tracker.md · ADR-0036-task-as-atomic-card.md

input=$(cat)
[ -n "$CLAUDE_PROJECT_DIR" ] || exit 0

session=$(printf '%s' "$input" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('session_id', '') or 'nosess')
except Exception:
    print('nosess')
" 2>/dev/null)
[ -n "$session" ] || session=nosess

# Карточки, которых ещё нет в git, — значит заводятся прямо сейчас. Отсутствие работ
# у старых, уже закоммиченных карточек ловит детектор на стратегировании, не хук.
#
# Шаблон без второго слэша отсекает 10-governance/6-tasks/archive/: перенос
# закрытой задачи в архив есть та же «некоммиченная карточка», но работа ей не нужна.
new_cards=$(git -C "$CLAUDE_PROJECT_DIR" ls-files --others --exclude-standard \
  -- 10-governance/6-tasks/ 2>/dev/null \
  | grep -E '^10-governance/6-tasks/[Tt]-[0-9]+[^/]*\.md$')
[ -n "$new_cards" ] || exit 0

# Одно напоминание на карточку за сессию: заведение — это запись плюс несколько правок,
# и повторять на каждую было бы шумом, который учатся пролистывать.
stamp_dir="${TMPDIR:-/tmp}/hypomnemata-task-mirror"
mkdir -p "$stamp_dir" 2>/dev/null || exit 0

pending=""
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  card=$(basename "$rel")
  tnum=$(printf '%s' "$card" | sed -n 's/^[Tt]-0*\([0-9]\{1,4\}\).*/\1/p')
  [ -n "$tnum" ] || continue

  # «Некоммиченная карточка» ≠ «новая активная задача». Закрытая или снятая задача
  # работы не требует: она не заводится, а уходит. Без этой проверки хук
  # трижды подряд доложил про архивацию и снятие как про заведение.
  status=$(awk '/^---$/{n++; next} n==1 && /^status:/{sub(/^status:[ ]*/,""); gsub(/["'"'"']/,""); print tolower($0); exit}' \
    "$CLAUDE_PROJECT_DIR/$rel" 2>/dev/null | tr -d ' ')
  case "$status" in
    done|closed|dropped|later) continue ;;
  esac
  stamp="$stamp_dir/${session}-${tnum}"
  [ -e "$stamp" ] && continue
  : > "$stamp" 2>/dev/null || continue
  pending="${pending}${tnum}|${card}"$'\n'
done <<EOF
$new_cards
EOF

[ -n "$pending" ] || exit 0

# Тег инвестированного времени — id объекта в вашем приборе, задаётся в config.md
# строкой `sp_invested_tag: <id>`; без него строка про тег в напоминание не идёт.
invested_tag=$(grep -m1 -oE 'sp_invested_tag:[[:space:]]*[A-Za-z0-9_-]+' \
  "$CLAUDE_PROJECT_DIR/80-kernel/config.md" 2>/dev/null | sed -E 's/.*:[[:space:]]*//')

printf '%s' "$pending" | INVESTED_TAG="$invested_tag" python3 -c "
import os, sys, json

cards = []
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    num, _, name = line.partition('|')
    cards.append((f'{int(num):03d}', name))  # T-007, не T-7
if not cards:
    sys.exit(0)

listed = '\n'.join(f'  T-{n} — {name}' for n, name in cards)
head = ('Карточка задачи заводится впервые (ещё не в git):' if len(cards) == 1
        else 'Карточки задач заводятся впервые (ещё не в git):')
first = cards[0][0]
tag = os.environ.get('INVESTED_TAG', '')
tag_line = (f'  tag_ids: [\"{tag}\"] (тег инвестированного времени) — если работа идёт в '
            f'инвестированное время, а не в текучку.\n') if tag else ''

msg = (
    f'{head}\n{listed}\n\n'
    f'По ADR-0033/ADR-0036 у задачи, взятой в юнит, обязана быть хотя бы одна работа '
    f'в Super Productivity — иначе физическое время по ней списывать некуда (INV-15).\n'
    f'Заведи её: mcp__super-productivity__create_task — по одной на каждую '
    f'сформулированную работу (когда, в каком порядке, в какой день).\n'
    f'  title: \`T-{first} — <формулировка работы>\` — префикс T-NNN несущий, по нему '
    f'детектор находит работы задачи;\n'
    f'  project_id: проект-зеркало из поля \`project:\` карточки (ADR-0031, 1:1 с реестром; '
    f'узнать — get_projects);\n'
    f'  time_estimate: бюджет работы в миллисекундах (1 ч = 3600000); сумма работ '
    f'сходится с \`budget_h\` карточки;\n'
    f'{tag_line}'
    f'Если работы уже заведены — пропусти. В карточку id задачи НЕ пишем: обратная '
    f'запись в файл, за которым следит этот хук, дала бы петлю.'
)
print(json.dumps({'hookSpecificOutput': {
    'hookEventName': 'PostToolUse',
    'additionalContext': msg,
}}, ensure_ascii=False))
" 2>/dev/null

exit 0
