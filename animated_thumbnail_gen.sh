#!/bin/bash
# Creates an animated WebP thumbnail from one or multiple video files.
# Uses scene cuts; falls back to evenly-spaced frames for low-cut videos.
# Original idea: https://gist.github.com/Voldrix/84a01b602e5d6c53c2b67e156bf26a10

if [ -z "$1" ]; then
  echo "Usage: ./animated_thumbnail_gen.sh video1.mp4 video2.mp4 ..."
  echo "       ./animated_thumbnail_gen.sh *.mp4"
  exit 1
fi

numOfScenes=8      # max number of scenes to capture
sceneLength=1.5    # seconds of each scene clip
sceneDelay=0.3     # seconds after a cut before recording (skips transition flash)
sceneThreshold=0.3 # scene-change sensitivity (0.0=any change, 1.0=only big cuts)

for i; do
  echo ""
  echo "Processing: $i"

  if [ ! -f "$i" ]; then
    echo "  SKIP: file not found — $i"
    continue
  fi

  # Get framerate (returned as fraction like 30/1) and duration separately
  framerate_raw=$(ffprobe -v 0 -select_streams V:0 \
    -show_entries stream=r_frame_rate \
    -of default=nw=1:nk=1 "$i")
  duration=$(ffprobe -v 0 \
    -show_entries format=duration \
    -of default=nw=1:nk=1 "$i")

  if [ -z "$framerate_raw" ] || [ -z "$duration" ]; then
    echo "  SKIP: could not read video info — $i"
    continue
  fi

  # Halve the framerate (for smoother animation at smaller file size)
  framerate=$(bc <<< "scale=3; ${framerate_raw%/*} / ${framerate_raw#*/} / 2")
  sceneSpacer=$(bc <<< "scale=3; $duration / (($numOfScenes - 1) * 2)")

  echo "  Duration: ${duration}s | FPS (half): $framerate | Scene spacer: ${sceneSpacer}s"

  # --- Attempt 1: scene-detection ---
  ffmpeg -nostdin -ss "$sceneSpacer" -i "$i" \
    -fps_mode vfr \
    -vf "select=if(gt(scene\,$sceneThreshold)*(isnan(prev_selected_t)+gte(t-prev_selected_t\,$sceneSpacer))\,st(1\,t)*0*st(2\,ld(2)+1)\,if(ld(1)*lte(ld(2)\,$numOfScenes)\,between(t\,ld(1)+$sceneDelay\,ld(1)+$sceneDelay+$sceneLength))),scale=320:180:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=bicubic,framestep=2,setpts=N/(${framerate}*TB)" \
    -an -sn -map_chapters -1 -map_metadata -1 -hide_banner \
    -compression_level 5 -q:v 75 -loop 0 -f webp -y "${i%.*}_tmp_scene.webp" 2>/dev/null

  scene_size=$(stat -c%s "${i%.*}_tmp_scene.webp" 2>/dev/null || echo 0)

  if [ "$scene_size" -gt 1024 ]; then
    mv "${i%.*}_tmp_scene.webp" "${i%.*}.webp"
    echo "  Done (scene-detection) → ${i%.*}.webp"
  else
    rm -f "${i%.*}_tmp_scene.webp"
    echo "  No scene cuts found — using evenly-spaced frames instead"

    # --- Fallback: evenly-spaced time windows ---
    interval=$(bc <<< "scale=3; $duration / $numOfScenes")
    filter_parts=""
    for ((n=0; n<numOfScenes; n++)); do
      start=$(bc <<< "scale=3; $n * $interval + 0.5")
      end=$(bc <<< "scale=3; $start + $sceneLength")
      if [ -n "$filter_parts" ]; then
        filter_parts="${filter_parts}+between(t\,$start\,$end)"
      else
        filter_parts="between(t\,$start\,$end)"
      fi
    done

    ffmpeg -nostdin -i "$i" \
      -fps_mode vfr \
      -vf "select='${filter_parts}',scale=320:180:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=bicubic,framestep=2,setpts=N/(${framerate}*TB)" \
      -an -sn -map_chapters -1 -map_metadata -1 -hide_banner \
      -compression_level 5 -q:v 75 -loop 0 -f webp -y "${i%.*}.webp"

    echo "  Done (evenly-spaced) → ${i%.*}.webp"
  fi
done

echo ""
echo "All done."
