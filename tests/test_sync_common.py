from pathlib import Path

import sync_common
from sync_common import DOCS_ROOT, OTHERS_ROOT, URLS_DIR, doc_path, nested_others_rels_from_docs, rebuild_url_records, url_record_path


def test_doc_path_maps_root_level_docs_to_others() -> None:
    assert doc_path("index.md") == OTHERS_ROOT / "index.md"
    assert doc_path("ci.md") == OTHERS_ROOT / "ci.md"
    assert doc_path("vps.md") == OTHERS_ROOT / "vps.md"


def test_doc_path_keeps_nested_docs_under_original_sections() -> None:
    assert doc_path("tools/browser.md") == DOCS_ROOT / Path("tools/browser.md")
    assert doc_path("gateway/index.md") == DOCS_ROOT / Path("gateway/index.md")
    assert doc_path("reference/templates/USER.md") == DOCS_ROOT / Path("reference/templates/USER.md")


def test_doc_path_maps_selected_top_level_sections_under_others() -> None:
    assert doc_path("automation/index.md") == DOCS_ROOT / Path("others/automation/index.md")
    assert doc_path("nodes/index.md") == DOCS_ROOT / Path("others/nodes/index.md")
    assert doc_path("web/index.md") == DOCS_ROOT / Path("others/web/index.md")


def test_url_record_path_mirrors_local_docs_structure() -> None:
    assert url_record_path("index.md") == URLS_DIR / Path("others/index.txt")
    assert url_record_path("gateway/index.md") == URLS_DIR / Path("gateway/index.txt")
    assert url_record_path("platforms/mac/canvas.md") == URLS_DIR / Path("platforms/mac/canvas.txt")
    assert url_record_path("automation/index.md") == URLS_DIR / Path("others/automation/index.txt")
    assert url_record_path("web/index.md") == URLS_DIR / Path("others/web/index.txt")


def test_nested_others_rels_from_docs_finds_unambiguous_local_docs(tmp_path, monkeypatch) -> None:
    docs_root = tmp_path / "docs"
    others_root = docs_root / "others"
    (others_root / "web").mkdir(parents=True)
    (others_root / "custom").mkdir(parents=True)
    (others_root / "web" / "index.md").write_text("# web\n", encoding="utf-8")
    (others_root / "custom" / "index.md").write_text("# custom\n", encoding="utf-8")
    (others_root / "index.md").write_text("# ambiguous\n", encoding="utf-8")

    monkeypatch.setattr(sync_common, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(sync_common, "OTHERS_ROOT", others_root)

    assert nested_others_rels_from_docs() == ["others/custom/index.md", "web/index.md"]


def test_rebuild_url_records_removes_stale_flat_files_and_keeps_indexes(tmp_path, monkeypatch) -> None:
    docs_root = tmp_path / "docs"
    others_root = docs_root / "others"
    urls_dir = tmp_path / "urls"
    docs_root.mkdir()
    others_root.mkdir(parents=True)
    urls_dir.mkdir()

    monkeypatch.setattr(sync_common, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(sync_common, "OTHERS_ROOT", others_root)
    monkeypatch.setattr(sync_common, "URLS_DIR", urls_dir)

    (urls_dir / "all.txt").write_text("keep\n", encoding="utf-8")
    (urls_dir / "tools.txt").write_text("stale\n", encoding="utf-8")
    (urls_dir / "platforms").mkdir()
    (urls_dir / "platforms" / "old.txt").write_text("stale\n", encoding="utf-8")

    rebuild_url_records(["index.md", "gateway/index.md", "automation/index.md", "web/index.md"])

    assert (urls_dir / "all.txt").exists()
    assert not (urls_dir / "tools.txt").exists()
    assert (urls_dir / "others/index.txt").read_text(encoding="utf-8") == "https://docs.openclaw.ai/index.md\n"
    assert (urls_dir / "gateway/index.txt").read_text(encoding="utf-8") == "https://docs.openclaw.ai/gateway/index.md\n"
    assert (urls_dir / "others/automation/index.txt").read_text(encoding="utf-8") == "https://docs.openclaw.ai/automation/index.md\n"
    assert (urls_dir / "others/web/index.txt").read_text(encoding="utf-8") == "https://docs.openclaw.ai/web/index.md\n"
    assert not (urls_dir / "platforms").exists()


def test_sync_rels_supports_parallel_workers(tmp_path, monkeypatch) -> None:
    docs_root = tmp_path / "docs"
    others_root = docs_root / "others"
    urls_dir = tmp_path / "urls"
    docs_root.mkdir()
    others_root.mkdir(parents=True)
    urls_dir.mkdir()

    monkeypatch.setattr(sync_common, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(sync_common, "OTHERS_ROOT", others_root)
    monkeypatch.setattr(sync_common, "URLS_DIR", urls_dir)

    calls: list[tuple[str, int]] = []

    def fake_download_rel(rel: str, timeout: int = 45):
        calls.append((rel, timeout))
        path = sync_common.doc_path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# ok\n\nline1\nline2\nline3\n", encoding="utf-8")
        return True, None

    monkeypatch.setattr(sync_common, "download_rel", fake_download_rel)

    downloaded, failures = sync_common.sync_rels(
        ["index.md", "gateway/index.md"],
        timeout=9,
        force_download=True,
        max_workers=2,
    )

    assert downloaded == 2
    assert failures == []
    assert sorted(calls) == [("gateway/index.md", 9), ("index.md", 9)]
