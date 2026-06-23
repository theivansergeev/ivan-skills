#!/usr/bin/env bash
# Установщик скилла «Распаковка новичка» в Claude Code (VS Code и CLI).
# Кладёт скилл в ~/.claude/skills/ — работает и в расширении VS Code, и в терминале.
# Не требует git: качает архив репозитория через curl + tar.
set -euo pipefail

OWNER="theivansergeev"
REPO="ivan-skills"
BRANCH="main"
SKILL_NAME="${SKILL_NAME:-raspakovka-novichka}"          # переопределяемо для теста
SRC_PATH="plugins/raspakovka/skills/raspakovka-novichka"
DEST_DIR="$HOME/.claude/skills/$SKILL_NAME"

mkdir -p "$HOME/.claude/skills"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

TARBALL="https://codeload.github.com/$OWNER/$REPO/tar.gz/refs/heads/$BRANCH"
if ! curl -fsSL "$TARBALL" | tar -xz -C "$TMP" 2>/dev/null; then
  echo "✗ Не удалось скачать скилл. Проверь интернет и попробуй ещё раз." >&2
  exit 1
fi

SRC="$TMP/$REPO-$BRANCH/$SRC_PATH"
if [ ! -d "$SRC" ]; then
  echo "✗ В архиве не найден скилл ($SRC_PATH)." >&2
  exit 1
fi

rm -rf "$DEST_DIR"
cp -r "$SRC" "$DEST_DIR"

echo "✓ Скилл установлен: $DEST_DIR"
echo "  Вызов: напиши Claude «распакуй меня» или команду /$SKILL_NAME"
