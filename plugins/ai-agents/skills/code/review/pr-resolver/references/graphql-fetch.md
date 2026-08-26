# Fetching PR Review Threads (GraphQL)

Always use GraphQL — REST tooling paginates incorrectly and silently misses threads beyond the first page.

```bash
GH_PAGER=cat gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $after) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved path line
          comments(first: 10) {
            nodes { body author { login } url databaseId }
          }
        }
      }
    }
  }
}' -f owner=OWNER -f repo=REPO -F pr=PR_NUMBER
```

Paginate with `-f after=<endCursor>` until `hasNextPage` is false. Filter `isResolved: false`.

## Post a threaded reply

```bash
GH_PAGER=cat gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_DATABASE_ID/replies \
  -f body="Fixed in abc1234. <one-sentence summary>."
```

Reply templates:

- Fixed: "Fixed in `<commit>`. `<one-sentence summary>`."
- By design: "By design. `<one-sentence rationale>`."
- Blocked: "Blocked by `<reason>`."

## Resolve a thread

```bash
GH_PAGER=cat gh api graphql \
  --raw-field query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' \
  --raw-field t="THREAD_NODE_ID"
```

Resolve a fix thread only after the fix is on the remote branch. Verify by comparing local and upstream SHAs before resolving.

## New review vs thread reply

| Goal | Use |
|---|---|
| Post a **new** review (summary + approve/request-changes) | `code/review/reviewer/references/pr-comments.md` |
| Reply on an **existing** review thread | This file — `pulls/comments/{databaseId}/replies` below |
