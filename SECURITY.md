# Security policy

## Current status

This gateway is under development. Do not treat an initial commit, a successful build, or a running process as evidence of a complete security assessment.

## Trust boundaries

1. The identity provider owns passkey registration, local user verification, recovery, and OIDC token issuance.
2. The gateway validates the authorization response using a maintained OIDC implementation, enforces an explicit identity allowlist, and owns browser sessions.
3. Harness remains bound to loopback and retains its native authentication. Its launch token and session cookie stay server-side.
4. The TLS reverse proxy is the public ingress. A tunnel alone is not authentication.

Use separate operating-system accounts and restrict the gateway's access to the one upstream credential it needs. An authenticated user can operate the agent; this is a privileged application, not a public demo.

## Publish only sanitized material

Never commit live hostnames, public or private deployment addresses, account identifiers, access tokens, API keys, private keys, client secrets, session databases, HAR files, or authentication URLs. Use `example.com` and clearly fake placeholders. Public examples must fail closed until real credentials and the allowlist are configured.

Review the exact staged diff before each push. Ignored files alone are not a secret scanner. If a credential is committed, revoke it immediately; deleting a later revision is insufficient.

## Session requirements

Sessions must have independent absolute and inactivity deadlines. Refreshing activity must never extend the absolute lifetime. Revocation must also close associated long-lived streams. Cookies must be Secure, HttpOnly, host-only, and SameSite protected. State, nonce, and PKCE must be bound to the initiating browser.

## Reporting

Report vulnerabilities privately through the repository's GitHub security reporting feature when available. Do not include credentials in public issues.
