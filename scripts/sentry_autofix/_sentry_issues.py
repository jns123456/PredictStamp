"""Shared Sentry issue helpers for autofix scripts."""

from __future__ import annotations

import requests

AUTOFIX_MARKERS = ("[autofix:deployed]", "[autofix:skipped]", "[autofix:failed]")


def _comment_text(row: dict) -> str:
    return row.get("text") or row.get("data", {}).get("text", "") or ""


def _comments_url(api: str, issue_id: str, org: str) -> str:
    if org:
        return f"{api}/organizations/{org}/issues/{issue_id}/comments/"
    return f"{api}/issues/{issue_id}/comments/"


def issue_activity_text(
    api: str,
    headers: dict[str, str],
    issue_id: str,
    org: str = "",
    project: str = "",
) -> str:
    """Return concatenated issue comments (preferred) or legacy notes text."""
    for url in (_comments_url(api, issue_id, org), _comments_url(api, issue_id, "")):
        comments = requests.get(url, headers=headers, timeout=30)
        if comments.status_code == 200:
            return "\n".join(_comment_text(row) for row in comments.json())

    if org and project:
        notes = requests.get(
            f"{api}/projects/{org}/{project}/issues/{issue_id}/notes/",
            headers=headers,
            timeout=30,
        )
        if notes.status_code == 200:
            return "\n".join(note.get("text", "") for note in notes.json())

    return ""


def already_handled(activity: str) -> bool:
    return any(marker in activity for marker in AUTOFIX_MARKERS)


def add_issue_comment(
    api: str,
    headers: dict[str, str],
    issue_id: str,
    text: str,
    org: str = "",
    project: str = "",
) -> tuple[bool, int]:
    """Post an issue comment; fall back to legacy notes endpoint."""
    comment_urls = [_comments_url(api, issue_id, org)] if org else []
    comment_urls.append(_comments_url(api, issue_id, ""))
    for url in comment_urls:
        comment_resp = requests.post(
            url,
            headers=headers,
            json={"text": text},
            timeout=30,
        )
        if comment_resp.status_code in (200, 201):
            return True, comment_resp.status_code

    if org and project:
        note_resp = requests.post(
            f"{api}/projects/{org}/{project}/issues/{issue_id}/notes/",
            headers=headers,
            json={"text": text},
            timeout=30,
        )
        if note_resp.status_code in (200, 201):
            return True, note_resp.status_code
        return False, note_resp.status_code

    return False, comment_resp.status_code
