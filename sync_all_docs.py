#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sync_common import DEFAULT_MAX_WORKERS, all_doc_urls, check_rels, rebuild_url_records, rels_from_urls, sync_rels, write_url_list


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check/repair full docs.openclaw.ai markdown mirror. "
            "check-only validates local completeness against the current llms.txt index; "
            "update-all refreshes all currently indexed docs."
        )
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check missing/bad docs against the current llms.txt index; does not verify upstream freshness",
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        help="Download all currently indexed docs even when the local file already exists",
    )
    parser.add_argument("--timeout", type=int, default=45, help="HTTP timeout seconds (default: 45)")
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Concurrent download workers for sync operations (default: {DEFAULT_MAX_WORKERS})",
    )
    args = parser.parse_args()

    urls = all_doc_urls(timeout=args.timeout)
    rels = rels_from_urls(urls)
    write_url_list("all.txt", urls)
    rebuild_url_records(rels)

    print(f"expected_docs={len(rels)}")

    if args.check_only:
        missing, bad = check_rels(rels)
        print(f"missing={len(missing)}")
        print(f"bad={len(bad)}")
        if missing:
            print("MISSING:")
            for rel in missing:
                print(rel)
        if bad:
            print("BAD:")
            for rel in bad:
                print(rel)
        return

    downloaded, failures = sync_rels(rels, timeout=args.timeout, force_download=args.update_all, max_workers=args.workers)
    _, bad = check_rels(rels)
    print(f"downloaded={downloaded}")
    print(f"postcheck_bad={len(bad)}")
    print(f"failures={len(failures)}")

    if bad:
        print("BAD:")
        for rel in bad:
            print(rel)

    if failures:
        print("FAILURES:")
        for rel, msg in failures:
            print(f"{rel}	{msg}")


if __name__ == "__main__":
    main()
