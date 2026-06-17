#!/usr/bin/env python3
"""
Retrieve GitLab pipeline job statuses for the last N days and write a CSV summary.

Unlike gitlab_test_report.py (which relies on JUnit artifacts), this script tracks
every job by name — including jobs that fail before producing a test report.

Usage:
    python gitlab_job_stats.py [OPTIONS]  (see --help)
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

# GitLab job statuses that count as a definitive outcome
SUCCESS_STATUSES = {"success"}
FAILURE_STATUSES = {"failed"}
CANCELED_STATUSES = {"canceled"}
SKIPPED_STATUSES = {"skipped", "manual"}
# Any other status (created, pending, running, …) → "other"


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect_job_stats(client: GitLabClient, project_id: str, since,
                      ref: Optional[str], status_filter: Optional[str],
                      job_name_filter: Optional[str]) -> dict:
    """
    Return a dict keyed by job_name → {"success": int, "failed": int,
    "canceled": int, "skipped": int, "other": int}.
    """
    stats: dict = defaultdict(lambda: defaultdict(int))
    enc = project_encode(project_id)

    total_pipelines = 0
    total_jobs = 0

    print(f"Fetching pipelines since {since.isoformat()} …", file=sys.stderr)

    for pipeline in iter_pipelines(client, enc, since, ref, status_filter):
        pid = pipeline["id"]
        total_pipelines += 1

        for job in client.paginate(f"/projects/{enc}/pipelines/{pid}/jobs"):
            name = job.get("name", "unknown_job")

            if job_name_filter and job_name_filter.lower() not in name.lower():
                continue

            total_jobs += 1
            raw_status = job.get("status", "other").lower()

            if raw_status in SUCCESS_STATUSES:
                bucket = "success"
            elif raw_status in FAILURE_STATUSES:
                bucket = "failed"
            elif raw_status in CANCELED_STATUSES:
                bucket = "canceled"
            elif raw_status in SKIPPED_STATUSES:
                bucket = "skipped"
            else:
                bucket = "other"

            stats[name][bucket] += 1

        if total_pipelines % 20 == 0:
            print(f"  … {total_pipelines} pipelines processed, "
                  f"{total_jobs} jobs collected", file=sys.stderr)

    print(f"Done. {total_pipelines} pipelines scanned, "
          f"{total_jobs} job executions collected.", file=sys.stderr)
    return stats


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(stats: dict, output_path: str) -> None:
    rows = []
    for job_name, counts in stats.items():
        total = sum(counts.values())
        rows.append({
            "job_name": job_name,
            "success": counts.get("success", 0),
            "failed": counts.get("failed", 0),
            "canceled": counts.get("canceled", 0),
            "skipped": counts.get("skipped", 0),
            "other": counts.get("other", 0),
            "total_runs": total,
            "success_rate_%": round(counts.get("success", 0) / total * 100, 2) if total else 0.0,
        })

    rows.sort(key=lambda r: r["job_name"])

    fieldnames = ["job_name", "success", "failed", "canceled", "skipped", "other",
                  "total_runs", "success_rate_%"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV written to: {output_path}  ({len(rows)} distinct job names)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export GitLab job success/failure counts by job name to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (fallback for sensitive values):
  GITLAB_URL    GitLab instance URL  (e.g. https://gitlab.com)
  GITLAB_TOKEN  Personal / project access token

Examples:
  python gitlab_job_stats.py \\
      --url https://gitlab.com \\
      --token glpat-xxxx \\
      --project mygroup/myproject \\
      --days 30

  # Only jobs whose name contains "test", on the main branch
  python gitlab_job_stats.py \\
      --url https://gitlab.com \\
      --token glpat-xxxx \\
      --project mygroup/myproject \\
      --days 7 \\
      --ref main \\
      --job-name test \\
      --output job_stats.csv
""",
    )
    add_common_args(parser, default_output="job_stats.csv")
    parser.add_argument("--job-name", default=None,
                        help="Case-insensitive substring filter on job name (optional)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client_from_args(args)
    since = since_datetime(args.days)

    stats = collect_job_stats(
        client, args.project, since, args.ref, args.status,
        job_name_filter=args.job_name,
    )

    if not stats:
        print("No job data found for the given period / filters.", file=sys.stderr)
        sys.exit(0)

    write_csv(stats, args.output)


if __name__ == "__main__":
    main()
