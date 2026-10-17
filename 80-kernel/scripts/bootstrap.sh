#!/usr/bin/env bash
# Hypomnemata bootstrap — одноразовая настройка свежего клона vault.
# Ставит git-гейты через pre-commit framework (pinned в mise.toml) + права на скрипты.
# Claude-хуки (settings.json) и память (autoMemoryDirectory) поднимаются сами.
# Запуск: bash 80-kernel/scripts/bootstrap.sh   (см. ADR-0019)
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"

mise install                                       # ставит pre-commit (postinstall → pre-commit install)
mise exec -- pre-commit install --install-hooks    # идемпотентно — добивка, если postinstall не сработал
chmod +x .claude/hooks/*.sh 80-kernel/scripts/*.sh 80-kernel/scripts/*.py 2>/dev/null || true

# Внешние репозитории (ADR-0038): лестница принципов и всё, что вы допишете в реестр.
# Строка «склонируй вот это» в README забывается; реестр адресов исполняемый,
# и звать его должен сам bootstrap, а не память человека.
bash 80-kernel/scripts/repos-bootstrap.sh clone || true

echo "✓ git-гейты pre-commit поставлены (.pre-commit-config.yaml)"
echo "✓ права на хуки/скрипты выставлены"
echo "✓ внешние репозитории развёрнуты (repos-bootstrap.sh clone)"
echo "✓ Claude-хуки и память — из settings.json, автоматически"
echo "Готово. Vault настроен."
