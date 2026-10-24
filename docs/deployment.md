# Deployment guide

This is a small, single-owner gateway. It uses Node.js 24, SQLite, an OIDC provider and an HTTPS reverse proxy. Example names are reserved domains; replace them in your private configuration.

## 1. Prepare the private services

Keep Harness listening on `127.0.0.1:3080`. Add `--trusted-host agent.example.com` to its web command. The public URL does not replace Harness authentication.

Create separate Unix users `harness-gateway`, `pocket-id`, and `caddy`, and a group `harness-access`. Add the Harness user and gateway user to that group. Application source and binaries should be owned by root; only state directories should be writable by their service user.

Install [Pocket ID](https://pocket-id.org/docs/setup/installation) and [Caddy](https://caddyserver.com/docs/install) from their official releases and check the release SHA-256 digests before executing them. Copy the supplied systemd units from `deploy/`; adapt binary locations if needed.

Install this project's tracked files to `/opt/harness-passkey-gateway`, then install its pinned dependencies:

```sh
cd /opt/harness-passkey-gateway
npm ci --omit=dev --ignore-scripts
```

Use a private directory outside the checkout for configuration and certificates. Root-only environment files are loaded by systemd before it drops privileges. Do not make the OIDC client secret readable by the Harness user.

## 2. Provision identity before opening ingress

Copy `deploy/pocket-id.env.example` to `/etc/pocket-id/pocket-id.env`, mode `0600`, and generate a fresh encryption key. Set the actual HTTPS identity origin; this is the relying-party domain to which Passkeys are bound.

Start Pocket ID over loopback. Before exposing it publicly:

1. Create the owner through its local administrator API, using a temporary, random `STATIC_API_KEY`.
2. Leave public signups disabled and confirm `/api/signup/setup` is unavailable.
3. Create a confidential OIDC client with callback `https://agent.example.com/_gateway/callback`, PKCE enabled, and fresh authentication required.
4. Record the client ID, one-time returned client secret, and owner UUID in the gateway's private environment file.
5. Generate a short-lived, single-use owner login code for first Passkey enrollment. Remove the static administrator API key after provisioning.

Use `deploy/Caddyfile.example` to block initial setup routes as an additional ingress restriction. Do not expose an empty identity database. Identity account recovery is privileged: recovery codes grant access and must remain private.

## 3. Share only the Harness launch credential

`deploy/export-harness-launch.py` is an adapter for the current Harness startup journal format, not a general log scraper. Install it as `/usr/local/bin/export-harness-launch`, owned by root and executable. It reads the current service PID, waits for the loopback launch URL, and writes it atomically without printing it.

Example tmpfiles rule (replace `harness-user` with the existing service user):

```text
d /run/harness-gateway 0710 harness-user harness-access -
```

The Harness service needs the shared supplementary group and journal read access. Add an `ExecStartPost=/usr/local/bin/export-harness-launch` drop-in. Set `HARNESS_SERVICE` and `HARNESS_LAUNCH_FILE` if using non-default paths. The current adapter expects port 3080 and a query-based token URL. Revisit the adapter on Harness upgrades.

The resulting launch file must be `0640`, owned by the Harness user and `harness-access`. The gateway must be able to read it, but must not receive access to the whole agent state directory. Keep the existing private SSH launch flow if it is useful.

## 4. Configure the gateway

Copy `.env.example` to `/etc/harness-gateway/gateway.env`, mode `0600`. Set:

| Setting | Meaning |
| --- | --- |
| `PUBLIC_URL` | Exact HTTPS agent origin, without a path |
| `OIDC_ISSUER` | Exact provider HTTPS issuer |
| `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` | Confidential client credentials |
| `ALLOWED_SUBJECTS` | Explicit comma-separated OIDC subject UUIDs |
| `HARNESS_LAUNCH_URL_FILE` | Restricted, current private launch URL |
| `SESSION_MAX_DAYS` | Absolute lifetime, never more than 90 days |
| `SESSION_IDLE_DAYS` | Inactivity deadline, default 7 days |
| `MAX_UPLOAD_MIB` | Streaming request size cap, default 128 MiB |

Start `harness-gateway.service`. Its health route reports that the process is running; it does **not** prove OIDC or Harness readiness.

## 5. Add HTTPS and optional FRP

Provision a valid certificate for both HTTPS origins and configure automatic renewal before relying on persistent access. Keep the TLS private key readable only by root and the TLS proxy user. With the Caddy admin API disabled, renewals must restart the Caddy service; this briefly disconnects active streams. Back up the identity encryption key and database as well as the gateway database.

The supplied Caddy configuration uses a non-privileged local TLS port 8443. Bind it to a private interface when FRP runs on a different host. Keep backend ports 1411, 4180, and 3080 on loopback. Keep the Caddy admin API disabled, including on loopback: a local agent process must not be able to rewrite ingress configuration.

If using FRP, forward public TCP 443 to the private TLS listener. Run a separate frpc service so that gateway changes do not interrupt an existing SSH tunnel. Pin the client version to one supported by the relay. The example supports FRP 0.67; it does not require upgrading the relay.

DNS-only CNAMEs can point both origins to a DDNS-managed relay hostname. This keeps traffic on the FRP path. FRP without PROXY protocol hides the original client IP; strip untrusted forwarded headers and do not claim per-device IP auditing. The gateway uses a modest global login rate cap and Pocket ID's own controls.

## 6. Enroll devices

Open the private one-time enrollment link in the browser in which you want to register a Passkey. Complete local device verification yourself. Register a second credential or recovery method before depending on one phone. Device compatibility must be checked on the actual browser; do not infer it from the operating-system version alone.

After enrollment, open the agent origin and sign in. A gateway session lasts at most 90 days from creation, even while active. Seven days without authenticated traffic expires it earlier. A connected WebSocket sending client traffic counts as activity. Browser storage deletion also ends access on that browser.

## Operations

Run the session tool as root from the installed directory:

```sh
node --env-file=/etc/harness-gateway/gateway.env src/admin.mjs list
node --env-file=/etc/harness-gateway/gateway.env src/admin.mjs revoke <session-id>
node --env-file=/etc/harness-gateway/gateway.env src/admin.mjs revoke-all
```

The list contains session hashes, timestamps, a subject and a user-agent label; it does not print bearer cookies. Active streams and WebSockets are closed within 15 seconds after revocation or expiry. Deleting a Passkey alone does not revoke gateway sessions; revoke affected sessions too.

Disable public ingress first for rollback. The original loopback Harness server and SSH access can continue independently. Restore a matched database/configuration backup for identity recovery; changing the identity origin requires credential re-enrollment.

## Reference versions

The initial deployment used Node.js 24.22.1, openid-client 6.8.8, Pocket ID 2.19.1, Caddy 2.11.7, and DeepSeek Harness 0.2.1-rc.2. Harness is a prerelease; its launch adapter may change. FRP 0.67.0 was retained for compatibility with its existing relay. Check upstream support and advisories before adopting these versions.

## Validation boundary

Syntax validation is not an authentication security audit. Verify the full login, callback, HTTP, streaming, WebSocket, expiry, revocation, browser behavior and restore process for your deployment before granting other users access. This project does not provide a multi-user isolation boundary inside a shared Harness instance.

## Reusing the identity provider for Proxmox VE

Proxmox VE can use Pocket ID through its native OIDC realm. Create a separate confidential client, enable PKCE, and register the exact public origin as its callback (PVE sends the origin without a trailing slash). Bind a pre-created PVE user to the stable subject, disable automatic user creation, and assign explicit permissions. This does not use the Harness token bridge or inherit its 90-day session lifetime.

A separate HTTPS virtual host can share the same TCP ingress port. Use a hostname that is not already mapped to loopback for a local SSH tunnel. Include it in automated certificate renewal. Verify the upstream PVE certificate with the correct TLS server name; do not disable certificate checks. Preserve authenticated WebSocket upgrades and use same-origin framing policy for embedded consoles.

Keep a private recovery path: an identity provider running inside a managed VM cannot authenticate users while that VM is stopped. Existing PAM/SSH recovery should remain available through the private path.
