# Security

Report a suspected vulnerability through GitHub's private vulnerability reporting feature if it is enabled. If it is unavailable, open a brief issue requesting a private reporting channel without disclosing the vulnerability. Do not include credentials, personal data, or operational exports in an issue or pull request.

These examples use synthetic data and are designed for manual execution in an isolated n8n instance. The tenant-scoped retrieval example uses a small in-memory fixture; its sample filter does not enforce authorization in a deployed data system. No export contains an Agent node, authored prompt, credential, or external call. Static validation is included, but it does not establish compatibility with every n8n release or prove safe behavior after modification.
