---
name: вайбкодинг
description: Use when building a feature, refactoring, fixing a complex bug, changing architecture, or starting any non-trivial coding task. 12-stage verified dev workflow from research to deploy.
---

# Вайбкодинг — Adaptive Development Workflow

> **Author:** Ivan Sergeev @theivansergeevofficial
> **Version:** latest
> **License:** intellectual property

## Core Principle

**Code to solve problems, not code for code's sake.**

Before EVERY change ask: "Does this actually solve our problem? Is this the most efficient solution?"
If the answer isn't clear — stop, research alternatives, pick the best one.

### 4 Behavioral Rules (Karpathy)

The 12 stages enforce these behaviors. Internalize them — they apply to every change.

1. **Think Before Coding** — State assumptions explicitly. Present multiple interpretations instead of picking silently. Push back when a simpler approach exists. Stop and ask when something is unclear. *(Enforced by Stage 1 Research + Stage 3 Challenge Loop.)*

2. **Simplicity First** — No features beyond what was asked. No abstractions for single-use code. No "flexibility" or "configurability" not requested. No error handling for impossible scenarios. If 200 lines could be 50, rewrite. *(Enforced by Core Principle + Stage 3 Challenge Q3 "code for code's sake".)*

3. **Surgical Changes** — Touch only what the user asked for. Don't refactor adjacent code. Match existing style even if you'd do it differently. Drive-by improvements = separate task. Remove only orphans YOUR changes created. *(Enforced by Stage 5 Self-Audit + Stage 7 Impact Analysis.)*

4. **Goal-Driven Execution** — Transform tasks into verifiable success criteria (write tests that fail → make them pass). Loop until verified. Weak criteria like "make it work" require constant clarification. *(Enforced by Stage 4 TDD + Stage 6 Verification.)*

Derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

---

## Pick Your Mode

Not every task needs the full pipeline.

| Size | Examples | Mode | Stages |
|------|----------|------|--------|
| **мелко** (S) | Баг-фикс, мелкая правка, 1-2 файла | Lightweight | 1 → 4 → 5 → 6 → 7 → Gates (skip spec/plan) |
| **средне** (M) | Новая фича, рефактор, 3-10 файлов | Standard | Stages 1-10 |
| **масштабно** (L) | Архитектура, новый сервис, 10+ файлов | Full | Stages 1-12 (all) |

**How stages relate:** Stages 5-6-7 (Self-Audit, Verification, Impact) run **inside each implementation phase** as an inner loop. Stages 8-12 run **once after all phases complete** as an outer loop.

---

## Context Management (ALWAYS applies)

### Context Discipline (rescaled for our stack, 22.06.2026)
Quality still degrades when context is overloaded ("Dumb Zone"), but do NOT copy the old "40% / compact at 50%" numbers: they were tuned for ~200K windows. We run Opus 4.8 (1M) and the harness already auto-summarizes. So:
- Keep working context lean via Progressive Disclosure (below) and sub-agent summaries, not a fixed % trigger
- Manual `/compact` only before a heavy fresh stage (research → plan → implement) or when answer quality visibly drops, not on a threshold
- If a stage's context got polluted: save a handoff artifact → `/clear` → restart pointed at the artifact

### Fresh Context Between Stages
Every major stage = clean context window:
1. Save stage artifact (research / spec / plan / handoff)
2. `/clear`
3. Start new stage pointing the agent to the artifact path

### Handoff Protocol
Before `/clear` always create `progress/<task>-handoff.md`.
See `templates/handoff.md` for format.

### Progressive Disclosure
Don't dump the entire codebase into context:
- Research: sub-agents → compact summary
- Planning: summary + key interfaces only
- Implementation: only files for current phase
- In CLAUDE.md: `"For details, see path/to/docs.md"` (not @file)

---

## Stage 1: Deep Research

**Mode: Read-Only. No code. No changes.**

- Launch parallel Explore agents (1 per area: structure, patterns, deps, tests)
- **WebSearch: Who has already solved this problem? How did they solve it? What is the most efficient known solution?** Don't reinvent — find the best existing approach first.
- **Analyze all findings and make a conclusion: which solution is the BEST and why.** The research artifact must end with a clear recommendation, not just a list of options.
- Save to `thoughts/research/YYYY-MM-DD-<task>.md`
  (see `templates/research.md` for format)

**→ `/clear`**

---

## Stage 2: Spec / PRD

**Mode: Read + Write only in specs/. No code.**

**Spec = WHAT and WHY. Not how. Spec = contract.**

- Read Research Artifact from `thoughts/research/`
- Create `specs/YYYY-MM-DD-<name>.md`
  (see `templates/spec.md` for format)
- Key sections: Problem, Goal, Scope, Acceptance Criteria, Constraints, Non-Goals

**Skip for size S tasks.**
**→ `/clear`**

---

## Stage 3: Planning + Questions

**Mode: Read + Write only in plans/. No code yet.**

- Read **both** Spec (`specs/`) and Research (`thoughts/research/`)
- Launch Plan agents to check the approach
- Find gaps: what's unthought? What edge cases? What could break?
- **Be creative and proactive: anticipate ALL possible problems BEFORE writing code.** Think several steps ahead. What could go wrong in a week? A month? Under load? With unexpected user behavior? Solve problems before they exist.
- **WebSearch: How have others solved this exact problem? What libraries/patterns exist? What's the proven best practice?** Choose the most efficient solution, not the first one that comes to mind.
- After Plan agents verify the approach — **rewrite the plan into an improved version** incorporating all findings, edge cases, and research results. Not just patch it — rewrite it better.

### Challenge Loop (mandatory before finalizing plan)

```
Before finalizing the plan, answer 3 questions:

1. DOES THIS SOLVE THE PROBLEM?
   Compare every plan item against acceptance criteria from spec.
   If any criterion is uncovered — the plan is incomplete.

2. IS THIS THE MOST EFFICIENT SOLUTION?
   Search: who has already solved this problem? What approach did they use?
   Name 2-3 alternative approaches (including ones found via research).
   For each: pros, cons, effort.
   Justify why the chosen approach is better than all alternatives.

3. IS THERE "CODE FOR CODE'S SAKE"?
   Every change must directly serve acceptance criteria.
   If a change isn't tied to solving the problem — remove it.
   Drive-by refactoring = separate task, not part of this one.
```

### Annotation Cycle
1. Claude drafts the plan
2. `Ctrl+G` — plan opens in editor
3. User adds `> NOTE:` annotations
4. Claude: `"Address all notes, don't implement yet"`
5. Repeat until no notes remain

### Questions for User
- Only for real forks where there's a genuine decision to make
- Use AskUserQuestion with options
- For each question: **recommend which option you think is best and why**
- Don't ask the obvious

### Final Plan
Create `plans/YYYY-MM-DD-<name>.md`
(see `templates/plan.md` for full template with Challenge Log, phases, prompts)

**→ `/clear`**

---

## Stage 4: Phased Implementation

**Each phase = separate session, fresh context, feature branch.**

Phases can be run **in parallel** via separate Claude Code sessions/terminals when they don't depend on each other. Check the plan for dependencies before parallelizing.

**Guard phrase to start coding (scoped, 22.06.2026):** For L-size tasks (architecture / new service / irreversible) present the plan, get explicit approval, then start; the trigger `"Implement Phase N according to plan."` applies here. For S/M tasks, and ALWAYS in autonomous / ЭФИР mode ("делай сам / доведи сам"), approval is implicit: do NOT idle waiting for a trigger phrase (Rule #1: drive to result). The guard disciplines big irreversible work, it must never stall autonomous execution.

Order within each phase:
1. Create/switch to feature branch: `feature/<task>`
2. Update status → `in_progress`
3. **TDD**: tests FIRST (red)
4. **Implement**: code to make tests pass (green)
5. **Refactor** (if needed)
6. **Self-Audit** (Stage 5)
7. **Verification** (Stage 6)
8. **Impact Analysis** (Stage 7)
9. **Gates** (see Gates section)
10. **Commit** (checkpoint)
11. Status → `completed`, write to Changelog
12. **Handoff** → `/clear`

### Parallel Dispatch Discipline

Когда фазы независимы (нет shared state, нет file conflicts), запускать subagent'ы параллельно. Правила prompt structure для каждого subagent:

1. **Focused** - один subagent = один problem domain. Не «fix all tests», а «fix agent-tool-abort.test.ts».
2. **Self-contained** - paste все нужные ошибки / file paths / test names прямо в prompt. Не отсылать subagent читать сессионный контекст.
3. **Constraints** - явно «Do NOT change production code» или «Fix tests only». Без этого agent рефакторит лишнее.
4. **Specific output contract** - «Return: summary of root cause + changes made». Vague output = ты не знаешь что изменилось.

**When NOT parallel:**
- Failures related (fix one might fix others) - investigate together first
- Need full system context to understand
- Exploratory debugging (не знаешь ещё что сломано)
- Shared state (agents would edit same files)

**Real fragility (см):** 3+ параллельных subagent на >5 мин tasks падают по network. Решение - chunked WebSearch с immediate Write, не один большой research subagent.

### Implementer Status Protocol

Каждый dispatched subagent рапортует одним из 4 статусов:

- **DONE** - задача выполнена, всё зелёное. Proceed к review.
- **DONE_WITH_CONCERNS** - выполнено, но subagent flagнул сомнения. Прочитать concerns ДО review. Если про correctness/scope - fix перед review. Если observations («файл большой») - note и proceed.
- **NEEDS_CONTEXT** - subagent'у не хватает информации. Дать missing context + re-dispatch.
- **BLOCKED** - subagent не может выполнить. Оценить blocker:
  1. Context problem → больше context + re-dispatch тем же model
  2. Reasoning required → re-dispatch более capable model
  3. Task слишком большая → разбить на части
  4. План неверен → escalate к юзеру

**Never** игнорить escalation или force тот же model retry без изменений. Subagent сказал stuck = что-то должно измениться.

### Model Selection Heuristic

Самый дешёвый model который справится с task complexity:

- **Cheap (Haiku)** - mechanical implementation: 1-2 файла, полная спека, isolated function
- **Standard (Sonnet)** - integration / judgment: multi-file coordination, pattern matching, debugging
- **Most capable (Opus)** - architecture / design / review: cross-file reasoning, codebase-wide understanding

Сигналы для bump к более capable:
- Touches >5 файлов с integration concerns
- Требует design judgment, не mechanical mapping
- Cross-cutting refactor с unclear scope

---

## Stage 5: Self-Audit (after each phase)

**Mandatory BEFORE marking `completed`:**

```
Check the phase implementation:

1. SPEC COMPLIANCE
   Open spec. Walk through every acceptance criterion.
   For each: implemented? Where exactly in code?
   If any not covered — finish it.

2. CHALLENGE THE SOLUTION
   Look at the written code with fresh eyes.
   Does this actually solve the problem from spec?
   Is there a simpler/more efficient way?
   Any "code for code's sake" — changes unrelated to the task?
```

---

## Stage 5.5: Systematic Debugging Protocol

**Применяется когда:** test failure / unexpected behavior / production bug / build failure / performance issue.

### The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Quick patches маскируют underlying issues. Random fixes создают новые баги. Если Phase 1 не пройдена, fix не предлагать.

### 4 Phases

**Phase 1. Root Cause Investigation**

1. Прочитать error messages полностью (stack traces, line numbers, error codes). Не «X failed», а точная цитата.
2. Reproduce consistently. Если не reproducible, gather more data, не guess.
3. Check recent changes (git diff, new deps, config changes, env diffs).
4. **Multi-component evidence gathering** (для систем с layers - CI → build → sign / API → service → DB):
   - Добавить логи на КАЖДОЙ component boundary
   - Прогнать раз для evidence WHERE breaks
   - Анализ → identify failing layer → investigate именно его
   - Пример (CI signing):
     ```bash
     # Layer 1: workflow secrets
     echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"
     # Layer 2: build env
     env | grep IDENTITY || echo "IDENTITY not in env"
     # Layer 3: keychain state
     security find-identity -v
     # Layer 4: actual signing
     codesign --sign "$IDENTITY" --verbose=4 "$APP"
     ```
5. Trace data flow backward от bad output до source. Fix at source, не at symptom.

**Phase 2. Pattern Analysis**

- Найти working examples похожего кода в codebase
- Прочитать reference implementation ПОЛНОСТЬЮ (не skim)
- Идентифицировать differences между working и broken
- Понять dependencies / assumptions / config required

**Phase 3. Hypothesis Testing**

- Сформулировать ОДНУ гипотезу: «Я думаю X = root cause потому что Y»
- Test минимально - smallest possible change, one variable at a time
- Сработало → Phase 4. Не сработало → новая гипотеза, НЕ добавлять fixes поверх.
- Не знаешь, скажи «I don't understand X», не притворяйся.

**Phase 4. Implementation**

1. Failing test case (simplest reproduction). MUST exist before fix.
2. ONE fix at a time. Никаких «while I'm here» improvements.
3. Verify: test passes? Other tests intact? Issue actually resolved?

### 3+ Fix Failed = Architectural Problem

Если 3+ attempts провалились, STOP. Это НЕ failed hypothesis, это wrong architecture.

Pattern:
- Каждый fix вскрывает новый shared state / coupling в другом месте
- Fix требует «massive refactoring»
- Fix создаёт новые symptoms elsewhere

Действие: НЕ attempt fix #4. Поставить под вопрос fundamentals - is this pattern sound, or sticking through inertia? Discuss с пользователем architecture vs continue fixing symptoms.

### Red Flags - STOP and Return to Phase 1

Если ловишь себя на:
- «Quick fix for now, investigate later»
- «Just try changing X and see if it works»
- «Skip the test, manually verify»
- «It's probably X, let me fix that»
- «Don't fully understand but this might work»
- Предлагаю solutions ДО tracing data flow
- «One more fix attempt» (уже 2+ tried)

ВСЕ эти = STOP, вернуться в Phase 1.

### Common Rationalizations

- «Issue simple, не нужен процесс» → simple issues тоже имеют root causes. Процесс быстрый для simple.
- «Emergency, нет времени» → systematic FASTER чем guess-and-check thrashing.
- «Сначала try, потом investigate» → first fix задаёт pattern. Делай правильно сразу.
- «Multiple fixes сразу saves time» → не можешь изолировать что сработало. Causes new bugs.
- «Я вижу проблему, фикшу» → seeing symptoms ≠ understanding root cause.

Memory cross-ref: - первопричина + параллельный sweep похожих мест.

---

## Stage 6: Verification — Deep Bug Hunt

**Not just linting. Thoughtful review with false-positive filtering.**

### Step 1: Find errors
```
Check ALL code from this phase for:
- Logic errors (wrong conditions, off-by-one, race conditions)
- Data handling (null/undefined, type mismatches)
- Security (injection, auth bypass, exposed secrets)
- Performance (N+1 queries, memory leaks, unnecessary re-renders)
```

### Step 2: Verify bugs are REAL
```
For EACH found bug:
1. Is this a REAL bug or a false positive?
2. Can you prove this bug is reproducible?
3. If you can't prove it — it's NOT a bug. Don't touch it.

RULE: Don't fix code "for beauty" or "just in case".
Fix ONLY proven bugs that actually affect functionality.
Every "fix" without proof = risk of introducing a new bug.
```

### Step 3: Logic and efficiency check
```
Final code cleanliness check:
- Logic: is the data flow correct from input to output?
- Efficiency: any redundant operations?
- Readability: is the code understandable without comments?
BUT: don't refactor "for beauty". Only if it affects correctness.
```

---

## Stage 7: Impact Analysis — "Did we break anything?"

**The most underestimated stage. 75% of AI agents break previously working code.**

```
MANDATORY CHECK BEFORE MERGE:

1. REGRESSION
   What other modules/functions depend on changed files?
   Run ALL project tests (not just current phase).
   If anything broke — this is priority #1.

2. SIDE EFFECTS
   Did any contracts/interfaces change (API, props, types)?
   If yes — who uses them? Are all consumers updated?

3. THINK AHEAD
   What problems could these changes cause in a week/month?
   Edge cases we haven't tested?
   What happens with: zero data? Huge data? Concurrent requests?
   What if the user does something unexpected?

4. COMPATIBILITY
   Backward compatibility preserved?
   Data migrations needed?
   Feature flags needed for gradual rollout?
```

---

## Stage 8: Integration Check

- All phases `completed` → run gates across entire project
- Explore agents for audit: everything from spec implemented?
- Every acceptance criterion → fulfilled?

---

## Stage 9: Two-Stage Review (fresh context)

**New session. No implementation bias.** Не одну review, а две последовательно, разные lenses.

### Stage 9a: Spec Compliance Review

Цель: проверить что код соответствует spec / acceptance criteria. Не качество, а полнота.

- Открыть spec, пройти каждый acceptance criterion
- Для каждого: implemented? где именно в коде?
- Flag: missing requirements / extra functionality not in spec
- Approve только когда ВСЕ criteria covered, НИЧЕГО extra

**Spec reviewer found issues = NOT done.** Implementer fixes, спек reviewer пересматривает. Repeat до ✅.

### Stage 9b: Code Quality Review

ТОЛЬКО после 9a ✅. Цель: качество, не полнота.

- Launch `@code-reviewer` agent (see `agents/code-reviewer.md`)
- Checklist: edge cases, race conditions, backward compat, security, error handling, performance
- Magic numbers, unclear naming, missing tests for edge cases
- If possible: cross-model review (different model checks Claude's work)
- **Warning:** AI reviewing AI has shared blind spots. For critical code, human review is mandatory.

**Never** start 9b пока 9a с open issues. Wrong order = quality review на коде который не делает что должен.

---

## Stage 10: Security Scan (for M and L)

```bash
semgrep --config=auto .
# or
/security-review    # built into Claude Code
```

**Manual self-pentest "become the hacker yourself" (borrowed from competitor course Мари/ЛАБС)** — after the automated scan, run 4 quick checks by hand on the running app, then a final OWASP audit prompt:
1. Register with a weak password `123456` → must be rejected.
2. Change another user's id in the URL → must return 403, not someone else's data (IDOR).
3. Click submit 10–15 times fast → must hit 429 (rate-limit).
4. Open `/admin` without logging in → must require auth.
Then: ask the agent — *"do a final security audit of this project as an OWASP expert"*.
> Full version + the 3-AI security pass: your team playbook Playbook 1, Move 5. This manual layer is especially relevant for RU apps with personal data (pairs with the `yurist` 152-ФЗ app checklist).

---

## Stage 11: Fixes + Re-verification

If review/scan found issues:
1. Fix (only proven bugs — rule from Stage 6)
2. Re-run gates
3. Repeat Impact Analysis (Stage 7) — fixes didn't break anything else?
4. Re-review if major changes were made

---

## Stage 12: Cleanup + Deploy

- Archive plan: `mv plans/<file> plans/archive/`
- Keep spec as documentation
- Squash merge → main
- **Deploy — ONLY on explicit user request**

---

## Stage 13: Production QA stack (для проектов пользователя)

Применяется после Stages 1-12 для прод-проектов (TG-бот / Lovable frontend / Lovable Cloud / standalone API / CLI / ETL). Конкретный stack под наши проекты, не generic.

### Когда обязателен

- Любая задача где написан или изменён прод-код (фича / bug-fix / рефактор / архитектура / деплой / миграция)
- НЕ применяется только если задача = research / план / спека / контент-артефакт (your project files) / setup конфига без логики

### Core принципы

1. **Industry-standard stack** под тип проекта (см. ниже), не выдумывай ad-hoc скрипты
2. **Тестируй на реальных артефактах**, не на синтетике. iPhone-ролик с rotation, не testsrc2. Реальная речь, не sine 440Hz.
3. **Меряй ту же метрику что увидит пользователь**. Если в UI «N%» - прогони smoke и увидь это N% в логе до релиза.
4. **Negative tests обязательны**. Empty input / overflow / wrong type / отсутствие прав / упавший dep.
5. **Error tracking ДО релиза**. Sentry/GlitchTip активен с первой строки прод-кода.
6. **Healthcheck endpoint** для любого long-running сервиса.
7. **CI gates** блокируют merge при красных тестах.
8. **UI label = behavior контракт** (новое 24.05.2026). Если кнопка/опция говорит «без X / off / none / выкл» - код буквально не должен делать X. Маппер UI → params обязательно покрыт unit-тестом, который проверяет семантику, а не «возвращает tuple».
9. **Randomizer property tests** (новое 24.05.2026). Любая функция с `random.choice` / `r.uniform` / `r.randint` в дефолтном профиле прод-сервиса покрыта property-тестом на 100-200 seed'ах. Каждый sample проходит assert «output остаётся user-acceptable» (не deja-vu негатив / не нечитаемо тёмное / не порченое аудио).
10. **Visual smoke на user-facing output** (новое 24.05.2026). Для сервисов с выходом, который видит человек (видео-рендер / картинка / TTS / текст для публикации) - manual review 10+ random sample'ов с diverse fixtures (горизонталь/вертикаль/квадрат, кодек H.264/HEVC, длительность 5/30/120с). Не «pytest зелёный = готово».
11. **Подтяни свои уроки перед QA-прогоном** (если ведёшь заметки-память). Перед чек-листом перечитай свои сохранённые выводы про деплой, разрушающие изменения и постдеплой - попроси Claude: «прочитай мои заметки про деплой и разрушающие изменения перед прогоном чек-листа». Уроки живут в памяти, а в hard-чек не попадают сами.

### Universal checklist (применять ВСЕГДА перед закрытием)

**Перед написанием тестов:**
- [ ] Тип проекта определён (TG-бот / Frontend / API-backend / CLI / ETL)
- [ ] Базовый stack для типа выбран (см. ниже), не ad-hoc
- [ ] Error tracking настроен (Sentry / GlitchTip). DSN в env. Тестовый exception прилетает.
- [ ] Healthcheck endpoint (для сервисов) → 200 + JSON
- [ ] CI workflow (GitHub Actions) запускает тесты на push

**Unit/Integration tests:**
- [ ] Каждый публичный handler/функция - хотя бы happy-path тест
- [ ] Edge cases: empty input, max, wrong type, None/undefined, unicode
- [ ] Negative cases: что возвращается на ошибку / exception / отсутствие прав
- [ ] Боковые эффекты проверены (БД, файлы, внешние API)

**Регрессия (критично!):**
- [ ] Pytest регрессия на каждый bug в текущей сессии. Имя `test_<feature>_regression_<bug-id>`. ДО объявления готовым.
- [ ] Прогон ВСЕХ тестов, не только новых
- [ ] Если изменил публичный API - все callsites обновлены

**UI ↔ behavior contract (для любого сервиса с UI):**
- [ ] Каждый callback_data / button label / меню-опция имеет unit-тест который проверяет: label «без X» → код НЕ делает X; label «N% / X секунд» → код применяет именно N% / X секунд.
- [ ] Маппер `_ui_choice_to_param()` покрыт tabular-тестом для ВСЕХ значений из cycle.
- [ ] End-to-end тест: «пользователь выбрал none → output не содержит трансформации».
- [ ] Reference: `tests/unit/test_handler_ui_mapping.py` в uniqalizer-bot.

**Randomizer property tests (для любой функции с random в проде):**
- [ ] Каждый `random.choice(LIST)` в дефолтном профиле: явный assert что в LIST нет destructive значений (см. пример).
- [ ] Property test на 100-200 seed'ах: каждый sample проходит boundary asserts (brightness/gamma/contrast не на дне диапазона, который ломает UX).
- [ ] Сужение диапазонов: нижняя/верхняя граница `r.uniform(a, b)` явно объяснена в комментарии («ниже -0.05 brightness даёт нечитаемое изображение - см. memory feedback»).
- [ ] Reference: `test_curves_preset_no_destructive_values_regression_24_05` и `test_default_profile_property_200_samples_watchable` в uniqalizer-bot.

**Visual smoke на user-facing output (для контент-сервисов):**
- [ ] Diverse fixtures: 3+ файла разного aspect (16:9, 9:16, 1:1), кодека (H.264, HEVC), длительности (5с, 30с, 120с).
- [ ] Рендер 10+ random sample'ов default-профиля → ручной просмотр в Telegram preview / VLC. Не «file size OK = готово».
- [ ] Чек-критерии для каждого sample: видно/не видно ли контент; цвета не инвертированы; звук читаемый; рамки не вешаются вопреки выбору «без рамки».
- [ ] Если N% sample'ов «плохие» → bug, не «приемлемый процент».

**Deploy:**
- [ ] Rsync исключает .venv / .env / data/ / work / __pycache__
- [ ] Permissions владельца кода после rsync проверены (chown -R user:user)
- [ ] Systemd unit активен после restart
- [ ] Healthcheck возвращает 200 после рестарта

**Post-deploy active probe (КРИТИЧНО):**
Snapshot логов не достаточен. Service started ≠ работает.
- [ ] Воспроизвести исходный bug который фикс закрывает - убедиться что не падает
- [ ] **Если bind mount / external volume**: `docker exec <container> touch /mounted/file` → `sudo -u <host_user> cat`. Ловит permissions для **будущих** файлов.
- [ ] **Watch logs 10 минут** после deploy (live tail, не snapshot). Late errors на первом реальном запросе.
- [ ] **Active health probe**: `curl /healthz` ДО и ПОСЛЕ deploy с разницей 60+ сек.
- [ ] **Boundary fix (TG/HTTP/disk/perms)**: тест-клиент (Telethon/httpx) сразу.

**Dependency verification:**
- [ ] Импорт работает в target runtime: `python -c "import <pkg>"`. Если ImportError - пакет несовместим, выпиливать.
- [ ] Версия пакета совместима с major фреймворка (для aiogram 3 не aiogram-tests v1, для React 19 не enzyme).
- [ ] Research-agent recommendations не принимать на веру - сначала import, потом requirements.

**No module-level singletons (для aiogram-stack):**
- [ ] `router = Router(...)` НЕ на module-level, всегда внутри `make_router()` factory
- [ ] Bot/Db/Gate/Cfg тоже через factory
- [ ] `grep -E '^router = |^bot = ' bot/handlers/*.py` пусто

**Финал (обязательно перед фразой «готово»):**
- [ ] Все тесты зелёные (`pytest -q` exit code 0)
- [ ] CI workflow прошёл зелёным
- [ ] Sentry/GlitchTip за последние 5 минут - нет новых exceptions
- [ ] Healthcheck отвечает 200
- [ ] e2e на реальном артефакте успешен с измерением метрики
- [ ] Post-deploy active probe пройден

Если любой пункт red - ЗАДАЧА НЕ ЗАКРЫТА. Сказать пользователю прямо что red, не маскировать.

### Stack per project type

**TG-бот на aiogram 3 (Python):**
```
pytest==8.3.3
pytest-asyncio==0.24.0
telethon==1.37.0           # E2E через реальный TG-клиент
sentry-sdk[aiohttp]==2.18.0
# aiogram-tests НЕ использовать с aiogram 3 - только v2 совместим
```
Структура tests/: unit/ + integration/ (с ffmpeg/БД) + e2e/ (Telethon)
Mandatory: pytest для handler, Telethon e2e для критичного flow, /healthz на :8080, error router в Dispatcher → Sentry.

**Lovable frontend (React):**
```
vitest ^2.0
@testing-library/react ^16
@playwright/test ^1.47
@sentry/react ^8.30
```
Mandatory: vitest на hooks/utils, component tests для UI states (loading/error/empty/success), playwright e2e на 3-5 main flows, Lighthouse CI бюджет.

**Lovable Cloud backend / FastAPI:**
```
pytest==8.3.3
httpx==0.27.0              # async client для тестов API
pytest-postgresql==6.0.0   # ephemeral PG, не моки
sentry-sdk[fastapi]==2.18.0
```
Mandatory: pytest на endpoint (200/400/401/403/404/500), httpx TestClient, /health и /ready, rate limit.

**CLI / one-shot:** pytest на core logic, idempotency, exit codes, --dry-run для destructive.

**ETL / scheduled:** pytest на трансформации (fixture → expected), idempotency, partial failure handling, alerting на failure.

### Anti-patterns

1. **Ad-hoc `qa_suite.py`** с произвольными проверками. Используй pytest + параметризации.
2. **Synthetic input** (testsrc2 / sine 440Hz / lorem) когда прод на реальном. Synthetic только для smoke.
3. **«It works on my machine»** без CI gate.
4. **«Пока без error tracking»**. Sentry в первый commit.
5. **Mock БД/ffmpeg/redis** - используй ephemeral fixtures.
6. **«Всё работает, ошибок нет»** без явного прогона чек-листа выше.
7. **UI-label врёт** (24.05.2026). Кнопка «без рамки» → код подставляет «9:16». Кнопка «звук убрать» → код снижает громкость до -20dB вместо `-an`. Если так - bug, всегда. Маппер UI обязан семантически совпадать.
8. **Destructive значения в random.choice дефолтного профиля** (24.05.2026). `curves_preset` ∈ {darker, negative, vintage} в дефолте - не «вариативность для anti-spam», а 12-37% порченых выходов. Destructive значения - только в явном opt-in профиле (aggressive=True), никогда в дефолте.
9. **Test fixtures = один файл** (24.05.2026). Один 9:16 портретник в `tests/fixtures/` маскирует bug «letterbox 9:16 вешается на 16:9 источник». Нужно diverse: 16:9 + 9:16 + 1:1 + 4:5 минимум.
10. **pytest зелёный = готово** для user-facing output (24.05.2026). Технический pass не равен «зритель видит нормальный контент». Visual smoke на 10+ random sample'ах обязателен.
11. **Memory feedback в read-only режиме** (24.05.2026). Память накапливает уроки, но если skill не подтягивает их перед прогоном - они не материализуются в hard-чек. Auto-pull обязателен.

### Reference

- Реализация полного TG-бот QA-стека: `~/code/uniqalizer-bot/`
- tests/{unit,integration,e2e}/ структура
- `bot/observability.py` - Sentry init no-op без DSN
- `bot/health.py` - /healthz endpoint параллельно polling
- `.github/workflows/test.yml` - CI с ffmpeg + chromaprint

### Принципы перед каждым QA-прогоном

Держи их в голове (или вынеси в свои заметки-память и перечитывай перед чек-листом):

- **Глубокое ревью** - НЕ говорить «ошибок нет» без явного e2e-теста на реальном кейсе
- **Индустриальные стандарты, не самодел** - pytest + готовые библиотеки, не ad-hoc скрипты
- **Проверка через API, не клики пользователя** - psql/curl/CLI/логи, не дёргать пользователя кликать
- **Активная проверка после деплоя** - воспроизвести баг + 10 минут смотреть логи
- **Аудит всей пачки** - после 2+ скиллов за сессию прогнать аудит по всему батчу
- `feedback-ui-label-equals-behavior` - 24.05.2026: маппер UI → params покрыт unit-тестом на семантику
- `feedback-no-destructive-defaults-in-random` - 24.05.2026: random.choice в дефолте без destructive значений

### Post-mortem 24.05.2026 (Юлин кейс - bug который выявил пробел в Stage 13)

**Что случилось:** В uniqalizer-bot 2 грубых бага дожили до прода:
1. `_frame_to_layout_margin("none") → ("9:16", 0)` - UI label «без рамки» вешал letterbox на горизонтальное видео
2. `CURVES_PRESETS = (..., "darker", "negative", ...)` + `r.choice(CURVES_PRESETS)` - 25% копий получали затемнение/инверсию

**Почему прошли через QA:**
- Stage 13 ловил technical errors (returncode, file size, ffprobe meta), не user-visible quality
- Test fixtures - один 9:16 портретник → bug #1 невидим
- Property tests на рандомизатор отсутствовали → bug #2 невидим
- UI ↔ behavior contract не проверялся вообще
- Memory feedback'и накапливались (`deep_review_discipline` 19-21.05, `batch_cohort_audit` 23.05) но в hard-чек Stage 13 не материализовались

**Что исправлено в Stage 13:**
- Добавлены принципы 8-11 (UI contract / randomizer property / visual smoke / auto-pull memory)
- Добавлены 3 раздела в Universal checklist (UI ↔ behavior / Randomizer property / Visual smoke)
- Добавлены 5 anti-patterns (7-11)
- Memory cross-refs стали mandate, не reference

**Lesson encoded:** каждый раз, когда находишь bug который прошёл через Stage 13 - вернись и допиши чек, который его поймал бы. Skill эволюционирует вместе с памятью.

---

## Deterministic Gates

A phase CANNOT be `completed` without passing ALL required gates.

### Tier 1: Required (block the phase)
```bash
# Frontend
cd frontend && npx tsc --noEmit          # 0 type errors
cd frontend && npm run lint               # 0 lint errors
cd frontend && npm test                   # all tests green

# Backend
cd backend && python -m py_compile app/main.py
cd backend && pytest --tb=short -q
cd backend && ruff check .
```

### Tier 2: Recommended (for M and L)
```bash
npx madge --circular src/         # circular dependencies
npm audit --audit-level=high      # dependency vulnerabilities
pip-audit
```

### Tier 3: Deep Security (for Security Scan stage)
```bash
semgrep --config=auto .
# or /security-review
```

If a gate fails - fix and re-run. Never skip.

---

## Hooks

Опциональная защита поверх дисциплины: хук, который блокирует опасные Bash-команды (push в `main`, `rm -rf /`, `DROP TABLE`). Написан на Python - работает одинаково на macOS, Linux и Windows, без `jq` и без bash.

1. Создай файл `~/.claude/hooks/guard-dangerous-bash.py`:

```python
import json, re, sys

data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command", "")
if re.search(r"git push\s+.*\b(main|master)\b|rm\s+-rf\s+/|DROP\s+TABLE", cmd, re.I):
    print("BLOCKED: используй отдельную ветку или безопасную альтернативу.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
```

2. Подключи в `~/.claude/settings.json` (на **Windows** замени `python3` на `python`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/guard-dangerous-bash.py", "timeout": 5 }
        ]
      }
    ]
  }
}
```

> **Почему Python, а не bash-однострочник.** На Windows нет ни `bash`, ни `jq`, поэтому классический `bash -c "... | jq ..."`-хук там молча не срабатывает (падений нет, защита просто не работает). Python идёт в Claude Code-окружении и парсит JSON сам - один файл работает на всех системах. Сама дисциплина «не закрывать задачу без прогона тестов/линта/сборки» зашита в стадии Verify этого скилла, хук лишь страхует от самых опасных команд.

---

## Git Discipline

- Each task = `feature/<task>` branch
- Commit after each passed gate (checkpoint for rollback)
- NEVER push to main directly (hook blocks it)
- Squash merge on completion

---

## Optional Enhancements

### PreToolUse: блокировать захардкоженные секреты при записи файла

Кроссплатформенно (Python, без bash и jq). Создай `~/.claude/hooks/guard-secrets.py`:

```python
import json, re, sys

data = json.load(sys.stdin)
content = (data.get("tool_input") or {}).get("content", "")
if re.search(r"(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{10,}", content, re.I):
    print("BLOCKED: похоже на захардкоженный секрет. Используй переменные окружения.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
```

Подключи в `~/.claude/settings.json` (на **Windows** замени `python3` на `python`):

```json
{
  "matcher": "Write|Edit",
  "hooks": [
    { "type": "command", "command": "python3 ~/.claude/hooks/guard-secrets.py" }
  ]
}
```

Грубая проверка по regex, ловит очевидные ошибки. Для прода используй `semgrep` или `/security-review`.

---

## Model Recommendations

| Stage | Model | Why |
|-------|-------|-----|
| Research, Planning | Opus | Cross-file reasoning |
| Implementation (mechanical, 1-2 files, full spec) | Haiku | Speed, cheap |
| Implementation (multi-file integration, debugging) | Sonnet | Standard judgment |
| Implementation (cross-cutting refactor, design judgment) | Opus | Deep reasoning |
| Code Review, Security | Opus | Deep analysis |
| Anti-rationalization / verification Stop hooks | none (bash grep) | Deterministic, fast, zero model cost |

**Complexity heuristic для Stage 4 dispatch:**
- 1-2 файла + полная спека + isolated function → cheap model
- Multi-file coordination + pattern matching + integration → standard
- Cross-file reasoning + architecture decision + broad codebase → most capable

---

## Project Structure

```
project/
├── .claude/
│   ├── settings.json           # hooks config
│   ├── skills/
│   │   └── вайбкодинг/
│   │       ├── SKILL.md        # ← this file
│   │       ├── templates/
│   │       │   ├── research.md
│   │       │   ├── spec.md
│   │       │   ├── plan.md
│   │       │   └── handoff.md
│   │       └── agents/
│   │           └── code-reviewer.md
│   └── agents/                 # project-level agents
├── CLAUDE.md                   # project brain
├── specs/                      # WHAT and WHY
├── plans/                      # HOW
│   └── archive/                # completed plans
├── thoughts/research/          # research artifacts
└── progress/                   # handoff files
```
