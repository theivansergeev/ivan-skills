# Plan: [Name]
**Spec:** specs/YYYY-MM-DD-<name>.md
**Status:** planning | in_progress | completed

## Challenge Log
**Problem:** [1-2 sentences]
**Chosen solution:** [approach]
**Alternatives considered:**
1. [Alternative A] — rejected because [reason]
2. [Alternative B] — rejected because [reason]
**Why chosen solution is better:** [justification]

## Problems

| # | Problem | Solution | Status |
|---|---------|----------|--------|
| 1 | ... | ... | pending |

## Phases

### Phase 1: [Name]
- **Status:** pending | in_progress | completed
- **Files:** [specific list]
- **Changes:** [what exactly changes]
- **TDD:** [which tests to write first]
- **Gates:** tsc ✅ | pytest ✅ | lint ✅
- **Impact:** [what other modules could be affected]
- **Prompt for launch:**
  ```
  Read plans/YYYY-MM-DD-xxx.md, Phase 1.
  Read spec at specs/YYYY-MM-DD-xxx.md.
  Implement according to plan. Start with tests.
  Do not modify files outside of: [list].
  After completing:
  1. Self-audit against spec (every acceptance criterion covered?)
  2. Verify bugs are real (not cosmetic fixes)
  3. Impact analysis (did we break anything else?)
  4. Run all tier 1 gates
  ```

### Phase 2: [Name]
...

## Changelog

| Date | Phase | Changes |
|------|-------|---------|
