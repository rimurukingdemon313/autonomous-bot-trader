# dashboard/

**Status: empty. Later phase.**

## Purpose
Presentation only: show the system's state honestly.

## Planned content
AI status · current model and version · market regime · current
opportunity · decision · confidence · expected edge · risk · open trades ·
P/L · drawdown · NO_TRADE reason · research status · latest and failed
experiments · system health · broker status.

## Boundaries
- It can make the system **safer** (pause, kill switch) and ask it to look
  again. It can never open, size or close a trade, and it cannot bypass
  risk or execution checks.
- Controls that stop activity work without authentication. Controls that
  resume or initiate require it, enforced on the public-facing layer.
- It never displays a secret.
- A value that cannot be read is shown as unknown, never as zero.
- Usable on a phone.

## Binding contracts
[SECURITY_CONTRACT.md](../SECURITY_CONTRACT.md) §5 · [RISK_CONTRACT.md](../RISK_CONTRACT.md) §6
