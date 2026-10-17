#!/usr/bin/env bash
# ОРЗ-детектор (INV-5 / INV-10 / INV-17 «система-как-код»).
# Носитель «пропуск Close/стратегирования ДЕТЕКТИРУЕТСЯ»: запускается SessionStart-хуком
# (каждый старт сессии) + шагом 0 в /open. Печатает флаги ТОЛЬКО при отклонениях
# (тихо, если всё закрыто) — детект, не блок. Логика тонкая, скиллы не утяжеляет.
set -euo pipefail

root=$(git -C "${CLAUDE_PROJECT_DIR:-$PWD}" rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" 2>/dev/null || exit 0

# ORZ_TODAY подменяет дату — без него ветки рамки нельзя проверить на способность
# краснеть, а непроверенный гейт есть обещание, а не сторож (INV-17).
today=${ORZ_TODAY:-$(date +%Y-%m-%d)}
_dref() { date -j -f '%Y-%m-%d %H' "$today 12" "+$1" 2>/dev/null || date -d "$today 12:00" "+$1" 2>/dev/null; }
dow=$(_dref %u)         # день недели 1=Пн … 7=Вс
flags=()
shopt -s nullglob

# День стратегирования из config.md (секция «Ритм»). Substring-match — без
# Cyrillic-классов, чтобы не зависеть от локали. Дефолт: понедельник.
sline=$(grep -i 'strategy_day:' 80-kernel/config.md 2>/dev/null | head -1)
case "$sline" in
  *понедельник*) sday=1; sname=понедельник ;;
  *вторник*)     sday=2; sname=вторник ;;
  *среда*)       sday=3; sname=среда ;;
  *четверг*)     sday=4; sname=четверг ;;
  *пятниц*)      sday=5; sname=пятница ;;
  *суббот*)      sday=6; sname=суббота ;;
  *воскресень*)  sday=7; sname=воскресенье ;;
  *)             sday=1; sname=понедельник ;;
esac

# 1. INV-9/INV-5: незакрытый день — DayPlan прошлого дня остался в current/ (Close его архивирует)
for f in 10-governance/7-plans/current/dayplan-*.md; do
  d=$(basename "$f" | sed -E 's/dayplan-([0-9-]+)\.md/\1/')
  [ "$d" \< "$today" ] && flags+=("день $d не закрыт (DayPlan не в архиве) → /close")
done

# ── Положение в рамке: спринт, юнит, режим сессии (ADR-0037) ─────────────────
# sprint_epoch ЧИТАЕТСЯ из config.md и НЕ дублируется здесь. Прежний месячный
# параметр детектор не читал вовсе — вычислял дату сам, — и потому правка
# конфига ничего не меняла, а пропуск сессии был бесшумен пять недель.
# Полдень в парсинге дат — чтобы прибавление суток не ловило перевод часов.
d2s()  { date -j -f '%Y-%m-%d %H' "$1 12" +%s 2>/dev/null || date -d "$1 12:00" +%s 2>/dev/null; }
sfmt() { date -r "$1" "+$2" 2>/dev/null || date -d "@$1" "+$2" 2>/dev/null; }

WEEK=604800
CYCLE=13                # 12 недель спринта + разгрузочная

# Имя юнита по индексу внутри спринта (0..5): YYYY-wNN-wMM по его двум неделям.
unit_name() { # $1 = индекс юнита, $2 = понедельник первой недели спринта
  local m=$(( $2 + $1 * 2 * WEEK ))
  echo "$(sfmt "$m" '%G')-w$(sfmt "$m" '%V')-w$(sfmt $(( m + WEEK )) '%V')"
}
# Файл периода: ищется и с ведущим нулём, и без него — исторические имена
# писались как YYYY-wNN без выравнивания.
have_file() { # $1 = каталог, $2 = основа имени, $3 = суффикс
  local f
  for f in "$1/$2-$3"*.md $(echo "$1/$2-$3"*.md | sed 's/-w0/-w/g'); do
    [ -f "$f" ] && return 0
  done
  return 1
}

ep=$(grep -m1 'sprint_epoch:' 80-kernel/config.md 2>/dev/null \
     | sed -nE 's/.*sprint_epoch:[^0-9]*([0-9]{4})-[Ww]([0-9]{1,2}).*/\1 \2/p')
pos=-99
# Незаданная эпоха гасит все ветки рамки — без флага детектор врал бы зелёным.
[ -n "$ep" ] || flags+=("sprint_epoch не задан или не разобран в 80-kernel/config.md → ветки спринта и юнита молчат; задайте ISO-неделю YYYY-Www (ADR-0037)")
if [ -n "$ep" ]; then
  ep_yr=${ep% *}; ep_wk=${ep#* }
  # Понедельник ISO-недели эпохи: 4 января всегда лежит в W01.
  j4=$(d2s "$ep_yr-01-04"); u4=$(sfmt "$j4" '%u')
  ep_mon=$(( j4 - (u4 - 1) * 86400 + (10#$ep_wk - 1) * WEEK ))
  cur_mon=$(( $(d2s "$today") - (dow - 1) * 86400 ))
  weeks=$(( (cur_mon - ep_mon) / WEEK ))
  if [ "$weeks" -lt 0 ]; then
    pos=-1
    # День стратегирования последней недели перед эпохой играет роль дня разгрузочной:
    # она и открывает первый спринт. Без этой ветки детектор молчал бы ровно
    # в тот день, ради которого рамка заводилась.
    if [ "$weeks" -eq -1 ] && [ "$dow" -eq "$sday" ]; then
      sp_yr=$(sfmt "$ep_mon" '%G'); sp_fw=$(sfmt "$ep_mon" '%V')
      first_sp="$sp_yr-s$(( (10#$sp_fw - 1) / 13 + 1 ))"
      first_u="$(sfmt "$ep_mon" '%G')-w$(sfmt "$ep_mon" '%V')-w$(sfmt $(( ep_mon + WEEK )) '%V')"
      have_file 10-governance/7-plans/current "$first_sp" sprintplan         || flags+=("сегодня $sname — открытие первого спринта $first_sp, SprintPlan ещё нет → /strategize (INV-9)")
      have_file 10-governance/7-plans/current "$first_u" unitplan         || flags+=("нет UnitPlan на первый юнит $first_u → /strategize, режим «открытие спринта» (INV-10)")
    fi
    pre_msg="рамка спринтов стартует $ep_yr-W$ep_wk, через $(( -weeks )) нед. — текущий период идёт вне спринта"
  else
    sp_idx=$(( weeks / CYCLE ))
    pos=$(( weeks % CYCLE ))
    sp_mon=$(( ep_mon + sp_idx * CYCLE * WEEK ))
    sp_yr=$(sfmt "$sp_mon" '%G'); sp_fw=$(sfmt "$sp_mon" '%V')
    sprint="$sp_yr-s$(( (10#$sp_fw - 1) / 13 + 1 ))"
  fi
fi

if [ "$pos" -ge 0 ]; then
  # 2. INV-10: нет UnitPlan на текущий (в день открытия — на следующий) юнит.
  # Look-ahead держится того же довода, что прежняя недельная ветка: сессия
  # верстает вперёд, и без него пропуск сессии всплыл бы только на следующей неделе.
  if [ "$pos" -lt 12 ]; then
    u_idx=$(( pos / 2 )); u_half=$(( pos % 2 ))
    tgt_u=-1
    if [ "$dow" -eq "$sday" ] && [ "$u_half" -eq 1 ] && [ "$pos" -lt 11 ]; then
      tgt_u=$(( u_idx + 1 ))      # сессия закрытия юнита верстает следующий
    elif [ "$dow" -ne "$sday" ] || [ "$u_half" -eq 0 ]; then
      tgt_u=$u_idx
    fi
    if [ "$tgt_u" -ge 0 ]; then
      tu=$(unit_name "$tgt_u" "$sp_mon")
      have_file 10-governance/7-plans/current "$tu" unitplan \
        || flags+=("нет UnitPlan на юнит $tu → /strategize, режим «открытие юнита» (INV-10)")
    fi
  fi

  # 3. INV-9 масштаб «спринт»: нет SprintPlan. В разгрузочную неделю цель —
  # следующий спринт: её день стратегирования и есть открытие.
  if [ "$pos" -eq 12 ]; then
    nx_mon=$(( sp_mon + CYCLE * WEEK ))
    nx="$(sfmt "$nx_mon" '%G')-s$(( (10#$(sfmt "$nx_mon" '%V') - 1) / 13 + 1 ))"
    have_file 10-governance/7-plans/current "$nx" sprintplan \
      || flags+=("разгрузочная неделя — SprintPlan на $nx ещё нет → /strategize, режим «открытие спринта» (INV-9)")
    have_file 10-governance/7-plans/archive "$sprint" sprintreport \
      || flags+=("нет SprintReport за $sprint → свод спринта обязан быть отдельным файлом 7-plans/archive/$sprint-sprintreport.md (INV-10)")
  else
    have_file 10-governance/7-plans/current "$sprint" sprintplan \
      || flags+=("нет SprintPlan на спринт $sprint (идёт неделя $(( pos + 1 ))/12) → /strategize, режим «открытие спринта» (INV-9)")
  fi

  # 4. INV-10: нет UnitReport за прошедший юнит. Юнит кончается на чётной неделе,
  # значит с первой недели следующего его свод обязан существовать.
  prev_u=-1
  if [ "$pos" -eq 12 ]; then prev_u=5
  elif [ "$pos" -ge 2 ] && [ $(( pos % 2 )) -eq 0 ]; then prev_u=$(( pos / 2 - 1 )); fi
  if [ "$prev_u" -ge 0 ]; then
    pu=$(unit_name "$prev_u" "$sp_mon")
    have_file 10-governance/7-plans/archive "$pu" unitreport \
      || flags+=("нет UnitReport за юнит $pu → свод обязан назвать, взяты ли три главных результата (INV-10)")
  fi
fi

# 5. Карточки задач, чей назначенный срок наступил: awaiting <= сегодня.
# Поле возвращает карточку на активную доску само (start.md), но доску надо открыть;
# вернувшаяся задача легко вытесняется по ёмкости — флаг делает возврат слышимым.
for f in 10-governance/6-tasks/T-*.md; do
  aw=$(grep -m1 '^awaiting:' "$f" 2>/dev/null | sed 's/awaiting: *//;s/ *$//' || true)
  [ -z "$aw" ] && continue
  if [ ! "$today" \< "$aw" ]; then
    flags+=("$(basename "$f" .md): назначенный срок ($aw) наступил → предъявить на сессии")
  fi
done

# 6. INV-10: нет WeekReport за ПРОШЕДШУЮ ISO-неделю.
# Свод пишется сессией той недели, которую сводит; к следующей неделе он обязан
# существовать ОТДЕЛЬНЫМ файлом `7-plans/archive/YYYY-wNN-weekreport.md`.
# У автора три свода подряд осели разделами внутри СЛЕДУЮЩЕГО плана — и стали
# невидимы и для dataview, и для сводов старшего масштаба: недели просто не было
# в ряду. Скелет weekreport-tmpl.md об этом предупреждал прямым текстом, и
# предупреждение нарушили дважды после того, как его написали, — значит носителем
# правила обязан быть детектор, а не абзац в шаблоне (INV-17).
# Проверяется прошлая неделя, не текущая: сегодняшняя сессия свой свод ещё пишет.
# От $today, а не от часов машины: иначе ORZ_TODAY не доходит до этой ветки.
prev=$(sfmt $(( $(d2s "$today") - WEEK )) '%G %V' || true)
if [ -n "$prev" ]; then
  p_yr=${prev% *}; p_wk=${prev#* }
  have_wr=0
  for f in 10-governance/7-plans/archive/"$p_yr"-w"$p_wk"-weekreport*.md \
           10-governance/7-plans/archive/"$p_yr-w$((10#$p_wk))"-weekreport*.md; do
    [ -f "$f" ] && have_wr=1
  done
  if [ "$have_wr" -eq 0 ]; then
    flags+=("нет WeekReport за $p_yr-W$p_wk → свод обязан быть ОТДЕЛЬНЫМ файлом 7-plans/archive/$p_yr-w$p_wk-weekreport.md с type: weekreport, а не разделом внутри другого плана (INV-10)")
  fi
fi

# 7. Приоритет проектов не назначен (руководство МИМ по саморазвитию: приоритет проектов).
# Отбор задач периода идёт ВНУТРИ приоритетных проектов: без порядка на проектах
# шаг 9 опирается на суждение в моменте — у автора так план периода однажды вышел
# без раздела задач при пятнадцати активных.
# Проверяются активные карточки проектов (`status: active`) на поле `priority:`.
# Порог «сколько проектов считать приоритетными» здесь НЕ проверяется — это решение
# сессии; детектор ловит отсутствие оценки, а не её величину.
noprio=(); total=0
for f in 10-governance/5-projects/*/P*.md; do
  [ -f "$f" ] || continue
  grep -qE '^status: *active' "$f" 2>/dev/null || continue
  total=$((total + 1))
  grep -qE '^priority: *[0-9]+' "$f" 2>/dev/null || noprio+=("$(basename "$f" .md)")
done
if [ "$total" -gt 0 ] && [ ${#noprio[@]} -gt 0 ]; then
  if [ ${#noprio[@]} -eq "$total" ]; then
    flags+=("приоритет не назначен ни одному из $total активных проектов → шаг 4 сессии (поле priority: 1-10, investment: true у инвестиционных)")
  else
    flags+=("без приоритета ${#noprio[@]} из $total активных проектов: ${noprio[*]} → шаг 4 сессии")
  fi
fi

# 8. Отметка юнита протухла.
# Стартовая показывает только работы текущего юнита — карточки с полем `unit`,
# равным имени открытого UnitPlan. Карточка, оставшаяся помеченной прошлым юнитом,
# исчезает из списка молча: она не закрыта, не переназначена и никому не видна.
# Текущий юнит берётся из ИМЕНИ файла UnitPlan в plans/current/: у юнита
# есть собственный артефакт (ADR-0037), и он же его называет. Прежде истина жила
# в фильтре board.base — в настройке вида, которую надо было править руками каждые
# две недели. Тот же источник читает start.md; два списка разъехались бы тихо.
cur_unit=""
for f in 10-governance/7-plans/current/*-unitplan.md; do
  [ -f "$f" ] && cur_unit=$(basename "$f" -unitplan.md)
done
if [ -n "$cur_unit" ]; then
  stale=()
  for f in 10-governance/6-tasks/T-*.md; do
    [ -f "$f" ] || continue
    u=$(grep -m1 '^unit:' "$f" 2>/dev/null | sed 's/unit: *//;s/ *$//' || true)
    [ -z "$u" ] && continue
    [ "$u" = "$cur_unit" ] && continue
    stale+=("$(basename "$f" .md) ($u)")
  done
  if [ ${#stale[@]} -gt 0 ]; then
    flags+=("отметка юнита протухла у ${#stale[@]} карточек: ${stale[*]} — текущий юнит $cur_unit; снять поле либо переназначить на шаге 9")
  fi
fi

# 9. Потолок памяти (ADR-0010). Без счётчика порог был обещанием: индекс однажды
# стоял на 59 из 60, и следующая запись перешла бы его молча.
# Индекс режется по символам, поэтому и меряем символы — локаль задана явно, под C
# `wc -m` считает байты. ORZ_MEM_* подменяют каталог и пороги для проверки на краснение.
mem_dir=${ORZ_MEM_DIR:-70-memory}
mem_max_entries=${ORZ_MEM_MAX_ENTRIES:-60}
mem_max_chars=${ORZ_MEM_MAX_CHARS:-8700}
if [ -f "$mem_dir/MEMORY.md" ]; then
  mem_entries=0
  for f in "$mem_dir"/*.md; do
    [ "$(basename "$f")" = MEMORY.md ] || mem_entries=$((mem_entries + 1))
  done
  mem_chars=$(LC_ALL=en_US.UTF-8 wc -m < "$mem_dir/MEMORY.md" | tr -d ' ')
  if [ "$mem_entries" -gt "$mem_max_entries" ] || [ "$mem_chars" -gt "$mem_max_chars" ]; then
    flags+=("память за порогом: $mem_entries записей (≤$mem_max_entries), индекс $mem_chars символов (≤$mem_max_chars) → ревизия на ближайшем стратегировании (ADR-0010)")
  fi
fi

# 10. Лоток пережил свою сессию (ADR-0032 п.5). Хук tray-outcome ловит
# лоток, уходящий в архив без исходов, но лоток, не ушедший вовсе, ему не виден:
# так лоток снятой каденции пролежал в review/ без сессии, которая его читает.
# Срок — день стратегирования последней недели периода (юнит, старая неделя)
# либо 12-й недели спринта. ORZ_REVIEW_DIR подменяет каталог для проверки на краснение.
review_dir=${ORZ_REVIEW_DIR:-10-governance/7-plans/review}
iso_day() { # $1 = ISO-год, $2 = ISO-неделя, $3 = день недели 1..7 → epoch-секунды
  local j4 u4; j4=$(d2s "$1-01-04"); u4=$(sfmt "$j4" '%u')
  echo $(( j4 - (u4 - 1) * 86400 + (10#$2 - 1) * WEEK + ($3 - 1) * 86400 ))
}
today_s=$(d2s "$today")
for f in "$review_dir"/*forreview*.md; do
  b=$(basename "$f" .md); due=""
  if [[ "$b" =~ ^([0-9]{4})-w([0-9]{1,2})(-w([0-9]{1,2}))?-forreview ]]; then
    t_yr=${BASH_REMATCH[1]}; t_wk=${BASH_REMATCH[4]:-${BASH_REMATCH[2]}}
    [ "$((10#$t_wk))" -lt "$((10#${BASH_REMATCH[2]}))" ] && t_yr=$((t_yr + 1))
    due=$(iso_day "$t_yr" "$t_wk" "$sday")
  elif [[ "$b" =~ ^([0-9]{4}-s[0-9]+)-forreview ]] && [ -n "${ep_mon:-}" ]; then
    for k in 0 1 2 3 4 5 6 7 8; do
      m=$(( ep_mon + k * CYCLE * WEEK ))
      [ "$(sfmt "$m" '%G')-s$(( (10#$(sfmt "$m" '%V') - 1) / 13 + 1 ))" = "${BASH_REMATCH[1]}" ] || continue
      due=$(( m + 11 * WEEK + (sday - 1) * 86400 )); break
    done
  fi
  if [ -z "$due" ]; then
    flags+=("лоток $b: период не распознан по имени — каденций две, юнит и спринт → слить и убрать в 7-plans/archive/")
  elif [ "$today_s" -gt "$due" ]; then
    flags+=("лоток $b пережил свою сессию ($(sfmt "$due" '%Y-%m-%d')) и не слит → исходы строкам и перенос в 7-plans/archive/ (ADR-0032 п.5)")
  fi
done

# Положение печатается ВСЕГДА, даже когда рубежи закрыты: режим сессии есть
# скрытая величина, и невидимая она возвращает систему к тому, от чего ушли —
# к рамке, которую надо держать в голове (ArchGate, характеристика «Обучаемость»).
if [ "$pos" -eq -1 ] && [ -n "${pre_msg:-}" ]; then
  echo "📍 $pre_msg"
fi
if [ "$pos" -ge 0 ]; then
  if [ "$pos" -eq 12 ]; then
    echo "📍 $sprint пройден · разгрузочная неделя · $sname: открытие следующего спринта"
  else
    u_idx=$(( pos / 2 ))
    echo "📍 $sprint · неделя $(( pos + 1 ))/12 · юнит $(unit_name "$u_idx" "$sp_mon") ($(( pos % 2 + 1 ))-я) · $sname: $( [ "$pos" -eq 11 ] && echo "закрытие спринта" || { [ $(( pos % 2 )) -eq 1 ] && echo "закрытие юнита + открытие следующего" || echo "сверка остатка"; } )"
  fi
fi

if [ ${#flags[@]} -gt 0 ]; then
  echo "⚠ ОРЗ-детектор (INV-5/10): незакрытые рубежи ритма —"
  for fl in "${flags[@]}"; do echo "  • $fl"; done
fi
exit 0
