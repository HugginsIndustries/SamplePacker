# Repository Rename Completion Checklist

This checklist helps you complete the remaining steps after renaming the repository from SamplePacker to SpectroSampler.

## ✅ Completed Steps

- [x] Repository renamed on GitHub
- [x] Local git remote URL updated
- [x] All code references updated
- [x] All documentation updated
- [x] Package reinstalled with new name
- [x] CI/CD workflows updated

## 📋 Remaining Steps

### Step 3: CI/CD Pipelines

**Status:** ✅ Complete

**Actions taken:**
- ✅ Updated `.github/workflows/ci.yml` with new package name
- ✅ Changed `ruff check samplepacker` → `ruff check spectrosampler`
- ✅ Changed `mypy samplepacker` → `mypy spectrosampler`
- ✅ Changed `pyinstaller samplepacker.spec` → `pyinstaller spectrosampler.spec`
- ✅ Changed executable test from `./dist/samplepacker-gui` → `./dist/spectrosampler-gui`

**Fixed CI error:**
The build job was failing with `ERROR: Spec file "samplepacker.spec" not found!` - this has been resolved by updating the workflow to use `spectrosampler.spec`.

**Note:** If you have any other CI/CD configurations (secrets, environment variables, deployment scripts) that reference the old repository name, update those as well.

---

### Step 4: External Documentation & Links

**Status:** ⚠️ Partially complete

**Actions taken:**
- ✅ README.md updated with actual repository URL
- ✅ Internal documentation updated

**Still need to check:**
- [ ] Any external documentation sites (if you maintain docs elsewhere)
- [ ] Any blog posts or articles mentioning the old repository
- [ ] Any social media posts or announcements
- [ ] Any project pages or websites
- [ ] Any README badges that might reference the old repository URL

**Badge URLs to check:**
If you use GitHub badges in your README, they may need updating:
- Build status badges
- License badges
- Version badges
- Coverage badges

**Example badge URLs:**
```markdown
![GitHub](https://img.shields.io/github/license/HugginsIndustries/SpectroSampler)
![GitHub release](https://img.shields.io/github/v/release/HugginsIndustries/SpectroSampler)
```

---

### Step 5: Webhooks & Integrations

**Status:** ⚠️ Manual verification required

**GitHub Repository Settings:**
1. Go to your repository on GitHub: `https://github.com/HugginsIndustries/SpectroSampler`
2. Navigate to **Settings** → **Webhooks**
3. Review all webhooks and update any that reference the old repository name
4. Check **Settings** → **Integrations** for:
   - Slack integrations
   - Discord bots
   - Email notifications
   - Third-party services

**Common integrations to check:**
- [ ] Slack workspace integrations
- [ ] Discord bot notifications
- [ ] Email notification settings
- [ ] Issue trackers (Jira, Linear, etc.)
- [ ] Project management tools (Trello, Asana, etc.)
- [ ] Code quality tools (CodeClimate, SonarCloud, etc.)
- [ ] Deployment services (Vercel, Netlify, Heroku, etc.)
- [ ] Package managers (npm, pip, etc.) if they reference the repo

**GitHub Apps:**
- Check **Settings** → **Integrations** → **GitHub Apps**
- Review any installed apps that might reference the old name

---

### Step 6: Package Registries

**Status:** ⚠️ Verification needed

**PyPI (Python Package Index):**
- [ ] Check if `samplepacker` was published to PyPI
  - Visit: `https://pypi.org/project/samplepacker/`
  - If it exists, you'll need to:
    1. Publish the new package name `spectrosampler` to PyPI
    2. Update or deprecate the old package
    3. Add a note in the old package README pointing to the new name

**To publish to PyPI:**
```bash
# Build the package
python -m build

# Upload to PyPI (requires PyPI account and credentials)
python -m twine upload dist/*
```

**If you haven't published to PyPI yet:**
- [x] No action needed - package name is already updated in `pyproject.toml`
- When you're ready to publish, use: `twine upload dist/*`

**Other registries to check:**
- [ ] Conda/Anaconda (if applicable)
- [ ] Homebrew (if applicable)
- [ ] Chocolatey (if applicable)
- [ ] Any other package managers you use

---

## 🔍 Additional Verification

### Check GitHub Repository Settings

1. **Repository name** - Should be `SpectroSampler` ✅
2. **Description** - Update if it mentions "SamplePacker"
3. **Topics/Tags** - Update if any reference the old name
4. **About section** - Update website URL if applicable
5. **Releases** - Check if any release notes reference the old name

### Check for Hardcoded URLs

Search for any remaining references:
```bash
# Search for old repository name in files
grep -r "SamplePacker" . --exclude-dir=.git --exclude-dir=build --exclude-dir=dist

# Search for old repository URL patterns
grep -r "github.com.*SamplePacker" . --exclude-dir=.git
```

### Clean Up Old Artifacts

- [x] Removed old `samplepacker.egg-info` directory
- [ ] Consider removing old build artifacts in `build/` directory
- [ ] Consider removing old executables in `dist/` directory (if not needed)

To clean build artifacts:
```bash
# On Windows PowerShell
Remove-Item -Path "build\samplepacker" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist\samplepacker.exe" -Force -ErrorAction SilentlyContinue
```

---

## 📝 Notes

- GitHub automatically redirects old repository URLs to new ones, so existing links will continue to work
- If you have any collaborators, let them know about the rename
- Consider pinning an announcement in GitHub Discussions or adding a note to the repository description about the rename

---

## ✅ Final Verification

Before considering the rename complete, verify:

1. [x] All code references updated
2. [x] All documentation updated
3. [x] Repository URL updated in README
4. [x] CI/CD workflows updated
5. [ ] Webhooks reviewed and updated (if any)
6. [ ] Integrations reviewed and updated (if any)
7. [ ] Package registry status verified
8. [ ] No broken links or references
9. [x] New command works: `spectrosampler-gui`
10. [ ] Can clone repository with new name
11. [ ] All collaborators informed

---

**Last Updated:** After fixing CI/CD workflows

