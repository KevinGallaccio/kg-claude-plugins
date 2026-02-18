---
name: pr-merge-announcer
description: >
  Generate a formatted Slack announcement message after merging a GitHub PR.
  Use this skill whenever the user says things like "announce PR", "post merge message",
  "PR merged", "slack message for PR", "merged PR #X", or any variation of wanting to
  share a merged PR with their team. Also trigger when the user mentions they just merged
  something and want to let the team know. The skill uses `gh` CLI to fetch PR details
  and generates a ready-to-paste Slack message with emoji formatting.
---

# PR Merge Announcer

Post a formatted Slack message announcing a merged GitHub PR to a set channel.

## When to use

Trigger this skill when the user wants to announce a merged PR to their team. Common phrases:
- "announce PR #84"
- "post merge message for PR 84"
- "I just merged PR #84, write the slack message"
- "slack announcement for the PR I just merged"
- "let the team know about PR #84"


## Setup (one-time)

The skill posts to Slack via an incoming webhook.
`SLACK_WEBHOOK_URL` environment variable has been set in .zshrc — no need to ask the user.

## Workflow

### Step 1: Identify the PR

The user provides a PR number. If they don't:
1. get from conversation context. If there is no context, move on to step 2.

2. check for the most recently merged PR:

```bash
gh pr list --state merged --limit 1 --json number,title
```

### Step 2: Fetch PR details

```bash
gh pr view <NUMBER> --json number,title,url,headRefName,baseRefName,body
```

### Step 3: Generate the summary

The PR body (description) often contains detailed information. Distill it into a concise 1-3 sentence summary that captures:
- **What** was added/changed/fixed
- **Why** it matters (the business or technical value)
- **How** it works at a high level (if notable)

Write it as a cohesive paragraph, not a list. Keep it informative but brief — think "elevator pitch" for the PR.

If the PR body is empty or uninformative, use the PR title and commit messages as context. Ask the user if they want to provide additional detail.

### Step 4: Format and post

The message format uses Slack mrkdwn (note: Slack uses `*bold*` not `**bold**`, and `<url|text>` for links):

```
📂 *Repo*: <REPOSITORY>
✅ *PR #<NUMBER> Merged* — <URL|TITLE>
🔀 *Branch*: `<SOURCE_BRANCH>` → `<TARGET_BRANCH>`
📝 *Summary*:
>SUMMARY
```

Use the helper script to post directly:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/post_to_slack.py <PR_NUMBER> --summary "Your generated summary here"
```

The script fetches the PR details, formats the message, and posts it to Slack in one step.

Add `--dry-run` to preview without posting. Add `--repo owner/repo` if not in the repo directory.

### Step 5: Confirm to user

After posting, show the user the message that was sent and confirm success. If the post fails, show the formatted message so they can copy-paste it manually.

**Important**: Always do a `--dry-run` first and show the user the preview. Only post after they confirm it looks good.

## Example

**Input**: "announce PR #84"

**Dry-run preview**:
```
📂 *Repo*: ai-brain-app
✅ *PR #84 Merged* — <https://github.com/tp02ga/ai-brain-app/pull/84|feat: ContentBee feedback learning loop>
🔀 *Branch*: `feature/content-bee-learning` → `main`
📝 *Summary*:
>Adds a feedback learning system to ContentBee that closes the loop between human feedback and AI content generation. The system captures three types of signals — content edits, rejections, and regeneration feedback — analyzes them via AI to extract actionable insights, and injects those learnings into future generations so output improves over time per organization.
```

After user confirms → post via `post_to_slack.py` (without `--dry-run`).

## Edge Cases

- **PR not yet merged**: Still generate the message but note it to the user. They might be pre-drafting.
- **Empty PR body**: Use the title and commit messages as context. Ask the user if they want to provide additional detail.
- **Multiple repos**: If the user works across repos, they may need to specify `--repo owner/repo` or be in the right directory.
- **Long PR descriptions**: The summary should still be 1-3 sentences. Distill, don't truncate.
