# Production web server

Caddy replaces nginx and Certbot. It obtains certificates with the Cloudflare
DNS challenge and renews/loads them automatically. No renewal scripts or host timer
are needed. DNS validation works through the existing Cloudflare/FRP routing.

## Configure and run

Copy `caddy/cloudflare.env.example` to `caddy/cloudflare.env`, then set a
Cloudflare API token with Zone DNS Edit and Zone Read for the domain. The real
file is ignored by Git; never commit it. Existing Certbot credentials can be reused
if they have those permissions. The DNS plugin is built from the pinned Dockerfile.

Run `docker compose -f docker-compose.prod.yml config --quiet`, then
`docker compose -f docker-compose.prod.yml up -d --build --remove-orphans`.
For an existing installation, validate/build first, then stop/remove the old nginx
and Certbot containers before starting Caddy if their host ports conflict.
Do not delete the app's volumes or existing certificates during migration.

Caddy's `/data` named volume contains its ACME account and certificates; preserve it
across deployments (`docker compose down -v` would delete it). `/config` is also
persistent. View issuance/renewal messages with `docker compose -f docker-compose.prod.yml logs caddy`.
The `subweb-nginx-1` network alias preserves the existing FRP destination. Caddy
handles HTTP-to-HTTPS redirects; keep Cloudflare's origin mode at Full (strict).
The old nginx configuration is retained only for rollback.

## Deployment and rollback

The workflow builds the Caddy image on the server and updates containers without
bringing down the whole stack. Provision the ignored credentials file before
merging. Remove any earlier Certbot cron/systemd jobs once Caddy is verified.
To roll back, restore the previous Compose config and start nginx/Certbot using
the existing certificate directory; leave Caddy's volumes intact.
