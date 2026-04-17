#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

from tqdm.auto import tqdm

import project_env  # noqa: F401
from http_utils import fetch_bytes, fetch_text
from markdown_utils import count_markdown_body_lines, extract_markdown_links, is_empty_or_sparse_markdown

ROOT = Path(__file__).resolve().parent
DOCS_ROOT = ROOT / "docs"
OTHERS_ROOT = DOCS_ROOT / "others"
URLS_DIR = ROOT / "urls"

DEVELOPERS_LLMS_URL = "https://developers.openai.com/codex/llms.txt"
DEVELOPERS_PREFIX = "https://developers.openai.com/"
GITHUB_TREE_API_URL = "https://api.github.com/repos/openai/codex/git/trees/main?recursive=1"
GITHUB_RAW_PREFIX = "https://raw.githubusercontent.com/openai/codex/main/"

DEFAULT_MAX_WORKERS = 6
SELECTED_SECTION_PREFIXES = ["developers/codex", "github/docs"]

CLI_DEVELOPER_EXACT_PATHS = frozenset(
    {
        "codex/agent-approvals-security.md",
        "codex/auth.md",
        "codex/cli.md",
        "codex/config-advanced.md",
        "codex/config-basic.md",
        "codex/config-reference.md",
        "codex/config-sample.md",
        "codex/custom-prompts.md",
        "codex/feature-maturity.md",
        "codex/hooks.md",
        "codex/mcp.md",
        "codex/memories.md",
        "codex/models.md",
        "codex/noninteractive.md",
        "codex/overview.md",
        "codex/plugins.md",
        "codex/prompting.md",
        "codex/quickstart.md",
        "codex/remote-connections.md",
        "codex/rules.md",
        "codex/sdk.md",
        "codex/skills.md",
        "codex/speed.md",
        "codex/subagents.md",
        "codex/windows.md",
        "codex/workflows.md",
    }
)
CLI_DEVELOPER_PREFIXES = (
    "codex/cli/",
    "codex/concepts/",
    "codex/guides/",
    "codex/learn/",
    "codex/plugins/",
)
CLI_GITHUB_DOC_PATHS = frozenset(
    {
        "README.md",
        "AGENTS.md",
        "docs/agents_md.md",
        "docs/authentication.md",
        "docs/config.md",
        "docs/example-config.md",
        "docs/exec.md",
        "docs/execpolicy.md",
        "docs/getting-started.md",
        "docs/install.md",
        "docs/js_repl.md",
        "docs/sandbox.md",
        "docs/skills.md",
        "docs/slash_commands.md",
    }
)


def body_line_count(text: str) -> int:
    return count_markdown_body_lines(text)


def is_empty_or_truncated(text: str) -> bool:
    return is_empty_or_sparse_markdown(text)


def is_bad_doc(rel: str, text: str) -> bool:
    if len(text.strip()) == 0:
        return True
    if rel.startswith("github/docs/"):
        link_count = len(extract_markdown_links(text))
        if body_line_count(text) >= 2 and link_count >= 1:
            return False
    return is_empty_or_sparse_markdown(text)


def is_cli_developer_path(path: str) -> bool:
    return path in CLI_DEVELOPER_EXACT_PATHS or any(path.startswith(prefix) for prefix in CLI_DEVELOPER_PREFIXES)


def extract_developer_doc_urls(llms_text: str) -> list[str]:
    urls = set(re.findall(r"https://developers\.openai\.com/codex/[^\s)]+\.md", llms_text))
    return sorted(url for url in urls if is_cli_developer_path(urlparse(url).path.lstrip("/")))


def developer_doc_urls(timeout: int = 45) -> list[str]:
    return extract_developer_doc_urls(fetch_text(DEVELOPERS_LLMS_URL, timeout=timeout))


def is_github_repo_doc_path(path: str) -> bool:
    return path in CLI_GITHUB_DOC_PATHS


def extract_github_repo_doc_urls(tree_json_text: str) -> list[str]:
    payload = json.loads(tree_json_text)
    tree = payload.get("tree")
    if not isinstance(tree, list):
        message = payload.get("message") if isinstance(payload, dict) else None
        raise RuntimeError(f"unexpected GitHub tree payload: {message or type(payload).__name__}")

    urls: list[str] = []
    for entry in tree:
        if not isinstance(entry, dict) or entry.get("type") != "blob":
            continue
        path = entry.get("path")
        if isinstance(path, str) and is_github_repo_doc_path(path):
            urls.append(GITHUB_RAW_PREFIX + path)
    return sorted(set(urls))


def github_repo_doc_urls(timeout: int = 45) -> list[str]:
    return extract_github_repo_doc_urls(fetch_text(GITHUB_TREE_API_URL, timeout=timeout))


def all_doc_urls(timeout: int = 45) -> list[str]:
    return developer_doc_urls(timeout=timeout) + github_repo_doc_urls(timeout=timeout)


def rel_from_url(url: str) -> str:
    if url.startswith(DEVELOPERS_PREFIX):
        return f"developers/{url[len(DEVELOPERS_PREFIX):]}"
    if url.startswith(GITHUB_RAW_PREFIX):
        return f"github/{url[len(GITHUB_RAW_PREFIX):]}"
    raise ValueError(f"unsupported doc url: {url}")


def rels_from_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    rels: list[str] = []
    for url in urls:
        rel = rel_from_url(url)
        if rel in seen:
            continue
        seen.add(rel)
        rels.append(rel)
    return rels


def url_from_rel(rel: str) -> str:
    if rel.startswith("developers/"):
        return DEVELOPERS_PREFIX + rel.removeprefix("developers/")
    if rel.startswith("github/"):
        return GITHUB_RAW_PREFIX + rel.removeprefix("github/")
    raise ValueError(f"unsupported doc rel: {rel}")


def urls_from_rels(rels: list[str]) -> list[str]:
    return [url_from_rel(rel) for rel in rels]


def doc_path(rel: str) -> Path:
    return DOCS_ROOT / Path(rel)


def ensure_dirs() -> None:
    DOCS_ROOT.mkdir(exist_ok=True)
    URLS_DIR.mkdir(exist_ok=True)


def write_url_list(name: str, urls: list[str]) -> None:
    ensure_dirs()
    (URLS_DIR / name).write_text("\n".join(urls) + "\n", encoding="utf-8")


def url_record_path(rel: str) -> Path:
    return (URLS_DIR / Path(rel)).with_suffix(".txt")


def write_url_record(rel: str) -> Path:
    ensure_dirs()
    path = url_record_path(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(url_from_rel(rel) + "\n", encoding="utf-8")
    return path


def write_url_records(rels: list[str]) -> list[Path]:
    return [write_url_record(rel) for rel in rels]


def nested_others_rels_from_docs() -> list[str]:
    return []


def prune_stale_docs(rels: list[str]) -> list[Path]:
    ensure_dirs()
    desired = {doc_path(rel).relative_to(DOCS_ROOT) for rel in sorted(set(rels))}
    removed: list[Path] = []

    for path in sorted(DOCS_ROOT.rglob("*.md")):
        rel_path = path.relative_to(DOCS_ROOT)
        if rel_path not in desired:
            path.unlink()
            removed.append(path)

    for path in sorted((p for p in DOCS_ROOT.rglob("*") if p.is_dir()), reverse=True):
        if path == DOCS_ROOT:
            continue
        if any(path.iterdir()):
            continue
        path.rmdir()

    return removed


def rebuild_url_records(rels: list[str], keep_root_files: set[str] | None = None) -> list[Path]:
    ensure_dirs()
    keep_root = {"all.txt", "selected_sections.txt"} if keep_root_files is None else set(keep_root_files)
    desired = {url_record_path(rel).relative_to(URLS_DIR) for rel in sorted(set(rels))}

    for path in sorted(URLS_DIR.rglob("*.txt")):
        rel_path = path.relative_to(URLS_DIR)
        if rel_path.parent == Path(".") and rel_path.name in keep_root:
            continue
        if rel_path not in desired:
            path.unlink()

    written = write_url_records(sorted(set(rels)))

    for path in sorted((p for p in URLS_DIR.rglob("*") if p.is_dir()), reverse=True):
        if path == URLS_DIR:
            continue
        if any(path.iterdir()):
            continue
        path.rmdir()

    return written


def _rel_matches_prefix(rel: str, prefix: str) -> bool:
    normalized = prefix.rstrip("/")
    return rel == normalized or rel == normalized + ".md" or rel.startswith(normalized + "/")


def filter_rels_by_prefix(rels: list[str], prefix: str) -> list[str]:
    return [rel for rel in rels if _rel_matches_prefix(rel, prefix)]


def filter_rels_by_prefixes(rels: list[str], prefixes: list[str]) -> list[str]:
    normalized = [prefix.rstrip("/") for prefix in prefixes]
    return [rel for rel in rels if any(_rel_matches_prefix(rel, prefix) for prefix in normalized)]


def download_rel(rel: str, timeout: int = 45) -> tuple[bool, str | None]:
    url = url_from_rel(rel)
    path = doc_path(rel)
    try:
        data = fetch_bytes(url, timeout=timeout)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except Exception as exc:  # noqa: BLE001
        return False, f"download:{exc}"

    text = path.read_text(encoding="utf-8", errors="ignore")
    if is_bad_doc(rel, text):
        try:
            data = fetch_bytes(url, timeout=timeout)
            path.write_bytes(data)
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            return False, f"redownload:{exc}"
        if is_bad_doc(rel, text):
            return False, "content:empty-or-sparse"
    return True, None


def sync_rels(
    rels: list[str],
    timeout: int = 45,
    force_download: bool = True,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> tuple[int, list[tuple[str, str]]]:
    ensure_dirs()
    worker_count = max(1, int(max_workers))
    downloaded = 0
    failures: list[tuple[str, str]] = []
    pending: list[str] = []

    progress = tqdm(total=len(rels), desc="sync docs", unit="file")
    try:
        for rel in rels:
            path = doc_path(rel)
            need_download = force_download or (not path.exists())
            if not need_download:
                text = path.read_text(encoding="utf-8", errors="ignore")
                need_download = is_bad_doc(rel, text)
            if need_download:
                pending.append(rel)
            else:
                progress.update(1)
                progress.set_postfix(downloaded=downloaded, failures=len(failures), refresh=False)

        if worker_count == 1 or len(pending) <= 1:
            for rel in pending:
                ok, err = download_rel(rel, timeout=timeout)
                if ok:
                    downloaded += 1
                else:
                    failures.append((rel, err or "unknown"))
                progress.update(1)
                progress.set_postfix(downloaded=downloaded, failures=len(failures), refresh=False)
            return downloaded, failures

        with ThreadPoolExecutor(max_workers=min(worker_count, len(pending))) as executor:
            future_to_rel = {executor.submit(download_rel, rel, timeout=timeout): rel for rel in pending}
            for future in as_completed(future_to_rel):
                rel = future_to_rel[future]
                try:
                    ok, err = future.result()
                except Exception as exc:  # noqa: BLE001
                    ok, err = False, f"worker:{exc}"
                if ok:
                    downloaded += 1
                else:
                    failures.append((rel, err or "unknown"))
                progress.update(1)
                progress.set_postfix(downloaded=downloaded, failures=len(failures), refresh=False)
    finally:
        progress.close()

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
        if is_bad_doc(rel, text):
            bad.append(rel)
        progress.set_postfix(missing=len(missing), bad=len(bad), refresh=False)
    return missing, bad
