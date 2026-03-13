"""Pydantic models for Bouncer API responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DomainInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Domain name")
    acceptAll: str = Field(description="Whether domain accepts all emails: yes, no, or unknown")
    disposable: str = Field(description="Whether domain is disposable: yes, no, or unknown")
    free: str = Field(description="Whether domain is a free email provider: yes, no, or unknown")


class AccountInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str = Field(
        description="Whether email is a role account (e.g. info@, admin@): yes, no, or unknown"
    )
    disabled: str = Field(description="Whether account is disabled: yes, no, or unknown")
    fullMailbox: str = Field(description="Whether mailbox is full: yes, no, or unknown")


class DnsInfo(BaseModel):
    type: str = Field(description="DNS record type (e.g. MX)")
    record: str | None = Field(default=None, description="DNS record value")


class EmailVerificationResult(BaseModel):
    """Result of verifying a single email address."""

    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(description="The verified email address")
    status: str = Field(
        description="Verification status: deliverable, risky, undeliverable, or unknown"
    )
    reason: str = Field(
        description="Reason for the status: accepted_email, low_deliverability, low_quality, invalid_email, invalid_domain, rejected_email, dns_error, unavailable_smtp, unsupported, timeout, or unknown"
    )
    domain: DomainInfo | None = Field(default=None, description="Domain information")
    account: AccountInfo | None = Field(default=None, description="Account information")
    dns: DnsInfo | None = Field(default=None, description="DNS record information")
    provider: str | None = Field(default=None, description="Email provider (e.g. google.com)")
    score: int | None = Field(default=None, description="Deliverability score from 0 to 100")
    toxic: str | None = Field(default=None, description="Toxicity indicator")
    toxicity: int | None = Field(default=None, description="Toxicity score from 0 to 5")
    didYouMean: str | None = Field(
        default=None, description="Suggested email correction if a typo was detected"
    )
    retryAfter: str | None = Field(
        default=None, description="ISO timestamp to retry after, returned for greylisted emails"
    )


class DomainVerificationResult(BaseModel):
    """Result of verifying a single domain."""

    domain: DomainInfo = Field(description="Domain information")
    dns: DnsInfo = Field(description="DNS record information")
    provider: str | None = Field(default=None, description="Email provider (e.g. google.com)")
    toxic: str | None = Field(default=None, description="Toxicity indicator")


class CreditsResult(BaseModel):
    """Available Bouncer credits."""

    credits: int = Field(description="Number of verification credits available")


class BatchCreateResult(BaseModel):
    """Result of creating a batch verification job."""

    model_config = ConfigDict(populate_by_name=True)

    batchId: str = Field(
        description="Unique batch identifier — save this to check status and download results"
    )
    created: str = Field(description="ISO timestamp when the batch was created")
    status: str = Field(description="Batch status: queued")
    quantity: int = Field(description="Number of emails submitted")
    duplicates: int = Field(description="Number of duplicate emails removed")


class BatchStats(BaseModel):
    """Processing statistics for a completed batch."""

    deliverable: int = Field(description="Count of deliverable emails")
    risky: int = Field(description="Count of risky emails")
    undeliverable: int = Field(description="Count of undeliverable emails")
    unknown: int = Field(description="Count of unknown emails")


class BatchStatusResult(BaseModel):
    """Status of a batch verification job."""

    model_config = ConfigDict(populate_by_name=True)

    batchId: str = Field(description="Unique batch identifier")
    created: str = Field(description="ISO timestamp when the batch was created")
    started: str | None = Field(default=None, description="ISO timestamp when processing started")
    completed: str | None = Field(
        default=None, description="ISO timestamp when processing completed"
    )
    status: str = Field(description="Batch status: queued, processing, or completed")
    quantity: int = Field(description="Number of emails in the batch")
    duplicates: int = Field(description="Number of duplicate emails removed")
    credits: int | None = Field(
        default=None, description="Credits consumed (populated when completed)"
    )
    processed: int | None = Field(default=None, description="Number of emails processed so far")
    stats: BatchStats | None = Field(
        default=None, description="Verification statistics (when with_stats is true)"
    )


class BatchDeleteResult(BaseModel):
    """Result of deleting a batch."""

    success: bool = Field(description="Whether the batch was successfully deleted")


class BatchFinishResult(BaseModel):
    """Result of finishing a batch early."""

    success: bool = Field(description="Whether the finish request was accepted")


class ToxicityCreateResult(BaseModel):
    """Result of creating a toxicity check job."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(
        description="Toxicity job identifier — save this to check status and download results"
    )
    createdAt: str = Field(description="ISO timestamp when the job was created")
    status: str = Field(description="Job status: processing")


class ToxicityStatusResult(BaseModel):
    """Status of a toxicity check job."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Toxicity job identifier")
    createdAt: str = Field(description="ISO timestamp when the job was created")
    status: str = Field(description="Job status: processing, completed, or error")


class ToxicityEmailResult(BaseModel):
    """Toxicity result for a single email."""

    email: str = Field(description="Email address")
    toxicity: int = Field(description="Toxicity score")


class ToxicityDeleteResult(BaseModel):
    """Result of deleting a toxicity check job."""

    success: bool = Field(description="Whether the job was successfully deleted")
