# GitHub integration rollout policy

This document is the reusable GitHub operating baseline for Dmitry/Lyti4 repositories.

**Статус:** `active-policy` с `historical` account/repository snapshot. Все
утверждения ниже о том, что уже применено, API/plan limits и repository status
являются прошлым снимком и проверяются repo-by-repo через GitHub перед
использованием. Этот файл не расширяет полномочия проекта на другие repositories.

## Historical applied-baseline snapshot

Recorded as applied to public repositories when GitHub API supported it:

- Dependabot vulnerability alerts.
- Dependabot security updates.
- Secret scanning.
- Secret scanning push protection.
- Issues enabled.
- Auto-merge enabled where GitHub accepts it.
- Delete branch on merge enabled.

Recorded as applied to private repositories where supported:

- Dependabot vulnerability alerts.
- Issues enabled.
- Delete branch on merge enabled.

Historical API limitation: `security_and_analysis` was not returned for private
repositories and a full security patch was rejected. Reverify the current
account plan and repo UI/API; do not report private secret scanning as enabled
from this snapshot.

## Historical repository status snapshot

| Repository | Visibility | Default branch | Security baseline | Branch protection |
| --- | --- | --- | --- | --- |
| `Lyti4/obsidian-operating-layer` | public | `main` | enabled | enabled |
| `Lyti4/nl-vpn-infra` | public | `main` | enabled | not enabled |
| `Lyti4/soul-organism-spec-kit` | public | `master` | enabled | not enabled |
| `Lyti4/ParserRIba` | public | `main` | enabled | not enabled |
| `Lyti4/ParserRIba2` | public | `main` | enabled | not enabled |
| `Lyti4/SkladBotik` | private | `main` | partial/API-limited | not enabled |
| `Lyti4/dmitriy-bogomolov-fly` | private | `main` | partial/API-limited | not enabled |
| `Lyti4/SkladBOta` | private | `main` | partial/API-limited | not enabled |

## Branch protection rule

Enable strict branch protection only after the repository has stable required checks.

Recommended protection:

- require pull request before merge;
- require at least one approving review;
- require CODEOWNERS review when CODEOWNERS exists;
- dismiss stale reviews;
- require conversation resolution;
- require branches to be up to date before merge;
- require project-specific CI checks;
- disallow force-push;
- disallow branch deletion;
- do not enforce admins initially, so the owner can recover from a broken check configuration.

## Standard repository files

Recommended for every active repository:

- `.github/dependabot.yml`;
- `.github/workflows/verify.yml` adapted to project stack;
- `.github/workflows/codeql.yml` when supported;
- `.github/workflows/scorecard.yml` for public repos or when allowed;
- `.github/workflows/dependency-review.yml` for PRs;
- `.github/CODEOWNERS`;
- `.github/pull_request_template.md`;
- `.github/ISSUE_TEMPLATE/bug_report.yml`;
- `.github/ISSUE_TEMPLATE/feature_request.yml`;
- `.github/workflows/labeler.yml` and `.github/labeler.yml`;
- `SECURITY.md`.

## Marketplace / GitHub App policy

Third-party GitHub Apps can read/write code, issues, pull requests, checks, or secrets-adjacent metadata. Do not install them without explicit owner approval.

Before installing any app, capture:

- vendor and GitHub Marketplace URL;
- permissions requested;
- repositories selected;
- free/paid tier;
- whether it can open PRs automatically;
- whether it stores code externally;
- replacement/overlap with existing GitHub-native features;
- rollback/removal steps.

Preferred order:

1. GitHub-native features first.
2. Open-source GitHub Actions with minimal permissions second.
3. Third-party GitHub Apps only when they provide clear additional value.
4. Paid/high-volume tools only after explicit approval.
