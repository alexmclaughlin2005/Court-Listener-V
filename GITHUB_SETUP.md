# GitHub Repository Setup

Your local Git repository is initialized and ready! Follow these steps to push to GitHub.

## Step 1: Create GitHub Repository

### Option A: Via GitHub Website (Recommended)

1. Go to https://github.com/new
2. **Repository name**: `Court-Listener-V` (or your preferred name)
3. **Description**: "Case Law Search and Citation Network Analysis Tool"
4. **Visibility**: Choose Public or Private
5. **DO NOT** check "Initialize with README" (we already have one)
6. **DO NOT** add .gitignore or license (we already have them)
7. Click **"Create repository"**

### Option B: Via GitHub CLI (if installed)

```bash
gh repo create "Court-Listener-V" --public --description "Case Law Search and Citation Network Analysis Tool"
```

## Step 2: Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener V@"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/Court-Listener-V.git

# Push to GitHub
git push -u origin main
```

**Or if you prefer SSH:**

```bash
git remote add origin git@github.com:YOUR_USERNAME/Court-Listener-V.git
git push -u origin main
```

## Step 3: Verify

1. Go to your GitHub repository page
2. Verify all files are uploaded
3. Check that README.md displays correctly

## Troubleshooting

### Authentication Issues

If you get authentication errors:

**For HTTPS:**
- Use a Personal Access Token instead of password
- Create token: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- Use token as password when pushing

**For SSH:**
- Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Large Files

If you have issues with large CSV files:
- CSV files are already in `.gitignore`
- They won't be pushed to GitHub
- You'll upload them directly to Railway later

## Next Steps

After pushing to GitHub:

1. ✅ Proceed to Railway setup (see RAILWAY_CHECKLIST.md)
2. ✅ Railway will connect to your GitHub repo
3. ✅ Auto-deploy on every push

---

**Need help?** Check GitHub docs: https://docs.github.com/en/get-started

