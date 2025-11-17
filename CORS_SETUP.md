# CORS_ORIGINS Configuration

## Current Setup (Local Development)

Set in Railway → Backend Service → **Variables**:

```
CORS_ORIGINS=http://localhost:5173
```

This allows your local frontend (running on port 5173) to make API requests to the backend.

## After Vercel Deployment

Once you deploy the frontend to Vercel, update `CORS_ORIGINS` to include both:

```
CORS_ORIGINS=http://localhost:5173,https://your-app.vercel.app
```

**Important**: Separate multiple URLs with commas (no spaces).

## Format

- **Local**: `http://localhost:5173`
- **Vercel**: `https://your-app.vercel.app` (replace with your actual Vercel URL)
- **Multiple**: `http://localhost:5173,https://your-app.vercel.app` (comma-separated, no spaces)

**Note**: The backend automatically parses comma-separated URLs. You can also use JSON array format if preferred: `["http://localhost:5173","https://your-app.vercel.app"]`

## How to Set in Railway

1. Go to Railway → Your Backend Service
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. **Key**: `CORS_ORIGINS`
5. **Value**: `http://localhost:5173` (for now)
6. Click **"Add"**
7. Railway will auto-redeploy

## After Adding/Changing

Railway will automatically redeploy your backend when you change environment variables. Wait 1-2 minutes for the redeploy to complete.

## Troubleshooting

### CORS Errors in Browser

If you see CORS errors:
1. Verify `CORS_ORIGINS` includes your frontend URL
2. Check the URL matches exactly (including `http://` vs `https://`)
3. Ensure Railway redeployed after changing the variable
4. Check browser console for exact error message

### Testing

After setting CORS_ORIGINS:
1. Start local frontend: `cd frontend && npm run dev`
2. Open browser: `http://localhost:5173`
3. Check browser console for CORS errors
4. Test API calls from frontend

---

**Current Recommendation**: Set to `http://localhost:5173` for now, add Vercel URL after frontend deployment.

