# Community Plugin Review — ready Obsidian components

Date: 2026-06-28
Task: `t_141c87d4` / `ool-community-plugin-review`

## Verdict

Use community plugins as UI/read/search/render chunks, not as autonomous mutators. The safe near-term OOL stack is: Dataview + Templater + Tasks + Omnisearch + Virtual Content + Excalidraw, with Metadata Menu/Tag Wrangler as manual UI helpers and Linter/maintenance plugins only in sandbox/proposal mode.

Do not adopt agentic or batch-write plugins (`Vault Operator`, `Superpower Inside`, `File Cooker`, `Auto Note Mover`, link converters, publisher/serializer flows) as live automation until a separate sandbox proves they can be constrained behind `obslayer` proposal/apply.

## Evidence sources

- Official Obsidian registry: `obsidianmd/obsidian-releases/community-plugins.json`.
- Official community stats: `obsidianmd/obsidian-releases/community-plugin-stats.json`.
- GitHub repository metadata via `gh api repos/{owner}/{repo}`.
- Full machine-readable evidence: `docs/spec-kit/research/community-plugin-review-20260628.json`.

## Shortlist

|tier|plugin|repo|downloads|stars|license|registry updated|OOL role|risk note|
|---|---|---|---:|---:|---|---|---|---|
|adopt-now|Dataview|`blacksmithgu/obsidian-dataview`|4,433,626|9,118|MIT|2025-04-07|read/query/dashboard|Low: read/query only when used for dashboards; DataviewJS must be treated as local code and reviewed.|
|adopt-now|Templater|`silentvoid13/Templater`|4,708,142|5,097|AGPL-3.0|2026-06-23|templates/report/proposal/MOC scaffolding|Medium: can execute scripts and create notes; use only for human/manual templates or sandboxed generated proposals.|
|adopt-now|Tasks|`obsidian-tasks-group/obsidian-tasks`|3,700,210|3,829|MIT|2026-06-22|task query layer for review dashboard|Low-medium: writes task status when used interactively; automation should read/query only.|
|adopt-now|Omnisearch|`scambier/obsidian-omnisearch`|1,559,961|2,066|GPL-3.0|2026-05-24|local search UI and evidence lookup|Low-medium: OCR/PDF indexing increases local index surface; keep local-only and exclude secrets/protected paths.|
|adopt-now|Virtual Content|`signynt/virtual-content`|8,617|79|MIT|2026-06-20|non-mutating contextual overlays/dashboard fragments|Low: explicitly displays virtual content without modifying notes; good fit for review hints.|
|adopt-now|Excalidraw|`zsviczian/obsidian-excalidraw-plugin`|6,478,826|7,194|AGPL-3.0|2026-06-17|human-facing diagrams/sketches|Medium: AGPL and large plugin surface; use for manual visual layer, generated sources stay in repo/out first.|
|manual-ui|Metadata Menu|`mdelobelle/metadatamenu`|256,442|702|MIT|2026-02-11|metadata quality/edit UI|Medium: edits frontmatter; allow manual review workflows only, no autonomous bulk mutation.|
|manual-ui|Tag Wrangler|`pjeby/tag-wrangler`|990,782|908|ISC|2025-03-11|tag search/rename/merge UI|High for automation: rename/merge mutates vault-wide tags; manual-only after proposal approval.|
|sandbox-first|Linter|`platers/obsidian-linter`|951,332|1,980|MIT|2026-06-17|markdown/frontmatter normalization|High for automation: formatter mutates notes; only against sandbox/copy or through obslayer proposals.|
|sandbox-first|Find orphaned files and broken links|`vinzent03/find-unlinked-files`|209,929|365|MIT|2024-08-12|orphan/broken-link evidence|Low-medium: evidence plugin; do not delete/move, export findings to proposal/report.|
|sandbox-first|Dangling links|`graydon/obsidian-dangling-links`|18,450|47|MIT|2021-05-18|dangling-link evidence|Low-medium: older/smaller plugin; use as corroborating UI signal, not sole source of truth.|
|sandbox-first|Metadata Extractor|`kometenstaub/metadata-extractor`|26,423|131|MIT|2022-12-20|metadata export for external analysis|Medium: scheduled exporter can leak metadata; outputs must go under out/ and exclude protected paths.|
|sandbox-first|Dataview Serializer|`dsebastien/obsidian-dataview-serializer`|13,489|156|MIT|2026-05-15|materialize Dataview outputs to markdown|Medium-high: writes serialized notes; useful only in sandbox/proposal path.|
|research-track|Smart Connections|`brianpetro/obsidian-smart-connections`|1,058,291|5,218|NOASSERTION|2026-06-04|semantic related-notes/RAG UI|Medium-high: excellent fit for local semantic search, but license reported NOASSERTION and AI/index privacy need separate sandbox review.|
|research-track|Local GPT|`pfrankov/obsidian-local-gpt`|90,542|664|MIT|2026-05-02|local Ollama/OpenAI-compatible assistant|Medium: privacy-friendly local option; ensure no direct edits or external endpoints by default.|
|research-track|Copilot|`logancyang/obsidian-copilot`|1,493,685|7,301|AGPL-3.0|2026-05-21|AI copilot/RAG chat|High: AGPL, external model/API and agentic actions; not a default OOL component before policy sandbox.|
|deny-for-now|Dataview Publisher|`udus122/dataview-publisher`|11,609|69|MIT|2024-11-16|publish/materialize Dataview results|High: publishing/write semantics and lower adoption; avoid until explicit publication scope.|
|deny-for-now|File Cooker|`ivaneye/obsidian-files-cooker`|14,529|64|Apache-2.0|2026-04-06|batch note operations from search/Dataview|High: batch mutation tool; not a ready chunk for autonomous OOL unless wrapped behind proposal gate.|
|deny-for-now|Auto Note Mover|`farux/obsidian-auto-note-mover`|107,987|416|MIT|2022-04-16|rule-based note moves|High/stale: automatic moves are live mutation; only consider after sandbox plus explicit approval.|
|deny-for-now|Link Converter|`ozntel/obsidian-link-converter`|31,898|231|unknown|2024-02-10|bulk link conversion|High: scans and converts links vault-wide; proposal-only, no direct plugin automation.|
|deny-for-now|Vault Operator|`pssah4/vault-operator`|5,772|194|Apache-2.0|2026-06-24|agentic vault operator|High: real AI agent with tools; explicitly unreviewed in registry description, conflicts with obslayer as sole mutation gate.|
|deny-for-now|Superpower Inside|`magnitus99/Superpower-Inside`|1,030|1|MIT|2026-06-26|desktop AI copilot/RAG/MCP|High: unreviewed AI copilot with MCP/tools; defer until separate threat model.|

## Integration tiers

### Adopt now

- `Dataview`: dashboard/query substrate for review boards, proposal indexes, task summaries. Keep DataviewJS reviewed as code.
- `Templater`: human-triggered templates for reports/proposals/MOCs. Do not let templates bypass approval manifests.
- `Tasks`: review/task visibility in Obsidian dashboards; automation reads task state, humans may update manually.
- `Omnisearch`: local search UI for evidence lookup. Exclude secrets/protected folders from indexed surfaces where possible.
- `Virtual Content`: best fit for non-mutating contextual overlays because it displays matched content without modifying notes.
- `Excalidraw`: manual visual thinking layer; repo-generated source diagrams and PDFs still originate under `docs/` and `out/` before vault publication.

### Manual UI only

- `Metadata Menu`: good for data-quality review, but frontmatter edits remain human/manual or proposal-gated.
- `Tag Wrangler`: useful for tag discovery and manual rename/merge; no autonomous tag rewrites.

### Sandbox/proposal only

- `Linter`: formatting is mutation. Run on copied sandbox vault first; convert desired normalization into obslayer proposals.
- `Find orphaned files and broken links`, `Dangling links`, `Broken Links`: evidence sources only; never delete/move directly.
- `Metadata Extractor`: may feed graph/RAG workers, but outputs go under `out/` and protected paths are excluded.
- `Dataview Serializer`: useful to materialize dashboards only after sandbox proof and proposal approval.

### Research track

- `Smart Connections`: strong local semantic related-note candidate; blocked on license clarification and privacy/index sandbox.
- `Local GPT`: promising local/Ollama assistant layer; must be configured as read/propose only.
- `Copilot`: high adoption, but AGPL/API/agentic risks require a separate policy sandbox before use.

### Deny for now

- `Vault Operator`, `Superpower Inside`: agentic vault operators conflict with OOL trust boundary unless separately threat-modeled.
- `File Cooker`, `Auto Note Mover`, `Link Converter`, `Dataview Publisher`: direct/batch write semantics; not safe as default ready chunks.

## Multi-agent triage lanes

|lane|result|
|---|---|
|evidence_check|Registry and GitHub metadata refreshed for 22 focused candidates; no live vault access used.|
|architecture_impact|Plugins map to UI/read/search/render support layers. They do not replace obslayer safety core or worker proposal normalization.|
|safety_and_scope_review|Mutation-capable plugins are manual-only, sandbox-only, or denied. External components may emit findings/proposals, never direct live writes.|

## Acceptance binding

- No live vault writes performed.
- No plugin installed or executed against Дмитрий’s vault.
- Research artifacts are committed under `docs/spec-kit/research/`; transient raw refresh also exists under `out/research/`.
- Next card `ool-github-components-refresh` should refresh non-plugin GitHub components with the same capability/risk schema before Phase 4 RAG adapter work.
