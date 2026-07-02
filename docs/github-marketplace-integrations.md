# GitHub Apps / Marketplace integration shortlist

Purpose: choose GitHub-platform integrations that work directly with repositories: analyze code, suggest fixes, open PRs, update dependencies, improve security, and improve PR flow.

Policy: do not install third-party GitHub Apps without explicit owner approval. Each app must be installed only on selected repositories, not the full account by default.

## Recommended order

1. GitHub-native features: Dependabot, CodeQL, secret scanning, push protection, branch protection/rulesets, dependency review, CODEOWNERS.
2. Renovate for broader dependency update automation.
3. One code-quality/security SaaS at most, after comparing signal/noise.
4. One AI PR reviewer at most, only if PR volume justifies repo access.
5. Coverage/merge automation only after tests and CI are mature.

## High-fit candidates

| Tool | Category | What it adds | Risk / permissions | Cost note | Recommendation |
| --- | --- | --- | --- | --- | --- |
| GitHub Dependabot | Native dependency/security | Security alerts, security PRs, version update PRs | Native GitHub; lowest risk | Included | Already enabled as baseline; keep. |
| GitHub CodeQL | Native SAST/code scanning | Security/static analysis alerts in GitHub Security | Native GitHub; workflow permissions only | Included for public repos | Already added for `obsidian-operating-layer`; roll out per stack. |
| GitHub Secret Scanning + Push Protection | Native secrets | Detects committed secrets and blocks pushes with supported secret patterns | Native GitHub; public repos verified enabled | Included for public repos; private depends on plan/API | Enabled on public repos; verify private repos in UI later. |
| GitHub Dependency Review Action | Native PR guard | Blocks/flags vulnerable dependency changes in PRs | Native GitHub action | Included | Added to `obsidian-operating-layer`; roll out where package manifests exist. |
| Renovate | Dependency automation | Broader dependency updates than Dependabot, grouping/scheduling, release notes, auto-merge rules | Third-party Mend app; reads/writes PRs/branches; stores repo metadata externally | Marketplace page shows free hosted plan for public/private repos | Strong candidate. Install only after per-repo approval; start with one public repo. |
| OpenSSF Scorecard | Supply-chain posture | Scores branch protection, pinned actions, dangerous workflows, security policy, etc.; uploads SARIF | GitHub Action; no broad app install | Free | Already added for `obsidian-operating-layer`; roll out to public repos. |
| StepSecurity Harden-Runner | Actions security | Monitors/limits outbound network in GitHub Actions; helps stop CI/CD supply-chain attacks | Action/App; can inspect CI network/process behavior | Marketplace app; verify tier before install | Good for repos with deployments/secrets; not urgent for docs-only repos. |
| Semgrep | SAST/custom rules | Fast code/security scanning, custom policies, PR comments/SARIF | Third-party app or action; code is analyzed by Semgrep Cloud unless self-hosted/action-local mode chosen | Free tiers exist; verify current limits | Candidate for Python/security-sensitive repos if CodeQL signal is insufficient. |
| SonarQube Cloud | Quality + security | Bugs, vulnerabilities, code smells, maintainability in PRs | Third-party cloud analyzes code | Free for open source/public; private usually paid tiers | Candidate for public repos; avoid duplicating with Semgrep/Codacy until tested. |
| Codecov / Coveralls | Coverage | Coverage trends and PR coverage comments | Third-party app reads CI artifacts/repo metadata | Free tiers vary | Useful only after coverage reports are produced by tests. Not first wave. |

## AI PR review candidates

| Tool | What it does | Risk | Recommendation |
| --- | --- | --- | --- |
| CodeRabbit | AI PR summaries/reviews, line comments, bug suggestions | Third-party AI gets repository/PR code access; can be noisy | Consider only selected public repo trial; not full-account install. |
| Sourcery | AI code review + security scanning | Third-party AI/code access | Alternative to CodeRabbit; do not run multiple AI reviewers at once. |
| Qodo Merge | AI PR review, bugs/edge cases/security risks | Third-party AI/code access | Candidate if tests are weak and PRs are frequent. |
| Bito AI Code Review Agent | PR summaries/suggestions | Third-party AI/code access | Lower priority; compare only if CodeRabbit/Sourcery rejected. |

## Code-quality alternatives

| Tool | Fit | Recommendation |
| --- | --- | --- |
| Codacy | Broad code quality/security PR checks | Candidate if SonarQube Cloud is not a fit. Avoid stacking with Sonar/Semgrep initially. |
| DeepSource | AI/code quality platform | Candidate for Python repos; test on one public repo only. |
| CodeFactor | Automated code review | Lower priority; evaluate only if lighter/noisier tools fail. |
| Qlty Cloud / Code Climate | Quality and coverage | Useful if we standardize coverage metrics. Not first wave. |

## Security/IaC candidates

| Tool | Fit | Recommendation |
| --- | --- | --- |
| Snyk | Dependencies/container/IaC vulnerabilities and fix PRs | Strong but overlaps with Dependabot/CodeQL/Renovate. Consider for VPN/infra repos after cost/permissions review. |
| GitGuardian | Secrets security | GitHub native secret scanning is already enabled for public repos. Consider only if private repo secret scanning remains unavailable. |
| Bridgecrew / Prisma Cloud Code Security | IaC/security posture | Relevant for `nl-vpn-infra` if it has Terraform/Kubernetes/Docker/IaC. Verify stack first. |
| Socket Security | Malicious dependency risk | Interesting if JS/npm supply-chain risk appears; not first for Python-only repos. |
| Rewind/GitProtect/Cloudback | GitHub backup/restore | Useful for production/compliance; paid/permissions-heavy. Prefer local/gh mirror backup first. |

## Practical next wave

1. Roll out repository files/workflows to `nl-vpn-infra`, `soul-organism-spec-kit`, `ParserRIba`, `ParserRIba2` after checking their stacks.
2. Add branch protection only after each repo has stable required checks.
3. Trial Renovate on `obsidian-operating-layer` or another low-risk public repo.
4. Trial exactly one AI reviewer on a public repo if PR flow becomes active.
5. For `nl-vpn-infra`, evaluate IaC/security scanners separately because it may be more sensitive than normal app repos.

## Do not install by default

- Full-account third-party apps.
- Multiple overlapping AI reviewers.
- Paid security/compliance apps.
- Apps requiring write access to all repositories without narrow selection.
- Apps that upload private repository code to external services without explicit approval.
