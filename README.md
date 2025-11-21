# Production Deployment Guide

## Prerequisites
- Docker 24+ and Docker Compose plugin.
- DuckDNS hostname (set `DUCKDNS_DOMAIN` in `.env`).
- Valid email for Let's Encrypt (`CERTBOT_EMAIL`).

## 1. Prepare environment
Create `.env` beside `docker-compose.yml`:

```env
DUCKDNS_DOMAIN=yourdomain.duckdns.org
ALLOWED_ORIGINS=https://yourdomain.duckdns.org,http://localhost:3000
NEXT_PUBLIC_API_URL=https://yourdomain.duckdns.org
CERTBOT_EMAIL=you@example.com
```

Create the folders expected by the stack:

```bash
mkdir -p certbot/conf certbot/www nginx
```

`nginx/nginx.conf.template` references `${DUCKDNS_DOMAIN}` so no hostnames are committed.

## 2. Bootstrap certificates
Do this step once before the renew loop:

```bash
DUCKDNS_DOMAIN=yourdomain.duckdns.org
CERTBOT_EMAIL=you@example.com

sudo docker compose run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  -d "$DUCKDNS_DOMAIN" \
  --email "$CERTBOT_EMAIL" --agree-tos --no-eff-email
```

## 3. Build and launch

```bash
docker compose up -d --build
```

- Backend: FastAPI + uvicorn on `backend:8000`.
- Frontend: Next.js server on `frontend:3000`.
- Nginx: terminates TLS and proxies to both services.
- Certbot: renews every 12h using the mounted webroot.

## 4. Verification
1. Check container health:
   ```bash
   docker compose ps
   ```
2. Validate Nginx config:
   ```bash
   docker compose exec nginx nginx -t
   ```
3. Tail logs until you see successful TLS handshakes:
   ```bash
   docker compose logs -f nginx certbot
   ```
4. Browse `https://${DUCKDNS_DOMAIN}` and confirm the app loads; `/api/v1/health` should return `{ "status": "ok" }`.

## 5. Maintenance
- Certificates: renew job already runs; confirm with `docker compose logs certbot` monthly.
- Updates: pull latest code, rebuild `docker compose up -d --build`.
- Backups: `backend-data` (uploads) and `backend-temp` volumes can be exported via `docker run --rm -v video-translator_backend-data:/data busybox tar -czf /backup/uploads.tar.gz /data`.

## 6. Troubleshooting
- Port conflicts: ensure host ports 80/443/8000/3000 are free before starting.
- Cert failures: verify DuckDNS record points to this server and that `certbot/www` is world-readable by Nginx.
- CORS issues: adjust `ALLOWED_ORIGINS` in `.env` and redeploy.
