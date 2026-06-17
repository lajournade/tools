"""
Shared GitLab API client and CLI helpers used by the gitlab_* scripts.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests


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
            if not resp.headers.get("X-Next-Page"):
                break
            page += 1

    def get_json(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        resp = self._get(path, params)
        if resp.status_code in (404, 204):
            return None
        resp.raise_for_status()
        return resp.json()


PIPELINE_STATUSES = [
    "created", "waiting_for_resource", "preparing", "pending",
    "running", "success", "failed", "canceled", "skipped", "blocked", "scheduled",
]


def add_common_args(parser: argparse.ArgumentParser, default_output: str) -> None:
    """Attach the shared CLI arguments to an ArgumentParser."""
    parser.add_argument("--url", default=os.getenv("GITLAB_URL", "https://gitlab.com"),
                        help="GitLab base URL (default: https://gitlab.com or $GITLAB_URL)")
    parser.add_argument("--token", default=os.getenv("GITLAB_TOKEN"),
                        help="GitLab access token ($GITLAB_TOKEN)")
    parser.add_argument("--project", required=True,
                        help="Project ID (numeric) or path (e.g. mygroup/myproject)")
    parser.add_argument("--days", type=int, default=30,
                        help="How many days back to look (default: 30)")
    parser.add_argument("--ref", default=None,
                        help="Filter by branch or tag name (optional)")
    parser.add_argument("--status", default=None, choices=PIPELINE_STATUSES,
                        help="Filter pipelines by status (optional, default: all)")
    parser.add_argument("--output", default=default_output,
                        help=f"Output CSV file path (default: {default_output})")
    parser.add_argument("--per-page", type=int, default=100,
                        help="Items per API page (default: 100, max: 100)")


def build_client_from_args(args: argparse.Namespace) -> GitLabClient:
    """Validate token and return an authenticated client."""
    if not args.token:
        print("ERROR: GitLab token is required. Pass --token or set $GITLAB_TOKEN.", file=sys.stderr)
        sys.exit(1)
    client = GitLabClient(args.url, args.token, per_page=args.per_page)
    me = client.get_json("/user")
    if me is None:
        print("ERROR: Could not authenticate with GitLab. Check your token and URL.", file=sys.stderr)
        sys.exit(1)
    print(f"Authenticated as: {me.get('username', '?')} on {args.url}", file=sys.stderr)
    return client


def since_datetime(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def project_encode(project_id: str) -> str:
    return requests.utils.quote(project_id, safe="")


def iter_pipelines(client: GitLabClient, project_path_enc: str,
                   since: datetime, ref: Optional[str], status_filter: Optional[str]):
    """Yield all pipelines for the project updated after *since*."""
    params: dict = {
        "updated_after": since.isoformat(),
        "order_by": "updated_at",
        "sort": "desc",
    }
    if ref:
        params["ref"] = ref
    if status_filter:
        params["status"] = status_filter
    yield from client.paginate(f"/projects/{project_path_enc}/pipelines", params)
