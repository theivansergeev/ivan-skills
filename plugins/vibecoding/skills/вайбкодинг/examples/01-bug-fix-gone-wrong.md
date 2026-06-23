# Example 1: Bug Fix Gone Wrong

## The Task

"Fix the login timeout — users get logged out after 5 minutes instead of 30."

## Without Вайбкодинг

The AI agent:
1. Found the timeout constant: `SESSION_TIMEOUT = 300` (5 min)
2. Changed it to `SESSION_TIMEOUT = 1800` (30 min)
3. While reading the auth module, noticed "messy" session validation code
4. Refactored `validateSession()` — changed the function signature
5. "Improved" error handling in the token refresh flow
6. Added a new middleware for session logging

**Result:**
- Login timeout: fixed ✅
- Password reset: broken ❌ (depended on old `validateSession()` signature)
- OAuth flow: broken ❌ (token refresh error handling change broke the retry logic)
- 3 files changed that didn't need changing

## With Вайбкодинг

**Stage 1 — Research:** Agent identifies that `SESSION_TIMEOUT` is the only root cause. Notes that `validateSession()` and token refresh are consumers but not related to the bug.

**Stage 4 — Implementation:** Changes `SESSION_TIMEOUT = 300` → `SESSION_TIMEOUT = 1800`. One line. One file.

**Stage 5 — Self-Audit:** "Does this fix match the spec? Yes — timeout is now 30 minutes."

**Stage 6 — Verification:** No bugs introduced (one constant changed).

**Stage 7 — Impact Analysis:** "Who else uses `SESSION_TIMEOUT`? Token refresh uses it for max retry window — still valid at 1800. No regressions."

**Result:**
- Login timeout: fixed ✅
- Password reset: still works ✅
- OAuth flow: still works ✅
- 1 file changed, 1 line modified

## The Lesson

The Challenge Loop question — "Is there code for code's sake?" — would have caught the unnecessary refactoring at the planning stage. The Impact Analysis would have caught the broken consumers even if the refactoring had slipped through.
