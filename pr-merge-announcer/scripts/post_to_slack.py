#!/usr/bin/env python3
"""Post a formatted PR merge announcement to Slack via webhook.

Usage:
    python3 post_to_slack.py <PR_NUMBER> --summary "Your summary here" [--repo owner/repo] [--webhook-url URL] [--dry-run]

If --webhook-url is not provided, reads from SLACK_WEBHOOK_URL environment variable.
Use --dry-run to preview the message without posting.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error


def fetch_pr(pr_number: int, repo: str | None = None) -> dict:
    """Fetch PR details using gh CLI."""
    cmd = [
        "gh", "pr", "view", str(pr_number),
        "--json", "number,title,url,headRefName,baseRefName,body"
    ]
    if repo:
        cmd.extend(["--repo", repo])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error fetching PR #{pr_number}: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)


def format_message(pr: dict, summary: str) -> str:
    """Format the Slack announcement message."""
    # Extract repo name from the PR URL (https://github.com/owner/repo/pull/N)
    repo_name = pr["url"].split("/")[4]
    return (
        f"📂 *Repo*: {repo_name}\n"
        f"✅ *PR #{pr['number']} Merged* — <{pr['url']}|{pr['title']}>\n"
        f"🔀 *Branch*: `{pr['headRefName']}` → `{pr['baseRefName']}`\n"
        f"📝 *Summary*:\n"
        f">{summary}"
    )


def post_to_slack(webhook_url: str, message: str) -> bool:
    """Post message to Slack via incoming webhook. Returns True on success."""
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                return True
            print(f"Slack returned status {resp.status}", file=sys.stderr)
            return False
    except urllib.error.HTTPError as e:
        print(f"Slack webhook error: {e.code} {e.reason}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Post PR merge announcement to Slack")
    parser.add_argument("pr_number", type=int, help="PR number to announce")
    parser.add_argument("--summary", type=str, required=True, help="Summary of the PR changes")
    parser.add_argument("--repo", type=str, default=None, help="Repository in owner/repo format")
    parser.add_argument("--webhook-url", type=str, default=None, help="Slack webhook URL (or set SLACK_WEBHOOK_URL env var)")
    parser.add_argument("--dry-run", action="store_true", help="Preview the message without posting")
    args = parser.parse_args()

    # Fetch PR details
    pr = fetch_pr(args.pr_number, args.repo)
    message = format_message(pr, args.summary)

    if args.dry_run:
        print("=== DRY RUN — Message preview ===\n")
        print(message)
        print("\n=== End preview ===")
        return

    # Resolve webhook URL
    webhook_url = args.webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Error: No webhook URL provided. Use --webhook-url or set SLACK_WEBHOOK_URL env var.", file=sys.stderr)
        sys.exit(1)

    # Post to Slack
    if post_to_slack(webhook_url, message):
        print(f"✅ Posted PR #{pr['number']} merge announcement to Slack!")
    else:
        print("❌ Failed to post to Slack.", file=sys.stderr)
        print("\nMessage was:\n")
        print(message)
        sys.exit(1)


if __name__ == "__main__":
    main()
