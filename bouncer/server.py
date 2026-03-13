"""Bouncer MCP Server — Email verification tools powered by the Bouncer API."""

from __future__ import annotations

import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from mcp.gumstack import GumstackHost
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from bouncer.models import (
    BatchCreateResult,
    BatchDeleteResult,
    BatchFinishResult,
    BatchStatusResult,
    CreditsResult,
    DomainVerificationResult,
    EmailVerificationResult,
    ToxicityCreateResult,
    ToxicityDeleteResult,
    ToxicityEmailResult,
    ToxicityStatusResult,
)
from bouncer.utils.auth import get_credentials
from bouncer.utils.client import BouncerClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(name=__name__)

PORT = int(os.environ.get("PORT", 8000))

mcp = FastMCP("Bouncer", host="0.0.0.0", port=PORT)


def _get_client() -> BouncerClient:
    creds = get_credentials()
    api_key = creds.get("api_key", "")
    if not api_key:
        raise ValueError("API_KEY is not configured. Set it in your .env file.")
    return BouncerClient(api_key)


@mcp.custom_route("/health_check", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Real-Time Email Verification
# ---------------------------------------------------------------------------


@mcp.tool()
async def verify_email(
    email: Annotated[str, Field(description="The email address to verify")],
    timeout: Annotated[
        int, Field(description="Verification timeout in seconds (default 10, max 30)")
    ] = 10,
) -> EmailVerificationResult:
    """Verify a single email address in real time. Checks syntax, domain, and SMTP deliverability. Returns status (deliverable, risky, undeliverable, unknown), domain info, toxicity score, and more."""
    client = _get_client()
    try:
        data = await client.get("/v1.1/email/verify", params={"email": email, "timeout": timeout})
        return EmailVerificationResult.model_validate(data)
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Domain Verification
# ---------------------------------------------------------------------------


@mcp.tool()
async def verify_domain(
    domain: Annotated[str, Field(description="The domain name to verify (e.g. 'usebouncer.com')")],
) -> DomainVerificationResult:
    """Verify a domain to check for valid MX records, catch-all behavior, disposable status, and email provider. Consumes one credit."""
    client = _get_client()
    try:
        data = await client.get("/v1.1/domain", params={"domain": domain})
        return DomainVerificationResult.model_validate(data)
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------


@mcp.tool()
async def check_credits() -> CreditsResult:
    """Check the number of email verification credits available on the Bouncer account."""
    client = _get_client()
    try:
        data = await client.get("/v1.1/credits")
        return CreditsResult.model_validate(data)
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Batch Synchronous Verification
# ---------------------------------------------------------------------------


@mcp.tool()
async def verify_emails_sync(
    emails: Annotated[
        list[str], Field(description="List of email addresses to verify (max 10,000 per request)")
    ],
) -> list[EmailVerificationResult]:
    """Verify multiple emails synchronously using Bouncer's batch sync queue. Waits for all results before returning. Best for small-to-medium lists where you want immediate results."""
    client = _get_client()
    try:
        data = await client.post("/v1.1/email/verify/batch/sync", json=emails)
        return [EmailVerificationResult.model_validate(item) for item in data]
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Batch Async Verification
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_batch_verification(
    emails: Annotated[
        list[str], Field(description="List of email addresses to verify in the batch")
    ],
    callback: Annotated[
        str | None,
        Field(
            description="Optional callback URL that Bouncer will POST to when the batch completes"
        ),
    ] = None,
) -> BatchCreateResult:
    """Create an asynchronous batch email verification job. Returns a batchId to track progress. Use get_batch_status to poll for completion, then get_batch_results to download results. Best for large lists (1K-100K emails)."""
    client = _get_client()
    try:
        body = [{"email": e} for e in emails]
        params = {"callback": callback} if callback else None
        data = await client.post("/v1.1/email/verify/batch", json=body, params=params)
        return BatchCreateResult.model_validate(data)
    finally:
        await client.close()


@mcp.tool()
async def get_batch_status(
    batch_id: Annotated[
        str, Field(description="The batchId returned from create_batch_verification")
    ],
    with_stats: Annotated[
        bool, Field(description="Include processing progress statistics in the response")
    ] = False,
) -> BatchStatusResult:
    """Check the status of an asynchronous batch verification job. Poll every 10-30 seconds until status is 'completed', then use get_batch_results to download."""
    client = _get_client()
    try:
        params: dict = {}
        if with_stats:
            params["with-stats"] = "true"
        data = await client.get(f"/v1.1/email/verify/batch/{batch_id}", params=params or None)
        return BatchStatusResult.model_validate(data)
    finally:
        await client.close()


@mcp.tool()
async def get_batch_results(
    batch_id: Annotated[
        str, Field(description="The batchId of a completed batch verification job")
    ],
    status_filter: Annotated[
        str,
        Field(
            description="Filter results by status: all, deliverable, risky, undeliverable, or unknown"
        ),
    ] = "all",
) -> list[EmailVerificationResult]:
    """Download results from a completed batch verification job. The batch must have status 'completed' before results can be downloaded."""
    client = _get_client()
    try:
        data = await client.get(
            f"/v1.1/email/verify/batch/{batch_id}/download",
            params={"download": status_filter},
        )
        return [EmailVerificationResult.model_validate(item) for item in data]
    finally:
        await client.close()


@mcp.tool()
async def finish_batch(
    batch_id: Annotated[str, Field(description="The batchId of a running batch to finish early")],
) -> BatchFinishResult:
    """Finish a running batch verification early. Stops processing and returns credits for any unverified emails. Results can be downloaded once status becomes 'completed'."""
    client = _get_client()
    try:
        await client.post(f"/v1.1/email/verify/batch/{batch_id}/finish")
        return BatchFinishResult(success=True)
    finally:
        await client.close()


@mcp.tool()
async def delete_batch(
    batch_id: Annotated[str, Field(description="The batchId of the batch to delete")],
) -> BatchDeleteResult:
    """Delete a batch verification job and all associated email data. Results will be permanently lost."""
    client = _get_client()
    try:
        await client.delete(f"/v1.1/email/verify/batch/{batch_id}")
        return BatchDeleteResult(success=True)
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Toxicity Checking
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_toxicity_check(
    emails: Annotated[
        list[str], Field(description="List of email addresses to check for toxicity")
    ],
) -> ToxicityCreateResult:
    """Create a toxicity check job for a list of email addresses. Returns a job id to track progress. Use get_toxicity_status to poll for completion, then get_toxicity_results to download scores."""
    client = _get_client()
    try:
        data = await client.post("/v1/toxicity/list", json=emails)
        return ToxicityCreateResult.model_validate(data)
    finally:
        await client.close()


@mcp.tool()
async def get_toxicity_status(
    job_id: Annotated[
        str, Field(description="The toxicity job id returned from create_toxicity_check")
    ],
) -> ToxicityStatusResult:
    """Check the status of a toxicity check job. Poll until status is 'completed', then use get_toxicity_results to download scores."""
    client = _get_client()
    try:
        data = await client.get(f"/v1/toxicity/list/{job_id}")
        return ToxicityStatusResult.model_validate(data)
    finally:
        await client.close()


@mcp.tool()
async def get_toxicity_results(
    job_id: Annotated[str, Field(description="The toxicity job id of a completed toxicity check")],
) -> list[ToxicityEmailResult]:
    """Download toxicity scores for a completed toxicity check job. Each email receives a toxicity score."""
    client = _get_client()
    try:
        data = await client.get(f"/v1/toxicity/list/{job_id}/data")
        return [ToxicityEmailResult.model_validate(item) for item in data]
    finally:
        await client.close()


@mcp.tool()
async def delete_toxicity_check(
    job_id: Annotated[str, Field(description="The toxicity job id to delete")],
) -> ToxicityDeleteResult:
    """Delete a toxicity check job and its results."""
    client = _get_client()
    try:
        await client.delete(f"/v1/toxicity/list/{job_id}")
        return ToxicityDeleteResult(success=True)
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    load_dotenv()
    if os.environ.get("ENVIRONMENT") != "local":
        host = GumstackHost(mcp)
        host.run(host="0.0.0.0", port=PORT)
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
