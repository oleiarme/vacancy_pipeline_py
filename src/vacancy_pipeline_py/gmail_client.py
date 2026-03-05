from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class GmailClient:
    access_token: str
    timeout_sec: float = 30.0

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        with httpx.Client(timeout=self.timeout_sec) as client:
            resp = client.get(url, headers=headers, params=params or {})
        if resp.status_code >= 400:
            raise RuntimeError(f"Gmail API {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def list_labels(self) -> list[dict[str, Any]]:
        data = self._get("labels")
        labels = data.get("labels") or []
        return labels if isinstance(labels, list) else []

    def find_label_id(self, label_name: str) -> str | None:
        target = str(label_name or "").strip().lower()
        for label in self.list_labels():
            name = str(label.get("name") or "").strip().lower()
            if name == target:
                return str(label.get("id") or "").strip() or None
        return None

    def list_messages(self, label_id: str, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        params = {
            "labelIds": label_id,
            "q": query or "",
            "maxResults": max(1, int(max_results)),
        }
        data = self._get("messages", params=params)
        messages = data.get("messages") or []
        return messages if isinstance(messages, list) else []

    def get_message_full(self, message_id: str) -> dict[str, Any]:
        return self._get(f"messages/{message_id}", params={"format": "full"})