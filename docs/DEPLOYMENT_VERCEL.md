# Vercel Deployment Guide

This guide walks you through deploying the **Vite + React frontend** to **Vercel** and connecting it to your **FastAPI backend** (hosted on Render, Railway, Fly.io, or Azure).

---

## Architecture Overview

- **Frontend (Vercel)**: Fast global CDN hosting for the Vite/React Single Page Application (`frontend/`).
- **Backend (Render / Cloud)**: Runs the Dockerized FastAPI server, background worker, PostgreSQL, and storage.
- **Communication**: Frontend sends API calls to the backend either directly via `VITE_API_URL` or through Vercel's built-in reverse proxy rewrites.

---

## Option 1: Deploy via Vercel Dashboard (Recommended)

### Step 1: Push your code to GitHub
Make sure your changes are pushed to your GitHub repository:
```bash
git add .
git commit -m "Configure Vercel deployment and CORS support"
git push origin <your-branch>
```

### Step 2: Import the project in Vercel
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **Add New...** -> **Project**.
3. Select your GitHub repository (`ganapathyshree007/cube-03-pack-manager`).
4. In the **Configure Project** screen:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** and select `frontend` *(Important!)*
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
   - **Install Command**: `npm install` (default)

### Step 3: Add Environment Variables in Vercel
Expand the **Environment Variables** section and add:
- `VITE_API_URL`: Your deployed backend URL (e.g. `https://pack-manager-web.onrender.com`)

*(Note: Leave `VITE_API_URL` empty if you prefer using Vercel's proxy rewrites described below).*

### Step 4: Click Deploy
Click **Deploy**. Vercel will install dependencies, build the Vite app, and assign you a live production URL (e.g. `https://cube-03-pack-manager.vercel.app`).

---

## Option 2: Deploy via Vercel CLI

If you prefer using the terminal:

1. In powershell / terminal, navigate to the `frontend` folder:
   ```powershell
   cd frontend
   ```
2. Run Vercel CLI (or install via `npm i -g vercel`):
   ```powershell
   npx vercel
   ```
3. Follow the interactive prompts:
   - Set up and deploy? **Y**
   - Which scope? **Your Account**
   - Link to existing project? **N**
   - What's your project's name? **cube-03-pack-manager**
   - In which directory is your code located? `./`
4. Deploy to production:
   ```powershell
   npx vercel --prod
   ```

---

## Connecting Backend & Handling CORS / Origin Security

The backend includes origin protection against unauthorized cross-site requests. When your frontend is deployed on Vercel:

1. In your backend environment (e.g. on Render dashboard under **Environment Variables** or `.env`):
   ```env
   ALLOWED_ORIGINS=https://cube-03-pack-manager.vercel.app
   ```
   *(You can also use `.vercel.app` to allow all your Vercel preview branch deployments).*
2. Re-deploy or restart the backend service.

---

## Alternative: Using Vercel Proxy Rewrites (Zero-CORS)

If you don't want to use `VITE_API_URL` and prefer same-origin proxying where Vercel forwards `/api/*` to Render:

Edit `frontend/vercel.json` to include your backend URL:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/:match*",
      "destination": "https://your-backend-service.onrender.com/api/:match*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## Verification Checklist

- [ ] Vercel build succeeds (`npm run build` runs with 0 errors).
- [ ] Direct page refresh on any subpath (e.g. `/orders`) works without 404.
- [ ] Frontend can reach `/api/v1/config` and `/api/v1/health/live`.
- [ ] Login (Supabase or Demo session) works with cookies/tokens.
