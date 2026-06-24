#!/usr/bin/env bash
# Pull every external SIGNAL around a viral video: metrics, full caption, tools the author named.
#
# WHY this exists (lesson 2026-06-21): the caption emoji "comet / chair / wave" encoded the whole
# causal sequence (meteor -> man in chair -> wave) and was ignored; and the real production level
# comes from tools the author names in the caption (Runway / Seedance / Seedream / Topaz / Kling /
# DaVinci), not from one text prompt. Never reconstruct from the picture alone - read the signals.
#
# Usage: reel-meta.sh <video-url>
# Env:   IG_COOKIES=/path/to/instagram-cookies.txt  (default ~/.config/yt-dlp/instagram-cookies.txt)
set -uo pipefail

URL="${1:?usage: reel-meta.sh <video-url>}"
CK="${IG_COOKIES:-$HOME/.config/yt-dlp/instagram-cookies.txt}"
COOK=(); [ -f "$CK" ] && COOK=(--cookies "$CK")

command -v yt-dlp >/dev/null || { echo "ERROR: yt-dlp missing (brew install yt-dlp)"; exit 2; }

echo "=== METRICS (virality proof - on the PUBLISH platform, not a proxy) ==="
yt-dlp "${COOK[@]}" --skip-download --no-warnings \
  --print "uploader=%(uploader)s | likes=%(like_count)s | views=%(view_count)s | comments=%(comment_count)s | date=%(upload_date)s | dur=%(duration)ss" \
  "$URL" 2>&1 | head -3

echo; echo "=== FULL CAPTION (read the EMOJI and any beat/sequence cues, do not skim) ==="
CAP=$(yt-dlp "${COOK[@]}" --skip-download --no-warnings --print "%(description)s" "$URL" 2>/dev/null)
printf '%s\n' "$CAP"

echo; echo "=== TOOLS NAMED BY AUTHOR (this is the production pipeline) ==="
TOOLS=$(printf '%s\n' "$CAP" | grep -ioE 'seedance ?[0-9.]*|seedream ?[0-9.]*|runway|kling ?[0-9.]*|midjourney|gpt ?image ?[0-9.]*|nano ?banana|topaz|starlight|astra|davinci|resolve|higgsfield|elevenlabs|veo ?[0-9.]*|sora ?[0-9.]*|google ?flow|luma|hailuo|pika|capcut|magnific' | sort -u)
if [ -n "$TOOLS" ]; then printf '%s\n' "$TOOLS" | sed 's/^/  - /'; else echo "  (none named - pipeline must be INFERRED from frames + knowledge/production-pipeline.md)"; fi

echo; echo "=== CODE-WORD / DM-GATED WORKFLOW (author may hand the prompt on a comment) ==="
printf '%s\n' "$CAP" | grep -iE 'comment|comenta|coment|\bDM\b|код-слово|кодовое|напиши .* в комм' | head -5 || true
echo "(if present: the full prompt/workflow is gated behind that code-word, note it for the user)"