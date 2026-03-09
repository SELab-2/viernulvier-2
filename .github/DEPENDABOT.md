# Dependabot Configuration

## Overview

Dependabot automatically monitors and updates dependencies in the repository. It creates pull requests with dependency version updates that can be automatically approved and merged based on configured rules.

## Schedule

All dependency updates run **weekly on Monday at 09:00 UTC**.

## What Gets Monitored

### 1. **npm** (Frontend)
- **Directory:** `/frontend`
- **Limit:** Max 5 open PRs

### 2. **pip** (Backend)
- **Directory:** `/backend/requirements`
- **Limit:** Max 5 open PRs

### 3. **GitHub Actions**
- **Directory:** Root (`/`)
- **Limit:** Max 3 open PRs

## Update Grouping Strategy

Each ecosystem is split into two groups:

### `patch-minor-updates`
- Covers `patch` and `minor` version updates
- **Auto-approve and auto-merge enabled**
- Examples:
  - Django 6.0.2 → 6.0.3 (patch)
  - python-dotenv 1.2.1 → 1.2.2 (patch)
  - faker 40.5.1 → 40.8.0 (minor)

### `major-updates`
- Covers `major` version updates only
- **Manual review required** (not auto-merged)
- Requires human approval due to potential breaking changes
- Examples:
  - i18next 23.16.8 → 25.8.14 (major)

## Auto-Merge Workflow

### How It Works

The workflow in `.github/workflows/dependabot-auto-merge.yml` automatically:

1. **Detects Dependabot PRs** – Runs only on pull requests created by `dependabot[bot]`
2. **Fetches Update Metadata** – Determines the update type (patch, minor, or major)
3. **Approves patch/minor updates** – Uses `actions/github-script` to add an approval
4. **Enables auto-merge** – Uses `actions/github-script` with the `enablePullRequestAutoMerge` GraphQL mutation to enable squash auto-merge for patch/minor updates
5. **Waits for checks** – Auto-merge proceeds once all status checks pass

### Merge Strategy

- **Squash merge** is used for all auto-merged PRs
- Keeps commit history clean by combining all dependency changes into a single commit

### Branch Protection Bypass
- **Dependabot bypass:** Enabled
  - Dependabot (`dependabot[bot]`) can bypass review requirements for patch/minor updates

## Conditions for Auto-Merge

Auto-merge is **enabled only for**:
- ✅ Patch version updates (`version-update:semver-patch`)
- ✅ Minor version updates (`version-update:semver-minor`)

Auto-merge is **skipped for**:
- ❌ Major version updates (`version-update:semver-major`)
- ❌ Any other update types
