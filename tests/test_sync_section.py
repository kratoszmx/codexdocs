import sys

import sync_section


def test_sync_section_writes_mirrored_url_records(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_section, "all_doc_urls", lambda timeout: [
        "https://developers.openai.com/codex/cli.md",
        "https://developers.openai.com/codex/cli/reference.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
    ])

    written: list[list[str]] = []
    monkeypatch.setattr(sync_section, "write_url_records", lambda rels: written.append(list(rels)))

    sync_calls: list[tuple[list[str], int, bool, int]] = []
    monkeypatch.setattr(
        sync_section,
        "sync_rels",
        lambda rels, timeout, force_download, max_workers: (
            sync_calls.append((list(rels), timeout, force_download, max_workers)) or (2, [])
        ),
    )

    monkeypatch.setattr(sys, "argv", ["sync_section.py", "developers/codex/cli", "--timeout", "11", "--workers", "4"])
    sync_section.main()

    out = capsys.readouterr().out
    assert written == [["developers/codex/cli.md", "developers/codex/cli/reference.md"]]
    assert sync_calls == [(["developers/codex/cli.md", "developers/codex/cli/reference.md"], 11, True, 4)]
    assert "developers/codex/cli: 2" in out
    assert "downloaded: 2" in out
