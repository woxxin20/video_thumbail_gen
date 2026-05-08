# Deploy to Hugging Face Spaces — Step by Step

Your app will be live at a public URL like:
`https://huggingface.co/spaces/YOUR_USERNAME/thumbgen`

---

## What You Need

- A free Hugging Face account
- Git installed on your PC
- The project folder: `webp-thumbnail-app/`

---

## Step 1 — Create a Hugging Face Account

Go to https://huggingface.co/join and sign up (free).

---

## Step 2 — Install Git (if not already)

Download from https://git-scm.com/download/win and install with all defaults.

Verify in terminal:
```
git --version
```

---

## Step 3 — Create a New Space on Hugging Face

1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Space name:** `thumbgen` (or any name you like)
   - **License:** MIT
   - **SDK:** select **Docker**
   - **Visibility:** Public (so anyone can use it)
3. Click **Create Space**

Your Space is created. It will show a blank page for now — that's normal.

---

## Step 4 — Get Your Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Click **New token**
3. Name it anything, set role to **Write**
4. Copy the token — you'll need it once in the next step

---

## Step 5 — Push the Code

Open a terminal (Command Prompt or Git Bash) and run these commands one by one.

Replace `YOUR_USERNAME` with your actual Hugging Face username:

```bash
# Go into the project folder
cd path\to\webp-thumbnail-app

# Set up git
git init
git add .
git commit -m "first deploy"

# Connect to your Hugging Face Space
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/thumbgen

# Push (it will ask for username + password)
# Username = your HF username
# Password = the token you copied in Step 4
git push origin main
```

> If it asks `branch 'main' doesn't exist`, try:
> ```bash
> git push origin master:main
> ```

---

## Step 6 — Wait for Build

Go to your Space page:
`https://huggingface.co/spaces/YOUR_USERNAME/thumbgen`

Click the **Logs** tab. You'll see it installing FFmpeg and Python packages.
Build takes **2–4 minutes** the first time.

When it says **Running**, your app is live. ✅

---

## Step 7 — Share It

Your public URL is:
```
https://YOUR_USERNAME-thumbgen.hf.space
```

Anyone can open that URL and use the tool — no account needed.

---

## Updating the App Later

If you make changes to any file, push again:

```bash
git add .
git commit -m "update"
git push origin main
```

Hugging Face rebuilds automatically.

---

## Troubleshooting

**Build fails with "port" error**
→ Make sure `Dockerfile` has `EXPOSE 7860` and CMD uses `--port 7860`. Already set correctly.

**"Repository not found" on git push**
→ Double-check the URL has your correct username and space name.

**App shows but videos fail to process**
→ Check the Logs tab on your Space page for the exact FFmpeg error.

**App sleeping / slow to start**
→ Free tier spaces "sleep" after inactivity. First visit after sleep takes ~30 seconds to wake up. Normal behavior.
