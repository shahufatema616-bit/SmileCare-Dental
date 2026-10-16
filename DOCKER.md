# SmileCare Dental — Docker handoff

Yes — Docker is the right way to share this with a client. No local Python setup drama.

## What the client needs

- Docker Desktop (or Docker Engine + Compose plugin)
- About 1–2 minutes for the first build

## Start the demo

From this folder:

```bash
docker compose up --build
```

Then open:

- Website: http://localhost:8091/
- Admin: http://localhost:8091/admin/
- Reports: http://localhost:8091/admin/reports/

### Admin login

- Username: `admin`
- Password: `SmileCare@2026`

## What’s included

- Full booking app (book / manage / cancel / reschedule)
- Branded admin + clinic reports
- Demo database with sample patients, confirmed bookings, and reminder logs
- Developer credits page

## Stop

```bash
docker compose down
```

To reset demo data (fresh sample DB):

```bash
docker compose down -v
docker compose up --build
```

## Notes

- Host port is **8091** (mapped to container port 8000).
- Emails print inside the container logs:

```bash
docker compose logs -f web
```

Look for `SMILECARE EMAIL SENT`.
