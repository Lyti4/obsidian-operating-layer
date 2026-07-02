# GitHub Integration Layer

Status: active for `Lyti4/obsidian-operating-layer`.

## Enabled repository checks

- `verify`: Python 3.11/3.12 matrix, `make verify`, package build smoke.
- `codeql`: GitHub CodeQL Python analysis on push, PR, and weekly schedule.
- `dependency-review`: PR dependency risk gate, fails on high severity.
- `scorecard`: OpenSSF Scorecard SARIF upload on push/schedule/ruleset changes.
- Dependabot version updates for GitHub Actions and Python packaging.

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
