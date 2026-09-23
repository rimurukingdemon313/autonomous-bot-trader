# broker/

**Status: empty. Phase 9.**

## Purpose
The adapter to the broker, and the only holder of broker credentials.

## Responsibilities (when built)
- Authenticate using credentials from environment variables or a secret
  store, never from files in the repository.
- Verify the account type from the broker's own evidence. Missing or
  contradictory evidence fails the check.
- Provide reads (with bounded retry) and writes (never retried) to the
  execution layer only.

## Boundaries
- Credentials and tokens never leave this layer. They are never logged,
  and never passed to models, prompts or the dashboard.
- It never changes endpoint on a retry, an error or a default.
- The AI has no path to this layer.

## Binding contracts
[SECURITY_CONTRACT.md](../SECURITY_CONTRACT.md) · [EXECUTION_CONTRACT.md](../EXECUTION_CONTRACT.md) ·
[RISK_CONTRACT.md](../RISK_CONTRACT.md) §5
