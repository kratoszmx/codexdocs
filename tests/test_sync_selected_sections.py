import sys

import sync_selected_sections


SECTIONS = sync_selected_sections.SECTIONS


def test_sync_selected_sections_updates_index_and_mirrored_records(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_selected_sections, "all_doc_urls", lambda timeout: [
        "https://developers.openai.com/codex/cli.md",
        "https://developers.openai.com/codex/quickstart.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
        "https://raw.githubusercontent.com/openai/codex/main/README.md",
    ])

    index_calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(sync_selected_sections, "write_url_list", lambda name, urls: index_calls.append((name, list(urls))))

    record_calls: list[list[str]] = []
    monkeypatch.setattr(sync_selected_sections, "write_url_records", lambda rels: record_calls.append(list(rels)))

    sync_calls: list[tuple[list[str], int, bool, int]] = []
    monkeypatch.setattr(
        sync_selected_sections,
        "sync_rels",
        lambda rels, timeout, force_download, max_workers: (
            sync_calls.append((list(rels), timeout, force_download, max_workers)) or (3, [])
        ),
    )

    monkeypatch.setattr(sys, "argv", ["sync_selected_sections.py", "--timeout", "12", "--workers", "5"])
    sync_selected_sections.main()

    expected_rels = [
        "developers/codex/cli.md",
        "developers/codex/quickstart.md",
        "github/docs/install.md",
    ]
    expected_urls = [
        "https://developers.openai.com/codex/cli.md",
        "https://developers.openai.com/codex/quickstart.md",
        "https://raw.githubusercontent.com/openai/codex/main/docs/install.md",
    ]

    out = capsys.readouterr().out
    assert index_calls == [("selected_sections.txt", expected_urls)]
    assert record_calls == [expected_rels]
    assert sync_calls == [(expected_rels, 12, True, 5)]
    assert "SYNCED 3 files" in out
    for section in SECTIONS:
        assert f"{section}:" in out
