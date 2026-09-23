# Failure policy

Failure is an expected and useful result. Hiding it is the only real
failure.

## When a model, strategy or hypothesis fails

- **Do not hide the result.**
- **Do not delete the experiment.**
- **Do not modify historical data** to change the outcome.
- **Do not re-run the test with variations until it passes.**
- **Record it as FAILED**, with:
  - which criterion failed;
  - the numbers;
  - what was learned;
  - whether a *materially different* follow-up hypothesis is justified.
    If so, it is registered as a new experiment and counted.

## When the final holdout fails

The candidate is **rejected**. The holdout is spent. The model is not
adjusted and re-tested on the same holdout. A new candidate needs new
unseen data.

## When the system fails in operation

| Failure | Response |
|---|---|
| Data failure | NO_TRADE for the affected instruments; flagged on the dashboard |
| Model artifact problem | NO_TRADE; no fallback model |
| Risk state unreadable | no new orders |
| Broker or API failure | no new orders; reads retried with backoff; writes never retried |
| Ambiguous order outcome | query the broker and reconcile; never resend |
| Account type unverifiable | kill switch trips; the message names the fields checked |
| Unexpected exception in the decision path | NO_TRADE for that decision; recorded |

Every operational failure is visible: on the dashboard, in the journal,
and in a message that says what was checked and what was found.

## Incidents

A safety incident (a duplicate order, a limit breached, a secret exposed)
stops promotion through the lifecycle until its cause is found, fixed,
covered by a test, and recorded.
