FROM caddy:2.11.7-builder AS builder
RUN GOMAXPROCS=2 GOMEMLIMIT=512MiB xcaddy build v2.11.7 --with github.com/caddy-dns/cloudflare@v0.2.4

FROM caddy:2.11.7
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
