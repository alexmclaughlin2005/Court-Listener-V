# Vercel Environment Variables Setup

Your backend URL: `https://court-listener-v-production.up.railway.app`

## Step 1: Deploy to Vercel

1. Go to https://vercel.com
2. Click "Add New..." → "Project"
3. Import your GitHub repository: `Court-Listener-V`
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (auto-detected)
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)

## Step 2: Set Environment Variable

Before deploying, add environment variable:

1. In Vercel project settings → **Environment Variables**
2. Add new variable:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://court-listener-v-production.up.railway.app`
   - **Environment**: Production, Preview, Development (select all)
3. Click **Save**

## Step 3: Deploy

1. Click **Deploy**
2. Wait for build to complete
3. Vercel will provide a URL (e.g., `https://your-app.vercel.app`)

## Step 4: Update Backend CORS

After Vercel deployment, update Railway backend CORS:

1. Go to Railway → Your Backend Service → **Variables**
2. Update `CORS_ORIGINS`:
   ```
   https://your-app.vercel.app,http://localhost:3000
   ```
3. Save (Railway will auto-redeploy)

## Step 5: Test

1. Visit your Vercel URL
2. Open browser console (F12)
3. Check for API connection errors
4. Test search functionality

## Troubleshooting

### CORS Errors

- Verify `CORS_ORIGINS` includes your Vercel URL
- Check backend logs in Railway
- Ensure backend was redeployed after CORS change

### API Connection Errors

- Verify `VITE_API_URL` is set in Vercel
- Check environment variable is available at build time
- Test backend directly: `curl https://court-listener-v-production.up.railway.app/health`

---

**Backend URL**: `https://court-listener-v-production.up.railway.app`
**API Docs**: `https://court-listener-v-production.up.railway.app/docs`

