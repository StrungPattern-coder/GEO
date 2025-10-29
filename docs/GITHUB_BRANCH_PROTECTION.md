# GitHub Branch Protection Rules

This guide explains how to set up branch protection rules so that only you can push directly to `main`, while requiring others to submit Pull Requests.

## 🔐 Setting Up Branch Protection

### Step 1: Navigate to Repository Settings

1. Go to your repository: `https://github.com/StrungPattern-coder/GEO`
2. Click **Settings** (top right)
3. In the left sidebar, click **Branches** (under "Code and automation")

### Step 2: Add Branch Protection Rule

1. Click **Add branch protection rule** (or **Add rule**)
2. In **Branch name pattern**, enter: `main`

### Step 3: Configure Protection Rules

Enable the following settings:

#### ✅ **Require a pull request before merging**
- ☑️ Check this box
- **Required approvals**: Set to `1` (or more if you want)
- ☑️ **Dismiss stale pull request approvals when new commits are pushed**
- ☑️ **Require review from Code Owners** (optional, if you create a CODEOWNERS file)

#### ✅ **Require status checks to pass before merging**
- ☑️ Check this box
- Search and select your CI/CD checks (e.g., `build`, `test`, `lint`)
- ☑️ **Require branches to be up to date before merging**

#### ✅ **Require conversation resolution before merging**
- ☑️ Check this box (ensures all review comments are addressed)

#### ✅ **Require signed commits** (optional but recommended)
- ☑️ Check this box for extra security

#### ✅ **Require linear history** (optional)
- ☑️ Check this box to prevent merge commits (forces rebase or squash)

#### ✅ **Do not allow bypassing the above settings**
- ⚠️ **LEAVE THIS UNCHECKED** - This is the key setting!
- When unchecked, **repository admins (you) can bypass these rules**
- Others will be blocked from pushing directly

#### ✅ **Restrict who can push to matching branches**
- ☑️ Check this box
- Click **Add** under "Restrict pushes that create matching branches"
- **DO NOT add anyone** - Leave it empty or only add yourself
- This explicitly restricts direct pushes

#### ✅ **Allow force pushes** 
- Configure this based on your preference:
  - **Specify who can force push**: Select only yourself
  - OR leave unchecked to block all force pushes

#### ✅ **Allow deletions**
- ⚠️ **LEAVE UNCHECKED** - Prevents accidental branch deletion

### Step 4: Save Changes

Click **Create** or **Save changes** at the bottom.

---

## 🎯 What This Achieves

### For You (Repository Owner/Admin):
- ✅ Can push directly to `main` (bypasses protection rules)
- ✅ Can merge PRs without approval
- ✅ Can force push if needed
- ✅ Full control over the repository

### For Contributors:
- ❌ Cannot push directly to `main`
- ✅ Must create a feature branch
- ✅ Must open a Pull Request
- ✅ Must get approval before merging
- ✅ CI/CD checks must pass

---

## 📋 Alternative: Using GitHub Rulesets (New Feature)

GitHub now offers **Repository Rulesets** as a more flexible alternative:

### Navigate to Rulesets
1. Go to **Settings** → **Rules** → **Rulesets**
2. Click **New ruleset** → **New branch ruleset**

### Configure Ruleset
```yaml
Name: Protect main branch
Enforcement status: Active
Bypass list: @StrungPattern-coder (your username)

Target branches: main

Rules:
☑️ Restrict deletions
☑️ Require pull request before merging
   - Required approvals: 1
☑️ Require status checks to pass
☑️ Block force pushes
```

### Benefits of Rulesets:
- More granular control
- Better bypass management
- Easier to maintain multiple rules
- Modern GitHub feature

---

## 👥 Creating a CODEOWNERS File (Optional)

Create `.github/CODEOWNERS` to automatically request reviews from specific people:

```bash
# Default owner for everything
*       @StrungPattern-coder

# Backend code
/src/backend/     @StrungPattern-coder

# Frontend code
/apps/web/        @StrungPattern-coder

# Documentation
/docs/            @StrungPattern-coder

# CI/CD
/.github/         @StrungPattern-coder
```

---

## 🔄 Workflow for Contributors

### 1. Fork & Clone
```bash
# Fork on GitHub, then:
git clone https://github.com/<their-username>/GEO.git
cd GEO
git remote add upstream https://github.com/StrungPattern-coder/GEO.git
```

### 2. Create Feature Branch
```bash
git checkout -b feature/my-awesome-feature
# Make changes
git add .
git commit -m "feat: add awesome feature"
```

### 3. Push to Their Fork
```bash
git push origin feature/my-awesome-feature
```

### 4. Open Pull Request
- Go to their fork on GitHub
- Click **Compare & pull request**
- Submit PR to your `main` branch

### 5. You Review & Merge
- Review the code
- Request changes if needed
- Approve and merge when ready

---

## 🛡️ Additional Security Measures

### 1. Enable Two-Factor Authentication (2FA)
- Go to **Settings** → **Password and authentication**
- Enable 2FA for your account

### 2. Require 2FA for Collaborators
- Repository **Settings** → **Moderation options**
- ☑️ **Require contributors to sign commits**

### 3. Set Up Dependabot
Already in your repo! Check `.github/dependabot.yml`

### 4. Enable Secret Scanning
- Repository **Settings** → **Code security and analysis**
- Enable **Secret scanning**
- Enable **Push protection**

---

## 📊 Verification

After setting up, test with a collaborator:

```bash
# They try to push to main directly
git push origin main
# Should fail with: "refusing to allow a OAuth App to create or update workflow"

# Correct workflow
git checkout -b feature/test
git push origin feature/test
# Then open PR on GitHub ✅
```

---

## 🚨 Emergency Override

If you need to temporarily disable protection (e.g., emergency hotfix):

1. Go to **Settings** → **Branches**
2. Click **Edit** on the protection rule
3. Temporarily disable or bypass
4. Make your changes
5. **Re-enable immediately after!**

---

## 📚 References

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [CODEOWNERS Syntax](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

## ✅ Quick Checklist

- [ ] Navigate to Settings → Branches
- [ ] Add protection rule for `main`
- [ ] Enable "Require pull request before merging"
- [ ] Enable "Require status checks to pass"
- [ ] Enable "Restrict who can push" (leave empty or add only yourself)
- [ ] **Leave "Allow bypassing" UNCHECKED** (so you can bypass)
- [ ] Create `.github/CODEOWNERS` (optional)
- [ ] Test with a test branch
- [ ] Update `CONTRIBUTING.md` with the new workflow

---

**Pro Tip**: After setting this up, add a badge to your README:

```markdown
[![Branch Protection](https://img.shields.io/badge/branch%20protection-enabled-green)]()
```
