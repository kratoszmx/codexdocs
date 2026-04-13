import sys

import sync_selected_sections


SECTIONS = sync_selected_sections.SECTIONS


def test_sync_selected_sections_updates_index_and_mirrored_records(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sync_selected_sections, "all_doc_urls", lambda timeout: [
        "https://docs.openclaw.ai/tools/browser.md",
        "https://docs.openclaw.ai/install/docker.md",
        "https://docs.openclaw.ai/gateway/index.md",
        "https://docs.openclaw.ai/concepts/agent.md",
    ])

    index_calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(sync_selected_sections, "write_url_list", lambda name, urls: index_calls.append((name, list(urls))))

    record_calls: list[list[str]] = []
    monkeypatch.setattr(sync_selected_sections, "write_url_records", lambda rels: record_calls.append(list(rels)))

    sync_calls: list[tuple[list[str], int, bool]] = []
    monkeypatch.setattr(
        sync_selected_sections,
        "sync_rels",
        lambda rels, timeout, force_download: (sync_calls.append((list(rels), timeout, force_download)) or (3, [])),
    )

    monkeypatch.setattr(sys, "argv", ["sync_selected_sections.py", "--timeout", "12"])
    sync_selected_sections.main()

    expected_rels = ["tools/browser.md", "install/docker.md", "gateway/index.md"]
    expected_urls = [f"https://docs.openclaw.ai/{rel}" for rel in expected_rels]

    out = capsys.readouterr().out
    assert index_calls == [("selected_sections.txt", expected_urls)]
    assert record_calls == [expected_rels]
    assert sync_calls == [(expected_rels, 12, True)]
    assert "SYNCED 3 files" in out
    for section in SECTIONS:
        assert f"{section}:" in out
