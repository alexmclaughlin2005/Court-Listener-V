# Fix Vercel "Error Loading Network" Issue

## Problem
The Vercel frontend is showing "Error Loading Network" because it's trying to connect to `http://localhost:8000` instead of your Railway backend.

## Root Cause
The `VITE_API_URL` environment variable is not set in Vercel, so it defaults to localhost.

## Solution

### Step 1: Get Your Railway Backend URL

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click on your backend service
3. Go to **Settings** → **Public Networking**
4. Copy the public domain (e.g., `https://court-listener-v-production.up.railway.app`)

### Step 2: Set Environment Variable in Vercel

#### Option A: Via Vercel Dashboard (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click on your project
3. Go to **Settings** → **Environment Variables**
4. Click **Add New**
5. Set:
   - **Key**: `VITE_API_URL`
   - **Value**: Your Railway URL (e.g., `https://court-listener-v-production.up.railway.app`)
   - **Environments**: Check **Production**, **Preview**, and **Development**
6. Click **Save**

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI if you haven't
npm i -g vercel

# Add the environment variable
vercel env add VITE_API_URL production

# When prompted, paste your Railway backend URL
# Example: https://court-listener-v-production.up.railway.app
```

### Step 3: Redeploy

#### Option A: Via Vercel Dashboard

1. Go to **Deployments** tab
2. Click the three dots (**...**) on the latest deployment
3. Click **Redeploy**
4. Check **Use existing Build Cache** (faster)
5. Click **Redeploy**

#### Option B: Via Git Push

```bash
# Make a small change and push
git commit --allow-empty -m "Trigger Vercel redeploy with API URL"
git push origin main
```

#### Option C: Via Vercel CLI

```bash
cd frontend
vercel --prod
```

### Step 4: Verify

1. Wait for deployment to complete (~2 minutes)
2. Visit your Vercel URL
3. Try to navigate to a citation network page
4. The error should be gone!

## Verify Environment Variable is Set

After deployment, check the deployment logs or run:

```bash
vercel env ls
```

You should see `VITE_API_URL` listed.

## Additional CORS Configuration (If Still Getting Errors)

If you still see CORS errors after setting `VITE_API_URL`, update Railway backend CORS settings:

1. Go to Railway Dashboard → Backend Service
2. Go to **Variables** tab
3. Add or update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-vercel-app.vercel.app,https://court-listener-v.vercel.app
   ```
4. Railway will automatically redeploy

## Troubleshooting

### Still seeing localhost errors?

**Check**: Build logs in Vercel
- The environment variable is only available at **build time** for Vite
- You must **redeploy** after adding the variable
- Check build logs to confirm: `VITE_API_URL=https://...`

### Getting CORS errors?

**Solution**: Add your Vercel domain to Railway CORS_ORIGINS (see above)

### Railway backend not responding?

**Check**:
- Railway service is running (Dashboard → Service → Status)
- Public networking is enabled (Settings → Public Networking)
- Health check passes: `curl https://your-railway-url.up.railway.app/health`

## Quick Test

Once deployed, open browser console on your Vercel site and run:

```javascript
console.log(import.meta.env.VITE_API_URL)
```

Should print your Railway URL, not `http://localhost:8000`.

---

**Expected Result**: All API calls should now go to your Railway backend instead of localhost.
