# Serves the static site with Caddy. Railway builds this via railway.json.
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY site /srv
