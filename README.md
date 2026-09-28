# Dog Everlasting

Website for Dog Everlasting, a private atelier that preserves dogs so they can stay by their family's side forever.

## Structure

```
site/index.html   The full website: a single self-contained HTML file (inline CSS and JS)
Dockerfile        Container that serves site/ with Caddy (used by Railway)
Caddyfile         Web server config: static files, gzip, /healthz, security headers
railway.json      Railway build and deploy settings
```

Open `site/index.html` in a browser to view it. There is no build step.

## Deploying to Railway

The site is served by [Caddy](https://caddyserver.com) in a small container (`Dockerfile`, `Caddyfile`). Railway reads `railway.json`, builds the Dockerfile, and checks `/healthz`.

1. In Railway: **New Project → Deploy from GitHub repo** → pick `dog_everlasting`.
2. **Settings → Networking → Custom Domain**: add your domain, then create the DNS record Railway shows you at your registrar.

No environment variables are needed yet. Railway sets `PORT` automatically.

To run the container locally:

```bash
docker build -t dog-everlasting . && docker run --rm -p 8080:8080 dog-everlasting
```

## The site

- **Collection:** three commissions by size: The Petite ($10,000), The Signature ($16,500), The Grand ($24,000), plus refinements (add-ons).
- **Plans:** *At Time of Need* ($10,000, paid in full at commission) or *The Register* ($800 a year, credited toward the commission, billing stops at $10,000; one photo a month; non-refundable; one named dog, not transferable).
- **Booking flow:** a full-screen, five-step consultation request with a live price summary.
- **Structured data:** schema.org JSON-LD in `<head>` describes the business, plans, prices and FAQ for search engines and AI agents. Keep it in sync with the page copy.

## Before launch

- [ ] Connect the booking form to a backend (see `TODO` in `site/index.html`)
- [ ] Replace placeholder phone number (+1 888 555 0142) and confirm the email domain
- [ ] Replace photography placeholders (each `.ph` block's caption is the shot brief)
- [ ] Legal review of the Register (prepaid, multi-year plan)

## Roadmap

1. Backend: form submissions, Stripe billing for the Register, member accounts, photo storage
2. Meta Muse member connector: monthly photo submission and Register status
3. Meta Muse directory connector: public, read-only services and booking
