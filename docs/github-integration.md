# GitHub Integration Layer

Status: active for `Lyti4/obsidian-operating-layer`.

## Enabled repository checks

- `verify`: Python 3.11/3.12 matrix, `make verify`, package build smoke.
- `codeql`: GitHub CodeQL Python analysis on push, PR, and weekly schedule.
- `dependency-review`: PR dependency risk gate, fails on high severity.
- `scorecard`: OpenSSF Scorecard SARIF upload on push/schedule/ruleset changes.
- Dependabot version updates for GitHub Actions and Python packaging.
- `labeler`: path-based PR labels for documentation, CI, security, tests, indexing, and GitHub integration.

## Repository security settings target

- Dependabot alerts: enabled.
- Dependabot security updates: enabled when supported by GitHub API.
- Secret scanning: enabled.
- Secret scanning push protection: enabled.
- Secret scanning non-provider patterns: requested, currently disabled by GitHub for this repo.
- Secret scanning validity checks: requested, currently disabled by GitHub for this repo.
- Private vulnerability reporting: enabled.
- Delete branch on merge: enabled.
- Auto-merge: enabled.

## Branch protection target

`main` should require:

- pull request before merge;
- CODEOWNERS review when practical;
- status checks from `verify`, `codeql`, and `scorecard` after their first green run names are confirmed;
- conversation resolution;
- no force-push and no delete.

## Rollout rule for other projects

Apply this layer repo-by-repo after a local green baseline. Do not bulk-enable destructive or blocking rules on all projects until each repository has at least one green CI run and a rollback path.

## Notes

- Scorecard external result publishing is disabled because this workflow uploads SARIF to GitHub code scanning and therefore needs `security-events: write`; OpenSSF external publication rejects workflows with that write permission.

## Actual branch protection

`main` currently requires:

- up-to-date branch before merge;
- `verify / python-3.11`;
- `verify / python-3.12`;
- `codeql / python`;
- `openssf scorecard`;
- one approving review;
- CODEOWNERS review;
- stale review dismissal;
- conversation resolution;
- no force-push;
- no branch deletion.

Admins are not enforced so the owner can still recover the repository if a check misconfiguration blocks normal PR flow.
