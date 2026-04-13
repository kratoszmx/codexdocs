import sys

import sync_all_docs


def test_sync_all_docs_check_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_all_docs, "all_doc_urls", lambda timeout: [
        "https://docs.openclaw.ai/index.md",
        "https://docs.openclaw.ai/gateway/index.md",
    ])
    monkeypatch.setattr(sync_all_docs, "write_url_list", lambda name, urls: None)
    rebuilt: list[list[str]] = []
    monkeypatch.setattr(sync_all_docs, "rebuild_url_records", lambda rels: rebuilt.append(list(rels)))
    monkeypatch.setattr(sync_all_docs, "check_rels", lambda rels: (["index.md"], ["gateway/index.md"]))
    monkeypatch.setattr(sync_all_docs, "sync_rels", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("sync_rels should not run")))

    monkeypatch.setattr(sys, "argv", ["sync_all_docs.py", "--check-only"])
    sync_all_docs.main()

    out = capsys.readouterr().out
    assert "expected_docs=2" in out
    assert "missing=1" in out
    assert "bad=1" in out
    assert rebuilt == [["index.md", "gateway/index.md"]]


def test_sync_all_docs_update_all(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_all_docs, "all_doc_urls", lambda timeout: [
        "https://docs.openclaw.ai/index.md",
        "https://docs.openclaw.ai/gateway/index.md",
    ])
    monkeypatch.setattr(sync_all_docs, "write_url_list", lambda name, urls: None)
    monkeypatch.setattr(sync_all_docs, "rebuild_url_records", lambda rels: None)
    sync_calls: list[tuple[list[str], int, bool]] = []
    monkeypatch.setattr(
        sync_all_docs,
        "sync_rels",
        lambda rels, timeout, force_download: (sync_calls.append((list(rels), timeout, force_download)) or (2, [])),
    )
    monkeypatch.setattr(sync_all_docs, "check_rels", lambda rels: ([], []))

    monkeypatch.setattr(sys, "argv", ["sync_all_docs.py", "--update-all", "--timeout", "9"])
    sync_all_docs.main()

    out = capsys.readouterr().out
    assert "downloaded=2" in out
    assert "postcheck_bad=0" in out
    assert sync_calls == [(["index.md", "gateway/index.md"], 9, True)]
