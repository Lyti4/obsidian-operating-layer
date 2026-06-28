# Diagram and PDF Pipeline

## Goal

Hermes must produce clear, good-looking diagrams and PDF reports for Дмитрий from reproducible source files.

## Ready tools first

Preferred candidates:

- Obsidian Mermaid blocks — fast flow/sequence diagrams inside notes.
- Excalidraw-style Obsidian workflow — human-friendly sketches and architecture maps.
- Mermaid CLI — automated SVG/PDF export from Mermaid source.
- D2 — clean text-to-diagram architecture diagrams.
- Graphviz — dependency graphs and vault relationship maps.
- PlantUML — sequence/component diagrams.
- Typst or Quarto — final PDF assembly from Markdown + diagrams.

## Source/output layout

```text
docs/diagrams/
  architecture.mmd
  safety-sequence.puml
  worker-flow.d2
out/diagrams/
  architecture.svg
  safety-sequence.svg
out/reports/
  obslayer-architecture.pdf
```

## Required diagram set

1. Final component architecture map.
2. Worker orchestration flow.
3. Safety gate sequence: proposal → manifest → backup → apply → verify.
4. Adapter capability map.
5. Vault curation before/after map.
6. MCP/RAG sandbox data flow.

## Pipeline rule

```text
text source -> renderer -> SVG/PNG/PDF -> report assembler -> out/reports
```

Generated PDFs stay in `out/reports/` first. Publishing them into Obsidian is a normal write and must use proposal/apply unless Дмитрий manually places them.

## Acceptance criteria

- Diagram source is text or Obsidian-native where possible.
- PDF can be regenerated from committed source.
- No secrets or private paths beyond approved project/vault paths are exposed.
- Output is visually useful, not just technically valid.
- The report includes generation command and source file paths.

## First proof-of-concept

Build one PDF containing:

- high-level architecture diagram;
- worker queue flow;
- safety sequence;
- one-page explanation.

Use the simplest available installed toolchain first; if missing, record install candidates and keep source diagrams ready.
