import os
import uuid
import asyncio
import subprocess
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Animated Thumbnail Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/tmp/thumb_uploads")
OUTPUT_DIR = Path("/tmp/thumb_outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Settings
NUM_SCENES = 8
SCENE_LENGTH = 1.5
SCENE_DELAY = 0.3
SCENE_THRESHOLD = 0.3


def get_video_info(video_path: str):
    """Get framerate and duration from video."""
    fr_result = subprocess.run([
        "ffprobe", "-v", "0", "-select_streams", "V:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=nw=1:nk=1", video_path
    ], capture_output=True, text=True)

    dur_result = subprocess.run([
        "ffprobe", "-v", "0",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", video_path
    ], capture_output=True, text=True)

    framerate_raw = fr_result.stdout.strip()
    duration_str = dur_result.stdout.strip()

    if not framerate_raw or not duration_str:
        raise ValueError("Could not read video metadata")

    # Parse fraction like "30/1"
    num, den = framerate_raw.split("/")
    framerate = float(num) / float(den) / 2  # halved for animation
    duration = float(duration_str)

    return framerate, duration


def build_evenly_spaced_filter(duration: float, framerate: float) -> str:
    """Build select filter using evenly-spaced time windows."""
    interval = duration / NUM_SCENES
    parts = []
    for n in range(NUM_SCENES):
        start = round(n * interval + 0.5, 3)
        end = round(start + SCENE_LENGTH, 3)
        parts.append(f"between(t\\,{start}\\,{end})")
    select_expr = "+".join(parts)
    scale = "scale=320:180:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=bicubic"
    return f"select='{select_expr}',{scale},framestep=2,setpts=N/({framerate}*TB)"


def build_scene_filter(scene_spacer: float, framerate: float) -> str:
    """Build select filter using scene detection."""
    scale = "scale=320:180:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=bicubic"
    select = (
        f"select=if(gt(scene\\,{SCENE_THRESHOLD})*"
        f"(isnan(prev_selected_t)+gte(t-prev_selected_t\\,{scene_spacer}))"
        f"\\,st(1\\,t)*0*st(2\\,ld(2)+1)"
        f"\\,if(ld(1)*lte(ld(2)\\,{NUM_SCENES})"
        f"\\,between(t\\,ld(1)+{SCENE_DELAY}\\,ld(1)+{SCENE_DELAY}+{SCENE_LENGTH})))"
    )
    return f"{select},{scale},framestep=2,setpts=N/({framerate}*TB)"


async def process_video(video_path: str, output_path: str) -> dict:
    """Process a single video into animated WebP."""
    try:
        framerate, duration = get_video_info(video_path)
        scene_spacer = round(duration / ((NUM_SCENES - 1) * 2), 3)

        logger.info(f"Video: duration={duration}s framerate={framerate} spacer={scene_spacer}")

        # Try scene detection first
        tmp_scene = output_path.replace(".webp", "_tmp.webp")
        scene_filter = build_scene_filter(scene_spacer, framerate)

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-nostdin", "-ss", str(scene_spacer), "-i", video_path,
            "-fps_mode", "vfr",
            "-vf", scene_filter,
            "-an", "-sn", "-map_chapters", "-1", "-map_metadata", "-1",
            "-hide_banner", "-loglevel", "error",
            "-compression_level", "5", "-q:v", "75", "-loop", "0",
            "-f", "webp", "-y", tmp_scene,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        scene_size = os.path.getsize(tmp_scene) if os.path.exists(tmp_scene) else 0

        if scene_size > 1024:
            shutil.move(tmp_scene, output_path)
            method = "scene-detection"
        else:
            if os.path.exists(tmp_scene):
                os.remove(tmp_scene)

            # Fallback: evenly spaced
            fallback_filter = build_evenly_spaced_filter(duration, framerate)
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-nostdin", "-i", video_path,
                "-fps_mode", "vfr",
                "-vf", fallback_filter,
                "-an", "-sn", "-map_chapters", "-1", "-map_metadata", "-1",
                "-hide_banner", "-loglevel", "error",
                "-compression_level", "5", "-q:v", "75", "-loop", "0",
                "-f", "webp", "-y", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            method = "evenly-spaced"

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 512:
            raise ValueError("Output file is empty or missing")

        size_kb = round(os.path.getsize(output_path) / 1024, 1)
        return {"success": True, "method": method, "size_kb": size_kb}

    except Exception as e:
        logger.error(f"Error processing {video_path}: {e}")
        return {"success": False, "error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/process")
async def process_videos(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results = []
    job_id = str(uuid.uuid4())[:8]

    for file in files:
        if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm")):
            results.append({
                "filename": file.filename,
                "success": False,
                "error": "Unsupported format. Use MP4, MOV, MKV, AVI, or WEBM."
            })
            continue

        safe_name = f"{job_id}_{uuid.uuid4().hex[:6]}"
        ext = Path(file.filename).suffix
        input_path = str(UPLOAD_DIR / f"{safe_name}{ext}")
        output_path = str(OUTPUT_DIR / f"{safe_name}.webp")

        # Save upload
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        result = await process_video(input_path, output_path)
        result["filename"] = file.filename
        result["output_id"] = safe_name

        # Clean up input
        try:
            os.remove(input_path)
        except Exception:
            pass

        results.append(result)

    return {"results": results}


@app.get("/download/{output_id}")
async def download(output_id: str):
    # Basic path safety check
    if "/" in output_id or ".." in output_id:
        raise HTTPException(status_code=400, detail="Invalid ID")

    output_path = OUTPUT_DIR / f"{output_id}.webp"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired")

    return FileResponse(
        str(output_path),
        media_type="image/webp",
        filename=f"{output_id}.webp"
    )


@app.get("/health")
async def health():
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    return {"status": "ok", "ffmpeg": ffmpeg_ok}
