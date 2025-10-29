# 🚀 Quick Setup: Protect Main Branch (5 Minutes)

**Goal**: Only you can push to `main`. Everyone else must use Pull Requests.

---

## ⚡ Quick Steps (TL;DR)

1. Go to: `https://github.com/StrungPattern-coder/GEO/settings/branches`
2. Click **Add branch protection rule**
3. Branch name: `main`
4. Check these boxes:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Restrict who can push to matching branches (leave empty)
   - ⚠️ **UNCHECK** "Do not allow bypassing" (so YOU can push)
5. Click **Create**

**Done!** You can now push directly. Others need PRs.

---

## 📸 Visual Guide

### Step 1: Go to Settings → Branches
```
Your Repo → Settings (top right) → Branches (left sidebar)
```

### Step 2: Add Protection Rule
Click the green **"Add branch protection rule"** button.

### Step 3: Configure Settings

#### Branch name pattern:
```
main
```

#### Protection rules to enable:
```
✅ Require a pull request before merging
   ├─ Required approvals: 1
   └─ Dismiss stale PR approvals when new commits pushed

✅ Require status checks to pass before merging
   ├─ Search for: build, test, lint
   └─ Require branches to be up to date

✅ Require conversation resolution before merging

✅ Restrict who can push to matching branches
   └─ Leave empty (or add only @StrungPattern-coder)

❌ Do not allow bypassing the above settings
   └─ LEAVE UNCHECKED! (This lets admins bypass = you!)

❌ Allow force pushes
   └─ Unchecked (safer)

❌ Allow deletions
   └─ Unchecked (prevents accidents)
```

---

## 🧪 Test It Works

### Test 1: You Can Push (Admin Bypass)
```bash
# You should be able to do this:
echo "# Test" >> test.txt
git add test.txt
git commit -m "test: admin push"
git push origin main
# ✅ Success!
```

### Test 2: Others Cannot Push
If someone else tries:
```bash
git push origin main
# ❌ Error: refusing to allow push to protected branch
```

They must do this instead:
```bash
git checkout -b feature/my-change
git push origin feature/my-change
# Then open PR on GitHub ✅
```

---

## 🔍 Verify Settings

Go to: `https://github.com/StrungPattern-coder/GEO/settings/branches`

You should see:
```
Branch protection rules
─────────────────────
main
├─ Require pull request: ✓
├─ Require status checks: ✓
├─ Restrict pushes: ✓
└─ Allow bypassing: ✗ (unchecked = admins can bypass)
```

---

## 📋 What Each Contributor Must Do

### 1. Fork your repo
On GitHub: Click **Fork** button

### 2. Clone their fork
```bash
git clone https://github.com/their-username/GEO.git
cd GEO
```

### 3. Add your repo as upstream
```bash
git remote add upstream https://github.com/StrungPattern-coder/GEO.git
```

### 4. Create feature branch
```bash
git checkout -b feature/awesome-feature
# Make changes...
git commit -am "feat: add awesome feature"
```

### 5. Push to their fork
```bash
git push origin feature/awesome-feature
```

### 6. Open Pull Request
Go to GitHub → their fork → **Compare & pull request**

### 7. Wait for your review
You review → approve → merge ✅

---

## 🎯 Summary

| Action | You (Admin) | Contributors |
|--------|-------------|--------------|
| Push to main | ✅ Allowed | ❌ Blocked |
| Create branch | ✅ Yes | ✅ Yes (on fork) |
| Open PR | ✅ Yes | ✅ Yes |
| Merge PR | ✅ Yes | ❌ No |
| Force push | ✅ Yes (if enabled) | ❌ No |

---

## 🚨 Troubleshooting

### "I can't push to main either!"
- Check if "Do not allow bypassing" is **UNCHECKED**
- Verify you're logged in as the repo owner
- Check if you have admin rights: Settings → Collaborators

### "Branch protection rule not working"
- Wait 1-2 minutes (GitHub caching)
- Try pushing again
- Check rule is **active** (not draft)

### "Need to make emergency push"
1. Settings → Branches → Edit rule
2. Temporarily disable
3. Make push
4. **Re-enable immediately!**

---

## ✅ Done!

Your `main` branch is now protected. Update your `CONTRIBUTING.md` to tell contributors about the PR workflow!
