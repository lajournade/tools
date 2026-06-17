#!/usr/bin/env python3
"""
Retrieve GitLab pipeline test results for the last N days and write a CSV summary.

Relies on JUnit artifacts published via `artifacts: reports: junit:` in .gitlab-ci.yml.
Jobs that fail before producing a test report are ignored — use gitlab_job_stats.py
to track job-level outcomes regardless of test reports.

Usage:
    python gitlab_test_report.py [OPTIONS]  (see --help)
"""

import argparse
import csv
import sys
from collections import defaultdict
from typing import Optional

from _gitlab_common import (
    add_common_args,
    build_client_from_args,
    iter_pipelines,
    project_encode,
    since_datetime,
    GitLabClient,
)


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect_test_stats(client: GitLabClient, project_id: str, since,
                       ref: Optional[str], status_filter: Optional[str]) -> dict:
    """
    Return a dict keyed by (suite_name, test_name) → {"success": int, "failed": int, …}.
    """
    stats: dict = defaultdict(lambda: defaultdict(int))
    enc = project_encode(project_id)

    total_pipelines = 0
    total_with_tests = 0

    print(f"Fetching pipelines since {since.isoformat()} …", file=sys.stderr)

    for pipeline in iter_pipelines(client, enc, since, ref, status_filter):
        pid = pipeline["id"]
        total_pipelines += 1

        # Lightweight check before fetching the full report
        summary = client.get_json(f"/projects/{enc}/pipelines/{pid}/test_report_summary")
        if not summary or summary.get("total", {}).get("count", 0) == 0:
            continue

        report = client.get_json(f"/projects/{enc}/pipelines/{pid}/test_report")
        if not report:
            continue

        total_with_tests += 1
        for suite in report.get("test_suites", []):
            suite_name = suite.get("name", "unknown_suite")
            for case in suite.get("test_cases", []):
                key = (suite_name, case.get("name", "unknown_test"))
                stats[key][case.get("status", "unknown").lower()] += 1

        if total_pipelines % 20 == 0:
            print(f"  … {total_pipelines} pipelines processed, "
                  f"{total_with_tests} had test reports", file=sys.stderr)

    print(f"Done. {total_pipelines} pipelines scanned, "
          f"{total_with_tests} had test reports.", file=sys.stderr)
    return stats


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(stats: dict, output_path: str) -> None:
    rows = []
    for (suite, name), counts in stats.items():
        total = sum(counts.values())
        rows.append({
            "suite": suite,
            "test_name": name,
            "success": counts.get("success", 0),
            "failed": counts.get("failed", 0),
            "error": counts.get("error", 0),
            "skipped": counts.get("skipped", 0),
            "total_runs": total,
            "success_rate_%": round(counts.get("success", 0) / total * 100, 2) if total else 0.0,
        })

    rows.sort(key=lambda r: (r["suite"], r["test_name"]))

    fieldnames = ["suite", "test_name", "success", "failed", "error", "skipped",
                  "total_runs", "success_rate_%"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV written to: {output_path}  ({len(rows)} test cases)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export GitLab pipeline test results (JUnit reports) to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (fallback for sensitive values):
  GITLAB_URL    GitLab instance URL  (e.g. https://gitlab.com)
  GITLAB_TOKEN  Personal / project access token

Examples:
  python gitlab_test_report.py \\
      --url https://gitlab.com \\
      --token glpat-xxxx \\
      --project mygroup/myproject \\
      --days 30

  python gitlab_test_report.py \\
      --project 12345 --days 7 --ref main --status success --output weekly.csv
""",
    )
    add_common_args(parser, default_output="test_report.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client_from_args(args)
    since = since_datetime(args.days)

    stats = collect_test_stats(client, args.project, since, args.ref, args.status)

    if not stats:
        print("No test data found for the given period / filters.", file=sys.stderr)
        sys.exit(0)

    write_csv(stats, args.output)


if __name__ == "__main__":
    main()
