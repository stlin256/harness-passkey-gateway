# Identity and ingress on a separate host

The default listener remains loopback. To put the TLS ingress on a trusted
virtualization host while keeping Harness inside its guest, set both:

```dotenv
LISTEN_HOST=10.20.0.2
TRUSTED_PROXY_IP=10.20.0.1
```

Only RFC 1918 IPv4 addresses are accepted for this mode. The gateway closes
connections whose actual TCP peer does not match `TRUSTED_PROXY_IP`, including
WebSocket connections. Forwarding headers cannot override this check.
The Harness upstream must still be loopback.

Use a private host/guest bridge protected from untrusted workloads. This hop
is HTTP; it is not encrypted or authenticated against an attacker able to
spoof the trusted host on that bridge. Use a mutually authenticated encrypted
transport if the network itself is not trusted. Bind the host ingress only to
the required interfaces, and forward the existing public TLS port to it.

Move the identity database using a consistent SQLite backup or while its
service is stopped. Preserve its encryption key, OIDC clients, signing keys,
uploads, canonical origin, TLS certificates, and ACME account state. Keep a
restricted rollback backup. Remove obsolete guest-side identity and ACME
secrets after the cutover is confirmed; retain the gateway's own OIDC secret
and session database.
