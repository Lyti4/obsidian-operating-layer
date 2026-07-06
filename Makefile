.PHONY: test lint compile verify smoke dashboard-list dashboard-validate live-proposal-only field-slice-example render-diagrams rag-benchmark mcp-benchmark external-tool-benchmark indexing-sandbox indexing-spike indexing-runtime-auto-probe indexing-runtime-stdio-probe-fake swap-drain embedding-resource-preflight resource-preflight graphify-embedding-handoff graphify-embedding-run graphify-embedding-query nanobot-evidence-gateway channel-registry-verify semantic-proposal-report semantic-candidate-decision-packet semantic-targeted-proposal llm-channel-smoke llm-channel-smoke-live semantic-review-index project-docs-lag-audit semantic-manifest

VAULT ?= /home/hermesadmin/Obsidian
PROPOSAL_ROOT ?= out/proposals
FIELD_SLICE_OUT ?= out/field-slices/example
DIAGRAM_OUT ?= out/diagrams/manual-acceptance
REPORT_OUT ?= out/reports/manual-acceptance
RAG_SANDBOX ?= out/sandbox-vaults/rag-benchmark
RAG_REPORTS ?= out/reports/rag-benchmark
MCP_SANDBOX ?= out/sandbox-vaults/mcp-benchmark
MCP_REPORTS ?= out/reports/mcp-benchmark
INDEX_SANDBOX_ROOT ?= out/sandbox-vaults
INDEX_SANDBOX_NAME ?= indexing-spike
INDEX_SANDBOX ?= $(INDEX_SANDBOX_ROOT)/$(INDEX_SANDBOX_NAME)
INDEX_REPORTS ?= out/reports/indexing-spike
INDEX_CANDIDATE ?= docs/spec-kit/research/sample-adapter-records/dalecb-obsidian-semantic-mcp.json
INDEX_RUNTIME_DERIVED ?= out/external-indexing-spike/auto-probe
INDEX_RUNTIME_REPORTS ?= out/reports/external-indexing-spike/auto-probe
INDEX_STDIO_DERIVED ?= out/external-indexing-spike/stdio-probe-fake
INDEX_STDIO_REPORTS ?= out/reports/external-indexing-spike/stdio-probe-fake
LIVE_PROPOSAL_OUT ?= out/live-proposal-only
GRAPHIFY_EMBED_GRAPH ?= out/reports/graphify-embedding-handoff/input/graphify-out/graph.json
GRAPHIFY_EMBED_SANDBOX ?= out/sandbox-vaults/graphify-embedding
GRAPHIFY_EMBED_REPORTS ?= out/reports/graphify-embedding-handoff/manual
GRAPHIFY_EMBED_DERIVED ?= out/external-indexing-spike/graphify-derived/manual
GRAPHIFY_EMBED_MANIFEST ?= $(GRAPHIFY_EMBED_REPORTS)/embedding-manifest.json
GRAPHIFY_EMBED_RUN_REPORTS ?= out/reports/graphify-embedding-runs/manual
GRAPHIFY_EMBED_PROVIDER ?= ollama
GRAPHIFY_EMBED_OLLAMA_BASE_URL ?= http://localhost:11434
GRAPHIFY_EMBED_OLLAMA_MODEL ?= bge-m3
GRAPHIFY_EMBED_MAX_FILES ?= 50
GRAPHIFY_EMBED_MAX_CHARS_PER_FILE ?= 5000
GRAPHIFY_EMBED_MAX_CHARS_PER_CHUNK ?= 500
GRAPHIFY_EMBED_CHUNK_OVERLAP ?= 50
GRAPHIFY_EMBED_OLLAMA_TIMEOUT_SECONDS ?= 360
GRAPHIFY_EMBED_ALLOW_SMOKE_PROVIDER ?=
GRAPHIFY_EMBED_KEEP_OLLAMA_LOADED ?=
GRAPHIFY_EMBED_QUERY_RUN_JSON ?= $(GRAPHIFY_EMBED_RUN_REPORTS)/embedding-run.json
GRAPHIFY_EMBED_QUERY_REPORTS ?= out/reports/graphify-embedding-query-smoke/manual
GRAPHIFY_EMBED_QUERY_TOP_K ?= 8
GRAPHIFY_EMBED_QUERY_1 ?= Obsidian Operating Layer safety boundary
GRAPHIFY_EMBED_QUERY_2 ?= approval manifest backup apply verify
GRAPHIFY_EMBED_QUERY_3 ?= Graphify corpus index cross repository patterns
RESOURCE_MIN_AVAILABLE_MB ?= 1024
RESOURCE_MAX_SWAP_USED_MB ?= 512
RESOURCE_MAX_LOAD_PER_CPU ?= 1.25
RESOURCE_MAX_SWAP_IO_PAGES_PER_SEC ?= 20
SWAP_DRAIN_MIN_POST_AVAILABLE_MB ?= 256
CHANNEL_REGISTRY ?= docs/spec-kit/channel-registry.json
CHANNEL_REGISTRY_REPORTS ?= out/reports/channel-registry-verify/manual
LLM_CHANNEL_SMOKE_REPORTS ?= out/reports/llm-channel-smoke/manual
DASHBOARD_SOURCE ?= docs/obsidian-review-dashboard/index.md
DASHBOARD_VALIDATE_REPORTS ?= out/reports/dashboard-source-validate/manual
SEMANTIC_PROPOSAL_QUERY_JSON ?= out/reports/graphify-embedding-query-smoke/final468-20260704T065635Z/query-smoke.json
SEMANTIC_PROPOSAL_OUT ?= out/proposals/semantic-query-reports/manual
SEMANTIC_PROPOSAL_MAX_CANDIDATES ?= 25
SEMANTIC_DECISION_PROPOSAL_JSON ?= out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/proposal.json
SEMANTIC_DECISION_OUT ?= out/proposals/semantic-candidate-decisions/manual
SEMANTIC_TARGETED_PACKET_JSON ?= out/proposals/semantic-candidate-decisions/final468-operator-review-20260704T105830Z/decision-packet.json
SEMANTIC_TARGETED_OUT ?= out/proposals/semantic-targeted-proposals/manual
SEMANTIC_TARGETED_GROUP ?= link_hygiene_reports
SEMANTIC_REVIEW_INDEX_PROPOSAL_JSON ?= out/proposals/semantic-targeted-proposals/link-hygiene-20260704T112830Z/proposal.json
SEMANTIC_REVIEW_INDEX_OUT ?= out/proposals/semantic-review-indexes/manual
PROJECT_DOCS_LAG_AUDIT_OUT ?= out/reports/project-docs-lag-audit/manual
SEMANTIC_MANIFEST_EMBEDDING_MANIFEST ?= out/reports/graphify-embedding-handoff/full-sandbox-20260703T082644Z/handoff/embedding-manifest.json
SEMANTIC_MANIFEST_EMBEDDING_RUN ?= out/reports/graphify-embedding-runs/step468-final-safe-20260703T192852Z/embedding-run.json
SEMANTIC_MANIFEST_QUERY_SMOKE ?= out/reports/graphify-embedding-query-smoke/final468-20260704T065635Z/query-smoke.json
SEMANTIC_MANIFEST_SEMANTIC_PROPOSAL ?= out/proposals/semantic-query-reports/final468-operator-review-20260704T093433Z/proposal.json
SEMANTIC_MANIFEST_DECISION_PACKET ?= out/proposals/semantic-candidate-decisions/final468-operator-review-20260704T105830Z/decision-packet.json
SEMANTIC_MANIFEST_TARGETED_PROPOSAL ?= out/proposals/semantic-targeted-proposals/link-hygiene-20260704T112830Z/proposal.json
SEMANTIC_MANIFEST_REVIEW_INDEX ?= out/proposals/semantic-review-indexes/link-hygiene-20260704T1200Z/review-index.json
SEMANTIC_MANIFEST_OUT ?= out/reports/semantic-manifests/manual
EXTERNAL_TOOL_BENCHMARK_OUT ?= out/reports/external-tool-benchmark/manual

test:
	python3 -m pytest -q

lint:
	python3 -m ruff check .

compile:
	python3 -m compileall -q .

verify: test lint compile

smoke:
	python3 scripts/smoke.py --vault $(VAULT)

dashboard-list:
	python3 tools/obsidian_review_dashboard.py list --proposal-root $(PROPOSAL_ROOT) --json


dashboard-validate:
	mkdir -p $(DASHBOARD_VALIDATE_REPORTS)
	python3 tools/obsidian_review_dashboard.py validate-source --dashboard $(DASHBOARD_SOURCE) --json --out $(DASHBOARD_VALIDATE_REPORTS)/dashboard-validation.json
	python3 tools/obsidian_review_dashboard.py validate-source --dashboard $(DASHBOARD_SOURCE) --out $(DASHBOARD_VALIDATE_REPORTS)/REPORT.md

live-proposal-only:
	stamp=$$(date -u +%Y%m%dT%H%M%SZ); \
	base="$(LIVE_PROPOSAL_OUT)-$$stamp"; \
	mkdir -p "$$base"; \
	python3 tools/obsidian_observe.py --vault $(VAULT) --out "$$base/observation.json"; \
	python3 tools/obsidian_propose.py --observe "$$base/observation.json" --out-dir "$$base/propose"; \
	python3 tools/obsidian_verify.py --observe "$$base/observation.json" --proposal "$$base/propose/proposal.json" --json-only > "$$base/verify.json"; \
	printf 'BASE=%s\n' "$$base" | tee "$$base/run.env"

field-slice-example:
	python3 tools/obsidian_field_slice.py --vault $(VAULT) --out-root $(FIELD_SLICE_OUT) --task-id make-field-slice-example --decision pending

render-diagrams:
	python3 tools/obsidian_diagram_pdf_report.py --adapter-record docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json --project-root . --diagram-out-dir $(DIAGRAM_OUT) --report-out-dir $(REPORT_OUT)

rag-benchmark:
	python3 tools/obsidian_rag_graph_adapter.py --adapter-record docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json --sandbox-vault $(RAG_SANDBOX) --out-dir $(RAG_REPORTS) --query "Find notes related to Obsidian Operating Layer." --query "Suggest MOC for automation/safety architecture."

mcp-benchmark:
	python3 tools/obsidian_mcp_adapter.py --adapter-record docs/spec-kit/research/sample-adapter-records/cyanheads-obsidian-mcp-server.json --sandbox-vault $(MCP_SANDBOX) --out-dir $(MCP_REPORTS) --probe-tool read_note --probe-tool search_notes --probe-tool write_note

external-tool-benchmark:
	python3 tools/obsidian_external_tool_benchmark.py --out-dir $(EXTERNAL_TOOL_BENCHMARK_OUT)

indexing-sandbox:
	python3 tools/obsidian_sandbox.py --source-vault $(VAULT) --sandbox-root $(INDEX_SANDBOX_ROOT) --name $(INDEX_SANDBOX_NAME) --reset --out $(INDEX_REPORTS)/sandbox-copy.json

indexing-spike: indexing-sandbox
	python3 tools/obsidian_indexing_spike.py --candidate-record $(INDEX_CANDIDATE) --sandbox-vault $(INDEX_SANDBOX) --out-dir $(INDEX_REPORTS) --query "Obsidian Operating Layer safety boundary" --query "approval manifest backup apply verify" --query "wikilinks tags frontmatter knowledge graph"

indexing-runtime-auto-probe: indexing-sandbox
	python3 tools/obsidian_indexing_runtime.py --sandbox-vault $(INDEX_SANDBOX) --derived-root $(INDEX_RUNTIME_DERIVED) --auto-probe-sample --raw-report $(INDEX_RUNTIME_REPORTS)/raw/auto-probe-transcript.json --sanitized-report $(INDEX_RUNTIME_REPORTS)/auto-probe-sanitized-transcript.json --report-root $(INDEX_RUNTIME_REPORTS) --command node --command server.js

indexing-runtime-stdio-probe-fake: indexing-sandbox
	python3 tools/obsidian_indexing_stdio_probe.py --sandbox-vault $(INDEX_SANDBOX) --derived-root $(INDEX_STDIO_DERIVED) --raw-report $(INDEX_STDIO_REPORTS)/raw/transcript.json --sanitized-report $(INDEX_STDIO_REPORTS)/sanitized-transcript.json --report-root $(INDEX_STDIO_REPORTS) --command python3 --command tests/fixtures/fake_jsonline_mcp_server.py --query "Obsidian Operating Layer safety boundary" --timeout-seconds 5


swap-drain:
	python3 tools/obsidian_swap_drain.py --min-post-drain-available-mb $(SWAP_DRAIN_MIN_POST_AVAILABLE_MB)


resource-preflight:
	python3 tools/obsidian_resource_preflight.py --min-available-mb $(RESOURCE_MIN_AVAILABLE_MB) --max-swap-used-mb $(RESOURCE_MAX_SWAP_USED_MB) --max-load-per-cpu $(RESOURCE_MAX_LOAD_PER_CPU) --max-swap-io-pages-per-sec $(RESOURCE_MAX_SWAP_IO_PAGES_PER_SEC)


embedding-resource-preflight: swap-drain resource-preflight


graphify-embedding-handoff: resource-preflight
	python3 tools/obsidian_graphify_embedding_handoff.py --graph-json $(GRAPHIFY_EMBED_GRAPH) --sandbox-vault $(GRAPHIFY_EMBED_SANDBOX) --out-dir $(GRAPHIFY_EMBED_REPORTS) --derived-root $(GRAPHIFY_EMBED_DERIVED) --max-candidates 50


graphify-embedding-run: embedding-resource-preflight
	python3 tools/obsidian_graphify_embedding_run.py --manifest $(GRAPHIFY_EMBED_MANIFEST) --out-dir $(GRAPHIFY_EMBED_RUN_REPORTS) --derived-root $(GRAPHIFY_EMBED_DERIVED) --max-files $(GRAPHIFY_EMBED_MAX_FILES) $(GRAPHIFY_EMBED_ALLOW_SMOKE_PROVIDER) --provider $(GRAPHIFY_EMBED_PROVIDER) --ollama-base-url $(GRAPHIFY_EMBED_OLLAMA_BASE_URL) --ollama-model $(GRAPHIFY_EMBED_OLLAMA_MODEL) --ollama-timeout-seconds $(GRAPHIFY_EMBED_OLLAMA_TIMEOUT_SECONDS) --min-available-mb $(RESOURCE_MIN_AVAILABLE_MB) --max-swap-used-mb $(RESOURCE_MAX_SWAP_USED_MB) --max-load-per-cpu $(RESOURCE_MAX_LOAD_PER_CPU) --max-swap-io-pages-per-sec $(RESOURCE_MAX_SWAP_IO_PAGES_PER_SEC) --dimensions 128 --max-chars-per-file $(GRAPHIFY_EMBED_MAX_CHARS_PER_FILE) --max-chars-per-chunk $(GRAPHIFY_EMBED_MAX_CHARS_PER_CHUNK) --chunk-overlap $(GRAPHIFY_EMBED_CHUNK_OVERLAP) $(GRAPHIFY_EMBED_KEEP_OLLAMA_LOADED)


graphify-embedding-query: resource-preflight
	python3 tools/obsidian_graphify_embedding_query.py --run-json $(GRAPHIFY_EMBED_QUERY_RUN_JSON) --out-dir $(GRAPHIFY_EMBED_QUERY_REPORTS) --top-k $(GRAPHIFY_EMBED_QUERY_TOP_K) --query "$(GRAPHIFY_EMBED_QUERY_1)" --query "$(GRAPHIFY_EMBED_QUERY_2)" --query "$(GRAPHIFY_EMBED_QUERY_3)" --provider $(GRAPHIFY_EMBED_PROVIDER) --ollama-base-url $(GRAPHIFY_EMBED_OLLAMA_BASE_URL) --ollama-model $(GRAPHIFY_EMBED_OLLAMA_MODEL) --ollama-timeout-seconds $(GRAPHIFY_EMBED_OLLAMA_TIMEOUT_SECONDS)


nanobot-evidence-gateway:
	python3 tools/nanobot_readonly_evidence_gateway.py --host 127.0.0.1 --port 18791


channel-registry-verify:
	python3 tools/obsidian_channel_registry_verify.py --registry $(CHANNEL_REGISTRY) --out-dir $(CHANNEL_REGISTRY_REPORTS)

semantic-proposal-report:
	python3 tools/obsidian_semantic_proposal_report.py --query-smoke-json $(SEMANTIC_PROPOSAL_QUERY_JSON) --out-dir $(SEMANTIC_PROPOSAL_OUT) --max-candidates $(SEMANTIC_PROPOSAL_MAX_CANDIDATES)

semantic-candidate-decision-packet:
	python3 tools/obsidian_semantic_candidate_decision_packet.py --semantic-proposal-json $(SEMANTIC_DECISION_PROPOSAL_JSON) --out-dir $(SEMANTIC_DECISION_OUT)


semantic-targeted-proposal:
	python3 tools/obsidian_semantic_targeted_proposal.py --decision-packet-json $(SEMANTIC_TARGETED_PACKET_JSON) --out-dir $(SEMANTIC_TARGETED_OUT) --group $(SEMANTIC_TARGETED_GROUP)

llm-channel-smoke:
	python3 tools/obsidian_llm_channel_smoke.py --registry $(CHANNEL_REGISTRY) --out-dir $(LLM_CHANNEL_SMOKE_REPORTS)

llm-channel-smoke-live:
	python3 tools/obsidian_llm_channel_smoke.py --registry $(CHANNEL_REGISTRY) --out-dir $(LLM_CHANNEL_SMOKE_REPORTS) --live-probes

semantic-review-index:
	python3 tools/obsidian_semantic_review_index.py --targeted-proposal-json $(SEMANTIC_REVIEW_INDEX_PROPOSAL_JSON) --out-dir $(SEMANTIC_REVIEW_INDEX_OUT)

project-docs-lag-audit:
	python3 tools/obsidian_project_docs_lag_audit.py --repo . --out-dir $(PROJECT_DOCS_LAG_AUDIT_OUT)


semantic-manifest:
	python3 tools/obsidian_semantic_manifest.py --repo . --embedding-manifest $(SEMANTIC_MANIFEST_EMBEDDING_MANIFEST) --embedding-run $(SEMANTIC_MANIFEST_EMBEDDING_RUN) --query-smoke $(SEMANTIC_MANIFEST_QUERY_SMOKE) --semantic-proposal $(SEMANTIC_MANIFEST_SEMANTIC_PROPOSAL) --decision-packet $(SEMANTIC_MANIFEST_DECISION_PACKET) --targeted-proposal $(SEMANTIC_MANIFEST_TARGETED_PROPOSAL) --review-index $(SEMANTIC_MANIFEST_REVIEW_INDEX) --out-dir $(SEMANTIC_MANIFEST_OUT)
