# Architecture and deployment contract

## Public components

- **TLS reverse proxy:** routes `agent.example.com` and `auth.example.com`, preserves streaming, and never publishes internal listeners directly.
- **OIDC identity provider:** Pocket ID is the reference provider. Enrollment is closed after bootstrap.
- **Gateway:** an authorization-code relying party with PKCE, an explicit user allowlist, persistent server-side sessions, and a private Harness bridge.

## Harness bridge

The bridge reads the current local launch URL through a restricted credential file, exchanges it on loopback, and forwards only its server-owned upstream cookie. It refreshes this state after Harness restarts. Browser-supplied upstream authentication cookies and identity headers are never trusted.

Every HTTP request, stream, and WebSocket handshake must cross the same session boundary. Mutating requests and WebSockets require the configured public Origin; proxy headers are accepted only from the local TLS ingress. A revoked session must lose existing streams as well as new access.

## Ingress

An frp TCP tunnel can carry TLS bytes between a public relay and the private reverse proxy. DNS-only records may point to the relay. Public certificate validation, DNS editing, relay ports, and firewall policy are deployment-specific and intentionally excluded from the repository.

## Persistent authentication

Default policy: 90-day maximum lifetime and 7-day inactivity expiration. A session's creation timestamp is immutable. Keep administrative access and independent recovery credentials outside this browser session.

## Deployment isolation

Use service accounts and protected data directories. Keep identity-provider data and gateway configuration inaccessible to the agent account. Only the minimum Harness launch credential is shared. Deployments must explicitly choose how ingress reaches the gateway; no live DNS or firewall changes are embedded in the source.
