import sys

import sync_section


def test_sync_section_writes_mirrored_url_records(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_section, "all_doc_urls", lambda timeout: [
        "https://docs.openclaw.ai/tools/browser.md",
        "https://docs.openclaw.ai/tools/read.md",
        "https://docs.openclaw.ai/gateway/index.md",
    ])

    written: list[list[str]] = []
    monkeypatch.setattr(sync_section, "write_url_records", lambda rels: written.append(list(rels)))

    sync_calls: list[tuple[list[str], int, bool]] = []
    monkeypatch.setattr(
        sync_section,
        "sync_rels",
        lambda rels, timeout, force_download: (sync_calls.append((list(rels), timeout, force_download)) or (2, [])),
    )

    monkeypatch.setattr(sys, "argv", ["sync_section.py", "tools", "--timeout", "11"])
    sync_section.main()

    out = capsys.readouterr().out
    assert written == [["tools/browser.md", "tools/read.md"]]
    assert sync_calls == [(["tools/browser.md", "tools/read.md"], 11, True)]
    assert "tools: 2" in out
    assert "downloaded: 2" in out
