#!/usr/bin/env bash
# Hypomnemata — реестр вложенных репозиториев и их развёртывание (INV-1: состояние
# системы восстановимо из чистого клона).
#
# Файл заменил `.gitmodules`. Submodule по построению консервирует версию: указатель
# на ревизию живёт в родителе, и свежесть внешнего репо доезжает до второй машины
# только отдельным коммитом указателя. Внешние источники (лестница принципов и всё,
# что вы допишете в реестр) нужны ПОСТОЯННО СВЕЖИМИ, а не на зафиксированной ревизии, —
# поэтому они держатся обычными вложенными клонами, а машинно-читаемым реестром
# адресов служит список REPOS ниже: `clone` разворачивает отсутствующее на новой
# машине, `pull` обновляет всё разом.
#
# Fail-open — не удобство, а условие применимости: скрипт зовётся из Pull-on-Touch
# в начале работы, и недоступный апстрим (нет сети, нет ключа к приватному репо)
# не имеет права ронять сессию. Отказ по одному репозиторию печатается, работа идёт
# дальше; ненулевой код возвращается, только если не удалось НИЧЕГО.
#
# Корень берётся от расположения самого файла, а не от cwd: скрипт зовут хуком и из
# произвольного каталога.
#
# REPOS_BOOTSTRAP_LIST подменяет список (строки `путь|адрес`) — тем же доводом, что
# ORZ_TODAY в orz-check.sh: без подмены проверить поведение можно лишь против живых
# апстримов, то есть не проверить вовсе, а непроверенный развёртыватель есть
# обещание восстановимости, а не её носитель.
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)

# Реестр: строка `путь-в-vault|адрес`. Каждый путь обязан стоять и в .gitignore —
# контент вложенного репо в git родителя не входит. Строка с `#` — комментарий.
# Лестница принципов — публичные апстримы; свои репозитории дописывайте ниже.
REPOS_DEFAULT='
.principles/zp|https://github.com/TserenTserenov/ZP.git
.principles/fpf|https://github.com/ailev/FPF.git
.principles/spf|https://github.com/TserenTserenov/SPF.git
# 30-knowledge/core|git@github.com:<owner>/<knowledge-core>.git
'
repos=${REPOS_BOOTSTRAP_LIST:-$REPOS_DEFAULT}

mode=${1:-pull}
case "$mode" in
  clone|pull) ;;
  *)
    printf 'usage: %s [clone|pull]\n' "$(basename -- "${BASH_SOURCE[0]}")" >&2
    printf '  clone — развернуть отсутствующие репозитории (существующие не трогает)\n' >&2
    printf '  pull  — обновить существующие (умолчание)\n' >&2
    exit 2
    ;;
esac

# Сеть висит молча, а висящий Pull-on-Touch неотличим от сломанной сессии. Но
# coreutils-таймаута на macOS нет по умолчанию (`gtimeout` из brew — и того может
# не быть), поэтому его отсутствие деградирует до работы без таймаута, а не до
# «command not found», которое читалось бы как отказ самого git.
net_timeout=${REPOS_BOOTSTRAP_TIMEOUT:-120}
timeout_bin=""
for candidate in timeout gtimeout; do
  if command -v "$candidate" >/dev/null 2>&1; then
    timeout_bin=$candidate
    break
  fi
done

run_net() {
  if [ -n "$timeout_bin" ]; then
    "$timeout_bin" "$net_timeout" "$@"
  else
    "$@"
  fi
}

# Из вывода git человеку нужна причина, а не протокол: печатаем ПЕРВУЮ непустую
# строку — в ней живёт «Permission denied (publickey)» либо «repository does not
# exist», тогда как хвост занят вежливым «and the repository exists.», одинаковым
# для всех отказов.
reason() {
  printf '%s' "$1" | grep -v '^[[:space:]]*$' | head -1 | cut -c1-120
}

# Вывод и статус сетевой операции в одном месте: 124 от timeout иначе пришёл бы
# с пустым выводом, то есть отказ по таймауту печатался бы причиной без причины.
out=""
try_net() {
  local st=0
  out=$(run_net "$@" 2>&1) || st=$?
  if [ "$st" -eq 124 ] && [ -n "$timeout_bin" ]; then
    out="превышен таймаут ${net_timeout}s"
  fi
  return "$st"
}

# Гейт pre-commit ставится «один раз на клон», и ничто не проверяло, что это
# случилось: без хука opsec-гард вложенного репо молча пропускается.
# Поэтому clone ставит хук и в свежий клон, и в
# уже развёрнутый. Нет pre-commit — сообщаем и идём дальше: отказ здесь не сетевой,
# но ронять развёртывание из-за него так же нельзя.
pc=$(command -v pre-commit 2>/dev/null || (cd "$root" && mise which pre-commit 2>/dev/null) || true)
ensure_hook() { # $1 = каталог клона, $2 = путь в реестре
  [ -f "$1/.pre-commit-config.yaml" ] || return 0
  local hook
  hook=$(git -C "$1" rev-parse --path-format=absolute --git-path hooks/pre-commit 2>/dev/null) || return 0
  grep -qs 'pre-commit' "$hook" && return 0
  if [ -z "$pc" ]; then
    printf '  ⚠ %s — pre-commit не найден, хук не поставлен → pre-commit install в клоне\n' "$2"
  elif hook_out=$(cd "$1" && "$pc" install 2>&1); then
    printf '  ↳ %s — хук pre-commit поставлен\n' "$2"
  else
    printf '  ⚠ %s — хук pre-commit не поставлен: %s\n' "$2" "$(reason "$hook_out")"
  fi
}

ok=0
failed=0

while IFS='|' read -r rel url; do
  rel=${rel%%[[:space:]]*}
  url=${url%%[[:space:]]*}
  [ -n "$rel" ] || continue
  case "$rel" in \#*) continue ;; esac
  [ -n "$url" ] || { printf '✗ %s — нет адреса в реестре\n' "$rel"; failed=$((failed + 1)); continue; }
  dir="$root/$rel"

  # «Каталог есть» ещё не значит «репозиторий развёрнут»: клон, прерванный на
  # середине (в том числе нашим же таймаутом), оставляет скелет .git без единой
  # ревизии, и rev-parse --git-dir его признаёт. Признаком развёрнутости берём
  # достижимый HEAD — иначе повторный clone вечно печатал бы «уже развёрнут»,
  # а репозиторий не приезжал бы никогда (проверено пробой: kill клона на 3-й
  # секунде, после чего clone стал нерабочим навсегда).
  deployed=0
  if [ -e "$dir/.git" ] && git -C "$dir" rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
    deployed=1
  fi

  if [ "$mode" = clone ]; then
    # Труп оборванного клона убираем сами — его породил наш же таймаут. Условие
    # нарочно узкое: внутри каталога нет ничего, кроме бесплодного .git, то есть
    # удалять нечего, кроме собственного мусора.
    if [ "$deployed" -eq 0 ] && [ -e "$dir/.git" ]; then
      leftovers=$(find "$dir" -mindepth 1 -maxdepth 1 ! -name .git -print -quit 2>/dev/null || true)
      if [ -z "$leftovers" ]; then
        rm -rf "$dir"
      fi
    fi
    if [ "$deployed" -eq 1 ]; then
      printf '· %s — уже развёрнут\n' "$rel"
      ok=$((ok + 1))
      ensure_hook "$dir" "$rel"
    elif [ -d "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null)" ]; then
      printf '✗ %s — каталог занят не репозиторием, руками\n' "$rel"
      failed=$((failed + 1))
    elif mkdir -p "$(dirname -- "$dir")" && try_net git clone --quiet "$url" "$dir"; then
      printf '✓ %s — склонирован из %s\n' "$rel" "$url"
      ok=$((ok + 1))
      ensure_hook "$dir" "$rel"
    else
      printf '✗ %s — клон не удался: %s\n' "$rel" "$(reason "$out")"
      failed=$((failed + 1))
    fi
    continue
  fi

  # Отсутствие каталога в режиме pull — не отказ: на этой машине репозиторий просто
  # ещё не разворачивали. Говорим, чем это лечится, и идём дальше.
  if [ ! -e "$dir/.git" ]; then
    printf '· %s — нет на этой машине → repos-bootstrap.sh clone\n' "$rel"
    continue
  fi
  if [ "$deployed" -eq 0 ]; then
    printf '✗ %s — оборванный клон без ревизий → удалить каталог и repos-bootstrap.sh clone\n' "$rel"
    failed=$((failed + 1))
    continue
  fi
  if try_net git -C "$dir" pull --ff-only --quiet; then
    printf '✓ %s — %s\n' "$rel" "$(git -C "$dir" rev-parse --short HEAD 2>/dev/null || echo '?')"
    ok=$((ok + 1))
  else
    printf '✗ %s — обновить не удалось: %s\n' "$rel" "$(reason "$out")"
    failed=$((failed + 1))
  fi
done <<EOF
$repos
EOF

if [ "$failed" -gt 0 ]; then
  printf '⚠ отказов: %d из %d\n' "$failed" "$((failed + ok))" >&2
fi
# Ненулевой код — только когда не вышло ничего: одиночный отказ есть новость,
# а не повод считать шаг Pull-on-Touch проваленным.
if [ "$ok" -eq 0 ] && [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
