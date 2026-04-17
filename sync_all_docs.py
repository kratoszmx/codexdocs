#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

from sync_common import DEFAULT_MAX_WORKERS, all_doc_urls, check_rels, prune_stale_docs, rebuild_url_records, rels_from_urls, sync_rels, write_url_list


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check/repair the local Codex CLI docs mirror. "
            "This sync pulls from official Codex developer docs plus the openai/codex repo markdown docs. "
            "check-only validates local completeness against the current discovered source indexes; "
            "update-all refreshes all currently indexed docs."
        )
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check missing/bad docs against the current discovered indexes; does not verify upstream freshness",
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
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Print lightweight phase timings and throughput metrics",
    )
    args = parser.parse_args()

    started = time.perf_counter()
    urls = all_doc_urls(timeout=args.timeout)
    after_index_fetch = time.perf_counter()
    rels = rels_from_urls(urls)
    write_url_list("all.txt", urls)
    rebuild_url_records(rels)
    prune_stale_docs(rels)
    after_metadata = time.perf_counter()

    print(f"expected_docs={len(rels)}")

    if args.check_only:
        missing, bad = check_rels(rels)
        after_check = time.perf_counter()
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
        if args.benchmark:
            print(f"benchmark_workers={args.workers}")
            print(f"benchmark_index_fetch_seconds={after_index_fetch - started:.3f}")
            print(f"benchmark_metadata_seconds={after_metadata - after_index_fetch:.3f}")
            print("benchmark_download_seconds=0.000")
            print(f"benchmark_postcheck_seconds={after_check - after_metadata:.3f}")
            print(f"benchmark_total_seconds={after_check - started:.3f}")
            print("benchmark_docs_per_second=0.000")
        return

    downloaded, failures = sync_rels(rels, timeout=args.timeout, force_download=args.update_all, max_workers=args.workers)
    after_download = time.perf_counter()
    _, bad = check_rels(rels)
    after_postcheck = time.perf_counter()
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
            print(f"{rel}\t{msg}")

    if args.benchmark:
        download_seconds = after_download - after_metadata
        docs_per_second = downloaded / download_seconds if download_seconds > 0 else 0.0
        print(f"benchmark_workers={args.workers}")
        print(f"benchmark_index_fetch_seconds={after_index_fetch - started:.3f}")
        print(f"benchmark_metadata_seconds={after_metadata - after_index_fetch:.3f}")
        print(f"benchmark_download_seconds={download_seconds:.3f}")
        print(f"benchmark_postcheck_seconds={after_postcheck - after_download:.3f}")
        print(f"benchmark_total_seconds={after_postcheck - started:.3f}")
        print(f"benchmark_docs_per_second={docs_per_second:.3f}")


if __name__ == "__main__":
    main()
