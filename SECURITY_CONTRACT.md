# Security contract

---

## 1. No secrets in Git, ever

The following never appear anywhere in this repository: source, tests,
documentation, examples, commit messages, issues or pull requests.

- API keys;
- passwords;
- broker credentials (username, password, account IDs paired with
  credentials, access or refresh tokens);
- Telegram or other bot tokens;
- database passwords or connection strings containing credentials;
- private keys and certificates.

Example configuration files list variable **names** with empty or
obviously fake placeholder values, never real ones.

## 2. Where secrets live

- In **environment variables** provided by the hosting platform's secret
  management, or a dedicated secret store.
- Never in files committed to the repository. `.env` and similar files are
  ignored by `.gitignore`.
- Secrets are never requested in, or pasted into, chat, issues, pull
  requests or public source code.

## 3. Least privilege

- **Only the broker layer reads broker credentials.** Access tokens never
  leave it. No model, prompt, agent, dashboard or log receives them.
- The AI has no access to credentials of any kind, and no network path to
  the broker.
- Each deployment uses the narrowest credentials that work, and a demo
  account until LIVE is explicitly approved.

## 4. Logs and errors

- Secrets are never logged. Log and error output is redacted for known
  secret fields and for token-shaped values.
- Error messages name the **variable** that is missing or wrong, never its
  value.

## 5. The dashboard

- It displays state and never shows a secret, or a partial secret.
- Controls that resume, widen or initiate trading require authentication,
  enforced on the **public-facing layer**, not only on internal services.
  Hostnames are not secrets.
- Controls that only stop or pause remain available without
  authentication ([RISK_CONTRACT.md](RISK_CONTRACT.md) §6).
- Closed CORS is not a substitute for authentication.

## 6. If a secret is committed

1. **Rotate it immediately.** Treat it as public from the moment it was
   pushed.
2. Then remove it from history. Rewriting history does not un-leak a
   secret, so rotation always comes first.
3. Record the incident, without the secret.

## 7. Checks

Before a commit is pushed, it is scanned for secrets (Phase 1 adds an
automated check). The pull request template requires confirming that no
secret is included.
