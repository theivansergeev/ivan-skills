#!/usr/bin/env bash
# Dense frame extraction + sectioned contact sheets for shot-by-shot reverse-engineering.
#
# WHY this exists (lesson 2026-06-21): a reconstruction built from sparse 1 fps frames in a
# tiny preview MISSED the wow-trigger - a falling meteor that streaks for <1s and causes the
# wave. The reconstructed script then invented "wave grows from nowhere" and the regen was junk.
# Fix: cut DENSE (multiple frames/sec), build LARGE readable sectioned sheets, and read EACH
# sheet in order so sub-second events (meteor, flash, cut, transformation beat) are caught.
#
# Usage: dense-frames.sh <video.(mp4|mov|webm)> [outdir]
# Output: <outdir>/frames/*.jpg  +  sheet_NN_<a>-<b>s.jpg (one per ~6s window)  +  overview.jpg
set -uo pipefail

VIDEO="${1:?usage: dense-frames.sh <video> [outdir]}"
[ -f "$VIDEO" ] || { echo "ERROR: no such file: $VIDEO"; exit 2; }
OUT="${2:-$(dirname "$VIDEO")/dense-$(basename "${VIDEO%.*}")}"
mkdir -p "$OUT/frames"

command -v ffmpeg  >/dev/null || { echo "ERROR: ffmpeg missing (brew install ffmpeg)";  exit 2; }
command -v ffprobe >/dev/null || { echo "ERROR: ffprobe missing (brew install ffmpeg)"; exit 2; }

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO" 2>/dev/null | cut -d. -f1)
DUR=${DUR:-15}; [ "$DUR" -lt 1 ] && DUR=1

# fps by length: short reels carry sub-second beats, sample them densely
if   [ "$DUR" -le 20 ]; then FPS=6
elif [ "$DUR" -le 45 ]; then FPS=4
else                        FPS=2
fi

echo "[dense] duration=${DUR}s  fps=${FPS}"
rm -f "$OUT"/frames/*.jpg "$OUT"/sheet_*.jpg "$OUT"/overview.jpg 2>/dev/null
ffmpeg -loglevel error -i "$VIDEO" -vf "fps=${FPS},scale=720:-1" "$OUT/frames/f_%04d.jpg"
NF=$(ls "$OUT"/frames/*.jpg 2>/dev/null | wc -l | tr -d ' ')
echo "[dense] extracted $NF frames -> $OUT/frames/"

# Sectioned contact sheets: ~6s windows, LARGE tiles so small/fast details stay visible.
# Read EACH sheet, not one shrunk grid - that is exactly where the meteor was lost before.
WIN=6; SEG=0; START=0
while [ "$START" -lt "$DUR" ]; do
  SEG=$((SEG+1))
  TAG=$(printf '%02d' "$SEG")
  ffmpeg -loglevel error -ss "$START" -t "$WIN" -i "$VIDEO" \
    -vf "fps=${FPS},scale=640:-1,tile=${FPS}x${WIN}" -frames:v 1 \
    "$OUT/sheet_${TAG}_${START}-$((START+WIN))s.jpg" 2>/dev/null
  START=$((START+WIN))
done
echo "[dense] $SEG sectioned sheets (~${WIN}s each, large tiles) -> $OUT/sheet_*.jpg"

# Full overview sheet - one glance for global structure and shot-change rhythm
ffmpeg -loglevel error -framerate 1 -i "$OUT/frames/f_%04d.jpg" \
  -vf "tile=6x6,scale=2000:-1" -frames:v 1 "$OUT/overview.jpg" 2>/dev/null
echo "[dense] overview -> $OUT/overview.jpg"
echo "[dense] READ ORDER: sheet_01..sheet_${SEG} in sequence (catch fast events), then overview.jpg"
echo "OUTDIR=$OUT"