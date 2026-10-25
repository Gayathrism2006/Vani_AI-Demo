# 🚀 Deploying Vani AI to Vercel & Production

## Architecture Overview
Vani AI is composed of:
1. **Frontend**: React 18 + Vite SPA with real-time Web Speech recognition and audio players.
2. **Backend**: FastAPI with PyTorch, OpenVoice neural voice cloning, ElevenLabs Audio Isolation & STT, and SQLite.

> [!IMPORTANT]
> **Why Vercel + Backend Host?**
> Vercel is a **serverless** platform designed for frontends and lightweight serverless functions (max function size: **250 MB**, max execution time: **10s**). 
> The PyTorch AI voice engine (`torch`, `torchaudio`, and OpenVoice checkpoints) requires **~1.5 GB**, system C-libraries (`ffmpeg`, `libsndfile`), and persistent disk storage.
> 
> The production standard is:
> - **Frontend**: Deployed to **Vercel** (Global Edge CDN, instantaneous loads).
> - **Backend**: Deployed to a container host like **Render**, **Railway**, **Fly.io**, or **AWS** (Full PyTorch & GPU/CPU support).
> - All frontend requests to `/api/*` are automatically forwarded to the backend via `vercel.json` rewrites!

---

## Step 1: Deploy Backend (Render / Railway)

### Option A: Render (Free / Easy)
1. Push your repository to **GitHub**.
2. Go to [Render.com](https://render.com) and click **New +** $\rightarrow$ **Web Service**.
3. Connect your repository.
4. Select **Docker** as the Environment (it will automatically use the root `Dockerfile`).
5. Add your Environment Variables under **Environment**:
   - `OPENAI_API_KEY`: `your_openai_key`
   - `ELEVENLABS_API_KEY`: `your_elevenlabs_key`
   - `JWT_SECRET`: `your_jwt_secret`
6. Click **Deploy Web Service**.
7. Copy your assigned Render URL (e.g. `https://vani-ai-backend.onrender.com`).

---

## Step 2: Deploy Frontend to Vercel

1. Go to [Vercel.com](https://vercel.com) and click **Add New...** $\rightarrow$ **Project**.
2. Import your GitHub repository.
3. In Project Settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (or leave default root with root `vercel.json`)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Update `vercel.json`:
   Replace `https://YOUR_BACKEND_URL` with your actual backend URL from Step 1:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://vani-ai-backend.onrender.com/api/:path*"
       },
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
5. Click **Deploy**.

---

## Local Development
To run everything locally on your machine:
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000).
