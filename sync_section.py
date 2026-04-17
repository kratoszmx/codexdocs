#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sync_common import DEFAULT_MAX_WORKERS, all_doc_urls, filter_rels_by_prefix, rels_from_urls, sync_rels, write_url_records


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sync one Codex docs subtree. Prefix examples: developers/codex/cli, developers/codex/security, github/docs"
        )
    )
    parser.add_argument("section", help="Prefix to sync, e.g. developers/codex/cli or github/docs")
    parser.add_argument("--timeout", type=int, default=45, help="HTTP timeout seconds (default: 45)")
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Concurrent download workers (default: {DEFAULT_MAX_WORKERS})",
    )
    args = parser.parse_args()

    rels = filter_rels_by_prefix(rels_from_urls(all_doc_urls(timeout=args.timeout)), args.section)
    write_url_records(rels)

    downloaded, failures = sync_rels(rels, timeout=args.timeout, force_download=True, max_workers=args.workers)
    print(f"{args.section}: {len(rels)}")
    print(f"downloaded: {downloaded}")
    if failures:
        print("FAILURES:")
        for rel, msg in failures:
            print(f"{rel}\t{msg}")


if __name__ == "__main__":
    main()
