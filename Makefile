.PHONY: test lint compile verify smoke dashboard-list field-slice-example render-diagrams rag-benchmark mcp-benchmark

VAULT ?= /home/hermesadmin/Obsidian
PROPOSAL_ROOT ?= out/proposals
FIELD_SLICE_OUT ?= out/field-slices/example
DIAGRAM_OUT ?= out/diagrams/manual-acceptance
REPORT_OUT ?= out/reports/manual-acceptance
RAG_SANDBOX ?= out/sandbox-vaults/rag-benchmark
RAG_REPORTS ?= out/reports/rag-benchmark
MCP_SANDBOX ?= out/sandbox-vaults/mcp-benchmark
MCP_REPORTS ?= out/reports/mcp-benchmark

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

field-slice-example:
	python3 tools/obsidian_field_slice.py --vault $(VAULT) --out-root $(FIELD_SLICE_OUT) --task-id make-field-slice-example --decision pending

render-diagrams:
	python3 tools/obsidian_diagram_pdf_report.py --adapter-record docs/spec-kit/research/sample-adapter-records/diagram-renderer-mermaid-cli.json --project-root . --diagram-out-dir $(DIAGRAM_OUT) --report-out-dir $(REPORT_OUT)

rag-benchmark:
	python3 tools/obsidian_rag_graph_adapter.py --adapter-record docs/spec-kit/research/sample-adapter-records/benmaster82-kwipu.json --sandbox-vault $(RAG_SANDBOX) --out-dir $(RAG_REPORTS) --query "Find notes related to Obsidian Operating Layer." --query "Suggest MOC for automation/safety architecture."

mcp-benchmark:
	python3 tools/obsidian_mcp_adapter.py --adapter-record docs/spec-kit/research/sample-adapter-records/cyanheads-obsidian-mcp-server.json --sandbox-vault $(MCP_SANDBOX) --out-dir $(MCP_REPORTS) --probe-tool read_note --probe-tool search_notes --probe-tool write_note
