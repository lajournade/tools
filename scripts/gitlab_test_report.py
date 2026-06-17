#!/usr/bin/env python3
"""
Retrieve GitLab pipeline test results for the last N days and write a CSV summary.

Usage:
    python gitlab_test_report.py [OPTIONS]

Options are passed as CLI arguments or environment variables (see --help).
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests


# ---------------------------------------------------------------------------
# GitLab API helpers
# ---------------------------------------------------------------------------

class GitLabClient:
    def __init__(self, base_url: str, token: str, per_page: int = 100):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "PRIVATE-TOKEN": token,
            "Accept": "application/json",
        })
        self.per_page = per_page

    def _get(self, path: str, params: Optional[dict] = None, retries: int = 3) -> requests.Response:
        url = f"{self.base_url}/api/v4{path}"
        params = params or {}
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 10))
                    print(f"  [rate-limit] waiting {retry_after}s …", file=sys.stderr)
                    time.sleep(retry_after)
                    continue
                return resp
            except requests.RequestException as exc:
                if attempt == retries:
                    raise
                wait = 2 ** attempt
                print(f"  [network] attempt {attempt} failed ({exc}), retrying in {wait}s …", file=sys.stderr)
                time.sleep(wait)
        raise RuntimeError(f"Failed after {retries} attempts: GET {url}")

    def paginate(self, path: str, params: Optional[dict] = None):
        """Yield every item across all pages for a list endpoint."""
        params = dict(params or {})
        params["per_page"] = self.per_page
        page = 1
        while True:
            params["page"] = page
            resp = self._get(path, params)
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break
            yield from items
            # GitLab signals last page when X-Next-Page header is empty
            if not resp.headers.get("X-Next-Page"):
                break
            page += 1

    def get_json(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        resp = self._get(path, params)
        if resp.status_code in (404, 204):
            return None
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect_test_stats(client: GitLabClient, project_id: str, since: datetime,
                       ref: Optional[str], status_filter: Optional[str]) -> dict:
    """
    Return a dict keyed by (suite_name, test_name) with values
    {"success": int, "failed": int, "skipped": int, "error": int}.
    """
    stats: dict = defaultdict(lambda: defaultdict(int))

    since_str = since.isoformat()
    pipeline_params: dict = {"updated_after": since_str, "order_by": "updated_at", "sort": "desc"}
    if ref:
        pipeline_params["ref"] = ref
    if status_filter:
        pipeline_params["status"] = status_filter

    project_path = requests.utils.quote(project_id, safe="")
    pipelines_path = f"/projects/{project_path}/pipelines"

    total_pipelines = 0
    total_with_tests = 0

    print(f"Fetching pipelines since {since_str} …", file=sys.stderr)

    for pipeline in client.paginate(pipelines_path, pipeline_params):
        pid = pipeline["id"]
        created = pipeline.get("created_at", "")
        total_pipelines += 1

        # Try the pipeline-level test report summary first (lightweight)
        summary_path = f"/projects/{project_path}/pipelines/{pid}/test_report_summary"
        summary = client.get_json(summary_path)

        if not summary or summary.get("total", {}).get("count", 0) == 0:
            continue  # no test data for this pipeline

        # Fetch the full test report (contains individual test cases)
        report_path = f"/projects/{project_path}/pipelines/{pid}/test_report"
        report = client.get_json(report_path)
        if not report:
            continue

        total_with_tests += 1
        for suite in report.get("test_suites", []):
            suite_name = suite.get("name", "unknown_suite")
            for case in suite.get("test_cases", []):
                case_name = case.get("name", "unknown_test")
                key = (suite_name, case_name)
                result = case.get("status", "unknown").lower()
                # GitLab statuses: success, failed, error, skipped
                stats[key][result] += 1

        if total_pipelines % 20 == 0:
            print(f"  … processed {total_pipelines} pipelines, "
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
        rows.append({
            "suite": suite,
            "test_name": name,
            "success": counts.get("success", 0),
            "failed": counts.get("failed", 0),
            "error": counts.get("error", 0),
            "skipped": counts.get("skipped", 0),
            "total_runs": sum(counts.values()),
            "success_rate_%": (
                round(counts.get("success", 0) / sum(counts.values()) * 100, 2)
                if sum(counts.values()) > 0 else 0.0
            ),
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
        description="Export GitLab pipeline test results to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables (used as fallback for sensitive values):
  GITLAB_URL    GitLab instance URL  (e.g. https://gitlab.com)
  GITLAB_TOKEN  Personal / project access token

Examples:
  # Last 30 days, all branches
  python gitlab_test_report.py \\
      --url https://gitlab.com \\
      --token glpat-xxxx \\
      --project mygroup/myproject \\
      --days 30

  # Last 7 days, main branch only, only finished pipelines
  python gitlab_test_report.py \\
      --project 12345 \\
      --days 7 \\
      --ref main \\
      --status success \\
      --output weekly_tests.csv
""",
    )
    parser.add_argument("--url", default=os.getenv("GITLAB_URL", "https://gitlab.com"),
                        help="GitLab base URL (default: https://gitlab.com or $GITLAB_URL)")
    parser.add_argument("--token", default=os.getenv("GITLAB_TOKEN"),
                        help="GitLab access token ($GITLAB_TOKEN)")
    parser.add_argument("--project", required=True,
                        help="Project ID (numeric) or URL-encoded path (e.g. mygroup%2Fmyproject)")
    parser.add_argument("--days", type=int, default=30,
                        help="How many days back to look (default: 30)")
    parser.add_argument("--ref", default=None,
                        help="Filter by branch / tag name (optional)")
    parser.add_argument("--status", default=None,
                        choices=["created", "waiting_for_resource", "preparing", "pending",
                                 "running", "success", "failed", "canceled", "skipped",
                                 "blocked", "scheduled"],
                        help="Filter pipelines by status (optional, default: all)")
    parser.add_argument("--output", default="test_report.csv",
                        help="Output CSV file path (default: test_report.csv)")
    parser.add_argument("--per-page", type=int, default=100,
                        help="Items per API page (default: 100, max: 100)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.token:
        print("ERROR: GitLab token is required. Pass --token or set $GITLAB_TOKEN.", file=sys.stderr)
        sys.exit(1)

    since = datetime.now(timezone.utc) - timedelta(days=args.days)

    client = GitLabClient(args.url, args.token, per_page=args.per_page)

    # Verify connectivity / token
    me = client.get_json("/user")
    if me is None:
        print("ERROR: Could not authenticate with GitLab. Check your token and URL.", file=sys.stderr)
        sys.exit(1)
    print(f"Authenticated as: {me.get('username', '?')} on {args.url}", file=sys.stderr)

    stats = collect_test_stats(
        client,
        project_id=args.project,
        since=since,
        ref=args.ref,
        status_filter=args.status,
    )

    if not stats:
        print("No test data found for the given period / filters.", file=sys.stderr)
        sys.exit(0)

    write_csv(stats, args.output)


if __name__ == "__main__":
    main()
