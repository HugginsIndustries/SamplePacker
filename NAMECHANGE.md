# Repository Rename Instructions

This document provides instructions for renaming the repository from "SamplePacker" to "SpectroSampler" on GitHub/GitLab/etc.

## GitHub

### Method 1: Via GitHub Web Interface

1. Navigate to your repository on GitHub
2. Go to **Settings** (gear icon in the repository navigation)
3. Scroll down to the **Repository name** section
4. Enter the new name: `SpectroSampler`
5. Click **Rename**

### Method 2: Via GitHub CLI

```bash
gh repo rename SpectroSampler
```

### Method 3: Via Git (if you have admin access)

1. Update your local remote URL:
   ```bash
   git remote set-url origin https://github.com/YOUR_USERNAME/SpectroSampler.git
   ```

2. Push to the new repository:
   ```bash
   git push -u origin main
   ```

## GitLab

1. Navigate to your repository on GitLab
2. Go to **Settings** → **General**
3. Expand the **Project name** section
4. Change the project name to `SpectroSampler`
5. Click **Save changes**

## After Renaming

1. **Update local repository remote URL:**
   ```bash
   git remote set-url origin <NEW_REPOSITORY_URL>
   ```

2. **Verify the change:**
   ```bash
   git remote -v
   ```

3. **Update any CI/CD pipelines** that reference the old repository name

4. **Update any external documentation** or links that reference the old repository name

5. **Update any webhooks** or integrations that use the repository name

6. **Update any package registries** (PyPI, etc.) if the package name is tied to the repository name

## Notes

- GitHub will automatically redirect old repository URLs to the new name
- Existing clones will continue to work, but new clones should use the new URL
- Update any bookmarks, documentation, or references to the repository URL
- If you use GitHub Pages, the URL structure may change (check GitHub Pages settings)

## Verification

After renaming, verify everything works:

1. Clone the repository with the new name:
   ```bash
   git clone <NEW_REPOSITORY_URL>
   cd SpectroSampler
   ```

2. Run the application:
   ```bash
   spectrosampler-gui
   ```

3. Verify all imports and references work correctly

