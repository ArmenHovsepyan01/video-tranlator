# Backend Deployment Guide

## Prerequisites
- Docker 24+ and Docker Compose plugin.
- DuckDNS hostname (configure `DUCKDNS_DOMAIN` in `.env`).
- Valid email for Let's Encrypt (`CERTBOT_EMAIL`).
- Ports 80 and 443 open on the host.

## 1. Prepare environment
Create `.env` beside `docker-compose.yml` (never commit this file):

```env
DUCKDNS_DOMAIN=yourdomain.duckdns.org
CERTBOT_EMAIL=you@example.com
ALLOWED_ORIGINS=https://frontend.example.com
```

Create the folders expected by the stack:

```bash
mkdir -p certbot/conf certbot/www nginx
```

Copy the provided `nginx.conf.template` into `nginx/`. It references `${DUCKDNS_DOMAIN}` so nothing sensitive is committed.

## 2. Bootstrap certificates (one-time)
With DNS already pointing to your server, run:

```bash
DUCKDNS_DOMAIN=yourdomain.duckdns.org
CERTBOT_EMAIL=you@example.com

sudo docker compose run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  -d "$DUCKDNS_DOMAIN" \
  --email "$CERTBOT_EMAIL" --agree-tos --no-eff-email
```

This populates `certbot/conf` with the initial certificates used by nginx.

## 3. Build and launch backend stack

```bash
docker compose up -d --build
```

- `backend`: FastAPI + uvicorn listening on `backend:8000`, CORS controlled via `ALLOWED_ORIGINS`.
- `nginx`: terminates TLS for `${DUCKDNS_DOMAIN}` and proxies all requests to the backend; also serves ACME HTTP challenges.
- `certbot`: runs a renewal loop every 12h against the shared webroot.

## 4. Verification
- `docker compose ps` ensures all services are healthy.
- `docker compose exec nginx nginx -t` validates the active config.
- `docker compose logs -f nginx certbot` shows TLS handshakes and cert renewals.
- `curl -I https://$DUCKDNS_DOMAIN/api/v1/health` should return `200 OK`.

## 5. Maintenance
- Certificates renew automatically; check logs monthly to confirm.
- When updating the backend code, pull latest commits and rerun `docker compose up -d --build`.
- Back up uploaded media via the `backend-data` volume if needed.

## Notes
- Keep `.env` out of source control so your DuckDNS domain and frontend origin stay private.
- If you later deploy a separate frontend, set its URL in `ALLOWED_ORIGINS` so browsers can call this backend over HTTPS.
