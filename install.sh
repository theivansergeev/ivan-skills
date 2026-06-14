#!/usr/bin/env bash
# Установщик скилла «Распаковка новичка» в Claude Code (VS Code и CLI).
# Кладёт скилл в ~/.claude/skills/ — работает и в расширении VS Code, и в терминале.
set -euo pipefail

REPO="https://github.com/theivansergeev/ivan-skills"
SKILL_NAME="${SKILL_NAME:-raspakovka-novichka}"          # переопределяемо для теста
SRC_PATH="plugins/raspakovka/skills/raspakovka-novichka"
DEST_DIR="$HOME/.claude/skills/$SKILL_NAME"

mkdir -p "$HOME/.claude/skills"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 "$REPO" "$TMP" >/dev/null 2>&1
rm -rf "$DEST_DIR"
cp -r "$TMP/$SRC_PATH" "$DEST_DIR"

echo "✓ Скилл установлен: $DEST_DIR"
echo "  Вызов: напиши Claude «распакуй меня» или команду /$SKILL_NAME"
