# Animated Thumbnail Generator - Expanded By Woxxin20 😎 aka RDX
it's fork verion of [Animated Thumbnail Generator](https://gist.github.com/Voldrix/84a01b602e5d6c53c2b67e156bf26a10)

Converts `.mp4` videos into animated `.webp` thumbnails using FFmpeg.
Works on **one file or many at once**. Uses scene cuts when available, falls back to evenly-spaced frames for low-cut videos.

---

## What You Need

- **Windows 10 or 11**
- **MSYS2** (provides the `bash` terminal)
- **FFmpeg** (does the actual video processing)

---

## Step 1 — Install MSYS2

1. Go to https://www.msys2.org and download the installer
2. Run it, keep all defaults, finish
3. At the end it opens a terminal — close it for now

---

## Step 2 — Install FFmpeg inside MSYS2

1. Open **MSYS2 UCRT64** from the Start menu
2. Paste this and press Enter:

```bash
pacman -S mingw-w64-ucrt-x86_64-ffmpeg
```

3. When asked `Proceed with installation?` type `y` and press Enter
4. Wait for it to finish

**Verify it worked:**

```bash
ffmpeg -version
ffprobe -version
```

Both should print version info. If they do, you're good.

---

## Step 3 — Set Up the Script

1. Create a folder anywhere, e.g. `D:\thumbnail_tool`
2. Save `animated_thumbnail_gen.sh` into that folder
3. Open **MSYS2 UCRT64**
4. Navigate to your folder (replace the path with yours):

```bash
cd /d/thumbnail_tool
```

> **Tip:** Windows path `D:\thumbnail_tool` becomes `/d/thumbnail_tool` in MSYS2

5. Fix line endings (do this once, only needed if you got the file on Windows):

```bash
sed -i 's/\r//' animated_thumbnail_gen.sh
```

6. Make it executable:

```bash
chmod +x animated_thumbnail_gen.sh
```

---

## Step 4 — Run It

Put your `.mp4` files in the same folder as the script, then:

**One file:**

```bash
./animated_thumbnail_gen.sh myvideo.mp4
```

**Multiple specific files:**

```bash
./animated_thumbnail_gen.sh clip1.mp4 clip2.mp4 clip3.mp4
```

**All MP4s in the folder at once:**

```bash
./animated_thumbnail_gen.sh *.mp4
```

Each video gets a `.webp` file next to it with the same name.
Example: `myvideo.mp4` → `myvideo.webp`

---

## Settings (Optional)

Open `animated_thumbnail_gen.sh` in Notepad and look at the top:

```bash
numOfScenes=8      # how many clips to pick (more = longer animation)
sceneLength=1.5    # seconds per clip
sceneDelay=0.3     # skip this many seconds after a scene cut (avoids flash)
sceneThreshold=0.3 # how different frames need to be to count as a scene cut
                   # lower = more sensitive, higher = only big cuts
```

Change any of these numbers and save. No reinstall needed.

---

## Troubleshooting

**`command not found: ffmpeg`**
→ FFmpeg isn't installed or MSYS2 UCRT64 isn't the terminal you opened. Repeat Step 2.

**`permission denied`**
→ Run the `chmod +x` command from Step 3.

**`^M` errors**
→ Run the `sed -i 's/\r//'` command from Step 3.

**Output `.webp` is tiny or 0 bytes**
→ The video is too short or has no scene changes. The script will automatically retry with evenly-spaced frames. If it still fails, check the video plays normally in VLC.

**Script runs but no `.webp` appears**
→ Make sure you're in the right folder. Run `ls *.mp4` to confirm your videos are there.

---

## Viewing the Output

Any modern browser (Chrome, Edge, Firefox) can open `.webp` files directly.
Just drag the `.webp` file into the browser window to preview the animation.


--RDX