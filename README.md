# Bouncer

Bouncer MCP for ensuring email deliverability via the [Bouncer Email Verification API](https://docs.usebouncer.com).

## Setup

```bash
# Install dependencies
uv sync

# Copy environment file
cp env.example .env

# Edit .env with your Bouncer API key
```

## Local Development

```bash
# Run the server
./run.sh

# Or directly
uv run bouncer
```

## Authentication

This server uses a developer-provided API key. Set `API_KEY` in your `.env` file with your Bouncer API key (found at https://app.usebouncer.com).

Users don't need to provide any credentials — the API key is managed by the server.

## Tools

### Real-Time Verification
- `verify_email` — Verify a single email address in real time (syntax, domain, SMTP deliverability)
- `verify_domain` — Verify a domain for MX records, catch-all behavior, and disposable status

### Credits
- `check_credits` — Check the number of verification credits available

### Batch Sync Verification
- `verify_emails_sync` — Verify multiple emails synchronously (up to 10K, waits for results)

### Batch Async Verification
- `create_batch_verification` — Create an async batch job (1K–100K emails)
- `get_batch_status` — Poll batch job status
- `get_batch_results` — Download results from a completed batch
- `finish_batch` — Stop a running batch early and reclaim unused credits
- `delete_batch` — Delete a batch and its results

### Toxicity Checking
- `create_toxicity_check` — Create a toxicity check job for a list of emails
- `get_toxicity_status` — Poll toxicity job status
- `get_toxicity_results` — Download toxicity scores
- `delete_toxicity_check` — Delete a toxicity job and its results
