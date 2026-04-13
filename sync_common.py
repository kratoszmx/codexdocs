#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from tqdm.auto import tqdm

import project_env  # noqa: F401
from http_utils import fetch_bytes, fetch_text
from markdown_utils import count_markdown_body_lines, is_empty_or_sparse_markdown

ROOT = Path(__file__).resolve().parent
DOCS_ROOT = ROOT / "docs"
OTHERS_ROOT = DOCS_ROOT / "others"
URLS_DIR = ROOT / "urls"
LLMS_URL = "https://docs.openclaw.ai/llms.txt"
DOC_PREFIX = "https://docs.openclaw.ai/"
LOCAL_OTHERS_SECTIONS = frozenset({"automation", "debug", "diagnostics", "nodes", "plugins", "security", "start", "web"})


def body_line_count(text: str) -> int:
    return count_markdown_body_lines(text)


def is_empty_or_truncated(text: str) -> bool:
    return is_empty_or_sparse_markdown(text)


def extract_doc_urls(llms_text: str) -> list[str]:
    return sorted(set(re.findall(r"https://docs\.openclaw\.ai/[^\s)]+\.md", llms_text)))


def all_doc_urls(timeout: int = 45) -> list[str]:
    return extract_doc_urls(fetch_text(LLMS_URL, timeout=timeout))


def rels_from_urls(urls: list[str]) -> list[str]:
    return [url.replace(DOC_PREFIX, "") for url in urls]


def urls_from_rels(rels: list[str]) -> list[str]:
    return [DOC_PREFIX + rel for rel in rels]


def local_doc_rel(rel: str) -> Path:
    """Map a docs.openclaw.ai relative path to the local path under `docs/`.

    Local layout rule:
    - root-level markdown files are grouped under `docs/others/`
    - selected top-level sections also live under `docs/others/<section>/`
    - all other nested docs keep their original section path under `docs/`
    """
    rel_path = Path(rel)
    if rel_path.parts[:1] == ("others",):
        return rel_path
    if rel_path.parent == Path("."):
        return Path("others") / rel_path.name
    if rel_path.parts[0] in LOCAL_OTHERS_SECTIONS:
        return Path("others") / rel_path
    return rel_path


def site_rel_from_local(local_rel: str | Path) -> str:
    """Invert a local `docs/` relative path back to a site-relative path."""
    local_path = Path(local_rel)
    if local_path.parts[:1] != ("others",):
        return local_path.as_posix()
    if len(local_path.parts) == 2:
        return local_path.name
    if local_path.parts[1] in LOCAL_OTHERS_SECTIONS:
        return Path(*local_path.parts[1:]).as_posix()
    return local_path.as_posix()


def doc_path(rel: str) -> Path:
    """Map a docs.openclaw.ai relative markdown path to the local mirror path.

    Local layout rule:
    - root-level markdown files are grouped under `docs/others/`
    - selected top-level sections also live under `docs/others/<section>/`
    - all other nested docs keep their original section path under `docs/`
    """
    return DOCS_ROOT / local_doc_rel(rel)


def ensure_dirs() -> None:
    DOCS_ROOT.mkdir(exist_ok=True)
    OTHERS_ROOT.mkdir(exist_ok=True)
    URLS_DIR.mkdir(exist_ok=True)


def write_url_list(name: str, urls: list[str]) -> None:
    ensure_dirs()
    (URLS_DIR / name).write_text("\n".join(urls) + "\n", encoding="utf-8")


def url_record_path(rel: str) -> Path:
    """Return the mirrored URL-record path under `urls/` for a doc rel path.

    The `urls/` tree mirrors the local `docs/` tree. Examples:
    - `gateway/configuration.md` -> `urls/gateway/configuration.txt`
    - root-level `index.md` -> `urls/others/index.txt`
    - `automation/index.md` -> `urls/others/automation/index.txt`
    """
    local_rel = local_doc_rel(rel)
    return (URLS_DIR / local_rel).with_suffix(".txt")


def write_url_record(rel: str) -> Path:
    ensure_dirs()
    path = url_record_path(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DOC_PREFIX + rel + "\n", encoding="utf-8")
    return path


def write_url_records(rels: list[str]) -> list[Path]:
    return [write_url_record(rel) for rel in rels]


def nested_others_rels_from_docs() -> list[str]:
    """Return unambiguous site rels recoverable from the local docs tree.

    Local `docs/others/*.md` at the top level can be ambiguous because root-level
    docs are also grouped there. Nested paths like `docs/others/web/index.md`
    or `docs/others/custom/index.md` map unambiguously back to a site rel.
    """
    rels: list[str] = []
    for path in DOCS_ROOT.rglob("*.md"):
        local_rel = path.relative_to(DOCS_ROOT)
        if local_rel.parts[:1] == ("others",) and len(local_rel.parts) > 2:
            rels.append(site_rel_from_local(local_rel))
    return sorted(set(rels))


def rebuild_url_records(rels: list[str], keep_root_files: set[str] | None = None) -> list[Path]:
    """Rewrite mirrored URL records so `urls/` matches the local `docs/` tree.

    Root index files such as `all.txt` can be kept via `keep_root_files`.
    All other stale `.txt` files under `urls/` are removed.
    """
    ensure_dirs()
    keep_root = {"all.txt", "selected_sections.txt"} if keep_root_files is None else set(keep_root_files)
    all_rels = sorted(set(rels) | set(nested_others_rels_from_docs()))
    desired = {url_record_path(rel).relative_to(URLS_DIR) for rel in all_rels}

    for path in sorted(URLS_DIR.rglob("*.txt")):
        rel_path = path.relative_to(URLS_DIR)
        if rel_path.parent == Path(".") and rel_path.name in keep_root:
            continue
        if rel_path not in desired:
            path.unlink()

    written = write_url_records(all_rels)

    for path in sorted((p for p in URLS_DIR.rglob("*") if p.is_dir()), reverse=True):
        if path == URLS_DIR:
            continue
        if any(path.iterdir()):
            continue
        path.rmdir()

    return written


def filter_rels_by_prefix(rels: list[str], prefix: str) -> list[str]:
    return [rel for rel in rels if rel.startswith(prefix + "/")]


def filter_rels_by_prefixes(rels: list[str], prefixes: list[str]) -> list[str]:
    allowed = tuple(prefix + "/" for prefix in prefixes)
    return [rel for rel in rels if rel.startswith(allowed)]


def download_rel(rel: str, timeout: int = 45) -> tuple[bool, str | None]:
    url = DOC_PREFIX + rel
    path = doc_path(rel)
    try:
        data = fetch_bytes(url, timeout=timeout)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except Exception as exc:  # noqa: BLE001
        return False, f"download:{exc}"

    text = path.read_text(encoding="utf-8", errors="ignore")
    if is_empty_or_truncated(text):
        try:
            data = fetch_bytes(url, timeout=timeout)
            path.write_bytes(data)
        except Exception as exc:  # noqa: BLE001
            return False, f"redownload:{exc}"
    return True, None


def sync_rels(rels: list[str], timeout: int = 45, force_download: bool = True) -> tuple[int, list[tuple[str, str]]]:
    ensure_dirs()
    downloaded = 0
    failures: list[tuple[str, str]] = []

    progress = tqdm(rels, desc="sync docs", unit="file")
    for rel in progress:
        path = doc_path(rel)
        need_download = force_download or (not path.exists())
        if not need_download:
            text = path.read_text(encoding="utf-8", errors="ignore")
            need_download = is_empty_or_truncated(text)
        if not need_download:
            progress.set_postfix(downloaded=downloaded, failures=len(failures), refresh=False)
            continue

        ok, err = download_rel(rel, timeout=timeout)
        if ok:
            downloaded += 1
        else:
            failures.append((rel, err or "unknown"))
        progress.set_postfix(downloaded=downloaded, failures=len(failures), refresh=False)

    return downloaded, failures


def check_rels(rels: list[str]) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    bad: list[str] = []
    progress = tqdm(rels, desc="check docs", unit="file")
    for rel in progress:
        path = doc_path(rel)
        if not path.exists():
            missing.append(rel)
            progress.set_postfix(missing=len(missing), bad=len(bad), refresh=False)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if is_empty_or_truncated(text):
            bad.append(rel)
        progress.set_postfix(missing=len(missing), bad=len(bad), refresh=False)
    return missing, bad
