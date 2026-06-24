#!/usr/bin/env bash
# Verification gate для reel-to-script (Stage 13). Прогоняет ВСЕ проверки разом.
# exit 0 = можно заявлять «готово». exit 1 = НЕ готово, что-то red.
#
# Зачем: за сессию 22.06.2026 внешний хук code-done-needs-verification ловил «готово» без
# прогона. Иван: «всегда их в скилле внеси». Теперь скилл сам себя верифицирует ДО выдачи.
#
# Usage: bash scripts/verify.sh        (e2e на /tmp/wave580.mp4 если есть, иначе SKIP)
#        REEL_TEST=/path/to.mp4 bash scripts/verify.sh   (e2e на своём ролике)
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SKILL_DIR" || { echo "no skill dir"; exit 2; }
FAIL=0
note(){ printf '  %-26s %s\n' "$1" "$2"; }

echo "=== reel-to-script verify gate ==="

# 1. Синтаксис всех bash-скриптов
for s in scripts/*.sh; do
  [ "$s" = "scripts/verify.sh" ] && continue
  if bash -n "$s" 2>/dev/null; then note "syntax $(basename "$s")" "OK"; else note "syntax $(basename "$s")" "FAIL"; FAIL=1; fi
done

# 2. L1 frontmatter (name + description 80-500)
if python3 - <<'PY' 2>/dev/null
import re,yaml
s=open('SKILL.md').read()
m=re.match(r'^---\n(.*?)\n---',s,re.DOTALL); assert m
fm=yaml.safe_load(m.group(1))
assert fm['name']=='reel-to-script'
d=len(fm['description']); assert 80<=d<=500
PY
then note "L1 frontmatter" "OK"; else note "L1 frontmatter" "FAIL"; FAIL=1; fi

# 3. em-dash 0 (правило проекта no-long-dashes)
N=$(grep -rn '—' . 2>/dev/null | grep -v 'verify.sh' | wc -l | tr -d ' ')
if [ "$N" = "0" ]; then note "em-dash" "OK (0)"; else note "em-dash" "FAIL ($N)"; FAIL=1; fi

# 4. Cross-refs из SKILL.md существуют
MISS=0
for f in $(grep -rohE '(prompts|knowledge|scripts|examples)/[A-Za-z0-9._-]+' SKILL.md 2>/dev/null | sort -u); do
  [ -e "$f" ] || { note "ref $f" "MISSING"; MISS=1; FAIL=1; }
done
[ "$MISS" = "0" ] && note "cross-refs" "OK"

# 5. L6 защита присутствует (опасная тройка / prompt-injection)
if grep -q 'опасная тройка' SKILL.md && grep -q 'ДАННЫЕ' prompts/02-signal-extraction.md; then
  note "L6 prompt-injection" "OK"; else note "L6 prompt-injection" "FAIL"; FAIL=1; fi

# 6. Ключевые принципы на месте (один промпт / потолок 15с / референс)
for rule in 'Один промпт ВСЕГДА' 'потолок' 'по референсу'; do
  if grep -q "${rule}" SKILL.md; then note "rule: ${rule}" "OK"; else note "rule: ${rule}" "FAIL"; FAIL=1; fi
done

# 7. e2e на реальном ролике (опционально)
REEL="${REEL_TEST:-/tmp/wave580.mp4}"
if [ -f "$REEL" ]; then
  if bash scripts/dense-frames.sh "$REEL" /tmp/r2s-verify-gate >/dev/null 2>&1 \
     && [ -n "$(ls /tmp/r2s-verify-gate/sheet_*.jpg 2>/dev/null)" ]; then
    note "e2e dense-frames" "OK ($(ls /tmp/r2s-verify-gate/sheet_*.jpg 2>/dev/null | wc -l | tr -d ' ') sheets)"
  else note "e2e dense-frames" "FAIL"; FAIL=1; fi
else
  note "e2e dense-frames" "SKIP (no $REEL)"
fi

echo
if [ "$FAIL" = "0" ]; then echo "VERIFY: PASS (exit 0)"; exit 0
else echo "VERIFY: FAIL (exit 1) - НЕ заявлять готово, чинить red выше"; exit 1; fi