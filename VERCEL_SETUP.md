# Vercel Setup Guide

## Prerequisites

- Railway backend deployed and running
- Backend URL (e.g., `https://your-app.up.railway.app`)

## Step 1: Create Vercel Account & Project

1. Go to https://vercel.com
2. Sign up/login with GitHub
3. Click "Add New..." → "Project"
4. Import your GitHub repository: `Court Listener V@`

## Step 2: Configure Project

1. **Root Directory**: Set to `frontend`
2. **Framework Preset**: Vite (auto-detected)
3. **Build Command**: `npm run build` (auto-detected)
4. **Output Directory**: `dist` (auto-detected)
5. **Install Command**: `npm install` (auto-detected)

## Step 3: Set Environment Variables

In Vercel project settings → Environment Variables, add:

```
VITE_API_URL=https://your-backend.up.railway.app
```

Replace `your-backend.up.railway.app` with your actual Railway backend URL.

## Step 4: Deploy

1. Click "Deploy"
2. Wait for build to complete
3. Vercel will provide a URL (e.g., `https://your-app.vercel.app`)

## Step 5: Update Backend CORS

Go back to Railway backend → Environment Variables:

```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

Redeploy backend if needed.

## Step 6: Verify Deployment

1. Visit your Vercel URL
2. Test search functionality
3. Check browser console for API errors

## Custom Domain (Optional)

1. In Vercel project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

## Next Steps

- Test the full application
- Import data via Railway backend
- Monitor performance and errors

