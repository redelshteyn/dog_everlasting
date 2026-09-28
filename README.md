# Dog Everlasting

Website for Dog Everlasting, a private atelier that preserves dogs so they can stay by their family's side forever.

## Structure

```
site/index.html      The website: a single self-contained HTML file (inline CSS and JS)
site/likeness.html   The private likeness page for Register members: photos, film, measurements
app/                 FastAPI backend: serves the site, saves commissions, uploads and measurements
  catalog.py         What we ask families to capture (views, film, measurements). Edit here.
  main.py            Routes and API
  admin.py           Password-protected pages for the team (/admin)
migrations/          Database migrations (Alembic), applied automatically on startup
tests/               pytest suite
Dockerfile           Container Railway builds
railway.json         Railway build and deploy settings
```

## Running it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080. It uses a local SQLite file (`dogeverlasting.db`) and saves uploads to `./media`. The admin password locally is `letmein` unless you set `ADMIN_PASSWORD`.

Run the tests with `pytest`.

## Deploying to Railway

1. **Connect the repo** through the Railway GitHub app so pushes to `main` deploy automatically.
2. **Add the Postgres plugin** to the project. Railway injects `DATABASE_URL`.
3. **Add a volume** to the service, mounted at `/data`. Photos and film are saved there. Without it, every deploy would wipe what families have uploaded.
4. **Set `ADMIN_PASSWORD`** under Variables. It protects `/admin`, where the team sees every request, upload and measurement.

The app **refuses to start** on Railway without Postgres, the volume and `ADMIN_PASSWORD`, and Railway keeps the previous deploy live, so nothing breaks while you set them up. Health check: `/healthz`.

## How the Register flow works

1. A family joins the Register through "Begin a commission". The request is saved, and they get a private link: `/likeness/<token>`.
2. On that page they add photographs by view (front, sides, three-quarters, rear, above; eyes, nose, whisker pads, ear set; markings, standing, sitting) and a short film, over as many days as they like.
3. They add rounds of measurements, in inches or centimetres. We average every round.
4. The team sees everything at `/admin`.

The link is the only key to the page, so treat it like a password. It is not yet emailed; families see it once on the confirmation screen, so they should bookmark it until email is connected.

## The site

- **Collection:** three commissions by size: The Petite ($10,000), The Signature ($16,500), The Grand ($24,000).
- **Memorial options:** a comparison of preservation against memorial diamonds, tattoos, luxury funerals and painted portraits, answering "What are luxury pet memorial options?" and "How can I preserve my dog?" (also in the structured data FAQ).
- **Plans:** *At Time of Need* ($10,000, paid in full at commission; likeness modelled from photographs) or *The Register* ($35 a month, credited toward the commission: a 3D model of the dog made now and stored until needed, and arrangements with the vet in advance; remaining balance due at commission; non-refundable; one named dog, not transferable).
- **Commission flow:** a full-screen, five-step "Begin a commission" form with a live price summary. Time of Need and the Register ask for the dog's veterinarian.
- **Process:** (1) 3D model of the dog while alive, pose and presentation agreed; (2) we provide our case to the vet, who sends the dog when the time comes; (3) form sculpted from the model while the coat is preserved; (4) changes since the model are agreed with the owner; (5) assembled and returned by fine-art shipper.
- **Structured data:** schema.org JSON-LD in `<head>` describes the business, plans, prices and FAQ for search engines and AI agents. Keep it in sync with the page copy.

## Before launch

- [ ] Email the team on every new request, and email families their private likeness link
- [ ] Replace placeholder phone number (+1 888 555 0142) and confirm the email domain
- [ ] Replace photography placeholders (each `.ph` block's caption is the shot brief)
- [ ] Legal review of the Register (prepaid, multi-year plan)
- [ ] Written carrier agreement (UPS or FedEx) for shipping frozen animals; standard terms prohibit it
- [ ] Design and source the preservation case (insulated, leak-proof, sized per commission)

## Roadmap

1. Backend: ~~form submissions~~ (done, saved to Postgres), ~~likeness uploads and measurements~~ (done), email notifications, Stripe billing for the Register ($35/month)
2. Meta Muse member connector: Register status and veterinarian details
3. Meta Muse directory connector: public, read-only services and booking
