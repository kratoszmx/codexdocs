from pathlib import Path

import sync_common
from sync_common import DOCS_ROOT, URLS_DIR, doc_path, is_bad_doc, prune_stale_docs, rebuild_url_records, rels_from_urls, url_record_path, urls_from_rels


def test_rels_from_urls_maps_developers_and_github_sources() -> None:
    urls = [
        "https://developers.openai.com/codex/cli.md",
        "https://developers.openai.com/codex/cli/reference.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
        "https://raw.githubusercontent.com/openai/codex/main/README.md",
    ]

    assert rels_from_urls(urls) == [
        "developers/codex/cli.md",
        "developers/codex/cli/reference.md",
        "github/docs/install.md",
        "github/README.md",
    ]
    assert urls_from_rels(rels_from_urls(urls)) == urls


def test_doc_path_keeps_source_namespace() -> None:
    assert doc_path("developers/codex/cli.md") == DOCS_ROOT / Path("developers/codex/cli.md")
    assert doc_path("github/docs/install.md") == DOCS_ROOT / Path("github/docs/install.md")
    assert doc_path("github/README.md") == DOCS_ROOT / Path("github/README.md")


def test_url_record_path_mirrors_local_docs_structure() -> None:
    assert url_record_path("developers/codex/cli.md") == URLS_DIR / Path("developers/codex/cli.txt")
    assert url_record_path("github/docs/install.md") == URLS_DIR / Path("github/docs/install.txt")
    assert url_record_path("github/README.md") == URLS_DIR / Path("github/README.txt")


def test_prune_stale_docs_removes_old_mirror_files(tmp_path, monkeypatch) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "developers/codex").mkdir(parents=True)
    (docs_root / "github/docs").mkdir(parents=True)
    keep = docs_root / "developers/codex/cli.md"
    stale = docs_root / "legacy/openclaw.md"
    keep.write_text("# keep\n", encoding="utf-8")
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("# stale\n", encoding="utf-8")

    monkeypatch.setattr(sync_common, "DOCS_ROOT", docs_root)

    removed = prune_stale_docs(["developers/codex/cli.md"])

    assert keep.exists()
    assert stale in removed
    assert not stale.exists()



def test_rebuild_url_records_removes_stale_files_and_keeps_indexes(tmp_path, monkeypatch) -> None:
    docs_root = tmp_path / "docs"
    urls_dir = tmp_path / "urls"
    docs_root.mkdir()
    urls_dir.mkdir()

    monkeypatch.setattr(sync_common, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(sync_common, "URLS_DIR", urls_dir)

    (urls_dir / "all.txt").write_text("keep\n", encoding="utf-8")
    (urls_dir / "stale.txt").write_text("stale\n", encoding="utf-8")
    (urls_dir / "github").mkdir()
    (urls_dir / "github" / "old.txt").write_text("stale\n", encoding="utf-8")

    rebuild_url_records(["developers/codex/cli.md", "github/docs/install.md", "github/README.md"])

    assert (urls_dir / "all.txt").exists()
    assert not (urls_dir / "stale.txt").exists()
    assert (urls_dir / "developers/codex/cli.txt").read_text(encoding="utf-8") == (
        "https://developers.openai.com/codex/cli.md\n"
    )
    assert (urls_dir / "github/docs/install.txt").read_text(encoding="utf-8") == (
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md\n"
    )
    assert (urls_dir / "github/README.txt").read_text(encoding="utf-8") == (
        "https://raw.githubusercontent.com/openai/codex/main/README.md\n"
    )
    assert not (urls_dir / "github/old.txt").exists()



def test_is_bad_doc_allows_short_github_redirect_stubs() -> None:
    stub = "# Skills\n\nFor information about skills, refer to [this documentation](https://developers.openai.com/codex/skills).\n"
    assert is_bad_doc("github/docs/skills.md", stub) is False
    assert is_bad_doc("developers/codex/skills.md", stub) is True



def test_sync_rels_supports_parallel_workers(tmp_path, monkeypatch) -> None:
    docs_root = tmp_path / "docs"
    urls_dir = tmp_path / "urls"
    docs_root.mkdir()
    urls_dir.mkdir()

    monkeypatch.setattr(sync_common, "DOCS_ROOT", docs_root)
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
        ["developers/codex/cli.md", "github/docs/install.md"],
        timeout=9,
        force_download=True,
        max_workers=2,
    )

    assert downloaded == 2
    assert failures == []
    assert sorted(calls) == [("developers/codex/cli.md", 9), ("github/docs/install.md", 9)]
