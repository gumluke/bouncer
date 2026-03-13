"""HTTP client for the Bouncer API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.usebouncer.com"


class BouncerAPIError(Exception):
    """Raised when the Bouncer API returns an error response."""

    def __init__(self, status_code: int, error: str, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(f"Bouncer API error {status_code} ({error}): {message}")


class BouncerClient:
    """Async HTTP client for the Bouncer Email Verification API."""

    def __init__(self, api_key: str):
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"x-api-key": api_key},
            timeout=60.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    def _raise_for_error(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                body = response.json()
            except Exception:
                body = {}
            raise BouncerAPIError(
                status_code=response.status_code,
                error=body.get("error", response.reason_phrase or "Unknown"),
                message=body.get("message", response.text),
            )

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params)
        self._raise_for_error(response)
        return response.json()

    async def post(self, path: str, json: Any = None, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.post(path, json=json, params=params)
        self._raise_for_error(response)
        if response.status_code == 202:
            return {"success": True}
        return response.json()

    async def delete(self, path: str) -> Any:
        response = await self._client.delete(path)
        self._raise_for_error(response)
        return response.json()
