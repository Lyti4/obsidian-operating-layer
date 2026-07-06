# Generated report noise policy

Status: accepted after live cleanup on 2026-07-06.

## Problem

Generated reports must not behave like source memory notes. Report-only examples and synthetic navigation links can create hundreds of false broken wikilinks and make the vault look worse than it is.

Observed classes:

- Graphify `_COMMUNITY_*` navigation links that do not correspond to real notes.
- Report sample sections listing broken links with raw `[[wikilink]]` syntax.
- Placeholder examples such as `[[Title]]`, `[[...]]`, `[[Memory-Vault/...|Title]]`.
- Report references to generated JSON artifacts that are files, not memory notes.
- Soul/protected links that require explicit cross-vault policy, not bulk mutation.

## Policy

1. Generated report samples must render example wikilinks as literals, not active Obsidian links:
   - use escaped form: `\[\[Example\]\]`, or
   - put examples inside code spans/blocks and make the scanner ignore inline/fenced code.
2. Graphify community navigation must not create note links unless files are actually generated:
   - if the community section exists in the same report, link to the local heading anchor;
   - if the community is omitted/thin, render it as plain text.
3. Empty/synthetic report navigation is evidence, not memory. Do not create hundreds of placeholder notes only to satisfy generated links.
4. Active-vault hygiene scans must exclude `_Backups`, `_Archive`, `.trash`, hidden paths, and should ignore inline/fenced code examples.
5. Soul/protected/cross-vault links stay in a separate policy bucket. Do not auto-fix them as Memory-Vault links without explicit approval.

## Verification baseline after cleanup

Memory-Vault active-only, excluding backups/archive/trash/hidden and ignoring inline code examples:

```text
markdown_files: 313
total wikilinks scanned: 667
ok: 660
ambiguous: 0
broken: 7
```

The remaining 7 are Soul/protected cross-vault links, not generated report garbage.

Evidence:

- `out/proposals/generated-report-noise-cleanup/20260706T0625Z-generated-report-noise-cleanup/apply-result.json`
- `out/proposals/generated-report-noise-cleanup/20260706T0635Z-report-sample-noise-polish/apply-result.json`
- `out/proposals/generated-report-noise-cleanup/20260706T0645Z-final-soul-link-polish/apply-result.json`
- `out/reports/post-generated-report-noise-cleanup/20260706T0645Z-final-active-only/summary.json`

## Code enforcement

The repo observer now enforces this policy in `obsidian_operating_layer/core.py`:

- skips `_Backups`, `_Archive`, `.trash`, hidden paths, `.obsidian`, and tool/cache directories;
- ignores escaped wikilinks;
- masks inline code spans and fenced code blocks before extracting wikilinks;
- resolves candidate targets only against the active markdown file set.

Regression coverage: `tests/test_obslayer.py::test_observe_vault_ignores_report_examples_code_and_archives`.
