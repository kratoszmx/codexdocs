import sys

import sync_all_docs


def test_sync_all_docs_check_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_all_docs, "all_doc_urls", lambda timeout: [
        "https://developers.openai.com/codex/cli.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
    ])
    monkeypatch.setattr(sync_all_docs, "write_url_list", lambda name, urls: None)
    rebuilt: list[list[str]] = []
    pruned: list[list[str]] = []
    monkeypatch.setattr(sync_all_docs, "rebuild_url_records", lambda rels: rebuilt.append(list(rels)))
    monkeypatch.setattr(sync_all_docs, "prune_stale_docs", lambda rels: pruned.append(list(rels)))
    monkeypatch.setattr(sync_all_docs, "check_rels", lambda rels: (["developers/codex/cli.md"], ["github/docs/install.md"]))
    monkeypatch.setattr(sync_all_docs, "sync_rels", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("sync_rels should not run")))

    monkeypatch.setattr(sys, "argv", ["sync_all_docs.py", "--check-only"])
    sync_all_docs.main()

    out = capsys.readouterr().out
    assert "expected_docs=2" in out
    assert "missing=1" in out
    assert "bad=1" in out
    assert rebuilt == [["developers/codex/cli.md", "github/docs/install.md"]]
    assert pruned == [["developers/codex/cli.md", "github/docs/install.md"]]



def test_sync_all_docs_update_all(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_all_docs, "all_doc_urls", lambda timeout: [
        "https://developers.openai.com/codex/cli.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
    ])
    monkeypatch.setattr(sync_all_docs, "write_url_list", lambda name, urls: None)
    monkeypatch.setattr(sync_all_docs, "rebuild_url_records", lambda rels: None)
    monkeypatch.setattr(sync_all_docs, "prune_stale_docs", lambda rels: None)
    sync_calls: list[tuple[list[str], int, bool, int]] = []
    monkeypatch.setattr(
        sync_all_docs,
        "sync_rels",
        lambda rels, timeout, force_download, max_workers: (
            sync_calls.append((list(rels), timeout, force_download, max_workers)) or (2, [])
        ),
    )
    monkeypatch.setattr(sync_all_docs, "check_rels", lambda rels: ([], []))

    monkeypatch.setattr(sys, "argv", ["sync_all_docs.py", "--update-all", "--timeout", "9", "--workers", "7"])
    sync_all_docs.main()

    out = capsys.readouterr().out
    assert "downloaded=2" in out
    assert "postcheck_bad=0" in out
    assert sync_calls == [(["developers/codex/cli.md", "github/docs/install.md"], 9, True, 7)]



def test_sync_all_docs_benchmark_outputs_timings(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_all_docs, "all_doc_urls", lambda timeout: [
        "https://developers.openai.com/codex/cli.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
    ])
    monkeypatch.setattr(sync_all_docs, "write_url_list", lambda name, urls: None)
    monkeypatch.setattr(sync_all_docs, "rebuild_url_records", lambda rels: None)
    monkeypatch.setattr(sync_all_docs, "prune_stale_docs", lambda rels: None)
    monkeypatch.setattr(sync_all_docs, "sync_rels", lambda rels, timeout, force_download, max_workers: (2, []))
    monkeypatch.setattr(sync_all_docs, "check_rels", lambda rels: ([], []))

    ticks = iter([100.0, 101.0, 103.0, 109.0, 110.0])
    monkeypatch.setattr(sync_all_docs.time, "perf_counter", lambda: next(ticks))

    monkeypatch.setattr(sys, "argv", ["sync_all_docs.py", "--update-all", "--workers", "7", "--benchmark"])
    sync_all_docs.main()

    out = capsys.readouterr().out
    assert "benchmark_workers=7" in out
    assert "benchmark_index_fetch_seconds=1.000" in out
    assert "benchmark_metadata_seconds=2.000" in out
    assert "benchmark_download_seconds=6.000" in out
    assert "benchmark_postcheck_seconds=1.000" in out
    assert "benchmark_total_seconds=10.000" in out
    assert "benchmark_docs_per_second=0.333" in out
