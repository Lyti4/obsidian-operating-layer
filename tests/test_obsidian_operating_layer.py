import json
from pathlib import Path

from obsidian_operating_layer import scan_vault, write_bundle


def test_scan_vault_counts_markdown(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "b.md").write_text("y", encoding="utf-8")
    obs = scan_vault(tmp_path)
    assert obs.counts["markdown_files"] == 2
    assert set(obs.notes) == {"a.md", "b.md"}


def test_write_bundle_creates_json_and_md(tmp_path: Path):
    payload = {"hello": "world"}
    json_path = write_bundle(tmp_path, "bundle", payload, "Title")
    assert json_path.exists()
    assert (tmp_path / "bundle.md").exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data == payload
