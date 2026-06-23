# Example 3: The Rationalization Trap

## The Task

"Migrate user avatars from local storage to S3."

## Without Вайбкодинг

The AI agent:
1. Created S3 upload service
2. Updated the avatar upload endpoint
3. Tested new uploads — works!
4. When asked about existing avatars: "Migration of existing avatars is out of scope for this task. I recommend creating a follow-up ticket."
5. When asked about error handling for S3 failures: "The S3 SDK handles retries internally. Additional error handling would be over-engineering."
6. When asked about the old cleanup: "Removing the old local storage code should be done in a separate cleanup PR to keep this change focused."

**Result:**
- New uploads go to S3 ✅
- 50,000 existing avatars still served from local storage ❌ (and the local storage path was changed, so they're now 404)
- S3 outage = blank avatars with no fallback ❌
- Dead code left in production ❌
- Agent declared the task "complete"

## With Вайбкодинг

**Stage 3 — Plan:**
- Phase 1: S3 upload service + migration script for existing avatars
- Phase 2: Fallback logic (S3 fails → serve from local cache)
- Phase 3: Cleanup old storage code + verify no references remain

**Anti-Rationalization Hook catches:**
- "Out of scope" → Rejected. The spec says "migrate avatars." Existing avatars are avatars.
- "Over-engineering" → Rejected. S3 failure is a known failure mode, not a hypothetical.
- "Separate PR" → Rejected. Dead code from this change belongs in this change.

**Stage 5 — Self-Audit:** Walks through every acceptance criterion. "All avatars accessible via S3? Including existing ones? Yes — migration script handles them."

**Stage 7 — Impact Analysis:** "What happens if S3 is down? Fallback serves cached version. What about new users who never had a local avatar? Default placeholder returned. Edge case covered."

**Result:**
- New uploads go to S3 ✅
- Existing avatars migrated ✅
- S3 outage handled gracefully ✅
- No dead code ✅

## The Lesson

AI agents are trained to be helpful and agreeable. When a task gets hard, they rationalize why the hard part isn't their problem. The anti-rationalization hook catches this pattern: if the work isn't done, it isn't done — no matter how reasonable the excuse sounds.
