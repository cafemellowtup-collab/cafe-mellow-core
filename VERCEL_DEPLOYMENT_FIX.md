# Vercel 250MB Function Size - Fix Applied

## Problem
Vercel was trying to bundle your entire Python backend (FastAPI + pandas + numpy + google-cloud-bigquery + streamlit) as a serverless function, which exceeded the 250MB unzipped limit.

## Solution
Split the deployment architecture:
- **Frontend (Next.js)** → Vercel
- **Backend (FastAPI)** → Cloud Run (or similar)

## Changes Made

### 1. Created `vercel.json`
Configures Vercel to only build the `web/` folder (Next.js frontend):
```json
{
  "buildCommand": "cd web && npm install && npm run build",
  "outputDirectory": "web/.next",
  "installCommand": "cd web && npm install",
  "framework": null,
  "ignoreCommand": "echo 'Skipping build check'"
}
```

### 2. Updated `.vercelignore`
Excludes all Python backend code and dependencies:
- All `.py` files
- `requirements.txt` files
- Backend folders: `api/`, `backend/`, `pillars/`, `scheduler/`, `scripts/`, `utils/`
- Python artifacts: `.venv/`, `__pycache__/`, etc.
- Credentials and state files

## Deployment Steps

### Step 1: Deploy Frontend to Vercel

1. **Commit and push** the new `vercel.json` and `.vercelignore`:
   ```bash
   git add vercel.json .vercelignore
   git commit -m "fix: Configure Vercel for frontend-only deployment"
   git push
   ```

2. **Redeploy on Vercel**:
   - Go to your Vercel dashboard
   - Click **Redeploy** on the latest deployment
   - Or push will trigger automatically

3. **Set Environment Variable** in Vercel dashboard:
   - Go to Project Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_BASE_URL` = `https://your-backend-url.run.app`
   - (You'll get this URL after deploying the backend in Step 2)

### Step 2: Deploy Backend to Cloud Run

Your backend is already containerized with `Dockerfile`. Deploy it:

```bash
# From project root
gcloud run deploy cafe-mellow-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=your-project-id,DATASET_ID=your-dataset-id
```

Or use the Cloud Run UI:
1. Go to Cloud Run console
2. Click **Create Service**
3. Select **Deploy from source repository**
4. Connect your GitHub repo
5. Set build source to root directory (uses `Dockerfile`)
6. Configure environment variables from `.env`

### Step 3: Update Frontend Environment Variable

After backend deploys, you'll get a Cloud Run URL like:
`https://cafe-mellow-backend-xxxxx-uc.a.run.app`

1. Copy this URL
2. Go to Vercel → Project Settings → Environment Variables
3. Update `NEXT_PUBLIC_API_BASE_URL` to the Cloud Run URL
4. Redeploy frontend

## Verification

1. **Frontend**: Visit your Vercel URL - should load the Next.js app
2. **Backend**: Visit `https://your-backend-url.run.app/docs` - should show FastAPI docs
3. **Integration**: Test a frontend feature that calls the backend API

## Architecture

```
┌─────────────────┐
│   Vercel        │
│  (Next.js)      │  ← Frontend only, ~50MB
│  Port: 3000     │
└────────┬────────┘
         │
         │ API calls via NEXT_PUBLIC_API_BASE_URL
         │
         ▼
┌─────────────────┐
│  Cloud Run      │
│  (FastAPI)      │  ← Backend with all Python deps
│  Port: 8000     │
└─────────────────┘
```

## Why This Works

- **Vercel**: Optimized for Node.js/Next.js, 250MB serverless limit
- **Cloud Run**: Supports containers, no size limit (up to 32GB memory)
- **Separation**: Each platform handles what it's best at

## Rollback

If you need to rollback, delete `vercel.json` and revert `.vercelignore` to only exclude build artifacts (not source code).
